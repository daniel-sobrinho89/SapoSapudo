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

        self.entidade_alvo = None

        self.tempo = 0.0
        self.flip = False

    def iniciar(self, arvore, personagem):
        self.entidade_alvo = arvore
        self.personagem = personagem

        self.tempo = 0.0

        self.flip = arvore.x < self.personagem.x

        if self.flip:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_MACHADO_FLIP
        else:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_MACHADO

    def cancelar(self):
        self.entidade_alvo = None

    def executar(self, dt):
        if self.entidade_alvo is None:
            return

        if self.personagem.animacoes.maquina.cortando_arvore():
            self._obter(dt)
        elif self.personagem.animacoes.maquina.entregando_madeira():
            self._entregar(dt)
        else:
            self._andar(dt)

    # --------------------------------------------------------

    def _andar(self, dt):
        rect = self.entidade_alvo.corpo_rect

        if self.flip:
            destino_x = rect.right - 5
        else:
            destino_x = rect.left - 1

        destino_y = rect.bottom - 25

        dx = destino_x - self.personagem.x
        dy = destino_y - self.personagem.y

        distancia = hypot(dx, dy)

        if distancia <= self.DISTANCIA_PARADA:
            self.tempo = 0.0

            if self.flip:
                self.personagem.animacoes.estado = EstadoAldeao.USANDO_MACHADO_FLIP
            else:
                self.personagem.animacoes.estado = EstadoAldeao.USANDO_MACHADO

            return

        if distancia > 0:
            self.personagem.destino_x = destino_x
            self.personagem.destino_y = destino_y

            self.cenario_principal.mover_personagem.executar(
                personagem=self.personagem,
                navegacao=self.cenario_principal.navegacao,
                velocidade=self.VELOCIDADE,
                estado_correndo=EstadoAldeao.CORRENDO_MACHADO,
                estado_correndo_flip=EstadoAldeao.CORRENDO_MACHADO_FLIP,
                estado_parado=EstadoAldeao.OCIOSO,
                estado_parado_flip=EstadoAldeao.OCIOSO_FLIP,
                dt=dt,
            )

    # --------------------------------------------------------

    def _obter(self, dt):
        self.tempo += dt

        if self.tempo < self.TEMPO_OBTENDO:
            return

        self.flip = self.guardar_recurso_x < self.personagem.x
        self.entidade_alvo.obter_madeira()

        if self.flip:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_MADEIRA_FLIP
        else:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_MADEIRA

    def _entregar(self, dt):
        if self.entidade_alvo.animacoes.estado == EstadoArvore.CORTADA:
            self.cenario_principal.parar_acao_global(
                self.entidade_alvo,
                ignorar=self.personagem,
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

            self.cenario_principal.carregar_entidade("madeira", recurso_x, recurso_y)
            self.cenario_principal.adicionar_estoque("madeira", 1)

            if self.entidade_alvo.animacoes.estado == EstadoArvore.CORTADA:
                self.entidade_alvo = None
            else:
                self.iniciar(self.entidade_alvo, self.personagem)

            return

        self.personagem.destino_x = destino_x
        self.personagem.destino_y = destino_y

        self.cenario_principal.mover_personagem.executar(
            personagem=self.personagem,
            navegacao=self.cenario_principal.navegacao,
            velocidade=self.VELOCIDADE,
            estado_correndo=EstadoAldeao.CORRENDO_MADEIRA,
            estado_correndo_flip=EstadoAldeao.CORRENDO_MADEIRA_FLIP,
            estado_parado=EstadoAldeao.OCIOSO,
            estado_parado_flip=EstadoAldeao.OCIOSO_FLIP,
            dt=dt,
        )
