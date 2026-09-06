import random

from application.usecases.personagem.mover import MoverPersonagemUseCase


class ControlarComportamentoUseCase:
    """Comportamento autônomo genérico orientado a ações visuais declarativas."""

    def __init__(self, navegacao, estado=None, mover=None, world_context=None):
        self.navegacao = navegacao
        # ``estado`` é mantido apenas como parâmetro de compatibilidade.
        self.estado = estado
        self.mover = mover or MoverPersonagemUseCase()
        self.world_context = world_context
        self.tempo = 0.0
        self.proxima_acao = random.uniform(3, 8)
        self.velocidade = 48
        self.personagem = None
        self._frames_sem_deslocamento = 0

    def _definir_animacao(self, nome, flip=None):
        animacoes = getattr(self.personagem, "animacoes", None)
        if animacoes is None:
            return
        definir = getattr(animacoes, "definir", None)
        if callable(definir):
            if flip is None:
                flip = getattr(animacoes, "flip", False)
            definir(nome, flip=flip)
            return
        # Compatibilidade com controladores antigos.
        sufixo = "_flip" if flip else ""
        animacoes.definir(f"{nome}{sufixo}")

    def iniciar(self, personagem, destino_x, destino_y):
        self.personagem = personagem
        personagem.destino_x = destino_x
        personagem.destino_y = destino_y
        self.personagem.animacoes.definir_por_direcao(
            "correndo", destino_x - personagem.x
        )
        self.tempo = 0

    def parar(self, personagem):
        personagem.destino_x = personagem.x
        personagem.destino_y = personagem.y
        self.personagem = personagem
        self._definir_animacao("ocioso")

    def executar(self, dt, personagem):
        self.personagem = personagem

        # A movimentação autônoma não depende mais de uma máquina de estado
        # legada. O próprio destino é a fonte de verdade: se há distância
        # suficiente até o destino, este comportamento precisa mover a entidade.
        distancia_ao_destino = (
            (personagem.destino_x - personagem.x) ** 2
            + (personagem.destino_y - personagem.y) ** 2
        ) ** 0.5

        if distancia_ao_destino > 2.0:
            x_anterior, y_anterior = personagem.x, personagem.y
            moveu = self.mover.executar(
                personagem=personagem,
                navegacao=self.navegacao,
                velocidade=self.velocidade,
                dt=dt,
                animacao_correndo="correndo",
                animacao_parado="ocioso",
            )
            deslocamento_real = (
                (personagem.x - x_anterior) ** 2 + (personagem.y - y_anterior) ** 2
            ) ** 0.5

            if moveu and deslocamento_real > 0.0001:
                self._frames_sem_deslocamento = 0
            else:
                self._frames_sem_deslocamento += 1
                # O movimento já informou que não houve progresso real. Não
                # mantenha a apresentação em "correndo" enquanto a IA tenta
                # decidir o próximo destino.
                self._definir_animacao("ocioso")

            if self._frames_sem_deslocamento >= 3:
                # Não deixe uma animação de corrida permanecer ativa quando
                # a navegação deixou de produzir deslocamento real. Isso vale
                # apenas para a IA autônoma; missões e combate não passam por
                # este mecanismo de recuperação.
                cancelar = getattr(self.mover, "cancelar_rota", None)
                if callable(cancelar):
                    cancelar(personagem)
                personagem.animacoes.definir("ocioso", flip=personagem.animacoes.flip)
                self._frames_sem_deslocamento = 0
                self.tempo = self.proxima_acao
            elif not moveu:
                self.tempo = 0
                self.proxima_acao = random.uniform(3, 8)
            return

        self.tempo += dt
        if self.tempo < self.proxima_acao:
            return

        self.tempo = 0
        self.proxima_acao = random.uniform(3, 8)
        self._escolher_proxima_acao()

    def _escolher_proxima_acao(self):
        nome_estado = self.personagem.animacoes.nome_animacao_atual
        world_context = (
            getattr(self.personagem, "world_context", None) or self.world_context
        )
        atividade_mundo = getattr(
            getattr(world_context, "state", None),
            "atividade",
            1.0,
        )
        politica = (
            world_context.politica_local(self.personagem.x, self.personagem.y)
            if world_context
            else {}
        )
        risco = politica.get("risco", "baixo")
        papel = politica.get("papel", "generica")
        chance = 0.35 * atividade_mundo
        if risco == "medio_alto":
            chance *= 0.78
        if papel in {"coleta_recorrente", "nucleo_social_fauna"}:
            chance *= 1.15
        correr = random.random() < min(0.85, chance)

        if nome_estado != "ocioso":
            return

        if correr:
            destino = (
                world_context.ponto_autonomo(
                    self.personagem,
                    40,
                    self.personagem.raio_movimento_livre,
                )
                if world_context is not None
                else None
            )
            if destino is None:
                destino = self.navegacao.ponto_aleatorio_no_raio(
                    self.personagem.base_x,
                    self.personagem.base_y,
                    self.personagem.altura,
                    40,
                    self.personagem.raio_movimento_livre,
                )
            if destino is None:
                self._definir_animacao("ocioso")
                return

            self.personagem.destino_x, self.personagem.destino_y = destino
            self.personagem.animacoes.definir_por_direcao(
                "correndo", destino[0] - self.personagem.x
            )
        else:
            self._definir_animacao("ocioso")


class ControlarComportamentoOvelhaUseCase(ControlarComportamentoUseCase):
    """Variação da ovelha, que possui comportamento de alimentação."""

    def __init__(self, navegacao, mover=None, world_context=None):
        super().__init__(navegacao, mover=mover, world_context=world_context)

    def _escolher_proxima_acao(self):
        estado = self.personagem.animacoes.nome_animacao_atual
        acao = random.random()
        world_context = (
            getattr(self.personagem, "world_context", None) or self.world_context
        )
        world_state = getattr(world_context, "state", None)
        if world_state is not None:
            # Fauna responde ao estado persistente do mundo.
            if world_state.fase.value == "noite":
                self.personagem.animacoes.definir(
                    "ocioso_flip" if self.personagem.animacoes.flip else "ocioso"
                )
                return
            if world_state.clima.value == "seca" and acao < 0.35:
                destino = (
                    world_context.ponto_autonomo(
                        self.personagem,
                        60,
                        min(180, self.personagem.raio_movimento_livre),
                    )
                    if world_context
                    else None
                )
                if destino:
                    self.personagem.destino_x, self.personagem.destino_y = destino
                    self.personagem.animacoes.definir_por_direcao(
                        "correndo",
                        destino[0] - self.personagem.x,
                    )
                    return

        estado_base = estado.replace("_flip", "")
        if estado_base in ("ocioso", "comendo"):
            if acao < 0.70:
                self.personagem.animacoes.definir(
                    "comendo",
                    flip=self.personagem.animacoes.flip,
                )
            elif acao < 0.90:
                self.personagem.destino_x, self.personagem.destino_y = (
                    self.navegacao.ponto_aleatorio_no_raio(
                        self.personagem.x,
                        self.personagem.y,
                        self.personagem.altura,
                        40,
                        180,
                    )
                )
                self.personagem.animacoes.definir_por_direcao(
                    "correndo",
                    self.personagem.destino_x - self.personagem.x,
                )
            else:
                self.personagem.animacoes.definir(
                    "ocioso",
                    flip=self.personagem.animacoes.flip,
                )
            return
