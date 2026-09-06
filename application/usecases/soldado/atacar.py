from application.usecases.personagem.atacar import (
    AtacarPersonagemUseCase,
)


class AtacarSoldadoUseCase(AtacarPersonagemUseCase):
    def __init__(self, cenario_principal):
        super().__init__(cenario_principal)
        self.segundo_golpe = False

    def iniciar(self, personagemalvo, personagem, manual=False):
        if personagem.animacoes.esta_em("atacando1"):
            self.segundo_golpe = False
        elif personagem.animacoes.esta_em("atacando2"):
            self.segundo_golpe = True
        else:
            self.segundo_golpe = False

        super().iniciar(personagemalvo, personagem, manual=manual)

    def _iniciar_ataque(self):
        self.flip = self.personagem.animacoes.flip_para_direcao(
            self.entidade_alvo.x - self.personagem.x
        )

        if self.flip:
            self.personagem.animacoes.definir(
                "atacando2_flip" if self.segundo_golpe else "atacando1_flip"
            )
        else:
            self.personagem.animacoes.definir(
                "atacando2" if self.segundo_golpe else "atacando1"
            )

    def _apos_causar_dano(self):
        self.segundo_golpe = not self.segundo_golpe
        self._iniciar_ataque()

    def _animacao_correndo(self):
        if self.flip:
            self.personagem.animacoes.definir("correndo_flip")
        else:
            self.personagem.animacoes.definir("correndo")

    def _animacao_ocioso(self):
        if self.flip:
            self.personagem.animacoes.definir("ocioso_flip")
        else:
            self.personagem.animacoes.definir("ocioso")

    def _estado_correndo(self):
        return "correndo"

    def _estado_correndo_flip(self):
        return "correndo_flip"

    def _estado_ocioso(self):
        return "ocioso"

    def _estado_ocioso_flip(self):
        return "ocioso_flip"
