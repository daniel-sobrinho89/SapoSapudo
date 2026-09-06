import pytest

from core.animacoes import Animacoes


@pytest.mark.parametrize(
    "tipo, dx, esperado",
    [
        ("sapudo", -10, True),
        ("sapudo", 10, False),
        ("aldeao", -10, True),
        ("aldeao", 10, False),
        ("bandido", -10, True),
        ("bandido", 10, False),
        ("ovelha", -10, True),
        ("ovelha", 10, False),
        ("urso", -10, True),
        ("urso", 10, False),
    ],
)
def test_flip_por_direcao_respeita_convencao_de_cada_personagem(tipo, dx, esperado):
    animacoes = Animacoes(tipo)
    assert animacoes.flip_para_direcao(dx) is esperado


def test_personagem_expoe_flip_sincronizado_com_animacao():
    from domains.personagem.entity import Personagem

    personagem = Personagem("aldeao", 0, 0, 0, 10, 1, 0)
    personagem.animacoes.definir_por_direcao("correndo", -10)
    assert personagem.flip is True

    personagem.flip = False
    assert personagem.animacoes.flip is False
