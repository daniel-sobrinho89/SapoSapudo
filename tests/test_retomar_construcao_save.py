from types import SimpleNamespace

from application.usecases.aldeao.construir_casa import ConstruirCasaUseCase


class Animacoes:
    def __init__(self):
        self.flip = False
        self.estado = None

    def flip_para_direcao(self, dx):
        return dx < 0

    def definir(self, estado, **kwargs):
        self.estado = estado
        if "flip" in kwargs:
            self.flip = kwargs["flip"]


def test_retomar_construcao_preserva_progresso_e_mantem_bernardo_martelando():
    cenario = SimpleNamespace()
    u = ConstruirCasaUseCase(cenario)
    b = SimpleNamespace(
        x=100.0, y=100.0, destino_x=0, destino_y=0, animacoes=Animacoes()
    )
    casa = SimpleNamespace(x=120.0, y=100.0)
    assert u.retomar(b, casa, (130.0, 100.0), 4, tempo=0.75, flip=False)
    assert u.ativo is True
    assert u.madeira_restante == 4
    assert u.tempo == 0.75
    assert u.bernardo is b
    assert u.casa is casa
    assert u.ponto == (130.0, 100.0)
    assert b.destino_x == b.x
    assert b.destino_y == b.y
    assert b.animacoes.estado == "usando_martelo"
