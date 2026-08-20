from collections import deque
from math import atan2, cos, hypot, sin
from random import choice, randint, uniform

from utils.config import TILE_SIZE

DIRECOES_4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIRECOES_8 = DIRECOES_4 + ((1, 1), (-1, -1), (1, -1), (-1, 1))


class NavegacaoMapa:
    RAIO_COLISAO_CONSTRUCAO = 8

    def __init__(self, tilemap, obter_obstaculos=None):
        self.tilemap = tilemap
        self._obter_obstaculos = obter_obstaculos or (lambda: ())
        # Obstáculos dinâmicos e rotas são cacheados para evitar recalcular
        # Rects de sprites e BFS repetidamente durante o mesmo trajeto.
        self._obstaculos_cache = ()
        self._assinatura_obstaculos = None
        self._versao_obstaculos = 0
        self._cache_rotas = {}
        self._cache_desvios = {}
        self._cache_rotas_limite = 256
        self._cache_desvios_limite = 128

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
            self._cache_desvios.clear()

    def invalidar_cache_rotas(self):
        self._cache_rotas.clear()
        self._cache_desvios.clear()
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

    def encontrar_ponto_acessivel_proximo(
        self,
        origem_x,
        origem_y,
        alvo_x,
        alvo_y,
        altura,
        distancia=45.0,
        candidatos_extra=(),
        distancia_maxima_alvo=None,
        exigir_linha_livre_ate_alvo=False,
    ):
        """
        Encontra um ponto caminhável próximo de um alvo que também seja
        alcançável a partir da posição atual.

        Evita que o destino de ataque/coleta caia dentro de uma construção
        quando o alvo estiver encostado nela.
        """
        diagonais = distancia / (2**0.5)
        candidatos = [
            (alvo_x - distancia, alvo_y),
            (alvo_x + distancia, alvo_y),
            (alvo_x, alvo_y - distancia),
            (alvo_x, alvo_y + distancia),
            (alvo_x - diagonais, alvo_y - diagonais),
            (alvo_x + diagonais, alvo_y - diagonais),
            (alvo_x - diagonais, alvo_y + diagonais),
            (alvo_x + diagonais, alvo_y + diagonais),
        ]

        # Quando um item dropa encostado em uma construção, os oito pontos
        # radiais acima podem cair todos dentro da área bloqueada. Nesse caso
        # usamos a própria borda dos obstáculos como área de interação, tal
        # como já fazemos para atacar construções.
        for obstaculo in self._obstaculos_cache:
            distancia_rect_x = max(obstaculo.left - alvo_x, 0, alvo_x - obstaculo.right)
            distancia_rect_y = max(obstaculo.top - alvo_y, 0, alvo_y - obstaculo.bottom)
            if hypot(distancia_rect_x, distancia_rect_y) > distancia + TILE_SIZE:
                continue

            margem = max(8.0, distancia * 0.35)
            candidatos.extend(
                [
                    (
                        obstaculo.left - margem,
                        min(max(alvo_y, obstaculo.top), obstaculo.bottom),
                    ),
                    (
                        obstaculo.right + margem,
                        min(max(alvo_y, obstaculo.top), obstaculo.bottom),
                    ),
                    (
                        min(max(alvo_x, obstaculo.left), obstaculo.right),
                        obstaculo.top - margem,
                    ),
                    (
                        min(max(alvo_x, obstaculo.left), obstaculo.right),
                        obstaculo.bottom + margem,
                    ),
                    (obstaculo.left - margem, obstaculo.top - margem),
                    (obstaculo.right + margem, obstaculo.top - margem),
                    (obstaculo.left - margem, obstaculo.bottom + margem),
                    (obstaculo.right + margem, obstaculo.bottom + margem),
                ]
            )

        candidatos.extend(candidatos_extra)

        validos = []
        vistos = set()

        for x, y in candidatos:
            chave = (round(x), round(y))
            if chave in vistos:
                continue
            vistos.add(chave)

            if (
                distancia_maxima_alvo is not None
                and hypot(x - alvo_x, y - alvo_y) > distancia_maxima_alvo
            ):
                continue

            if exigir_linha_livre_ate_alvo and self.linha_bloqueada_por_obstaculos(
                x, y, alvo_x, alvo_y
            ):
                continue

            col_dest, lin_dest = self.tilemap.pixel_para_tile(x, y)
            alturas_validas = {self.tilemap.obter_altura(col_dest, lin_dest)}
            degrau_dest = self.tilemap.obter_degrau(col_dest, lin_dest)
            if degrau_dest:
                alturas_validas.update(
                    (degrau_dest["altura_baixa"], degrau_dest["altura_alta"])
                )

            if not any(
                self.tilemap.pode_andar(col_dest, lin_dest, alt)
                for alt in alturas_validas
            ):
                continue

            distancia_origem = hypot(x - origem_x, y - origem_y)

            if distancia_origem < 3:
                validos.append((0.0, x, y))
                continue

            rota = self.calcular_rota(
                origem_x,
                origem_y,
                x,
                y,
                altura,
            )

            if not rota:
                if self._caminho_livre(
                    origem_x,
                    origem_y,
                    x,
                    y,
                    altura,
                ):
                    validos.append((distancia_origem, x, y))
                continue

            comprimento_rota = 0.0
            px, py = origem_x, origem_y
            for rx, ry in rota:
                comprimento_rota += hypot(rx - px, ry - py)
                px, py = rx, ry

            validos.append((comprimento_rota + distancia_origem * 0.05, x, y))

        if not validos:
            return None

        _, x, y = min(validos, key=lambda item: item[0])
        return x, y

    @staticmethod
    def distancia_para_rect(x, y, rect):
        dx = max(rect.left - x, 0, x - rect.right)
        dy = max(rect.top - y, 0, y - rect.bottom)
        return hypot(dx, dy)

    def encontrar_ponto_acessivel_ao_redor_rect(
        self,
        origem_x,
        origem_y,
        rect,
        altura,
        margem=45.0,
    ):
        ponto_borda_x = min(max(origem_x, rect.left), rect.right)
        ponto_borda_y = min(max(origem_y, rect.top), rect.bottom)

        dx = origem_x - ponto_borda_x
        dy = origem_y - ponto_borda_y
        comprimento = hypot(dx, dy)

        if comprimento > 0:
            nx = dx / comprimento
            ny = dy / comprimento
        else:
            # Se estiver sobre o centro geométrico, escolha o lado mais curto.
            dist_left = abs(origem_x - rect.left)
            dist_right = abs(rect.right - origem_x)
            dist_top = abs(origem_y - rect.top)
            dist_bottom = abs(rect.bottom - origem_y)
            menor = min(dist_left, dist_right, dist_top, dist_bottom)

            if menor == dist_left:
                nx, ny = -1.0, 0.0
            elif menor == dist_right:
                nx, ny = 1.0, 0.0
            elif menor == dist_top:
                nx, ny = 0.0, -1.0
            else:
                nx, ny = 0.0, 1.0

        # Pequeno conjunto de pontos junto à borda e alguns pontos laterais
        # para permitir contornar a construção quando o lado direto estiver
        # bloqueado por outro obstáculo.
        distancia = max(10.0, margem)
        candidatos = [
            (
                ponto_borda_x + nx * distancia,
                ponto_borda_y + ny * distancia,
            ),
            (rect.left - distancia, rect.centery),
            (rect.right + distancia, rect.centery),
            (rect.centerx, rect.top - distancia),
            (rect.centerx, rect.bottom + distancia),
            (rect.left - distancia, rect.top - distancia),
            (rect.right + distancia, rect.top - distancia),
            (rect.left - distancia, rect.bottom + distancia),
            (rect.right + distancia, rect.bottom + distancia),
        ]

        validos = []
        vistos = set()

        for x, y in candidatos:
            chave = (round(x), round(y))
            if chave in vistos:
                continue
            vistos.add(chave)

            if not self.pode_andar(x, y, altura):
                continue

            distancia_origem = hypot(x - origem_x, y - origem_y)
            rota = self.calcular_rota(
                origem_x,
                origem_y,
                x,
                y,
                altura,
            )

            if not rota:
                if self._caminho_livre(origem_x, origem_y, x, y, altura):
                    validos.append((distancia_origem, x, y))
                continue

            comprimento_rota = 0.0
            px, py = origem_x, origem_y
            for rx, ry in rota:
                comprimento_rota += hypot(rx - px, ry - py)
                px, py = rx, ry

            validos.append((comprimento_rota, x, y))

        if not validos:
            return None

        _, x, y = min(validos, key=lambda item: item[0])
        return x, y

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

        chave_cache = (
            orig_c,
            orig_l,
            dest_c,
            dest_l,
            altura,
            self._versao_obstaculos,
            round(limite),
        )
        if chave_cache in self._cache_desvios:
            return self._cache_desvios[chave_cache]

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
            if len(self._cache_desvios) >= self._cache_desvios_limite:
                self._cache_desvios.pop(next(iter(self._cache_desvios)))
            self._cache_desvios[chave_cache] = melhor
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
                resultado = (xx, yy)
                if len(self._cache_desvios) >= self._cache_desvios_limite:
                    self._cache_desvios.pop(next(iter(self._cache_desvios)))
                self._cache_desvios[chave_cache] = resultado
                return resultado

        resultado = (xx, yy)
        if len(self._cache_desvios) >= self._cache_desvios_limite:
            self._cache_desvios.pop(next(iter(self._cache_desvios)))
        self._cache_desvios[chave_cache] = resultado
        return resultado

    def _ponto_para_tile_seguro(self, coluna, linha, altura):
        if self.tilemap.eh_degrau(coluna, linha):
            return self._ponto_central_degrau(coluna, linha)

        xx, yy = self.tilemap.tile_para_pixel(coluna, linha)
        centro_x, centro_y = xx + TILE_SIZE // 2, yy + TILE_SIZE // 2
        margem = max(8, TILE_SIZE // 8)
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

    def linha_bloqueada_por_obstaculos(self, x0, y0, x1, y1):
        """Retorna True quando um obstáculo bloqueia a linha entre dois pontos."""
        distancia = hypot(x1 - x0, y1 - y0)
        passos = max(1, int(distancia / 6))

        for i in range(passos + 1):
            t = i / passos
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            for obstaculo in self._obstaculos_cache:
                if self._ponto_colide_com_obstaculo(x, y, obstaculo, 0):
                    return True

        return False

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

        # Uma célula de degrau representa os dois lados do relevo. O destino
        # não pode ser preso arbitrariamente à altura 0 da célula, senão uma
        # rota que precisa terminar no lado alto parece inexistente.
        alturas_destino = {self.tilemap.obter_altura(*destino)}
        degrau_destino = self.tilemap.obter_degrau(*destino)
        if degrau_destino:
            alturas_destino.update(
                (
                    degrau_destino["altura_baixa"],
                    degrau_destino["altura_alta"],
                )
            )

        # Para destinos de chão normal, mantém o comportamento de nivelar a
        # célula ao nível da unidade quando solicitado.
        if nivelar_destino and not degrau_destino:
            alturas_destino = {altura_inicial}

        estado_inicial = (*origem, altura_inicial)
        fila = deque([estado_inicial])
        veio_de = {estado_inicial: None}
        estado_destino = None

        while fila:
            c_atual, l_atual, alt_atual = fila.popleft()

            if (c_atual, l_atual) == destino and alt_atual in alturas_destino:
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
            DIRECOES_4,
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
