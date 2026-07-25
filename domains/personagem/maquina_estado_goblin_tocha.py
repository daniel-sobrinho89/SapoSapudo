from enum import Enum

from domains.sapudo.maquina_estado_sapo import StateMachine


class EstadoGoblinTocha(Enum):
    OCIOSO = "ocioso"
    OCIOSO_FLIP = "ocioso_flip"
    CORRENDO = "correndo"
    CORRENDO_FLIP = "correndo_flip"
    ATACANDO = "atacando"
    ATACANDO_FLIP = "atacando_flip"


class MaquinaEstadoGoblinTocha(StateMachine):
    def __init__(self):
        super().__init__(EstadoGoblinTocha.OCIOSO)

    def carregando_recuso(self):
        return False

    def atacando(self):
        return self.em_estado(
            EstadoGoblinTocha.ATACANDO, EstadoGoblinTocha.ATACANDO_FLIP
        )

    def atacando_flip(self):
        return self.em_estado(EstadoGoblinTocha.ATACANDO_FLIP)
