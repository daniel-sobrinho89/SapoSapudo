import random

from application.usecases.personagem.mover import MoverPersonagemUseCase
from domains.personagem.maquina_estado_ovelha import EstadoOvelha


class ControlarComportamentoUseCase:
    """Comportamento autônomo genérico dos personagens.

    O estado de animação é injetado pela fábrica, evitando uma classe vazia
    para cada tipo de personagem que só mudava o Enum usado.
    """

    def __init__(self, navegacao, estado, mover=None):
        self.navegacao = navegacao
        self.estado = estado
        # O cenário fornece um único movimentador para que rotas persistentes
        # não fiquem espalhadas por instâncias diferentes de IA.
        self.mover = mover or MoverPersonagemUseCase()
        self.tempo = 0.0
        self.proxima_acao = random.uniform(3, 8)
        self.velocidade = 48
        self.personagem = None

    def iniciar(self, personagem, destino_x, destino_y):
        self.personagem = personagem
        personagem.destino_x = destino_x
        personagem.destino_y = destino_y
        personagem.animacoes.estado = (
            self.estado.CORRENDO
            if destino_x >= personagem.x
            else self.estado.CORRENDO_FLIP
        )
        self.tempo = 0

    def parar(self, personagem):
        personagem.destino_x = personagem.x
        personagem.destino_y = personagem.y
        personagem.animacoes.estado = (
            self.estado.OCIOSO_FLIP
            if personagem.animacoes.maquina.flip
            else self.estado.OCIOSO
        )

    def executar(self, dt, personagem):
        self.personagem = personagem
        correndo = (
            self.estado.CORRENDO,
            self.estado.CORRENDO_FLIP,
        )
        if personagem.animacoes.estado in correndo:
            if not self.mover.executar(
                personagem=personagem,
                navegacao=self.navegacao,
                velocidade=self.velocidade,
                estado_correndo=self.estado.CORRENDO,
                estado_correndo_flip=self.estado.CORRENDO_FLIP,
                estado_parado=self.estado.OCIOSO,
                estado_parado_flip=self.estado.OCIOSO_FLIP,
                dt=dt,
            ):
                self.tempo = 0
                self.proxima_acao = random.uniform(3, 8)
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

        if estado == self.estado.OCIOSO:
            parado, corrida = self.estado.OCIOSO, self.estado.CORRENDO
        elif estado == self.estado.OCIOSO_FLIP:
            parado, corrida = self.estado.OCIOSO_FLIP, self.estado.CORRENDO_FLIP
        else:
            return

        if correr:
            self.personagem.destino_x, self.personagem.destino_y = (
                self.navegacao.ponto_aleatorio_no_raio(
                    self.personagem.base_x,
                    self.personagem.base_y,
                    self.personagem.altura,
                    40,
                    self.personagem.raio_movimento_livre,
                )
            )
            self.personagem.animacoes.estado = corrida
        else:
            self.personagem.animacoes.estado = (
                self.estado.OCIOSO_FLIP
                if parado == self.estado.OCIOSO
                else self.estado.OCIOSO
            )


class ControlarComportamentoOvelhaUseCase(ControlarComportamentoUseCase):
    """Variação da ovelha, que possui comportamento de alimentação."""

    def __init__(self, navegacao, mover=None):
        super().__init__(navegacao, EstadoOvelha, mover=mover)

    def _escolher_proxima_acao(self):
        estado = self.personagem.animacoes.estado
        acao = random.random()

        estados = (
            (EstadoOvelha.OCIOSO, EstadoOvelha.COMENDO, EstadoOvelha.CORRENDO),
            (
                EstadoOvelha.OCIOSO_FLIP,
                EstadoOvelha.COMENDO_FLIP,
                EstadoOvelha.CORRENDO_FLIP,
            ),
        )
        for ocioso, comendo, correndo in estados:
            if estado in (ocioso, comendo):
                if acao < 0.70:
                    self.personagem.animacoes.estado = comendo
                elif acao < 0.90:
                    self.personagem.destino_x, self.personagem.destino_y = (
                        self.navegacao.ponto_aleatorio_no_raio(
                            self.personagem.x,
                            self.personagem.y,
                            self.personagem.altura,
                            40,
                            180,
                        )
                    )
                    self.personagem.animacoes.estado = correndo
                else:
                    self.personagem.animacoes.estado = (
                        EstadoOvelha.OCIOSO_FLIP
                        if ocioso == EstadoOvelha.OCIOSO
                        else EstadoOvelha.OCIOSO
                    )
                return
