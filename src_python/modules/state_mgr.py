# Simulation TEE/Secure Storage + Entropie Système + Entropie Utilisateur
import os
import json
import time
from src_python.utils.converters import bytes_le_to_int, int_to_bytes_le

class StateManager:
    """
    Simule une zone de stockage sécurisée (TEE/Secure Element).
    Rôle : Sauvegarder l'état du DRBG pour la persistance entre redémarrages.
    """
    
    def __init__(self, filename="secure_state.json"):
        self.filename = filename
        self.in_memory_state = {}

    def save_state(self, seed: bytes, reseed_counter: int):
        """
        Écrit l'état de manière atomique (simule une écriture Flash sécurisée).
        """
        state_data = {
            "seed_hex": seed.hex(),
            "reseed_counter": reseed_counter,
            "timestamp": time.time(),
            "checksum": self._compute_checksum(seed, reseed_counter)
        }
        
        # Simulation d'écriture sécurisée (Sealing)
        try:
            with open(self.filename, 'w') as f:
                json.dump(state_data, f, indent=4)
        except IOError as e:
            print(f"[ERREUR TEE] Échec sauvegarde état: {e}")

    def load_state(self):
        """
        Charge l'état au démarrage. Retourne (seed, counter) ou (None, 0) si vide.
        """
        if not os.path.exists(self.filename):
            return None, 0
            
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                
            seed = bytes.fromhex(data["seed_hex"])
            counter = data["reseed_counter"]
            
            # Vérification anti-corruption
            if data["checksum"] != self._compute_checksum(seed, counter):
                print("[ALERTE SÉCURITÉ] Checksum invalide ! État corrompu.")
                return None, 0
                
            return seed, counter
            
        except (json.JSONDecodeError, KeyError):
            return None, 0

    def _compute_checksum(self, seed: bytes, counter: int) -> int:
        """Checksum simple pour détecter la corruption (pas une signature crypto ici)."""
        return sum(seed) + counter