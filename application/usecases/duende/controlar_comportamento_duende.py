import math
import random

from config import ALTURA, CENTRO_OFFSET_Y, LARGURA


class ControlarComportamentoDuendeUseCase:
    # ==========================
    # ESTADOS
    # ==========================

    EXPLORANDO = "explorando"
    ORBITANDO = "orbitando"
    FUGINDO = "fugindo"
    PERSEGUINDO_ESFERA = "perseguindo_esfera"

    def __init__(self, duende, sapo):
        self.duende = duende
        self.sapo = sapo

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
        self.interesses = {
            self.PERSEGUINDO_ESFERA: 10,
            self.EXPLORANDO: 30,
            self.ORBITANDO: 20,
            self.FUGINDO: 15,
        }

        self.duende.escolher_novo_destino()

    def executar(self, dt):
        estado = self._decidir_proximo_estado(dt)

        if estado == self.PERSEGUINDO_ESFERA:
            pass
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

            self.estado = self._escolher_estado()
            if self.estado == self.PERSEGUINDO_ESFERA:
                self.duende.animacoes.estado = self.duende.animacoes.INDO_ATRAS_ESFERA
            elif self.estado == self.EXPLORANDO:
                destino_x, destino_y = self._obter_destino_teleporte()
                self.duende.teleportar(
                    destino_x,
                    destino_y,
                    duracao=0.35,
                    duracao_sumido=1.15,
                )
            elif self.estado == self.ORBITANDO:
                self.orbita_angulo = 0.0

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

    def _escolher_estado(self):
        pesos = self.interesses.copy()

        # evita repetir o mesmo comportamento
        pesos[self.estado] *= 0.20

        estados = list(pesos.keys())
        valores = list(pesos.values())

        escolhido = random.choices(
            estados,
            weights=valores,
            k=1,
        )[0]

        # reseta o interesse do escolhido
        self.interesses[escolhido] = 5

        # aumenta o interesse dos demais
        for estado in self.interesses:
            if estado != escolhido:
                self.interesses[estado] += 2

        return escolhido

    def _obter_destino_teleporte(self):
        while True:
            escolha = random.randint(0, 5)

            if escolha == 0:
                # Perto do sapo
                destino_x = self.sapo.x + random.randint(-80, 80)
                destino_y = self.sapo.y - random.randint(140, 200)

            elif escolha == 1:
                # Perto do pote
                destino_x = self.pote_x + random.randint(-70, 70)
                destino_y = self.pote_y - random.randint(90, 170)

            elif escolha == 2:
                # Parte superior da tela
                destino_x = random.randint(120, LARGURA - 120)
                destino_y = random.randint(40, 120)

            elif escolha == 3:
                # Lado esquerdo
                destino_x = random.randint(60, 220)
                destino_y = random.randint(80, 260)

            elif escolha == 4:
                # Lado direito
                destino_x = random.randint(LARGURA - 220, LARGURA - 60)
                destino_y = random.randint(80, 260)

            else:
                # Qualquer lugar da área de voo
                destino_x = random.randint(100, LARGURA - 100)
                destino_y = random.randint(60, 260)

            distancia = math.hypot(
                destino_x - self.duende.x,
                destino_y - self.duende.y,
            )

            if distancia >= 220:
                return destino_x, destino_y
