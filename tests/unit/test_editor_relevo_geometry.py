from types import SimpleNamespace

from core.world.editor import WorldEditor
from render.tilemap_renderer import TileMapRenderer


def test_segmentos_relevo_preserva_colunas_de_cada_linha():
    renderer = TileMapRenderer.__new__(TileMapRenderer)
    relevo = {
        "id": 7,
        "altura": 2,
        "forma": [
            {"x": 5, "y": 2, "colunas": 6},
            {"x": 6, "y": 3, "colunas": 4},
            {"x": 6, "y": 4, "colunas": 3},
            {"x": 7, "y": 5, "colunas": 2},
        ],
        "bordas": {
            "esquerda": True,
            "direita": True,
            "superior": True,
            "inferior": True,
        },
    }

    segmentos = renderer._segmentos_relevo(relevo)

    assert [(s["y"], s["x"], s["colunas"], s["linhas"]) for s in segmentos] == [
        (2, 5, 6, 1),
        (3, 6, 4, 1),
        (4, 6, 3, 1),
        (5, 7, 2, 1),
    ]


def test_iniciar_area_seleciona_relevo_existente_em_vez_de_criar():
    class Renderer:
        TIPO_GRAMA = "grama"
        _relevos_config = [
            {
                "id": 11,
                "altura": 1,
                "forma": [
                    {"x": 3, "y": 4, "colunas": 3},
                    {"x": 4, "y": 5, "colunas": 2},
                    {"x": 4, "y": 6, "colunas": 1},
                ],
            }
        ]

        def obter_tipo(self, _c, _l):
            return self.TIPO_GRAMA

    renderer = Renderer()
    context = SimpleNamespace(
        tilemap_renderer=renderer,
        validator=SimpleNamespace(colunas=20, linhas=20),
    )
    world_service = SimpleNamespace(context=context)
    editor = WorldEditor(world_service)
    editor.modo = "terreno"
    editor.submodo_terreno = "relevo"

    assert editor.iniciar_area(5, 5) is True
    assert editor.relevo_selecionado_id == 11
    assert editor.arrastando is False
    assert editor.colunas_por_linha_relevo == [3, 2, 1]
    assert editor.linhas_relevo == 3
    assert editor.colunas_relevo == 3
