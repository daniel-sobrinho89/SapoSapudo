from core.animacoes import Animacoes


class Efeitos:
    def __init__(self, nome):
        self.nome = nome

        self.animacoes = Animacoes(nome)
        self.corpo_rect = None
        self.x = 0
        self.y = 0
        self.escala_x = 1.0
        self.escala_y = 1.0
        self.inicio_x = 0
        self.deslocamento_x = 0
        self.vida = 0
        self.persistente = False

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)


def criar_efeitos(nome):
    return Efeitos(nome)
