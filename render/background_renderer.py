import pygame
from datetime import datetime
from utils.paths import BASE_DIR


class BackgroundRenderer:

    def __init__(
        self,
        tela,
        largura,
        altura
    ):

        self.tela = tela

        # =====================================
        # BACKGROUND MANHÃ
        # =====================================

        background_manha = pygame.image.load(
            str(BASE_DIR / "assets" / "background_manha.png")
        ).convert()

        self.background_manha = pygame.transform.smoothscale(
            background_manha,
            (largura, altura)
        )

        # =====================================
        # BACKGROUND DIA
        # =====================================

        background_day = pygame.image.load(
            str(BASE_DIR / "assets" / "background.png")
        ).convert()

        self.background_day = pygame.transform.smoothscale(
            background_day,
            (largura, altura)
        )

        # =====================================
        # BACKGROUND FINAL TARDE
        # =====================================

        background_final_tarde = pygame.image.load(
            str(BASE_DIR / "assets" / "background_final_tarde.png")
        ).convert()

        self.background_final_tarde = pygame.transform.smoothscale(
            background_final_tarde ,
            (largura, altura)
        )

        # =====================================
        # BACKGROUND NOITE
        # =====================================

        background_night = pygame.image.load(
            str(BASE_DIR / "assets" / "background_night_19h.png")
        ).convert()

        self.background_night = pygame.transform.smoothscale(
            background_night,
            (largura, altura)
        )

    def obter_background_atual(self):

        agora = datetime.now()

        hora_atual = (
            agora.hour
            + (agora.minute / 60)
        )

        # =====================================
        # MANHÃ
        # =====================================

        if 6 <= hora_atual < 12:

            return self.background_manha

        # =====================================
        # FINAL TARDE
        # =====================================

        if 15 <= hora_atual < 18.5:

            return self.background_final_tarde

        # =====================================
        # NOITE
        # =====================================

        if hora_atual >= 18.5 or hora_atual < 6:

            return self.background_night

        # =====================================
        # DIA
        # =====================================

        return self.background_day

    def eh_dia(self):

        hora_atual = datetime.now().hour

        return not (
            hora_atual >= 19
            or hora_atual < 6
        )

    def desenhar(self):

        background = self.obter_background_atual()

        self.tela.blit(
            background,
            (0, 0)
        )