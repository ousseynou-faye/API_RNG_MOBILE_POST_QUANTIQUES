import sys
import os
import binascii

# Fix PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src_python.api.mobile_rng import MobileRNG
except ImportError as e:
    print(f"[ERREUR] {e}")
    sys.exit(1)

def main():
    print("==================================================")
    print("   DEMO RNG MOBILE POST-QUANTIQUE (Module-LWR)    ")
    print("   Sécurité basée sur les Réseaux Euclidiens      ")
    print("==================================================\n")

    rng = MobileRNG()
    
    print(">>> 1. Initialisation (Chargement TEE + Source Entropie)...")
    if rng.initialize():
        print("[SUCCÈS] Moteur LWR prêt.")
    else:
        print("[FAIL] Erreur Init.")
        return

    # ICI : On change le message pour être clair
    print("\n>>> 2. Génération d'ALÉA POST-QUANTIQUE (Lattice-Based)")
    print("Ces octets sont générés par le problème mathématique LWR.\n")
    
    for i in range(5):
        # On génère 32 octets (Taille d'une clé AES-256)
        data, status = rng.generate(32)
        if status == 0:
            print(f"Sortie PQC #{i+1}: {binascii.hexlify(data).decode().upper()}")
        else:
            print("Erreur")

    print("\n>>> 3. Vérification Santé")
    print(rng.health_check())

if __name__ == "__main__":
    main()