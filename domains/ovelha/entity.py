import random

from config import LARGURA
from core.animacoes import Animacoes
from domains.ovelha.maquina_estado import EstadoOvelha


class Ovelha:
    def __init__(self, transform, x, y, nome):
        self.nome = nome
        self.transform = transform
        self.x = x
        self.y = y
        self.animacoes = Animacoes(nome)
        self.selecionado = False
        self.tempo = 0.0
        self.proxima_acao = random.uniform(3, 8)
        self.destino_x = self.x
        self.carne = 10
        self.vida = 40
        self.limite_esquerdo = 30
        self.limite_direito = LARGURA - 220

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)

    def receber_golpe(self, atacante_x, destino_x, destino_y):
        if self.vida <= 0:
            return

        self.vida -= 1

        self.destino_x = destino_x
        self.destino_y = destino_y

        if atacante_x < self.x:
            self.animacoes.estado = EstadoOvelha.CORRENDO
        else:
            self.animacoes.estado = EstadoOvelha.CORRENDO_FLIP

    def obter_carne(self):
        self.carne -= 1
        if self.carne == 0:
            self.animacoes.estado = EstadoOvelha.OBTIDO
