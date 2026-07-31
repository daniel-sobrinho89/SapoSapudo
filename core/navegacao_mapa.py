from math import atan2, cos, hypot, sin
from random import choice, randint, uniform

from utils.config import TILE_SIZE


class NavegacaoMapa:
    def __init__(self, tilemap):
        self.tilemap = tilemap
        self.pontos_grama = [
            (
                coluna * TILE_SIZE + TILE_SIZE // 2,
                linha * TILE_SIZE + TILE_SIZE // 2,
            )
            for linha, tiles in enumerate(self.tilemap.tiles)
            for coluna, tile in enumerate(tiles)
            if tile == self.tilemap.TIPO_GRAMA
        ]

    def pode_andar(self, x, y):
        return self.tilemap.eh_grama(x, y)

    def fugir(
        self,
        x,
        y,
        atacante_x,
        atacante_y,
    ):
        angulo = atan2(
            y - atacante_y,
            x - atacante_x,
        )

        angulo += uniform(-0.5, 0.5)

        distancia = uniform(120, 180)

        destino_x = x + cos(angulo) * distancia
        destino_y = y + sin(angulo) * distancia

        return self.ajustar_posicao(
            destino_x,
            destino_y,
        )

    def ajustar_posicao(self, x, y):
        if self.pode_andar(x, y):
            return x, y

        return self._procurar_grama_mais_proxima(x, y)

    def limitar_movimento(self, x0, y0, x1, y1):
        if self.pode_andar(x1, y1):
            return x1, y1

        return self._procurar_grama_mais_proxima(x1, y1)

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
                xx, yy
            ):
                return xx, yy

        return self._procurar_grama_mais_proxima(x, y)

    def _escolher_ponto_grama(self):
        return choice(self.pontos_grama)

    def _procurar_grama_mais_proxima(self, x, y):
        for raio in range(1, 8):
            for dx in range(-raio, raio + 1):
                for dy in range(-raio, raio + 1):
                    xx = x + dx * TILE_SIZE
                    yy = y + dy * TILE_SIZE

                    if self.pode_andar(xx, yy):
                        return xx, yy

        return x, y
