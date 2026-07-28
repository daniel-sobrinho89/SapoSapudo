from math import hypot

from domains.personagem.maquina_estado import EstadoAldeao


class ObterCarneUseCase:
    VELOCIDADE = 110
    DISTANCIA_PARADA = 18
    DISTANCIA_DESLOCAMENTO_PARA_PERSEGUIR = 40
    DISTANCIA_LATERAL_ATAQUE = 40
    TEMPO_MINIMO_ATAQUE = 0.25

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.guardar_recurso_x = 550
        self.guardar_recurso_y = 255

        self.entidade_alvo = None
        self.tempo = 0.0
        self.flip = False
        self.posicao_alvo_no_inicio_ataque = None
        self.item_carregado = None

    def iniciar(self, animal, personagem):
        self.entidade_alvo = animal
        self.personagem = personagem
        self.posicao_alvo_no_inicio_ataque = None
        self.item_carregado = None

        self.tempo = 0.0

        self.flip = animal.x < self.personagem.x

        if self.flip:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_FACA_FLIP
        else:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_FACA

    def cancelar(self):
        self.entidade_alvo = None
        self.item_carregado = None

        if self.flip:
            self.personagem.animacoes.estado = EstadoAldeao.OCIOSO_FLIP
        else:
            self.personagem.animacoes.estado = EstadoAldeao.OCIOSO

    # --------------------------------------------------------

    def executar(self, dt):
        if self.entidade_alvo is None:
            return

        if self.personagem.animacoes.maquina.obtendo_carne():
            if self.entidade_alvo.nome == "carne":
                self._obter()
            elif self.entidade_alvo.vida > 0:
                self._atacar()

        elif self.personagem.animacoes.maquina.entregando_carne():
            self._entregar(dt)
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

    def _atacar(self):
        animacao = self.personagem.animacoes.animacao_atual

        if not self._alvo_ainda_esta_no_alcance():
            if not animacao.golpe_executado:
                return

            self.flip = self.entidade_alvo.x < self.personagem.x

            if self.flip:
                self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_FACA_FLIP
            else:
                self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_FACA

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

        self.entidade_alvo.receber_golpe(
            self.personagem.x,
            *destino,
        )

    def _obter(self):
        self.flip = self.guardar_recurso_x < self.personagem.x

        if not self.cenario_principal.coletar_recurso(
            self.entidade_alvo,
            self.personagem,
        ):
            self.cancelar()
            return

        self.item_carregado = self.entidade_alvo

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

            self.cenario_principal.adicionar_estoque("carne", 1)

            proxima_carne = self.cenario_principal.reservar_recurso(
                "carne",
                self.personagem,
            )

            if proxima_carne is None:
                self.cancelar()
            else:
                self.iniciar(proxima_carne, self.personagem)

            return

        self.personagem.x += (dx / distancia) * self.VELOCIDADE * dt
        self.personagem.y += (dy / distancia) * self.VELOCIDADE * dt
