from core.animacao import Animacao
from core.event_bus import event_bus
from domains.casa_duende.maquina_estado import EstadoCasa, MaquinaEstadoCasaDuende


class AnimacoesCasaDuende:
    def __init__(self):
        self.maquina = MaquinaEstadoCasaDuende()
        self.inicial = Animacao(7, 0.15)
        self.abrir_janela = Animacao(9, 0.65, loop=False)
        self.luz_acesa = Animacao(4, 0.35)

        event_bus.assinar("voo_iniciado", self.iniciar_inicial)
        event_bus.assinar("descendo_para_dormir", self.iniciar_abrir_janela)

    @property
    def estado(self):
        return self.maquina.estado

    @estado.setter
    def estado(self, valor):
        self.maquina.trocar(valor)

    def iniciar_inicial(self, _evento=None):
        self.inicial.reset()
        self.maquina.trocar(EstadoCasa.INICIAL)

    def iniciar_abrir_janela(self, _evento=None):
        self.abrir_janela.reset()
        self.maquina.trocar(EstadoCasa.ABRIR_JANELA)

    def iniciar_luz_acesa(self):
        self.luz_acesa.reset()
        self.maquina.trocar(EstadoCasa.LUZ_ACESA)

    @property
    def luz_esta_acesa(self):
        return self.maquina.eh(EstadoCasa.LUZ_ACESA)

    # ====================================
    # UPDATE
    # ====================================

    def atualizar(self, dt):
        self.maquina.atualizar(dt)
        self._atualizar_animacoes(dt)

    def _atualizar_animacoes(self, dt):
        self.inicial.atualizar(dt) if self.maquina.eh(EstadoCasa.INICIAL) else None
        self.abrir_janela.atualizar(dt) if self.maquina.eh(
            EstadoCasa.ABRIR_JANELA
        ) else None
        self.luz_acesa.atualizar(dt) if self.maquina.eh(EstadoCasa.LUZ_ACESA) else None

    def obter_selecao_frame(self):
        if self.maquina.eh(EstadoCasa.LUZ_ACESA):
            return "luz_acesa", self.luz_acesa.frame
        if self.maquina.eh(EstadoCasa.ABRIR_JANELA):
            return "abrir_janela", self.abrir_janela.frame

        return "inicial", self.inicial.frame
