import pygame
import random


class ParticulaPoeira:

    def __init__(
        self,
        largura,
        altura
    ):

        self.largura = largura
        self.altura = altura

        self.resetar()

    def resetar(self):

        self.x = random.randint(
            0,
            self.largura
        )

        self.y = random.randint(
            0,
            self.altura
        )

        self.vel_x = random.uniform(
            -0.08,
            0.12
        )

        self.vel_y = random.uniform(
            -0.03,
            -0.12
        )

        self.raio = random.randint(2, 4)

        self.alpha = random.randint(35, 90)

    def atualizar(
        self,
        ambiente
    ):

        self.x += (
            self.vel_x
            + ambiente.vento * 0.03
        )

        self.y += self.vel_y

        if self.y < -10:

            self.y = (
                self.altura + 10
            )

            self.x = random.randint(
                0,
                self.largura
            )

    def desenhar(
        self,
        tela
    ):

        tamanho = self.raio * 6

        superficie = pygame.Surface(
            (
                tamanho,
                tamanho
            ),
            pygame.SRCALPHA
        )

        centro = tamanho // 2

        # =================================
        # GLOW EXTERNO
        # =================================

        pygame.draw.circle(
            superficie,
            (
                255,
                255,
                255,
                int(self.alpha * 0.25)
            ),
            (
                centro,
                centro
            ),
            self.raio * 2
        )

        # =================================
        # NÚCLEO
        # =================================

        pygame.draw.circle(
            superficie,
            (
                255,
                255,
                255,
                self.alpha
            ),
            (
                centro,
                centro
            ),
            self.raio
        )

        tela.blit(
            superficie,
            (
                self.x,
                self.y
            )
        )