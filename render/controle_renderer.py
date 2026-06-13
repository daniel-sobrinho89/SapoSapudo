import pygame_adapter
from config import *


class ControleRenderer:

    def __init__(
        self,
        tela,
        assets,
        transform
    ):
        self.tela = tela
        self.assets = assets
        self.transform = transform
        self.botao_esquerda_pressionado = False
        self.botao_direita_pressionado = False

        self.botao_esquerda = self.assets.carregar(
            "ui/seta_esquerda.webp"
        )

        self.botao_esquerda = pygame_adapter.transform.scale(
            self.botao_esquerda,
            (
                self.botao_esquerda.get_width() // 2,
                self.botao_esquerda.get_height() // 2
            )
        )

        # =====================================
        # POSIÇÃO VISUAL
        # =====================================

        self.rect_esquerda = pygame_adapter.Rect(
            -15,
            ALTURA - 95,
            self.botao_esquerda.get_width(),
            self.botao_esquerda.get_height()
        )

        self.botao_direita = pygame_adapter.transform.flip(
            self.botao_esquerda,
            True,   # espelha horizontalmente
            False   # não espelha verticalmente
        )

        self.rect_direita = pygame_adapter.Rect(
            LARGURA - self.botao_direita.get_width() + 15,
            ALTURA - 95,
            self.botao_direita.get_width(),
            self.botao_direita.get_height()
        )

        # =====================================
        # ÁREA DE CLIQUE
        # =====================================
        # Ajustada para remover as bordas transparentes
        # sem alterar a posição visual dos botões.

        self.rect_clique_esquerda = pygame_adapter.Rect(
            self.rect_esquerda.x + 18,
            self.rect_esquerda.y + 31,
            self.rect_esquerda.width - 38,
            self.rect_esquerda.height - 65
        )

        self.rect_clique_direita = pygame_adapter.Rect(
            self.rect_direita.x + 18,
            self.rect_direita.y + 31,
            self.rect_direita.width - 38,
            self.rect_direita.height - 65
        )

    def renderizar(self):
        botao_esquerda = self.botao_esquerda
        if self.botao_esquerda_pressionado:

            largura = int(botao_esquerda.get_width() * 0.9)
            altura = int(botao_esquerda.get_height() * 0.9)

            botao_esquerda = pygame_adapter.transform.scale(
                botao_esquerda,
                (largura, altura)
            )

            x = self.rect_esquerda.x + (
                self.rect_esquerda.width - largura
            ) // 2

            y = self.rect_esquerda.y + (
                self.rect_esquerda.height - altura
            ) // 2

        else:

            x = self.rect_esquerda.x
            y = self.rect_esquerda.y

        self.tela.blit(botao_esquerda, (x, y))

        botao_direita = self.botao_direita
        if self.botao_direita_pressionado:

            largura = int(botao_direita.get_width() * 0.9)
            altura = int(botao_direita.get_height() * 0.9)

            botao_direita = pygame_adapter.transform.scale(
                botao_direita,
                (largura, altura)
            )

            x = self.rect_direita.x + (
                self.rect_direita.width - largura
            ) // 2

            y = self.rect_direita.y + (
                self.rect_direita.height - altura
            ) // 2

        else:

            x = self.rect_direita.x
            y = self.rect_direita.y

        self.tela.blit(botao_direita, (x, y))

        # DEBUG
        # pygame_adapter.draw.rect(
        #     self.tela,
        #     (255, 0, 0),
        #     self.rect_clique_esquerda
        # )
        #
        # pygame_adapter.draw.rect(
        #     self.tela,
        #     (0, 255, 0),
        #     self.rect_clique_direita
        # )