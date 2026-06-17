from systems.sapudo.agenda_sapo import AgendaSapo
from systems.sapudo.logica_violao import LogicaViolaoSapo
from systems.sapudo.maquina_estado_sapo import EstadoSapo, MaquinaEstadoSapo


class AnimacoesSapo:
    """
    Motor técnico de animação e orquestrador de estados do Sapo.
    Delega regras de comportamento para AgendaSapo e LogicaViolaoSapo.
    """

    def __init__(self):
        # ====================================
        # COMPONENTES DE COMPORTAMENTO
        # ====================================
        self.maquina = MaquinaEstadoSapo()
        self.agenda = AgendaSapo()
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

        self.ultimo_frame_guardar = -1
        self.parar_audio_violao = False
        self.callback_verificar_spotify = None

    # ====================================
    # PROPRIEDADES DE COMPATIBILIDADE (LEGACY)
    # ====================================
    @property
    def horarios_caminhada(self):
        return self.agenda.horarios_caminhada

    @property
    def proxima_tentativa_caminhada(self):
        return self.agenda.proxima_tentativa_caminhada

    @proxima_tentativa_caminhada.setter
    def proxima_tentativa_caminhada(self, v):
        self.agenda.proxima_tentativa_caminhada = v

    @property
    def ultima_execucao_caminhada(self):
        return self.agenda.ultima_execucao_caminhada

    @ultima_execucao_caminhada.setter
    def ultima_execucao_caminhada(self, v):
        self.agenda.ultima_execucao_caminhada = v

    @property
    def iniciou_sono_hoje(self):
        return self.agenda.iniciou_sono_hoje

    @iniciou_sono_hoje.setter
    def iniciou_sono_hoje(self, v):
        self.agenda.iniciou_sono_hoje = v

    @property
    def executou_acordar_hoje(self):
        return self.agenda.executou_acordar_hoje

    @executou_acordar_hoje.setter
    def executou_acordar_hoje(self, v):
        self.agenda.executou_acordar_hoje = v

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
        self._atualizar_animations_tecnicas(dt)
        self._atualizar_fluxo_estado(dt)

    def _atualizar_animations_tecnicas(self, dt):
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
        self.parado.atualizar(dt) if self.maquina.eh(EstadoSapo.PARADO) else None
        self.dormindo.atualizar(dt) if self.maquina.eh(EstadoSapo.DORMINDO) else None

    def _atualizar_fluxo_estado(self, dt):
        m = self.maquina

        # ACORDANDO
        if m.eh(EstadoSapo.ACORDANDO):
            if self.acordar.atualizar(dt):
                m.trocar(EstadoSapo.PARADO)
            return

        # ADORMECENDO
        horario_sono = self.agenda.verificar_horario_sono()
        if m.eh(EstadoSapo.ADORMECENDO):
            if not horario_sono:
                self.iniciar_acordar()
                return
            if self.dormir.atualizar(dt):
                m.trocar(EstadoSapo.DORMINDO)
            return

        # CICLO DIÁRIO E RESETS
        self.agenda.atualizar_resets_diarios()

        if (
            not horario_sono
            and not self.agenda.executou_acordar_hoje
            and m.em_estado(EstadoSapo.DORMINDO, EstadoSapo.ADORMECENDO)
        ):
            self.iniciar_acordar()
            self.agenda.executou_acordar_hoje = True
            return

        if (
            horario_sono
            and not self.agenda.iniciou_sono_hoje
            and not m.em_estado(EstadoSapo.DORMINDO, EstadoSapo.ADORMECENDO)
        ):
            self.agenda.iniciou_sono_hoje = True
            self.iniciar_dormir()
            return

        # VIOLÃO (Delegado)
        if m.eh(EstadoSapo.PEGANDO_VIOLAO) and (
            self.pegar_violao.frame >= self.pegar_violao.total_frames - 1
        ):  # Checa se acabou
            m.trocar(EstadoSapo.TOCANDO_VIOLAO)
            self.violao_logic.resetar()

        if (
            m.eh(EstadoSapo.TOCANDO_VIOLAO)
            and self.violao_logic.atualizar_frames(dt) == "levantar"
        ):
            self.iniciar_levantar_violao()

        if (
            m.eh(EstadoSapo.LEVANTANDO_VIOLAO)
            and self.levantar_violao.frame >= self.levantar_violao.total_frames - 1
        ):
            spotify_tocando = (
                self.callback_verificar_spotify()
                if self.callback_verificar_spotify
                else False
            )
            if spotify_tocando:
                m.trocar(EstadoSapo.TOCANDO_VIOLAO)
                self.violao_logic.resetar()
            else:
                m.trocar(EstadoSapo.GUARDANDO_VIOLAO)
                self.guardar_violao.reset()
                self.ultimo_frame_guardar = -1

        if (
            m.eh(EstadoSapo.SOLTANDO_VIOLAO)
            and self.soltar_violao.frame >= self.soltar_violao.total_frames - 1
        ):
            m.trocar(EstadoSapo.PARADO)
            self.violao_logic.tempo_tocando = 0

    def iniciar_dormir(self):
        self.dormir.reset()
        self.maquina.trocar(EstadoSapo.ADORMECENDO)

    def iniciar_acordar(self):
        self.acordar.reset()
        self.maquina.trocar(EstadoSapo.ACORDANDO)

    def iniciar_violao(self):
        if self.maquina.em_estado(EstadoSapo.TOCANDO_VIOLAO, EstadoSapo.PEGANDO_VIOLAO):
            return
        self.maquina.trocar(EstadoSapo.PEGANDO_VIOLAO)
        self.pegar_violao.reset()
        self.violao_logic.resetar()

    def parar_violao(self):
        self.maquina.trocar(EstadoSapo.PARADO)
        self.violao_logic.resetar()

    def iniciar_levantar_violao(self):
        self.maquina.trocar(EstadoSapo.LEVANTANDO_VIOLAO)
        self.levantar_violao.reset()

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
