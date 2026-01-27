import sys
import os

# Ce fichier configure l'environnement avant les tests.
# Il force Python à voir le dossier racine du projet.

# 1. On récupère le dossier où se trouve ce fichier (tests/)
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. On remonte d'un cran pour trouver la racine du projet (API_RNG_...)
# ATTENTION : Si ce fichier est dans tests/python_tests, mettez '../..'
# Si ce fichier est dans tests/, mettez '..'
project_root = os.path.abspath(os.path.join(current_dir, '../'))

# 3. On l'ajoute au chemin système
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"[CONFTEST] Racine du projet ajoutée : {project_root}")