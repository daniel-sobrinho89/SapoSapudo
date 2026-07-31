import random

from core.animacoes import Animacoes
from domains.ovelha.maquina_estado import EstadoOvelha
from utils.config import LARGURA


class Ovelha:
    VIDA_MAXIMA = 40
    TEMPO_EXIBIR_BARRA_VIDA = 3.0

    def __init__(self, nome, x, y):
        self.nome = nome
        self.x = x
        self.y = y
        self.animacoes = Animacoes(nome)
        self.selecionado = False
        self.tempo = 0.0
        self.proxima_acao = random.uniform(3, 8)
        self.destino_x = self.x
        self.carne = 10
        self.vida = self.VIDA_MAXIMA
        self.limite_esquerdo = 30
        self.limite_direito = LARGURA - 220
        self.tempo_barra_vida = 0.0

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)
        self.tempo_barra_vida = max(0.0, self.tempo_barra_vida - dt)

    def receber_golpe(self, atacante, destino_x, destino_y):
        if self.vida <= 0:
            return

        self.vida -= 1
        self.tempo_barra_vida = self.TEMPO_EXIBIR_BARRA_VIDA

        self.destino_x = destino_x
        self.destino_y = destino_y

        if atacante.x < self.x:
            self.animacoes.estado = EstadoOvelha.CORRENDO
        else:
            self.animacoes.estado = EstadoOvelha.CORRENDO_FLIP

    def obter_carne(self):
        self.carne -= 1
        if self.carne == 0:
            self.animacoes.estado = EstadoOvelha.OBTIDO
