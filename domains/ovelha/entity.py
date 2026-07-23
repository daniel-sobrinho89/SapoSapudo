import random

from domains.ovelha.animacoes import AnimacoesOvelha
from domains.ovelha.maquina_estado import EstadoOvelha


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
        self.carne = 10
        self.vida = 60

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)

    def receber_golpe(self):
        if self.vida > 0:
            self.vida -= 1

    def obter_carne(self):
        self.carne -= 1
        if self.carne == 0:
            self.animacoes.estado = EstadoOvelha.OBTIDO
