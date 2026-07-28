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
        self.personagem = personagem

        self.tempo = 0.0

        self.flip = mina.x < self.personagem.x

        if self.flip:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_PICARETA_FLIP
        else:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_PICARETA

    # --------------------------------------------------------

    def executar(self, dt):
        if self.entidade_alvo is None:
            return

        if self.personagem.animacoes.maquina.obtendo_ouro():
            self._obter(dt)
        elif self.personagem.animacoes.maquina.entregando_ouro():
            self._entregar(dt)
        else:
            self._andar(dt)

    # --------------------------------------------------------

    def _andar(self, dt):
        rect = self.entidade_alvo.corpo_rect

        if self.flip:
            destino_x = rect.right + 18.5
        else:
            destino_x = rect.left - 40

        destino_y = rect.bottom - 35

        dx = destino_x - self.personagem.x
        dy = destino_y - self.personagem.y

        distancia = hypot(dx, dy)

        if distancia <= self.DISTANCIA_PARADA:
            self.tempo = 0.0

            if self.flip:
                self.personagem.animacoes.estado = EstadoAldeao.USANDO_PICARETA_FLIP
            else:
                self.personagem.animacoes.estado = EstadoAldeao.USANDO_PICARETA

            return

        if distancia > 0:
            self.personagem.x += (dx / distancia) * self.VELOCIDADE * dt
            self.personagem.y += (dy / distancia) * self.VELOCIDADE * dt

    # --------------------------------------------------------

    def _obter(self, dt):
        self.tempo += dt

        if self.tempo < self.TEMPO_OBTENDO:
            return

        self.flip = self.guardar_recurso_x < self.personagem.x
        self.entidade_alvo.obter_ouro()

        if self.flip:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_OURO_FLIP
        else:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_OURO

    def _entregar(self, dt):
        if self.entidade_alvo.animacoes.estado == EstadoOuro.OBTIDO:
            self.cenario_principal.remover_personagem(
                self.entidade_alvo, ignorar=self.personagem
            )

        destino_x = self.guardar_recurso_x - 40
        destino_y = self.guardar_recurso_y + 150

        dx = destino_x - self.personagem.x
        dy = destino_y - self.personagem.y

        distancia = hypot(dx, dy)

        if distancia <= self.DISTANCIA_PARADA:
            if self.flip:
                self.personagem.animacoes.estado = EstadoAldeao.OCIOSO_FLIP
            else:
                self.personagem.animacoes.estado = EstadoAldeao.OCIOSO

            OFFSET = 40

            if self.flip:
                recurso_x = self.personagem.x - OFFSET
            else:
                recurso_x = self.personagem.x + OFFSET

            recurso_y = self.personagem.y

            self.cenario_principal.carregar_entidade("ouro", recurso_x, recurso_y)
            self.cenario_principal.adicionar_estoque("ouro", 1)

            if self.entidade_alvo.animacoes.estado == EstadoOuro.OBTIDO:
                self.entidade_alvo = None
            else:
                self.iniciar(self.entidade_alvo, self.personagem)

            return

        self.personagem.x += (dx / distancia) * self.VELOCIDADE * dt
        self.personagem.y += (dy / distancia) * self.VELOCIDADE * dt
