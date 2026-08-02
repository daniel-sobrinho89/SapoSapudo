from utils.config import ALTURA, LARGURA
from utils.kivy_adapter import Rect


class Camera:
    def __init__(
        self,
    ):
        self.x = 0
        self.y = 0

        self.zoom = 1.0
        self.zoom_min = 0.5
        self.zoom_max = 3.0

        self.largura = LARGURA
        self.altura = ALTURA
        self.arrastando = False
        self.ultimo_mouse = None

    def seguir(self, entidade):
        self.x = entidade.x - self.largura // 2
        self.y = entidade.y - self.altura // 2

        self.x = max(0, self.x)
        self.y = max(0, self.y)

    def tela(self, x, y):
        return (
            (x - self.x) * self.zoom,
            (y - self.y) * self.zoom,
        )

    def visivel(
        self,
        x,
        y,
        largura,
        altura,
    ):
        largura_visivel = self.largura / self.zoom
        altura_visivel = self.altura / self.zoom

        sx = x - self.x
        sy = y - self.y

        return not (
            sx + largura < 0
            or sy + altura < 0
            or sx > largura_visivel
            or sy > altura_visivel
        )

    def tela_rect(self, rect):
        return Rect(
            int((rect.x - self.x) * self.zoom),
            int((rect.y - self.y) * self.zoom),
            int(rect.w * self.zoom),
            int(rect.h * self.zoom),
        )

    def mundo(
        self,
        x,
        y,
    ):
        return (
            x / self.zoom + self.x,
            y / self.zoom + self.y,
        )

    def aproximar(self):
        self.zoom = min(self.zoom + 0.1, self.zoom_max)

    def afastar(self):
        self.zoom = max(self.zoom - 0.1, self.zoom_min)

    def definir_zoom(self, zoom):
        self.zoom = max(self.zoom_min, min(zoom, self.zoom_max))
