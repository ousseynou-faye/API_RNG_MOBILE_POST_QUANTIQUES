"""
PARAMÈTRES DU SYSTÈME RNG POST-QUANTIQUE (Module-LWR)
Ces constantes définissent la sécurité mathématique du système.
"""

# --- Paramètres du Réseau (Lattice) ---

# N : Dimension du vecteur/polynôme. 
# 256 est standard pour la sécurité post-quantique (Kyber/Dilithium).
N = 256 

# K : Rang du module (Matrice K x K). 
# K=3 correspond au niveau de sécurité NIST 1 (~AES-128 équivalent PQ).
K = 3 

# Q : Le grand Modulo (Espace de travail).
# 3329 est le nombre premier utilisé par Kyber. 
# Pour un DRBG mobile, on pourrait utiliser 4096 (2^12), mais 3329 reste la référence académique.
Q = 3329 

# P : Le Modulo d'Arrondi (Rounding Modulus).
# C'est l'innovation LWR : on compresse Q vers P.
# P doit être < Q. Une puissance de 2 permet une extraction de bits facile.
P = 1024 

# --- Paramètres Système ---

# Taille de la Seed en octets (256 bits)
SEED_SIZE_BYTES = 32 

# Limite de sécurité avant reseed obligatoire (NIST SP 800-90A)
RESEED_INTERVAL = 10000