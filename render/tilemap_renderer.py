import json

from utils.config import TILE_SIZE


class TileMapRenderer:
    TIPO_GRAMA = "grama"
    TIPO_AGUA = "agua"
    TIPO_AGUA_FUNDO = "agua_fundo"
    TIPO_PENHASCO = "penhasco"
    TIPO_ROCHA = "rocha"
    TIPO_VAZIO = None

    MAPA_INDICES_SPRITE = {
        0: 0,  # borda superior esquerda grama agua
        1: 1,  # borda superior meio grama agua
        2: 2,  # borda superior direita grama agua
        3: 3,  # vertical superior grama agua
        4: 5,  # borda superior esquerda grama penhasco
        5: 6,  # borda superior meio grama penhasco
        6: 7,  # borda superior direita grama penhasco
        7: 8,  # grama superior sozinha penhasco
        8: 9,  # borda lateral esquerda grama agua
        9: 10,  # meio grama agua
        10: 11,  # borda lateral direita grama agua
        11: 18,  # borda inferior esquerda grama agua
        12: 19,  # borda inferior meio grama agua
        13: 20,  # borda inferior direita grama agua
        14: 27,  # horizontal esquerda grama agua
        15: 28,  # horizontal meio grama agua
        16: 29,  # horizontal direita grama agua
        17: 35,  # sozinha grama penhasco
        18: 12,  # vertical meio grama agua
        19: 21,  # vertical inferior grama agua
        20: 30,  # sozinha grama agua
        21: 41,  # lateral esquerda penhasco
        22: 42,  # meio penhasco
        23: 43,  # lateral direita penhasco
        24: 44,  # sozinho penhasco
        25: 50,  # lateral esquerda penhasco agua
        26: 51,  # meio penhasco agua
        27: 52,  # lateral direita penhasco agua
        28: 53,  # sozinho penhasco agua
        29: 23,  # borda inferior esquerda grama penhasco
        30: 24,  # borda inferior meio grama penhasco
        31: 25,  # borda inferior direita grama penhasco
        32: 14,  # borda lateral esquerda grama penhasco
        33: 16,  # borda lateral direita grama penhasco
        34: 36,  # borda superior esquerda degrau penhasco
        35: 45,  # borda inferior esquerda degrau penhasco
        36: 39,  # borda superior direita degrau penhasco
        37: 48,  # borda inferior direita degrau penhasco
        38: 15,  # meio grama penhasco
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
        self._relevos_agua_config = []
        self.ambiente = []

        self.alturas = {}
        self.topos_penhasco = set()
        self.paredes_penhasco = {}
        self.relevos_flags = {}
        self.degraus = {}
        self.degraus_por_relevo = {}
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

        self.ambiente = dados.get("ambiente", [])
        self.largura = dados.get("colunas", 0)
        self.altura = dados.get("linhas", 0)
        self.offset_y = self.altura - 96

        self._processar_biomas(dados.get("biomas", []), dados.get("transicoes", []))
        self._processar_relevos(dados.get("relevos", []))
        self._processar_degraus(dados.get("degraus", []))
        self._processar_relevos_agua(dados.get("relevos_agua", []))

        self._construir_grid_mapa()
        self._aplicar_rios(dados.get("rios", []))
        self._processar_espumas(dados.get("espumas", []))
        self._pre_calcular_autotiling()

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
        self._relevos_config = relevos
        self.alturas.clear()
        self.topos_penhasco.clear()
        self.paredes_penhasco.clear()
        self.relevos_flags.clear()

        for relevo in relevos:
            altura = relevo.get("altura", 1)
            x = relevo["x"]
            y = relevo["y"]
            colunas_x = relevo["colunas"]
            linhas = relevo["linhas"]

            tem_esq = relevo.get("tem_borda_esquerda", True)
            tem_dir = relevo.get("tem_borda_direita", True)
            tem_sup = relevo.get("tem_borda_superior", True)
            tem_inf = relevo.get("tem_borda_inferior", True)  # Lendo a nova propriedade

            linha_borda = y + 1

            for coluna in range(x, x + colunas_x):
                self.alturas[(coluna, linha_borda)] = altura
                self.topos_penhasco.add((coluna, linha_borda))
                self.paredes_penhasco[(coluna, linha_borda)] = linhas

                self.relevos_flags[(coluna, linha_borda)] = {
                    "esq": tem_esq,
                    "dir": tem_dir,
                    "sup": tem_sup,
                    "inf": tem_inf,
                    "primeira_col": x,
                    "ultima_col": x + colunas_x - 1,
                }

            linha_inicio_parede = linha_borda + 1
            for linha in range(linha_inicio_parede, linha_inicio_parede + linhas + 1):
                for coluna in range(x, x + colunas_x):
                    self.alturas[(coluna, linha)] = altura

    def _processar_degraus(self, degraus):
        self.degraus.clear()
        self.degraus_por_relevo.clear()

        relevos_dit = {r["id"]: r for r in self._relevos_config}

        for grupo in degraus:
            relevo_id = grupo["relevo_id"]
            relevo = relevos_dit.get(relevo_id)

            if not relevo:
                continue

            altura_alta = relevo["altura"]
            altura_baixa = altura_alta - 1

            for coluna, linha in grupo.get("tiles", []):
                self.degraus[(coluna, linha)] = {
                    "relevo_id": relevo_id,
                    "direcao": grupo["direcao"],
                    "altura_baixa": altura_baixa,
                    "altura_alta": altura_alta,
                }
                self.degraus_por_relevo.setdefault(relevo_id, []).append(
                    (coluna, linha)
                )
                self.tiles_bloqueados.discard((coluna, linha))
                self.tiles_bloqueados.discard((coluna, linha - 1))

    def _processar_relevos_agua(self, relevos):
        self.relevos_agua.clear()
        self._relevos_agua_config = relevos
        for relevo in relevos:
            altura = relevo.get("altura", -1)
            x = relevo["x"]
            y = relevo["y"]
            colunas = relevo["colunas"]

            for coluna in range(x, x + colunas):
                self.relevos_agua.add((coluna, y))
                self.alturas[(coluna, y - 1)] = altura
                self.tiles_bloqueados.add((coluna, y - 1))

    def _construir_grid_mapa(self):
        self.mapa = []
        for linha in range(self.altura):
            linha_mapa = []
            for coluna in range(self.largura):
                tipo = (
                    self.TIPO_AGUA_FUNDO
                    if linha == self.altura - 1
                    else self.TIPO_GRAMA
                )
                linha_mapa.append(
                    {
                        "tipo": tipo,
                        "altura": self.alturas.get((coluna, linha), 0),
                        "sprite_index": 9,
                    }
                )
            self.mapa.append(linha_mapa)

    def _aplicar_rios(self, rios):
        for rio in rios:
            x_inicial = rio.get("x", 0)
            y_inicial = rio.get("y", 0)
            colunas = rio.get("colunas", 1)
            linhas = rio.get("linhas", 1)

            for linha in range(y_inicial, y_inicial + linhas):
                for coluna in range(x_inicial, x_inicial + colunas):
                    if self._coordenada_valida(coluna, linha):
                        self.mapa[linha][coluna]["tipo"] = self.TIPO_AGUA_FUNDO

    def _processar_espumas(self, espumas):
        self.espumas = {}
        for grupo in espumas:
            offset_x = grupo.get("offset_x", 0)
            offset_y = grupo.get("offset_y", 0)

            x_inicial = grupo.get("x", 0)
            y_inicial = grupo.get("y", 0)
            colunas = grupo.get("colunas", 1)
            linhas = grupo.get("linhas", 1)

            for linha in range(y_inicial, y_inicial + linhas):
                for coluna in range(x_inicial, x_inicial + colunas):
                    self.espumas[(coluna, linha)] = {
                        "offset_x": offset_x,
                        "offset_y": offset_y,
                    }

    def _pre_calcular_autotiling(self):
        for linha in range(self.altura):
            for coluna in range(self.largura):
                if self.obter_tipo(coluna, linha) == self.TIPO_GRAMA:
                    self.mapa[linha][coluna]["sprite_index"] = (
                        self._calcular_indice_grama(coluna, linha)
                    )

    def _calcular_indice_grama(self, coluna, linha):
        v = self.obter_vizinhos_logicos(coluna, linha, self.TIPO_GRAMA)

        # Ilha / Isolado
        if not (v["n"] or v["s"] or v["e"] or v["w"]):
            return 16

        # Bordas Superiores
        if not v["n"]:
            return 0 if not v["w"] else (2 if not v["e"] else 1)

        # Bordas Inferiores
        if not v["s"]:
            if (coluna, linha + 2) in self.relevos_agua:
                if not v["w"] and not v["e"]:
                    return 30
                return 29 if not v["w"] else (31 if not v["e"] else 30)
            return 11 if not v["w"] else (13 if not v["e"] else 12)

        # Bordas Laterais
        if not v["w"]:
            return 8
        if not v["e"]:
            return 10

        if v["n"] and v["s"] and v["w"] and v["e"] and (not v["nw"] or not v["sw"]):
            return 9

        # Cantos internos e preenchimento
        if v["n"] and v["s"] and v["w"] and v["e"]:
            if not v["nw"]:
                return 3
            if not v["ne"]:
                return 18
            if not v["sw"]:
                return 19
            if not v["se"]:
                return 20
            return 9

        return 9

    def atualizar_carregamento(self):
        if self.carregado:
            return

        self.agua_parada = self.assets.carregar("background/agua_parada.png")
        self.sombra = self.assets.carregar("background/sombra.png")
        spritesheet_agua = self.assets.carregar("background/agua.png")
        self.tiles_agua = self.transform.recortar_spritesheet(
            spritesheet_agua, linhas=1, colunas=16
        )

        for i in range(1, 6):
            nome = f"tilemap_color{i}"
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
        return self.obter_tipo(coluna + 1, linha + 1) == tipo_alvo

    def existe_penhasco(self, coluna, linha):
        return (
            self.obter_tipo(coluna, linha) == self.TIPO_GRAMA
            and (coluna, linha) in self.paredes_penhasco
        )

    def eh_penhasco_interno(self, coluna, linha):
        return (
            linha + 2 < self.altura
            and self.obter_tipo(coluna, linha + 2) == self.TIPO_GRAMA
        )

    def eh_grama(self, x, y, altura):
        coluna, linha = self.pixel_para_tile(x, y)
        return self.pode_andar(coluna, linha, altura)

    def pode_andar(self, coluna, linha, altura):
        if (
            not self._coordenada_valida(coluna, linha)
            or (coluna, linha) in self.tiles_bloqueados
        ):
            return False
        if self.obter_tipo(coluna, linha) != self.TIPO_GRAMA:
            return False
        if self.obter_altura(coluna, linha) == altura:
            return True

        degrau = self.obter_degrau(coluna, linha)
        if degrau:
            return altura in (degrau["altura_baixa"], degrau["altura_alta"])
        return False

    def obter_degrau(self, coluna, linha):
        return self.degraus.get((coluna, linha))

    def eh_degrau(self, coluna, linha):
        return (coluna, linha) in self.degraus

    def obter_transicao_degrau(
        self, origem_coluna, origem_linha, destino_coluna, destino_linha, altura
    ):
        coord_degrau = (
            (origem_coluna, origem_linha)
            if (origem_coluna, origem_linha) in self.degraus
            else (destino_coluna, destino_linha)
            if (destino_coluna, destino_linha) in self.degraus
            else None
        )

        if not coord_degrau:
            return None

        degrau = self.degraus[coord_degrau]
        offset = 1 if degrau["direcao"] == "direita" else -1
        lado_baixo = (coord_degrau[0] - offset, coord_degrau[1])
        lado_alto = (coord_degrau[0] + offset, coord_degrau[1])

        origem = (origem_coluna, origem_linha)
        destino = (destino_coluna, destino_linha)

        if altura == degrau["altura_baixa"]:
            if (origem == lado_baixo and destino == coord_degrau) or (
                origem == coord_degrau and destino == lado_alto
            ):
                return degrau["altura_alta"]
        elif (
            altura == degrau["altura_alta"]
            and (origem == lado_alto and destino == coord_degrau)
            or (origem == coord_degrau and destino == lado_baixo)
        ):
            return degrau["altura_baixa"]

        return None

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

    # ==================================================
    # RENDERIZAÇÃO
    # ==================================================

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
        self._renderizar_sombras_relevos(camera)
        self._renderizar_grama_relevos_agua(camera)
        self._renderizar_camada_degraus(camera)
        self._renderizar_penhascos(camera)

    def _atualizar_animacao_agua(self, dt):
        self.tempo_agua += dt
        if self.tempo_agua >= 0.08:
            self.tempo_agua = 0
            self.frame_agua = (self.frame_agua % len(self.tiles_agua)) + 1

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
                tiles = self.obter_tiles(coluna, linha)

                # Renderiza fundo contínuo sob penhascos
                if (
                    self.existe_penhasco(coluna, linha)
                    and self.obter_tipo(coluna, linha + 1) == self.TIPO_GRAMA
                ):
                    self._desenhar_sprite_cenario(tiles[9], coluna, linha, camera)

                # Busca o índice pré-calculado
                indice = self.mapa[linha][coluna].get("sprite_index", 9)
                self._desenhar_sprite_cenario(tiles[indice], coluna, linha, camera)

    def _renderizar_grama_relevos_agua(self, camera):
        for relevo in self._relevos_agua_config:
            linhas = relevo.get("linhas", 1)
            primeira_coluna = relevo["x"]
            colunas = relevo["colunas"]
            ultima_coluna = primeira_coluna + colunas - 1
            linha_agua = relevo["y"]

            if linhas <= 1 or colunas <= 0:
                continue

            tem_esq = relevo.get("tem_borda_esquerda", True)
            tem_dir = relevo.get("tem_borda_direita", True)
            tem_sup = relevo.get("tem_borda_superior", True)
            tem_inf = relevo.get("tem_borda_inferior", True)

            for nivel in range(linhas):
                is_topo = nivel == linhas - 1
                is_base = nivel == 0

                if is_topo and not tem_sup:
                    continue

                if is_base and not tem_inf:
                    continue

                offset_y = (
                    -(linhas + 2) * TILE_SIZE if is_topo else -(nivel + 3) * TILE_SIZE
                )

                for coluna in range(primeira_coluna, ultima_coluna + 1):
                    tiles = self.obter_tiles(coluna, linha_agua)

                    if is_topo:
                        indice = (
                            4
                            if (coluna == primeira_coluna and tem_esq)
                            else 6
                            if (coluna == ultima_coluna and tem_dir)
                            else 5
                        )
                    else:
                        indice = (
                            32
                            if (coluna == primeira_coluna and tem_esq)
                            else 33
                            if (coluna == ultima_coluna and tem_dir)
                            else 9
                        )

                    self._desenhar_sprite_cenario(
                        tiles[indice], coluna, linha_agua, camera, offset_y=offset_y
                    )

    def _renderizar_sombras_relevos(self, camera):
        for relevo in self._relevos_config:
            x = relevo["x"]
            y = relevo["y"]
            colunas = relevo["colunas"]
            linhas = relevo["linhas"]

            tem_esq = relevo.get("tem_borda_esquerda", False)
            tem_dir = relevo.get("tem_borda_direita", False)
            tem_inf = relevo.get("tem_borda_inferior", False)

            linha_topo = y + 1
            linha_base_parede = y + 1 + linhas

            if tem_esq:
                for linha in range(linha_topo, linha_base_parede + 1):
                    self._desenhar_sprite_cenario(self.sombra, x - 1, linha, camera)

            if tem_dir:
                for linha in range(linha_topo, linha_base_parede + 1):
                    self._desenhar_sprite_cenario(
                        self.sombra,
                        x + colunas - 1,
                        linha,
                        camera,
                        offset_x=-(TILE_SIZE - 4),
                    )

            if tem_inf:
                limite_coluna = (x + colunas - 2) if tem_dir else (x + colunas)

                for coluna in range(x, limite_coluna):
                    self._desenhar_sprite_cenario(
                        self.sombra, coluna, linha_base_parede, camera
                    )

    def _precisa_tile_38(self, coluna, linha_sprite):
        for relevo in self._relevos_config:
            x = relevo["x"]
            colunas_x = relevo["colunas"]
            if not (x <= coluna < x + colunas_x):
                continue

            for degrau_coluna, degrau_linha in self.degraus_por_relevo.get(
                relevo["id"], []
            ):
                degrau = self.degraus.get((degrau_coluna, degrau_linha))
                if not degrau:
                    continue

                is_esq = degrau["direcao"] == "esquerda" and coluna == (
                    x + colunas_x - 1
                )
                is_dir = degrau["direcao"] == "direita" and coluna == x

                if (is_esq or is_dir) and linha_sprite == degrau_linha - 1:
                    return True
        return False

    def _renderizar_penhascos(self, camera):
        for coluna, linha in self._iterar_area_visivel(camera):
            if not self.existe_penhasco(coluna, linha):
                continue

            tiles = self.obter_tiles(coluna, linha)

            flags = self.relevos_flags.get(
                (coluna, linha),
                {
                    "esq": True,
                    "dir": True,
                    "sup": True,
                    "inf": True,
                    "primeira_col": -1,
                    "ultima_col": -1,
                },
            )

            w = self.existe_penhasco(coluna - 1, linha)
            if coluna == flags["primeira_col"] and not flags["esq"]:
                w = True

            e = self.existe_penhasco(coluna + 1, linha)
            # Se é a última coluna do relevo e não tem borda, força o vizinho da direita
            if coluna == flags["ultima_col"] and not flags["dir"]:
                e = True

            linhas_penhasco = self.paredes_penhasco[(coluna, linha)]
            interno = self.eh_penhasco_interno(coluna, linha)

            # ====== TOPO DO PENHASCO ======
            limite_iteracao = linhas_penhasco if interno else linhas_penhasco - 1

            desenha_topo = interno and flags["sup"]

            if desenha_topo:
                if not w and not e:
                    topo = tiles[5]
                elif not w:
                    topo = tiles[4]
                elif not e:
                    topo = tiles[6]
                else:
                    topo = tiles[5]
                self._desenhar_sprite_cenario(topo, coluna, linha, camera)

            # Se não tiver borda superior, a parede de pedra começa direto do topo (0)
            inicio_meio = 1 if interno else 0
            if interno and not flags["sup"]:
                inicio_meio = 0

            for i in range(inicio_meio, limite_iteracao):
                linha_sprite = linha + i

                if self._precisa_tile_38(coluna, linha_sprite):
                    meio = tiles[38]
                else:
                    if not w:
                        meio = tiles[32]
                    elif not e:
                        meio = tiles[33]
                    else:
                        meio = tiles[9]

                self._desenhar_sprite_cenario(
                    meio, coluna, linha, camera, penhasco_size=TILE_SIZE * i
                )

            # Nova condição: só desenha a base se tem_borda_inferior for True
            if flags.get("inf", True):
                altura_borda = TILE_SIZE * limite_iteracao
                if not w and not e:
                    borda = tiles[30]
                elif not w:
                    borda = tiles[29]
                elif not e:
                    borda = tiles[31]
                else:
                    borda = tiles[30]

                self._desenhar_sprite_cenario(
                    borda, coluna, linha, camera, penhasco_size=altura_borda
                )

                # ====== PAREDE DO PENHASCO ======
                if not w and not e:
                    parede = tiles[22]
                elif not w:
                    parede = tiles[21]
                elif not e:
                    parede = tiles[23]
                else:
                    parede = tiles[22]

                altura_final = TILE_SIZE * (
                    linhas_penhasco + 1 if interno else linhas_penhasco
                )
                linha_bloqueada = linha + (
                    linhas_penhasco + 1 if interno else linhas_penhasco
                )

                self.tiles_bloqueados.add((coluna, linha_bloqueada))
                self._desenhar_sprite_cenario(
                    parede, coluna, linha, camera, penhasco_size=altura_final
                )

    def _renderizar_camada_degraus(self, camera):
        for (coluna, linha), dados in self.degraus.items():
            tiles = self.obter_tiles(coluna, linha)
            direcao = dados["direcao"]

            if direcao == "direita":
                tile_superior, tile_inferior = tiles[34], tiles[35]
            elif direcao == "esquerda":
                tile_superior, tile_inferior = tiles[36], tiles[37]
            else:
                continue

            self._desenhar_sprite_cenario(tile_inferior, coluna, linha, camera)
            self._desenhar_sprite_cenario(
                tile_superior, coluna, linha, camera, offset_y=-TILE_SIZE
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

        sw, sh = sprite.get_width(), sprite.get_height()
        inicio_x, fim_x = (
            int(camera.x // sw) - 1,
            int((camera.x + camera.largura) // sw) + 2,
        )
        inicio_y, fim_y = (
            int(camera.y // sh) - 1,
            int((camera.y + camera.altura) // sh) + 2,
        )

        for y in range(inicio_y, fim_y):
            for x in range(inicio_x, fim_x):
                self.tela.blit(sprite, (x * sw - camera.x, y * sh - camera.y))
