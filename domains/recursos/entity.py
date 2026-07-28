from core.animacoes import Animacoes


class Recurso:
    def __init__(self, nome, x, y):
        self.nome = nome
        self.x = x
        self.y = y
        self.vida = 0
        self.animacoes = Animacoes(nome)
        self.reservado_por = None

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)
