import math


class AnimacaoFolha:

    def __init__(self):

        self.tempo = 0.0

        # ==========================
        # ROTAÇÃO
        # ==========================

        self.rotacao = 0.0

        self.velocidade = 0.0

        # ==========================
        # CONFIG
        # ==========================

        # Quanto maior:
        # mais rápido tenta voltar
        self.forca_retorno = 5.5

        # Quanto mais perto de 1:
        # mais suave e pesado
        self.amortecimento = 0.94

        # Quanto a respiração afeta
        # a inclinação da folha
        self.intensidade_respiracao = 6.0

        # Intensidade do vento
        self.intensidade_vento = 1.8

    # =====================================
    # UPDATE
    # =====================================

    def atualizar(
        self,
        dt,
        intensidade_respiracao,
        ambiente
    ):

        self.tempo += dt

        # =================================
        # VENTO LENTO E NATURAL
        # =================================

        vento = (
            ambiente.vento
            * self.intensidade_vento
        )

        # =================================
        # RESPIRAÇÃO
        # =================================

        respiracao = (
            intensidade_respiracao
            * self.intensidade_respiracao
        )

        # =================================
        # ALVO
        # =================================

        alvo = vento + respiracao

        # =================================
        # SPRING PHYSICS
        # =================================

        aceleracao = (
            alvo - self.rotacao
        ) * self.forca_retorno

        self.velocidade += aceleracao * (dt * 60)

        self.velocidade *= self.amortecimento

        self.rotacao += self.velocidade * dt
        
        self.rotacao = max(
            -18,
            min(
                18,
                self.rotacao
            )
        )

    # =====================================
    # ROTAÇÃO
    # =====================================

    def obter_rotacao(self):

        return self.rotacao

    # =====================================
    # MICRO MOVIMENTO NATURAL
    # =====================================

    def obter_offset_x(self):

        return (
            math.sin(self.tempo * 0.55)
            * 0.35
        )

    def obter_offset_y(self):

        return (
            math.sin(self.tempo * 0.9)
            * 0.2
        )

    # =====================================
    # MOVIMENTO HERDADO
    # DA RESPIRAÇÃO DA CABEÇA
    # =====================================

    def obter_offset_respiracao(
        self,
        intensidade_respiracao
    ):

        curva = math.sin(
            self.tempo * 0.9
        )

        # Quando a cabeça infla,
        # a folha desce e desloca
        # levemente para esquerda

        offset_x = (
            curva
            * intensidade_respiracao
            * -0.45
        )

        if curva > 0:

            offset_y = (
                curva
                * intensidade_respiracao
                * 0.45
            )

        else:

            offset_y = (
                curva
                * intensidade_respiracao
                * 1.4
            )

        return (
            offset_x,
            offset_y
        )