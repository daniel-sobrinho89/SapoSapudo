from core.animacao import Animacao
from domains.ovelha.maquina_estado import EstadoOvelha, MaquinaEstadoOvelha


class AnimacoesOvelha:
    def __init__(self):
        self.maquina = MaquinaEstadoOvelha()
        self.ocioso = Animacao(6, 0.20)
        self.ocioso_flip = Animacao(6, 0.20)
        self.comendo = Animacao(12, 0.35)
        self.comendo_flip = Animacao(12, 0.35)
        self.correndo = Animacao(4, 0.15)
        self.correndo_flip = Animacao(4, 0.15)

    @property
    def estado(self):
        return self.maquina.estado

    @estado.setter
    def estado(self, valor):
        self.maquina.trocar(valor)

    # ====================================
    # UPDATE
    # ====================================

    def atualizar(self, dt):
        self.maquina.atualizar(dt)
        self._atualizar_animacoes(dt)

    def _atualizar_animacoes(self, dt):
        self.ocioso.atualizar(dt) if self.maquina.eh(EstadoOvelha.OCIOSO) else None
        self.ocioso_flip.atualizar(dt) if self.maquina.eh(
            EstadoOvelha.OCIOSO_FLIP
        ) else None
        self.comendo.atualizar(dt) if self.maquina.eh(EstadoOvelha.COMENDO) else None
        self.comendo_flip.atualizar(dt) if self.maquina.eh(
            EstadoOvelha.COMENDO_FLIP
        ) else None
        self.correndo.atualizar(dt) if self.maquina.eh(EstadoOvelha.CORRENDO) else None
        self.correndo_flip.atualizar(dt) if self.maquina.eh(
            EstadoOvelha.CORRENDO_FLIP
        ) else None

    def obter_selecao_frame(self):
        if self.maquina.eh(EstadoOvelha.OCIOSO_FLIP):
            return "ocioso_flip", self.ocioso_flip.frame
        if self.maquina.eh(EstadoOvelha.COMENDO):
            return "comendo", self.comendo.frame
        if self.maquina.eh(EstadoOvelha.COMENDO_FLIP):
            return "comendo_flip", self.comendo_flip.frame
        if self.maquina.eh(EstadoOvelha.CORRENDO):
            return "correndo", self.correndo.frame
        if self.maquina.eh(EstadoOvelha.CORRENDO_FLIP):
            return "correndo_flip", self.correndo_flip.frame

        return "ocioso", self.ocioso.frame
