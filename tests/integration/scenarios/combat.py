from math import hypot

from application.usecases.construcao.defender_construcao import (
    DefenderConstrucaoUseCase,
)
from tests.integration.harness.assertions import (
    IntegrationFailure,
    assert_in_attack_range,
    assert_moved,
    assert_target_damaged,
)
from tests.integration.harness.scenario import (
    IntegrationScenario,
    ponto_degrau,
    snapshot_construcao,
    snapshot_efeito,
    snapshot_visual_entity,
)


def _snapshot(c, personagens, construcoes=()):
    dados = {
        "tempo": round(c.clock.tempo, 3),
        "personagens": [],
        "construcoes": [
            snapshot_construcao(
                x,
                faccao=getattr(x, "_faccao_teste", None),
            )
            for x in construcoes
            if x in c.construcoes or x in c.construcoes_hostis
        ],
    }
    for p in personagens:
        ataque = (
            c.controladores.get(p, {}).get("acoes", {}).get("atacar", {}).get("usecase")
        )
        alvo = getattr(ataque, "entidade_alvo", None)
        pessoa = snapshot_visual_entity(
            p,
            faccao=getattr(p, "_faccao_teste", None),
        )
        pessoa["alvo"] = getattr(alvo, "nome", None)
        dados["personagens"].append(pessoa)
    if personagens:
        dados.update(
            {
                "x": personagens[0].x,
                "y": personagens[0].y,
                "altura": personagens[0].altura,
                "vida_soldado": personagens[0].vida,
            }
        )
    if len(personagens) > 1:
        dados.update(
            {
                "goblin_x": personagens[1].x,
                "goblin_y": personagens[1].y,
                "altura_goblin": personagens[1].altura,
                "vida_goblin": personagens[1].vida,
            }
        )
        dados.update(
            {
                "s1x": personagens[0].x,
                "s1y": personagens[0].y,
                "s2x": personagens[1].x,
                "s2y": personagens[1].y,
            }
        )
    if construcoes:
        dados["vida_construcao"] = max(0, construcoes[0].vida)
    dados["efeitos"] = [snapshot_efeito(e) for e in c.efeitos]
    return dados


def personagem_perto_inimigo():
    c = IntegrationScenario()
    soldado = c.criar_personagem("soldado", 600, 300, faccao="aliada")
    goblin = c.criar_personagem("goblin_tocha", 800, 300, faccao="goblin")
    inicio_s = (soldado.x, soldado.y)
    inicio_g = (goblin.x, goblin.y)
    trace = []
    morte_detectada = False
    pos_morte = None
    for i in range(2400):
        c.tick()
        if i % 6 == 0 or morte_detectada:
            trace.append(_snapshot(c, [soldado, goblin]))
        if not morte_detectada and (soldado.vida <= 0 or goblin.vida <= 0):
            morte_detectada = True
            pos_morte = i
        if morte_detectada and pos_morte is not None and i >= pos_morte + 90:
            break
    assert_moved(inicio_s, soldado)
    assert_moved(inicio_g, goblin)
    assert any(
        p.get("alvo") == "goblin_tocha"
        for frame in trace
        for p in frame.get("personagens", [])
        if p.get("nome") == "soldado"
    ), "soldado não registrou o goblin como alvo durante a luta"
    assert any(
        p.get("alvo") == "soldado"
        for frame in trace
        for p in frame.get("personagens", [])
        if p.get("nome") == "goblin_tocha"
    ), "goblin não registrou o soldado como alvo durante a luta"
    assert soldado.vida < soldado.VIDA_MAXIMA or goblin.vida < goblin.VIDA_MAXIMA
    assert morte_detectada, "a luta não chegou à morte de um dos personagens"
    assert any(
        e["nome"] == "poeira_grande"
        for frame in trace
        for e in frame.get("efeitos", [])
    ), "efeito de poeira da morte não apareceu no trace"
    return {
        "kind": "combat",
        "data_source": "real_runtime",
        "trace": trace,
        "actors": [soldado.nome, goblin.nome],
        "construction": None,
        "tilemap": c.tilemap_renderer,
    }


def personagem_com_construcao_inimiga():
    c = IntegrationScenario()
    soldado = c.criar_personagem("soldado", 600, 300, faccao="aliada")
    goblin = c.criar_personagem("goblin_tocha", 900, 300, faccao="goblin")
    casa = c.criar_construcao_teste("casa", 760, 300, faccao="goblin", tamanho=192)
    inicio = (soldado.x, soldado.y)
    trace = []
    # O teste valida a reação inicial à construção inimiga, mas o visual
    # precisa registrar tempo suficiente para mostrar o deslocamento.
    for i in range(120):
        c.tick()
        if i % 5 == 0:
            trace.append(_snapshot(c, [soldado, goblin], [casa]))

    if hypot(soldado.x - inicio[0], soldado.y - inicio[1]) < 8:
        raise IntegrationFailure(
            "soldado não se moveu ao ter construção inimiga no contexto",
            {
                "kind": "combat_construction",
                "trace": trace,
                "start": inicio,
                "goal": (goblin.x, goblin.y),
                "construction": {"x": casa.x, "y": casa.y, "size": 192},
                "tilemap": c.tilemap_renderer,
            },
        )
    return {
        "kind": "combat_construction",
        "data_source": "real_runtime",
        "trace": trace,
        "construction": {
            "nome": casa.nome,
            "x": casa.x,
            "y": casa.y,
            "size": 192,
            "vida": casa.vida,
            "vida_inicial": casa.VIDA_MAXIMA,
            "faccao": getattr(casa, "_faccao_teste", None),
        },
        "tilemap": c.tilemap_renderer,
    }


def soldado_ataca_goblin():
    c = IntegrationScenario()
    soldado = c.criar_personagem("soldado", 600, 300, faccao="aliada")
    goblin = c.criar_personagem("goblin_tocha", 1000, 300, faccao="goblin")
    ataque = c.controladores[soldado]["acoes"]["atacar"]["usecase"]
    ataque.iniciar(goblin, soldado, manual=True)
    inicio = (soldado.x, soldado.y)
    vida = goblin.vida
    trace = []
    for i in range(1500):
        c.tick()
        if i % 10 == 0:
            trace.append(_snapshot(c, [soldado, goblin]))
        if goblin.vida < vida:
            break
    assert_moved(inicio, soldado)
    assert_in_attack_range(soldado, goblin)
    assert_target_damaged(vida, goblin)
    return {
        "kind": "combat",
        "data_source": "real_runtime",
        "trace": trace,
        "construction": None,
        "tilemap": c.tilemap_renderer,
    }


def soldado_contorna_construcao():
    c = IntegrationScenario()
    soldado = c.criar_personagem("soldado", 500, 300, faccao="aliada")
    goblin = c.criar_personagem("goblin_tocha", 900, 240, faccao="goblin")
    casa = c.criar_construcao_teste("casa", 760, 240, faccao="goblin", tamanho=192)
    ataque = c.controladores[soldado]["acoes"]["atacar"]["usecase"]
    ataque.iniciar(goblin, soldado, manual=True)
    inicio = (soldado.x, soldado.y)
    vida = goblin.vida
    trace = []
    for i in range(1800):
        c.tick()
        if i % 10 == 0:
            trace.append(_snapshot(c, [soldado, goblin], [casa]))
        if goblin.vida < vida:
            break
    if hypot(soldado.x - inicio[0], soldado.y - inicio[1]) < 8:
        raise IntegrationFailure(
            "soldado não iniciou o contorno da construção",
            {
                "kind": "combat_construction",
                "trace": trace,
                "start": inicio,
                "goal": (goblin.x, goblin.y),
                "construction": {"x": casa.x, "y": casa.y, "size": 192},
                "tilemap": c.tilemap_renderer,
            },
        )
    assert_target_damaged(vida, goblin)
    assert_in_attack_range(soldado, goblin)
    rect_casa = c.obter_rect_colisao(casa)
    passou_da_barreira = (
        soldado.x > rect_casa.right + 8
        or soldado.x < rect_casa.left - 8
        or soldado.y > rect_casa.bottom + 8
        or soldado.y < rect_casa.top - 8
    )
    if not passou_da_barreira:
        raise IntegrationFailure(
            "soldado não chegou ao outro lado da construção",
            {
                "kind": "combat_construction",
                "trace": trace,
                "start": inicio,
                "goal": (goblin.x, goblin.y),
                "construction": {"x": casa.x, "y": casa.y, "size": 192},
                "tilemap": c.tilemap_renderer,
            },
        )
    return {
        "kind": "combat_construction",
        "data_source": "real_runtime",
        "trace": trace,
        "construction": {"x": casa.x, "y": casa.y, "size": 192, "vida": casa.vida},
        "tilemap": c.tilemap_renderer,
    }


def soldado_defende_construcao():
    c = IntegrationScenario()
    # O soldado fica fora da área imediata de ataque da casa, mas dentro do
    # raio de convocação de defensores (6 tiles). A casa precisa chamar o
    # soldado, que então contorna a construção antes de atacar o goblin.
    soldado = c.criar_personagem("soldado", 500, 240, faccao="aliada")
    goblin = c.criar_personagem("goblin_tocha", 900, 240, faccao="goblin")
    casa = c.criar_construcao_teste("casa", 760, 240, faccao="aliada", tamanho=192)
    defensor = DefenderConstrucaoUseCase(c)
    c.registrar_controlador_construcao(casa, defensor)
    ataque_g = c.controladores[goblin]["acoes"]["atacar"]["usecase"]
    ataque_s = c.controladores[soldado]["acoes"]["atacar"]["usecase"]

    vida_casa = casa.vida
    vida_goblin = goblin.vida
    inicio_soldado = (soldado.x, soldado.y)
    trace = []

    # Primeiro o goblin recebe a ordem real de atacar a construção.
    ataque_g.iniciar(casa, goblin, manual=True)

    primeira_danificacao_casa = None
    primeira_defesa = None
    primeira_troca_goblin = None
    primeiro_dano_goblin = None

    for i in range(2400):
        c.tick()

        deve_capturar = i % 10 == 0

        if primeira_danificacao_casa is None and casa.vida < vida_casa:
            primeira_danificacao_casa = i
            deve_capturar = True

        if primeira_defesa is None and ataque_s.entidade_alvo is goblin:
            primeira_defesa = i
            deve_capturar = True

        if primeira_troca_goblin is None and ataque_g.entidade_alvo is soldado:
            primeira_troca_goblin = i
            deve_capturar = True

        if primeiro_dano_goblin is None and goblin.vida < vida_goblin:
            primeiro_dano_goblin = i
            deve_capturar = True

        if deve_capturar:
            trace.append(_snapshot(c, [soldado, goblin], [casa]))

        # Depois da troca de alvo, mantemos alguns segundos do fluxo para o
        # GIF mostrar também o goblin abandonando a construção e partindo
        # contra o defensor, em vez de terminar exatamente no frame da troca.
        if primeira_troca_goblin is not None and i >= primeira_troca_goblin + 300:
            break

    assert primeira_danificacao_casa is not None, "goblin não danificou a construção"
    assert primeira_defesa is not None, "construção não chamou o soldado defensor"

    # O soldado não pode atacar a própria construção em nenhum momento.
    alvos_soldado = [
        p["alvo"]
        for frame in trace
        for p in frame["personagens"]
        if p["nome"] == "soldado"
    ]
    assert "casa" not in alvos_soldado, "soldado defensor atacou a própria construção"

    # O defensor precisa realmente se aproximar, contornar a casa e somente
    # depois causar dano ao goblin.
    assert_moved(inicio_soldado, soldado)
    rect_casa = c.obter_rect_colisao(casa)
    contornou = any(
        p["nome"] == "soldado"
        and (
            p["x"] > rect_casa.right + 8
            or p["x"] < rect_casa.left - 8
            or p["y"] > rect_casa.bottom + 8
            or p["y"] < rect_casa.top - 8
        )
        for frame in trace
        for p in frame["personagens"]
    )
    assert contornou, "soldado defensor não contornou a construção antes do ataque"

    assert primeiro_dano_goblin is not None, (
        "soldado defensor não causou dano ao goblin"
    )
    assert primeira_troca_goblin is not None, (
        "goblin não trocou o alvo para o soldado defensor"
    )
    assert primeiro_dano_goblin >= primeira_defesa, (
        "soldado causou dano antes de ser chamado como defensor"
    )
    assert primeira_troca_goblin >= primeiro_dano_goblin, (
        "goblin trocou de alvo antes de receber o primeiro golpe do defensor"
    )
    assert ataque_g.entidade_alvo is soldado, "goblin não passou a atacar o soldado"
    assert goblin.vida < vida_goblin

    return {
        "kind": "defend_construction",
        "data_source": "real_runtime",
        "trace": trace,
        "construction": {
            "x": casa.x,
            "y": casa.y,
            "size": 192,
            "vida_inicial": vida_casa,
            "vida_final": casa.vida,
        },
        "goblin_trocou_alvo": ataque_g.entidade_alvo is soldado,
        "tilemap": c.tilemap_renderer,
    }


def dois_soldados_atacam_construcao():
    c = IntegrationScenario()
    casa = c.criar_construcao_teste("casa", 820, 300, faccao="goblin", tamanho=128)
    # A construção de teste precisa respeitar a vida configurada pelo jogo
    # para ``casa_goblin``. O GIF e o teste usam essa mesma fonte.
    from core.game_config import obter_config

    assert obter_config("casa_goblin")["vida"] == casa.VIDA_MAXIMA
    s1 = c.criar_personagem("soldado", 600, 240, faccao="aliada")
    s2 = c.criar_personagem("soldado", 600, 360, faccao="aliada")
    a1 = c.controladores[s1]["acoes"]["atacar"]["usecase"]
    a2 = c.controladores[s2]["acoes"]["atacar"]["usecase"]
    a1.iniciar(casa, s1, manual=True)
    a2.iniciar(casa, s2, manual=True)
    trace = []
    destruicao_detectada = False
    pos_destruicao = None
    for i in range(3000):
        c.tick()
        if i % 6 == 0 or destruicao_detectada:
            trace.append(_snapshot(c, [s1, s2], [casa]))
        if not destruicao_detectada and casa.vida <= 0:
            destruicao_detectada = True
            pos_destruicao = i
        if (
            destruicao_detectada
            and pos_destruicao is not None
            and i >= pos_destruicao + 90
        ):
            break
    assert destruicao_detectada, "a construção não chegou a ser destruída"
    assert any(
        e["nome"].startswith("fogo")
        for frame in trace
        for e in frame.get("efeitos", [])
    ), "o fogo da construção não apareceu no trace"
    assert any(
        e["nome"] == "explosao2" for frame in trace for e in frame.get("efeitos", [])
    ), "a explosão da destruição não apareceu no trace"
    assert hypot(s1.x - s2.x, s1.y - s2.y) > 0
    return {
        "kind": "construction_attack",
        "data_source": "real_runtime",
        "trace": trace,
        "construction": {
            "nome": casa.nome,
            "x": casa.x,
            "y": casa.y,
            "size": 128,
            "faccao": getattr(casa, "_faccao_teste", None),
            "vida_inicial": casa.VIDA_MAXIMA,
            "vida_final": casa.vida,
        },
        "tilemap": c.tilemap_renderer,
    }


def inimigos_em_niveis_diferentes():
    c = IntegrationScenario()
    coluna, linha, (sx, sy) = ponto_degrau(c)
    soldado = c.criar_personagem("soldado", sx - 160, sy, altura=0, faccao="aliada")
    goblin = c.criar_personagem("goblin_tocha", sx + 160, sy, altura=1, faccao="goblin")
    atk = c.controladores[soldado]["acoes"]["atacar"]["usecase"]
    atk.iniciar(goblin, soldado, manual=True)
    trace = []
    for i in range(900):
        c.tick()
        if i % 10 == 0:
            trace.append(_snapshot(c, [soldado, goblin]))
        if goblin.vida < goblin.VIDA_MAXIMA:
            break
    assert (
        soldado.altura != goblin.altura
        or soldado.vida < soldado.VIDA_MAXIMA
        or goblin.vida < goblin.VIDA_MAXIMA
    )
    assert goblin.vida < goblin.VIDA_MAXIMA
    return {
        "kind": "combat_step",
        "data_source": "real_runtime",
        "trace": trace,
        "degrau": {"coluna": coluna, "linha": linha},
        "tilemap": c.tilemap_renderer,
    }


def goblin_no_degrau():
    c = IntegrationScenario()
    coluna, linha, (gx, gy) = ponto_degrau(c)
    soldado = c.criar_personagem("soldado", gx - 160, gy, altura=0, faccao="aliada")
    goblin = c.criar_personagem("goblin_tocha", gx, gy, altura=0, faccao="goblin")
    atk = c.controladores[soldado]["acoes"]["atacar"]["usecase"]
    atk.iniciar(goblin, soldado, manual=True)
    inicio = (soldado.x, soldado.y)
    trace = []
    for i in range(900):
        c.tick()
        if i % 10 == 0:
            trace.append(_snapshot(c, [soldado, goblin]))
        if goblin.vida < goblin.VIDA_MAXIMA:
            break
    assert_moved(inicio, soldado)
    assert abs(goblin.x - gx) < 80 and abs(goblin.y - gy) < 80
    assert goblin.vida < goblin.VIDA_MAXIMA
    return {
        "kind": "combat_step",
        "data_source": "real_runtime",
        "trace": trace,
        "degrau": {"coluna": coluna, "linha": linha},
        "tilemap": c.tilemap_renderer,
    }
