from datetime import datetime, timedelta

from domains.sapudo.agenda_sapo import AgendaSapo
from domains.sapudo.maquina_estado_sapo import EstadoSapo
from utils.input import LARGURA


class ControlarComportamentoSapoUseCase:
    # ==========================
    # ESTADOS
    # ==========================

    EXPLORANDO = "explorando"
    ORBITANDO = "orbitando"
    FUGINDO = "fugindo"

    def __init__(
        self,
        sapo,
        spotify,
        audio,
        clima_service=None,
        tts_service=None,
    ):
        self.sapo = sapo
        self.spotify = spotify
        self.audio = audio
        self.animacoes = sapo.animacoes
        self.agenda = AgendaSapo()
        self.clima_service = clima_service
        self.tts_service = tts_service
        self._estado_sapo_anterior = None

    def iniciar_controle_esquerda(self):
        if not self.sapo.pode_caminhar():
            return

        self.sapo.andando_manual = True
        self.sapo.controle_esquerda = True
        self.sapo.andar_iniciado_por_controle = True

        if not self.animacoes.maquina.eh(EstadoSapo.ANDANDO_ESQUERDA):
            self.animacoes.iniciar_andar_esquerda()

    def parar_controle_esquerda(self):
        self.sapo.andando_manual = False
        self.sapo.controle_esquerda = False
        if self.animacoes.maquina.eh(EstadoSapo.ANDANDO_ESQUERDA):
            self.animacoes.maquina.trocar(EstadoSapo.PARADO)

    def iniciar_controle_direita(self):
        if not self.sapo.pode_caminhar():
            return

        self.sapo.andando_manual = True
        self.sapo.controle_direita = True
        self.sapo.andar_iniciado_por_controle = True

        if not self.animacoes.maquina.eh(EstadoSapo.ANDANDO_DIREITA):
            self.animacoes.iniciar_andar_direita()

    def parar_controle_direita(self):
        self.sapo.andando_manual = False
        self.sapo.controle_direita = False
        if self.animacoes.maquina.eh(EstadoSapo.ANDANDO_DIREITA):
            self.animacoes.maquina.trocar(EstadoSapo.PARADO)

    def executar(self, dt):
        maquina = self.animacoes.maquina

        # =====================================
        # AGENDAMENTO CAMINHADA
        # =====================================
        agora = datetime.now()
        horario_atual = (agora.hour, agora.minute)
        executar_caminhada = False

        if self.sapo.controle_esquerda:
            self.sapo.x -= 4

        if self.sapo.controle_direita:
            self.sapo.x += 4

            if self.sapo.x > LARGURA:
                self.sapo.x = LARGURA

        intencao = self._escolher_intencao(
            agora,
            horario_atual,
            maquina,
        )

        if intencao == "caminhar":
            executar_caminhada = True

        if executar_caminhada:
            self.sapo.andar_iniciado_por_controle = False
            if self.sapo.pode_caminhar():
                self.animacoes.proxima_tentativa_caminhada = None
                self.animacoes._ultimo_frame_andar = -1
                self.animacoes.iniciar_andar_esquerda()
                if not self.spotify.spotify_tocando_cache:
                    self.audio.tocar_passeio_sapudo()
            else:
                self.animacoes.proxima_tentativa_caminhada = agora + timedelta(
                    minutes=15
                )

        if self.animacoes.maquina.eh(EstadoSapo.ANDANDO_ESQUERDA):
            frame_atual = self.animacoes.andar_esquerda.frame

            if not hasattr(self.animacoes, "_ultimo_frame_andar"):
                self.animacoes._ultimo_frame_andar = -1

            if frame_atual != self.animacoes._ultimo_frame_andar:
                self.animacoes._ultimo_frame_andar = frame_atual
                self.sapo.x -= 4

        if self.animacoes.maquina.eh(EstadoSapo.ANDANDO_DIREITA):
            frame_atual = self.animacoes.andar_direita.frame

            if not hasattr(self.animacoes, "_ultimo_frame_andar_direita"):
                self.animacoes._ultimo_frame_andar_direita = -1

            if frame_atual != self.animacoes._ultimo_frame_andar_direita:
                self.animacoes._ultimo_frame_andar_direita = frame_atual
                self.sapo.x += 4

        # ===================================
        # ACORDANDO
        # ===================================
        if maquina.eh(EstadoSapo.ACORDANDO):
            if self.animacoes.acordar.atualizar(dt):
                maquina.trocar(EstadoSapo.PARADO)
            self._estado_sapo_anterior = maquina.estado
            return

        # ===================================
        # ADORMECENDO
        # ===================================
        horario_sono = self.agenda.verificar_horario_sono(agora)
        if maquina.eh(EstadoSapo.ADORMECENDO):
            if not horario_sono:
                self.animacoes.iniciar_acordar()
                self._estado_sapo_anterior = maquina.estado
                return

            if self.animacoes.dormir.atualizar(dt):
                maquina.trocar(EstadoSapo.DORMINDO)

            self._estado_sapo_anterior = maquina.estado
            return

        # ===================================
        # RESET DIÁRIO
        # ===================================
        self.agenda.atualizar_resets_diarios(agora)
        # ===================================
        # ACORDAR
        # ===================================
        if intencao == "acordar" and maquina.em_estado(
            EstadoSapo.DORMINDO,
            EstadoSapo.ADORMECENDO,
        ):
            self.animacoes.iniciar_acordar()
            self.agenda.executou_acordar_hoje = True
            self._estado_sapo_anterior = maquina.estado
            return

        # ===================================
        # DORMIR
        # ===================================
        if intencao == "dormir" and not maquina.em_estado(
            EstadoSapo.DORMINDO,
            EstadoSapo.ADORMECENDO,
        ):
            self.agenda.iniciou_sono_hoje = True
            self.animacoes.iniciar_dormir()
            self._estado_sapo_anterior = maquina.estado
            return

        self._estado_sapo_anterior = maquina.estado

    def _escolher_intencao(self, agora, horario_atual, maquina):
        if self.agenda.deve_iniciar_caminhada(agora, horario_atual):
            return "caminhar"

        if (
            not self.agenda.verificar_horario_sono(agora)
            and not self.agenda.executou_acordar_hoje
            and maquina.em_estado(
                EstadoSapo.DORMINDO,
                EstadoSapo.ADORMECENDO,
            )
        ):
            return "acordar"

        if (
            self.agenda.verificar_horario_sono(agora)
            and not self.agenda.iniciou_sono_hoje
            and not maquina.em_estado(
                EstadoSapo.DORMINDO,
                EstadoSapo.ADORMECENDO,
            )
        ):
            return "dormir"

        return "nenhuma"
