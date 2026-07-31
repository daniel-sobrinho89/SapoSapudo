from math import hypot

from domains.personagem.maquina_estado_soldado import EstadoSoldado


class AtacarSoldadoUseCase:
    VELOCIDADE = 110
    DISTANCIA_PARADA = 18
    DISTANCIA_DESLOCAMENTO_PARA_PERSEGUIR = 40
    DISTANCIA_LATERAL_ATAQUE = 45
    TEMPO_MINIMO_ATAQUE = 0.25

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.entidade_alvo = None

        self.tempo = 0.0
        self.flip = False
        self.segundo_golpe = False
        self.posicao_alvo_no_inicio_ataque = None

    def iniciar(self, personagemalvo, personagem):
        self.tempo = 0.0
        self.segundo_golpe = False
        self.entidade_alvo = personagemalvo
        self.personagem = personagem
        self.posicao_alvo_no_inicio_ataque = None

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
        if self.posicao_alvo_no_inicio_ataque is None:
            return True

        alvo_x, alvo_y = self.posicao_alvo_no_inicio_ataque
        deslocamento_alvo = hypot(
            self.entidade_alvo.x - alvo_x,
            self.entidade_alvo.y - alvo_y,
        )

        return deslocamento_alvo <= self.DISTANCIA_DESLOCAMENTO_PARA_PERSEGUIR

    def _esta_correndo(self, personagem):
        estado = personagem.animacoes.estado
        tipo_estado = estado.__class__

        return estado in (tipo_estado.CORRENDO, tipo_estado.CORRENDO_FLIP)

    def _andar(self, dt):
        self.flip = self.entidade_alvo.x < self.personagem.x

        if self.flip:
            destino_x = self.entidade_alvo.x + self.DISTANCIA_LATERAL_ATAQUE
        else:
            destino_x = self.entidade_alvo.x - self.DISTANCIA_LATERAL_ATAQUE

        destino_y = self.entidade_alvo.y

        dx = destino_x - self.personagem.x
        dy = destino_y - self.personagem.y

        distancia = hypot(dx, dy)

        if distancia <= self.DISTANCIA_PARADA:
            self.tempo = 0.0
            self.posicao_alvo_no_inicio_ataque = (
                self.entidade_alvo.x,
                self.entidade_alvo.y,
            )

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

            self.posicao_alvo_no_inicio_ataque = None
            return

        if not animacao.golpe_executado:
            return

        destino = self.cenario_principal.navegacao.fugir(
            self.entidade_alvo.x,
            self.entidade_alvo.y,
            self.personagem.x,
            self.personagem.y,
        )

        ctrl = self.cenario_principal.controladores.get(self.entidade_alvo)
        entity = self.cenario_principal.obter_entidade(self.entidade_alvo)

        if entity["grupo"] == "construcoes":
            self.entidade_alvo.receber_golpe()

            defender = ctrl["padrao"]
            defender.iniciar(self.entidade_alvo, self.personagem, entity["faccao"])
        else:
            self.entidade_alvo.receber_golpe(
                self.personagem,
                *destino,
            )

            atacar = ctrl["acoes"].get("atacar")
            alvo_atual = atacar["usecase"].entidade_alvo if atacar else None

            if (
                atacar is not None
                and not self._esta_correndo(self.entidade_alvo)
                and (alvo_atual is None or self._esta_correndo(alvo_atual))
            ):
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
