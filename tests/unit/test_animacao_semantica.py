from core.animacoes import Animacoes


def test_animacao_semantica_e_flip():
    anim = Animacoes("esqueleto")
    anim.definir("correndo", flip=True)
    assert anim.nome_animacao_atual == "correndo"
    assert anim.esta_em("correndo")
    assert anim.flip is True


def test_animacao_semantica_preserva_nome_ao_trocar_direcao():
    anim = Animacoes("soldado")
    anim.definir("atacando1")
    anim.definir_flip(True)
    assert anim.esta_em("atacando1")
    assert anim.flip is True
