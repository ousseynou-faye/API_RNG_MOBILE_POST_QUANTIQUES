import os
import time
import struct
from dataclasses import dataclass
from typing import Optional

# Import relatif propre au projet
try:
    from src_python.core.conditioner import Conditioner
except ImportError:
    # Fallback si exécuté en standalone (pour debug)
    print("[WARN] Import relatif échoué, mode dégradé.")
    class Conditioner:
        def condition(self, r, p, b): return b'\x00' * (b//8)

# 1. Structures de Données
class EntropyHealthError(Exception): pass

@dataclass
class HealthReport:
    ok: bool
    rct_ok: bool
    apt_ok: bool
    reason: str = ""

# 2. Collecteurs
class NoiseCollector:
    def sample(self) -> bytes: raise NotImplementedError

class JitterCollector(NoiseCollector):
    def __init__(self, k_deltas: int = 32):
        self.k = k_deltas
    
    def sample(self) -> bytes:
        last = time.perf_counter_ns()
        deltas = []
        for _ in range(self.k):
            now = time.perf_counter_ns()
            delta = (now - last) & 0xFFFFFFFFFFFFFFFF
            deltas.append(delta)
            last = now
        return b"".join(struct.pack("<Q", d) for d in deltas)

# 3. Tests de Santé (Optimisés)
class RepetitionCountTest:
    def __init__(self, cutoff: int = 20):
        self.cutoff = cutoff
        self._last = None
        self._count = 0
    
    def update(self, x: bytes) -> bool:
        if self._last is None:
            self._last = x
            self._count = 1
            return True
        if x == self._last:
            self._count += 1
            if self._count >= self.cutoff: return False
        else:
            self._last = x
            self._count = 1
        return True

class AdaptiveProportionTest:
    def __init__(self, window: int = 512, cutoff: int = 13):
        self.window = window
        self.cutoff = cutoff
        self.sample_count = 0
        self.target = None
        self.target_count = 0
    
    def update(self, x: bytes) -> bool:
        self.sample_count += 1
        if self.sample_count == 1:
            self.target = x
            self.target_count = 1
            return True
        if x == self.target: self.target_count += 1
        if self.sample_count >= self.window:
            res = (self.target_count <= self.cutoff)
            self.sample_count = 0
            self.target = None
            self.target_count = 0
            return res
        return True

# 4. Le Gestionnaire (C'est lui que le test appelle !)
class EntropySourceManager:
    def __init__(self, collector: NoiseCollector, conditioner: Conditioner):
        self.collector = collector
        self.cond = conditioner
        self.rct = RepetitionCountTest()
        self.apt = AdaptiveProportionTest()
        self.startup_done = False

    def startup_tests(self) -> HealthReport:
        for _ in range(64):
            x = self.collector.sample()
            if not self.rct.update(x): return HealthReport(False, False, True, "Startup RCT Fail")
            if not self.apt.update(x): return HealthReport(False, True, False, "Startup APT Fail")
        self.startup_done = True
        return HealthReport(True, True, True, "Startup OK")

    def get_entropy(self, num_bytes: int = 48) -> bytes:
        if not self.startup_done:
            rep = self.startup_tests()
            if not rep.ok: raise EntropyHealthError(rep.reason)
        
        buffer = bytearray()
        needed = max(1, num_bytes // 8) * 2
        for _ in range(needed):
            sample = self.collector.sample()
            if not self.rct.update(sample): raise EntropyHealthError("Continuous RCT Fail")
            if not self.apt.update(sample): raise EntropyHealthError("Continuous APT Fail")
            buffer.extend(sample)
            
        return self.cond.condition(buffer, b"ENTROPY", num_bytes * 8)