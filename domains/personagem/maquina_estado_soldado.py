from enum import Enum

from domains.sapudo.maquina_estado_sapo import StateMachine


class EstadoSoldado(Enum):
    OCIOSO = "ocioso"
    OCIOSO_FLIP = "ocioso_flip"
    CORRENDO = "correndo"
    CORRENDO_FLIP = "correndo_flip"
    ATACANDO1 = "atacando1"
    ATACANDO1_FLIP = "atacando1_flip"
    ATACANDO2 = "atacando2"
    ATACANDO2_FLIP = "atacando2_flip"
    DEFENDENDO = "defendendo"
    DEFENDENDO_FLIP = "defendendo_flip"


class MaquinaEstadoSoldado(StateMachine):
    def __init__(self):
        super().__init__(EstadoSoldado.OCIOSO)

    @property
    def flip(self):
        return self.estado.name.endswith("_FLIP")

    def carregando_recuso(self):
        return False

    def atacando(self):
        return self.em_estado(
            EstadoSoldado.ATACANDO1,
            EstadoSoldado.ATACANDO1_FLIP,
            EstadoSoldado.ATACANDO2,
            EstadoSoldado.ATACANDO2_FLIP,
        )

    def atacando_flip(self):
        return self.em_estado(
            EstadoSoldado.ATACANDO1_FLIP, EstadoSoldado.ATACANDO2_FLIP
        )
