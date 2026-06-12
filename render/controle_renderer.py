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

        self.botao = self.assets.carregar(
            "ui/seta_esquerda.webp"
        )

        self.rect = pygame_adapter.Rect(
            20,
            ALTURA - 160,
            128,
            128
        )

    def renderizar(self):

        self.tela.blit(
            self.botao,
            (
                self.rect.x,
                self.rect.y
            )
        )