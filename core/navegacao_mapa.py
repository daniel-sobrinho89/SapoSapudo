from collections import deque
from math import atan2, cos, hypot, sin
from random import choice, randint, uniform

from utils.config import TILE_SIZE

DIRECOES_4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIRECOES_8 = DIRECOES_4 + ((1, 1), (-1, -1), (1, -1), (-1, 1))


class NavegacaoMapa:
    RAIO_COLISAO_CONSTRUCAO = 20

    def __init__(self, tilemap, obter_obstaculos=None):
        self.tilemap = tilemap
        self._obter_obstaculos = obter_obstaculos or (lambda: ())
        # Obstáculos dinâmicos e rotas são cacheados para evitar recalcular
        # Rects de sprites e BFS repetidamente durante o mesmo trajeto.
        self._obstaculos_cache = ()
        self._assinatura_obstaculos = None
        self._versao_obstaculos = 0
        self._cache_rotas = {}
        self._cache_rotas_limite = 256

        self.pontos_grama = [
            (
                self.tilemap.tile_para_pixel(c, lin)[0] + TILE_SIZE // 2,
                self.tilemap.tile_para_pixel(c, lin)[1] + TILE_SIZE // 2,
            )
            for lin in range(self.tilemap.altura)
            for c in range(self.tilemap.largura)
            if self.tilemap.pode_andar_pixel(
                self.tilemap.tile_para_pixel(c, lin)[0] + TILE_SIZE // 2,
                self.tilemap.tile_para_pixel(c, lin)[1] + TILE_SIZE // 2,
                0,
            )
        ]

    def definir_obter_obstaculos(self, obter_obstaculos):
        self._obter_obstaculos = obter_obstaculos or (lambda: ())

    def atualizar_obstaculos(self):
        obstaculos = tuple(self._obter_obstaculos())
        assinatura = tuple(
            (
                getattr(r, "left", 0),
                getattr(r, "top", 0),
                getattr(r, "right", 0),
                getattr(r, "bottom", 0),
            )
            for r in obstaculos
        )
        if assinatura != self._assinatura_obstaculos:
            self._assinatura_obstaculos = assinatura
            self._obstaculos_cache = obstaculos
            self._versao_obstaculos += 1
            self._cache_rotas.clear()

    def invalidar_cache_rotas(self):
        self._cache_rotas.clear()
        self._assinatura_obstaculos = None

    def pode_andar(self, x, y, altura):
        if not self.tilemap.pode_andar_pixel(x, y, altura):
            return False

        margem = self.RAIO_COLISAO_CONSTRUCAO
        obstaculos = self._obstaculos_cache
        if not obstaculos:
            # Compatibilidade para chamadas isoladas fora do ciclo normal.
            obstaculos = tuple(self._obter_obstaculos())
            self._obstaculos_cache = obstaculos
        for obstaculo in obstaculos:
            if self._ponto_colide_com_obstaculo(x, y, obstaculo, margem):
                return False

        return True

    @staticmethod
    def _ponto_colide_com_obstaculo(x, y, obstaculo, margem):
        esquerda = obstaculo.left - margem
        direita = obstaculo.right + margem
        topo = obstaculo.top - margem
        base = obstaculo.bottom + margem
        return esquerda <= x < direita and topo <= y < base

    def obter_altura_transicao(self, origem_x, origem_y, destino_x, destino_y, altura):
        """
        Resolve transições de altura atravessadas durante um único movimento.

        O movimento de uma unidade pode atravessar mais de uma fronteira de
        tile em um frame. Verificar somente o tile inicial e final faz a
        unidade perder a mudança de altura quando o degrau fica no meio do
        segmento.
        """
        distancia = hypot(destino_x - origem_x, destino_y - origem_y)
        passos = max(1, int(distancia / 8))

        altura_atual = altura
        x_anterior, y_anterior = origem_x, origem_y
        coluna_anterior, linha_anterior = self.tilemap.pixel_para_tile(
            x_anterior, y_anterior
        )

        for indice in range(1, passos + 1):
            t = indice / passos
            x_atual = origem_x + (destino_x - origem_x) * t
            y_atual = origem_y + (destino_y - origem_y) * t
            coluna_atual, linha_atual = self.tilemap.pixel_para_tile(x_atual, y_atual)

            if (coluna_atual, linha_atual) != (
                coluna_anterior,
                linha_anterior,
            ):
                nova_altura = self.tilemap.obter_transicao_degrau(
                    coluna_anterior,
                    linha_anterior,
                    coluna_atual,
                    linha_atual,
                    altura_atual,
                )
                if nova_altura is not None:
                    altura_atual = nova_altura

            coluna_anterior, linha_anterior = coluna_atual, linha_atual
            x_anterior, y_anterior = x_atual, y_atual

        return altura_atual if altura_atual != altura else None

    def fugir(self, x, y, atacante_x, atacante_y, altura):
        angulo = atan2(y - atacante_y, x - atacante_x) + uniform(-0.5, 0.5)
        distancia = uniform(120, 180)

        destino_x = x + cos(angulo) * distancia
        destino_y = y + sin(angulo) * distancia

        destino = self.ajustar_posicao(destino_x, destino_y, altura)

        return destino if destino is not None else (x, y)

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
        if not self.pontos_grama:
            return None

        # Obstáculos podem surgir depois da criação do mapa, portanto a lista
        # pré-calculada é apenas um conjunto de candidatos. A validação final
        # usa a regra atual.
        candidatos = [
            ponto for ponto in self.pontos_grama if self.pode_andar(*ponto, 0)
        ]
        return choice(candidatos) if candidatos else None

    def _procurar_grama_mais_proxima(self, x, y, altura):
        col, lin = self.tilemap.pixel_para_tile(x, y)

        for raio in range(1, 8):
            for dx in range(-raio, raio + 1):
                for dy in range(-raio, raio + 1):
                    c, lin = col + dx, lin + dy
                    px, py = self.tilemap.tile_para_pixel(c, lin)
                    cx, cy = px + TILE_SIZE // 2, py + TILE_SIZE // 2
                    if self.pode_andar(cx, cy, altura):
                        return cx, cy
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

        # Um único BFS. A implementação anterior fazia um novo BFS completo
        # para praticamente cada ponto da rota encontrada.
        rota = self._calcular_rota_grade(orig_c, orig_l, dest_c, dest_l, altura)
        if not rota:
            return self.ajustar_posicao(destino_x, destino_y, altura)

        melhor = None
        for col, lin in rota:
            xx, yy = self._ponto_para_tile_seguro(col, lin, altura)
            distancia = hypot(xx - origem_x, yy - origem_y)
            if distancia < 24:
                continue
            if distancia <= limite:
                melhor = (xx, yy)
                break

        if melhor is not None:
            return melhor

        # Quando o primeiro tile da rota está além do passo máximo, avança
        # somente até o limite permitido, sem recalcular outra rota.
        col, lin = rota[0]
        xx, yy = self._ponto_para_tile_seguro(col, lin, altura)
        distancia = hypot(xx - origem_x, yy - origem_y)
        if distancia > limite:
            proporcao = limite / distancia
            xx = origem_x + (xx - origem_x) * proporcao
            yy = origem_y + (yy - origem_y) * proporcao
            if self.pode_andar(xx, yy, altura):
                return xx, yy

        return xx, yy

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
                not self.pode_andar(
                    *self._centro_do_tile(vizinho[0], vizinho[1]),
                    altura,
                )
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
        passos = max(1, int(hypot(x1 - x0, y1 - y0) / 32))
        for i in range(passos + 1):
            t = i / passos
            if not self.pode_andar(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, altura):
                return False
        return True

    def _centro_do_tile(self, coluna, linha):
        x, y = self.tilemap.tile_para_pixel(coluna, linha)
        return x + TILE_SIZE // 2, y + TILE_SIZE // 2

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

                if nova_alt is None and not self.pode_andar(
                    *self._centro_do_tile(c_vizinho, l_vizinho),
                    alt_vizinho,
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

        chave = (
            origem[0],
            origem[1],
            destino[0],
            destino[1],
            altura,
            self._versao_obstaculos,
        )
        rota_cache = self._cache_rotas.get(chave)
        if rota_cache is not None:
            return rota_cache

        rota_bruta = self._buscar_caminho_base(
            origem,
            destino,
            altura,
            DIRECOES_8,
            nivelar_destino=False,
        )

        rota_final = []
        for col, lin, _ in rota_bruta:
            if self.tilemap.eh_degrau(col, lin):
                rota_final.append(self._ponto_central_degrau(col, lin))
            else:
                x, y = self.tilemap.tile_para_pixel(col, lin)
                rota_final.append((x + TILE_SIZE // 2, y + TILE_SIZE // 2))

        if len(self._cache_rotas) >= self._cache_rotas_limite:
            self._cache_rotas.pop(next(iter(self._cache_rotas)))
        self._cache_rotas[chave] = rota_final
        return rota_final
