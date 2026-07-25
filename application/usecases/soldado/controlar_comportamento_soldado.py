import random

from application.usecases.mover_personagem import MoverPersonagemUseCase
from domains.personagem.maquina_estado_soldado import EstadoSoldado


class ControlarComportamentoSoldadoUseCase:
    def __init__(self, navegacao):
        self.navegacao = navegacao
        self.mover = MoverPersonagemUseCase()
        self.tempo = 0.0
        self.proxima_acao = random.uniform(3, 8)

        self.velocidade = 35

    def executar(self, dt, personagem):
        self.personagem = personagem

        if self.personagem.animacoes.estado in (
            EstadoSoldado.CORRENDO,
            EstadoSoldado.CORRENDO_FLIP,
        ):
            self._andar(dt)
            return

        self.tempo += dt

        if self.tempo < self.proxima_acao:
            return

        self.tempo = 0
        self.proxima_acao = random.uniform(3, 8)
        self._escolher_proxima_acao()

    def _escolher_proxima_acao(self):
        estado = self.personagem.animacoes.estado
        correr = random.random() < 0.35

        if estado == EstadoSoldado.OCIOSO:
            if correr:
                (
                    self.personagem.destino_x,
                    self.personagem.destino_y,
                ) = self.navegacao.ponto_aleatorio_no_raio(
                    self.personagem.x,
                    self.personagem.y,
                    40,
                    180,
                )

                self.personagem.animacoes.estado = EstadoSoldado.CORRENDO

            else:
                self.personagem.animacoes.estado = EstadoSoldado.OCIOSO_FLIP

        elif estado == EstadoSoldado.OCIOSO_FLIP:
            if correr:
                (
                    self.personagem.destino_x,
                    self.personagem.destino_y,
                ) = self.navegacao.ponto_aleatorio_no_raio(
                    self.personagem.x,
                    self.personagem.y,
                    40,
                    180,
                )

                self.personagem.animacoes.estado = EstadoSoldado.CORRENDO_FLIP

            else:
                self.personagem.animacoes.estado = EstadoSoldado.OCIOSO

    def _andar(self, dt):
        self.mover.executar(
            personagem=self.personagem,
            navegacao=self.navegacao,
            velocidade=self.velocidade,
            estado_correndo=EstadoSoldado.CORRENDO,
            estado_correndo_flip=EstadoSoldado.CORRENDO_FLIP,
            estado_parado=EstadoSoldado.OCIOSO,
            estado_parado_flip=EstadoSoldado.OCIOSO_FLIP,
            dt=dt,
        )
