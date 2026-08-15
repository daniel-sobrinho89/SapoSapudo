from application.usecases.personagem.atacar import (
    AtacarPersonagemUseCase,
)
from domains.personagem.maquina_estado_goblin_tocha import (
    EstadoGoblinTocha,
)


class AtacarGoblinUseCase(AtacarPersonagemUseCase):
    def _iniciar_ataque(self):
        if self.flip:
            self.personagem.animacoes.estado = EstadoGoblinTocha.ATACANDO_FLIP
        else:
            self.personagem.animacoes.estado = EstadoGoblinTocha.ATACANDO

    def _animacao_correndo(self):
        if self.flip:
            self.personagem.animacoes.estado = EstadoGoblinTocha.CORRENDO_FLIP
        else:
            self.personagem.animacoes.estado = EstadoGoblinTocha.CORRENDO

    def _animacao_ocioso(self):
        if self.flip:
            self.personagem.animacoes.estado = EstadoGoblinTocha.OCIOSO_FLIP
        else:
            self.personagem.animacoes.estado = EstadoGoblinTocha.OCIOSO

    def _estado_correndo(self):
        return EstadoGoblinTocha.CORRENDO

    def _estado_correndo_flip(self):
        return EstadoGoblinTocha.CORRENDO_FLIP

    def _estado_ocioso(self):
        return EstadoGoblinTocha.OCIOSO

    def _estado_ocioso_flip(self):
        return EstadoGoblinTocha.OCIOSO_FLIP
