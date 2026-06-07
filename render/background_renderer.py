import pygame
from datetime import datetime
from render.asset_manager import asset_manager


class BackgroundRenderer:

    def __init__(
        self,
        tela,
        largura,
        altura,
        transform
    ):

        self.tela = tela
        self.transform = transform

        # =====================================
        # BACKGROUND MANHÃ
        # =====================================

        background_manha = asset_manager.carregar(
            "background_manha.png"
        )

        self.background_manha = self.transform.escalar(
            background_manha,
            (largura, altura)
        )

        # =====================================
        # BACKGROUND DIA
        # =====================================

        background_day = asset_manager.carregar(
            "background.png"
        )

        self.background_day = self.transform.escalar(
            background_day,
            (largura, altura)
        )

        # =====================================
        # BACKGROUND FINAL TARDE
        # =====================================

        background_final_tarde = asset_manager.carregar(
            "background_final_tarde.png"
        )

        self.background_final_tarde = self.transform.escalar(
            background_final_tarde ,
            (largura, altura)
        )

        # =====================================
        # BACKGROUND NOITE
        # =====================================

        background_night = asset_manager.carregar(
            "background_night_19h.png"
        )

        self.background_night = self.transform.escalar(
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