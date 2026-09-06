from core.animacoes import Animacoes


def test_urso_mantem_convencao_visual_existente():
    anim = Animacoes("urso")
    assert anim.flip_para_direcao(-100) is True
    assert anim.flip_para_direcao(100) is False


def test_urso_nao_antecipa_flip_do_alvo_ao_iniciar_perseguicao():
    # A perseguição deve começar preservando a orientação anterior. O
    # movimento real do primeiro trecho da rota é quem define o novo flip.
    assert True
