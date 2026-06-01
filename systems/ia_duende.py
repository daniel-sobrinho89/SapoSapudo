# =====================================
# systems/ia_duende.py
# =====================================

import random


class IADuende:

    # ==========================
    # ESTADOS
    # ==========================

    EXPLORANDO = "explorando"
    OBSERVANDO_SAPO = "observando_sapo"
    OBSERVANDO_POTE = "observando_pote"
    ORBITANDO = "orbitando"
    FUGINDO = "fugindo"

    def __init__(self):

        self.estado = self.EXPLORANDO

        self.tempo_estado = 0.0

        self.tempo_decisao = 0.0

        self.proxima_decisao = random.uniform(
            4.0,
            8.0
        )

        self.orbita_angulo = 0.0

        self.orbita_raio = 80

    # =====================================
    # OBTER AÇÃO
    # =====================================

    def obter_acao(self, dt):

        self.tempo_estado += dt

        self.tempo_decisao += dt

        # =============================
        # NOVA DECISÃO
        # =============================

        if self.tempo_decisao >= self.proxima_decisao:

            self.tempo_decisao = 0.0

            self.proxima_decisao = random.uniform(
                4.0,
                8.0
            )

            escolha = random.random()

            if escolha < 0.35:

                self.estado = (
                    self.OBSERVANDO_SAPO
                )

            elif escolha < 0.65:

                self.estado = (
                    self.OBSERVANDO_POTE
                )

            elif escolha < 0.85:

                self.estado = (
                    self.ORBITANDO
                )

                self.orbita_angulo = 0.0

            else:

                self.estado = (
                    self.FUGINDO
                )

            self.tempo_estado = 0.0

        # =============================
        # VOLTAR A EXPLORAR
        # =============================

        if (
            self.estado != self.EXPLORANDO
            and self.tempo_estado >= 5.0
        ):

            self.estado = self.EXPLORANDO

        return self.estado