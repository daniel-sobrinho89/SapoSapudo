from enum import Enum

from domains.sapudo.maquina_estado_sapo import StateMachine


class EstadoConstrucao(Enum):
    OCIOSO = "ocioso"


class MaquinaEstadoConstrucao(StateMachine):
    def __init__(self):
        super().__init__(EstadoConstrucao.OCIOSO)
