# Le moteur LWR (Update/Generate) DRBG (Deterministic Random Bit Generator)
# Basé sur le standard NIST SP 800-90A
import numpy as np
from typing import Tuple, Optional

# Imports internes
from src_python.utils.constants import N, K, Q, P, RESEED_INTERVAL
from src_python.core.conditioner import Conditioner

class LwrDrbgCore:
    """
    Générateur de Bits Aléatoires Déterministe basé sur Module-LWR.
    
    RELATION AVEC LWE (Learning With Errors) :
    ------------------------------------------
    Le problème LWE standard s'écrit : b = A*s + e (où 'e' est un bruit gaussien).
    Le problème LWR (ce code) s'écrit : b = Round(A*s).
    
    Le 'Rounding' remplace le bruit 'e'. C'est une variante déterministe de LWE.
    
    POURQUOI C'EST POST-QUANTIQUE ?
    -------------------------------
    Retrouver le secret 's' à partir des sorties nécessite de résoudre
    le problème CVP (Closest Vector Problem) sur un réseau euclidien.
    Aucun algorithme quantique connu (ni Shor, ni Grover) ne résout ça efficacement.
    """

    def __init__(self):
        self.conditioner = Conditioner()
        
        # Le Secret 's' (La clé du réseau)
        # Dimension : K * N (ex: 3 * 256 = 768 coefficients)
        self.state_s = np.zeros(K * N, dtype=np.int32)
        
        # Compteur de sécurité NIST
        self.reseed_counter = 0
        
        # Génération de la Matrice Publique A (La base du réseau)
        self._instantiate_matrix_A()

    def _instantiate_matrix_A(self):
        """Génère la matrice A (Structure publique du Lattice)."""
        rng_public = np.random.default_rng(seed=42)
        self.matrix_A = rng_public.integers(0, Q, size=(K * N, K * N), dtype=np.int32)

    def _lwr_rounding(self, vector_v: np.ndarray) -> np.ndarray:
        """
        L'OPÉRATION LWR (LWE SANS BRUIT GAUSSIEN).
        
        Maths : y = floor( (P/Q) * v )
        
        C'est cette opération qui détruit l'information et empêche
        l'inversion par un ordinateur quantique.
        """
        return np.floor((P / Q) * vector_v).astype(np.int32)

    def update(self, provided_data: bytes):
        """
        Mise à jour de l'état secret 's'.
        Utilise SHAKE-256 (Quantum-Resistant Hash) pour mélanger.
        """
        current_state_bytes = self.state_s.tobytes()
        needed_bytes = (K * N * 2)
        
        seed_material = self.conditioner.condition(
            raw_entropy=current_state_bytes + provided_data,
            personalization_string=b"DRBG_UPDATE_LWR",
            output_bits=needed_bytes * 8
        )
        
        new_state = np.frombuffer(seed_material, dtype=np.uint16).astype(np.int32)
        self.state_s = new_state[:K*N] % Q
        self.reseed_counter = 1

    def generate(self, num_bytes: int) -> bytes:
        """
        Génération via Lattice Operation.
        """
        if self.reseed_counter > RESEED_INTERVAL:
            raise RuntimeError("DRBG: Reseed Required.")

        # 1. Opération LWE/LWR : Produit Matrice-Vecteur
        # C'est lourd, mais c'est ça qui donne la sécurité géométrique.
        vector_v = np.dot(self.matrix_A, self.state_s) % Q
        
        # 2. Extraction du Bruit Déterministe (LWR Rounding)
        vector_y = self._lwr_rounding(vector_v)
        
        # 3. Sérialisation
        raw_output = vector_y.astype(np.uint16).tobytes()
        
        # 4. Ajustement de taille (Whitening final)
        final_output = self.conditioner.condition(
            raw_entropy=raw_output,
            personalization_string=b"LWR_OUTPUT",
            output_bits=num_bytes * 8
        )
        
        # 5. Forward Secrecy (Rotation de l'état)
        self.update(b"FS_ROTATE")
        self.reseed_counter += 1
        
        return final_output