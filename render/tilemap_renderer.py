from utils.config import TILE_SIZE


class TileMapRenderer:
    TIPO_GRAMA = "grama"
    TIPO_AGUA = "agua"
    TIPO_ROCHA = "rocha"
    TIPO_VAZIO = None

    def __init__(self, tela, assets, transform):
        self.tela = tela
        self.assets = assets
        self.transform = transform

        self.carregado = False

        self.tiles = []

        self.mapa = []

        self.largura = 0
        self.altura = 0
        self.offset_y = 0
        self.frame_agua = 1
        self.tempo_agua = 0.0
        self.offset_agua_parada_x = -1
        self.offset_agua_parada_y = 85

        self._carregar_mapa(self.floresta())

    @staticmethod
    def floresta():
        largura = 24
        altura = 11

        return [
            [
                {
                    "tipo": TileMapRenderer.TIPO_GRAMA,
                    "altura": 1,
                }
                for _ in range(largura)
            ]
            for _ in range(altura)
        ]

    @staticmethod
    def vila_goblin():
        return [
            ["grama"] * 24,
            ["grama"] * 24,
            ["grama"] * 24,
        ]

    # ==================================================
    # LOAD
    # ==================================================

    def atualizar_carregamento(self):
        if self.carregado:
            return

        self.agua_parada = self.assets.carregar("background/agua_parada.png")

        spritesheet_agua = self.assets.carregar("background/agua.png")

        agua = self.transform.recortar_spritesheet(
            spritesheet_agua,
            linhas=1,
            colunas=16,
        )

        self.tiles_agua = agua

        spritesheet = self.assets.carregar("background/chao1.png")

        colunas = spritesheet.get_width() // TILE_SIZE
        linhas = spritesheet.get_height() // TILE_SIZE

        tiles = self.transform.recortar_spritesheet(
            spritesheet,
            linhas=linhas,
            colunas=colunas,
        )

        self.tiles = {
            #
            # topo
            #
            1: tiles[0],
            2: tiles[1],
            3: tiles[2],
            4: tiles[9],
            5: tiles[10],
            6: tiles[11],
            7: tiles[18],
            8: tiles[19],
            9: tiles[20],
            #
            # horizontal
            #
            10: tiles[27],
            11: tiles[28],
            12: tiles[29],
            #
            # vertical
            #
            13: tiles[3],
            14: tiles[12],
            15: tiles[21],
            16: tiles[30],
            #
            # penhasco
            #
            17: tiles[41],
            18: tiles[42],
            19: tiles[43],
            20: tiles[44],
            21: tiles[50],
            22: tiles[51],
            23: tiles[52],
            24: tiles[53],
            #
            # topo penhasco
            #
            25: tiles[23],
            26: tiles[24],
            27: tiles[25],
        }

        self.carregado = True

    # ==================================================
    # MAPA
    # ==================================================

    def _carregar_mapa(self, mapa):
        self.mapa = mapa
        self.altura = len(mapa)
        self.largura = len(mapa[0]) if mapa else 0
        self.offset_y = self.altura - 96
        self.offset_x = -60

    # ==================================================
    # CONSULTAS
    # ==================================================

    def obter_tipo(self, coluna, linha):
        if coluna < 0 or coluna >= self.largura:
            return self.TIPO_AGUA

        if linha < 0 or linha >= self.altura:
            return self.TIPO_AGUA

        tile = self.mapa[linha][coluna]

        if tile is None:
            return None

        if isinstance(tile, str):
            return tile

        return tile["tipo"]

    def obter_altura(self, coluna, linha):
        if coluna < 0:
            return 0

        if linha < 0:
            return 0

        if coluna >= self.largura:
            return 0

        if linha >= self.altura:
            return 0

        tile = self.mapa[linha][coluna]

        if tile is None:
            return 0

        if isinstance(tile, str):
            return 0

        return tile.get("altura", 0)

    def mesma_altura(self, coluna1, linha1, coluna2, linha2):
        return self.obter_altura(coluna1, linha1) == self.obter_altura(coluna2, linha2)

    def existe_grama(self, coluna, linha):
        return (
            0 <= coluna < self.largura
            and 0 <= linha < self.altura
            and self.obter_tipo(coluna, linha) == self.TIPO_GRAMA
        )

    def eh_grama(self, x, y):
        coluna, linha = self.pixel_para_tile(x, y)

        return self.pode_andar(
            coluna,
            linha,
        )

    def pode_andar(self, coluna, linha):
        if self.obter_tipo(coluna, linha) != self.TIPO_GRAMA:
            return False

        return not self.existe_penhasco(coluna, linha)

    # ==================================================
    # PIXEL
    # ==================================================

    def pixel_para_tile(self, x, y):
        coluna = int((x - self.offset_x) // TILE_SIZE)
        linha = int((y - self.offset_y) // TILE_SIZE)

        return coluna, linha

    def tile_para_pixel(self, coluna, linha):
        return (
            self.offset_x + coluna * TILE_SIZE,
            self.offset_y + linha * TILE_SIZE,
        )

    # ==================================================
    # AUTOTILE
    # ==================================================

    def tem_grama_vizinha(self, coluna, linha):
        # Verifica vizinhos diretos (cruz) e diagonais para incluir as quinas
        for dx, dy in [
            (0, -1),
            (0, 1),
            (-1, 0),
            (1, 0),
            (1, 1),
            (-1, 1),
            (1, -1),
            (-1, -1),
        ]:
            if self.obter_tipo(coluna + dx, linha + dy) == self.TIPO_GRAMA:
                return True
        return False

    def tem_vizinho_agua(self, coluna, linha):
        # Mesma lógica da cruz para a água
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            if self.obter_tipo(coluna + dx, linha + dy) == self.TIPO_AGUA:
                return True
        return False

    def existe_penhasco(self, coluna, linha):
        if self.obter_tipo(coluna, linha) != self.TIPO_GRAMA:
            return False

        return self.obter_altura(coluna, linha) > self.obter_altura(coluna, linha + 1)

    def atualizar_animacao_agua(self, dt):
        self.tempo_agua += dt

        if self.tempo_agua < 0.08:
            return

        self.tempo_agua = 0
        self.frame_agua += 1

        if self.frame_agua > len(self.tiles_agua):
            self.frame_agua = 1

    def obter_sprite(self, coluna, linha):
        tipo = self.obter_tipo(coluna, linha)

        if tipo is None:
            return None

        if tipo == self.TIPO_AGUA:
            return self.obter_sprite_agua(coluna, linha)

        if tipo != self.TIPO_GRAMA:
            return None

        v = self.obter_vizinhos(coluna, linha, tipo)

        n = v["n"]
        s = v["s"]
        e = v["e"]
        w = v["w"]

        ne = v["ne"]
        nw = v["nw"]
        se = v["se"]
        sw = v["sw"]

        #
        # ilha
        #

        if not n and not s and not e and not w:
            return self.tiles[16]

        #
        # topo
        #

        if not n:
            if not w:
                return self.tiles[1]

            if not e:
                return self.tiles[3]

            return self.tiles[2]

        #
        # base
        #

        if not s:
            if self.existe_penhasco(coluna, linha):
                return self.obter_sprite_topo_penhasco(
                    coluna,
                    linha,
                )

            if not w:
                return self.tiles[7]

            if not e:
                return self.tiles[9]

            return self.tiles[8]

        #
        # esquerda
        #

        if not w:
            return self.tiles[4]

        #
        # direita
        #

        if not e:
            return self.tiles[6]

        #
        # cantos internos
        #

        if not nw:
            return self.tiles[13]

        if not ne:
            return self.tiles[14]

        if not sw:
            return self.tiles[15]

        if not se:
            return self.tiles[16]

        #
        # centro
        #

        return self.tiles[5]

    def obter_sprite_topo_penhasco(self, coluna, linha):
        v = self.obter_vizinhos_penhasco(
            coluna,
            linha,
        )

        w = v["w"]
        e = v["e"]

        if not w and not e:
            return self.tiles[26]

        if not w:
            return self.tiles[25]

        if not e:
            return self.tiles[27]

        return self.tiles[26]

    def obter_sprite_agua(self, coluna, linha):
        if self.tem_grama_vizinha(coluna, linha):
            return self.tiles_agua[self.frame_agua - 1]

        return None

    def obter_sprite_coluna(self, coluna, linha):
        v = self.obter_vizinhos_penhasco(
            coluna,
            linha,
        )

        w = v["w"]
        e = v["e"]

        if not w and not e:
            return self.tiles[24]

        if not w:
            return self.tiles[21]

        if not e:
            return self.tiles[23]

        return self.tiles[22]

    def obter_vizinhos(self, coluna, linha, tipo):
        def igual(col, lin):
            return self.obter_tipo(col, lin) == tipo

        return {
            "n": igual(coluna, linha - 1),
            "ne": igual(coluna + 1, linha - 1),
            "e": igual(coluna + 1, linha),
            "se": igual(coluna + 1, linha + 1),
            "s": igual(coluna, linha + 1),
            "sw": igual(coluna - 1, linha + 1),
            "w": igual(coluna - 1, linha),
            "nw": igual(coluna - 1, linha - 1),
        }

    def obter_vizinhos_penhasco(self, coluna, linha):
        return {
            "w": self.existe_penhasco(coluna - 1, linha),
            "e": self.existe_penhasco(coluna + 1, linha),
        }

    def desenhar_agua(self, coluna, linha, camera):
        if self.existe_grama(coluna, linha):
            return

        if not self.tem_grama_vizinha(coluna, linha):
            return

        sprite = self.tiles_agua[self.frame_agua - 1]

        x = self.offset_x + coluna * TILE_SIZE - camera.x
        y = self.offset_y + linha * TILE_SIZE - camera.y

        self.tela.blit(
            sprite,
            (
                x,
                y,
            ),
        )

    # ==================================================
    # RENDER
    # ==================================================

    def renderizar(self, dt, camera):
        if not self.carregado:
            return

        self.atualizar_animacao_agua(dt)
        self.renderizar_fundo(camera)

        inicio_x = max(-2, int((camera.x - self.offset_x) // TILE_SIZE) - 2)
        fim_x = min(
            self.largura + 2,
            int((camera.x + camera.largura - self.offset_x) // TILE_SIZE) + 3,
        )

        inicio_y = max(-2, int((camera.y - self.offset_y) // TILE_SIZE) - 2)
        fim_y = min(
            self.altura + 3,
            int((camera.y + camera.altura - self.offset_y) // TILE_SIZE) + 4,
        )

        # 1. Desenha a espuma tanto sob as bordas da grama quanto na água ao redor
        for linha in range(inicio_y, fim_y):
            for coluna in range(inicio_x, fim_x):
                tipo = self.obter_tipo(coluna, linha)
                desenhar_espuma = False

                if tipo == self.TIPO_AGUA:
                    # Água vizinha da terra
                    if self.tem_grama_vizinha(
                        coluna, linha
                    ) and not self.existe_penhasco(coluna, linha - 1):
                        desenhar_espuma = True
                elif tipo == self.TIPO_GRAMA and (
                    self.tem_vizinho_agua(coluna, linha)
                    and self.obter_tipo(coluna + 1, linha) != self.TIPO_AGUA
                ):
                    desenhar_espuma = True

                if desenhar_espuma:
                    sprite = self.tiles_agua[self.frame_agua - 1]
                    x = self.offset_x + coluna * TILE_SIZE - camera.x
                    y = self.offset_y + linha * TILE_SIZE - camera.y

                    self.tela.blit(sprite, (x, y))

        # 2. Desenha todos os tiles de grama por cima da espuma
        for linha in range(inicio_y, fim_y):
            for coluna in range(inicio_x, fim_x):
                if self.obter_tipo(coluna, linha) == self.TIPO_GRAMA:
                    sprite = self.obter_sprite(coluna, linha)
                    if sprite is not None:
                        x = self.offset_x + coluna * TILE_SIZE - camera.x
                        y = self.offset_y + linha * TILE_SIZE - camera.y
                        self.tela.blit(sprite, (x, y))

        # 3. Desenha os sprites de penhasco
        for linha in range(inicio_y, fim_y):
            for coluna in range(inicio_x, fim_x):
                if self.existe_penhasco(coluna, linha):
                    sprite = self.obter_sprite_coluna(coluna, linha)
                    if sprite is not None:
                        x = self.offset_x + coluna * TILE_SIZE - camera.x
                        y = self.offset_y + linha * TILE_SIZE - camera.y
                        self.tela.blit(sprite, (x, y + TILE_SIZE))

    def renderizar_fundo(self, camera):
        sprite = self.agua_parada

        largura = sprite.get_width()
        altura = sprite.get_height()

        inicio_x = int(camera.x // largura) - 1
        fim_x = int((camera.x + camera.largura) // largura) + 2

        inicio_y = int(camera.y // altura) - 1
        fim_y = int((camera.y + camera.altura) // altura) + 2

        for y in range(inicio_y, fim_y):
            for x in range(inicio_x, fim_x):
                self.tela.blit(
                    sprite,
                    (
                        x * largura - camera.x,
                        y * altura - camera.y,
                    ),
                )
