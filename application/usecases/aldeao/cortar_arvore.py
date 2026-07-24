from math import hypot

from domains.arvore.maquina_estado import EstadoArvore
from domains.personagem.maquina_estado import EstadoAldeao


class CortarArvoreUseCase:
    VELOCIDADE = 110
    DISTANCIA_PARADA = 18
    TEMPO_OBTENDO = 4.0

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.guardar_recurso_x = 550
        self.guardar_recurso_y = 275

        self.arvore = None

        self.tempo = 0.0
        self.flip = False

    def iniciar(self, arvore, personagem):
        self.arvore = arvore
        self.aldeao = personagem

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
            self._obter(dt)
        elif self.aldeao.animacoes.maquina.entregando_madeira():
            self._entregar(dt)
        else:
            self._andar(dt)

    # --------------------------------------------------------

    def _andar(self, dt):
        rect = self.arvore.corpo_rect

        if self.flip:
            destino_x = rect.right - 5
        else:
            destino_x = rect.left - 1

        destino_y = rect.bottom - 25

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

    def _obter(self, dt):
        self.tempo += dt

        if self.tempo < self.TEMPO_OBTENDO:
            return

        self.flip = self.guardar_recurso_x < self.aldeao.x
        self.arvore.obter_madeira()

        if self.flip:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_MADEIRA_FLIP
        else:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_MADEIRA

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

            self.cenario_principal.adicionar_recurso(recurso_x, recurso_y, "madeira")

            if self.arvore.animacoes.estado == EstadoArvore.CORTADA:
                self.arvore = None
            else:
                self.iniciar(self.arvore, self.aldeao)

            return

        self.aldeao.x += (dx / distancia) * self.VELOCIDADE * dt
        self.aldeao.y += (dy / distancia) * self.VELOCIDADE * dt
