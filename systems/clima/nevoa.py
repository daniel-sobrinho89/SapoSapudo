# ==========================================
# nevoa.py
# ==========================================

import pygame
import random
import math


class ParticulaNevoa:

    def __init__(self, area, intensidade):

        self.area = area

        self.reset(intensidade)

    # =====================================
    # RESET
    # =====================================

    def reset(self, intensidade):

        self.x = random.uniform(
            0,
            self.area.width
        )

        self.y = random.uniform(
            0,
            self.area.height
        )

        self.velocidade_x = random.uniform(
            0.5,
            2
        ) * intensidade

        self.velocidade_y = random.uniform(
            -2,
            2
        ) * 0.2

        self.raio = random.randint(
            25,
            60
        )

        self.alpha = random.randint(
            2,
            6
        )

        self.offset = random.uniform(
            0,
            100
        )

    # =====================================
    # UPDATE
    # =====================================

    def atualizar(self, dt):

        self.x += self.velocidade_x * dt

        self.y += (
            math.sin(
                pygame.time.get_ticks() * 0.001
                + self.offset
            ) * 0.15
        )

        self.y += self.velocidade_y * dt

        if self.x > self.area.width + self.raio:

            self.x = -self.raio

            self.y = random.uniform(
                0,
                self.area.height
            )

    # =====================================
    # RENDER
    # =====================================

    def renderizar(self, surface):

        largura = self.raio * 5
        altura = self.raio * 2

        blob = pygame.Surface(
            (largura, altura),
            pygame.SRCALPHA
        )

        for i in range(12):

            alpha = int(
                self.alpha * (
                    1 - (i / 12)
                )
            )

            pygame.draw.ellipse(
                blob,
                (255, 255, 255, alpha),
                (
                    i * 2,
                    i // 2,
                    largura - (i * 4),
                    altura - i
                )
            )

        surface.blit(
            blob,
            (
                int(self.x),
                int(self.y)
            )
        )


# ==========================================
# NÉVOA
# ==========================================

class Nevoa:

    def __init__(self, area, intensidade=1):

        self.area = area

        self.intensidade = intensidade

        self.surface = pygame.Surface(
            (
                area.width,
                area.height
            ),
            pygame.SRCALPHA
        ).convert_alpha()

        self.particulas = []

        quantidade = int(
            35 + (40 * intensidade)
        )

        for _ in range(quantidade):

            self.particulas.append(
                ParticulaNevoa(
                    area,
                    intensidade
                )
            )

    # =====================================
    # UPDATE
    # =====================================

    def atualizar(self, dt):

        for particula in self.particulas:
            particula.atualizar(dt)

    # =====================================
    # RENDER
    # =====================================

    def renderizar(self, tela):

        self.surface.fill((0, 0, 0, 0))

        for particula in self.particulas:
            particula.renderizar(self.surface)

        tela.blit(
            self.surface,
            (
                int(self.area.x),
                int(self.area.y)
            )
        )