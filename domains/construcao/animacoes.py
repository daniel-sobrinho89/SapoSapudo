from core.animacao import Animacao
from domains.construcao.maquina_estado import EstadoConstrucao, MaquinaEstadoConstrucao


class AnimacoesConstrucao:
    def __init__(self):
        self.maquina = MaquinaEstadoConstrucao()
        self.ocioso = Animacao(1, 0.20)
        self.ocioso_flip = Animacao(1, 0.20)
        self.ocioso_madeira = Animacao(1, 0.15)
        self.ocioso_madeira_flip = Animacao(1, 0.15)

    @property
    def estado(self):
        return self.maquina.estado

    @estado.setter
    def estado(self, valor):
        self.maquina.trocar(valor)

    def iniciar_ocioso(self, _evento=None):
        self.ocioso.reset()
        self.maquina.trocar(EstadoConstrucao.OCIOSO)

    # ====================================
    # UPDATE
    # ====================================

    def atualizar(self, dt):
        self.maquina.atualizar(dt)
        self._atualizar_animacoes(dt)

    def _atualizar_animacoes(self, dt):
        self.ocioso.atualizar(dt) if self.maquina.eh(EstadoConstrucao.OCIOSO) else None
        self.ocioso_flip.atualizar(dt) if self.maquina.eh(
            EstadoConstrucao.OCIOSO_FLIP
        ) else None
        self.ocioso_madeira.atualizar(dt) if self.maquina.eh(
            EstadoConstrucao.OCIOSO_MADEIRA
        ) else None
        self.ocioso_madeira_flip.atualizar(dt) if self.maquina.eh(
            EstadoConstrucao.OCIOSO_MADEIRA_FLIP
        ) else None

    def obter_selecao_frame(self):
        if self.maquina.eh(EstadoConstrucao.OCIOSO_FLIP):
            return "ocioso_flip", self.ocioso_flip.frame
        if self.maquina.eh(EstadoConstrucao.OCIOSO_MADEIRA):
            return "ocioso_madeira", self.ocioso_madeira.frame
        if self.maquina.eh(EstadoConstrucao.OCIOSO_MADEIRA_FLIP):
            return "ocioso_madeira_flip", self.ocioso_madeira_flip.frame

        return "ocioso", self.ocioso.frame
