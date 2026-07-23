from math import hypot

from domains.aldeao.maquina_estado import EstadoAldeao
from domains.ouro.maquina_estado import EstadoOuro


class ObterOuroUseCase:
    VELOCIDADE = 110
    DISTANCIA_PARADA = 18
    TEMPO_OBTENDO = 4.0

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.guardar_recurso_x = 550
        self.guardar_recurso_y = 265

        self.mina = None
        self.renderer_ouro = None

        self.tempo = 0.0
        self.flip = False

    def iniciar(self, mina, renderer_ouro, personagem):
        self.mina = mina
        self.renderer_ouro = renderer_ouro
        self.aldeao = personagem

        self.tempo = 0.0

        self.flip = mina.x < self.aldeao.x

        if self.flip:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_PICARETA_FLIP
        else:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_PICARETA

    # --------------------------------------------------------

    def executar(self, dt):
        if self.mina is None:
            return

        if self.aldeao.animacoes.maquina.obtendo_ouro():
            self._obter(dt)
        elif self.aldeao.animacoes.maquina.entregando_ouro():
            self._entregar(dt)
        else:
            self._andar(dt)

    # --------------------------------------------------------

    def _andar(self, dt):
        rect = self.renderer_ouro.corpo_rect

        if self.flip:
            destino_x = rect.right - 5
        else:
            destino_x = rect.left - 40

        destino_y = rect.bottom - 35

        dx = destino_x - self.aldeao.x
        dy = destino_y - self.aldeao.y

        distancia = hypot(dx, dy)

        if distancia <= self.DISTANCIA_PARADA:
            self.tempo = 0.0

            if self.flip:
                self.aldeao.animacoes.estado = EstadoAldeao.USANDO_PICARETA_FLIP
            else:
                self.aldeao.animacoes.estado = EstadoAldeao.USANDO_PICARETA

            return

        if distancia > 0:
            self.aldeao.x += (dx / distancia) * self.VELOCIDADE * dt
            self.aldeao.y += (dy / distancia) * self.VELOCIDADE * dt

    # --------------------------------------------------------

    def _obter(self, dt):
        self.tempo += dt

        if self.tempo < self.TEMPO_OBTENDO:
            return

        self.flip = self.guardar_recurso_x < self.aldeao.x
        self.mina.obter_ouro()

        if self.flip:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_OURO_FLIP
        else:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_OURO

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

            self.cenario_principal.adicionar_recurso(recurso_x, recurso_y, "ouro")

            if self.mina.animacoes.estado == EstadoOuro.OBTIDO:
                self.cenario_principal.remover_recurso(self.renderer_ouro)
                self.mina = None
                self.renderer_ouro = None
            else:
                self.iniciar(self.mina, self.renderer_ouro, self.aldeao)

            return

        self.aldeao.x += (dx / distancia) * self.VELOCIDADE * dt
        self.aldeao.y += (dy / distancia) * self.VELOCIDADE * dt
