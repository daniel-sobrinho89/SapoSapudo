from core.animacoes import Animacoes


def test_animacoes_nao_dependem_da_maquina_especifica_do_personagem():
    animacao = Animacoes("esqueleto")

    assert animacao.nome_animacao_atual == "ocioso"
    assert animacao.estado == "ocioso"


def test_controlador_aceita_enums_legados_e_resolve_animacao_sem_importa_los():
    animacao = Animacoes("soldado")

    animacao.definir("correndo", flip=True)

    assert animacao.flip is True
    assert animacao.nome_animacao_atual == "correndo"
    assert animacao.animacao_atual is animacao.animacoes["correndo"]


def test_controlador_expoe_api_declarativa_sem_enum():
    animacao = Animacoes("goblin_tocha")

    animacao.definir("atacando", flip=True)

    assert animacao.nome_animacao_atual == "atacando"
    assert animacao.flip is True
    assert animacao.esta_em("atacando")


def test_estado_visual_e_queries_genericas():
    animacao = Animacoes("esqueleto")
    animacao.definir("defendendo", flip=True)

    assert animacao.esta_em("defendendo")
    assert animacao.flip


def test_mover_pode_usar_nome_de_animacao_sem_enum():
    # A interface é verificada no controlador para não depender de pygame.
    animacao = Animacoes("aldeao")
    animacao.definir("correndo", flip=False)
    assert animacao.nome_animacao_atual == "correndo"
    animacao.definir("ocioso", flip=True)
    assert animacao.nome_animacao_atual == "ocioso"
    assert animacao.flip


def test_animacao_nao_depende_de_maquina_estado_legacy():
    import pathlib

    assert not pathlib.Path("core/maquina_estado_animacao.py").exists()
    assert not pathlib.Path("domains/personagem/maquina_estado.py").exists()


def test_configuracao_nao_contem_flip_para_esquerda():
    for _tipo, config in Animacoes.CONFIG.items():
        assert "flip_para_esquerda" not in config


def test_animacao_flip_continua_avancando_os_mesmos_frames_da_animacao_base():
    animacao = Animacoes("sapudo")

    animacao.definir("correndo", flip=True)
    assert animacao.obter_selecao_frame()[0] == "correndo_flip"
    assert animacao.obter_selecao_frame()[1] == 0

    animacao.atualizar(0.16)
    assert animacao.obter_selecao_frame()[1] == 0

    animacao.atualizar(0.16)
    assert animacao.obter_selecao_frame()[1] == 1


def test_trocar_apenas_o_flip_nao_cria_outra_animacao_temporal():
    animacao = Animacoes("soldado")

    animacao.definir("atacando1", flip=False)
    base = animacao.animacao_atual
    animacao.atualizar(0.21)
    animacao.definir_flip(True)

    assert animacao.animacao_atual is base
    assert animacao.esta_em("atacando1")
    assert animacao.flip is True
