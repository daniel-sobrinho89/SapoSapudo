import math
import random

from config import ALTURA, LARGURA
from constants import CENTRO_OFFSET_Y


class ControlarComportamentoDuendeUseCase:
    # ==========================
    # ESTADOS
    # ==========================

    EXPLORANDO = "explorando"
    ESCONDIDO_VIOLAO = "escondido_violao"
    ORBITANDO = "orbitando"
    FUGINDO = "fugindo"

    def __init__(self, duende, sapo, esconder_atras_violao):
        self.duende = duende
        self.sapo = sapo
        self.esconder_atras_violao = esconder_atras_violao

        self.estado = self.EXPLORANDO
        self.tempo_estado = 0
        self.tempo_decisao = 0
        self.proxima_decisao = random.uniform(4, 8)

        self.orbita_angulo = 0
        self.orbita_raio = 100

        self.centro_x = LARGURA // 2
        self.centro_y = ALTURA // 2 + CENTRO_OFFSET_Y
        self.pote_x = self.centro_x - 260
        self.pote_y = self.centro_y + 40

    def executar(self, dt):
        estado = self._decidir_proximo_estado(dt)

        if estado == self.ESCONDIDO_VIOLAO:
            terminou = self.esconder_atras_violao.executar(dt)
            self.tempo_decisao = 0
            if terminou:
                self.estado = self.EXPLORANDO
                self.tempo_estado = 0
                self.duende.animacoes.iniciar_voo()
        elif estado == self.ORBITANDO:
            self.orbita_angulo += dt * 1.8
            self.duende.alvo_x = (
                self.sapo.x + math.cos(self.orbita_angulo) * self.orbita_raio
            )
            self.duende.alvo_y = self.sapo.y - 140 + math.sin(self.orbita_angulo) * 35
        elif estado == self.FUGINDO:
            self.duende.alvo_x = random.randint(80, 1150)
            self.duende.alvo_y = random.randint(50, 220)

    def _decidir_proximo_estado(self, dt):
        self.tempo_estado += dt
        self.tempo_decisao += dt
        if self.tempo_decisao >= self.proxima_decisao:
            self.tempo_decisao = 0.0
            self.proxima_decisao = random.uniform(4.0, 8.0)
            escolha = random.random()

            if escolha < 0.35 and not self.duende.animacoes.escondendo_atras_violao:
                self.estado = self.ESCONDIDO_VIOLAO
                self.esconder_atras_violao.iniciar()
            elif escolha < 0.65:
                self.estado = self.EXPLORANDO
                destino_x, destino_y = self._obter_destino_teleporte()

                self.duende.teleporte.iniciar(
                    destino_x, destino_y, duracao=0.35, duracao_sumido=1.15
                )
            elif escolha < 0.85:
                self.estado = self.ORBITANDO
                self.orbita_angulo = 0.0
            else:
                self.estado = self.FUGINDO

            self.tempo_estado = 0.0

        if (
            self.estado
            in (
                self.ORBITANDO,
                self.FUGINDO,
            )
            and self.tempo_estado >= 7.0
        ):
            self.estado = self.EXPLORANDO
            self.tempo_estado = 0.0

        return self.estado

    def _obter_destino_teleporte(self):
        while True:
            if random.random() < 0.5:
                destino_x = self.sapo.x + random.randint(-60, 60)
                destino_y = self.sapo.y - 170
            else:
                destino_x = self.pote_x + random.randint(-50, 50)
                destino_y = self.pote_y - 120

            distancia = math.hypot(
                destino_x - self.duende.x,
                destino_y - self.duende.y,
            )

            if distancia >= 220:
                return destino_x, destino_y
