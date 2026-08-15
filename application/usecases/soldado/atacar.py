from application.usecases.personagem.atacar import (
    AtacarPersonagemUseCase,
)
from domains.personagem.maquina_estado_soldado import (
    EstadoSoldado,
)


class AtacarSoldadoUseCase(AtacarPersonagemUseCase):
    def __init__(self, cenario_principal):
        super().__init__(cenario_principal)
        self.segundo_golpe = False

    def iniciar(self, personagemalvo, personagem):
        estado_atual = personagem.animacoes.estado

        if estado_atual in (
            EstadoSoldado.ATACANDO1,
            EstadoSoldado.ATACANDO1_FLIP,
        ):
            self.segundo_golpe = False

        elif estado_atual in (
            EstadoSoldado.ATACANDO2,
            EstadoSoldado.ATACANDO2_FLIP,
        ):
            self.segundo_golpe = True

        else:
            self.segundo_golpe = False

        # Toda a gestão de alvo, ordem de ataque e prioridade fica na classe
        # base. Isso é importante para o soldado não quebrar as regras de foco.
        super().iniciar(personagemalvo, personagem)

    def _iniciar_ataque(self):
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

    def _apos_causar_dano(self):
        self.segundo_golpe = not self.segundo_golpe
        self._iniciar_ataque()

    def _animacao_correndo(self):
        if self.flip:
            self.personagem.animacoes.estado = EstadoSoldado.CORRENDO_FLIP
        else:
            self.personagem.animacoes.estado = EstadoSoldado.CORRENDO

    def _animacao_ocioso(self):
        if self.flip:
            self.personagem.animacoes.estado = EstadoSoldado.OCIOSO_FLIP
        else:
            self.personagem.animacoes.estado = EstadoSoldado.OCIOSO

    def _estado_correndo(self):
        return EstadoSoldado.CORRENDO

    def _estado_correndo_flip(self):
        return EstadoSoldado.CORRENDO_FLIP

    def _estado_ocioso(self):
        return EstadoSoldado.OCIOSO

    def _estado_ocioso_flip(self):
        return EstadoSoldado.OCIOSO_FLIP
