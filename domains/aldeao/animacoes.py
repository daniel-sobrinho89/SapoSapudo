from core.animacao import Animacao
from domains.aldeao.maquina_estado import EstadoAldeao, MaquinaEstadoAldeao


class AnimacoesAldeao:
    def __init__(self):
        self.maquina = MaquinaEstadoAldeao()
        self.ocioso = Animacao(8, 0.20)
        self.ocioso_flip = Animacao(8, 0.20)
        self.ocioso_madeira = Animacao(8, 0.15)
        self.ocioso_madeira_flip = Animacao(8, 0.15)
        self.correndo = Animacao(6, 0.15)
        self.correndo_flip = Animacao(6, 0.15)
        self.correndo_machado = Animacao(6, 0.15)
        self.correndo_machado_flip = Animacao(6, 0.15)
        self.correndo_madeira = Animacao(6, 0.15)
        self.correndo_madeira_flip = Animacao(6, 0.15)
        self.usando_machado = Animacao(6, 0.15)
        self.usando_machado_flip = Animacao(6, 0.15)
        self.correndo_picareta = Animacao(6, 0.15)
        self.correndo_picareta_flip = Animacao(6, 0.15)
        self.usando_picareta = Animacao(6, 0.15)
        self.usando_picareta_flip = Animacao(6, 0.15)
        self.correndo_ouro = Animacao(6, 0.15)
        self.correndo_ouro_flip = Animacao(6, 0.15)

    @property
    def estado(self):
        return self.maquina.estado

    @estado.setter
    def estado(self, valor):
        self.maquina.trocar(valor)

    def iniciar_ocioso(self, _evento=None):
        self.ocioso.reset()
        self.maquina.trocar(EstadoAldeao.OCIOSO)

    def iniciar_ocioso_madeira(self, _evento=None):
        self.ocioso_madeira.reset()
        self.maquina.trocar(EstadoAldeao.OCIOSO_MADEIRA)

    # ====================================
    # UPDATE
    # ====================================

    def atualizar(self, dt):
        self.maquina.atualizar(dt)
        self._atualizar_animacoes(dt)

    def _atualizar_animacoes(self, dt):
        self.ocioso.atualizar(dt) if self.maquina.eh(EstadoAldeao.OCIOSO) else None
        self.ocioso_flip.atualizar(dt) if self.maquina.eh(
            EstadoAldeao.OCIOSO_FLIP
        ) else None
        self.ocioso_madeira.atualizar(dt) if self.maquina.eh(
            EstadoAldeao.OCIOSO_MADEIRA
        ) else None
        self.ocioso_madeira_flip.atualizar(dt) if self.maquina.eh(
            EstadoAldeao.OCIOSO_MADEIRA_FLIP
        ) else None
        self.correndo.atualizar(dt) if self.maquina.eh(EstadoAldeao.CORRENDO) else None
        self.correndo_flip.atualizar(dt) if self.maquina.eh(
            EstadoAldeao.CORRENDO_FLIP
        ) else None
        self.correndo_machado.atualizar(dt) if self.maquina.eh(
            EstadoAldeao.CORRENDO_MACHADO
        ) else None
        self.correndo_machado_flip.atualizar(dt) if self.maquina.eh(
            EstadoAldeao.CORRENDO_MACHADO_FLIP
        ) else None
        self.correndo_madeira.atualizar(dt) if self.maquina.eh(
            EstadoAldeao.CORRENDO_MADEIRA
        ) else None
        self.correndo_madeira_flip.atualizar(dt) if self.maquina.eh(
            EstadoAldeao.CORRENDO_MADEIRA_FLIP
        ) else None
        self.usando_machado.atualizar(dt) if self.maquina.eh(
            EstadoAldeao.USANDO_MACHADO
        ) else None
        self.usando_machado_flip.atualizar(dt) if self.maquina.eh(
            EstadoAldeao.USANDO_MACHADO_FLIP
        ) else None
        self.correndo_picareta.atualizar(dt) if self.maquina.eh(
            EstadoAldeao.CORRENDO_PICARETA
        ) else None
        self.correndo_picareta_flip.atualizar(dt) if self.maquina.eh(
            EstadoAldeao.CORRENDO_PICARETA_FLIP
        ) else None
        self.usando_picareta.atualizar(dt) if self.maquina.eh(
            EstadoAldeao.USANDO_PICARETA
        ) else None
        self.usando_picareta_flip.atualizar(dt) if self.maquina.eh(
            EstadoAldeao.USANDO_PICARETA_FLIP
        ) else None
        self.correndo_ouro.atualizar(dt) if self.maquina.eh(
            EstadoAldeao.CORRENDO_OURO
        ) else None
        self.correndo_ouro_flip.atualizar(dt) if self.maquina.eh(
            EstadoAldeao.CORRENDO_OURO_FLIP
        ) else None

    def obter_selecao_frame(self):
        if self.maquina.eh(EstadoAldeao.OCIOSO_FLIP):
            return "ocioso_flip", self.ocioso_flip.frame
        if self.maquina.eh(EstadoAldeao.OCIOSO_MADEIRA):
            return "ocioso_madeira", self.ocioso_madeira.frame
        if self.maquina.eh(EstadoAldeao.OCIOSO_MADEIRA_FLIP):
            return "ocioso_madeira_flip", self.ocioso_madeira_flip.frame
        if self.maquina.eh(EstadoAldeao.CORRENDO):
            return "correndo", self.correndo.frame
        if self.maquina.eh(EstadoAldeao.CORRENDO_FLIP):
            return "correndo_flip", self.correndo_flip.frame
        if self.maquina.eh(EstadoAldeao.CORRENDO_MACHADO):
            return "correndo_machado", self.correndo_machado.frame
        if self.maquina.eh(EstadoAldeao.CORRENDO_MACHADO_FLIP):
            return "correndo_machado_flip", self.correndo_machado_flip.frame
        if self.maquina.eh(EstadoAldeao.CORRENDO_MADEIRA):
            return "correndo_madeira", self.correndo_madeira.frame
        if self.maquina.eh(EstadoAldeao.CORRENDO_MADEIRA_FLIP):
            return "correndo_madeira_flip", self.correndo_madeira_flip.frame
        if self.maquina.eh(EstadoAldeao.USANDO_MACHADO):
            return "usando_machado", self.usando_machado.frame
        if self.maquina.eh(EstadoAldeao.USANDO_MACHADO_FLIP):
            return "usando_machado_flip", self.usando_machado_flip.frame
        if self.maquina.eh(EstadoAldeao.CORRENDO_PICARETA):
            return "correndo_picareta", self.correndo_picareta.frame
        if self.maquina.eh(EstadoAldeao.CORRENDO_PICARETA_FLIP):
            return "correndo_picareta_flip", self.correndo_picareta_flip.frame
        if self.maquina.eh(EstadoAldeao.USANDO_PICARETA):
            return "usando_picareta", self.usando_picareta.frame
        if self.maquina.eh(EstadoAldeao.USANDO_PICARETA_FLIP):
            return "usando_picareta_flip", self.usando_picareta_flip.frame
        if self.maquina.eh(EstadoAldeao.CORRENDO_OURO):
            return "correndo_ouro", self.correndo_ouro.frame
        if self.maquina.eh(EstadoAldeao.CORRENDO_OURO_FLIP):
            return "correndo_ouro_flip", self.correndo_ouro_flip.frame

        return "ocioso", self.ocioso.frame
