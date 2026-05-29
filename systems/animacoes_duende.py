# =====================================
# systems/animacoes_duende.py
# =====================================

import random


class AnimacoesDuende:

    def __init__(self):

        self.piscando = False

        self.dormindo = False

        self.tempo_piscada = 0.0

        self.tempo_espera = 0.0

        self.intervalo = random.uniform(
            2.0,
            5.0
        )

    # =====================================
    # UPDATE
    # =====================================

    def atualizar(self, dt):

        # =================================
        # DORMINDO
        # =================================

        if self.dormindo:

            self.piscando = False

            return

        # =================================
        # ESPERA
        # =================================

        self.tempo_espera += dt

        # =================================
        # INICIAR PISCADA
        # =================================

        if not self.piscando:

            if (
                self.tempo_espera
                >= self.intervalo
            ):

                self.piscando = True

                self.tempo_piscada = 0.0

        # =================================
        # FINALIZAR PISCADA
        # =================================

        else:

            self.tempo_piscada += dt

            if self.tempo_piscada >= 0.12:

                self.piscando = False

                self.tempo_espera = 0.0

                self.intervalo = random.uniform(
                    2.0,
                    5.0
                )