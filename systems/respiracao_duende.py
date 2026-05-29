# =====================================
# systems/respiracao_duende.py
# =====================================

import math


class RespiracaoDuende:

    def __init__(self):

        self.tempo = 0.0

        self.intensidade = 0.0

    # =====================================
    # UPDATE
    # =====================================

    def atualizar(
        self,
        dt,
        dormindo=False
    ):

        velocidade = (

            0.45

            if dormindo

            else 1.2
        )

        self.tempo += (
            dt * velocidade
        )

        self.intensidade = math.sin(
            self.tempo * 1.7
        )