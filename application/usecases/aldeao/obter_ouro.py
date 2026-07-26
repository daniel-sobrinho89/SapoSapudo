from math import hypot

from domains.ouro.maquina_estado import EstadoOuro
from domains.personagem.maquina_estado import EstadoAldeao


class ObterOuroUseCase:
    VELOCIDADE = 110
    DISTANCIA_PARADA = 18
    TEMPO_OBTENDO = 4.0

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.guardar_recurso_x = 550
        self.guardar_recurso_y = 265

        self.entidade_alvo = None

        self.tempo = 0.0
        self.flip = False

    def iniciar(self, mina, personagem):
        self.entidade_alvo = mina
        self.aldeao = personagem

        self.tempo = 0.0

        self.flip = mina.x < self.aldeao.x

        if self.flip:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_PICARETA_FLIP
        else:
            self.aldeao.animacoes.estado = EstadoAldeao.CORRENDO_PICARETA

    # --------------------------------------------------------

    def executar(self, dt):
        if self.entidade_alvo is None:
            return

        if self.aldeao.animacoes.maquina.obtendo_ouro():
            self._obter(dt)
        elif self.aldeao.animacoes.maquina.entregando_ouro():
            self._entregar(dt)
        else:
            self._andar(dt)

    # --------------------------------------------------------

    def _andar(self, dt):
        rect = self.entidade_alvo.corpo_rect

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
        self.entidade_alvo.obter_ouro()

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
            self.cenario_principal.adicionar_estoque("ouro", 1)

            if self.entidade_alvo.animacoes.estado == EstadoOuro.OBTIDO:
                self.cenario_principal.remover_recurso(self.entidade_alvo)
                self.entidade_alvo = None
            else:
                self.iniciar(self.entidade_alvo, self.aldeao)

            return

        self.aldeao.x += (dx / distancia) * self.VELOCIDADE * dt
        self.aldeao.y += (dy / distancia) * self.VELOCIDADE * dt
