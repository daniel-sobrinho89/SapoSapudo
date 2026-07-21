from math import hypot

from domains.aldeao.maquina_estado import EstadoAldeao
from domains.ouro.maquina_estado import EstadoOuro


class ObterOuroUseCase:
    VELOCIDADE = 110
    DISTANCIA_PARADA = 18
    TEMPO_CORTANDO = 4.0

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.aldeao = self.cenario_principal.aldeao
        self.casa_duende = self.cenario_principal.casa_duende

        self.mina = None
        self.renderer_ouro = None

        self.tempo = 0.0
        self.flip = False

    def iniciar(self, mina, renderer_ouro):
        self.mina = mina
        self.renderer_ouro = renderer_ouro

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
        OFFSET_X_ESQUERDA = -24
        OFFSET_X_DIREITA = 32
        OFFSET_Y = -34

        if self.flip:
            destino_x = self.mina.x + OFFSET_X_DIREITA
        else:
            destino_x = self.mina.x + OFFSET_X_ESQUERDA

        destino_y = self.mina.y + OFFSET_Y

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

        if self.tempo < self.TEMPO_CORTANDO:
            return

        self.flip = self.casa_duende.x < self.aldeao.x
        self.mina.obter_ouro()

        if self.flip:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_OURO_FLIP
        else:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_OURO

    def _entregar(self, dt):
        destino_x = self.casa_duende.x - 40
        destino_y = self.casa_duende.y + 150

        dx = destino_x - self.aldeao.x
        dy = destino_y - self.aldeao.y

        distancia = hypot(dx, dy)

        if distancia <= self.DISTANCIA_PARADA:
            if self.flip:
                self.aldeao.animacoes.estado = EstadoAldeao.OCIOSO_FLIP
            else:
                self.aldeao.animacoes.estado = EstadoAldeao.OCIOSO

            OFFSET = 80

            if self.flip:
                recurso_x = self.aldeao.x - OFFSET
            else:
                recurso_x = self.aldeao.x + OFFSET

            recurso_y = self.aldeao.y + 70

            self.cenario_principal.adicionar_recurso(recurso_x, recurso_y, "ouro")

            if self.mina.animacoes.estado == EstadoOuro.OBTIDO:
                self.cenario_principal.remover_recurso(self.renderer_ouro)
                self.mina = None
                self.renderer_ouro = None
            else:
                self.iniciar(self.mina, self.renderer_ouro)

            return

        self.aldeao.x += (dx / distancia) * self.VELOCIDADE * dt
        self.aldeao.y += (dy / distancia) * self.VELOCIDADE * dt
