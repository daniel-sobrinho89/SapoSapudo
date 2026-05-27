import pygame


class AssetManager:

    def __init__(self):

        self.assets = {}

    def carregar(self, nome):

        if nome not in self.assets:

            self.assets[nome] = pygame.image.load(
                f"assets/{nome}"
            ).convert_alpha()

        return self.assets[nome]