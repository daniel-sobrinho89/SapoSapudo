from application.usecases.personagem.atacar import AtacarPersonagemUseCase


class AtacarCobraUseCase(AtacarPersonagemUseCase):
    INTERVALO_APOS_GOLPE = 0.12

    def __init__(self, cenario_principal):
        super().__init__(cenario_principal)
        self.tempo_apos_golpe = 0.0

    def iniciar(self, personagemalvo, personagem, manual=False):
        super().iniciar(personagemalvo, personagem, manual=manual)
        self.tempo_apos_golpe = 0.0

    def executar(self, dt):
        if self.tempo_apos_golpe > 0.0:
            self.tempo_apos_golpe = max(0.0, self.tempo_apos_golpe - dt)
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

        super().executar(dt)

    def _apos_causar_dano(self):
        self.tempo_apos_golpe = self.INTERVALO_APOS_GOLPE
        self.posicao_alvo_no_inicio_ataque = None
        self.personagem.animacoes.reset()
