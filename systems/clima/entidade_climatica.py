import pygame
import random


class EntidadeClimatica:

    def __init__(self, imagem, x, y):

        self.imagem = imagem

        self.x = x
        self.y = y

        self.velocidade_y = random.uniform(
            -0.1,
            -0.3
        )

        self.velocidade_x = random.uniform(
            -0.05,
            0.05
        )

        self.alpha = random.randint(120, 220)

        self.direcao = random.choice([-1, 1])

        self.oscilacao = random.uniform(0.1, 0.5)

    # =====================================
    # UPDATE
    # =====================================

    def atualizar(self):

        self.y += self.velocidade_y

        self.x += self.velocidade_x

    # =====================================
    # RENDER
    # =====================================

    def renderizar(self, tela):

        imagem = self.imagem.copy()

        imagem.set_alpha(self.alpha)

        tela.blit(
            imagem,
            (self.x, self.y)
        )