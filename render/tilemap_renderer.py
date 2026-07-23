class TileMapRenderer:
    TILE_SIZE = 64

    TIPO_GRAMA = "grama"
    TIPO_AGUA = "agua"
    TIPO_ROCHA = "rocha"

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
        return [
            ["agua"] * 17,
            ["agua"] * 18,
            [
                "agua",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "agua",
            ],
            [
                "agua",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "agua",
            ],
            [
                "agua",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "agua",
            ],
            [
                "agua",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "grama",
                "agua",
            ],
        ]

    @staticmethod
    def feira():
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

        self.tiles_agua = {
            1: agua[0],
            2: agua[1],
            3: agua[2],
            4: agua[3],
            5: agua[4],
            6: agua[5],
            7: agua[6],
            8: agua[7],
            9: agua[8],
            10: agua[9],
            11: agua[10],
            12: agua[11],
            13: agua[12],
            14: agua[13],
            15: agua[14],
            16: agua[15],
        }

        spritesheet = self.assets.carregar("background/chao1.png")

        colunas = spritesheet.get_width() // self.TILE_SIZE
        linhas = spritesheet.get_height() // self.TILE_SIZE

        tiles = self.transform.recortar_spritesheet(
            spritesheet,
            linhas=linhas,
            colunas=colunas,
        )

        self.tiles = {
            1: tiles[0],
            2: tiles[1],
            3: tiles[2],
            4: tiles[9],
            5: tiles[10],
            6: tiles[11],
            7: tiles[18],
            8: tiles[19],
            9: tiles[20],
            10: tiles[27],
            11: tiles[28],
            12: tiles[29],
            13: tiles[3],
            14: tiles[12],
            15: tiles[21],
            16: tiles[30],
        }

        self.carregado = True

    # ==================================================
    # MAPA
    # ==================================================

    def _carregar_mapa(self, mapa):
        self.mapa = mapa
        self.altura = len(mapa)
        self.largura = len(mapa[0]) if mapa else 0
        self.offset_y = self.altura + 220
        self.offset_x = -60

    # ==================================================
    # CONSULTAS
    # ==================================================

    def obter_tipo(self, coluna, linha):
        if coluna < 0:
            return None

        if linha < 0:
            return None

        if coluna >= self.largura:
            return None

        if linha >= self.altura:
            return None

        return self.mapa[linha][coluna]

    def eh_grama(self, x, y):
        coluna, linha = self.pixel_para_tile(x, y)

        return self.pode_andar(
            coluna,
            linha,
        )

    def pode_andar(self, coluna, linha):
        tipo = self.obter_tipo(coluna, linha)

        if tipo is None:
            return False

        return tipo == self.TIPO_GRAMA

    # ==================================================
    # PIXEL
    # ==================================================

    def pixel_para_tile(self, x, y):
        coluna = int((x - self.offset_x) // self.TILE_SIZE)
        linha = int((y - self.offset_y) // self.TILE_SIZE)

        return coluna, linha

    def tile_para_pixel(self, coluna, linha):
        return (coluna * self.TILE_SIZE, linha * self.TILE_SIZE)

    # ==================================================
    # AUTOTILE
    # ==================================================

    def obter_sprite(self, coluna, linha):
        tipo = self.obter_tipo(coluna, linha)

        if tipo is None:
            return None

        if tipo == self.TIPO_AGUA:
            return self.obter_sprite_agua(coluna, linha)
        elif tipo == self.TIPO_ROCHA:
            return self.tiles[40]

        n = self.obter_tipo(coluna, linha - 1) == tipo
        s = self.obter_tipo(coluna, linha + 1) == tipo
        w = self.obter_tipo(coluna - 1, linha) == tipo
        e = self.obter_tipo(coluna + 1, linha) == tipo

        # ------------------------------------
        # Ilha
        # ------------------------------------

        if not n and not s and not w and not e:
            return self.tiles[16]  # 16

        # ------------------------------------
        # Linha superior
        # ------------------------------------

        if not n:
            if not w:
                return self.tiles[1]  # 1

            if not e:
                return self.tiles[3]  # 3

            return self.tiles[2]  # 2

        # ------------------------------------
        # Linha inferior
        # ------------------------------------

        if not s:
            if not w:
                return self.tiles[7]  # 7

            if not e:
                return self.tiles[9]  # 9

            return self.tiles[8]  # 8

        # ------------------------------------
        # Linha do meio
        # ------------------------------------

        if not w:
            return self.tiles[4]  # 4

        if not e:
            return self.tiles[6]  # 6

        return self.tiles[5]  # 5

    def obter_sprite_agua(self, coluna, linha):
        for y in (-1, 0, 1):
            for x in (-1, 0, 1):
                if x == 0 and y == 0:
                    continue

                if self.obter_tipo(coluna + x, linha + y) == self.TIPO_GRAMA:
                    return self.tiles_agua[self.frame_agua]

        return self.agua_parada

    # ==================================================
    # RENDER
    # ==================================================

    def renderizar(self, dt):
        if not self.carregado:
            return

        for linha in range(self.altura):
            for coluna in range(self.largura):
                sprite = self.obter_sprite(coluna, linha)

                if sprite is None:
                    continue

                x = self.offset_x + coluna * self.TILE_SIZE
                y = self.offset_y + linha * self.TILE_SIZE

                if sprite == self.agua_parada:
                    x += self.offset_agua_parada_x
                    y += self.offset_agua_parada_y

                self.tela.blit(sprite, (x, y))

        self.tempo_agua += dt

        if self.tempo_agua >= 0.08:
            self.tempo_agua = 0

            self.frame_agua += 1

            if self.frame_agua > 16:
                self.frame_agua = 1
