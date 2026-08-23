from application.usecases.personagem.trocar_comportamento import (
    TrocarComportamentoUseCase,
)
from tests.integration.harness.assertions import assert_moved
from tests.integration.harness.scenario import (
    IntegrationScenario,
    ponto_degrau,
    ponto_tile,
    snapshot_visual_entity,
)


def _snap(c, p):
    dados = snapshot_visual_entity(p, faccao=getattr(p, "_faccao_teste", None))
    dados["tempo"] = round(c.clock.tempo, 3)
    return dados


def _ordenar_movimento(c, personagem, destino):
    controlador = c.controladores[personagem]
    return TrocarComportamentoUseCase().executar(
        controlador, personagem, c.navegacao, destino[0], destino[1]
    )


def movimento_com_obstaculo():
    c = IntegrationScenario()
    inicio = ponto_tile(c, 7, 7)
    fim = ponto_tile(c, 12, 7)
    personagem = c.criar_personagem("soldado", *inicio, faccao="aliada")
    obstaculo = c.criar_construcao_teste(
        "casa", (inicio[0] + fim[0]) / 2, inicio[1], faccao="neutra", tamanho=128
    )
    c.atualizar_obstaculos()
    assert _ordenar_movimento(c, personagem, fim)
    trace = []
    for i in range(1400):
        c.tick()
        if i % 10 == 0:
            trace.append(_snap(c, personagem))
        if abs(personagem.x - fim[0]) < 8 and abs(personagem.y - fim[1]) < 8:
            break
    assert_moved(inicio, personagem)
    assert abs(personagem.x - fim[0]) < 12
    assert any(abs(p["y"] - inicio[1]) > 20 for p in trace), "não contornou o obstáculo"
    return {
        "kind": "movement",
        "data_source": "real_runtime",
        "trace": trace,
        "start": inicio,
        "goal": fim,
        "obstacle": {"x": obstaculo.x, "y": obstaculo.y, "size": 128},
        "tilemap": c.tilemap_renderer,
    }


def movimento_degrau():
    c = IntegrationScenario()
    coluna, linha, _ = ponto_degrau(c)
    inicio = ponto_tile(c, coluna - 1, linha)
    # Vai além do primeiro tile do degrau para deixar visível a subida e,
    # depois, a entrada no miolo do relevo.
    fim = ponto_tile(c, coluna + 4, linha)
    personagem = c.criar_personagem("soldado", *inicio, altura=0, faccao="aliada")
    assert _ordenar_movimento(c, personagem, fim)
    altura_inicial = personagem.altura
    trace = []
    subiu = False
    for i in range(1200):
        c.tick()
        if personagem.altura == 1:
            subiu = True
        if i % 6 == 0 or (subiu and i % 3 == 0):
            trace.append(_snap(c, personagem))
        if subiu and abs(personagem.x - fim[0]) < 8 and i >= 30:
            break
    assert_moved(inicio, personagem)
    assert personagem.altura == 1, f"altura final inesperada: {personagem.altura}"
    assert any(p["altura"] == 1 for p in trace), (
        "transição de altura não aconteceu no runtime real"
    )
    assert any(
        p["altura"] == 1 and p["x"] > ponto_tile(c, coluna + 1, linha)[0] + 60
        for p in trace
    ), "soldado subiu o degrau, mas não avançou para o meio do relevo"
    return {
        "kind": "movement_step",
        "data_source": "real_runtime",
        "trace": trace,
        "degrau": {
            "coluna": coluna,
            "linha": linha,
            "altura_antes": altura_inicial,
            "altura_depois": personagem.altura,
        },
        "tilemap": c.tilemap_renderer,
    }


def raio_movimento_livre():
    c = IntegrationScenario()
    inicio = ponto_tile(c, 10, 8)
    personagem = c.criar_personagem("soldado", *inicio, faccao="aliada")

    # O spawn define o primeiro centro da área.
    assert personagem.base_x == inicio[0]
    assert personagem.base_y == inicio[1]
    assert personagem.raio_movimento_livre == 4 * 64

    # Força uma decisão autônoma e confirma que o destino sorteado usa
    # o centro original, e não a posição atual do personagem.
    controlador = c.controladores[personagem]["padrao"]
    controlador.personagem = personagem
    personagem.x = inicio[0] + 3 * 64
    personagem.y = inicio[1]
    controlador._escolher_proxima_acao()

    distancia_do_spawn = (
        (personagem.destino_x - inicio[0]) ** 2
        + (personagem.destino_y - inicio[1]) ** 2
    ) ** 0.5
    assert distancia_do_spawn <= 4 * 64 + 1e-6, (
        f"destino autônomo saiu do raio do spawn: {distancia_do_spawn}"
    )

    # Uma nova ordem redefine o centro.
    novo_centro = ponto_tile(c, 12, 7)
    assert _ordenar_movimento(c, personagem, novo_centro)
    assert personagem.base_x == novo_centro[0]
    assert personagem.base_y == novo_centro[1]

    # Depois da ordem, uma nova decisão autônoma deve usar o novo centro.
    personagem.x = novo_centro[0] + 3 * 64
    personagem.y = novo_centro[1]
    controlador._escolher_proxima_acao()

    distancia_do_novo_centro = (
        (personagem.destino_x - novo_centro[0]) ** 2
        + (personagem.destino_y - novo_centro[1]) ** 2
    ) ** 0.5
    assert distancia_do_novo_centro <= 4 * 64 + 1e-6, (
        f"destino autônomo não respeitou o novo centro: {distancia_do_novo_centro}"
    )

    return {
        "kind": "movement_free_radius",
        "data_source": "real_runtime",
        "start": inicio,
        "new_center": novo_centro,
        "radius": 4 * 64,
    }


def rota_persistente_e_invalida_com_obstaculo():
    """A rota não é refeita por movimento; uma construção no caminho a invalida."""
    c = IntegrationScenario()
    inicio = ponto_tile(c, 6, 7)
    fim = ponto_tile(c, 15, 7)
    personagem = c.criar_personagem("soldado", *inicio, faccao="aliada")

    obstaculo_inicial = c.criar_construcao_teste(
        "casa",
        ponto_tile(c, 10, 7)[0],
        ponto_tile(c, 10, 7)[1],
        faccao="neutra",
        tamanho=112,
    )
    assert _ordenar_movimento(c, personagem, fim)

    # Alguns ticks criam a rota persistente e fazem o personagem começar a
    # consumi-la. O contador é zerado para medir somente o período estável.
    for _ in range(180):
        c.tick()
        if c.mover_personagem._rotas_por_personagem.get(id(personagem)):
            break

    dados = c.mover_personagem._rotas_por_personagem.get(id(personagem))
    assert dados is not None, "rota persistente não foi criada"
    chamadas_antes = c.metricas_desempenho.counters.get("pathfinding_chamadas", 0)
    pos_antes = (personagem.x, personagem.y)

    # A nova construção cai sobre um trecho ainda não percorrido da rota.
    rota = dados["rota"]
    indice = dados["indice"]
    restantes = rota[indice:]
    assert restantes, "rota já havia sido consumida"
    bloqueio_x, bloqueio_y = restantes[min(2, len(restantes) - 1)]
    obstaculo_novo = c.criar_construcao_teste(
        "casa",
        bloqueio_x,
        bloqueio_y,
        faccao="neutra",
        tamanho=96,
    )

    for _ in range(1400):
        c.tick()
        if abs(personagem.x - fim[0]) < 24 and abs(personagem.y - fim[1]) < 24:
            break

    chamadas_depois = c.metricas_desempenho.counters.get("pathfinding_chamadas", 0)
    assert chamadas_depois > chamadas_antes, (
        "a construção no caminho não provocou novo pathfinding"
    )
    assert (personagem.x, personagem.y) != pos_antes, (
        "personagem ficou parado após a invalidação da rota"
    )
    assert abs(personagem.x - fim[0]) < 24 and abs(personagem.y - fim[1]) < 24, (
        "personagem não retomou o caminho até o destino após o obstáculo"
    )

    return {
        "kind": "movement_dynamic_obstacle",
        "data_source": "real_runtime",
        "trace": [],
        "start": inicio,
        "goal": fim,
        "obstacle_initial": {"x": obstaculo_inicial.x, "y": obstaculo_inicial.y},
        "obstacle_inserted": {"x": obstaculo_novo.x, "y": obstaculo_novo.y},
        "pathfinding_before": chamadas_antes,
        "pathfinding_after": chamadas_depois,
        "tilemap": c.tilemap_renderer,
    }


def camera_zoom_e_limite():
    from core.camera import Camera

    camera = Camera()
    assert camera.zoom_min == 0.5
    assert camera.zoom_max == 4.0

    for _ in range(100):
        camera.aproximar()

    assert camera.zoom == 4.0

    entidade = type("EntidadeTeste", (), {"x": 640, "y": 360})()
    camera.seguir(entidade)

    largura_mundo = camera.largura / camera.zoom
    altura_mundo = camera.altura / camera.zoom
    assert abs(camera.x - (entidade.x - largura_mundo / 2)) < 1e-6
    assert abs(camera.y - (entidade.y - altura_mundo / 2)) < 1e-6

    # Alterar o zoom não pode deslocar o ponto sob o centro da tela.
    centro = (camera.largura / 2, camera.altura / 2)
    foco_antes = camera.mundo(*centro)
    camera.definir_zoom(2.0)
    foco_depois = camera.mundo(*centro)
    assert abs(foco_antes[0] - foco_depois[0]) < 1e-6
    assert abs(foco_antes[1] - foco_depois[1]) < 1e-6

    # O arrasto é informado em pixels de tela e deve ser convertido pelo zoom.
    camera.definir_zoom(2.0)
    x_antes, y_antes = camera.x, camera.y
    camera.arrastar(100, 50)
    assert abs(camera.x - (x_antes - 50)) < 1e-6
    assert abs(camera.y - (y_antes - 25)) < 1e-6

    return {
        "kind": "camera_zoom",
        "data_source": "real_runtime",
        "trace": [],
    }


def tilemap_cache_zoom_nao_reutiliza_surface_temporaria():
    """Garante que o viewport escalado não depende do cache por id(Surface)."""
    from types import SimpleNamespace

    import utils.kivy_adapter as kivy_adapter
    from render.tilemap_renderer import TileMapRenderer

    class TransformComSentinela:
        def __init__(self):
            self.sentinela = kivy_adapter.Surface((1, 1))

        def escalar(self, imagem, tamanho):
            # O renderer do tilemap não deve chamar o cache genérico para uma
            # Surface de viewport temporária.
            return self.sentinela

    transform = TransformComSentinela()
    tela = kivy_adapter.Surface((320, 240))
    renderer = TileMapRenderer(tela, None, transform)

    base = kivy_adapter.Surface((512, 512))
    base.fill((10, 20, 30, 255))
    renderer._cache_terreno_base = base
    renderer._cache_terreno_pad_x = 0
    renderer._cache_terreno_pad_y = 0

    camera = SimpleNamespace(
        x=32.0,
        y=48.0,
        largura=320,
        altura=240,
        zoom=2.0,
    )

    viewport, _ = renderer._obter_cache_terreno_viewport(camera)

    assert viewport is not transform.sentinela, (
        "viewport de terreno não pode usar o cache genérico por id(Surface)"
    )

    # A mesma região e o mesmo zoom devem reutilizar o viewport próprio.
    viewport_2, _ = renderer._obter_cache_terreno_viewport(camera)
    assert viewport_2 is viewport

    # Ao mover a câmera uma unidade de mundo, o recorte precisa mudar.
    camera.x += 1
    viewport_3, _ = renderer._obter_cache_terreno_viewport(camera)
    assert viewport_3 is not viewport

    return {
        "kind": "tilemap_cache",
        "data_source": "real_runtime",
        "trace": [],
    }


def mobile_duplo_clique_reconhece_dois_toques():
    """Dois toques reais devem continuar sendo duplo clique; um toque isolado não."""
    from core.mouse_events import DoubleClickDetector

    detector = DoubleClickDetector()

    # Primeiro toque: apenas registra.
    assert detector.detectar((500, 300)) is False

    # Segundo toque próximo e dentro da janela: abre o menu via duplo clique.
    import time

    original = time.monotonic
    try:
        # O detector usa time.monotonic diretamente. Em condições normais,
        # dois toques consecutivos deste teste ficam muito abaixo do limite.
        assert detector.detectar((502, 301)) is True
    finally:
        _ = original

    # Um novo toque isolado volta a ser apenas primeiro clique.
    assert detector.detectar((500, 300)) is False

    return {
        "kind": "input_mobile_double_click",
        "data_source": "logic",
    }
