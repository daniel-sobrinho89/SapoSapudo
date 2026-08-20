from core.animacoes import Animacoes


class Recurso:
    def __init__(self, nome, x, y, altura):
        self.nome = nome
        self.x = x
        self.y = y
        self.altura = altura
        self.vida = 1
        self.animacoes = Animacoes(nome)
        self.reservado_por = None
        self.grupo_drop = None

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)
