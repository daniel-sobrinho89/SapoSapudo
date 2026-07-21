from enum import Enum

from domains.sapudo.maquina_estado_sapo import StateMachine


class EstadoOuro(Enum):
    OCIOSO = "ocioso"
    NIVEL_OURO5 = "nivel_ouro5"
    NIVEL_OURO4 = "nivel_ouro4"
    NIVEL_OURO3 = "nivel_ouro3"
    NIVEL_OURO2 = "nivel_ouro2"
    NIVEL_OURO1 = "nivel_ouro1"
    OBTIDO = "obtido"


class MaquinaEstadoOuro(StateMachine):
    def __init__(self):
        super().__init__(EstadoOuro.OCIOSO)
