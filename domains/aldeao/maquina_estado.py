from enum import Enum

from domains.sapudo.maquina_estado_sapo import StateMachine


class EstadoAldeao(Enum):
    OCIOSO = "ocioso"
    OCIOSO_FLIP = "ocioso_flip"
    OCIOSO_MADEIRA = "ocioso_madeira"
    OCIOSO_MADEIRA_FLIP = "ocioso_madeira_flip"
    CORRENDO = "correndo"
    CORRENDO_FLIP = "correndo_flip"
    CORRENDO_MACHADO = "correndo_machado"
    CORRENDO_MACHADO_FLIP = "correndo_machado_flip"
    CORRENDO_MADEIRA = "correndo_madeira"
    CORRENDO_MADEIRA_FLIP = "correndo_madeira_flip"
    USANDO_MACHADO = "usando_machado"
    USANDO_MACHADO_FLIP = "usando_machado_flip"
    CORRENDO_PICARETA = "correndo_picareta"
    CORRENDO_PICARETA_FLIP = "correndo_picareta_flip"
    USANDO_PICARETA = "usando_picareta"
    USANDO_PICARETA_FLIP = "usando_picareta_flip"
    CORRENDO_OURO = "correndo_ouro"
    CORRENDO_OURO_FLIP = "correndo_ouro_flip"


class MaquinaEstadoAldeao(StateMachine):
    def __init__(self):
        super().__init__(EstadoAldeao.OCIOSO)

    def interagindo_arvore(self):
        return self.em_estado(
            EstadoAldeao.CORRENDO_MACHADO,
            EstadoAldeao.CORRENDO_MACHADO_FLIP,
            EstadoAldeao.USANDO_MACHADO,
            EstadoAldeao.USANDO_MACHADO_FLIP,
            EstadoAldeao.CORRENDO_MADEIRA,
            EstadoAldeao.CORRENDO_MADEIRA_FLIP,
        )

    def cortando_arvore(self):
        return self.em_estado(
            EstadoAldeao.USANDO_MACHADO,
            EstadoAldeao.USANDO_MACHADO_FLIP,
        )

    def entregando_madeira(self):
        return self.em_estado(
            EstadoAldeao.CORRENDO_MADEIRA,
            EstadoAldeao.CORRENDO_MADEIRA_FLIP,
        )

    def interagindo_ouro(self):
        return self.em_estado(
            EstadoAldeao.CORRENDO_PICARETA,
            EstadoAldeao.CORRENDO_PICARETA_FLIP,
            EstadoAldeao.USANDO_PICARETA,
            EstadoAldeao.USANDO_PICARETA_FLIP,
            EstadoAldeao.CORRENDO_OURO,
            EstadoAldeao.CORRENDO_OURO_FLIP,
        )

    def obtendo_ouro(self):
        return self.em_estado(
            EstadoAldeao.USANDO_PICARETA,
            EstadoAldeao.USANDO_PICARETA_FLIP,
        )

    def entregando_ouro(self):
        return self.em_estado(
            EstadoAldeao.CORRENDO_OURO,
            EstadoAldeao.CORRENDO_OURO_FLIP,
        )
