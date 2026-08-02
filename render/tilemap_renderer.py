import json

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
        self.tiles_bioma = {}
        self.cache_tiles = {}
        self.alturas = {}
        self.topos_penhasco = set()
        self.paredes_penhasco = {}

        self.largura = 0
        self.altura = 0
        self.offset_y = 0
        self.frame_agua = 1
        self.tempo_agua = 0.0
        self.offset_agua_parada_x = -1
        self.offset_agua_parada_y = 85

        self.carregar_mapa("data/mapas/mapa1.json")

    def carregar_mapa(self, caminho):
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        self.largura = dados["colunas"]
        self.altura = dados["linhas"]

        self.biomas = dados["biomas"]

        self.tiles_bioma.clear()

        for bioma in self.biomas:
            nome = bioma["tilemap"]

            for linha in range(
                bioma["y"],
                bioma["y"] + bioma["linhas"],
            ):
                for coluna in range(
                    bioma["x"],
                    bioma["x"] + bioma["colunas"],
                ):
                    self.tiles_bioma[(coluna, linha)] = nome

        self.alturas.clear()
        self.topos_penhasco.clear()
        self.paredes_penhasco.clear()

        for relevo in dados.get("relevos", []):
            altura = relevo["altura"]

            topo = relevo["topo"]

            for linha in range(
                topo["y"],
                topo["y"] + topo["linhas"],
            ):
                for coluna in range(
                    topo["x"],
                    topo["x"] + topo["colunas"],
                ):
                    self.alturas[(coluna, linha)] = altura
                    self.topos_penhasco.add((coluna, linha))

            parede = relevo["parede"]

            for linha in range(
                parede["y"],
                parede["y"] + parede["linhas"],
            ):
                for coluna in range(
                    parede["x"],
                    parede["x"] + parede["colunas"],
                ):
                    self.paredes_penhasco[(coluna, linha)] = {
                        "altura": altura,
                        "linhas": parede["linhas"],
                    }

        self.mapa = []

        for linha in range(self.altura):
            linha_mapa = []
            for coluna in range(self.largura):
                linha_mapa.append(
                    {
                        "tipo": self.TIPO_GRAMA,
                        "altura": self.alturas.get(
                            (coluna, linha),
                            1,
                        ),
                    }
                )

            self.mapa.append(linha_mapa)

        self.offset_y = self.altura - 96
        self.offset_x = -60

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
        self.tiles = {}

        for nome in (
            "tilemap_color1",
            "tilemap_color2",
            "tilemap_color3",
            "tilemap_color4",
            "tilemap_color5",
        ):
            spritesheet = self.assets.carregar(f"background/{nome}.png")

            colunas = spritesheet.get_width() // TILE_SIZE
            linhas = spritesheet.get_height() // TILE_SIZE

            tiles = self.transform.recortar_spritesheet(
                spritesheet,
                linhas=linhas,
                colunas=colunas,
            )

            self.tiles[nome] = {
                0: tiles[0],
                1: tiles[1],
                2: tiles[2],
                3: tiles[3],
                4: tiles[5],
                5: tiles[6],
                6: tiles[7],
                7: tiles[8],
                8: tiles[9],
                9: tiles[10],
                10: tiles[11],
                11: tiles[18],
                12: tiles[19],
                13: tiles[20],
                14: tiles[27],
                15: tiles[28],
                16: tiles[29],
                17: tiles[0],
                18: tiles[12],
                19: tiles[21],
                20: tiles[30],
                21: tiles[41],
                22: tiles[42],
                23: tiles[43],
                24: tiles[44],
                25: tiles[50],
                26: tiles[51],
                27: tiles[52],
                28: tiles[53],
                29: tiles[23],
                30: tiles[24],
                31: tiles[25],
                32: tiles[14],
                33: tiles[16],
            }

        self.cache_tiles.clear()

        for (coluna, linha), nome in self.tiles_bioma.items():
            self.cache_tiles[(coluna, linha)] = self.tiles[nome]

        self.carregado = True

    # ==================================================
    # MAPA
    # ==================================================

    def obter_tiles(self, coluna, linha):
        return self.cache_tiles.get(
            (coluna, linha),
            self.tiles["tilemap_color1"],
        )

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

    def eh_grama(self, x, y):
        coluna, linha = self.pixel_para_tile(x, y)

        return self.pode_andar(coluna, linha)

    def pode_andar(self, coluna, linha):
        if self.obter_tipo(coluna, linha) != self.TIPO_GRAMA:
            return False

        return not self.existe_penhasco(coluna, linha)

    def eh_penhasco_interno(self, coluna, linha):
        return (
            linha + 2 < self.altura
            and self.obter_tipo(coluna, linha + 2) == self.TIPO_GRAMA
        )

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
        tiles = self.obter_tiles(coluna, linha)

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
            return tiles[16]

        #
        # topo
        #
        if not n:
            if not w:
                return tiles[0]

            if not e:
                return tiles[2]

            return tiles[1]

        #
        # base
        #
        if not s:
            if not w:
                return tiles[11]

            if not e:
                return tiles[13]

            return tiles[12]

        #
        # esquerda
        #
        if not w:
            return tiles[8]

        #
        # direita
        #
        if not e:
            return tiles[10]

        #
        # cantos internos
        #
        if not nw:
            return tiles[3]

        if not ne:
            return tiles[18]

        if not sw:
            return tiles[19]

        if not se:
            return tiles[20]

        return tiles[9]

    def obter_sprite_agua(self, coluna, linha):
        if self.tem_grama_vizinha(coluna, linha):
            return self.tiles_agua[self.frame_agua - 1]

        return None

    def obter_sprite_coluna(self, coluna, linha):
        tiles = self.obter_tiles(coluna, linha)

        v = self.obter_vizinhos_penhasco(coluna, linha)

        w = v["w"]
        e = v["e"]

        if not w and not e:
            return tiles[22]

        if not w:
            return tiles[21]

        if not e:
            return tiles[23]

        return tiles[22]

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
                    if coluna == self.largura:
                        continue

                    if linha == self.altura:
                        continue

                    if (
                        self.tem_grama_vizinha(coluna, linha)
                        and self.obter_tipo(coluna - 1, linha) != self.TIPO_GRAMA
                        and not self.existe_penhasco(coluna, linha - 1)
                    ):
                        desenhar_espuma = True

                elif tipo == self.TIPO_GRAMA and self.tem_vizinho_agua(coluna, linha):
                    desenhar_espuma = True

                if desenhar_espuma:
                    sprite = self.tiles_agua[self.frame_agua - 1]
                    offset_x = 0
                    offset_y = 0

                    # Última coluna do mapa
                    if coluna == self.largura - 1:
                        offset_x = -62

                    # Última linha do mapa
                    if linha == self.altura - 1:
                        offset_y = -3

                    self._renderizar_cenario(
                        sprite,
                        coluna,
                        linha,
                        camera,
                        offset_x=offset_x,
                        offset_y=offset_y,
                    )

        # 2. Desenha todos os tiles de grama por cima da espuma
        for linha in range(inicio_y, fim_y):
            for coluna in range(inicio_x, fim_x):
                if self.obter_tipo(coluna, linha) == self.TIPO_GRAMA:
                    if (
                        self.existe_penhasco(coluna, linha)
                        and self.obter_tipo(coluna, linha + 1) == self.TIPO_GRAMA
                    ):
                        tiles = self.obter_tiles(coluna, linha)
                        self._renderizar_cenario(tiles[9], coluna, linha, camera)

                    sprite = self.obter_sprite(coluna, linha)

                    if sprite is not None:
                        self._renderizar_cenario(
                            sprite,
                            coluna,
                            linha,
                            camera,
                        )

        # 3. Desenha os topos e gramas dos penhascos (Passo 1)
        for linha in range(inicio_y, fim_y):
            for coluna in range(inicio_x, fim_x):
                if not self.existe_penhasco(coluna, linha):
                    continue

                tiles = self.obter_tiles(coluna, linha)
                w = self.existe_penhasco(coluna - 1, linha)
                e = self.existe_penhasco(coluna + 1, linha)

                # Calcula quantas linhas de profundidade o penhasco tem
                altura_topo = self.obter_altura(coluna, linha)
                altura_base = self.obter_altura(coluna, linha + 1)
                linhas_penhasco = altura_topo - altura_base

                if linhas_penhasco < 1:
                    linhas_penhasco = 1

                if self.eh_penhasco_interno(coluna, linha):
                    # O topo inicial (linha 0 do penhasco)
                    if not w and not e:
                        topo = tiles[5]
                    elif not w:
                        topo = tiles[4]
                    elif not e:
                        topo = tiles[6]
                    else:
                        topo = tiles[5]

                    self._renderizar_cenario(topo, coluna, linha, camera)

                    # PREENCHIMENTO VERTICAL DAS LINHAS DO MEIO
                    for i in range(1, linhas_penhasco):
                        # Se for a borda esquerda do penhasco, usa o tile 32
                        if not w:
                            meio_tile = tiles[32]
                        # Se for a borda direita do penhasco, usa o tile 33
                        elif not e:
                            meio_tile = tiles[33]
                        # Se for o miolo, usa a grama lisa (tile 9)
                        else:
                            meio_tile = tiles[9]

                        self._renderizar_cenario(
                            meio_tile, coluna, linha, camera, TILE_SIZE * i
                        )

                    # BORDA FINAL (última linha do platô antes da parede)
                    if not w and not e:
                        borda = tiles[30]
                    elif not w:
                        borda = tiles[29]
                    elif not e:
                        borda = tiles[31]
                    else:
                        borda = tiles[30]

                    self._renderizar_cenario(
                        borda, coluna, linha, camera, TILE_SIZE * linhas_penhasco
                    )

                else:
                    # Penhascos externos
                    for i in range(linhas_penhasco - 1):
                        if not w:
                            meio_tile = tiles[32]
                        elif not e:
                            meio_tile = tiles[33]
                        else:
                            meio_tile = tiles[9]

                        self._renderizar_cenario(
                            meio_tile, coluna, linha, camera, TILE_SIZE * i
                        )

                    if not w and not e:
                        borda = tiles[30]
                    elif not w:
                        borda = tiles[29]
                    elif not e:
                        borda = tiles[31]
                    else:
                        borda = tiles[30]

                    self._renderizar_cenario(
                        borda, coluna, linha, camera, TILE_SIZE * (linhas_penhasco - 1)
                    )

        # 4. Desenha as paredes dos penhascos (Passo 2)
        for linha in range(inicio_y, fim_y):
            for coluna in range(inicio_x, fim_x):
                if not self.existe_penhasco(coluna, linha):
                    continue

                tiles = self.obter_tiles(coluna, linha)
                w = self.existe_penhasco(coluna - 1, linha)
                e = self.existe_penhasco(coluna + 1, linha)

                if not w and not e:
                    parede = tiles[22]
                elif not w:
                    parede = tiles[21]
                elif not e:
                    parede = tiles[23]
                else:
                    parede = tiles[22]

                altura_topo = self.obter_altura(coluna, linha)
                altura_base = self.obter_altura(coluna, linha + 1)
                linhas_penhasco = altura_topo - altura_base

                if linhas_penhasco < 1:
                    linhas_penhasco = 1

                # Desenha a parede única lá no final, empurrada pela altura!
                if self.eh_penhasco_interno(coluna, linha):
                    self._renderizar_cenario(
                        parede, coluna, linha, camera, TILE_SIZE * (linhas_penhasco + 1)
                    )
                else:
                    self._renderizar_cenario(
                        parede, coluna, linha, camera, TILE_SIZE * linhas_penhasco
                    )

    def _renderizar_cenario(
        self,
        sprite,
        coluna,
        linha,
        camera,
        penhasco_size=0,
        offset_x=0,
        offset_y=0,
    ):
        x = (self.offset_x + coluna * TILE_SIZE - camera.x) * camera.zoom
        y = (self.offset_y + linha * TILE_SIZE - camera.y) * camera.zoom

        sprite = self.transform.escalar(
            sprite,
            (
                int(sprite.get_width() * camera.zoom),
                int(sprite.get_height() * camera.zoom),
            ),
        )

        self.tela.blit(
            sprite,
            (
                x + offset_x * camera.zoom,
                y + penhasco_size + offset_y * camera.zoom,
            ),
        )

    def renderizar_fundo(self, camera):
        sprite = self.agua_parada

        sprite = self.transform.escalar(
            sprite,
            (
                int(sprite.get_width() * camera.zoom),
                int(sprite.get_height() * camera.zoom),
            ),
        )

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
