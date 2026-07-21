import random

from config import LARGURA
from domains.ovelha.maquina_estado import EstadoOvelha


class ControlarComportamentoOvelhaUseCase:
    def __init__(self):
        self.velocidade = 35

        self.limite_esquerdo = 30
        self.limite_direito = LARGURA - 220
        self.distancia_minima = 40

    def executar(self, dt, ovelha):
        self.ovelha = ovelha

        if self.ovelha.animacoes.estado in (
            EstadoOvelha.CORRENDO,
            EstadoOvelha.CORRENDO_FLIP,
        ):
            self._andar(dt)
            return

        self.ovelha.tempo += dt

        if self.ovelha.tempo < self.ovelha.proxima_acao:
            return

        self.ovelha.tempo = 0
        self.ovelha.proxima_acao = random.uniform(3, 8)
        self._escolher_proxima_acao()

    def _escolher_proxima_acao(self):
        estado = self.ovelha.animacoes.estado
        acao = random.random()

        # ==================================================
        # OLHANDO PARA DIREITA
        # ==================================================

        if estado in (
            EstadoOvelha.OCIOSO,
            EstadoOvelha.COMENDO,
        ):
            if acao < 0.70:
                self.ovelha.animacoes.estado = EstadoOvelha.COMENDO

            elif (
                acao < 0.90
                and self.ovelha.x < self.limite_direito - self.distancia_minima
            ):
                self.ovelha.destino_x = random.randint(
                    int(self.ovelha.x + self.distancia_minima),
                    self.limite_direito,
                )
                self.ovelha.animacoes.estado = EstadoOvelha.CORRENDO

            else:
                self.ovelha.animacoes.estado = EstadoOvelha.OCIOSO_FLIP

        # ==================================================
        # OLHANDO PARA ESQUERDA
        # ==================================================

        elif estado in (
            EstadoOvelha.OCIOSO_FLIP,
            EstadoOvelha.COMENDO_FLIP,
        ):
            if acao < 0.70:
                self.ovelha.animacoes.estado = EstadoOvelha.COMENDO_FLIP

            elif (
                acao < 0.90
                and self.ovelha.x > self.limite_esquerdo + self.distancia_minima
            ):
                self.ovelha.destino_x = random.randint(
                    self.limite_esquerdo,
                    int(self.ovelha.x - self.distancia_minima),
                )
                self.ovelha.animacoes.estado = EstadoOvelha.CORRENDO_FLIP

            else:
                self.ovelha.animacoes.estado = EstadoOvelha.OCIOSO

    def _andar(self, dt):
        estado = self.ovelha.animacoes.estado

        if estado == EstadoOvelha.CORRENDO:
            self.ovelha.x += self.velocidade * dt

            if self.ovelha.x >= self.ovelha.destino_x:
                self.ovelha.x = self.ovelha.destino_x
                self.ovelha.animacoes.estado = EstadoOvelha.COMENDO

        elif estado == EstadoOvelha.CORRENDO_FLIP:
            self.ovelha.x -= self.velocidade * dt

            if self.ovelha.x <= self.ovelha.destino_x:
                self.ovelha.x = self.ovelha.destino_x
                self.ovelha.animacoes.estado = EstadoOvelha.COMENDO_FLIP
