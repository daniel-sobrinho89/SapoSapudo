from tests.integration.harness.scenario import (
    IntegrationScenario,
    snapshot_efeito,
    snapshot_visual_entity,
)


def aldeoes_cortando_arvore(quantidade):
    c = IntegrationScenario()
    arvore = c.criar_arvore_teste(700, 300)
    aldeoes = []
    controls = []
    for i in range(quantidade):
        aldeao = c.criar_personagem("aldeao", 500, 220 + i * 70, faccao="aliada")
        controle = c.controladores[aldeao]["acoes"]["arvore"]["usecase"]
        controle.iniciar(arvore, aldeao, manual=True)
        aldeoes.append(aldeao)
        controls.append(controle)
    trace = []
    fases = {a: 0 for a in aldeoes}
    corte_inicial = {a: False for a in aldeoes}
    retorno_detectado = {a: False for a in aldeoes}
    segundo_corte = {a: False for a in aldeoes}

    for i in range(2400):
        c.tick()
        for aldeao in aldeoes:
            cortando = aldeao.animacoes.maquina.cortando_arvore()
            entregando = aldeao.animacoes.maquina.entregando_madeira()
            if cortando and not corte_inicial[aldeao]:
                corte_inicial[aldeao] = True
                fases[aldeao] = max(fases[aldeao], 1)
            if corte_inicial[aldeao] and entregando:
                retorno_detectado[aldeao] = True
                fases[aldeao] = max(fases[aldeao], 2)
            if retorno_detectado[aldeao] and cortando:
                segundo_corte[aldeao] = True
                fases[aldeao] = max(fases[aldeao], 3)

        if i % 6 == 0:
            trace.append(
                {
                    "tempo": round(c.clock.tempo, 3),
                    "arvore_madeira": arvore.madeira,
                    "aldeoes": [
                        {
                            **snapshot_visual_entity(
                                a, faccao=getattr(a, "_faccao_teste", None)
                            ),
                            "cortando": a.animacoes.maquina.cortando_arvore(),
                            "entregando": a.animacoes.maquina.entregando_madeira(),
                        }
                        for a in aldeoes
                    ],
                    "efeitos": [snapshot_efeito(e) for e in c.efeitos],
                }
            )

        if all(segundo_corte.values()) and i >= 30:
            break

    assert all(corte_inicial.values()), (
        "nem todos os aldeões chegaram ao primeiro corte"
    )
    assert all(retorno_detectado.values()), (
        "nem todos os aldeões voltaram ao destino após cortar"
    )
    assert all(segundo_corte.values()), (
        "nem todos os aldeões retornaram ao corte para o segundo ciclo"
    )
    return {
        "kind": "gathering",
        "data_source": "real_runtime",
        "trace": trace,
        "tree": {"x": arvore.x, "y": arvore.y, "madeira": arvore.madeira},
        "count": quantidade,
        "tilemap": c.tilemap_renderer,
    }


def aldeao_termina_arvore_e_inicia_outra():
    """Valida o ciclo REAL de esgotamento de uma árvore.

    A primeira árvore usa a quantidade normal de madeira (8), evitando que
    o teste passe por um atalho artificial de uma única coleta. O aldeão
    precisa cortar, transportar todas as unidades, esgotar a árvore e então
    iniciar o corte em outra árvore dentro de 4 tiles.
    """
    c = IntegrationScenario()
    arvore_inicial = c.criar_arvore_teste(700, 300)
    arvore_proxima = c.criar_arvore_teste(700 + (4 * 64), 300)

    aldeao = c.criar_personagem("aldeao", 500, 220, faccao="aliada")
    controle = c.controladores[aldeao]["acoes"]["arvore"]["usecase"]
    assert controle.iniciar(arvore_inicial, aldeao, manual=True)

    primeiro_corte = False
    primeira_arvore_esgotou = False
    iniciou_segunda_arvore = False
    segundo_corte = False
    entregas = 0
    ultimo_estoque = 0
    trace = []

    for i in range(5000):
        c.tick()

        if aldeao.animacoes.maquina.cortando_arvore():
            if not primeiro_corte:
                primeiro_corte = True
            if iniciou_segunda_arvore:
                segundo_corte = True

        if c.estoque["madeira"] > ultimo_estoque:
            entregas += c.estoque["madeira"] - ultimo_estoque
            ultimo_estoque = c.estoque["madeira"]

        if arvore_inicial.madeira <= 0:
            primeira_arvore_esgotou = True

        if (
            primeira_arvore_esgotou
            and controle.ultima_posicao_corte_x == arvore_proxima.x
            and controle.ultima_posicao_corte_y == arvore_proxima.y
        ):
            iniciou_segunda_arvore = True

        if i % 6 == 0:
            trace.append(
                {
                    "tempo": round(c.clock.tempo, 3),
                    "arvore_inicial_madeira": arvore_inicial.madeira,
                    "arvore_proxima_madeira": arvore_proxima.madeira,
                    "estoque_madeira": c.estoque["madeira"],
                    "aldeao": {
                        **snapshot_visual_entity(
                            aldeao,
                            faccao=getattr(aldeao, "_faccao_teste", None),
                        ),
                        "alvo_x": controle.ultima_posicao_corte_x,
                        "alvo_y": controle.ultima_posicao_corte_y,
                        "cortando": aldeao.animacoes.maquina.cortando_arvore(),
                        "entregando": aldeao.animacoes.maquina.entregando_madeira(),
                    },
                }
            )

        if segundo_corte and i >= 30:
            break

    assert primeiro_corte, "o aldeão não chegou ao primeiro corte"
    assert entregas >= 8, (
        "o aldeão não completou o ciclo normal de transporte das 8 unidades "
        f"de madeira; entregas observadas={entregas}"
    )
    assert primeira_arvore_esgotou, "a primeira árvore não foi completamente cortada"
    assert iniciou_segunda_arvore, (
        "o aldeão não procurou a segunda árvore após esgotar a primeira"
    )
    assert segundo_corte, "o aldeão encontrou a segunda árvore, mas não iniciou o corte"

    return {
        "kind": "gathering_tree_cycle",
        "data_source": "real_runtime",
        "trace": trace,
        "tree_initial": {
            "x": arvore_inicial.x,
            "y": arvore_inicial.y,
            "madeira": arvore_inicial.madeira,
        },
        "tree_next": {
            "x": arvore_proxima.x,
            "y": arvore_proxima.y,
            "madeira": arvore_proxima.madeira,
        },
        "count": 1,
        "tilemap": c.tilemap_renderer,
    }


def aldeoes_trocam_para_arvore_proxima(quantidade=3):
    """Valida a retomada automática em árvore vizinha num raio de até 4 tiles."""
    c = IntegrationScenario()
    arvore_inicial = c.criar_arvore_teste(700, 300)
    # Exatamente 4 tiles (4 * 64 px) da última árvore cortada.
    arvore_proxima = c.criar_arvore_teste(700 + (4 * 64), 300)

    aldeoes = []
    controles = []
    for i in range(quantidade):
        aldeao = c.criar_personagem(
            "aldeao",
            500,
            220 + i * 70,
            faccao="aliada",
        )
        controle = c.controladores[aldeao]["acoes"]["arvore"]["usecase"]
        assert controle.iniciar(arvore_inicial, aldeao, manual=True)
        aldeoes.append(aldeao)
        controles.append(controle)

    primeira_arvore_esgotou = False
    trocas = {aldeao: False for aldeao in aldeoes}
    segundos_cortes = {aldeao: False for aldeao in aldeoes}
    trace = []

    for i in range(2400):
        c.tick()

        if arvore_inicial.madeira <= 0:
            primeira_arvore_esgotou = True

        for aldeao, controle in zip(aldeoes, controles):
            if (
                primeira_arvore_esgotou
                and controle.ultima_posicao_corte_x == arvore_proxima.x
                and controle.ultima_posicao_corte_y == arvore_proxima.y
            ):
                trocas[aldeao] = True

            if trocas[aldeao] and aldeao.animacoes.maquina.cortando_arvore():
                segundos_cortes[aldeao] = True

        if i % 6 == 0:
            trace.append(
                {
                    "tempo": round(c.clock.tempo, 3),
                    "arvore_inicial_madeira": arvore_inicial.madeira,
                    "arvore_proxima_madeira": arvore_proxima.madeira,
                    "aldeoes": [
                        {
                            **snapshot_visual_entity(
                                aldeao,
                                faccao=getattr(aldeao, "_faccao_teste", None),
                            ),
                            "alvo_x": controle.ultima_posicao_corte_x,
                            "alvo_y": controle.ultima_posicao_corte_y,
                            "cortando": aldeao.animacoes.maquina.cortando_arvore(),
                            "entregando": aldeao.animacoes.maquina.entregando_madeira(),
                        }
                        for aldeao, controle in zip(aldeoes, controles)
                    ],
                    "efeitos": [snapshot_efeito(e) for e in c.efeitos],
                }
            )

        if primeira_arvore_esgotou and all(segundos_cortes.values()):
            break

    assert primeira_arvore_esgotou, "a árvore inicial não foi esgotada"
    assert all(trocas.values()), (
        "nem todos os aldeões procuraram a árvore próxima após a árvore inicial esgotar"
    )
    assert all(segundos_cortes.values()), (
        "nem todos os aldeões iniciaram o corte na segunda árvore após a troca"
    )

    return {
        "kind": "gathering_tree_handoff",
        "data_source": "real_runtime",
        "trace": trace,
        "tree_initial": {
            "x": arvore_inicial.x,
            "y": arvore_inicial.y,
            "madeira": arvore_inicial.madeira,
        },
        "tree_next": {
            "x": arvore_proxima.x,
            "y": arvore_proxima.y,
            "madeira": arvore_proxima.madeira,
        },
        "count": quantidade,
        "tilemap": c.tilemap_renderer,
    }


def aldeao_corta_arvore_sem_corpo_rect():
    """O aldeão deve conseguir iniciar o corte mesmo antes do primeiro render da árvore."""
    c = IntegrationScenario()
    aldeao = c.criar_personagem("aldeao", 500, 300, faccao="aliada")
    arvore = c.criar_arvore_teste(700, 300)
    arvore.corpo_rect = None

    controle = c.controladores[aldeao]["acoes"]["arvore"]["usecase"]
    assert controle.iniciar(arvore, aldeao, manual=True)

    for _ in range(240):
        c.tick(1 / 60)
        if aldeao.animacoes.maquina.cortando_arvore():
            break

    assert aldeao.animacoes.maquina.cortando_arvore(), (
        "o aldeão não conseguiu chegar à árvore quando corpo_rect ainda era None"
    )

    return {
        "aldeao": {"x": aldeao.x, "y": aldeao.y},
        "arvore": {"x": arvore.x, "y": arvore.y, "madeira": arvore.madeira},
    }


def aldeao_obter_carne_nao_golpeia_recurso_invalido():
    """Um Recurso que entrou indevidamente no use case não pode derrubar o jogo."""
    from domains.recursos.entity import Recurso

    c = IntegrationScenario()
    aldeao = c.criar_personagem("aldeao", 500, 220, faccao="aliada")
    controle = c.controladores[aldeao]["acoes"]["carne"]["usecase"]

    recurso = Recurso("madeira", 520, 220, 0)
    c.adicionar(recurso, "recursos")

    # Reproduz a situação problemática do runtime: o alvo é um Recurso sem
    # receber_golpe e o use case de carne está no fluxo de ataque.
    controle.entidade_alvo = recurso
    controle.personagem = aldeao

    controle._atacar()

    assert controle.entidade_alvo is None, (
        "um recurso inválido não deveria permanecer como alvo do ObterCarneUseCase"
    )

    return {
        "kind": "gathering_invalid_resource_guard",
        "data_source": "real_runtime",
        "trace": [],
        "tilemap": c.tilemap_renderer,
    }
