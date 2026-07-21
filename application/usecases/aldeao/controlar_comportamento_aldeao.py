import random

from config import LARGURA
from domains.aldeao.maquina_estado import EstadoAldeao


class ControlarComportamentoAldeaoUseCase:
    def __init__(self, aldeao):
        self.aldeao = aldeao

        self.tempo = 0.0
        self.proxima_acao = random.uniform(3, 8)

        self.andando = False
        self.velocidade = 35

        self.limite_esquerdo = 30
        self.limite_direito = LARGURA - 220
        self.distancia_minima = 40

    def executar(self, dt):
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

        if estado == EstadoAldeao.OCIOSO:
            if correr and self.aldeao.x < self.limite_direito - self.distancia_minima:
                self.andando = True
                self.aldeao.destino_x = random.randint(
                    int(self.aldeao.x + self.distancia_minima),
                    self.limite_direito,
                )

                self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO
            else:
                self.aldeao.animacoes.estado = EstadoAldeao.OCIOSO_FLIP

        # =====================================
        # OCIOSO FLIP (olhando para esquerda)
        # =====================================

        elif estado == EstadoAldeao.OCIOSO_FLIP:
            if correr and self.aldeao.x > self.limite_esquerdo + self.distancia_minima:
                self.andando = True
                self.aldeao.destino_x = random.randint(
                    self.limite_esquerdo,
                    int(self.aldeao.x - self.distancia_minima),
                )

                self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_FLIP
            else:
                self.aldeao.animacoes.estado = EstadoAldeao.OCIOSO

        # =====================================
        # MADEIRA
        # =====================================

        elif estado == EstadoAldeao.OCIOSO_MADEIRA:
            if correr and self.aldeao.x < self.limite_direito - self.distancia_minima:
                self.andando = True
                self.aldeao.destino_x = random.randint(
                    int(self.aldeao.x + self.distancia_minima),
                    self.limite_direito,
                )

                self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_MADEIRA
            else:
                self.aldeao.animacoes.estado = EstadoAldeao.OCIOSO_MADEIRA_FLIP

        elif estado == EstadoAldeao.OCIOSO_MADEIRA_FLIP:
            if correr and self.aldeao.x > self.limite_esquerdo + self.distancia_minima:
                self.andando = True
                self.aldeao.destino_x = random.randint(
                    self.limite_esquerdo,
                    int(self.aldeao.x - self.distancia_minima),
                )

                self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_MADEIRA_FLIP
            else:
                self.aldeao.animacoes.estado = EstadoAldeao.OCIOSO_MADEIRA

    def _andar(self, dt):
        estado = self.aldeao.animacoes.estado

        if estado in (
            EstadoAldeao.CORRENDO,
            EstadoAldeao.CORRENDO_MADEIRA,
        ):
            self.aldeao.x += self.velocidade * dt

            if self.aldeao.x >= self.aldeao.destino_x:
                self.aldeao.x = self.aldeao.destino_x
                self.andando = False

                if estado == EstadoAldeao.CORRENDO_MADEIRA:
                    self.aldeao.animacoes.estado = EstadoAldeao.OCIOSO_MADEIRA
                else:
                    self.aldeao.animacoes.estado = EstadoAldeao.OCIOSO_FLIP

        elif estado in (
            EstadoAldeao.CORRENDO_FLIP,
            EstadoAldeao.CORRENDO_MADEIRA_FLIP,
        ):
            self.aldeao.x -= self.velocidade * dt

            if self.aldeao.x <= self.aldeao.destino_x:
                self.aldeao.x = self.aldeao.destino_x
                self.andando = False

                if estado == EstadoAldeao.CORRENDO_MADEIRA_FLIP:
                    self.aldeao.animacoes.estado = EstadoAldeao.OCIOSO_MADEIRA_FLIP
                else:
                    self.aldeao.animacoes.estado = EstadoAldeao.OCIOSO
