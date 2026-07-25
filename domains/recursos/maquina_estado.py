from enum import Enum

from domains.sapudo.maquina_estado_sapo import StateMachine


class EstadoRecurso(Enum):
    OCIOSO = "ocioso"


class MaquinaEstadoRecurso(StateMachine):
    def __init__(self):
        super().__init__(EstadoRecurso.OCIOSO)
