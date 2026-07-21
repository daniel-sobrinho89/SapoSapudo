from enum import Enum

from core.animacao import Animacao
from domains.sapudo.maquina_estado_sapo import StateMachine


class EstadoRecurso(Enum):
    OCIOSO = "ocioso"


class MaquinaEstadoRecurso(StateMachine):
    def __init__(self):
        super().__init__(EstadoRecurso.OCIOSO)


class AnimacoesRecurso:
    def __init__(self, total_frames_recurso):
        self.maquina = MaquinaEstadoRecurso()
        self.ocioso = Animacao(total_frames_recurso, 0.45)

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
        self.ocioso.atualizar(dt) if self.maquina.eh(EstadoRecurso.OCIOSO) else None

    def obter_selecao_frame(self):
        return "ocioso", self.ocioso.frame
