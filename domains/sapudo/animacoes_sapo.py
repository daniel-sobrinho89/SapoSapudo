from core.event_bus import event_bus
from domains.sapudo.maquina_estado_sapo import EstadoSapo, MaquinaEstadoSapo
from domains.violao.logic import LogicaViolaoSapo


class AnimacoesSapo:
    def __init__(self):
        # ====================================
        # COMPONENTES DE COMPORTAMENTO
        # ====================================
        self.maquina = MaquinaEstadoSapo()
        self.violao_logic = LogicaViolaoSapo()

        # ====================================
        # CONTROLE TROCA DE FRAMES
        # ====================================
        self.parado = Animacao(60, 0.15)
        self.dormir = Animacao(60, 0.15, loop=False)
        self.dormindo = Animacao(9, 0.50)
        self.acordar = Animacao(60, 0.15, loop=False)
        self.pegar_violao = Animacao(15, 0.16, loop=False)
        self.levantar_violao = Animacao(15, 0.14, loop=False)
        self.guardar_violao = Animacao(9, 0.14)
        self.soltar_violao = Animacao(9, 0.14, loop=False)
        self.andar_esquerda = Animacao(10, 0.07)
        self.andar_direita = Animacao(10, 0.07)
        self.conversar = Animacao(60, 0.17)
        self.pegar_livro = Animacao(20, 0.16, loop=False)
        self.lendo_livro = Animacao(40, 0.17)

        self.ultimo_frame_guardar = -1
        self.finalizou_soltar_violao = False

        event_bus.assinar("tts_iniciado", self.fala_iniciada)
        event_bus.assinar("tts_finalizado", self.fala_finalizada)

    @property
    def estado(self):
        return self.maquina.estado

    @estado.setter
    def estado(self, valor):
        self.maquina.trocar(valor)

    @property
    def frame_violao(self):
        return self.violao_logic.frame_atual

    @frame_violao.setter
    def frame_violao(self, v):
        self.violao_logic.frame_atual = v

    # ====================================
    # UPDATE
    # ====================================

    def atualizar(self, dt):
        self.maquina.atualizar(dt)
        self._atualizar_animacoes(dt)

    def _atualizar_animacoes(self, dt):
        self.pegar_violao.atualizar(dt) if self.maquina.eh(
            EstadoSapo.PEGANDO_VIOLAO
        ) else None
        self.levantar_violao.atualizar(dt) if self.maquina.eh(
            EstadoSapo.LEVANTANDO_VIOLAO
        ) else None
        self.guardar_violao.atualizar(dt) if self.maquina.eh(
            EstadoSapo.GUARDANDO_VIOLAO
        ) else None
        self.soltar_violao.atualizar(dt) if self.maquina.eh(
            EstadoSapo.SOLTANDO_VIOLAO
        ) else None
        self.andar_esquerda.atualizar(dt) if self.maquina.eh(
            EstadoSapo.ANDANDO_ESQUERDA
        ) else None
        self.andar_direita.atualizar(dt) if self.maquina.eh(
            EstadoSapo.ANDANDO_DIREITA
        ) else None
        self.conversar.atualizar(dt) if self.maquina.eh(EstadoSapo.CONVERSAR) else None
        self.parado.atualizar(dt) if self.maquina.eh(EstadoSapo.PARADO) else None
        self.dormindo.atualizar(dt) if self.maquina.eh(EstadoSapo.DORMINDO) else None
        self.pegar_livro.atualizar(dt) if self.maquina.eh(
            EstadoSapo.PEGANDO_LIVRO
        ) else None
        self.lendo_livro.atualizar(dt) if self.maquina.eh(
            EstadoSapo.LENDO_LIVRO
        ) else None

    def iniciar_dormir(self):
        self.dormir.reset()
        self.maquina.trocar(EstadoSapo.ADORMECENDO)

    def iniciar_acordar(self):
        self.acordar.reset()
        self.maquina.trocar(EstadoSapo.ACORDANDO)

    def parar_violao(self, _evento=None):
        self.maquina.trocar(EstadoSapo.PARADO)
        self.violao_logic.resetar()

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


class Animacao:
    def __init__(self, total_frames, intervalo, loop=True):
        self.frame = 0
        self.tempo = 0.0
        self.total_frames = total_frames
        self.intervalo = intervalo
        self.loop = loop

    def atualizar(self, dt):
        self.tempo += dt
        if self.tempo < self.intervalo:
            return False
        self.tempo -= self.intervalo
        self.frame += 1
        terminou = False
        if self.frame >= self.total_frames:
            terminou = True
            if self.loop:
                self.frame = 0
            else:
                self.frame = self.total_frames - 1
        return terminou

    def reset(self):
        self.frame = 0
        self.tempo = 0
