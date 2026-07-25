from core.animacao import AnimacaoMovimento
from core.event_bus import event_bus
from domains.sapudo.maquina_estado_sapo import EstadoSapo, MaquinaEstadoSapo


class Animacoes:
    def __init__(self):
        # ====================================
        # COMPONENTES DE COMPORTAMENTO
        # ====================================
        self.maquina = MaquinaEstadoSapo()

        # ====================================
        # CONTROLE TROCA DE FRAMES
        # ====================================
        self.parado = AnimacaoMovimento(60, 0.15)
        self.dormir = AnimacaoMovimento(60, 0.15, loop=False)
        self.dormindo = AnimacaoMovimento(9, 0.50)
        self.acordar = AnimacaoMovimento(60, 0.15, loop=False)
        self.andar_esquerda = AnimacaoMovimento(10, 0.07)
        self.andar_direita = AnimacaoMovimento(10, 0.07)
        self.conversar = AnimacaoMovimento(60, 0.17)

        self.ultimo_frame_guardar = -1

        event_bus.assinar("tts_iniciado", self.fala_iniciada)
        event_bus.assinar("tts_finalizado", self.fala_finalizada)

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
        self.andar_esquerda.atualizar(dt) if self.maquina.eh(
            EstadoSapo.ANDANDO_ESQUERDA
        ) else None
        self.andar_direita.atualizar(dt) if self.maquina.eh(
            EstadoSapo.ANDANDO_DIREITA
        ) else None
        self.conversar.atualizar(dt) if self.maquina.eh(EstadoSapo.CONVERSAR) else None
        self.parado.atualizar(dt) if self.maquina.eh(EstadoSapo.PARADO) else None
        self.dormindo.atualizar(dt) if self.maquina.eh(EstadoSapo.DORMINDO) else None

    def obter_selecao_frame(self):
        if self.maquina.eh(EstadoSapo.ADORMECENDO):
            return "dormir", self.dormir.frame
        if self.maquina.eh(EstadoSapo.DORMINDO):
            return "dormindo", self.dormindo.frame
        if self.maquina.eh(EstadoSapo.ACORDANDO):
            return "acordar", self.acordar.frame
        if self.maquina.eh(EstadoSapo.ANDANDO_ESQUERDA):
            return "andar_esquerda", self.andar_esquerda.frame
        if self.maquina.eh(EstadoSapo.ANDANDO_DIREITA):
            return "andar_direita", self.andar_direita.frame
        if self.maquina.eh(EstadoSapo.CONVERSAR):
            return "conversar", self.conversar.frame

        return "parado", self.parado.frame

    def iniciar_dormir(self):
        self.dormir.reset()
        self.maquina.trocar(EstadoSapo.ADORMECENDO)

    def iniciar_acordar(self):
        self.acordar.reset()
        self.maquina.trocar(EstadoSapo.ACORDANDO)

    def iniciar_andar_esquerda(self):
        if self.maquina.eh(EstadoSapo.ANDANDO_ESQUERDA):
            return
        self.maquina.trocar(EstadoSapo.ANDANDO_ESQUERDA)
        self.andar_esquerda.reset()

    def iniciar_andar_direita(self):
        if self.maquina.eh(EstadoSapo.ANDANDO_DIREITA):
            return
        self.maquina.trocar(EstadoSapo.ANDANDO_DIREITA)
        self.andar_direita.reset()

    def fala_iniciada(self, _evento=None):
        if self.maquina.eh(EstadoSapo.PARADO):
            self.maquina.trocar(EstadoSapo.CONVERSAR)

    def fala_finalizada(self, _evento=None):
        if self.maquina.eh(EstadoSapo.CONVERSAR):
            self.maquina.trocar(EstadoSapo.PARADO)
