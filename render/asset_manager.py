import pygame_adapter
from utils.paths import BASE_DIR


class AssetManager:

    def __init__(self):
        self.assets = {}

    def carregar(self, nome):
        if nome not in self.assets:

            path = BASE_DIR / "assets" / nome
            self.assets[nome] = pygame_adapter.image.load(
                str(path)
            ).convert_alpha()

        return self.assets[nome]

    def carregar_raw(self, nome):
        path = BASE_DIR / "assets" / nome
        return pygame_adapter.image.load_raw(
            str(path)
        )

    def limpar(self):
        self.assets.clear()


asset_manager = AssetManager()