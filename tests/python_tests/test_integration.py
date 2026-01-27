import pytest
from src_python.core.conditioner import Conditioner
# Correction : On importe 'EntropySourceManager', pas 'EntropySource'
from src_python.modules.entropy_src import EntropySourceManager, JitterCollector

def test_integration_chain():
    """
    Test complet de la chaîne : Collecte -> Conditionnement -> Seed
    """
    print("\n=== DÉBUT DU TEST D'INTÉGRATION ===")

    # 1. Initialisation
    try:
        cond = Conditioner()
        collector = JitterCollector()
        mgr = EntropySourceManager(collector, cond)
        print("[OK] Modules initialisés.")
    except Exception as e:
        pytest.fail(f"Échec initialisation : {e}")

    # 2. Exécution (Génération de seed)
    try:
        # On demande 32 octets (256 bits)
        seed = mgr.get_entropy(32)
        print(f"[INFO] Seed générée : {seed.hex().upper()}")
    except Exception as e:
        pytest.fail(f"Échec génération entropie : {e}")

    # 3. Validation (Assertions)
    # C'est ici qu'on prouve que ça marche
    assert len(seed) == 32, "La taille de la seed est incorrecte !"
    assert isinstance(seed, bytes), "Le format de sortie doit être des bytes !"
    
    print("=== TEST RÉUSSI AVEC SUCCÈS ✅ ===")