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

    def __init__(
        self,
        sapo,
        violao,
        spotify,
        audio,
        evento_livro,
        clima_service=None,
        tts_service=None,
    ):
        self.sapo = sapo
        self.violao = violao
        self.spotify = spotify
        self.audio = audio
        self.evento_livro = evento_livro
        self.animacoes = sapo.animacoes
        self.agenda = AgendaSapo()
        self.clima_service = clima_service
        self.livro_climatico = getattr(self.evento_livro, "livro_climatico", None)
        self.tts_service = tts_service
        self._narracao_livro_disparada = False
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
        estado_anterior = self._estado_sapo_anterior

        if estado_anterior == EstadoSapo.LENDO_LIVRO and not maquina.eh(
            EstadoSapo.LENDO_LIVRO
        ):
            self._narracao_livro_disparada = False

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

            # quando finaliza soltar violao, encapsular ação sobre o violao
            if self.animacoes.finalizou_soltar_violao:
                self.violao.voltar_origem()
                self.animacoes.finalizou_soltar_violao = False

        if (
            maquina.eh(EstadoSapo.PEGANDO_LIVRO)
            and self.animacoes.pegar_livro.frame
            >= self.animacoes.pegar_livro.total_frames - 1
        ):
            maquina.trocar(EstadoSapo.LENDO_LIVRO)

        if maquina.eh(EstadoSapo.LENDO_LIVRO) and not self._narracao_livro_disparada:
            self._narracao_livro_disparada = True
            self._falar_narracao_livro()

        if (
            maquina.eh(EstadoSapo.LEVANTAR_LIVRO)
            and self.animacoes.levantar_livro.frame
            >= self.animacoes.levantar_livro.total_frames - 1
        ):
            self.evento_livro.mostrar_em_frente_do_sapo(self.sapo)
            maquina.trocar(EstadoSapo.PARADO)

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

    def _falar_narracao_livro(self):
        if not self.tts_service or not self.clima_service:
            return

        texto = self.livro_climatico.gerar_texto_narracao(self.clima_service)
        self.tts_service.falar(texto, self._finalizar_leitura)

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

    def _finalizar_leitura(self):
        if self.animacoes.maquina.eh(EstadoSapo.LENDO_LIVRO):
            self.animacoes.iniciar_levantar_livro()
            self.animacoes.maquina.trocar(EstadoSapo.LEVANTAR_LIVRO)
