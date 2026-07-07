from datetime import datetime, timedelta

from domains.sapudo.agenda_sapo import AgendaSapo
from domains.sapudo.maquina_estado_sapo import EstadoSapo
from utils.input import LARGURA


class ControlarComportamentoSapoUseCase:
    # ==========================
    # ESTADOS
    # ==========================

    EXPLORANDO = "explorando"
    ESCONDIDO_VIOLAO = "escondido_violao"
    ORBITANDO = "orbitando"
    FUGINDO = "fugindo"

    def __init__(self, sapo, violao, spotify, audio):
        self.sapo = sapo
        self.violao = violao
        self.spotify = spotify
        self.audio = audio
        self.animacoes = sapo.animacoes
        self.agenda = AgendaSapo()

    def ir_para_feira(self):
        self.sapo.comando_ir_feira = True
        self.sapo.andar_iniciado_por_controle = False
        if self.sapo.pode_caminhar():
            self.animacoes.proxima_tentativa_caminhada = None
            self.animacoes._ultimo_frame_andar = -1
            self.animacoes.iniciar_andar_esquerda()

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

        if self.sapo.controle_esquerda and not self.sapo.indo_para_feira:
            self.sapo.x -= 4
            if self.sapo.background_renderer.cenario_feira and self.sapo.x <= 0:
                self.sapo.x = 0

        if self.sapo.controle_direita:
            self.sapo.x += 4

            if self.sapo.background_renderer.cenario_feira:
                if self.sapo.x > LARGURA:
                    excesso = self.sapo.x - LARGURA

                    self.sapo.background_renderer.cenario_feira = False
                    self.sapo.x = excesso

            else:
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

            if (
                self.sapo.x < 0
                and (self.sapo.comando_ir_feira or not self.sapo.indo_para_feira)
                and not self.sapo.background_renderer.cenario_feira
            ):
                self.sapo.background_renderer.cenario_feira = True
                self.sapo.indo_para_feira = True

                self.sapo.x = LARGURA + 100
                self.sapo.comando_ir_feira = False

            if self.sapo.indo_para_feira:
                destino = (LARGURA // 2) + 180

                if self.sapo.x <= destino:
                    self.sapo.x = destino

                    self.sapo.indo_para_feira = False
                    self.sapo.comando_ir_feira = False

                    self.sapo.controle_esquerda = False
                    self.sapo.andando_manual = False

                    self.animacoes.maquina.trocar(EstadoSapo.PARADO)

                    self.animacoes._ultimo_frame_andar = -1

        if self.animacoes.maquina.eh(EstadoSapo.ANDANDO_DIREITA):
            frame_atual = self.animacoes.andar_direita.frame

            if not hasattr(self.animacoes, "_ultimo_frame_andar_direita"):
                self.animacoes._ultimo_frame_andar_direita = -1

            if frame_atual != self.animacoes._ultimo_frame_andar_direita:
                self.animacoes._ultimo_frame_andar_direita = frame_atual
                self.sapo.x += 4

            # quando finaliza soltar violao, encapsular ação sobre o violao
            if self.animacoes.finalizou_soltar_violao:
                self.violao.voltar_origem()
                self.animacoes.finalizou_soltar_violao = False

        if (
            self.animacoes.maquina.eh(EstadoSapo.PEGANDO_LIVRO)
            and self.animacoes.pegar_livro.frame
            >= self.animacoes.pegar_livro.total_frames - 1
        ):
            self.animacoes.maquina.trocar(EstadoSapo.LENDO_LIVRO)

        # ===================================
        # ACORDANDO
        # ===================================
        if maquina.eh(EstadoSapo.ACORDANDO):
            if self.animacoes.acordar.atualizar(dt):
                maquina.trocar(EstadoSapo.PARADO)
            return

        # ===================================
        # ADORMECENDO
        # ===================================
        horario_sono = self.agenda.verificar_horario_sono(agora)
        if maquina.eh(EstadoSapo.ADORMECENDO):
            if not horario_sono:
                self.animacoes.iniciar_acordar()
                return

            if self.animacoes.dormir.atualizar(dt):
                maquina.trocar(EstadoSapo.DORMINDO)

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
            return

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
