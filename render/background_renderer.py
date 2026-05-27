import pygame
from datetime import datetime


class BackgroundRenderer:

    def __init__(
        self,
        tela,
        largura,
        altura
    ):

        self.tela = tela

        # =====================================
        # BACKGROUND DIA
        # =====================================

        background_day = pygame.image.load(
            "assets/background.png"
        ).convert()

        self.background_day = pygame.transform.smoothscale(
            background_day,
            (largura, altura)
        )

        # =====================================
        # BACKGROUND NOITE
        # =====================================

        background_night = pygame.image.load(
            "assets/background_night_19h.png"
        ).convert()

        self.background_night = pygame.transform.smoothscale(
            background_night,
            (largura, altura)
        )

    def obter_background_atual(self):

        hora_atual = datetime.now().hour

        # =====================================
        # NOITE
        # =====================================

        if hora_atual >= 19 or hora_atual < 6:

            return self.background_night

        # =====================================
        # DIA
        # =====================================

        return self.background_day

    def desenhar(self):

        background = self.obter_background_atual()

        self.tela.blit(
            background,
            (0, 0)
        )