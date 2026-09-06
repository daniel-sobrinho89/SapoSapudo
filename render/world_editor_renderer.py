from __future__ import annotations

import utils.kivy_adapter as kivy_adapter
from utils.config import ALTURA, LARGURA, TILE_SIZE
from utils.kivy_adapter import Rect


class WorldEditorRenderer:
    """Editor visual de autoria do mundo, ativado por F4."""

    CORES_MODO = {
        "regiao": (96, 220, 125),
        "objeto": (155, 120, 245),
        "terreno": (110, 205, 190),
    }

    MODOS = (
        ("regiao", "REGIÃO"),
        ("objeto", "OBJETO"),
        ("terreno", "TERRENO"),
    )

    def __init__(self, tela, editor):
        self.tela = tela
        self.editor = editor
        self._botoes = []

    @property
    def ativo(self):
        return self.editor.ativo

    def _add_botao(self, rect, label, action, selected=False):
        self._botoes.append((rect, label, action))
        bg = (
            self.CORES_MODO.get(self.editor.modo, (60, 80, 90))
            if selected
            else (36, 45, 52)
        )
        fg = (15, 20, 20) if selected else (235, 240, 242)
        kivy_adapter.draw.rect(self.tela, bg, rect)
        kivy_adapter.draw.rect(self.tela, (95, 112, 120, 255), rect, width=1)
        kivy_adapter.draw.text(self.tela, label, (rect.x + 7, rect.y + 7), fg, 11)

    def _offsets(self, context):
        tilemap = getattr(context, "tilemap_renderer", None)
        return (
            getattr(tilemap, "offset_x", -60) if tilemap else -60,
            getattr(tilemap, "offset_y", -66) if tilemap else -66,
        )

    def renderizar(self, context, camera):
        if not self.ativo or context is None:
            return
        self._botoes = []
        self._render_mundo(context, camera)
        self._render_topbar()
        self._render_left(context)
        self._render_right(context)

    def _render_mundo(self, context, camera):
        ox, oy = self._offsets(context)
        modo = self.editor.modo
        selecionado = self.editor.item_selecionado()

        if modo == "regiao":
            colecao = context.world.regions
            cor = self.CORES_MODO[modo]
            for item in colecao.values():
                rect = camera.tela_rect(
                    Rect(
                        ox + item.x * TILE_SIZE,
                        oy + item.y * TILE_SIZE,
                        item.colunas * TILE_SIZE,
                        item.linhas * TILE_SIZE,
                    )
                )
                kivy_adapter.draw.rect(self.tela, cor + (235,), rect, width=2)

        # Regiões usam apenas contornos para preservar a leitura do mapa.
        if modo == "objeto":
            runtime = getattr(context, "_entidades_runtime", {})
            for spawn in self.editor.spawns_visuais():
                entidade = runtime.get(spawn.id)
                px_mundo = getattr(entidade, "x", spawn.posicao.x)
                py_mundo = getattr(entidade, "y", spawn.posicao.y)
                c, lin = context._pixel_para_tile(px_mundo, py_mundo)
                px, py = camera.tela(
                    ox + c * TILE_SIZE + TILE_SIZE // 2,
                    oy + lin * TILE_SIZE + TILE_SIZE // 2,
                )
                cor = (
                    (255, 245, 120)
                    if spawn.id == (self.editor.selecao or {}).get("id")
                    else (188, 150, 255)
                )
                kivy_adapter.draw.circle(self.tela, cor, (px, py), 4)
                if spawn.id == (self.editor.selecao or {}).get("id"):
                    kivy_adapter.draw.circle(
                        self.tela, (255, 240, 120), (px, py), 10, width=3
                    )

        if modo == "terreno":
            tilemap = context.tilemap_renderer
            for (coluna, linha), tipo in getattr(
                tilemap, "terrain_overrides", {}
            ).items():
                x, y = camera.tela(ox + coluna * TILE_SIZE, oy + linha * TILE_SIZE)
                cor = (85, 220, 160) if tipo == "grama" else (70, 170, 220)
                kivy_adapter.draw.rect(
                    self.tela,
                    cor + (70,),
                    Rect(
                        x, y, int(TILE_SIZE * camera.zoom), int(TILE_SIZE * camera.zoom)
                    ),
                )
                kivy_adapter.draw.rect(
                    self.tela,
                    cor + (150,),
                    Rect(
                        x, y, int(TILE_SIZE * camera.zoom), int(TILE_SIZE * camera.zoom)
                    ),
                    width=1,
                )

        preview = self.editor.preview_area()
        submodo_terreno = getattr(self.editor, "submodo_terreno", "pincel")
        if (
            preview is not None
            and modo == "terreno"
            and submodo_terreno in ("relevo", "espuma")
        ):
            c, lin, cols, linhas = preview
            px, py = camera.tela(ox + c * TILE_SIZE, oy + lin * TILE_SIZE)
            largura = max(1, int(cols * TILE_SIZE * camera.zoom))
            altura = max(1, int(linhas * TILE_SIZE * camera.zoom))
            cor = (
                (180, 120, 245, 80)
                if submodo_terreno == "relevo"
                else (110, 210, 245, 80)
            )
            borda = (
                (210, 150, 255, 230)
                if submodo_terreno == "relevo"
                else (130, 230, 255, 230)
            )
            kivy_adapter.draw.rect(self.tela, cor, Rect(px, py, largura, altura))
            kivy_adapter.draw.rect(
                self.tela, borda, Rect(px, py, largura, altura), width=2
            )

        if selecionado is not None:
            self._highlight(context, camera, selecionado, ox, oy)

    def _highlight(self, context, camera, item, ox, oy):
        if hasattr(item, "posicao_tile"):
            c, lin = item.posicao_tile
            x, y = camera.tela(ox + c * TILE_SIZE, oy + lin * TILE_SIZE)
            kivy_adapter.draw.circle(
                self.tela,
                (255, 240, 120),
                (
                    x + int(TILE_SIZE * camera.zoom / 2),
                    y + int(TILE_SIZE * camera.zoom / 2),
                ),
                13,
                width=3,
            )
        elif hasattr(item, "posicao"):
            runtime = getattr(context, "_entidades_runtime", {})
            entidade = runtime.get(getattr(item, "id", None)) or runtime.get(
                getattr(item, "world_spawn_id", None)
            )
            px = getattr(entidade, "x", item.posicao.x)
            py = getattr(entidade, "y", item.posicao.y)
            c, lin = context._pixel_para_tile(px, py)
            x, y = camera.tela(ox + c * TILE_SIZE, oy + lin * TILE_SIZE)
            cx = x + int(TILE_SIZE * camera.zoom / 2)
            cy = y + int(TILE_SIZE * camera.zoom / 2)
            kivy_adapter.draw.circle(
                self.tela,
                (255, 240, 120),
                (cx, cy),
                max(6, int(8 * camera.zoom)),
                width=3,
            )
        elif (
            isinstance(item, dict)
            and self.editor.modo == "terreno"
            and self.editor.relevo_selecionado_id is not None
        ):
            bx, by, cols, linhas = self.editor._bbox_relevo(item)
            rect = camera.tela_rect(
                Rect(
                    ox + bx * TILE_SIZE,
                    oy + by * TILE_SIZE,
                    cols * TILE_SIZE,
                    linhas * TILE_SIZE,
                )
            )
            kivy_adapter.draw.rect(self.tela, (255, 240, 120), rect, width=3)
            cx, cy = camera.tela(
                ox + (bx + cols / 2) * TILE_SIZE, oy + (by + linhas / 2) * TILE_SIZE
            )
            kivy_adapter.draw.circle(
                self.tela,
                (255, 240, 120),
                (cx, cy),
                max(6, int(6 * camera.zoom)),
                width=3,
            )
        elif hasattr(item, "pontos"):
            pontos = [
                camera.tela(
                    ox + c * TILE_SIZE + TILE_SIZE // 2,
                    oy + lin * TILE_SIZE + TILE_SIZE // 2,
                )
                for c, lin in item.pontos
            ]
            for a, b in zip(pontos, pontos[1:]):
                kivy_adapter.draw.line(
                    self.tela,
                    (255, 240, 120),
                    a,
                    b,
                    width=max(4, int(item.largura * 2 + 2)),
                )
        else:
            rect = camera.tela_rect(
                Rect(
                    ox + item.x * TILE_SIZE,
                    oy + item.y * TILE_SIZE,
                    item.colunas * TILE_SIZE,
                    item.linhas * TILE_SIZE,
                )
            )
            kivy_adapter.draw.rect(self.tela, (255, 240, 120), rect, width=4)

    def _render_topbar(self):
        kivy_adapter.draw.rect(
            self.tela, (13, 18, 22, 252), Rect(8, 8, LARGURA - 16, 48)
        )
        kivy_adapter.draw.text(self.tela, "WORLD EDITOR", (18, 18), (255, 220, 105), 15)
        x = 116
        for modo, label in self.MODOS:
            rect = Rect(x, 12, 74, 34)
            self._add_botao(
                rect,
                label,
                lambda m=modo: self.editor.definir_modo(m),
                selected=(self.editor.modo == modo),
            )
            x += rect.w + 5

        # A área à direita fica reservada aos comandos globais, sem criar
        # botões adicionais para RELEVO ou ESPUMA. Eles pertencem ao submenu
        # TERRENO.
        comandos_x = min(x + 8, LARGURA - 250)
        self._add_botao(
            Rect(comandos_x, 12, 64, 34), "SALVAR", lambda: self.editor.salvar()
        )
        self._add_botao(
            Rect(comandos_x + 70, 12, 64, 34), "VALIDAR", lambda: self.editor.validar()
        )
        self._add_botao(
            Rect(comandos_x + 140, 12, 100, 34),
            "FECHAR F4",
            lambda: self.editor.alternar(),
        )

    def _render_left(self, context):
        x, y, w, h = 8, 64, 225, ALTURA - 72
        kivy_adapter.draw.rect(self.tela, (18, 24, 29, 248), Rect(x, y, w, h))
        kivy_adapter.draw.text(self.tela, "CATÁLOGO", (20, 76), (235, 240, 242), 13)

        if self.editor.modo == "objeto":
            kivy_adapter.draw.text(
                self.tela,
                f"PINCEL: {self.editor.tipo_objeto}",
                (20, 94),
                (190, 205, 225),
                10,
            )
            yy = 116
            tipos = self.editor.tipos_objeto
            for indice, tipo in enumerate(tipos):
                coluna = indice % 2
                linha = indice // 2
                rect = Rect(14 + coluna * 104, yy + linha * 27, 100, 23)
                ativo = tipo == self.editor.tipo_objeto
                self._add_botao(
                    rect,
                    tipo,
                    lambda t=tipo: self.editor.selecionar_tipo_objeto(t),
                    selected=ativo,
                )
            return

        if self.editor.modo == "terreno":
            submodo = getattr(self.editor, "submodo_terreno", "pincel")
            opcoes = (
                ("grama", "GRAMA"),
                ("agua_fundo", "ÁGUA"),
                ("relevo", "RELEVO"),
                ("espuma", "ESPUMA"),
            )
            for i, (tipo, label) in enumerate(opcoes):
                rect = Rect(14, 110 + i * 40, 205, 32)
                selecionado = (
                    tipo in ("grama", "agua_fundo")
                    and self.editor.submodo_terreno == "pincel"
                    and self.editor.tipo_terreno == tipo
                ) or (tipo == submodo and tipo in ("relevo", "espuma"))
                self._add_botao(
                    rect,
                    label,
                    lambda t=tipo: self.editor.selecionar_tipo_terreno(t),
                    selected=selecionado,
                )
            if submodo == "relevo":
                # Cada linha possui sua própria quantidade de colunas.
                # A linha atualmente editada recebe COL - / COL +.
                self._add_botao(
                    Rect(14, 285, 62, 28),
                    "LIN -",
                    lambda: self.editor.alterar_dimensao_relevo("linhas", -1),
                )
                self._add_botao(
                    Rect(79, 285, 62, 28),
                    "LIN +",
                    lambda: self.editor.alterar_dimensao_relevo("linhas", 1),
                )
                self._add_botao(
                    Rect(144, 285, 62, 28),
                    "COL -",
                    lambda: self.editor.alterar_colunas_linha(-1),
                )
                self._add_botao(
                    Rect(14, 318, 62, 28),
                    "COL +",
                    lambda: self.editor.alterar_colunas_linha(1),
                )
                self._add_botao(
                    Rect(79, 318, 62, 28),
                    "ALT 1",
                    lambda: setattr(self.editor, "altura_relevo", 1),
                    selected=self.editor.altura_relevo == 1,
                )
                self._add_botao(
                    Rect(144, 318, 62, 28),
                    "ALT 2",
                    lambda: setattr(self.editor, "altura_relevo", 2),
                    selected=self.editor.altura_relevo == 2,
                )
                linhas = getattr(self.editor, "colunas_por_linha_relevo", [1])
                linha_atual = min(
                    getattr(self.editor, "linha_relevo_editando", 0),
                    max(0, len(linhas) - 1),
                )
                cols_atual = linhas[linha_atual] if linhas else 1
                kivy_adapter.draw.text(
                    self.tela,
                    f"Linha {linha_atual + 1}: {cols_atual} colunas",
                    (20, 360),
                    (220, 225, 230),
                    11,
                )
                kivy_adapter.draw.text(
                    self.tela,
                    f"Forma: {len(linhas)} linhas | máx. {max(linhas) if linhas else 1} colunas",
                    (20, 378),
                    (190, 200, 205),
                    10,
                )
                y_linhas = 402
                for indice, cols in enumerate(linhas[:10]):
                    ativo = indice == linha_atual
                    self._add_botao(
                        Rect(14, y_linhas, 205, 24),
                        f"LINHA {indice + 1}: {cols} COL",
                        lambda i=indice: self.editor.selecionar_linha_relevo(i),
                        selected=ativo,
                    )
                    y_linhas += 27
                if len(linhas) > 10:
                    kivy_adapter.draw.text(
                        self.tela,
                        f"... +{len(linhas) - 10} linhas",
                        (20, y_linhas + 2),
                        (165, 175, 180),
                        9,
                    )
                kivy_adapter.draw.text(
                    self.tela,
                    "Clique no mapa para criar",
                    (20, min(y_linhas + 24, ALTURA - 48)),
                    (180, 190, 195),
                    10,
                )
            elif submodo == "espuma":
                kivy_adapter.draw.text(
                    self.tela,
                    "Clique e arraste na água ou",
                    (20, 285),
                    (180, 190, 195),
                    10,
                )
                kivy_adapter.draw.text(
                    self.tela,
                    "na borda imediata da água",
                    (20, 302),
                    (180, 190, 195),
                    10,
                )
            else:
                kivy_adapter.draw.text(
                    self.tela, "Clique/arraste = pintar", (20, 285), (180, 190, 195), 10
                )
            return

        colecao = {
            "regiao": context.world.regions,
        }[self.editor.modo]
        yy = 100
        for item_id, item in colecao.items():
            if yy > y + h - 24:
                break
            selecionado = (
                self.editor.selecao and self.editor.selecao.get("id") == item_id
            )
            rect = Rect(14, yy, 205, 23)
            self._add_botao(
                rect,
                getattr(item, "nome", item_id)[:27],
                lambda i=item_id, m=self.editor.modo: self.editor.selecionar_id(m, i),
                selected=selecionado,
            )
            yy += 25

    def _render_right(self, context):
        x, y, w, h = 744, 64, 272, ALTURA - 72
        kivy_adapter.draw.rect(self.tela, (18, 24, 29, 250), Rect(x, y, w, h))
        kivy_adapter.draw.text(
            self.tela, "PROPRIEDADES", (756, 76), (235, 240, 242), 13
        )

        desc = self.editor.descricao()
        yy = 100
        for key, value in desc.items():
            kivy_adapter.draw.text(
                self.tela, f"{key}: {str(value)[:37]}", (756, yy), (214, 222, 226), 10
            )
            yy += 17

        if self.editor.modo == "objeto":
            rect = Rect(756, max(245, yy + 10), 230, 32)
            self._add_botao(
                rect, "REMOVER OBJETO", lambda: self.editor.remover_selecionado()
            )
            yy = rect.bottom + 12
            kivy_adapter.draw.text(
                self.tela, "Clique vazio = colocar", (756, yy), (185, 195, 200), 10
            )
            kivy_adapter.draw.text(
                self.tela, "Arraste = mover objeto", (756, yy + 18), (185, 195, 200), 10
            )
        elif self.editor.modo == "terreno":
            submodo = getattr(self.editor, "submodo_terreno", "pincel")
            mensagem = (
                "Selecione um relevo ou crie um novo"
                if submodo == "relevo"
                else "Clique e arraste na margem da água"
                if submodo == "espuma"
                else "Clique/arraste = pintar"
            )
            kivy_adapter.draw.text(
                self.tela, mensagem, (756, max(230, yy + 10)), (185, 195, 200), 10
            )
            if submodo == "relevo" and self.editor.relevo_selecionado_id is not None:
                self._add_botao(
                    Rect(756, max(280, yy + 46), 230, 34),
                    "REMOVER RELEVO",
                    lambda: self.editor.remover_relevo_selecionado(),
                )
                kivy_adapter.draw.text(
                    self.tela,
                    "Selecionado: relevo existente",
                    (756, max(322, yy + 88)),
                    (185, 195, 200),
                    10,
                )
        elif self.editor.modo == "regiao":
            actions = [
                ("papel", "Papel"),
                ("risco", "Risco"),
                ("tier_down", "Tier -"),
                ("tier_up", "Tier +"),
                ("recompensa", "Recompensa"),
            ]
            by = max(235, yy + 12)
            for action, label in actions:
                self._add_botao(
                    Rect(756, by, 110, 28),
                    label,
                    lambda a=action: self.editor.alterar_propriedade(a),
                )
                by += 33

    def clicar(self, pos_virtual):
        for rect, _label, action in reversed(self._botoes):
            if rect.collidepoint(pos_virtual):
                action()
                return True
        return False
