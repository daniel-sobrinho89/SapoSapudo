# ==========================================
# sistema_nuvens.py
# ==========================================

import pygame

from systems.clima.nuvem import Nuvem


class SistemaNuvens:

    def __init__(self, area_interna):

        self.atualizar_area_interna(area_interna)

        self.intensidade = 0
        self.wind_direction = 0
        self.wind_speed = 0

        # atualiza nuvens apenas 20 vezes por segundo
        self.timer_update = 0
        self.intervalo_update = 1 / 20

        # nuvens ativas
        self.nuvens = []

        # pool pré-criado
        self.pool_nuvens = [

            Nuvem(
                self.area_interna,
                intensidade=1
            )

            for _ in range(12)
        ]

    # ==========================================
    # ATUALIZAR ÁREA
    # ==========================================

    def atualizar_area_interna(self, area_interna):
        self.area_interna = pygame.Rect(
            0,
            0,
            1280,
            320
        )

    # ==========================================
    # CALCULAR INTENSIDADE
    # ==========================================

    def calcular_intensidade(
        self,
        atual,
        futuro_1h,
        futuro_2h,
        futuro_3h
    ):

        intensidade = atual

        # crescimento gradual futuro

        if futuro_3h > atual:

            intensidade += (
                (futuro_1h - atual) * 0.2
            )

            intensidade += (
                (futuro_2h - atual) * 0.3
            )

            intensidade += (
                (futuro_3h - atual) * 0.5
            )

        intensidade = max(
            0,
            min(100, intensidade)
        )

        return intensidade

    # ==========================================
    # UPDATE
    # ==========================================

    def atualizar(
        self,
        dt,
        cloudiness,
        future_1h,
        future_2h,
        future_3h,
        wind_direction,
        wind_speed
    ):

        self.intensidade = self.calcular_intensidade(
            cloudiness,
            future_1h,
            future_2h,
            future_3h
        )

        # quantidade de nuvens
        alvo = int(self.intensidade / 15)

        # escala geral
        escala = max(
            0.7,
            self.intensidade / 100
        )

        self.wind_direction = wind_direction
        self.wind_speed = wind_speed

        # cria nuvens
        while len(self.nuvens) < alvo:

            self.nuvens.append(

                Nuvem(
                    self.area_interna,
                    intensidade=escala,
                    wind_direction=self.wind_direction,
                    wind_speed=self.wind_speed
                )
            )

        # remove nuvens extras se houver mais do que o alvo
        while len(self.nuvens) > alvo:

            self.nuvens.pop()

        # atualiza nuvens e mantém apenas as vivas
        nuvens_ativas = []

        for nuvem in self.nuvens:

            if nuvem.atualizar(dt):
                nuvens_ativas.append(nuvem)

        self.nuvens = nuvens_ativas

    # ==========================================
    # RENDER
    # ==========================================

    def renderizar(
        self,
        tela,
        eh_dia=False
    ):

        for nuvem in self.nuvens:

            nuvem.renderizar(
                tela,
                eh_dia
            )