# Gestion Little-Endian !! 
import struct
import numpy as np

def int_to_bytes_le(value: int, length: int = 4) -> bytes:
    """
    Convertit un entier Python en séquence d'octets Little-Endian.
    Vital pour l'interopérabilité avec le matériel ARM (Mobile).
    
    Args:
        value: L'entier à convertir.
        length: Le nombre d'octets voulu (ex: 4 pour un uint32).
    """
    try:
        # byteorder='little' est la clé pour l'architecture mobile
        return value.to_bytes(length, byteorder='little', signed=False)
    except OverflowError:
        raise ValueError(f"[ERREUR] L'entier {value} ne tient pas sur {length} octets.")

def bytes_le_to_int(data: bytes) -> int:
    """
    Convertit une séquence d'octets Little-Endian en entier Python.
    Utilisé pour lire les données brutes venant du DRBG ou de la source d'entropie.
    """
    return int.from_bytes(data, byteorder='little', signed=False)

def polynomial_to_bytes(poly: np.ndarray, q: int) -> bytes:
    """
    Sérialise un polynôme (vecteur numpy) en octets pour le stockage ou la transmission.
    Chaque coefficient est normalisé modulo q.
    """
    buffer = bytearray()
    for coeff in poly:
        val = int(coeff) % q
        # On stocke chaque coefficient sur 2 octets (car q=3329 tient sur 16 bits)
        buffer.extend(int_to_bytes_le(val, length=2))
    return bytes(buffer)