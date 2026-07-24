from enum import Enum

from domains.sapudo.maquina_estado_sapo import StateMachine


class EstadoSoldado(Enum):
    OCIOSO = "ocioso"
    OCIOSO_FLIP = "ocioso_flip"
    CORRENDO = "correndo"
    CORRENDO_FLIP = "correndo_flip"


class MaquinaEstadoSoldado(StateMachine):
    def __init__(self):
        super().__init__(EstadoSoldado.OCIOSO)

    def carregando_recuso(self):
        return False
