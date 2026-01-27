import os
import time
import struct
from dataclasses import dataclass
from typing import Optional

# Import du conditionneur qu'on vient de créer
from src_python.core.conditioner import Conditioner

# =========================
# 1) Exceptions & Status
# =========================
class EntropyHealthError(Exception):
    """Levée quand les tests de santé (RCT/APT) échouent."""
    pass

@dataclass
class HealthReport:
    ok: bool
    rct_ok: bool
    apt_ok: bool
    reason: str = ""

# =========================
# 2) Collecte (Noise + Digitizer)
# =========================
class NoiseCollector:
    """Interface abstraite de collecte."""
    def sample(self) -> bytes:
        raise NotImplementedError

class JitterCollector(NoiseCollector):
    """
    Collecte de jitter via deltas de perf_counter_ns().
    C'est ta version, intégrée proprement.
    """
    def __init__(self, k_deltas: int = 32):
        self.k = k_deltas
    
    def sample(self) -> bytes:
        last = time.perf_counter_ns()
        deltas = []
        for _ in range(self.k):
            now = time.perf_counter_ns()
            # Masque 64 bits pour éviter les entiers Python géants
            delta = (now - last) & 0xFFFFFFFFFFFFFFFF
            deltas.append(delta)
            last = now
        
        # Pack en Little-Endian (<Q) pour le mobile
        return b"".join(struct.pack("<Q", d) for d in deltas)

class OsRngCollector(NoiseCollector):
    """Auxiliaire: RNG OS (/dev/urandom)."""
    def __init__(self, n: int = 32):
        self.n = n
    def sample(self) -> bytes:
        return os.urandom(self.n)

# =========================
# 3) Health Tests (Optimisés Mobile)
# =========================
class RepetitionCountTest:
    """RCT (NIST SP 800-90B): Détecte si la source est bloquée."""
    def __init__(self, cutoff: int = 20):
        self.cutoff = cutoff
        self._last: Optional[bytes] = None
        self._count: int = 0

    def update(self, x: bytes) -> bool:
        if self._last is None:
            self._last = x
            self._count = 1
            return True
        
        if x == self._last:
            self._count += 1
            if self._count >= self.cutoff:
                return False # FAIL
        else:
            self._last = x
            self._count = 1
        return True

class AdaptiveProportionTest:
    """
    APT (NIST SP 800-90B): Détecte les biais statistiques.
    OPTIMISATION : Utilise une fenêtre 'Reset' au lieu de 'Deque' pour économiser la RAM.
    """
    def __init__(self, window: int = 512, cutoff: int = 13):
        self.window = window
        self.cutoff = cutoff
        self.sample_count = 0
        self.target: Optional[bytes] = None
        self.target_count = 0

    def update(self, x: bytes) -> bool:
        self.sample_count += 1
        
        # Début de fenêtre : le premier échantillon devient la cible
        if self.sample_count == 1:
            self.target = x
            self.target_count = 1
            return True
            
        # Comptage
        if x == self.target:
            self.target_count += 1
            
        # Fin de fenêtre : Verdict
        if self.sample_count >= self.window:
            passed = (self.target_count <= self.cutoff)
            
            # Reset pour la fenêtre suivante
            self.sample_count = 0
            self.target = None
            self.target_count = 0
            return passed
            
        return True # En cours de fenêtre

# =========================
# 4) Manager (Orchestrateur)
# =========================
class EntropySourceManager:
    """
    Remplace 'NistStyleEntropySource'.
    Orchestre tout : Collecte -> Test -> Conditionnement.
    """
    def __init__(self, 
                 collector: NoiseCollector, 
                 conditioner: Conditioner,
                 rct_cutoff: int = 20,
                 apt_window: int = 512, 
                 apt_cutoff: int = 13):
        
        self.collector = collector
        self.cond = conditioner
        self.rct = RepetitionCountTest(rct_cutoff)
        self.apt = AdaptiveProportionTest(apt_window, apt_cutoff)
        self.startup_done = False

    def startup_tests(self) -> HealthReport:
        """Tests au démarrage (Power-On Self Test)."""
        # On teste 64 échantillons pour être sûr
        for _ in range(64):
            x = self.collector.sample()
            if not self.rct.update(x):
                return HealthReport(False, False, True, "Startup RCT failed")
            if not self.apt.update(x):
                return HealthReport(False, True, False, "Startup APT failed")
        
        self.startup_done = True
        return HealthReport(True, True, True, "Startup OK")

    def get_entropy(self, out_len: int = 48) -> bytes:
        """Récupère l'entropie finale."""
        # 1. Vérif Startup
        if not self.startup_done:
            rep = self.startup_tests()
            if not rep.ok: raise EntropyHealthError(rep.reason)

        # 2. Collecte continue (Accumulation)
        # On prend un peu plus que demandé pour la sécurité
        buffer = bytearray()
        needed_loops = max(1, out_len // 8) * 2
        
        for _ in range(needed_loops):
            x = self.collector.sample()
            
            # Tests continus
            if not self.rct.update(x): raise EntropyHealthError("Continuous RCT Fail")
            if not self.apt.update(x): raise EntropyHealthError("Continuous APT Fail")
            
            buffer.extend(x)

        # 3. Conditionnement (SHAKE-256)
        # Utilise la méthode .condition() du fichier core/conditioner.py
        return self.cond.condition(
            raw_entropy=buffer, 
            personalization_string=b"ENTROPY_SRC_V1", 
            output_bits=out_len * 8
        )