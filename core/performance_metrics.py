from collections import defaultdict
from time import perf_counter


class PerformanceMetrics:
    """Instrumentação leve, desligável, para validar as etapas de otimização."""

    def __init__(self, habilitado=True):
        self.habilitado = habilitado
        self.frames = 0
        self.counters = defaultdict(int)
        self.timings = defaultdict(float)

    def contar(self, nome, quantidade=1):
        if self.habilitado:
            self.counters[nome] += quantidade

    def medir(self, nome):
        if not self.habilitado:
            return _NoOpTimer()
        return _Timer(self, nome)

    def iniciar_frame(self):
        if self.habilitado:
            self.frames += 1

    def snapshot(self):
        if not self.habilitado:
            return {"habilitado": False}
        return {
            "habilitado": True,
            "frames": self.frames,
            "counters": dict(self.counters),
            "timings": dict(self.timings),
        }

    def resetar(self):
        self.frames = 0
        self.counters.clear()
        self.timings.clear()


class _Timer:
    def __init__(self, metrics, nome):
        self.metrics = metrics
        self.nome = nome
        self.inicio = perf_counter()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.metrics.timings[self.nome] += perf_counter() - self.inicio
        return False


class _NoOpTimer:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False
