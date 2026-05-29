# ==========================================
# sistema_nevoa.py
# ==========================================

import pygame

from systems.clima.nevoa import Nevoa


class SistemaNevoa:

    def __init__(self, area_interna):

        self.nevoas = []

        self.atualizar_area(area_interna)

    # =====================================
    # AREA
    # =====================================

    def atualizar_area(self, area_interna):

        self.area = pygame.Rect(
            area_interna.left + 12,
            area_interna.top + 22,
            area_interna.width - 24,
            area_interna.height - 44
        )

    # =====================================
    # UPDATE
    # =====================================

    def atualizar(self, dt, cloudiness):

        alvo = max(1, int(cloudiness / 35))

        while len(self.nevoas) < alvo:

            self.nevoas.append(
                Nevoa(
                    self.area,
                    intensidade=cloudiness / 100
                )
            )

        while len(self.nevoas) > alvo:

            self.nevoas.pop()

        for nevoa in self.nevoas:
            nevoa.atualizar(dt)

    # =====================================
    # RENDER
    # =====================================

    def renderizar(self, tela):

        for nevoa in self.nevoas:
            nevoa.renderizar(tela)