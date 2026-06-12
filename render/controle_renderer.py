import pygame_adapter
from datetime import datetime
from render.asset_manager import asset_manager
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

        self.botao_esquerda = self.assets.carregar(
            "ui/seta_esquerda.webp"
        )

        self.rect_esquerda = pygame_adapter.Rect(
            20,
            ALTURA - 160,
            128,
            128
        )

        self.botao_direita = self.assets.carregar(
            "ui/seta_esquerda.webp"
        )

        self.rect_direita = pygame_adapter.Rect(
            170,
            ALTURA - 160,
            128,
            128
        )

    def renderizar(self):

        self.tela.blit(
            self.botao_esquerda,
            (
                self.rect_esquerda.x,
                self.rect_esquerda.y
            )
        )

        self.tela.blit(
            self.botao_direita,
            (
                self.rect_direita.x,
                self.rect_direita.y
            )
        )