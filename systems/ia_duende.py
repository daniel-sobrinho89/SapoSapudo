# =====================================
# systems/ia_duende.py
# =====================================

import math
import random


class IADuende:

    EXPLORANDO = "explorando"

    OBSERVANDO_SAPO = "observando_sapo"

    OBSERVANDO_POTE = "observando_pote"

    ORBITANDO = "orbitando"

    FUGINDO = "fugindo"

    def __init__(self):

        self.estado = self.EXPLORANDO

        self.tempo_estado = 0.0

        self.tempo_decisao = 0.0

        self.orbita_angulo = 0.0

        self.orbita_raio = 80

    # =====================================
    # UPDATE
    # =====================================

    def atualizar(
        self,
        dt,
        duende,
        sapo_x,
        sapo_y,
        pote_x,
        pote_y
    ):

        self.tempo_estado += dt

        self.tempo_decisao += dt

        # =================================
        # NOVA DECISÃO
        # =================================

        if self.tempo_decisao >= random.uniform(
            4.0,
            8.0
        ):

            self.tempo_decisao = 0.0

            escolha = random.random()

            # =============================
            # OBSERVAR SAPO
            # =============================

            if escolha < 0.35:

                self.estado = (
                    self.OBSERVANDO_SAPO
                )

            # =============================
            # OBSERVAR POTE
            # =============================

            elif escolha < 0.65:

                self.estado = (
                    self.OBSERVANDO_POTE
                )

            # =============================
            # ORBITAR
            # =============================

            elif escolha < 0.85:

                self.estado = (
                    self.ORBITANDO
                )

                self.orbita_angulo = 0.0

            # =============================
            # FUGIR
            # =============================

            else:

                self.estado = (
                    self.FUGINDO
                )

            self.tempo_estado = 0.0

        # =================================
        # EXPLORANDO
        # =================================

        if self.estado == self.EXPLORANDO:

            return

        # =================================
        # OBSERVANDO SAPO
        # =================================

        elif (
            self.estado
            == self.OBSERVANDO_SAPO
        ):

            duende.alvo_x = (
                sapo_x
                + random.randint(-60, 60)
            )

            duende.alvo_y = (
                sapo_y
                - 180
                + random.randint(-40, 40)
            )

        # =================================
        # OBSERVANDO POTE
        # =================================

        elif (
            self.estado
            == self.OBSERVANDO_POTE
        ):

            duende.alvo_x = (
                pote_x
                + random.randint(-40, 40)
            )

            duende.alvo_y = (
                pote_y
                - 120
                + random.randint(-40, 40)
            )

        # =================================
        # ORBITANDO
        # =================================

        elif (
            self.estado
            == self.ORBITANDO
        ):

            self.orbita_angulo += (
                dt * 1.8
            )

            duende.alvo_x = (
                sapo_x
                + math.cos(
                    self.orbita_angulo
                ) * self.orbita_raio
            )

            duende.alvo_y = (
                sapo_y
                - 140
                + math.sin(
                    self.orbita_angulo
                ) * 35
            )

        # =================================
        # FUGINDO
        # =================================

        elif (
            self.estado
            == self.FUGINDO
        ):

            duende.alvo_x = random.randint(
                80,
                1150
            )

            duende.alvo_y = random.randint(
                50,
                220
            )

        # =================================
        # VOLTAR A EXPLORAR
        # =================================

        if self.tempo_estado >= 5.0:

            self.estado = (
                self.EXPLORANDO
            )