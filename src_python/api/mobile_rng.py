from typing import Tuple, Optional, Dict
import time

# Imports des composants internes
from src_python.api.rng_interface import QuantumSafeRNG
from src_python.core.lwr_drbg import LwrDrbgCore
from src_python.core.conditioner import Conditioner
from src_python.modules.entropy_src import EntropySourceManager, JitterCollector
from src_python.modules.state_mgr import StateManager

class MobileRNG(QuantumSafeRNG):
    """
    Implémentation finale du RNG Mobile.
    Orchestre : Jitter -> SHAKE -> LWR-DRBG -> TEE.
    """

    def __init__(self):
        # 1. Briques de base
        self.conditioner = Conditioner()
        self.collector = JitterCollector()
        
        # 2. Gestionnaires
        self.entropy_mgr = EntropySourceManager(self.collector, self.conditioner)
        self.state_mgr = StateManager() # Simule le TEE
        
        # 3. Le Cœur Post-Quantique
        self.drbg = LwrDrbgCore()
        
        self.is_initialized = False

    def initialize(self, security_param: int = 256) -> bool:
        """Boot sequence."""
        try:
            # A. Charger l'état sauvegardé (Anti-Rollback)
            seed, counter = self.state_mgr.load_state()
            
            # B. Obtenir de l'entropie fraîche (avec Tests de Santé au démarrage)
            fresh_entropy = self.entropy_mgr.get_entropy(48) # 384 bits
            
            # C. Mélange initial
            if seed:
                # Cold Start vs Warm Start
                # On mélange l'ancien état avec le nouveau pour une sécurité maximale
                print("[INFO] Restauration état TEE détectée.")
                initial_seed = self.conditioner.condition(seed + fresh_entropy, b"INIT")
            else:
                print("[INFO] Premier démarrage (Factory Reset).")
                initial_seed = fresh_entropy

            # D. Initialisation du DRBG
            self.drbg.update(initial_seed)
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"[ERREUR INIT] {e}")
            return False

    def reseed(self, external_entropy: Optional[bytes] = None) -> bool:
        """Reseed manuel ou forcé."""
        if not self.is_initialized: return False
        
        try:
            # 1. Entropie interne (Jitter)
            internal = self.entropy_mgr.get_entropy(48)
            
            # 2. Entropie externe (OS, Touch events...)
            combined = internal
            if external_entropy:
                combined += external_entropy
            
            # 3. Update DRBG
            self.drbg.update(combined)
            
            # 4. Sauvegarde État (Checkpoint)
            # On génère un 'token' pour le futur, on ne sauvegarde jamais la clé active
            next_seed_token = self.drbg.generate(32)
            self.state_mgr.save_state(next_seed_token, self.drbg.reseed_counter)
            
            return True
        except Exception as e:
            print(f"[ERREUR RESEED] {e}")
            return False

    def generate(self, num_bytes: int) -> Tuple[bytes, int]:
        """Génération sécurisée."""
        if not self.is_initialized:
            return b"", -1 # Erreur Non-Init
            
        try:
            # Appel au cœur LWR
            data = self.drbg.generate(num_bytes)
            
            # Auto-reseed périodique (Politique de sécurité)
            if self.drbg.reseed_counter > 1000:
                self.reseed()
                
            return data, 0 # Succès
            
        except RuntimeError:
            # Si le DRBG force un reseed (compteur dépassé)
            self.reseed()
            return self.drbg.generate(num_bytes), 0
        except Exception as e:
            print(f"[ERREUR GEN] {e}")
            return b"", -2

    def health_check(self) -> Dict:
        """Diagnostic."""
        status = {
            "module": "MobileRNG-LWR",
            "initialized": self.is_initialized,
            "reseed_count": self.drbg.reseed_counter,
            "entropy_source": "OK" if self.entropy_mgr.startup_done else "UNKNOWN"
        }
        return status