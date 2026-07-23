from enum import Enum

from domains.sapudo.maquina_estado_sapo import StateMachine


class EstadoConstrucao(Enum):
    OCIOSO = "ocioso"
    OCIOSO_FLIP = "ocioso_flip"
    OCIOSO_MADEIRA = "ocioso_madeira"
    OCIOSO_MADEIRA_FLIP = "ocioso_madeira_flip"


class MaquinaEstadoConstrucao(StateMachine):
    def __init__(self):
        super().__init__(EstadoConstrucao.OCIOSO)
