from enum import Enum


class EstadoSapo(Enum):
    PARADO = "parado"

    ADORMECENDO = "adormecendo"
    DORMINDO = "dormindo"
    ACORDANDO = "acordando"

    PEGANDO_VIOLAO = "pegando_violao"
    TOCANDO_VIOLAO = "tocando_violao"
    LEVANTANDO_VIOLAO = "levantando_violao"
    GUARDANDO_VIOLAO = "guardando_violao"
    CHEGOU_AO_VIOLAO = "chegou_ao_violao"
    SOLTANDO_VIOLAO = "soltando_violao"

    ANDANDO_ESQUERDA = "andando_esquerda"
    ANDANDO_DIREITA = "andando_direita"
    CONVERSAR = "conversar"


class MaquinaEstadoSapo:
    def __init__(self):
        self.estado = EstadoSapo.PARADO

    def trocar(self, novo_estado):
        self.estado = novo_estado

    def eh(self, estado):
        return self.estado == estado

    def em_estado(self, *estados):
        return self.estado in estados

    def esta_com_violao(self):
        return self.em_estado(
            EstadoSapo.CHEGOU_AO_VIOLAO,
            EstadoSapo.PEGANDO_VIOLAO,
            EstadoSapo.TOCANDO_VIOLAO,
            EstadoSapo.LEVANTANDO_VIOLAO,
            EstadoSapo.GUARDANDO_VIOLAO,
            EstadoSapo.SOLTANDO_VIOLAO,
        )
