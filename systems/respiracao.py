import math


class Respiracao:

    def __init__(self):

        self.tempo = 0

        # ====================================
        # INTENSIDADE ATUAL
        # ====================================

        self.intensidade = 0.0

    # ====================================
    # UPDATE
    # ====================================

    def atualizar(
        self,
        dt,
        dormindo=False
    ):

        # ====================================
        # VELOCIDADE MAIS LENTA DORMINDO
        # ====================================

        velocidade = (
            0.7 if dormindo else 2.0
        )

        self.tempo += dt * velocidade

        # ====================================
        # SALVA INTENSIDADE
        # ====================================

        self.intensidade = math.sin(
            self.tempo * 2.0
        )

    # ====================================
    # ESCALAS
    # ====================================

    def obter_escalas(
        self,
        escala_base
    ):

        body_scale = escala_base * (
            1.0 + (0.012 * self.intensidade)
        )

        head_scale = escala_base * (
            1.0 + (0.018 * self.intensidade)
        )

        shadow_scale = escala_base * 0.9 * (
            1.0 - (0.03 * self.intensidade)
        )

        return {
            "body": body_scale,
            "head": head_scale,
            "shadow": shadow_scale
        }

    # ====================================
    # OFFSET SOMBRA CABEÇA
    # ====================================

    def obter_offset_sombra_cabeca(self):

        return (
            self.intensidade * 2.2
        )

    # ====================================
    # ROTAÇÃO FOLHA
    # ====================================

    def obter_rotacao_folha(self):

        return (
            math.sin(self.tempo * 1.2)
            * 3
        )