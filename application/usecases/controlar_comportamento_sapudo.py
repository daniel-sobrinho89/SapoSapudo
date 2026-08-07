import random

from application.usecases.mover_personagem import MoverPersonagemUseCase
from domains.personagem.maquina_estado_sapudo import EstadoSapudo


class ControlarComportamentoSapudoUseCase:
    def __init__(self, navegacao):
        self.tempo = 0.0
        self.proxima_acao = random.uniform(3, 8)
        self.navegacao = navegacao
        self.mover = MoverPersonagemUseCase()
        self.velocidade = 35

    def executar(
        self,
        dt,
        personagem,
    ):
        self.personagem = personagem

        if self.personagem.animacoes.estado in (
            EstadoSapudo.CORRENDO,
            EstadoSapudo.CORRENDO_FLIP,
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

        if estado == EstadoSapudo.OCIOSO:
            if correr:
                (
                    self.personagem.destino_x,
                    self.personagem.destino_y,
                ) = self.navegacao.ponto_aleatorio_no_raio(
                    self.personagem.x,
                    self.personagem.y,
                    self.personagem.altura,
                    40,
                    180,
                )

                self.personagem.animacoes.estado = EstadoSapudo.CORRENDO

            else:
                self.personagem.animacoes.estado = EstadoSapudo.OCIOSO_FLIP

        elif estado == EstadoSapudo.OCIOSO_FLIP:
            if correr:
                (
                    self.personagem.destino_x,
                    self.personagem.destino_y,
                ) = self.navegacao.ponto_aleatorio_no_raio(
                    self.personagem.x,
                    self.personagem.y,
                    self.personagem.altura,
                    40,
                    180,
                )

                self.personagem.animacoes.estado = EstadoSapudo.CORRENDO_FLIP

            else:
                self.personagem.animacoes.estado = EstadoSapudo.OCIOSO

    def _andar(self, dt):
        self.mover.executar(
            personagem=self.personagem,
            navegacao=self.navegacao,
            velocidade=self.velocidade,
            estado_correndo=EstadoSapudo.CORRENDO,
            estado_correndo_flip=EstadoSapudo.CORRENDO_FLIP,
            estado_parado=EstadoSapudo.OCIOSO,
            estado_parado_flip=EstadoSapudo.OCIOSO_FLIP,
            dt=dt,
        )
