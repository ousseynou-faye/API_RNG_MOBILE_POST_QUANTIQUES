"""
PARAMÈTRES DU SYSTÈME RNG POST-QUANTIQUE (LWR)
Alignés sur les standards NIST (inspirés de ML-KEM/Kyber mais adaptés pour LWR).
"""

# Dimension du réseau (Polynômes de degré 256)
N = 256 

# Module cryptographique (q). 
# 3329 est standard, mais pour l'optimisation mobile (LWR), 
# une puissance de 2 (4096) est souvent préférée pour éviter la division.
# Pour ce mémoire, on reste sur 3329 pour la rigueur académique (Kyber-compatible).
Q = 3329 

# Dimensions de la matrice (k x k). k=3 correspond au niveau de sécurité NIST 1 (AES-128 équivalent PQ).
K = 3 

# Taille de la Seed en octets (256 bits)
SEED_SIZE_BYTES = 32 

# Paramètre de sécurité pour le DRBG
SECURITY_STRENGTH_BITS = 256