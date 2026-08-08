import json

from utils.config import TILE_SIZE
from utils.kivy_adapter import draw


class TileMapRenderer:
    TIPO_GRAMA = "grama"
    TIPO_AGUA = "agua"
    TIPO_AGUA_FUNDO = "agua_fundo"
    TIPO_PENHASCO = "penhasco"
    TIPO_ROCHA = "rocha"
    TIPO_VAZIO = None

    # Mapeamento estático dos índices lógicos para os reais na spritesheet
    MAPA_INDICES_SPRITE = {
        0: 0,
        1: 1,
        2: 2,
        3: 3,
        4: 5,
        5: 6,
        6: 7,
        7: 8,
        8: 9,
        9: 10,
        10: 11,
        11: 18,
        12: 19,
        13: 20,
        14: 27,
        15: 28,
        16: 29,
        17: 0,
        18: 12,
        19: 21,
        20: 30,
        21: 41,
        22: 42,
        23: 43,
        24: 44,
        25: 50,
        26: 51,
        27: 52,
        28: 53,
        29: 23,
        30: 24,
        31: 25,
        32: 14,
        33: 16,
    }

    def __init__(self, tela, assets, transform):
        self.tela = tela
        self.assets = assets
        self.transform = transform
        self.carregado = False

        self.tiles = {}
        self.mapa = []
        self.tiles_bioma = {}
        self.cache_tiles = {}
        self.espumas = {}
        self.relevos_agua = set()

        self.alturas = {}
        self.topos_penhasco = set()
        self.paredes_penhasco = {}
        self.tiles_bloqueados = set()
        self.largura = 0
        self.altura = 0
        self.offset_y = 0
        self.offset_x = -60

        self.frame_agua = 1
        self.tempo_agua = 0.0
        self.offset_agua_parada_x = -1
        self.offset_agua_parada_y = 85

        self.carregar_mapa("data/mapas/mapa1.json")

    # ==================================================
    # LOAD E INICIALIZAÇÃO
    # ==================================================

    def carregar_mapa(self, caminho):
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        self.largura = dados.get("colunas", 0)
        self.altura = dados.get("linhas", 0)
        self.offset_y = self.altura - 96

        self._processar_biomas(dados.get("biomas", []), dados.get("transicoes", []))
        self._processar_relevos(dados.get("relevos", []))
        self._processar_relevos_agua(dados.get("relevos_agua", []))
        self._construir_grid_mapa()
        self._aplicar_rios(dados.get("rios", []))
        self._processar_espumas(dados.get("espumas", []))

    def _processar_biomas(self, biomas, transicoes):
        self.tiles_bioma.clear()

        for bioma in biomas:
            nome = bioma["tilemap"]
            for linha in range(bioma["y"], bioma["y"] + bioma["linhas"]):
                for coluna in range(bioma["x"], bioma["x"] + bioma["colunas"]):
                    self.tiles_bioma[(coluna, linha)] = nome

        for transicao in transicoes:
            destino = transicao["destino"]
            for coluna, linha in transicao["tiles"]:
                self.tiles_bioma[(coluna, linha)] = destino

    def _processar_relevos(self, relevos):
        self.alturas.clear()
        self.topos_penhasco.clear()
        self.paredes_penhasco.clear()

        for relevo in relevos:
            altura = relevo["altura"]
            topo = relevo["topo"]
            parede = relevo["parede"]

            linhas_parede = parede["linhas"]
            linha_borda = topo["y"] + topo["linhas"] - 1
            colunas_x = topo["colunas"]

            linha_inicio_topo = topo["y"] + 1

            for linha in range(linha_inicio_topo, topo["y"] + topo["linhas"]):
                for coluna in range(topo["x"], topo["x"] + colunas_x):
                    self.alturas[(coluna, linha)] = altura
                    self.topos_penhasco.add((coluna, linha))

                    if linha == topo["y"] + topo["linhas"] - 1:
                        self.paredes_penhasco[(coluna, linha)] = linhas_parede

            linha_inicio_parede = linha_borda + 1

            for linha in range(
                linha_inicio_parede, linha_inicio_parede + linhas_parede + 1
            ):
                for coluna in range(topo["x"], topo["x"] + colunas_x):
                    self.alturas[(coluna, linha)] = altura

    def _construir_grid_mapa(self):
        self.mapa = []

        for linha in range(self.altura):
            linha_mapa = []

            for coluna in range(self.largura):
                tipo = self.TIPO_GRAMA

                # Última linha do mapa é água de fundo
                if linha == self.altura - 1:
                    tipo = self.TIPO_AGUA_FUNDO

                linha_mapa.append(
                    {
                        "tipo": tipo,
                        "altura": self.alturas.get((coluna, linha), 0),
                    }
                )

            self.mapa.append(linha_mapa)

    def _aplicar_rios(self, rios):
        for rio in rios:
            largura = rio["largura"]
            pontos = rio["pontos"]

            for i in range(len(pontos) - 1):
                x0, y0 = pontos[i]
                x1, y1 = pontos[i + 1]
                dx, dy = x1 - x0, y1 - y0
                passos = max(abs(dx), abs(dy))

                if passos == 0:
                    continue

                for passo in range(passos + 1):
                    x = round(x0 + dx * passo / passos)
                    y = round(y0 + dy * passo / passos)

                    for oy in range(-largura + 1, largura):
                        for ox in range(-largura + 1, largura):
                            if self._coordenada_valida(x + ox, y + oy):
                                self.mapa[y + oy][x + ox]["tipo"] = self.TIPO_AGUA_FUNDO

    def _processar_espumas(self, espumas):
        self.espumas = {}

        for grupo in espumas:
            offset_x = grupo.get("offset_x", 0)
            offset_y = grupo.get("offset_y", 0)

            for coluna, linha in grupo.get("tiles", []):
                self.espumas[(coluna, linha)] = {
                    "offset_x": offset_x,
                    "offset_y": offset_y,
                }

    def _processar_relevos_agua(self, relevos):
        self.relevos_agua.clear()

        for relevo in relevos:
            altura = relevo.get("altura", -1)

            for coluna, linha in relevo["tiles"]:
                self.relevos_agua.add((coluna, linha))

                # Marca a altura na célula onde o sprite realmente aparece
                self.alturas[(coluna, linha - 1)] = altura
                self.tiles_bloqueados.add((coluna, linha - 1))

    def atualizar_carregamento(self):
        if self.carregado:
            return

        self.agua_parada = self.assets.carregar("background/agua_parada.png")
        spritesheet_agua = self.assets.carregar("background/agua.png")
        self.tiles_agua = self.transform.recortar_spritesheet(
            spritesheet_agua, linhas=1, colunas=16
        )

        nomes_tilemaps = [f"tilemap_color{i}" for i in range(1, 6)]

        for nome in nomes_tilemaps:
            spritesheet = self.assets.carregar(f"background/{nome}.png")
            colunas = spritesheet.get_width() // TILE_SIZE
            linhas = spritesheet.get_height() // TILE_SIZE
            tiles_recortados = self.transform.recortar_spritesheet(
                spritesheet, linhas=linhas, colunas=colunas
            )

            self.tiles[nome] = {
                logico: tiles_recortados[real]
                for logico, real in self.MAPA_INDICES_SPRITE.items()
            }

        self._atualizar_cache_tiles()
        self.carregado = True

    def _atualizar_cache_tiles(self):
        self.cache_tiles.clear()
        for (coluna, linha), nome in self.tiles_bioma.items():
            self.cache_tiles[(coluna, linha)] = self.tiles[nome]

    # ==================================================
    # CONSULTAS E LÓGICA DE MAPA
    # ==================================================

    def _coordenada_valida(self, coluna, linha):
        return 0 <= coluna < self.largura and 0 <= linha < self.altura

    def obter_tiles(self, coluna, linha):
        return self.cache_tiles.get((coluna, linha), self.tiles.get("tilemap_color1"))

    def obter_tipo(self, coluna, linha):
        if not self._coordenada_valida(coluna, linha):
            return self.TIPO_AGUA_FUNDO

        tile = self.mapa[linha][coluna]
        return tile if isinstance(tile, str) or tile is None else tile.get("tipo")

    def obter_altura(self, coluna, linha):
        return self.alturas.get((coluna, linha), 0)

    def _verificar_vizinhos_por_tipo(self, coluna, linha, tipo_alvo):
        direcoes = [(1, 1)]

        for dx, dy in direcoes:
            if self.obter_tipo(coluna + dx, linha + dy) == tipo_alvo:
                return True
        return False

    def existe_penhasco(self, coluna, linha):
        if self.obter_tipo(coluna, linha) != self.TIPO_GRAMA:
            return False
        return (coluna, linha) in self.paredes_penhasco

    def eh_penhasco_interno(self, coluna, linha):
        return (
            linha + 2 < self.altura
            and self.obter_tipo(coluna, linha + 2) == self.TIPO_GRAMA
        )

    def eh_grama(self, x, y, altura):
        coluna, linha = self.pixel_para_tile(x, y)
        return self.pode_andar(coluna, linha, altura)

    def pode_andar(self, coluna, linha, altura):
        if not self._coordenada_valida(coluna, linha):
            return False

        if (coluna, linha) in self.tiles_bloqueados:
            return False

        if self.obter_tipo(coluna, linha) != self.TIPO_GRAMA:
            return False

        return self.obter_altura(coluna, linha) == altura

    # ==================================================
    # CONVERSÃO DE COORDENADAS E SPRITES
    # ==================================================

    def pixel_para_tile(self, x, y):
        coluna = int((x - self.offset_x) // TILE_SIZE)
        linha = int((y - self.offset_y) // TILE_SIZE)
        return coluna, linha

    def tile_para_pixel(self, coluna, linha):
        return (self.offset_x + coluna * TILE_SIZE, self.offset_y + linha * TILE_SIZE)

    def obter_vizinhos_logicos(self, coluna, linha, tipo):
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

    def obter_sprite(self, coluna, linha):
        tipo = self.obter_tipo(coluna, linha)
        if tipo is None:
            return None

        if tipo == self.TIPO_AGUA:
            return (
                self.tiles_agua[self.frame_agua - 1]
                if self._verificar_vizinhos_por_tipo(coluna, linha, self.TIPO_GRAMA)
                else None
            )

        if tipo != self.TIPO_GRAMA:
            return None

        tiles = self.obter_tiles(coluna, linha)
        v = self.obter_vizinhos_logicos(coluna, linha, tipo)

        # Ilha
        if not v["n"] and not v["s"] and not v["e"] and not v["w"]:
            return tiles[16]

        # Topo e Base
        if not v["n"]:
            return tiles[0] if not v["w"] else tiles[2] if not v["e"] else tiles[1]
        if not v["s"]:
            if (coluna, linha + 2) in self.relevos_agua:
                return (
                    tiles[30]
                    if not v["w"] and not v["e"]
                    else tiles[29]
                    if not v["w"]
                    else tiles[31]
                    if not v["e"]
                    else tiles[30]
                )

            return tiles[11] if not v["w"] else tiles[13] if not v["e"] else tiles[12]

        if not v["w"]:
            return tiles[8]
        if not v["e"]:
            return tiles[10]

        # Margem direita de rios e cantos internos
        if v["n"] and v["s"] and v["w"] and v["e"] and not v["nw"] or not v["sw"]:
            return tiles[9]

        if not v["nw"]:
            return tiles[3]
        if not v["ne"]:
            return tiles[18]
        if not v["sw"]:
            return tiles[19]
        if not v["se"]:
            return tiles[20]

        return tiles[9]

    # ==================================================
    # RENDERIZAÇÃO
    # ==================================================

    def _atualizar_animacao_agua(self, dt):
        self.tempo_agua += dt
        if self.tempo_agua >= 0.08:
            self.tempo_agua = 0
            self.frame_agua = (self.frame_agua % len(self.tiles_agua)) + 1

    def _iterar_area_visivel(self, camera):
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

        for linha in range(inicio_y, fim_y):
            for coluna in range(inicio_x, fim_x):
                yield coluna, linha

    def renderizar(self, dt, camera):
        if not self.carregado:
            return

        self._atualizar_animacao_agua(dt)
        self._renderizar_fundo(camera)

        self._renderizar_camada_espuma(camera)
        self._renderizar_relevos_agua(camera)
        self._renderizar_camada_grama(camera)
        self._renderizar_camada_topos_penhasco(camera)
        self._renderizar_camada_paredes_penhasco(camera)
        # self._debug_tiles(camera)

    def _debug_tiles(self, camera):
        for coluna, linha in self._iterar_area_visivel(camera):
            x = int((self.offset_x + coluna * TILE_SIZE - camera.x) * camera.zoom)
            y = int((self.offset_y + linha * TILE_SIZE - camera.y) * camera.zoom)
            tamanho = int(TILE_SIZE * camera.zoom)

            draw.rect(
                self.tela,
                (255, 0, 0),
                (x, y, tamanho, tamanho),
                width=1,
            )

            altura = self.obter_altura(coluna, linha)

            draw.text(
                self.tela,
                f"{coluna},{linha}\nH:{altura}",
                (x + 3, y + 3),
                cor=(255, 0, 0),
                tamanho=14,
            )

    def _renderizar_camada_espuma(self, camera):
        sprite = self.tiles_agua[self.frame_agua - 1]

        for (coluna, linha), dados in self.espumas.items():
            self._desenhar_sprite_cenario(
                sprite,
                coluna,
                linha,
                camera,
                offset_x=dados["offset_x"],
                offset_y=dados["offset_y"],
            )

    def _renderizar_relevos_agua(self, camera):
        for coluna, linha in self._iterar_area_visivel(camera):
            if (coluna, linha) not in self.relevos_agua:
                continue

            tiles = self.obter_tiles(coluna, linha)

            esquerda = (coluna - 1, linha) in self.relevos_agua
            direita = (coluna + 1, linha) in self.relevos_agua

            if not esquerda:
                sprite = tiles[25]
            elif not direita:
                sprite = tiles[27]
            else:
                sprite = tiles[26]

            self._desenhar_sprite_cenario(
                sprite, coluna, linha, camera, offset_y=-TILE_SIZE
            )

    def _renderizar_camada_grama(self, camera):
        for coluna, linha in self._iterar_area_visivel(camera):
            if self.obter_tipo(coluna, linha) == self.TIPO_GRAMA:
                if (
                    self.existe_penhasco(coluna, linha)
                    and self.obter_tipo(coluna, linha + 1) == self.TIPO_GRAMA
                ):
                    tiles = self.obter_tiles(coluna, linha)
                    self._desenhar_sprite_cenario(tiles[9], coluna, linha, camera)

                sprite = self.obter_sprite(coluna, linha)
                if sprite:
                    self._desenhar_sprite_cenario(sprite, coluna, linha, camera)

    def _renderizar_camada_topos_penhasco(self, camera):
        for coluna, linha in self._iterar_area_visivel(camera):
            if not self.existe_penhasco(coluna, linha):
                continue

            tiles = self.obter_tiles(coluna, linha)
            w = self.existe_penhasco(coluna - 1, linha)
            e = self.existe_penhasco(coluna + 1, linha)

            linhas_penhasco = self.paredes_penhasco[(coluna, linha)]

            interno = self.eh_penhasco_interno(coluna, linha)
            limite_iteracao = linhas_penhasco if interno else linhas_penhasco - 1

            if interno:
                topo = (
                    tiles[5]
                    if not w and not e
                    else tiles[4]
                    if not w
                    else tiles[6]
                    if not e
                    else tiles[5]
                )
                self._desenhar_sprite_cenario(topo, coluna, linha, camera)

            for i in range(1 if interno else 0, limite_iteracao):
                meio = tiles[32] if not w else tiles[33] if not e else tiles[9]
                self._desenhar_sprite_cenario(
                    meio, coluna, linha, camera, penhasco_size=TILE_SIZE * i
                )

            borda = (
                tiles[30]
                if not w and not e
                else tiles[29]
                if not w
                else tiles[31]
                if not e
                else tiles[30]
            )
            altura_borda = (
                TILE_SIZE * linhas_penhasco
                if interno
                else TILE_SIZE * (linhas_penhasco - 1)
            )
            self._desenhar_sprite_cenario(
                borda, coluna, linha, camera, penhasco_size=altura_borda
            )

    def _renderizar_camada_paredes_penhasco(self, camera):
        for coluna, linha in self._iterar_area_visivel(camera):
            if not self.existe_penhasco(coluna, linha):
                continue

            tiles = self.obter_tiles(coluna, linha)
            w = self.existe_penhasco(coluna - 1, linha)
            e = self.existe_penhasco(coluna + 1, linha)

            parede_sprite = (
                tiles[22]
                if not w and not e
                else tiles[21]
                if not w
                else tiles[23]
                if not e
                else tiles[22]
            )

            linhas_penhasco = self.paredes_penhasco[(coluna, linha)]

            altura_final = (
                TILE_SIZE * (linhas_penhasco + 1)
                if self.eh_penhasco_interno(coluna, linha)
                else TILE_SIZE * linhas_penhasco
            )

            linha_bloqueada = linha + (
                linhas_penhasco + 1
                if self.eh_penhasco_interno(coluna, linha)
                else linhas_penhasco
            )

            self.tiles_bloqueados.add((coluna, linha_bloqueada))

            self._desenhar_sprite_cenario(
                parede_sprite, coluna, linha, camera, penhasco_size=altura_final
            )

    def _desenhar_sprite_cenario(
        self, sprite, coluna, linha, camera, penhasco_size=0, offset_x=0, offset_y=0
    ):
        x = (self.offset_x + coluna * TILE_SIZE - camera.x) * camera.zoom
        y = (self.offset_y + linha * TILE_SIZE - camera.y) * camera.zoom

        largura_zoom = int(sprite.get_width() * camera.zoom)
        altura_zoom = int(sprite.get_height() * camera.zoom)
        sprite_escalado = self.transform.escalar(sprite, (largura_zoom, altura_zoom))

        pos_x = x + offset_x * camera.zoom
        pos_y = y + penhasco_size + offset_y * camera.zoom
        self.tela.blit(sprite_escalado, (pos_x, pos_y))

    def _renderizar_fundo(self, camera):
        largura_zoom = int(self.agua_parada.get_width() * camera.zoom)
        altura_zoom = int(self.agua_parada.get_height() * camera.zoom)
        sprite = self.transform.escalar(self.agua_parada, (largura_zoom, altura_zoom))

        inicio_x = int(camera.x // sprite.get_width()) - 1
        fim_x = int((camera.x + camera.largura) // sprite.get_width()) + 2
        inicio_y = int(camera.y // sprite.get_height()) - 1
        fim_y = int((camera.y + camera.altura) // sprite.get_height()) + 2

        for y in range(inicio_y, fim_y):
            for x in range(inicio_x, fim_x):
                self.tela.blit(
                    sprite,
                    (
                        x * sprite.get_width() - camera.x,
                        y * sprite.get_height() - camera.y,
                    ),
                )
