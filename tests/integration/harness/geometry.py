from dataclasses import dataclass

from utils.config import TILE_SIZE


@dataclass(frozen=True)
class TestRect:
    x: float
    y: float
    w: float
    h: float

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.w

    @property
    def top(self):
        return self.y

    @property
    def bottom(self):
        return self.y + self.h

    @property
    def centerx(self):
        return self.x + self.w / 2

    @property
    def centery(self):
        return self.y + self.h / 2


def tile_center(col, row):
    return (
        col * TILE_SIZE + TILE_SIZE / 2,
        row * TILE_SIZE + TILE_SIZE / 2,
    )
