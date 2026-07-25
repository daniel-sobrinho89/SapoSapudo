import random

from application.usecases.mover_personagem import MoverPersonagemUseCase
from domains.ovelha.maquina_estado import EstadoOvelha


class ControlarComportamentoOvelhaUseCase:
    def __init__(self, navegacao):
        self.navegacao = navegacao
        self.velocidade = 35
        self.distancia_minima = 40
        self.mover = MoverPersonagemUseCase()

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

        if estado in (
            EstadoOvelha.OCIOSO,
            EstadoOvelha.COMENDO,
        ):
            if acao < 0.70:
                self.ovelha.animacoes.estado = EstadoOvelha.COMENDO

            elif acao < 0.90:
                (
                    self.ovelha.destino_x,
                    self.ovelha.destino_y,
                ) = self.navegacao.ponto_aleatorio_no_raio(
                    self.ovelha.x,
                    self.ovelha.y,
                    40,
                    180,
                )

                self.ovelha.animacoes.estado = EstadoOvelha.CORRENDO

            else:
                self.ovelha.animacoes.estado = EstadoOvelha.OCIOSO_FLIP

        elif estado in (
            EstadoOvelha.OCIOSO_FLIP,
            EstadoOvelha.COMENDO_FLIP,
        ):
            if acao < 0.70:
                self.ovelha.animacoes.estado = EstadoOvelha.COMENDO_FLIP

            elif acao < 0.90:
                (
                    self.ovelha.destino_x,
                    self.ovelha.destino_y,
                ) = self.navegacao.ponto_aleatorio_no_raio(
                    self.ovelha.x,
                    self.ovelha.y,
                    40,
                    180,
                )

                self.ovelha.animacoes.estado = EstadoOvelha.CORRENDO_FLIP

            else:
                self.ovelha.animacoes.estado = EstadoOvelha.OCIOSO

    def _andar(self, dt):
        self.mover.executar(
            personagem=self.ovelha,
            navegacao=self.navegacao,
            velocidade=self.velocidade,
            estado_correndo=EstadoOvelha.CORRENDO,
            estado_correndo_flip=EstadoOvelha.CORRENDO_FLIP,
            estado_parado=EstadoOvelha.COMENDO,
            estado_parado_flip=EstadoOvelha.COMENDO_FLIP,
            dt=dt,
        )
