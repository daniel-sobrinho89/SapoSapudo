from enum import Enum

from domains.sapudo.maquina_estado_sapo import StateMachine


class EstadoOvelha(Enum):
    OCIOSO = "ocioso"
    OCIOSO_FLIP = "ocioso_flip"
    COMENDO = "comendo"
    COMENDO_FLIP = "comendo_flip"
    CORRENDO = "correndo"
    CORRENDO_FLIP = "correndo_flip"
    OBTIDO = "obtido"


class MaquinaEstadoOvelha(StateMachine):
    def __init__(self):
        super().__init__(EstadoOvelha.OCIOSO)
