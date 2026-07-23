from math import hypot

from domains.aldeao.maquina_estado import EstadoAldeao
from domains.ovelha.maquina_estado import EstadoOvelha


class ObterCarneUseCase:
    VELOCIDADE = 110
    DISTANCIA_PARADA = 18
    TEMPO_OBTENDO = 4.0

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.guardar_recurso_x = 550
        self.guardar_recurso_y = 255

        self.animal = None
        self.renderer_animal = None

        self.tempo = 0.0
        self.flip = False

    def iniciar(self, animal, renderer_animal, personagem):
        self.animal = animal
        self.renderer_animal = renderer_animal
        self.aldeao = personagem

        self.tempo = 0.0

        self.flip = animal.x < self.aldeao.x

        if self.flip:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_FACA_FLIP
        else:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_FACA

    # --------------------------------------------------------

    def executar(self, dt):
        if self.animal is None:
            return

        if self.aldeao.animacoes.maquina.obtendo_carne():
            self._obter(dt)
        elif self.aldeao.animacoes.maquina.entregando_carne():
            self._entregar(dt)
        else:
            self._andar(dt)

    # --------------------------------------------------------

    def _andar(self, dt):
        rect = self.renderer_animal.corpo_rect

        if self.flip:
            destino_x = rect.right - 5
        else:
            destino_x = rect.left - 40

        destino_y = rect.bottom - 30

        dx = destino_x - self.aldeao.x
        dy = destino_y - self.aldeao.y

        distancia = hypot(dx, dy)

        if distancia <= self.DISTANCIA_PARADA:
            self.tempo = 0.0

            if self.flip:
                self.aldeao.animacoes.estado = EstadoAldeao.USANDO_FACA_FLIP
            else:
                self.aldeao.animacoes.estado = EstadoAldeao.USANDO_FACA

            return

        if distancia > 0:
            self.aldeao.x += (dx / distancia) * self.VELOCIDADE * dt
            self.aldeao.y += (dy / distancia) * self.VELOCIDADE * dt

    # --------------------------------------------------------

    def _obter(self, dt):
        self.tempo += dt

        if self.animal.vida > 0:
            self.animal.receber_golpe()
            return

        if self.tempo < self.TEMPO_OBTENDO:
            return

        self.flip = self.guardar_recurso_x < self.aldeao.x
        self.animal.obter_carne()

        if self.flip:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_CARNE_FLIP
        else:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_CARNE

    def _entregar(self, dt):
        destino_x = self.guardar_recurso_x - 40
        destino_y = self.guardar_recurso_y + 150

        dx = destino_x - self.aldeao.x
        dy = destino_y - self.aldeao.y

        distancia = hypot(dx, dy)

        if distancia <= self.DISTANCIA_PARADA:
            if self.flip:
                self.aldeao.animacoes.estado = EstadoAldeao.OCIOSO_FLIP
            else:
                self.aldeao.animacoes.estado = EstadoAldeao.OCIOSO

            OFFSET = 40

            if self.flip:
                recurso_x = self.aldeao.x - OFFSET
            else:
                recurso_x = self.aldeao.x + OFFSET

            recurso_y = self.aldeao.y

            self.cenario_principal.adicionar_recurso(recurso_x, recurso_y, "carne")

            if self.animal.animacoes.estado == EstadoOvelha.OBTIDO:
                self.cenario_principal.remover_recurso(self.renderer_animal)
                self.animal = None
                self.renderer_animal = None
            else:
                self.iniciar(self.animal, self.renderer_animal, self.aldeao)

            return

        self.aldeao.x += (dx / distancia) * self.VELOCIDADE * dt
        self.aldeao.y += (dy / distancia) * self.VELOCIDADE * dt
