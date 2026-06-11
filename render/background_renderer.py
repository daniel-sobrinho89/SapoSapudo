import pygame_adapter
from datetime import datetime
from render.asset_manager import asset_manager


class BackgroundRenderer:

    def __init__(
        self,
        tela,
        largura,
        altura,
        transform,
        clima_service
    ):

        self.tela = tela
        self.transform = transform
        self.clima_service = clima_service

        # =====================================
        # BACKGROUND MANHÃ
        # =====================================

        background_manha = asset_manager.carregar(
            "background_manha.webp"
        )

        self.background_manha = self.transform.escalar(
            background_manha,
            (largura, altura)
        )

        # =====================================
        # BACKGROUND DIA
        # =====================================

        background_day = asset_manager.carregar(
            "background.webp"
        )

        self.background_day = self.transform.escalar(
            background_day,
            (largura, altura)
        )

        # =====================================
        # BACKGROUND FINAL TARDE
        # =====================================

        background_final_tarde = asset_manager.carregar(
            "background_final_tarde.webp"
        )

        self.background_final_tarde = self.transform.escalar(
            background_final_tarde ,
            (largura, altura)
        )

        # =====================================
        # BACKGROUND NOITE
        # =====================================

        background_night = asset_manager.carregar(
            "background_night_19h.webp"
        )

        self.background_night = self.transform.escalar(
            background_night,
            (largura, altura)
        )

        # =====================================
        # FEIRA MANHÃ
        # =====================================

        background_feira_manha = asset_manager.carregar(
            "background_feira_manha.webp"
        )

        self.background_feira_manha = self.transform.escalar(
            background_feira_manha,
            (largura, altura)
        )

        # =====================================
        # FEIRA DIA
        # =====================================

        background_feira = asset_manager.carregar(
            "background_feira.webp"
        )

        self.background_feira = self.transform.escalar(
            background_feira,
            (largura, altura)
        )

        # =====================================
        # FEIRA FINAL TARDE
        # =====================================

        background_feira_final_tarde = asset_manager.carregar(
            "background_feira_final_tarde.webp"
        )

        self.background_feira_final_tarde = self.transform.escalar(
            background_feira_final_tarde,
            (largura, altura)
        )

        # =====================================
        # FEIRA NOITE
        # =====================================

        background_feira_night = asset_manager.carregar(
            "background_feira_night_19h.webp"
        )

        self.background_feira_night = self.transform.escalar(
            background_feira_night,
            (largura, altura)
        )

        # =====================================
        # CHUVA
        # =====================================

        background_chuva = asset_manager.carregar(
            "background_chuva.webp"
        )

        self.background_chuva = self.transform.escalar(
            background_chuva,
            (largura, altura)
        )

        background_feira_chuva = asset_manager.carregar(
            "background_feira_chuva.webp"
        )

        self.background_feira_chuva = self.transform.escalar(
            background_feira_chuva,
            (largura, altura)
        )

        self.cenario_feira = False


    def obter_background_atual(self):
        if self.cenario_feira:
            return self.obter_background_feira()
        
        if self.esta_chovendo():
            return self.background_chuva

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

    def obter_background_feira(self):
        if self.esta_chovendo():
            return self.background_feira_chuva

        agora = datetime.now()

        hora_atual = (
            agora.hour
            + (agora.minute / 60)
        )

        if 6 <= hora_atual < 12:
            return self.background_feira_manha

        if 15 <= hora_atual < 18.5:
            return self.background_feira_final_tarde

        if hora_atual >= 18.5 or hora_atual < 6:
            return self.background_feira_night

        return self.background_feira

    def eh_dia(self):

        hora_atual = datetime.now().hour

        return not (
            hora_atual >= 19
            or hora_atual < 6
        )

    def esta_chovendo(self):
        if not self.clima_service:
            return False

        return (
            self.clima_service.cloudiness >= 70
        )

    def desenhar(self):

        background = self.obter_background_atual()

        self.tela.blit(
            background,
            (0, 0)
        )