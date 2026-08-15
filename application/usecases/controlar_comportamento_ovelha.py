import random

from application.usecases.personagem.controlar_comportamento_base import (
    ControlarComportamentoBaseUseCase,
)
from domains.personagem.maquina_estado_ovelha import EstadoOvelha


class ControlarComportamentoOvelhaUseCase(ControlarComportamentoBaseUseCase):
    ESTADO = EstadoOvelha

    def _escolher_proxima_acao(self):
        estado = self.personagem.animacoes.estado
        acao = random.random()

        if estado in (
            EstadoOvelha.OCIOSO,
            EstadoOvelha.COMENDO,
        ):
            if acao < 0.70:
                self.personagem.animacoes.estado = EstadoOvelha.COMENDO

            elif acao < 0.90:
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

                self.personagem.animacoes.estado = EstadoOvelha.CORRENDO

            else:
                self.personagem.animacoes.estado = EstadoOvelha.OCIOSO_FLIP

        elif estado in (
            EstadoOvelha.OCIOSO_FLIP,
            EstadoOvelha.COMENDO_FLIP,
        ):
            if acao < 0.70:
                self.personagem.animacoes.estado = EstadoOvelha.COMENDO_FLIP

            elif acao < 0.90:
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

                self.personagem.animacoes.estado = EstadoOvelha.CORRENDO_FLIP

            else:
                self.personagem.animacoes.estado = EstadoOvelha.OCIOSO
