from math import hypot

from domains.personagem.maquina_estado import EstadoAldeao


class ObterCarneUseCase:
    VELOCIDADE = 110
    DISTANCIA_PARADA = 18
    DISTANCIA_PARADA_CARNE = 10
    DISTANCIA_DESLOCAMENTO_PARA_PERSEGUIR = 40
    DISTANCIA_LATERAL_ATAQUE = 40
    DISTANCIA_LATERAL_CARNE = 12
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
        self.grupo_recurso = None
        self.destino_coleta = None
        self.posicao_alvo_destino_coleta = None

    def iniciar(self, animal, personagem, manual=False):
        if getattr(animal, "nome", None) == "carne":
            if not manual:
                return False

            reservado_por = getattr(animal, "reservado_por", None)
            if reservado_por is None:
                if not self.cenario_principal.reservar_drop(animal, personagem):
                    return False
            elif reservado_por is not personagem:
                return False

        self.entidade_alvo = animal
        self.personagem = personagem
        self.grupo_recurso = (
            getattr(animal, "grupo_drop", None)
            if getattr(animal, "nome", None) == "carne"
            else getattr(animal, "grupo_drop", None)
        )
        if getattr(animal, "nome", None) == "carne" and self.grupo_recurso is None:
            self.grupo_recurso = animal

        self.posicao_alvo_no_inicio_ataque = None
        self.item_carregado = None

        self.tempo = 0.0

        self.flip = animal.x < self.personagem.x

        if self.flip:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_FACA_FLIP
        else:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_FACA

        return True

    def cancelar(self):
        alvo = self.entidade_alvo
        if (
            alvo is not None
            and getattr(alvo, "nome", None) == "carne"
            and getattr(alvo, "reservado_por", None) is self.personagem
            and alvo in self.cenario_principal.recursos
        ):
            self.cenario_principal.liberar_reserva_recurso(
                alvo,
                self.personagem,
            )

        self.entidade_alvo = None
        self.item_carregado = None
        self.grupo_recurso = None
        self.destino_coleta = None
        self.posicao_alvo_destino_coleta = None

    def cancelar_coleta(self):
        self.cancelar()

        if self.flip:
            self.personagem.animacoes.estado = EstadoAldeao.OCIOSO_FLIP
        else:
            self.personagem.animacoes.estado = EstadoAldeao.OCIOSO

    def tentar_adquirir_recurso(self, personagem):
        return False

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
        alvo = self.entidade_alvo

        eh_carne = getattr(alvo, "nome", None) == "carne"
        distancia_lateral = (
            self.DISTANCIA_LATERAL_CARNE if eh_carne else self.DISTANCIA_LATERAL_ATAQUE
        )
        distancia_parada = (
            self.DISTANCIA_PARADA_CARNE if eh_carne else self.DISTANCIA_PARADA
        )

        if (
            self.destino_coleta is None
            or self.posicao_alvo_destino_coleta is None
            or hypot(
                alvo.x - self.posicao_alvo_destino_coleta[0],
                alvo.y - self.posicao_alvo_destino_coleta[1],
            )
            > 8
            or not self.cenario_principal.navegacao.pode_andar(
                self.destino_coleta[0],
                self.destino_coleta[1],
                self.personagem.altura,
            )
            or (
                eh_carne
                and hypot(
                    self.destino_coleta[0] - alvo.x,
                    self.destino_coleta[1] - alvo.y,
                )
                > distancia_lateral
            )
        ):
            self.destino_coleta = (
                self.cenario_principal.navegacao.encontrar_ponto_acessivel_proximo(
                    self.personagem.x,
                    self.personagem.y,
                    alvo.x,
                    alvo.y,
                    self.personagem.altura,
                    distancia=distancia_lateral,
                    distancia_maxima_alvo=(distancia_lateral + 2 if eh_carne else None),
                )
            )
            self.posicao_alvo_destino_coleta = (alvo.x, alvo.y)

        if self.destino_coleta is None:
            return

        destino_x, destino_y = self.destino_coleta
        self.flip = alvo.x < self.personagem.x

        dx = destino_x - self.personagem.x
        dy = destino_y - self.personagem.y

        distancia = hypot(dx, dy)

        if distancia <= distancia_parada:
            self.tempo = 0.0
            self.posicao_alvo_no_inicio_ataque = (
                alvo.x,
                alvo.y,
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

        self.personagem.destino_x = destino_x
        self.personagem.destino_y = destino_y

        self.cenario_principal.mover_personagem.executar(
            personagem=self.personagem,
            navegacao=self.cenario_principal.navegacao,
            velocidade=self.VELOCIDADE,
            estado_correndo=EstadoAldeao.CORRENDO_FACA,
            estado_correndo_flip=EstadoAldeao.CORRENDO_FACA_FLIP,
            estado_parado=EstadoAldeao.OCIOSO,
            estado_parado_flip=EstadoAldeao.OCIOSO_FLIP,
            dt=dt,
        )

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
            self.personagem.altura,
        )

        self.entidade_alvo.receber_golpe(
            self.personagem,
            *destino,
        )

    def _obter(self):
        self.flip = self.guardar_recurso_x < self.personagem.x

        if not self.cenario_principal.coletar_recurso(
            self.entidade_alvo,
            self.personagem,
        ):
            self.cancelar_coleta()
            return

        self.item_carregado = self.entidade_alvo

        if self.flip:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_CARNE_FLIP
        else:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_CARNE

    def _continuar_coleta_mesmo_lote(self):
        grupo = self.grupo_recurso
        if grupo is None:
            return False

        candidatos = [
            recurso
            for recurso in self.cenario_principal.recursos
            if (
                getattr(recurso, "nome", None) == "carne"
                and getattr(recurso, "grupo_drop", None) is grupo
                and getattr(recurso, "reservado_por", None) in (None, self.personagem)
            )
        ]

        if not candidatos:
            return False

        candidatos.sort(
            key=lambda recurso: hypot(
                recurso.x - self.personagem.x,
                recurso.y - self.personagem.y,
            )
        )

        for recurso in candidatos:
            reservado_por = getattr(recurso, "reservado_por", None)
            if reservado_por is None:
                if not self.cenario_principal.reservar_drop(recurso, self.personagem):
                    continue

            elif reservado_por is not self.personagem:
                continue

            return self.iniciar(recurso, self.personagem, manual=True)

        return False

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

            if self._continuar_coleta_mesmo_lote():
                return

            self.cancelar_coleta()
            return

        self.personagem.destino_x = destino_x
        self.personagem.destino_y = destino_y

        self.cenario_principal.mover_personagem.executar(
            personagem=self.personagem,
            navegacao=self.cenario_principal.navegacao,
            velocidade=self.VELOCIDADE,
            estado_correndo=EstadoAldeao.CORRENDO_CARNE,
            estado_correndo_flip=EstadoAldeao.CORRENDO_CARNE_FLIP,
            estado_parado=EstadoAldeao.OCIOSO,
            estado_parado_flip=EstadoAldeao.OCIOSO_FLIP,
            dt=dt,
        )
