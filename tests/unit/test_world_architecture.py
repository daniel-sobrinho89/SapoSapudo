from core.world.service import WorldService


def test_world_service_loads_and_validates_before_runtime():
    context = WorldService().carregar()
    assert context.world.world_id == "sapudo_v1"
    assert not any(issue.severity == "ERROR" for issue in context.validator.issues)
    assert len(context.world.regions) == 9


def test_region_service_resolves_context():
    context = WorldService().carregar()
    location = context.localizar(548, 286)
    assert location.regiao is not None
    assert location.regiao.id == "vila_bernardo"
    assert not hasattr(location, "caminho")
    assert not hasattr(location, "landmark")


def test_spawn_system_is_runtime_source_for_entities():
    context = WorldService().carregar()
    arvores = context.spawn_system.obter_spawns_tipo("arvore1")
    assert arvores
    assert all(spawn.regiao for spawn in arvores)
    assert not hasattr(arvores[0], "spawn_rule")
    assert not hasattr(arvores[0], "zona")


def test_world_state_changes_over_time():
    context = WorldService().carregar()
    inicial = context.state.fase
    context.state.atualizar(context.state.duracao_dia / 3 + 0.1)
    assert context.state.fase != inicial


def test_autonomous_point_stays_inside_current_context_when_possible():
    context = WorldService().carregar()

    class Character:
        x = 548
        y = 286
        base_x = 548
        base_y = 286
        raio_movimento_livre = 160

    personagem = Character()
    context.vincular_entidade(personagem)
    destino = context.ponto_autonomo(personagem)
    assert destino is None or context.localizar(*destino).regiao.id == "vila_bernardo"


def test_world_state_simulates_weather_and_resource_regeneration():
    context = WorldService().carregar()
    context.state.registrar_recurso("mina_01")
    context.state.marcar_recurso_coletado("mina_01")
    context.state.atualizar(76)
    assert context.state.recurso_disponivel("mina_01")
    assert context.state.clima != context._clima_inicial()


def test_world_editor_is_an_authoring_tool():
    from core.world.editor import WorldEditor

    service = WorldService()
    service.carregar()
    editor = WorldEditor(service)
    selection = editor.selecionar(548, 286)
    assert set(selection) >= {"tile", "regiao", "id"}
    assert "path" not in selection
    assert "landmark" not in selection


def test_world_editor_can_change_region_semantics_in_memory():
    from core.world.editor import WorldEditor

    service = WorldService()
    context = service.carregar()
    editor = WorldEditor(service)
    assert editor.selecionar_id("regiao", "bosque")
    original = context.world.regions["bosque"]
    editor.alterar_propriedade("tier_up")
    assert context.world.regions["bosque"].tier == original.tier + 1
    assert editor.dirty is True


def test_world_editor_can_place_object_and_paint_terrain():
    from core.world.editor import WorldEditor

    class FakeTilemap:
        def __init__(self):
            self.terrain_overrides = {}

        def tile_para_pixel(self, coluna, linha):
            return -60 + coluna * 64, -66 + linha * 64

        def obter_altura(self, coluna, linha):
            return 0

        def definir_terreno_editor(self, coluna, linha, tipo):
            self.terrain_overrides[(coluna, linha)] = tipo

        def salvar_terreno_editor(self):
            pass

    service = WorldService()
    context = service.carregar()
    context.tilemap_renderer = FakeTilemap()
    editor = WorldEditor(service)
    editor.context.tilemap_renderer = context.tilemap_renderer

    regiao = context.world.regions["bosque"]
    tile = None
    for linha in range(regiao.y, regiao.y + regiao.linhas):
        for coluna in range(regiao.x, regiao.x + regiao.colunas):
            if (
                context.validator.terreno(coluna, linha) == "grama"
                and editor.spawn_no_tile(coluna, linha) is None
            ):
                tile = (coluna, linha)
                break
        if tile:
            break

    editor.selecionar_tipo_objeto("arvore1")
    editor.definir_modo("objeto")
    assert editor.adicionar_objeto_no_tile(*tile) is True
    assert editor.item_selecionado().tipo == "arvore1"

    editor.definir_modo("terreno")
    editor.selecionar_tipo_terreno("agua_fundo")
    assert editor.pintar_terreno_no_tile(1, 1) is True
    assert context.tilemap_renderer.terrain_overrides[(1, 1)] == "agua_fundo"


def test_world_editor_can_select_relevo_and_move_spawn_with_runtime_callback():
    from core.world.editor import WorldEditor

    class FakeTilemap:
        def __init__(self):
            self._relevos_config = [
                {"id": 99, "x": 3, "y": 4, "colunas": 2, "linhas": 1, "altura": 1}
            ]

        def tile_para_pixel(self, coluna, linha):
            return -60 + coluna * 64, -66 + linha * 64

        def obter_altura(self, coluna, linha):
            return 0

    service = WorldService()
    context = service.carregar()
    context.tilemap_renderer = FakeTilemap()
    editor = WorldEditor(service)

    assert editor.selecionar_relevo_por_tile(3, 4)["id"] == 99

    spawn = next(iter(context.world.spawns.values()))
    callbacks = []
    editor.configurar_callbacks(
        mover_spawn=lambda item, tile: callbacks.append((item.id, tile))
    )
    assert editor.selecionar_spawn_id(spawn.id)
    antigo = context._pixel_para_tile(spawn.posicao.x, spawn.posicao.y)
    assert editor.iniciar_arrasto(spawn.posicao.x, spawn.posicao.y)
    editor.mover_arrasto(
        context.tilemap_renderer.tile_para_pixel(antigo[0] + 1, antigo[1])[0] + 32,
        context.tilemap_renderer.tile_para_pixel(antigo[0] + 1, antigo[1])[1] + 32,
    )
    assert callbacks
    assert callbacks[-1][0] == spawn.id


def test_world_editor_relevo_bbox_and_dimension_update():
    from core.world.editor import WorldEditor

    class FakeTilemap:
        def __init__(self):
            self.largura = 42
            self.altura = 30
            self._relevos_config = [
                {
                    "id": 99,
                    "altura": 1,
                    "forma": [
                        {"y": 4, "x": 3, "colunas": 2},
                        {"y": 5, "x": 3, "colunas": 2},
                    ],
                }
            ]

        def _reindexar_camadas_editor(self):
            return None

    service = WorldService()
    context = service.carregar()
    context.tilemap_renderer = FakeTilemap()
    editor = WorldEditor(service)
    assert editor.selecionar_relevo_por_tile(4, 5)["id"] == 99
    assert editor.colunas_relevo == 2
    assert editor.linhas_relevo == 2
    assert editor.alterar_dimensao_relevo("colunas", 1)
    assert editor.colunas_relevo == 3


def test_world_editor_relevo_permite_colunas_por_linha_e_remocao():
    from core.world.editor import WorldEditor

    class FakeTilemap:
        largura = 42
        altura = 30

        def __init__(self):
            self._relevos_config = [
                {
                    "id": 77,
                    "altura": 2,
                    "forma": [
                        {"y": 8, "x": 4, "colunas": 3},
                        {"y": 9, "x": 4, "colunas": 5},
                        {"y": 10, "x": 4, "colunas": 2},
                    ],
                }
            ]
            self.reindexou = 0

        def _reindexar_camadas_editor(self):
            self.reindexou += 1

    service = WorldService()
    context = service.carregar()
    context.tilemap_renderer = FakeTilemap()
    editor = WorldEditor(service)

    assert editor.selecionar_relevo_por_tile(6, 9)["id"] == 77
    assert editor.colunas_por_linha_relevo == [3, 5, 2]

    editor.selecionar_linha_relevo(2)
    assert editor.alterar_colunas_linha(2)
    alvo = context.tilemap_renderer._relevos_config[0]
    assert [linha["colunas"] for linha in alvo["forma"]] == [3, 5, 4]

    assert editor.selecionar_linha_relevo(0)
    assert editor.alterar_dimensao_relevo("linhas", 1)
    assert len(alvo["forma"]) == 4
    assert [linha["colunas"] for linha in alvo["forma"]] == [3, 5, 4, 4]

    assert editor.remover_relevo_selecionado()
    assert context.tilemap_renderer._relevos_config == []
    assert editor.relevo_selecionado_id is None


def test_tilemap_relevo_agrupa_linhas_iguais_sem_perder_forma_individual():
    from render.tilemap_renderer import TileMapRenderer

    renderer = TileMapRenderer.__new__(TileMapRenderer)
    segmentos = renderer._segmentos_relevo(
        {
            "id": 10,
            "altura": 1,
            "forma": [
                {"y": 0, "x": 14, "colunas": 16},
                {"y": 1, "x": 16, "colunas": 14},
                {"y": 2, "x": 16, "colunas": 14},
                {"y": 3, "x": 16, "colunas": 14},
                {"y": 4, "x": 16, "colunas": 14},
            ],
            "bordas": {
                "esquerda": True,
                "direita": True,
                "superior": True,
                "inferior": True,
            },
        }
    )

    assert [(s["x"], s["y"], s["colunas"], s["linhas"]) for s in segmentos] == [
        (14, 0, 16, 1),
        (16, 1, 14, 4),
    ]
    assert segmentos[0]["tem_borda_esquerda"] is True
    assert segmentos[0]["tem_borda_direita"] is False
    assert segmentos[1]["tem_borda_esquerda"] is False
    assert segmentos[1]["tem_borda_direita"] is True
    assert segmentos[0]["tem_borda_superior"] is True
    assert segmentos[1]["tem_borda_superior"] is False
    assert segmentos[1]["tem_borda_inferior"] is True
