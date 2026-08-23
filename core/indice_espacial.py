from collections import defaultdict
from math import floor


class IndiceEspacial:
    """Grade simples para consultas locais de entidades.

    A estrutura prioriza previsibilidade e baixo overhead. Entidades são
    armazenadas em buckets quadrados e só mudam de bucket quando atravessam
    uma célula.
    """

    def __init__(self, tamanho_celula=128):
        self.tamanho_celula = max(16, int(tamanho_celula))
        self._buckets = defaultdict(set)
        self._posicoes = {}
        self._grupos = {}

    def _chave(self, x, y):
        return (
            floor(float(x) / self.tamanho_celula),
            floor(float(y) / self.tamanho_celula),
        )

    def registrar(self, entidade, grupo=None):
        if entidade is None:
            return

        chave = self._chave(entidade.x, entidade.y)
        anterior = self._posicoes.get(entidade)

        self._grupos[entidade] = grupo
        if anterior == chave:
            return

        if anterior is not None:
            bucket = self._buckets.get(anterior)
            if bucket is not None:
                bucket.discard(entidade)
                if not bucket:
                    self._buckets.pop(anterior, None)

        self._buckets[chave].add(entidade)
        self._posicoes[entidade] = chave

    def remover(self, entidade):
        if entidade is None:
            return

        chave = self._posicoes.pop(entidade, None)
        self._grupos.pop(entidade, None)
        if chave is None:
            return

        bucket = self._buckets.get(chave)
        if bucket is None:
            return

        bucket.discard(entidade)
        if not bucket:
            self._buckets.pop(chave, None)

    def atualizar(self, entidade):
        if entidade is None:
            return
        if entidade not in self._posicoes:
            self.registrar(entidade, self._grupos.get(entidade))
            return

        chave_nova = self._chave(entidade.x, entidade.y)
        chave_antiga = self._posicoes[entidade]
        if chave_nova == chave_antiga:
            return

        bucket = self._buckets.get(chave_antiga)
        if bucket is not None:
            bucket.discard(entidade)
            if not bucket:
                self._buckets.pop(chave_antiga, None)

        self._buckets[chave_nova].add(entidade)
        self._posicoes[entidade] = chave_nova

    def atualizar_todas(self, entidades):
        for entidade in entidades:
            self.atualizar(entidade)

    def consultar_raio(self, x, y, raio, grupos=None):
        grupos = set(grupos) if grupos is not None else None
        raio = max(0.0, float(raio))

        min_cx = floor((x - raio) / self.tamanho_celula)
        max_cx = floor((x + raio) / self.tamanho_celula)
        min_cy = floor((y - raio) / self.tamanho_celula)
        max_cy = floor((y + raio) / self.tamanho_celula)

        resultado = []
        raio_quadrado = raio * raio
        vistos = set()

        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                bucket = self._buckets.get((cx, cy))
                if not bucket:
                    continue

                for entidade in bucket:
                    if entidade in vistos:
                        continue
                    vistos.add(entidade)

                    if grupos is not None and self._grupos.get(entidade) not in grupos:
                        continue

                    dx = entidade.x - x
                    dy = entidade.y - y
                    if dx * dx + dy * dy <= raio_quadrado:
                        resultado.append(entidade)

        return resultado

    def consultar_celulas(self, x, y, raio_celulas=1, grupos=None):
        grupos = set(grupos) if grupos is not None else None
        cx, cy = self._chave(x, y)
        resultado = []
        vistos = set()

        for dx in range(-raio_celulas, raio_celulas + 1):
            for dy in range(-raio_celulas, raio_celulas + 1):
                bucket = self._buckets.get((cx + dx, cy + dy))
                if not bucket:
                    continue
                for entidade in bucket:
                    if entidade in vistos:
                        continue
                    vistos.add(entidade)
                    if grupos is None or self._grupos.get(entidade) in grupos:
                        resultado.append(entidade)

        return resultado

    def tamanho(self):
        return len(self._posicoes)
