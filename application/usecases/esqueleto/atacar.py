import random

from application.usecases.personagem.atacar import AtacarPersonagemUseCase


class AtacarEsqueletoUseCase(AtacarPersonagemUseCase):
    DISTANCIA_PARADA = 82
    # Defesa deliberada durante o combate para que o comportamento seja
    # perceptível no jogo, além da defesa reativa ao receber um golpe.
    DEFESA_INTERVALO_MIN = 1.4
    DEFESA_INTERVALO_MAX = 2.8
    CHANCE_DEFESA_COMBATE = 0.65
    DURACAO_DEFESA = 0.85
    INTERVALO_APOS_GOLPE = 0.12

    def __init__(self, cenario_principal):
        super().__init__(cenario_principal)
        self.tempo_proxima_defesa = random.uniform(
            self.DEFESA_INTERVALO_MIN,
            self.DEFESA_INTERVALO_MAX,
        )
        self.tempo_apos_golpe = 0.0

    def iniciar(self, personagemalvo, personagem, manual=False):
        super().iniciar(personagemalvo, personagem, manual=manual)
        # Cada combate começa com um intervalo novo, evitando que todos os
        # esqueletos defendam exatamente no mesmo instante.
        self.tempo_proxima_defesa = random.uniform(
            self.DEFESA_INTERVALO_MIN,
            self.DEFESA_INTERVALO_MAX,
        )
        self.tempo_apos_golpe = 0.0

    def executar(self, dt):
        tempo_apos_golpe = getattr(self, "tempo_apos_golpe", 0.0)
        if tempo_apos_golpe > 0.0:
            self.tempo_apos_golpe = max(0.0, tempo_apos_golpe - dt)
            if self.personagem is None or self.entidade_alvo is None:
                return
            if self.tempo_apos_golpe <= 0.0:
                self.tempo = 0.0
                if self.entidade_alvo.vida > 0:
                    self.flip = self.personagem.animacoes.flip_para_direcao(
                        self.entidade_alvo.x - self.personagem.x
                    )
                    self.personagem.animacoes.reset()
                    self._iniciar_ataque()
                else:
                    self._finalizar_ataque()
            return
        personagem = self.personagem

        if (
            personagem is not None
            and self.entidade_alvo is not None
            and getattr(personagem, "nome", None) == "esqueleto"
        ):
            if personagem.defesa_ativa:
                return

            self.tempo_proxima_defesa = max(0.0, self.tempo_proxima_defesa - dt)

            if self.tempo_proxima_defesa <= 0.0:
                self.tempo_proxima_defesa = random.uniform(
                    self.DEFESA_INTERVALO_MIN,
                    self.DEFESA_INTERVALO_MAX,
                )

                # Defesa apenas durante combate parado, nunca durante patrulha.
                esta_atacando = (
                    self.personagem.animacoes.esta_em("atacando")
                    or self.personagem.animacoes.esta_em("atacando1")
                    or self.personagem.animacoes.esta_em("atacando2")
                )
                distancia = (
                    (self.entidade_alvo.x - self.personagem.x) ** 2
                    + (self.entidade_alvo.y - self.personagem.y) ** 2
                ) ** 0.5
                parada = distancia <= self.DISTANCIA_PARADA
                if (
                    esta_atacando
                    and parada
                    and random.random() < self.CHANCE_DEFESA_COMBATE
                ):
                    self._iniciar_defesa()
                    return

        super().executar(dt)

    def _iniciar_defesa(self):
        personagem = self.personagem
        if personagem is None:
            return

        personagem.defesa_ativa = True
        personagem.perfect_block = False
        personagem._ultima_defesa_esqueleto = True
        personagem._tempo_defesa_esqueleto = self.DURACAO_DEFESA
        personagem._cooldown_defesa_esqueleto = self.DURACAO_DEFESA

        personagem.animacoes.definir("defendendo_flip" if self.flip else "defendendo")

    def _apos_causar_dano(self):
        # O alvo continua no mesmo lugar de combate. Não saímos para CORRENDO
        # depois de cada golpe, pois isso criava o flip/pausa observado no
        # primeiro ataque. Após uma pequena recuperação, reiniciamos a
        # animação de ataque diretamente.
        self.tempo_apos_golpe = self.INTERVALO_APOS_GOLPE
        self.posicao_alvo_no_inicio_ataque = None
        self.personagem.animacoes.reset()

    def _iniciar_ataque(self):
        self.personagem.animacoes.definir("atacando_flip" if self.flip else "atacando")

    def _animacao_correndo(self):
        self.personagem.animacoes.definir("correndo_flip" if self.flip else "correndo")

    def _animacao_ocioso(self):
        self.personagem.animacoes.definir("ocioso")

    def _estado_correndo(self):
        return "correndo"

    def _estado_correndo_flip(self):
        return "correndo_flip"

    def _estado_ocioso(self):
        return "ocioso"

    def _estado_ocioso_flip(self):
        return "ocioso_flip"
