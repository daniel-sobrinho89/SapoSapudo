import random

from application.usecases.personagem.mover import MoverPersonagemUseCase


class ControlarComportamentoBaseUseCase:
    ESTADO = None

    def __init__(self, navegacao):
        self.navegacao = navegacao
        self.mover = MoverPersonagemUseCase()

        self.tempo = 0.0
        self.proxima_acao = random.uniform(3, 8)
        self.velocidade = 48

    def iniciar(
        self,
        personagem,
        destino_x,
        destino_y,
    ):
        self.personagem = personagem

        personagem.destino_x = destino_x
        personagem.destino_y = destino_y

        if destino_x >= personagem.x:
            personagem.animacoes.estado = self.ESTADO.CORRENDO
        else:
            personagem.animacoes.estado = self.ESTADO.CORRENDO_FLIP

        self.tempo = 0

    def parar(
        self,
        personagem,
    ):
        personagem.destino_x = personagem.x
        personagem.destino_y = personagem.y

        if personagem.animacoes.maquina.flip:
            personagem.animacoes.estado = self.ESTADO.OCIOSO_FLIP
        else:
            personagem.animacoes.estado = self.ESTADO.OCIOSO

    def executar(
        self,
        dt,
        personagem,
    ):
        self.personagem = personagem

        if self.personagem.animacoes.estado in (
            self.ESTADO.CORRENDO,
            self.ESTADO.CORRENDO_FLIP,
        ):
            self._andar(dt)
            return

        self.tempo += dt

        if self.tempo < self.proxima_acao:
            return

        self.tempo = 0
        self.proxima_acao = random.uniform(3, 8)

        self._escolher_proxima_acao()

    def _andar(self, dt):
        movendo = self.mover.executar(
            personagem=self.personagem,
            navegacao=self.navegacao,
            velocidade=self.velocidade,
            estado_correndo=self.ESTADO.CORRENDO,
            estado_correndo_flip=self.ESTADO.CORRENDO_FLIP,
            estado_parado=self.ESTADO.OCIOSO,
            estado_parado_flip=self.ESTADO.OCIOSO_FLIP,
            dt=dt,
        )

        if not movendo:
            self.tempo = 0
            self.proxima_acao = random.uniform(3, 8)

    def _escolher_proxima_acao(self):
        estado = self.personagem.animacoes.estado
        correr = random.random() < 0.35

        if estado == self.ESTADO.OCIOSO:
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

                self.personagem.animacoes.estado = self.ESTADO.CORRENDO

            else:
                self.personagem.animacoes.estado = self.ESTADO.OCIOSO_FLIP

        elif estado == self.ESTADO.OCIOSO_FLIP:
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

                self.personagem.animacoes.estado = self.ESTADO.CORRENDO_FLIP

            else:
                self.personagem.animacoes.estado = self.ESTADO.OCIOSO
