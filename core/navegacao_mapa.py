from collections import deque
from math import atan2, cos, hypot, sin
from random import choice, randint, uniform

from utils.config import TILE_SIZE


class NavegacaoMapa:
    def __init__(self, tilemap):
        self.tilemap = tilemap
        self.pontos_grama = []

        for linha in range(self.tilemap.altura):
            for coluna in range(self.tilemap.largura):
                if self.tilemap.pode_andar(coluna, linha, 0):
                    x, y = self.tilemap.tile_para_pixel(coluna, linha)

                    self.pontos_grama.append(
                        (
                            x + TILE_SIZE // 2,
                            y + TILE_SIZE // 2,
                        )
                    )

    def pode_andar(self, x, y, altura):
        coluna, linha = self.tilemap.pixel_para_tile(x, y)
        return self.tilemap.pode_andar(coluna, linha, altura)

    def fugir(
        self,
        x,
        y,
        atacante_x,
        atacante_y,
        altura,
    ):
        angulo = atan2(
            y - atacante_y,
            x - atacante_x,
        )

        angulo += uniform(-0.5, 0.5)

        distancia = uniform(120, 180)

        destino_x = x + cos(angulo) * distancia
        destino_y = y + sin(angulo) * distancia

        return self.ajustar_posicao(destino_x, destino_y, altura)

    def ajustar_posicao(self, x, y, altura):
        if self.pode_andar(x, y, altura):
            return x, y

        posicao = self._procurar_grama_mais_proxima(x, y, altura)

        if posicao is None:
            return None

        return posicao

    def limitar_movimento(self, x0, y0, x1, y1, altura, distancia_maxima=None):
        if self._caminho_livre(x0, y0, x1, y1, altura) and self.pode_andar(
            x1, y1, altura
        ):
            return self._limitar_distancia(x0, y0, x1, y1, distancia_maxima)

        if distancia_maxima is not None:
            passo = min(distancia_maxima, 48.0)
        else:
            passo = 48.0

        rota = self.obter_ponto_rota(
            x0,
            y0,
            x1,
            y1,
            altura,
            distancia_maxima=passo,
        )

        if rota is not None:
            return self._limitar_distancia(x0, y0, rota[0], rota[1], distancia_maxima)

        desvio = self.encontrar_desvio(
            x0,
            y0,
            x1,
            y1,
            altura,
            distancia_maxima=passo,
        )

        if desvio is not None:
            return self._limitar_distancia(
                x0,
                y0,
                desvio[0],
                desvio[1],
                distancia_maxima,
            )

        destino = self._procurar_grama_mais_proxima(x1, y1, altura)
        if destino is None:
            return None

        return self._limitar_distancia(
            x0,
            y0,
            destino[0],
            destino[1],
            distancia_maxima,
        )

    def destino_aleatorio(self, max_tentativas=200):
        for _ in range(max_tentativas):
            x, y = self._escolher_ponto_grama()

            if x is not None:
                return x, y

        return 0, 0

    def ponto_aleatorio_no_raio(
        self,
        x,
        y,
        altura,
        distancia_minima,
        distancia_maxima,
        max_tentativas=100,
    ):
        for _ in range(max_tentativas):
            xx = randint(
                int(x - distancia_maxima),
                int(x + distancia_maxima),
            )

            yy = randint(
                int(y - distancia_maxima),
                int(y + distancia_maxima),
            )

            distancia = hypot(xx - x, yy - y)

            if distancia_minima <= distancia <= distancia_maxima and self.pode_andar(
                xx, yy, altura
            ):
                return xx, yy

        return self._procurar_grama_mais_proxima(x, y, altura)

    def _escolher_ponto_grama(self):
        return choice(self.pontos_grama)

    def _procurar_grama_mais_proxima(self, x, y, altura):
        coluna, linha = self.tilemap.pixel_para_tile(x, y)

        melhor = None
        melhor_distancia = float("inf")

        for raio in range(1, 8):
            for dx in range(-raio, raio + 1):
                for dy in range(-raio, raio + 1):
                    col = coluna + dx
                    lin = linha + dy

                    if not self.tilemap.pode_andar(col, lin, altura):
                        continue

                    xx, yy = self.tilemap.tile_para_pixel(col, lin)

                    distancia = abs(dx) + abs(dy)

                    if distancia < melhor_distancia:
                        melhor = (
                            xx + TILE_SIZE // 2,
                            yy + TILE_SIZE // 2,
                        )

                        melhor_distancia = distancia

            if melhor:
                return melhor

        return None

    def obter_ponto_rota(
        self,
        origem_x,
        origem_y,
        destino_x,
        destino_y,
        altura,
        distancia_maxima=None,
    ):
        if not self.pode_andar(destino_x, destino_y, altura):
            destino_x, destino_y = self.ajustar_posicao(
                destino_x, destino_y, altura
            ) or (
                destino_x,
                destino_y,
            )

        rota = self.calcular_rota(
            origem_x,
            origem_y,
            destino_x,
            destino_y,
            altura,
        )

        if not rota:
            return None

        if distancia_maxima is None:
            return rota[0]

        for ponto in rota:
            distancia = hypot(ponto[0] - origem_x, ponto[1] - origem_y)
            if distancia <= distancia_maxima:
                coluna, linha = self.tilemap.pixel_para_tile(ponto[0], ponto[1])
                return self._ponto_para_tile_seguro(coluna, linha, altura)

        primeiro = rota[0]
        coluna, linha = self.tilemap.pixel_para_tile(primeiro[0], primeiro[1])
        return self._ponto_para_tile_seguro(coluna, linha, altura)

    def encontrar_desvio(
        self,
        origem_x,
        origem_y,
        destino_x,
        destino_y,
        altura,
        distancia_maxima=None,
    ):
        limite = distancia_maxima

        if limite is None:
            limite = hypot(destino_x - origem_x, destino_y - origem_y)

        limite = max(16, float(limite))

        origem_coluna, origem_linha = self.tilemap.pixel_para_tile(origem_x, origem_y)
        destino_coluna, destino_linha = self.tilemap.pixel_para_tile(
            destino_x, destino_y
        )

        if not self._esta_em_grade(origem_coluna, origem_linha):
            origem_coluna, origem_linha = self._ajustar_para_grade(origem_x, origem_y)

        if not self._esta_em_grade(destino_coluna, destino_linha):
            destino_coluna, destino_linha = self._ajustar_para_grade(
                destino_x, destino_y
            )

        rota = self._calcular_rota_grade(
            origem_coluna,
            origem_linha,
            destino_coluna,
            destino_linha,
            altura,
        )

        if not rota:
            return self.ajustar_posicao(
                destino_x,
                destino_y,
                altura,
            )

        for coluna, linha in rota:
            ponto = self._ponto_para_tile_seguro(coluna, linha, altura)
            xx, yy = ponto

            distancia = hypot(xx - origem_x, yy - origem_y)
            if distancia > limite:
                continue

            if distancia < 24:
                continue

            if self._caminho_livre(xx, yy, destino_x, destino_y, altura):
                return xx, yy

        ultimo = rota[-1]

        ponto = self._ponto_para_tile_seguro(
            ultimo[0],
            ultimo[1],
            altura,
        )

        return self.ajustar_posicao(
            ponto[0],
            ponto[1],
            altura,
        )

    def _ponto_para_tile_seguro(self, coluna, linha, altura):
        xx, yy = self.tilemap.tile_para_pixel(coluna, linha)
        centro_x = xx + TILE_SIZE // 2
        centro_y = yy + TILE_SIZE // 2

        deslocamento_x = 0.0
        deslocamento_y = 0.0
        margem = max(20, TILE_SIZE // 3)

        for dx, dy in (
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
            (1, 1),
            (-1, 1),
            (1, -1),
            (-1, -1),
        ):
            vizinho = (coluna + dx, linha + dy)

            eh_nao_caminhavel = not self.tilemap.pode_andar(*vizinho, altura)

            if not eh_nao_caminhavel:
                continue

            if dx > 0:
                deslocamento_x -= margem
            elif dx < 0:
                deslocamento_x += margem

            if dy > 0:
                deslocamento_y -= margem
            elif dy < 0:
                deslocamento_y += margem

        x = centro_x + deslocamento_x
        y = centro_y + deslocamento_y

        x = min(max(x, xx + margem), xx + TILE_SIZE - margem)
        y = min(max(y, yy + margem), yy + TILE_SIZE - margem)

        return x, y

    def _limitar_distancia(self, x0, y0, x1, y1, distancia_maxima=None):
        if distancia_maxima is None:
            return x1, y1

        distancia_total = hypot(x1 - x0, y1 - y0)

        if distancia_total <= distancia_maxima:
            return x1, y1

        angulo = atan2(y1 - y0, x1 - x0)
        return (
            x0 + cos(angulo) * distancia_maxima,
            y0 + sin(angulo) * distancia_maxima,
        )

    def _esta_em_grade(self, coluna, linha):
        return isinstance(coluna, int) and isinstance(linha, int)

    def _ajustar_para_grade(self, x, y):
        coluna, linha = self.tilemap.pixel_para_tile(x, y)
        return coluna, linha

    def _calcular_rota_grade(
        self, origem_coluna, origem_linha, destino_coluna, destino_linha, altura
    ):
        fila = deque([(origem_coluna, origem_linha)])
        veio_de = {(origem_coluna, origem_linha): None}

        while fila:
            atual_coluna, atual_linha = fila.popleft()

            if (atual_coluna, atual_linha) == (destino_coluna, destino_linha):
                break

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                vizinho = (atual_coluna + dx, atual_linha + dy)
                if vizinho in veio_de:
                    continue
                if not self.tilemap.pode_andar(*vizinho, altura):
                    continue
                veio_de[vizinho] = (atual_coluna, atual_linha)
                fila.append(vizinho)

        if (destino_coluna, destino_linha) not in veio_de:
            return []

        rota = []
        atual = (destino_coluna, destino_linha)
        while atual != (origem_coluna, origem_linha):
            rota.append(atual)
            atual = veio_de[atual]
        rota.reverse()
        return rota

    def _caminho_livre(self, x0, y0, x1, y1, altura):
        distancia = hypot(
            x1 - x0,
            y1 - y0,
        )

        passos = max(1, int(distancia / 16))

        for i in range(passos + 1):
            t = i / passos

            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t

            if not self.pode_andar(x, y, altura):
                return False

        return True

    def calcular_rota(self, origem_x, origem_y, destino_x, destino_y, altura):
        origem = self.tilemap.pixel_para_tile(
            origem_x,
            origem_y,
        )

        destino = self.tilemap.pixel_para_tile(
            destino_x,
            destino_y,
        )

        fila = deque([origem])

        veio_de = {
            origem: None,
        }

        while fila:
            atual = fila.popleft()

            if atual == destino:
                break

            for dx, dy in (
                (1, 0),
                (-1, 0),
                (0, 1),
                (0, -1),
                (1, 1),
                (-1, -1),
                (1, -1),
                (-1, 1),
            ):
                vizinho = (
                    atual[0] + dx,
                    atual[1] + dy,
                )

                if vizinho in veio_de:
                    continue

                if not self.tilemap.pode_andar(vizinho[0], vizinho[1], altura):
                    continue

                veio_de[vizinho] = atual

                fila.append(vizinho)

        if destino not in veio_de:
            return []

        rota = []

        atual = destino

        while atual != origem:
            x, y = self.tilemap.tile_para_pixel(
                atual[0],
                atual[1],
            )

            rota.append(
                (
                    x + TILE_SIZE // 2,
                    y + TILE_SIZE // 2,
                )
            )

            atual = veio_de[atual]

        rota.reverse()

        return rota
