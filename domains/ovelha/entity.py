import random

from domains.ovelha.animacoes import AnimacoesOvelha


class Ovelha:
    def __init__(self, transform, x, y):
        self.transform = transform
        self.x = x
        self.y = y
        self.animacoes = AnimacoesOvelha()
        self.selecionado = False
        self.tempo = 0.0
        self.proxima_acao = random.uniform(3, 8)
        self.destino_x = self.x

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)
