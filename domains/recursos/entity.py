from core.animacoes import Animacoes


class Recurso:
    def __init__(self, transform, x, y, nome):
        self.nome = nome
        self.transform = transform
        self.x = x
        self.y = y
        self.animacoes = Animacoes(nome)

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)
