from enum import Enum

from domains.sapudo.maquina_estado_sapo import StateMachine


class EstadoArvore(Enum):
    OCIOSO = "ocioso"
    CORTADA = "cortada"


class MaquinaEstadoArvore(StateMachine):
    def __init__(self):
        super().__init__(EstadoArvore.OCIOSO)
