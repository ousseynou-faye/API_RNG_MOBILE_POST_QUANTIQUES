# Interface pour le RNG Post-Quantique Mobile
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict

class QuantumSafeRNG(ABC):
    """
    Interface Standard pour le RNG Mobile Post-Quantique.
    Définit le 'Contrat' que l'implémentation doit respecter.
    """

    @abstractmethod
    def initialize(self, security_param: int = 256) -> bool:
        """Démarre le système, charge l'état et vérifie la santé."""
        pass

    @abstractmethod
    def reseed(self, external_entropy: Optional[bytes] = None) -> bool:
        """Force un rafraîchissement de l'état interne (Injection d'entropie)."""
        pass

    @abstractmethod
    def generate(self, num_bytes: int) -> Tuple[bytes, int]:
        """
        Génère des octets aléatoires.
        Retourne: (données, code_statut) où 0 = Succès.
        """
        pass

    @abstractmethod
    def health_check(self) -> Dict:
        """Retourne un rapport de diagnostic complet."""
        pass