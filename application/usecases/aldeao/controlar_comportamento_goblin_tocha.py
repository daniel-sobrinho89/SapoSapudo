import random

from config import LARGURA
from domains.personagem.maquina_estado_goblin_tocha import EstadoGoblinTocha


class ControlarComportamentoGoblinTochaUseCase:
    def __init__(self):
        self.tempo = 0.0
        self.proxima_acao = random.uniform(3, 8)

        self.andando = False
        self.velocidade = 35

        self.limite_esquerdo = 30
        self.limite_direito = LARGURA - 220
        self.distancia_minima = 40

    def executar(self, dt, personagem):
        self.personagem = personagem

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
        estado = self.personagem.animacoes.estado
        correr = random.random() < 0.35

        # =====================================
        # OCIOSO (olhando para direita)
        # =====================================

        if estado == EstadoGoblinTocha.OCIOSO:
            if (
                correr
                and self.personagem.x < self.limite_direito - self.distancia_minima
            ):
                self.andando = True
                self.personagem.destino_x = random.randint(
                    int(self.personagem.x + self.distancia_minima),
                    self.limite_direito,
                )

                self.personagem.animacoes.estado = EstadoGoblinTocha.CORRENDO
            else:
                self.personagem.animacoes.estado = EstadoGoblinTocha.OCIOSO_FLIP

        # =====================================
        # OCIOSO FLIP (olhando para esquerda)
        # =====================================

        elif estado == EstadoGoblinTocha.OCIOSO_FLIP:
            if (
                correr
                and self.personagem.x > self.limite_esquerdo + self.distancia_minima
            ):
                self.andando = True
                self.personagem.destino_x = random.randint(
                    self.limite_esquerdo,
                    int(self.personagem.x - self.distancia_minima),
                )

                self.personagem.animacoes.estado = EstadoGoblinTocha.CORRENDO_FLIP
            else:
                self.personagem.animacoes.estado = EstadoGoblinTocha.OCIOSO

    def _andar(self, dt):
        estado = self.personagem.animacoes.estado

        if estado == EstadoGoblinTocha.CORRENDO:
            self.personagem.x += self.velocidade * dt

            if self.personagem.x >= self.personagem.destino_x:
                self.personagem.x = self.personagem.destino_x
                self.andando = False

                self.personagem.animacoes.estado = EstadoGoblinTocha.OCIOSO

        elif estado == EstadoGoblinTocha.CORRENDO_FLIP:
            self.personagem.x -= self.velocidade * dt

            if self.personagem.x <= self.personagem.destino_x:
                self.personagem.x = self.personagem.destino_x
                self.andando = False

                self.personagem.animacoes.estado = EstadoGoblinTocha.OCIOSO_FLIP
