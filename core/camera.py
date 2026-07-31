from utils.config import ALTURA, LARGURA
from utils.kivy_adapter import Rect


class Camera:
    def __init__(
        self,
    ):
        self.x = 0
        self.y = 0

        self.largura = LARGURA
        self.altura = ALTURA
        self.arrastando = False
        self.ultimo_mouse = None

    def seguir(self, entidade):
        self.x = entidade.x - self.largura // 2
        self.y = entidade.y - self.altura // 2

        self.x = max(0, self.x)
        self.y = max(0, self.y)

    def tela(
        self,
        x,
        y,
    ):
        return (
            x - self.x,
            y - self.y,
        )

    def visivel(
        self,
        x,
        y,
        largura,
        altura,
    ):
        sx = x - self.x
        sy = y - self.y

        return not (
            sx + largura < 0 or sy + altura < 0 or sx > self.largura or sy > self.altura
        )

    def tela_rect(self, rect):
        return Rect(
            rect.x - self.x,
            rect.y - self.y,
            rect.w,
            rect.h,
        )

    def mundo(
        self,
        x,
        y,
    ):
        return (
            x + self.x,
            y + self.y,
        )
