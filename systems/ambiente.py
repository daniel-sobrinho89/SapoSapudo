import math


class Ambiente:

    def __init__(self):

        self.tempo = 0

        self.vento = 0

    def atualizar(self, dt):

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