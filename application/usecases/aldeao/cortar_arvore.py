from math import hypot

from domains.aldeao.maquina_estado import EstadoAldeao
from domains.arvore.maquina_estado import EstadoArvore


class CortarArvoreUseCase:
    VELOCIDADE = 110
    DISTANCIA_PARADA = 18
    TEMPO_CORTANDO = 4.0

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.aldeao = self.cenario_principal.aldeao
        self.casa_duende = self.cenario_principal.casa_duende

        self.arvore = None

        self.tempo = 0.0
        self.flip = False

    # --------------------------------------------------------

    def iniciar(self, arvore):
        self.arvore = arvore

        self.tempo = 0.0

        self.flip = arvore.x < self.aldeao.x

        if self.flip:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_MACHADO_FLIP
        else:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_MACHADO

    # --------------------------------------------------------

    def executar(self, dt):
        if self.arvore is None:
            return

        if self.aldeao.animacoes.maquina.cortando_arvore():
            self._cortar(dt)
        elif self.aldeao.animacoes.maquina.entregando_madeira():
            self._entregar(dt)
        else:
            self._andar(dt)

    # --------------------------------------------------------

    def _andar(self, dt):
        OFFSET_X_ESQUERDA = -24
        OFFSET_X_DIREITA = 37
        OFFSET_Y = 107

        if self.flip:
            destino_x = self.arvore.x + OFFSET_X_DIREITA
        else:
            destino_x = self.arvore.x + OFFSET_X_ESQUERDA

        destino_y = self.arvore.y + OFFSET_Y

        dx = destino_x - self.aldeao.x
        dy = destino_y - self.aldeao.y

        distancia = hypot(dx, dy)

        if distancia <= self.DISTANCIA_PARADA:
            self.tempo = 0.0

            if self.flip:
                self.aldeao.animacoes.estado = EstadoAldeao.USANDO_MACHADO_FLIP
            else:
                self.aldeao.animacoes.estado = EstadoAldeao.USANDO_MACHADO

            return

        if distancia > 0:
            self.aldeao.x += (dx / distancia) * self.VELOCIDADE * dt
            self.aldeao.y += (dy / distancia) * self.VELOCIDADE * dt

    # --------------------------------------------------------

    def _cortar(self, dt):
        self.tempo += dt

        if self.tempo < self.TEMPO_CORTANDO:
            return

        self.flip = self.casa_duende.x < self.aldeao.x
        self.arvore.obter_madeira()

        if self.flip:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_MADEIRA_FLIP
        else:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_MADEIRA

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

            recurso_y = self.aldeao.y + 100

            self.cenario_principal.adicionar_recurso(recurso_x, recurso_y, "madeira")

            if self.arvore.animacoes.estado == EstadoArvore.CORTADA:
                self.arvore = None
            else:
                self.iniciar(self.arvore)

            return

        self.aldeao.x += (dx / distancia) * self.VELOCIDADE * dt
        self.aldeao.y += (dy / distancia) * self.VELOCIDADE * dt
