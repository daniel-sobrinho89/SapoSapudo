from core.animacao import Animacao
from domains.arvore.maquina_estado import EstadoArvore, MaquinaEstadoArvore


class AnimacoesArvore:
    def __init__(self):
        self.maquina = MaquinaEstadoArvore()
        self.ocioso = Animacao(8, 0.25)
        self.cortada = Animacao(1, 0.25)

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
        self.ocioso.atualizar(dt) if self.maquina.eh(EstadoArvore.OCIOSO) else None
        self.cortada.atualizar(dt) if self.maquina.eh(EstadoArvore.CORTADA) else None

    def obter_selecao_frame(self):
        if self.maquina.eh(EstadoArvore.CORTADA):
            return "cortada", self.cortada.frame

        return "ocioso", self.ocioso.frame
