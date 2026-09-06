import json

import utils.kivy_adapter as kivy_adapter
from core.regiao_mapa import RegiaoMapa
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
        39: 32,  # horizontal esquerda grama penhasco
        40: 34,  # horizontal direita grama penhasco
        41: 33,  # horizontal meio grama penhasco
    }

    def __init__(
        self, tela, assets, transform, world_context=None, ciclo_dia_noite=None
    ):
        self.tela = tela
        self.assets = assets
        self.transform = transform
        self.world_context = world_context
        self.ciclo_dia_noite = ciclo_dia_noite
        self._cache_iluminacao = {}
        self.carregado = False

        self.tiles = {}
        self.mapa = []
        self.tiles_bioma = {}
        self.terrain_overrides = {}
        self._terrain_editor_path = "data/mapas/mapa1.json"
        self.cache_tiles = {}
        self.espumas = {}
        self.tiles_agua_bloqueados = set()
        self.relevos_agua = set()
        self._relevos_agua_config = []
        self.world = None
        self.regioes = {}
        self.recursos_iniciais = {"madeira": 0, "ouro": 0, "carne": 0}

        self.alturas = {}
        self.topos_penhasco = set()
        self.paredes_penhasco = {}
        self.relevos_flags = {}
        self.degraus = {}
        self.degraus_superficie = {}
        self.degraus_por_relevo = {}
        self.tiles_bloqueados = set()

        # Regras de colisão baseadas nos índices lógicos usados pelo tilemap.
        # Os índices 21..28 são paredes/áreas que não aceitam movimento nem
        # construção. As listas de borda não bloqueiam o tile inteiro:
        # bloqueiam apenas a aproximação excessiva da respectiva borda.
        self.TILES_BLOQUEADOS_COLISAO = frozenset(range(21, 29))
        self.TILES_BORDA_ESQUERDA_COLISAO = frozenset((4, 32, 29, 0, 8, 11, 14, 39))
        self.TILES_BORDA_DIREITA_COLISAO = frozenset((2, 6, 10, 13, 16, 31, 33, 40))
        self.MARGEM_BORDA_COLISAO = 8
        self.regras_colisao_visuais = {}

        self.largura = 0
        self.altura = 0
        self.offset_y = 0
        self.offset_x = -60

        self.frame_agua = 1
        self.tempo_agua = 0.0

        self._cache_terreno_base = None
        self._cache_terreno_overlay = None
        self._cache_viewport = None
        self._cache_viewport_key = None
        self._cache_overlay_viewport = None
        self._cache_overlay_viewport_key = None
        self._cache_terreno_pad_x = 256
        self._cache_terreno_pad_y = 256
        self.offset_agua_parada_x = -1
        self.offset_agua_parada_y = 85

        self.carregar_mapa("data/mapas/mapa1.json")

    # ==================================================
    def obter_regiao(self, regiao_id):
        return self.regioes.get(regiao_id)

    def obter_regiao_no_ponto(self, x, y):
        if self.world_context is not None:
            return self.world_context.region_service.no_pixel(
                x - self.offset_x, y - self.offset_y
            )
        return None

    # LOAD E INICIALIZAÇÃO
    # ==================================================

    def carregar_mapa(self, caminho):
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        if self.world_context is not None:
            self.world = self.world_context.world
            self.regioes = {
                regiao.id: RegiaoMapa(
                    id=regiao.id,
                    nome=regiao.nome,
                    tipo=regiao.tipo,
                    x=regiao.x,
                    y=regiao.y,
                    colunas=regiao.colunas,
                    linhas=regiao.linhas,
                )
                for regiao in self.world.regions.values()
            }
        else:
            # O renderer é uma camada de apresentação e não deve criar um
            # WorldService por conta própria. Instâncias isoladas usadas por
            # testes/visualizações podem operar apenas com a geometria bruta.
            self.world = None
            self.regioes = {}

        recursos_iniciais = dados.get("recursos_iniciais", {})
        self.recursos_iniciais = {
            "madeira": max(0, int(recursos_iniciais.get("madeira", 0))),
            "ouro": max(0, int(recursos_iniciais.get("ouro", 0))),
            "carne": max(0, int(recursos_iniciais.get("carne", 0))),
        }
        self.largura = dados.get("colunas", 0)
        self.altura = dados.get("linhas", 0)
        # Mantém a origem vertical usada pelo mapa original. Ao aumentar a
        # quantidade de linhas, a expansão acontece somente na parte inferior.
        self.offset_y = self.altura - 96

        self._processar_biomas(dados.get("biomas", []), dados.get("transicoes", []))
        self.terrain_overrides = {
            (int(item["x"]), int(item["y"])): item["tipo"]
            for item in dados.get("terrain_overrides", [])
            if 0 <= int(item.get("x", -1)) < self.largura
            and 0 <= int(item.get("y", -1)) < self.altura
            and item.get("tipo") in (self.TIPO_GRAMA, self.TIPO_AGUA_FUNDO)
        }
        self._processar_relevos(dados.get("relevos", []))
        self._degraus_config = list(dados.get("degraus", []))
        self._rios_config = list(dados.get("rios", []))
        self._espumas_config = list(dados.get("espumas", []))
        self._processar_degraus(self._degraus_config)
        self._processar_relevos_agua(dados.get("relevos_agua", []))

        self._construir_grid_mapa()
        self._aplicar_rios(dados.get("rios", []))
        self._aplicar_overrides_terreno()
        self._processar_espumas(self._espumas_config)
        self._pre_calcular_autotiling()
        self._pre_calcular_regras_colisao_visuais()

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

    def _segmentos_relevo(self, relevo):
        if "forma" not in relevo:
            return [relevo]

        forma = relevo.get("forma", [])
        if not forma:
            return []

        bordas = relevo.get("bordas", {})
        tem_esq = bordas.get("esquerda", True)
        tem_dir = bordas.get("direita", True)
        tem_sup = bordas.get("superior", True)
        tem_inf = bordas.get("inferior", True)
        altura = relevo.get("altura", 1)
        relevo_id = relevo.get("id")

        active_cells = set()
        for linha in forma:
            y = linha.get("y", 0)
            x_ini = linha.get("x", 0)
            cols = linha.get("colunas", 0)
            for x in range(x_ini, x_ini + cols):
                active_cells.add((x, y))

        if not active_cells:
            return []

        col_max_y = {}
        for x, y in active_cells:
            col_max_y[x] = max(col_max_y.get(x, y), y)

        def is_covered(neighbor_x, current_y):
            if (neighbor_x, current_y) in active_cells:
                return True
            if neighbor_x in col_max_y:
                return current_y == col_max_y[neighbor_x] + 1
            return False

        min_y = min(y for x, y in active_cells)
        max_y = max(y for x, y in active_cells)

        row_segments = []
        for y in range(min_y, max_y + 1):
            active_x = sorted([x for x, row_y in active_cells if row_y == y])
            if not active_x:
                continue

            current_group = []
            for x in active_x:
                sup_empty = (x, y - 1) not in active_cells
                inf_empty = (x, y + 1) not in active_cells

                if not current_group:
                    current_group = [(x, sup_empty, inf_empty)]
                else:
                    prev_x, prev_sup, prev_inf = current_group[-1]
                    if (
                        x == prev_x + 1
                        and sup_empty == prev_sup
                        and inf_empty == prev_inf
                    ):
                        current_group.append((x, sup_empty, inf_empty))
                    else:
                        start_x = current_group[0][0]
                        end_x = current_group[-1][0]
                        row_segments.append(
                            {
                                "x": start_x,
                                "y": y,
                                "colunas": len(current_group),
                                "linhas": 1,
                                "sup": current_group[0][1],
                                "inf": current_group[0][2],
                                "cov_left": is_covered(start_x - 1, y),
                                "cov_right": is_covered(end_x + 1, y),
                            }
                        )
                        current_group = [(x, sup_empty, inf_empty)]

            if current_group:
                start_x = current_group[0][0]
                end_x = current_group[-1][0]
                row_segments.append(
                    {
                        "x": start_x,
                        "y": y,
                        "colunas": len(current_group),
                        "linhas": 1,
                        "sup": current_group[0][1],
                        "inf": current_group[0][2],
                        "cov_left": is_covered(start_x - 1, y),
                        "cov_right": is_covered(end_x + 1, y),
                    }
                )

        merged_segments = []
        for seg in row_segments:
            merged = False
            for m in reversed(merged_segments):
                if (
                    m["x"] == seg["x"]
                    and m["colunas"] == seg["colunas"]
                    and m["y"] + m["linhas"] == seg["y"]
                    and not m["inf"]
                    and not seg["sup"]
                    and m["cov_left"] == seg["cov_left"]
                    and m["cov_right"] == seg["cov_right"]
                ):
                    m["linhas"] += seg["linhas"]
                    m["inf"] = seg["inf"]
                    merged = True
                    break
            if not merged:
                merged_segments.append(seg)

        final_segments = []
        for rect in merged_segments:
            borda_esq = tem_esq and not rect["cov_left"]
            borda_dir = tem_dir and not rect["cov_right"]

            final_segments.append(
                {
                    "id": relevo_id,
                    "altura": altura,
                    "x": rect["x"],
                    "y": rect["y"],
                    "colunas": rect["colunas"],
                    "linhas": rect["linhas"],
                    "tem_borda_esquerda": borda_esq,
                    "tem_borda_direita": borda_dir,
                    "tem_borda_superior": tem_sup and rect["sup"],
                    "tem_borda_inferior": tem_inf and rect["inf"],
                }
            )

        return final_segments

    def _processar_relevos(self, relevos):
        self._relevos_config = relevos
        self._relevos_segmentos = []
        self.alturas.clear()
        self.topos_penhasco.clear()
        self.paredes_penhasco.clear()
        self.relevos_flags.clear()

        for relevo in relevos:
            segmentos = self._segmentos_relevo(relevo)
            self._relevos_segmentos.extend(segmentos)

            for segmento in segmentos:
                altura = segmento.get("altura", 1)
                x = segmento["x"]
                y = segmento["y"]
                colunas_x = segmento["colunas"]
                linhas = segmento["linhas"]

                tem_esq = segmento.get("tem_borda_esquerda", True)
                tem_dir = segmento.get("tem_borda_direita", True)
                tem_sup = segmento.get("tem_borda_superior", True)
                tem_inf = segmento.get("tem_borda_inferior", True)

                linha_borda = y + 1

                for coluna in range(x, x + colunas_x):
                    self.alturas[(coluna, linha_borda)] = altura
                    self.topos_penhasco.add((coluna, linha_borda))
                    self.paredes_penhasco[(coluna, linha_borda)] = max(
                        linhas, self.paredes_penhasco.get((coluna, linha_borda), 0)
                    )

                    self.relevos_flags[(coluna, linha_borda)] = {
                        "esq": tem_esq,
                        "dir": tem_dir,
                        "sup": tem_sup,
                        "inf": tem_inf,
                        "primeira_col": x,
                        "ultima_col": x + colunas_x - 1,
                    }

                linha_inicio_parede = linha_borda + 1
                for linha in range(
                    linha_inicio_parede, linha_inicio_parede + linhas + 1
                ):
                    for coluna in range(x, x + colunas_x):
                        self.alturas[(coluna, linha)] = altura

    def _processar_degraus(self, degraus):
        self.degraus.clear()
        self.degraus_superficie.clear()
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
                dados_degrau = {
                    "relevo_id": relevo_id,
                    "direcao": grupo["direcao"],
                    "altura_baixa": altura_baixa,
                    "altura_alta": altura_alta,
                    "tile": (coluna, linha),
                    # O sprite do degrau é desenhado 1 tile para cima.
                    # Portanto a superfície visual transitável pertence à
                    # célula imediatamente acima da célula lógica.
                    "superficie": (coluna, linha - 1),
                }
                self.degraus[(coluna, linha)] = dados_degrau
                if linha > 0:
                    self.degraus_superficie[(coluna, linha - 1)] = dados_degrau
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

    def _aplicar_overrides_terreno(self):
        for (coluna, linha), tipo in self.terrain_overrides.items():
            if self._coordenada_valida(coluna, linha):
                self.mapa[linha][coluna]["tipo"] = tipo
                self.mapa[linha][coluna]["altura"] = self.alturas.get(
                    (coluna, linha), 0
                )

    def definir_terreno_editor(self, coluna, linha, tipo):
        if not self._coordenada_valida(coluna, linha):
            return False
        if tipo not in (self.TIPO_GRAMA, self.TIPO_AGUA_FUNDO):
            return False
        self.terrain_overrides[(int(coluna), int(linha))] = tipo
        self.mapa[linha][coluna]["tipo"] = tipo
        self._recalcular_terreno_editor()
        return True

    def _recalcular_terreno_editor(self):
        self._pre_calcular_autotiling()
        self._pre_calcular_regras_colisao_visuais()
        self._cache_terreno_base = None
        self._cache_terreno_overlay = None
        self._cache_viewport = None
        self._cache_viewport_key = None
        self._cache_overlay_viewport = None
        self._cache_overlay_viewport_key = None
        if self.carregado:
            self._construir_cache_terreno()

    def salvar_terreno_editor(self):
        caminho = self._terrain_editor_path
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        dados["terrain_overrides"] = [
            {"x": coluna, "y": linha, "tipo": tipo}
            for (coluna, linha), tipo in sorted(self.terrain_overrides.items())
        ]
        dados["relevos"] = list(self._relevos_config)
        dados["espumas"] = list(getattr(self, "_espumas_config", []))
        import shutil

        backup = caminho + ".bak"
        shutil.copy2(caminho, backup)
        temp = caminho + ".tmp"
        with open(temp, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
            arquivo.write("\n")
        import os

        os.replace(temp, caminho)

    def _reindexar_camadas_editor(self):
        self._processar_relevos(list(self._relevos_config))
        self._processar_degraus(list(getattr(self, "_degraus_config", [])))
        self._processar_relevos_agua(list(self._relevos_agua_config))
        self._construir_grid_mapa()
        self._aplicar_rios(getattr(self, "_rios_config", []))
        self._aplicar_overrides_terreno()
        self._processar_espumas(list(getattr(self, "_espumas_config", [])))
        self._pre_calcular_autotiling()
        self._pre_calcular_regras_colisao_visuais()
        self._cache_terreno_base = None
        self._cache_terreno_overlay = None
        self._cache_viewport = None
        self._cache_viewport_key = None
        self._cache_overlay_viewport = None
        self._cache_overlay_viewport_key = None
        if self.carregado:
            self._construir_cache_terreno()

    def adicionar_relevo_editor(self, x, y, colunas, linhas, altura=1):
        if (
            not self._coordenada_valida(x, y)
            or x + colunas > self.largura
            or y + linhas > self.altura
        ):
            return None
        relevo_id = max([int(r.get("id", 0)) for r in self._relevos_config] or [0]) + 1
        forma = [
            {"y": int(y + linha), "x": int(x), "colunas": int(colunas)}
            for linha in range(int(linhas))
        ]
        relevo = {
            "id": relevo_id,
            "altura": int(altura),
            "forma": forma,
            "bordas": {
                "esquerda": True,
                "direita": True,
                "superior": True,
                "inferior": True,
            },
        }
        self._relevos_config = list(self._relevos_config) + [relevo]
        self._reindexar_camadas_editor()
        return relevo_id

    def _configurar_espuma_editor(self, coluna, linha):
        if not self._coordenada_valida(coluna, linha):
            return None

        tipo = self.obter_tipo(coluna, linha)

        def agua_em(c, lin):
            return (
                self._coordenada_valida(c, lin)
                and self.obter_tipo(c, lin) == self.TIPO_AGUA_FUNDO
            )

        def grama_em(c, lin):
            return (
                self._coordenada_valida(c, lin)
                and self.obter_tipo(c, lin) == self.TIPO_GRAMA
            )

        if tipo == self.TIPO_AGUA_FUNDO:
            if grama_em(coluna, linha + 1):
                return int(coluna), int(linha), 0, -6

            if grama_em(coluna, linha - 1):
                return int(coluna), int(linha - 1), 0, 1

            if grama_em(coluna - 1, linha):
                return int(coluna), int(linha), -(TILE_SIZE // 2), 0
            if grama_em(coluna + 1, linha):
                return int(coluna), int(linha), TILE_SIZE // 2, 0

            return int(coluna), int(linha), 0, 0

        if tipo == self.TIPO_GRAMA:
            if agua_em(coluna, linha + 1):
                print("TIPO_GRAMA1")
                return int(coluna), int(linha), 0, -1

            if agua_em(coluna, linha - 1):
                print("TIPO_GRAMA2")
                return int(coluna), int(linha - 1), -(TILE_SIZE // 1), 0

            if agua_em(coluna - 1, linha):
                print("TIPO_GRAMA3")
                return int(coluna), int(linha - 1), -70, -1
            if agua_em(coluna + 1, linha):
                print("TIPO_GRAMA4")
                return int(coluna), int(linha - 1), -55, 0

        return None

    def adicionar_espuma_editor(self, x, y, colunas, linhas):
        if (
            not self._coordenada_valida(x, y)
            or x + colunas > self.largura
            or y + linhas > self.altura
        ):
            return None

        configuracoes = []
        vistos = set()
        for linha in range(int(y), int(y) + int(linhas)):
            for coluna in range(int(x), int(x) + int(colunas)):
                config = self._configurar_espuma_editor(coluna, linha)
                if config is None:
                    return None
                ancora_x, ancora_y, offset_x, offset_y = config
                chave = (ancora_x, ancora_y, offset_x, offset_y)
                if chave in vistos:
                    continue
                vistos.add(chave)
                configuracoes.append((ancora_x, ancora_y, offset_x, offset_y))

        if not configuracoes:
            return None

        idx_base = len(getattr(self, "_espumas_config", [])) + 1
        novas = []
        for indice, (coluna, linha, offset_x, offset_y) in enumerate(configuracoes):
            novas.append(
                {
                    "id": f"editor_{idx_base + indice}",
                    "origem": "editor",
                    "relevo_agua_id": None,
                    "offset_x": int(offset_x),
                    "offset_y": int(offset_y),
                    "x": int(coluna),
                    "y": int(linha),
                    "colunas": 1,
                    "linhas": 1,
                }
            )

        self._espumas_config = list(getattr(self, "_espumas_config", [])) + novas
        self._processar_espumas(self._espumas_config)
        self._cache_viewport = None
        self._cache_viewport_key = None
        return novas[0]["id"]

    def _processar_espumas(self, espumas):
        self.espumas = {}
        self.tiles_agua_bloqueados = set()
        for grupo in espumas:
            offset_x = grupo.get("offset_x", 0)
            offset_y = grupo.get("offset_y", 0)

            if (
                grupo.get("relevo_agua_id") is None
                and offset_y == -TILE_SIZE
                and not (
                    grupo.get("origem") == "editor"
                    or str(grupo.get("id", "")).startswith("editor_")
                )
            ):
                offset_y = 0

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
                    if self._coordenada_valida(coluna, linha):
                        self.tiles_agua_bloqueados.add((coluna, linha))

    def _pre_calcular_autotiling(self):
        for linha in range(self.altura):
            for coluna in range(self.largura):
                if self.obter_tipo(coluna, linha) == self.TIPO_GRAMA:
                    self.mapa[linha][coluna]["sprite_index"] = (
                        self._calcular_indice_grama(coluna, linha)
                    )

    def _adicionar_regra_visual(self, coluna, linha, indice):
        if not self._coordenada_valida(coluna, linha):
            return
        self.regras_colisao_visuais.setdefault((coluna, linha), set()).add(indice)

    def _pre_calcular_regras_colisao_visuais(self):
        self.regras_colisao_visuais.clear()

        # Camada de grama: registra o índice lógico efetivamente escolhido pelo
        # autotiling para cada célula física.
        for linha in range(self.altura):
            for coluna in range(self.largura):
                if self.obter_tipo(coluna, linha) == self.TIPO_GRAMA:
                    self._adicionar_regra_visual(
                        coluna,
                        linha,
                        self.mapa[linha][coluna].get("sprite_index", 9),
                    )

        # Relevos de penhasco. Reproduz as mesmas posições físicas usadas pelo
        # renderer para que a colisão acompanhe a borda desenhada, inclusive
        # quando o índice não é o sprite base da célula.
        for relevo in getattr(self, "_relevos_segmentos", self._relevos_config):
            x = relevo["x"]
            y = relevo["y"]
            colunas = relevo["colunas"]
            linhas = relevo["linhas"]

            tem_esq = relevo.get("tem_borda_esquerda", True)
            tem_dir = relevo.get("tem_borda_direita", True)
            tem_sup = relevo.get("tem_borda_superior", True)
            tem_inf = relevo.get("tem_borda_inferior", True)

            linha_topo = y + 1

            for coluna in range(x, x + colunas):
                interno = self.eh_penhasco_interno(coluna, linha_topo)
                limite_iteracao = linhas if interno else linhas - 1
                limite_iteracao = max(0, limite_iteracao)

                w = self.existe_penhasco(coluna - 1, linha_topo)
                if coluna == x and not tem_esq:
                    w = True

                e = self.existe_penhasco(coluna + 1, linha_topo)
                if coluna == x + colunas - 1 and not tem_dir:
                    e = True

                if interno and tem_sup:
                    if not w and not e:
                        topo = 5
                    elif not w:
                        topo = 4
                    elif not e:
                        topo = 6
                    else:
                        topo = 5
                    self._adicionar_regra_visual(coluna, linha_topo, topo)

                inicio_meio = 1 if interno else 0
                if interno and not tem_sup:
                    inicio_meio = 0

                for i in range(inicio_meio, limite_iteracao):
                    linha_sprite = linha_topo + i
                    if not w:
                        meio = 32
                    elif not e:
                        meio = 33
                    else:
                        meio = 9
                    self._adicionar_regra_visual(coluna, linha_sprite, meio)

                if tem_inf:
                    linha_borda = linha_topo + limite_iteracao
                    if not w and not e:
                        borda = 30
                    elif not w:
                        borda = 29
                    elif not e:
                        borda = 31
                    else:
                        borda = 30
                    self._adicionar_regra_visual(coluna, linha_borda, borda)

                    linha_parede = linha_topo + (linhas + 1 if interno else linhas)
                    if not w and not e:
                        parede = 22
                    elif not w:
                        parede = 21
                    elif not e:
                        parede = 23
                    else:
                        parede = 22
                    self._adicionar_regra_visual(coluna, linha_parede, parede)

        # Relevos de água. Os frames da água animada/parada também ficam
        # bloqueados pelo tipo lógico da água, enquanto estas bordas adicionais
        # entram na máscara visual para manter a mesma regra das bordas de
        # penhasco.
        for relevo in self._relevos_agua_config:
            linhas = relevo.get("linhas", 1)
            primeira_coluna = relevo["x"]
            colunas = relevo["colunas"]
            ultima_coluna = primeira_coluna + colunas - 1
            linha_agua = relevo["y"]

            tem_esq = relevo.get("tem_borda_esquerda", True)
            tem_dir = relevo.get("tem_borda_direita", True)
            tem_sup = relevo.get("tem_borda_superior", True)
            tem_inf = relevo.get("tem_borda_inferior", True)

            if linhas > 1:
                for nivel in range(linhas):
                    is_topo = nivel == linhas - 1
                    is_base = nivel == 0

                    if is_topo and not tem_sup:
                        continue
                    if is_base and not tem_inf:
                        continue

                    linha_fisica = (
                        linha_agua - (linhas + 2)
                        if is_topo
                        else linha_agua - (nivel + 3)
                    )

                    for coluna in range(primeira_coluna, ultima_coluna + 1):
                        if coluna == primeira_coluna and tem_esq:
                            indice = 32
                        elif coluna == ultima_coluna and tem_dir:
                            indice = 33
                        else:
                            indice = 9
                        self._adicionar_regra_visual(coluna, linha_fisica, indice)

            for coluna in range(primeira_coluna, ultima_coluna + 1):
                esquerda = (coluna - 1) >= primeira_coluna
                direita = (coluna + 1) <= ultima_coluna
                if not esquerda:
                    indice = 25
                elif not direita:
                    indice = 27
                else:
                    indice = 26
                self._adicionar_regra_visual(coluna, linha_agua - 1, indice)

        # Um degrau é uma passagem física através da borda do relevo. O
        # autotiling do penhasco pode registrar nessa mesma célula uma borda
        # esquerda/direita que bloquearia a aproximação exatamente no ponto
        # em que o Sapudo precisa atravessar a escada. O degrau tem prioridade
        # de navegação, então removemos somente as regras visuais de colisão da
        # própria célula do degrau, preservando as paredes ao redor.
        for coord_degrau in self.degraus:
            self.regras_colisao_visuais[coord_degrau] = set()
        for coord_superficie in self.degraus_superficie:
            self.regras_colisao_visuais[coord_superficie] = set()

    def obter_regras_colisao(self, coluna, linha):
        return self.regras_colisao_visuais.get((coluna, linha), ())

    def pode_andar_pixel(self, x, y, altura, margem_borda=None, verificar_borda=True):
        coluna, linha = self.pixel_para_tile(x, y)

        if (
            not self.pode_andar(coluna, linha, altura)
            or (coluna, linha) in self.tiles_agua_bloqueados
        ):
            return False

        regras = self.obter_regras_colisao(coluna, linha)

        if any(indice in self.TILES_BLOQUEADOS_COLISAO for indice in regras):
            return False

        if not verificar_borda:
            return True

        margem = (
            self.MARGEM_BORDA_COLISAO
            if margem_borda is None
            else max(0, int(margem_borda))
        )
        tile_x, _ = self.tile_para_pixel(coluna, linha)

        bateu_esquerda = any(
            i in self.TILES_BORDA_ESQUERDA_COLISAO for i in regras
        ) and (x <= tile_x + margem)
        bateu_direita = any(i in self.TILES_BORDA_DIREITA_COLISAO for i in regras) and (
            x >= tile_x + TILE_SIZE - margem
        )

        return not (bateu_esquerda or bateu_direita)

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
                return 9
            if not v["sw"]:
                return 19
            if not v["se"]:
                return 9
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
        self._construir_cache_terreno()
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
        return self.pode_andar_pixel(x, y, altura)

    def pode_andar(self, coluna, linha, altura):
        if (
            not self._coordenada_valida(coluna, linha)
            or (coluna, linha) in self.tiles_bloqueados
        ):
            return False
        if self.obter_tipo(coluna, linha) != self.TIPO_GRAMA:
            return False

        altura_tile = self.obter_altura(coluna, linha)
        if altura_tile == altura:
            return True

        # A superfície visual do degrau fica exatamente uma célula acima
        # da célula lógica configurada no mapa. Essa célula precisa aceitar
        # as duas alturas enquanto o personagem atravessa a escada.
        degrau = self.obter_degrau(coluna, linha)
        if degrau:
            return altura in (degrau["altura_baixa"], degrau["altura_alta"])

        degrau_superficie = self.degraus_superficie.get((coluna, linha))
        if degrau_superficie:
            return altura in (
                degrau_superficie["altura_baixa"],
                degrau_superficie["altura_alta"],
            )

        return False

    def obter_degrau(self, coluna, linha):
        return self.degraus.get((coluna, linha)) or self.degraus_superficie.get(
            (coluna, linha)
        )

    def eh_degrau(self, coluna, linha):
        return (coluna, linha) in self.degraus or (
            coluna,
            linha,
        ) in self.degraus_superficie

    def obter_transicao_degrau(
        self, origem_coluna, origem_linha, destino_coluna, destino_linha, altura
    ):
        origem = self.obter_degrau(*((origem_coluna, origem_linha)))
        destino = self.obter_degrau(*((destino_coluna, destino_linha)))

        if origem is None and destino is None:
            return None

        # A transição acontece ao entrar/sair da SUPERFÍCIE visual do degrau.
        # Não esperamos o personagem chegar na célula lógica um tile abaixo.
        destino_altura_base = self.obter_altura(destino_coluna, destino_linha)

        if destino is not None:
            baixa = destino["altura_baixa"]
            alta = destino["altura_alta"]
            # Entrando na superfície de um degrau, vamos para o lado oposto
            # à altura atual.
            if altura == baixa and alta != destino_altura_base:
                return alta
            if altura == alta and baixa != destino_altura_base:
                return baixa

        if origem is not None and destino is None:
            baixa = origem["altura_baixa"]
            alta = origem["altura_alta"]
            if altura == alta:
                return baixa

        # Se o destino já possui a altura do lado alto/baixo, mantém.
        if destino_altura_base != altura and (
            destino_altura_base == 0
            or any(
                destino_altura_base == d["altura_alta"] for d in (origem, destino) if d
            )
        ):
            return destino_altura_base

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

    def _margem_vertical_relevos_tiles(self):
        """Calcula quantas linhas de ancora acima da camera ainda podem desenhar.

        As paredes de penhasco sao ancoradas no tile do topo e podem se
        estender varios tiles para baixo. Se iterarmos apenas as ancoras dentro
        do viewport, uma parede ainda visivel pode desaparecer quando a camera
        desce um pouco. A margem e derivada dos dados reais do relevo para nao
        depender de um valor magico.
        """
        maior_extensao = 0
        for paredes in getattr(self, "paredes_penhasco", {}).values():
            try:
                maior_extensao = max(maior_extensao, int(paredes) + 2)
            except (TypeError, ValueError):
                continue

        # Relevos de agua tambem usam offsets verticais que podem ultrapassar
        # uma celula; mantemos uma folga pequena para bordas/sombras.
        for relevo in getattr(self, "_relevos_agua_config", []):
            try:
                maior_extensao = max(maior_extensao, int(relevo.get("linhas", 1)) + 3)
            except (TypeError, ValueError):
                continue

        return max(2, maior_extensao)

    def _iterar_area_visivel(self, camera):
        inicio_x = max(-2, int((camera.x - self.offset_x) // TILE_SIZE) - 2)
        fim_x = min(
            self.largura + 2,
            int((camera.x + camera.largura - self.offset_x) // TILE_SIZE) + 3,
        )

        linha_camera = int((camera.y - self.offset_y) // TILE_SIZE)
        margem_relevos = self._margem_vertical_relevos_tiles()
        # Importante: uma parede pode comecar acima do viewport e continuar
        # visivel abaixo dele. Incluimos as ancoras dessa faixa superior.
        inicio_y = max(-2, linha_camera - margem_relevos)
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

        self._renderizar_cache_terreno(camera)
        self._renderizar_camada_espuma(camera)
        self._renderizar_cache_terreno_overlay(camera)

    def _construir_cache_terreno(self):
        if (
            self._cache_terreno_base is not None
            and self._cache_terreno_overlay is not None
        ):
            return

        largura = self.largura * TILE_SIZE + self._cache_terreno_pad_x * 2
        altura = self.altura * TILE_SIZE + self._cache_terreno_pad_y * 2

        class _CameraCache:
            def __init__(self, x, y, largura, altura):
                self.x = x
                self.y = y
                self.largura = largura
                self.altura = altura
                self.zoom = 1.0
                self.largura_mundo_visivel = largura
                self.altura_mundo_visivel = altura

        camera_cache = _CameraCache(
            -self._cache_terreno_pad_x,
            -self._cache_terreno_pad_y,
            largura,
            altura,
        )

        tela_anterior = self.tela
        try:
            # Base: fica abaixo da espuma.
            base = self.tela.__class__((largura, altura))
            base.fill((0, 0, 0, 0))
            self.tela = base
            self._renderizar_fundo(camera_cache)
            self._renderizar_agua_editor(camera_cache)
            self._cache_terreno_base = base

            # Overlay: fica acima da espuma.
            overlay = self.tela.__class__((largura, altura))
            overlay.fill((0, 0, 0, 0))
            self.tela = overlay
            self._renderizar_camada_grama(camera_cache)
            self._renderizar_sombras_relevos(camera_cache)
            self._renderizar_camada_degraus(camera_cache)
            self._renderizar_penhascos(camera_cache)
            self._renderizar_relevos_agua(camera_cache)
            self._renderizar_grama_relevos_agua(camera_cache)
            self._cache_terreno_overlay = overlay
        finally:
            self.tela = tela_anterior

    def _renderizar_agua_editor(self, camera):
        sprite = getattr(self, "agua_parada", None)
        if sprite is None:
            return
        for (coluna, linha), tipo in self.terrain_overrides.items():
            if tipo != self.TIPO_AGUA_FUNDO:
                continue
            self._desenhar_sprite_cenario(sprite, coluna, linha, camera)

    def _obter_cache_terreno_viewport(self, camera):
        base = self._cache_terreno_base
        if base is None:
            return None, (0, 0)

        zoom = max(0.01, float(camera.zoom))
        largura_mundo = max(1.0, float(camera.largura) / zoom)
        altura_mundo = max(1.0, float(camera.altura) / zoom)

        # O pixel 0 da superfície-base representa o mundo
        # (-pad_x, -pad_y).
        origem_cache_x = float(camera.x) + self._cache_terreno_pad_x
        origem_cache_y = float(camera.y) + self._cache_terreno_pad_y

        origem_x = int(origem_cache_x // 1)
        origem_y = int(origem_cache_y // 1)
        fracao_x = origem_cache_x - origem_x
        fracao_y = origem_cache_y - origem_y

        largura_origem = max(2, int(largura_mundo) + 2)
        altura_origem = max(2, int(altura_mundo) + 2)

        viewport_base = None
        src_x = max(0, origem_x)
        src_y = max(0, origem_y)
        src_right = min(base.get_width(), origem_x + largura_origem)
        src_bottom = min(base.get_height(), origem_y + altura_origem)

        if (
            src_right > src_x
            and src_bottom > src_y
            and origem_x >= 0
            and origem_y >= 0
            and origem_x + largura_origem <= base.get_width()
            and origem_y + altura_origem <= base.get_height()
        ):
            viewport_base = base.subsurface(
                (origem_x, origem_y, largura_origem, altura_origem)
            )
        else:
            viewport_base = self.tela.__class__((largura_origem, altura_origem))
            viewport_base.fill((0, 0, 0, 0))

            if src_right > src_x and src_bottom > src_y:
                viewport_base.blit(
                    base,
                    (src_x - origem_x, src_y - origem_y),
                    (
                        src_x,
                        src_y,
                        src_right - src_x,
                        src_bottom - src_y,
                    ),
                )

        if abs(zoom - 1.0) < 1e-9:
            viewport = viewport_base
        else:
            viewport_largura = max(1, int(round(largura_origem * zoom)))
            viewport_altura = max(1, int(round(altura_origem * zoom)))
            cache_key = (
                id(base),
                origem_x,
                origem_y,
                largura_origem,
                altura_origem,
                round(zoom, 6),
            )

            if self._cache_viewport_key != cache_key:
                if getattr(kivy_adapter, "IS_BROWSER", False):
                    viewport = kivy_adapter.transform.scale(
                        viewport_base,
                        (viewport_largura, viewport_altura),
                    )
                else:
                    viewport = kivy_adapter.transform.smoothscale(
                        viewport_base,
                        (viewport_largura, viewport_altura),
                    )
                self._cache_viewport = viewport
                self._cache_viewport_key = cache_key
            else:
                viewport = self._cache_viewport

        # A origem do recorte está em floor(camera), portanto somente a
        # fração restante precisa ser aplicada no destino.
        return viewport, (fracao_x * zoom, fracao_y * zoom)

    def _renderizar_cache_terreno(self, camera):
        viewport, deslocamento = self._obter_cache_terreno_viewport(camera)
        if viewport is None:
            return

        deslocamento_x, deslocamento_y = deslocamento
        viewport = self._aplicar_iluminacao(viewport)
        self.tela.blit(
            viewport,
            (
                int(round(-deslocamento_x)),
                int(round(-deslocamento_y)),
            ),
        )

    def _renderizar_cache_terreno_overlay(self, camera):
        viewport, deslocamento = self._obter_cache_terreno_overlay_viewport(camera)
        if viewport is None:
            return

        deslocamento_x, deslocamento_y = deslocamento
        self.tela.blit(
            viewport,
            (
                int(round(-deslocamento_x)),
                int(round(-deslocamento_y)),
            ),
        )

    def _obter_cache_terreno_overlay_viewport(self, camera):
        """Retorna somente a área visível da camada acima da espuma."""
        overlay = self._cache_terreno_overlay
        if overlay is None:
            return None, (0, 0)

        zoom = max(0.01, float(camera.zoom))
        largura_mundo = max(1.0, float(camera.largura) / zoom)
        altura_mundo = max(1.0, float(camera.altura) / zoom)

        origem_cache_x = float(camera.x) + self._cache_terreno_pad_x
        origem_cache_y = float(camera.y) + self._cache_terreno_pad_y

        origem_x = int(origem_cache_x // 1)
        origem_y = int(origem_cache_y // 1)
        fracao_x = origem_cache_x - origem_x
        fracao_y = origem_cache_y - origem_y

        largura_origem = max(2, int(largura_mundo) + 2)
        altura_origem = max(2, int(altura_mundo) + 2)

        src_x = max(0, origem_x)
        src_y = max(0, origem_y)
        src_right = min(overlay.get_width(), origem_x + largura_origem)
        src_bottom = min(overlay.get_height(), origem_y + altura_origem)

        if (
            src_right > src_x
            and src_bottom > src_y
            and origem_x >= 0
            and origem_y >= 0
            and origem_x + largura_origem <= overlay.get_width()
            and origem_y + altura_origem <= overlay.get_height()
        ):
            viewport_base = overlay.subsurface(
                (origem_x, origem_y, largura_origem, altura_origem)
            )
        else:
            viewport_base = self.tela.__class__((largura_origem, altura_origem))
            viewport_base.fill((0, 0, 0, 0))
            if src_right > src_x and src_bottom > src_y:
                viewport_base.blit(
                    overlay,
                    (src_x - origem_x, src_y - origem_y),
                    (
                        src_x,
                        src_y,
                        src_right - src_x,
                        src_bottom - src_y,
                    ),
                )

        if abs(zoom - 1.0) < 1e-9:
            viewport = viewport_base
        else:
            viewport_largura = max(1, int(round(largura_origem * zoom)))
            viewport_altura = max(1, int(round(altura_origem * zoom)))
            cache_key = (
                id(overlay),
                origem_x,
                origem_y,
                largura_origem,
                altura_origem,
                round(zoom, 6),
            )
            if self._cache_overlay_viewport_key != cache_key:
                if getattr(kivy_adapter, "IS_BROWSER", False):
                    viewport = kivy_adapter.transform.scale(
                        viewport_base,
                        (viewport_largura, viewport_altura),
                    )
                else:
                    viewport = kivy_adapter.transform.smoothscale(
                        viewport_base,
                        (viewport_largura, viewport_altura),
                    )
                self._cache_overlay_viewport = viewport
                self._cache_overlay_viewport_key = cache_key
            else:
                viewport = self._cache_overlay_viewport

        return viewport, (fracao_x * zoom, fracao_y * zoom)

    def _atualizar_animacao_agua(self, dt):
        self.tempo_agua += dt
        if self.tempo_agua >= 0.08:
            self.tempo_agua = 0
            self.frame_agua = (self.frame_agua % len(self.tiles_agua)) + 1

    def _renderizar_camada_espuma(self, camera):
        if not getattr(self, "tiles_agua", None):
            return
        indice = max(0, min(len(self.tiles_agua) - 1, self.frame_agua - 1))
        sprite = self.tiles_agua[indice]
        if sprite is None:
            return
        for (coluna, linha), dados in self.espumas.items():
            if not self._coordenada_valida(coluna, linha):
                continue
            if not self._celula_toca_agua_ou_margem(coluna, linha):
                continue
            self._desenhar_sprite_cenario(
                sprite,
                coluna,
                linha,
                camera,
                offset_x=dados["offset_x"],
                offset_y=dados["offset_y"],
            )

    def _celula_toca_agua_ou_margem(self, coluna, linha):
        if self.obter_tipo(coluna, linha) == self.TIPO_AGUA_FUNDO:
            return True
        for nc, nl in (
            (coluna - 1, linha),
            (coluna + 1, linha),
            (coluna, linha - 1),
            (coluna, linha + 1),
        ):
            if (
                self._coordenada_valida(nc, nl)
                and self.obter_tipo(nc, nl) == self.TIPO_AGUA_FUNDO
            ):
                return True
        return False

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
        for relevo in getattr(self, "_relevos_segmentos", self._relevos_config):
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
        for relevo in getattr(self, "_relevos_segmentos", self._relevos_config):
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

    def _aplicar_iluminacao(self, sprite, chave_extra=None):
        if self.ciclo_dia_noite is None:
            return sprite

        fator_luz = self.ciclo_dia_noite.nivel_luz
        if abs(fator_luz - 1.0) < 1e-6:
            return sprite

        # A chave usa o sprite-fonte e o período, nunca uma textura criada
        # durante o próprio render. Isso permite reaproveitar a mesma textura
        # iluminada por todas as células idênticas do mapa.
        cache_key = (id(sprite), self.ciclo_dia_noite.chave_iluminacao, chave_extra)
        cache_entry = self._cache_iluminacao.get(cache_key)
        iluminado = None
        if cache_entry is not None:
            fonte_cacheada, iluminado = cache_entry
            if fonte_cacheada is not sprite:
                iluminado = None

        if iluminado is None:
            iluminado = sprite.copy()
            iluminado.ajustar_luminosidade(fator_luz)
            # Guarda o sprite-fonte junto com o resultado para impedir que uma
            # reutilização de id() faça um sprite receber a aparência de outro.
            self._cache_iluminacao[cache_key] = (sprite, iluminado)

            if len(self._cache_iluminacao) > 256:
                for chave in list(self._cache_iluminacao)[:64]:
                    del self._cache_iluminacao[chave]
        return iluminado

    def _desenhar_sprite_cenario(
        self, sprite, coluna, linha, camera, penhasco_size=0, offset_x=0, offset_y=0
    ):
        x = (self.offset_x + coluna * TILE_SIZE - camera.x) * camera.zoom
        y = (self.offset_y + linha * TILE_SIZE - camera.y) * camera.zoom

        largura_zoom = int(sprite.get_width() * camera.zoom)
        altura_zoom = int(sprite.get_height() * camera.zoom)
        cache_key = (id(sprite), largura_zoom, altura_zoom)
        sprite_escalado = self._cache_iluminacao.get(("escala",) + cache_key)
        if sprite_escalado is None:
            sprite_escalado = self.transform.escalar(
                sprite, (largura_zoom, altura_zoom)
            )
            self._cache_iluminacao[("escala",) + cache_key] = sprite_escalado
        sprite_escalado = self._aplicar_iluminacao(
            sprite_escalado, chave_extra=cache_key
        )

        pos_x = x + offset_x * camera.zoom
        pos_y = y + penhasco_size + offset_y * camera.zoom
        self.tela.blit(sprite_escalado, (pos_x, pos_y))

    def _renderizar_fundo(self, camera):
        # O índice da repetição é calculado em coordenadas do mundo. Usar o
        # tamanho já escalado (pixels de tela) para dividir camera.x/y mistura
        # espaços e causa saltos no fundo durante zoom e arrasto, sobretudo na
        # versão web.
        mundo_w = max(1, self.agua_parada.get_width())
        mundo_h = max(1, self.agua_parada.get_height())
        largura_zoom = max(1, int(round(mundo_w * camera.zoom)))
        altura_zoom = max(1, int(round(mundo_h * camera.zoom)))
        fundo_cache_key = ("fundo", id(self.agua_parada), largura_zoom, altura_zoom)
        sprite = self._cache_iluminacao.get(fundo_cache_key)
        if sprite is None:
            sprite = self.transform.escalar(
                self.agua_parada,
                (largura_zoom, altura_zoom),
            )
            self._cache_iluminacao[fundo_cache_key] = sprite

        inicio_x = int(camera.x // mundo_w) - 1
        fim_x = int((camera.x + camera.largura_mundo_visivel) // mundo_w) + 2
        inicio_y = int(camera.y // mundo_h) - 1
        fim_y = int((camera.y + camera.altura_mundo_visivel) // mundo_h) + 2

        for y in range(inicio_y, fim_y):
            for x in range(inicio_x, fim_x):
                self.tela.blit(
                    self._aplicar_iluminacao(sprite),
                    (
                        int(round(x * mundo_w * camera.zoom - camera.x * camera.zoom)),
                        int(round(y * mundo_h * camera.zoom - camera.y * camera.zoom)),
                    ),
                )
