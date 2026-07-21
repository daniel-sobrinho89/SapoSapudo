from core.animacao import Animacao
from domains.ouro.maquina_estado import EstadoOuro, MaquinaEstadoOuro


class AnimacoesOuro:
    def __init__(self):
        self.maquina = MaquinaEstadoOuro()
        self.ocioso = Animacao(6, 0.45)
        self.nivel_ouro5 = Animacao(6, 0.45)
        self.nivel_ouro4 = Animacao(6, 0.45)
        self.nivel_ouro3 = Animacao(6, 0.45)
        self.nivel_ouro2 = Animacao(6, 0.45)
        self.nivel_ouro1 = Animacao(6, 0.45)

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
        self.ocioso.atualizar(dt) if self.maquina.eh(EstadoOuro.OCIOSO) else None
        self.nivel_ouro5.atualizar(dt) if self.maquina.eh(
            EstadoOuro.NIVEL_OURO5
        ) else None
        self.nivel_ouro4.atualizar(dt) if self.maquina.eh(
            EstadoOuro.NIVEL_OURO4
        ) else None
        self.nivel_ouro3.atualizar(dt) if self.maquina.eh(
            EstadoOuro.NIVEL_OURO3
        ) else None
        self.nivel_ouro2.atualizar(dt) if self.maquina.eh(
            EstadoOuro.NIVEL_OURO2
        ) else None
        self.nivel_ouro1.atualizar(dt) if self.maquina.eh(
            EstadoOuro.NIVEL_OURO1
        ) else None

    def obter_selecao_frame(self):
        if self.maquina.eh(EstadoOuro.NIVEL_OURO5):
            return "nivel_ouro5", self.nivel_ouro5.frame
        elif self.maquina.eh(EstadoOuro.NIVEL_OURO4):
            return "nivel_ouro4", self.nivel_ouro4.frame
        elif self.maquina.eh(EstadoOuro.NIVEL_OURO3):
            return "nivel_ouro3", self.nivel_ouro3.frame
        elif self.maquina.eh(EstadoOuro.NIVEL_OURO2):
            return "nivel_ouro2", self.nivel_ouro2.frame
        elif self.maquina.eh(EstadoOuro.NIVEL_OURO1):
            return "nivel_ouro1", self.nivel_ouro1.frame

        return "ocioso", self.ocioso.frame
