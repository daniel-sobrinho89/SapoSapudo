from math import hypot

from domains.ovelha.maquina_estado import EstadoOvelha
from domains.personagem.maquina_estado import EstadoAldeao


class ObterCarneUseCase:
    VELOCIDADE = 110
    DISTANCIA_PARADA = 18
    TEMPO_OBTENDO = 4.0
    TEMPO_MINIMO_ATAQUE = 0.25

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.guardar_recurso_x = 550
        self.guardar_recurso_y = 255

        self.entidade_alvo = None
        self.tempo = 0.0
        self.flip = False

    def iniciar(self, animal, personagem):
        self.entidade_alvo = animal
        self.personagem = personagem

        self.tempo = 0.0

        self.flip = animal.x < self.personagem.x

        if self.flip:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_FACA_FLIP
        else:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_FACA

    # --------------------------------------------------------

    def executar(self, dt):
        if self.entidade_alvo is None:
            return

        if self.personagem.animacoes.maquina.obtendo_carne():
            self._obter(dt)
        elif self.personagem.animacoes.maquina.entregando_carne():
            self._entregar(dt)
        else:
            self._andar(dt)

    def _alvo_ainda_esta_no_alcance(self):
        rect = self.entidade_alvo.corpo_rect

        if self.flip:
            destino_x = rect.right - 5
        else:
            destino_x = rect.left - 40

        destino_y = rect.bottom - 30

        dx = destino_x - self.personagem.x
        dy = destino_y - self.personagem.y

        return hypot(dx, dy) <= self.DISTANCIA_PARADA

    def _andar(self, dt):
        self.flip = self.entidade_alvo.x < self.personagem.x

        rect = self.entidade_alvo.corpo_rect

        if self.flip:
            destino_x = rect.right - 5
        else:
            destino_x = rect.left - 40

        destino_y = rect.bottom - 30

        dx = destino_x - self.personagem.x
        dy = destino_y - self.personagem.y

        distancia = hypot(dx, dy)

        if distancia <= self.DISTANCIA_PARADA:
            self.tempo = 0.0

            if self.flip:
                self.personagem.animacoes.estado = EstadoAldeao.USANDO_FACA_FLIP
            else:
                self.personagem.animacoes.estado = EstadoAldeao.USANDO_FACA

            return

        if self.flip:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_FACA_FLIP
        else:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_FACA

        self.personagem.x += (dx / distancia) * self.VELOCIDADE * dt
        self.personagem.y += (dy / distancia) * self.VELOCIDADE * dt

    def _obter(self, dt):
        if self.entidade_alvo.vida > 0:
            animacao = self.personagem.animacoes.animacao_atual

            if not self._alvo_ainda_esta_no_alcance():
                if not animacao.golpe_executado:
                    return

                self.flip = self.entidade_alvo.x < self.personagem.x

                if self.flip:
                    self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_FACA_FLIP
                else:
                    self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_FACA

                return

            if not animacao.golpe_executado:
                return

            destino = self.cenario_principal.navegacao.fugir(
                self.entidade_alvo.x,
                self.entidade_alvo.y,
                self.personagem.x,
                self.personagem.y,
            )

            self.entidade_alvo.receber_golpe(
                self.personagem.x,
                *destino,
            )

            return

        self.tempo += dt

        if self.tempo < self.TEMPO_OBTENDO:
            return

        self.flip = self.guardar_recurso_x < self.personagem.x

        self.entidade_alvo.obter_carne()

        if self.flip:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_CARNE_FLIP
        else:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_CARNE

    def _entregar(self, dt):
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

            self.cenario_principal.adicionar_recurso(recurso_x, recurso_y, "carne")

            if self.entidade_alvo.animacoes.estado == EstadoOvelha.OBTIDO:
                self.entidade_alvo = None
            else:
                self.iniciar(self.entidade_alvo, self.personagem)

            return

        self.personagem.x += (dx / distancia) * self.VELOCIDADE * dt
        self.personagem.y += (dy / distancia) * self.VELOCIDADE * dt
