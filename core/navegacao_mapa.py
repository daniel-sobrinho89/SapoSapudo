from collections import deque
from math import atan2, cos, hypot, sin
from random import choice, randint, uniform

from utils.config import TILE_SIZE

DIRECOES_4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIRECOES_8 = DIRECOES_4 + ((1, 1), (-1, -1), (1, -1), (-1, 1))


class NavegacaoMapa:
    def __init__(self, tilemap):
        self.tilemap = tilemap
        self.pontos_grama = [
            (
                self.tilemap.tile_para_pixel(c, lin)[0] + TILE_SIZE // 2,
                self.tilemap.tile_para_pixel(c, lin)[1] + TILE_SIZE // 2,
            )
            for lin in range(self.tilemap.altura)
            for c in range(self.tilemap.largura)
            if self.tilemap.pode_andar(c, lin, 0)
        ]

    def pode_andar(self, x, y, altura):
        coluna, linha = self.tilemap.pixel_para_tile(x, y)
        return self.tilemap.pode_andar(coluna, linha, altura)

    def obter_altura_transicao(self, origem_x, origem_y, destino_x, destino_y, altura):
        orig_c, orig_l = self.tilemap.pixel_para_tile(origem_x, origem_y)
        dest_c, dest_l = self.tilemap.pixel_para_tile(destino_x, destino_y)
        return self.tilemap.obter_transicao_degrau(
            orig_c, orig_l, dest_c, dest_l, altura
        )

    def fugir(self, x, y, atacante_x, atacante_y, altura):
        angulo = atan2(y - atacante_y, x - atacante_x) + uniform(-0.5, 0.5)
        distancia = uniform(120, 180)

        destino_x = x + cos(angulo) * distancia
        destino_y = y + sin(angulo) * distancia
        return self.ajustar_posicao(destino_x, destino_y, altura)

    def ajustar_posicao(self, x, y, altura):
        if self.pode_andar(x, y, altura):
            return x, y
        return self._procurar_grama_mais_proxima(x, y, altura)

    def limitar_movimento(self, x0, y0, x1, y1, altura, distancia_maxima=None):
        if self._caminho_livre(x0, y0, x1, y1, altura) and self.pode_andar(
            x1, y1, altura
        ):
            return self._limitar_distancia(x0, y0, x1, y1, distancia_maxima)

        passo = min(distancia_maxima, 48.0) if distancia_maxima is not None else 48.0
        ponto = self.obter_ponto_rota(x0, y0, x1, y1, altura, distancia_maxima=passo)

        if ponto:
            return self._limitar_distancia(x0, y0, ponto[0], ponto[1], distancia_maxima)
        return None

    def destino_aleatorio(self, max_tentativas=200):
        for _ in range(max_tentativas):
            ponto = self._escolher_ponto_grama()
            if ponto:
                return ponto
        return 0, 0

    def ponto_aleatorio_no_raio(
        self, x, y, altura, dist_min, dist_max, max_tentativas=100
    ):
        for _ in range(max_tentativas):
            xx = randint(int(x - dist_max), int(x + dist_max))
            yy = randint(int(y - dist_max), int(y + dist_max))

            if dist_min <= hypot(xx - x, yy - y) <= dist_max and self.pode_andar(
                xx, yy, altura
            ):
                return xx, yy

        return self._procurar_grama_mais_proxima(x, y, altura)

    def _escolher_ponto_grama(self):
        return choice(self.pontos_grama) if self.pontos_grama else None

    def _procurar_grama_mais_proxima(self, x, y, altura):
        col, lin = self.tilemap.pixel_para_tile(x, y)

        for raio in range(1, 8):
            for dx in range(-raio, raio + 1):
                for dy in range(-raio, raio + 1):
                    c, lin = col + dx, lin + dy
                    if self.tilemap.pode_andar(c, lin, altura):
                        px, py = self.tilemap.tile_para_pixel(c, lin)
                        return px + TILE_SIZE // 2, py + TILE_SIZE // 2
        return None

    def obter_ponto_rota(
        self, origem_x, origem_y, destino_x, destino_y, altura, distancia_maxima=None
    ):
        rota = self.calcular_rota(origem_x, origem_y, destino_x, destino_y, altura)
        if not rota:
            return None
        if distancia_maxima is None:
            return rota[0]

        for ponto in rota:
            if hypot(ponto[0] - origem_x, ponto[1] - origem_y) <= distancia_maxima:
                return ponto
        return rota[0]

    def encontrar_desvio(
        self, origem_x, origem_y, destino_x, destino_y, altura, distancia_maxima=None
    ):
        limite = max(
            16.0,
            float(
                distancia_maxima or hypot(destino_x - origem_x, destino_y - origem_y)
            ),
        )

        orig_c, orig_l = self.tilemap.pixel_para_tile(origem_x, origem_y)
        dest_c, dest_l = self.tilemap.pixel_para_tile(destino_x, destino_y)

        rota = self._calcular_rota_grade(orig_c, orig_l, dest_c, dest_l, altura)
        if not rota:
            return self.ajustar_posicao(destino_x, destino_y, altura)

        for col, lin in rota:
            xx, yy = self._ponto_para_tile_seguro(col, lin, altura)
            if 24 <= hypot(xx - origem_x, yy - origem_y) <= limite:
                nova_altura = self.obter_altura_transicao(
                    origem_x, origem_y, xx, yy, altura
                )
                if self.calcular_rota(
                    xx, yy, destino_x, destino_y, nova_altura or altura
                ):
                    return xx, yy

        ultimo_c, ultimo_l = rota[-1]
        ponto = self._ponto_para_tile_seguro(ultimo_c, ultimo_l, altura)

        if self.tilemap.eh_degrau(ultimo_c, ultimo_l):
            return ponto
        return self.ajustar_posicao(ponto[0], ponto[1], altura)

    def _ponto_para_tile_seguro(self, coluna, linha, altura):
        if self.tilemap.eh_degrau(coluna, linha):
            return self._ponto_central_degrau(coluna, linha)

        xx, yy = self.tilemap.tile_para_pixel(coluna, linha)
        centro_x, centro_y = xx + TILE_SIZE // 2, yy + TILE_SIZE // 2
        margem = max(20, TILE_SIZE // 3)
        desloc_x = desloc_y = 0.0

        for dx, dy in DIRECOES_8:
            vizinho = (coluna + dx, linha + dy)
            nao_caminhavel = (
                not self.tilemap.pode_andar(*vizinho, altura)
                and self.tilemap.obter_transicao_degrau(
                    coluna, linha, vizinho[0], vizinho[1], altura
                )
                is None
            )

            if nao_caminhavel:
                desloc_x -= margem if dx > 0 else (-margem if dx < 0 else 0)
                desloc_y -= margem if dy > 0 else (-margem if dy < 0 else 0)

        x = min(max(centro_x + desloc_x, xx + margem), xx + TILE_SIZE - margem)
        y = min(max(centro_y + desloc_y, yy + margem), yy + TILE_SIZE - margem)
        return x, y

    def _limitar_distancia(self, x0, y0, x1, y1, distancia_maxima=None):
        if distancia_maxima is None or hypot(x1 - x0, y1 - y0) <= distancia_maxima:
            return x1, y1
        angulo = atan2(y1 - y0, x1 - x0)
        return x0 + cos(angulo) * distancia_maxima, y0 + sin(angulo) * distancia_maxima

    def _caminho_livre(self, x0, y0, x1, y1, altura):
        passos = max(1, int(hypot(x1 - x0, y1 - y0) / 16))
        for i in range(passos + 1):
            t = i / passos
            if not self.pode_andar(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, altura):
                return False
        return True

    def _ponto_central_degrau(self, coluna, linha):
        x, y = self.tilemap.tile_para_pixel(coluna, linha)
        return x + TILE_SIZE // 2, y

    def _esta_em_grade(self, coluna, linha):
        return isinstance(coluna, int) and isinstance(linha, int)

    def _buscar_caminho_base(
        self, origem, destino, altura_inicial, direcoes, nivelar_destino=False
    ):
        if not self.tilemap._coordenada_valida(*destino):
            return []

        altura_dest = self.tilemap.obter_altura(*destino)

        # AQUI ESTAVA O PROBLEMA: a regra de nivelar só deve se aplicar à grade!
        if (
            nivelar_destino
            and altura_dest != altura_inicial
            and not self.tilemap.eh_degrau(*destino)
        ):
            altura_dest = altura_inicial

        estado_inicial = (*origem, altura_inicial)
        fila = deque([estado_inicial])
        veio_de = {estado_inicial: None}
        estado_destino = None

        while fila:
            c_atual, l_atual, alt_atual = fila.popleft()

            if (c_atual, l_atual) == destino and alt_atual == altura_dest:
                estado_destino = (c_atual, l_atual, alt_atual)
                break

            for dx, dy in direcoes:
                c_vizinho, l_vizinho = c_atual + dx, l_atual + dy
                if not self.tilemap._coordenada_valida(c_vizinho, l_vizinho):
                    continue

                nova_alt = self.tilemap.obter_transicao_degrau(
                    c_atual, l_atual, c_vizinho, l_vizinho, alt_atual
                )
                alt_vizinho = nova_alt if nova_alt is not None else alt_atual

                if nova_alt is None and not self.tilemap.pode_andar(
                    c_vizinho, l_vizinho, alt_vizinho
                ):
                    continue

                novo_estado = (c_vizinho, l_vizinho, alt_vizinho)
                if novo_estado not in veio_de:
                    veio_de[novo_estado] = (c_atual, l_atual, alt_atual)
                    fila.append(novo_estado)

        if not estado_destino:
            return []

        rota, atual = [], estado_destino
        while atual != estado_inicial:
            rota.append(atual)
            atual = veio_de[atual]

        return rota[::-1]

    def _calcular_rota_grade(
        self, origem_coluna, origem_linha, destino_coluna, destino_linha, altura
    ):
        rota_bruta = self._buscar_caminho_base(
            (origem_coluna, origem_linha),
            (destino_coluna, destino_linha),
            altura,
            DIRECOES_4,
            nivelar_destino=True,
        )
        return [(c, lin) for c, lin, _ in rota_bruta]

    def calcular_rota(self, origem_x, origem_y, destino_x, destino_y, altura):
        origem = self.tilemap.pixel_para_tile(origem_x, origem_y)
        destino = self.tilemap.pixel_para_tile(destino_x, destino_y)

        rota_bruta = self._buscar_caminho_base(
            origem,
            destino,
            altura,
            DIRECOES_8,
            nivelar_destino=False,  # Já para calcular rota livre, mantém a altura real
        )

        rota_final = []
        for col, lin, _ in rota_bruta:
            if self.tilemap.eh_degrau(col, lin):
                rota_final.append(self._ponto_central_degrau(col, lin))
            else:
                x, y = self.tilemap.tile_para_pixel(col, lin)
                rota_final.append((x + TILE_SIZE // 2, y + TILE_SIZE // 2))

        return rota_final
