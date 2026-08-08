from enum import Enum

from domains.sapudo.maquina_estado_sapo import StateMachine


class EstadoSapudo(Enum):
    OCIOSO = "ocioso"
    OCIOSO_FLIP = "ocioso_flip"
    CORRENDO = "correndo"
    CORRENDO_FLIP = "correndo_flip"


class MaquinaEstadoSapudo(StateMachine):
    def __init__(self):
        super().__init__(EstadoSapudo.OCIOSO)

    @property
    def flip(self):
        return self.estado.name.endswith("_FLIP")

    def carregando_recuso(self):
        return False
