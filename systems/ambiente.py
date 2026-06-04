import math


class Ambiente:

    def __init__(self):

        self.tempo = 0

        self.vento = 0

    def atualizar(self, dt, influencia_clima=0):

        self.tempo += dt

        vento_lento = math.sin(self.tempo * 0.15)

        micro_vento = (
            math.sin(self.tempo * 1.4) * 0.18
        )

        rajada = (
            math.sin(self.tempo * 0.05) * 0.7
        )

        self.vento = (
            vento_lento
            + micro_vento
            + rajada
        )

        self.vento += (
            influencia_clima * 4.0
        )