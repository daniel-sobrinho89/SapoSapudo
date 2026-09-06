from __future__ import annotations

import utils.kivy_adapter as kivy_adapter
from utils.config import TILE_SIZE
from utils.kivy_adapter import Rect


class WorldDebugRenderer:
    """Overlay semântico do World Model para autoria e diagnóstico."""

    def __init__(self, tela):
        self.tela = tela
        self.ativo = False
        self.mostrar_contexto = True
        self.editor_ativo = False

    def alternar(self):
        self.ativo = not self.ativo
        return self.ativo

    @staticmethod
    def _rect_tile(obj, offset_x, offset_y):
        return Rect(
            offset_x + obj.x * TILE_SIZE,
            offset_y + obj.y * TILE_SIZE,
            obj.colunas * TILE_SIZE,
            obj.linhas * TILE_SIZE,
        )

    def renderizar(self, context, camera, personagem=None):
        if not self.ativo or context is None:
            return

        # Indicador fixo de debug. Fica independente da câmera para deixar
        # explícito que o F3 foi reconhecido mesmo quando o mundo estiver
        # deslocado ou sem regiões visíveis no viewport atual.
        kivy_adapter.draw.rect(self.tela, (12, 18, 22, 235), Rect(10, 10, 190, 26))
        kivy_adapter.draw.text(
            self.tela,
            "WORLD DEBUG  |  F3",
            (18, 17),
            (245, 225, 120),
            12,
        )

        offset_x = getattr(camera, "mundo_offset_x", None) or 0
        # Camera.tela_rect trabalha com coordenadas de mundo; o mapa mantém o
        # offset absoluto no TileMapRenderer, então recebemos o valor abaixo.
        tilemap = getattr(context, "tilemap_renderer", None)
        offset_x = getattr(tilemap, "offset_x", -60) if tilemap else -60
        offset_y = getattr(tilemap, "offset_y", -66) if tilemap else -66

        cores_regiao = {
            "vila": (90, 220, 120, 100),
            "bosque": (60, 180, 90, 90),
            "lago": (80, 150, 230, 90),
            "mina": (210, 170, 90, 90),
            "acampamento": (220, 90, 80, 90),
            "campo": (190, 160, 110, 90),
            "margem": (90, 180, 220, 80),
            "clareira": (170, 210, 120, 80),
            "relevo": (150, 150, 150, 80),
        }
        for region in context.world.regions.values():
            rect_mundo = self._rect_tile(region, offset_x, offset_y)
            rect = camera.tela_rect(rect_mundo)
            cor = cores_regiao.get(region.tipo, (220, 220, 220, 80))
            kivy_adapter.draw.rect(self.tela, cor, rect, width=2)
            kivy_adapter.draw.text(
                self.tela,
                f"{region.nome} [T{region.tier}]",
                (rect.x + 6, rect.y + 5),
                cor[:3],
                13,
            )

        if personagem is not None and self.mostrar_contexto:
            location = context.contexto_entidade(personagem)
            linhas = [
                f"REG: {location.regiao.nome if location.regiao else '-'}",
                f"TEMPO: {context.state.fase.value} | CLIMA: {context.state.clima.value}",
            ]
            x, y = 12, 124
            kivy_adapter.draw.rect(
                self.tela, (15, 20, 25, 220), Rect(x - 6, y - 6, 300, 96)
            )
            for i, linha in enumerate(linhas):
                kivy_adapter.draw.text(
                    self.tela, linha, (x, y + i * 17), (235, 235, 235), 11
                )
        if self.editor_ativo:
            editor = getattr(context, "world_editor", None)
            descricao = getattr(editor, "descricao", lambda: {})() if editor else {}
            kivy_adapter.draw.rect(
                self.tela, (15, 20, 25, 235), Rect(320, 10, 330, 104)
            )
            kivy_adapter.draw.text(
                self.tela, "WORLD EDITOR | F4", (330, 18), (255, 220, 90), 12
            )
            linhas_editor = [
                "Região: " + str(descricao.get("regiao", "-")),
                "Use tools/world_editor.py para editar dados.",
            ]
            for i, linha in enumerate(linhas_editor):
                kivy_adapter.draw.text(
                    self.tela, linha, (330, 40 + i * 15), (230, 230, 230), 10
                )
