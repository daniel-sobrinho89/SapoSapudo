from math import hypot

from domains.personagem.maquina_estado_soldado import EstadoSoldado


class AtacarUseCase:
    VELOCIDADE = 110
    DISTANCIA_PARADA = 18
    TEMPO_MINIMO_ATAQUE = 0.25

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.entidade_alvo = None

        self.tempo = 0.0
        self.flip = False
        self.segundo_golpe = False

    def iniciar(self, personagemalvo, personagem):
        self.tempo = 0.0
        self.segundo_golpe = False
        self.entidade_alvo = personagemalvo
        self.personagem = personagem

        self.tempo = 0.0

        self.flip = personagemalvo.x < self.personagem.x

        if self.flip:
            self.personagem.animacoes.estado = EstadoSoldado.CORRENDO_FLIP
        else:
            self.personagem.animacoes.estado = EstadoSoldado.CORRENDO

    # --------------------------------------------------------

    def executar(self, dt):
        if self.entidade_alvo is None:
            return

        if self.personagem.animacoes.maquina.atacando():
            self._interagir(dt)
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
                self.personagem.animacoes.estado = EstadoSoldado.ATACANDO1_FLIP
            else:
                self.personagem.animacoes.estado = EstadoSoldado.ATACANDO1

            return

        if self.flip:
            self.personagem.animacoes.estado = EstadoSoldado.CORRENDO_FLIP
        else:
            self.personagem.animacoes.estado = EstadoSoldado.CORRENDO

        novo_x = self.personagem.x + ((dx / distancia) * self.VELOCIDADE * dt)

        novo_y = self.personagem.y + ((dy / distancia) * self.VELOCIDADE * dt)

        (
            self.personagem.x,
            self.personagem.y,
        ) = self.cenario_principal.navegacao.limitar_movimento(
            self.personagem.x,
            self.personagem.y,
            novo_x,
            novo_y,
        )

    def _interagir(self, dt):
        if self.entidade_alvo is None:
            return

        if self.entidade_alvo.vida <= 0:
            self.entidade_alvo = None

            if self.flip:
                self.personagem.animacoes.estado = EstadoSoldado.OCIOSO_FLIP
            else:
                self.personagem.animacoes.estado = EstadoSoldado.OCIOSO

            return

        # ==========================================
        # O alvo fugiu?
        # ==========================================

        animacao = self.personagem.animacoes.animacao_atual

        if not self._alvo_ainda_esta_no_alcance():
            if not animacao.golpe_executado:
                return

            self.flip = self.entidade_alvo.x < self.personagem.x

            if self.flip:
                self.personagem.animacoes.estado = EstadoSoldado.CORRENDO_FLIP
            else:
                self.personagem.animacoes.estado = EstadoSoldado.CORRENDO

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

        ctrl = self.cenario_principal.controladores.get(self.entidade_alvo)

        if ctrl is not None:
            atacar = ctrl["acoes"].get("atacar")

            if atacar is not None:
                atacar["usecase"].iniciar(
                    self.personagem,
                    self.entidade_alvo,
                )

        self.segundo_golpe = not self.segundo_golpe
        self.flip = self.entidade_alvo.x < self.personagem.x

        if self.flip:
            self.personagem.animacoes.estado = (
                EstadoSoldado.ATACANDO2_FLIP
                if self.segundo_golpe
                else EstadoSoldado.ATACANDO1_FLIP
            )
        else:
            self.personagem.animacoes.estado = (
                EstadoSoldado.ATACANDO2
                if self.segundo_golpe
                else EstadoSoldado.ATACANDO1
            )
