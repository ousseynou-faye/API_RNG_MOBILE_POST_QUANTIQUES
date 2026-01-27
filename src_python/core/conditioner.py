# Toeplitz + SHAKE256 Conditioner + LWR
# Basé sur le standard NIST SP 800-90A
from Crypto.Hash import SHAKE256

class Conditioner:
    """
    Module de Conditionnement Cryptographique (NIST SP 800-90C).
    Remplace l'ancien 'HashConditioner'.
    
    Algo : SHAKE-256 (Standard FIPS 202).
    Pourquoi ? Contrairement à SHA-256, c'est un XOF (Extendable Output Function),
    ce qui permet de générer une seed de n'importe quelle taille sans boucle complexe.
    """

    def __init__(self):
        pass

    def condition(self, raw_entropy: bytes, personalization_string: bytes = b'', output_bits: int = 256) -> bytes:
        """
        Nettoie l'entropie brute pour en faire une seed uniforme.
        
        Args:
            raw_entropy: Données bruitées (Jitter, etc.)
            personalization_string: Chaîne de contexte (ex: ID unique du tel)
            output_bits: Taille de sortie souhaitée (256 par défaut)
        """
        # 1. Création de l'instance SHAKE
        shake = SHAKE256.new()
        
        # 2. Absorption (On mélange tout)
        shake.update(raw_entropy)
        shake.update(personalization_string)
        
        # 3. Extraction (On tire le nombre exact d'octets)
        output_len_bytes = output_bits // 8
        return shake.read(output_len_bytes)

    # Méthodes de compatibilité si ton ancien code appelle extract/expand
    def extract(self, raw: bytes) -> bytes:
        return self.condition(raw, b"EXTRACT", 256)
    
    def expand(self, prk: bytes, out_len: int) -> bytes:
        return self.condition(prk, b"EXPAND", out_len * 8)