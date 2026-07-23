import time
from math import hypot

from utils.input import obter_posicao_ponteiro


class DoubleClickDetector:
    LIMITE_TEMPO = 0.30
    LIMITE_DISTANCIA = 20

    def __init__(self):
        self.ultimo_tempo = 0
        self.ultima_posicao = None

    def detectar(self, posicao):
        agora = time.time()

        if self.ultima_posicao is not None:
            distancia = hypot(
                posicao[0] - self.ultima_posicao[0],
                posicao[1] - self.ultima_posicao[1],
            )

            if (
                agora - self.ultimo_tempo <= self.LIMITE_TEMPO
                and distancia <= self.LIMITE_DISTANCIA
            ):
                self.ultimo_tempo = 0
                self.ultima_posicao = None
                return True

        self.ultimo_tempo = agora
        self.ultima_posicao = posicao

        return False


class Hover:
    @staticmethod
    def esta_sobre(rect):
        if rect is None:
            return False

        return rect.collidepoint(obter_posicao_ponteiro())
