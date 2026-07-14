from enum import Enum

from domains.sapudo.maquina_estado_sapo import StateMachine


class EstadoCasa(Enum):
    INICIAL = "inicial"
    ABRIR_JANELA = "abrir_janela"
    LUZ_ACESA = "luz_acesa"


class MaquinaEstadoCasaDuende(StateMachine):
    def __init__(self):
        super().__init__(EstadoCasa.INICIAL)
