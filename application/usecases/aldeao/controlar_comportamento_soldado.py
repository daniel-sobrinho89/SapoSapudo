import random

from config import LARGURA
from domains.personagem.maquina_estado_soldado import EstadoSoldado


class ControlarComportamentoSoldadoUseCase:
    def __init__(self):
        self.tempo = 0.0
        self.proxima_acao = random.uniform(3, 8)

        self.andando = False
        self.velocidade = 35

        self.limite_esquerdo = 30
        self.limite_direito = LARGURA - 220
        self.distancia_minima = 40

    def executar(self, dt, aldeao):
        self.aldeao = aldeao

        if self.andando:
            self._andar(dt)
            return

        self.tempo += dt

        if self.tempo < self.proxima_acao:
            return

        self.tempo = 0
        self.proxima_acao = random.uniform(3, 8)
        self._escolher_proxima_acao()

    def _escolher_proxima_acao(self):
        estado = self.aldeao.animacoes.estado
        correr = random.random() < 0.35

        # =====================================
        # OCIOSO (olhando para direita)
        # =====================================

        if estado == EstadoSoldado.OCIOSO:
            if correr and self.aldeao.x < self.limite_direito - self.distancia_minima:
                self.andando = True
                self.aldeao.destino_x = random.randint(
                    int(self.aldeao.x + self.distancia_minima),
                    self.limite_direito,
                )

                self.aldeao.animacoes.estado = EstadoSoldado.CORRENDO
            else:
                self.aldeao.animacoes.estado = EstadoSoldado.OCIOSO_FLIP

        # =====================================
        # OCIOSO FLIP (olhando para esquerda)
        # =====================================

        elif estado == EstadoSoldado.OCIOSO_FLIP:
            if correr and self.aldeao.x > self.limite_esquerdo + self.distancia_minima:
                self.andando = True
                self.aldeao.destino_x = random.randint(
                    self.limite_esquerdo,
                    int(self.aldeao.x - self.distancia_minima),
                )

                self.aldeao.animacoes.estado = EstadoSoldado.CORRENDO_FLIP
            else:
                self.aldeao.animacoes.estado = EstadoSoldado.OCIOSO

    def _andar(self, dt):
        estado = self.aldeao.animacoes.estado

        if estado == EstadoSoldado.CORRENDO:
            self.aldeao.x += self.velocidade * dt

            if self.aldeao.x >= self.aldeao.destino_x:
                self.aldeao.x = self.aldeao.destino_x
                self.andando = False

                self.aldeao.animacoes.estado = EstadoSoldado.OCIOSO

        elif estado == EstadoSoldado.CORRENDO_FLIP:
            self.aldeao.x -= self.velocidade * dt

            if self.aldeao.x <= self.aldeao.destino_x:
                self.aldeao.x = self.aldeao.destino_x
                self.andando = False

                self.aldeao.animacoes.estado = EstadoSoldado.OCIOSO_FLIP
