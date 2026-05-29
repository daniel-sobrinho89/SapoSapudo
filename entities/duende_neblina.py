# =====================================
# entities/duende_neblina.py
# =====================================

import math
import random

from systems.ia_duende import IADuende
from systems.animacoes_duende import AnimacoesDuende
from systems.respiracao_duende import RespiracaoDuende

class DuendeNeblina:

    def __init__(self):

        # =================================
        # POSIÇÃO
        # =================================

        self.x = 500
        self.y = 260

        self.base_y = self.y

        # =================================
        # SONO
        # =================================

        self.descendo_para_dormir = False

        self.indo_para_frasco = False

        self.x_entrada_frasco = 0
        self.y_entrada_frasco = 0

        self.y_voo = self.y

        self.y_sono = 510

        self.velocidade_descida = 40

        # =================================
        # MOVIMENTO
        # =================================

        self.velocidade = 35

        self.velocidade_x = 0
        self.velocidade_y = 0

        # =================================
        # DESTINO
        # =================================

        self.alvo_x = self.x
        self.alvo_y = self.y

        self.tempo_novo_destino = 0.0

        # =================================
        # VIDA
        # =================================

        self.tempo = random.uniform(
            0,
            999
        )

        self.batimento_asas = 0.0

        self.voando = True

        self.ia = IADuende()

        self.animacoes = AnimacoesDuende()

        self.respiracao = RespiracaoDuende()

        # =================================
        # ESCALA
        # =================================

        self.escala = 0.10

        # =================================
        # PRIMEIRO DESTINO
        # =================================

        self.escolher_novo_destino()

    # =====================================
    # NOVO DESTINO
    # =====================================

    def escolher_novo_destino(self):

        self.alvo_x = random.randint(
            180,
            1100
        )

        self.alvo_y = random.randint(
            120,
            340
        )

    # =====================================
    # UPDATE
    # =====================================

    def atualizar(
        self,
        dt,
        sapo_x,
        sapo_y,
        pote_x,
        pote_y,
        clima_service,
        frasco_rect
    ):

        self.tempo += dt

        # =================================
        # IA
        # =================================

        self.animacoes.atualizar(dt)

        if (
            not clima_service.clima_disponivel
            and
            not self.animacoes.dormindo
            and
            not self.descendo_para_dormir
            and
            not self.indo_para_frasco
        ):

            self.x_entrada_frasco = (
                frasco_rect.centerx
            )

            self.y_entrada_frasco = (
                frasco_rect.top - 30
            )

            self.indo_para_frasco = True

        if clima_service.clima_disponivel:

            self.indo_para_frasco = False

            self.descendo_para_dormir = False

            self.animacoes.dormindo = False

        self.respiracao.atualizar(
            dt,
            self.animacoes.dormindo
        )

        if self.animacoes.dormindo:

            self.y = self.y_sono

            self.velocidade_x = 0
            self.velocidade_y = 0

            return

        self.ia.atualizar(
            dt,
            self,
            sapo_x,
            sapo_y,
            pote_x,
            pote_y
        )

        # =================================
        # INDO PARA O FRASCO
        # =================================

        if self.indo_para_frasco:

            dx = (
                self.x_entrada_frasco
                - self.x
            )

            dy = (
                self.y_entrada_frasco
                - self.y
            )

            distancia = math.hypot(
                dx,
                dy
            )

            velocidade_base = 30

            velocidade_aproximacao = min(
                50,
                velocidade_base + distancia * 0.15
            )

            if distancia > 5:

                self.x += (
                    dx / distancia
                ) * velocidade_aproximacao * dt

                self.y += (
                    dy / distancia
                ) * velocidade_aproximacao * dt

                self.batimento_asas = math.sin(
                    self.tempo * 10
                )

            else:

                self.indo_para_frasco = False

                self.descendo_para_dormir = True

            return

        # =================================
        # DESCENDO PARA DORMIR
        # =================================

        if self.descendo_para_dormir:

            self.y += (
                self.velocidade_descida * dt
            )

            # pequena sustentação das asas
            altura_restante = max(
                0,
                self.y_sono - self.y
            )

            fator_voo = max(
                0,
                min(1, altura_restante / 80)
            )

            self.y += (
                math.sin(self.tempo * 8)
                * fator_voo
            )

            self.velocidade_x *= 0.95
            self.velocidade_y *= 0.95

            self.batimento_asas = math.sin(
                self.tempo * 8.0
            )

            if self.y >= self.y_sono:

                self.y = self.y_sono

                self.descendo_para_dormir = False

                self.animacoes.dormindo = True

                self.velocidade_x = 0
                self.velocidade_y = 0

                self.batimento_asas = 0

            return

        # =================================
        # TEMPO NOVO DESTINO
        # =================================

        self.tempo_novo_destino += dt

        if self.tempo_novo_destino >= random.uniform(
            3.0,
            6.0
        ):

            self.tempo_novo_destino = 0.0

            self.escolher_novo_destino()

        # =================================
        # DIREÇÃO
        # =================================

        dx = (
            self.alvo_x - self.x
        )

        dy = (
            self.alvo_y - self.y
        )

        distancia = math.hypot(
            dx,
            dy
        )

        # =================================
        # NORMALIZAÇÃO
        # =================================

        if distancia > 1:

            dir_x = dx / distancia
            dir_y = dy / distancia

            # =============================
            # SUAVIZAÇÃO
            # =============================

            aceleracao = 2.2

            self.velocidade_x += (
                (
                    dir_x * self.velocidade
                )
                - self.velocidade_x
            ) * aceleracao * dt

            self.velocidade_y += (
                (
                    dir_y * self.velocidade
                )
                - self.velocidade_y
            ) * aceleracao * dt

        # =================================
        # MOVIMENTO
        # =================================

        self.x += (
            self.velocidade_x * dt
        )

        self.y += (
            self.velocidade_y * dt
        )

        # =================================
        # FLUTUAÇÃO MÁGICA
        # =================================

        if self.animacoes.dormindo:
            self.y = self.y_sono
        else:

            flutuacao = (
                math.sin(self.tempo * 1.8) * 10
                +
                math.sin(self.tempo * 0.6) * 4
            )

            self.y += flutuacao * dt * 8

        # =================================
        # BATIMENTO DAS ASAS
        # =================================

        velocidade_real = math.hypot(
            self.velocidade_x,
            self.velocidade_y
        )

        intensidade_batida = (
            7.5
            + (
                velocidade_real * 0.05
            )
        )

        self.batimento_asas = math.sin(
            self.tempo
            * intensidade_batida
        )