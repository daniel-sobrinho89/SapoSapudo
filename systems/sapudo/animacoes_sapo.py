import random
from datetime import datetime

from systems.sapudo.maquina_estado_sapo import EstadoSapo, MaquinaEstadoSapo


class AnimacoesSapo:
    def __init__(self):
        # ====================================
        # ESTADOS
        # ====================================
        self.maquina = MaquinaEstadoSapo()

        # ====================================
        # CONTROLE SONO
        # ====================================

        self.iniciou_sono_hoje = False

        # ====================================
        # CONTROLE PISCADA
        # ====================================

        self.tempo_espera_piscada = 0.0

        self.intervalo_piscada = random.uniform(3.5, 6.0)

        self.tempo_piscada = 0.0

        self.duracao_piscada = 0.50

        self.frame_parado = 0

        self.tempo_parado = 0.0

        # ====================================
        # CONTROLE BOCEJO
        # ====================================

        self.ultimo_bocejo_minuto = None

        # ====================================
        # DORMIR (PNG)
        # ====================================

        self.frame_dormir = 0

        self.tempo_dormir = 0.0

        # ====================================
        # DORMINDO (LOOP)
        # ====================================

        self.frame_dormindo = 0

        self.tempo_dormindo = 0.0

        # ====================================
        # CONTROLE VIOLÃO
        # ====================================

        self.ultimo_frame_guardar = -1
        self.parar_audio_violao = False

        self.frame_pegar_violao = 0
        self.tempo_pegar_violao = 0.0

        self.frame_violao = 0

        self.ultimo_frame_violao = 0

        self.tempo_violao = 0.0

        self.direcao_violao = 1

        self.frame_min_violao = 0
        self.frame_max_violao = 9

        self.intervalo_violao = 0.22
        self.callback_verificar_spotify = None

        # ====================================
        # ACORDAR (PNG)
        # ====================================

        self.frame_acordar = 0
        self.tempo_acordar = 0.0

        self.executou_acordar_hoje = False

        self.frame_levantar_violao = 0
        self.frame_guardar_violao = 0
        self.frame_soltar_violao = 0
        self.tempo_levantar_violao = 0
        self.tempo_guardar_violao = 0
        self.tempo_soltar_violao = 0

        self.tempo_tocando_violao = 0

        # ====================================
        # CAMINHADA
        # ====================================

        self.frame_andar_esquerda = 0
        self.tempo_andar_esquerda = 0.0
        self.frame_andar_direita = 0
        self.tempo_andar_direita = 0.0

        # horários planejados
        self.horarios_caminhada = [(8, 0), (14, 0), (18, 0)]

        # retry quando não puder caminhar
        self.proxima_tentativa_caminhada = None

        # evita disparar várias vezes no mesmo minuto
        self.ultima_execucao_caminhada = None

    # ====================================
    # SONO
    # ====================================

    def verificar_horario_sono(self):
        agora = datetime.now()

        horario_atual = (agora.hour * 60) + agora.minute

        horario_dormir = (22 * 60) + 00
        horario_acordar = (7 * 60) + 30

        if horario_dormir < horario_acordar:
            return horario_dormir <= horario_atual < horario_acordar

        return horario_atual >= horario_dormir or horario_atual < horario_acordar

    # ====================================
    # UPDATE
    # ====================================

    def atualizar(self, dt):
        agora = datetime.now()

        self.atualizar_pegar_violao(dt)
        self.atualizar_violao(dt)
        self.atualizar_levantar_violao(dt)
        self.atualizar_guardar_violao(dt)
        self.atualizar_soltar_violao(dt)
        self.atualizar_andar_esquerda(dt)
        self.atualizar_andar_direita(dt)

        self.tempo_parado += dt

        horario_sono = self.verificar_horario_sono()

        if self.tempo_parado >= 0.15:
            self.tempo_parado = 0
            self.frame_parado += 1

            if self.frame_parado >= 60:
                self.frame_parado = 0

        if self.maquina.eh(EstadoSapo.ACORDANDO):
            self.tempo_acordar += dt

            if self.tempo_acordar >= 0.15:
                self.tempo_acordar = 0

                self.frame_acordar += 1

                if self.frame_acordar >= 60:
                    self.frame_acordar = 59

                    self.maquina.trocar(EstadoSapo.PARADO)

            return

        if self.maquina.eh(EstadoSapo.ADORMECENDO):
            self.tempo_dormir += dt

            if not horario_sono:
                self.iniciar_acordar()

                return

            if self.tempo_dormir >= 0.15:
                self.tempo_dormir = 0
                self.frame_dormir += 1

                if self.frame_dormir >= 60:
                    self.frame_dormir = 59
                    self.maquina.trocar(EstadoSapo.DORMINDO)

            return

        # ====================================
        # RESET
        # ====================================
        if agora.hour == 8 and agora.minute == 0:
            self.iniciou_sono_hoje = False
            self.executou_acordar_hoje = False

        if (
            not horario_sono
            and not self.executou_acordar_hoje
            and (self.maquina.em_estado(EstadoSapo.DORMINDO, EstadoSapo.ADORMECENDO))
        ):
            self.iniciar_acordar()

            self.executou_acordar_hoje = True

            return

        # ====================================
        # INICIAR SONO
        # ====================================

        if (
            horario_sono
            and not self.iniciou_sono_hoje
            and not (
                self.maquina.em_estado(EstadoSapo.DORMINDO, EstadoSapo.ADORMECENDO)
            )
        ):
            self.iniciou_sono_hoje = True

            self.iniciar_dormir()

            return

        # ====================================
        # DELAY SONO
        # ====================================

        if self.maquina.eh(EstadoSapo.DORMINDO):
            self.tempo_dormindo += dt

            if self.tempo_dormindo >= 0.5:
                self.tempo_dormindo = 0

                self.frame_dormindo += 1

                if self.frame_dormindo >= 9:
                    self.frame_dormindo = 0

    def iniciar_dormir(self):
        self.maquina.trocar(EstadoSapo.ADORMECENDO)

        self.frame_dormir = 0
        self.tempo_dormir = 0

    # ====================================
    # ACORDAR
    # ====================================

    def iniciar_acordar(self):
        self.maquina.trocar(EstadoSapo.ACORDANDO)

        self.frame_acordar = 0
        self.tempo_acordar = 0

    # ====================================
    # VIOLÃO
    # ====================================

    def atualizar_pegar_violao(self, dt):
        if not self.maquina.eh(EstadoSapo.PEGANDO_VIOLAO):
            return

        self.tempo_pegar_violao += dt

        if self.tempo_pegar_violao < 0.16:
            return

        self.tempo_pegar_violao = 0
        self.frame_pegar_violao += 1

        if self.frame_pegar_violao >= 15:
            self.frame_pegar_violao = 14
            self.maquina.trocar(EstadoSapo.TOCANDO_VIOLAO)
            self.frame_violao = 0
            self.direcao_violao = 1

    def iniciar_violao(self):
        if self.maquina.em_estado(EstadoSapo.TOCANDO_VIOLAO, EstadoSapo.PEGANDO_VIOLAO):
            return

        self.maquina.trocar(EstadoSapo.PEGANDO_VIOLAO)
        self.frame_pegar_violao = 0
        self.tempo_pegar_violao = 0
        self.frame_violao = 0
        self.direcao_violao = 1

    def parar_violao(self):
        self.maquina.trocar(EstadoSapo.PARADO)
        self.frame_pegar_violao = 0
        self.frame_violao = 0
        self.ultimo_frame_violao = 0

    def atualizar_violao(self, dt):
        if not self.maquina.eh(EstadoSapo.TOCANDO_VIOLAO):
            return

        self.tempo_tocando_violao += dt

        if self.tempo_tocando_violao >= 900:  # 900 15 minutos
            self.iniciar_levantar_violao()
            return

        self.tempo_violao += dt

        if self.tempo_violao < self.intervalo_violao:
            return

        self.tempo_violao = 0
        self.frame_violao += self.direcao_violao

        if self.frame_violao >= self.frame_max_violao:
            self.frame_violao = self.frame_max_violao
            self.direcao_violao = -1

        elif self.frame_violao <= self.frame_min_violao:
            self.frame_violao = self.frame_min_violao
            self.direcao_violao = 1

    def iniciar_levantar_violao(self):
        self.maquina.trocar(EstadoSapo.LEVANTANDO_VIOLAO)
        self.frame_levantar_violao = 0
        self.tempo_levantar_violao = 0

    def atualizar_levantar_violao(self, dt):
        if not self.maquina.eh(EstadoSapo.LEVANTANDO_VIOLAO):
            return

        self.tempo_levantar_violao += dt

        if self.tempo_levantar_violao < 0.14:
            return

        self.tempo_levantar_violao = 0
        self.frame_levantar_violao += 1

        if self.frame_levantar_violao >= 15:
            self.frame_levantar_violao = 14

            if self.callback_verificar_spotify:
                spotify_tocando = self.callback_verificar_spotify()

            if spotify_tocando:
                self.maquina.trocar(EstadoSapo.TOCANDO_VIOLAO)
                self.frame_violao = 0
                self.direcao_violao = 1
            else:
                self.maquina.trocar(EstadoSapo.GUARDANDO_VIOLAO)
                self.frame_guardar_violao = 0
                self.tempo_guardar_violao = 0
                self.ultimo_frame_guardar = -1

    def atualizar_guardar_violao(self, dt):
        if not self.maquina.eh(EstadoSapo.GUARDANDO_VIOLAO):
            return

        self.tempo_guardar_violao += dt

        if self.tempo_guardar_violao < 0.14:
            return

        self.tempo_guardar_violao = 0
        self.frame_guardar_violao += 1
        if self.frame_guardar_violao >= 9:
            self.frame_guardar_violao = 0

    def atualizar_soltar_violao(self, dt):
        if not self.maquina.eh(EstadoSapo.SOLTANDO_VIOLAO):
            return

        self.tempo_soltar_violao += dt

        if self.tempo_soltar_violao < 0.14:
            return

        self.tempo_soltar_violao = 0
        self.frame_soltar_violao += 1

        if self.frame_soltar_violao >= 9:
            self.frame_soltar_violao = 8
            self.maquina.trocar(EstadoSapo.PARADO)
            self.tempo_tocando_violao = 0

    def iniciar_andar_esquerda(self):
        self.maquina.trocar(EstadoSapo.ANDANDO_ESQUERDA)
        self.frame_andar_esquerda = 0
        self.tempo_andar_esquerda = 0

    def iniciar_andar_direita(self):
        self.maquina.trocar(EstadoSapo.ANDANDO_DIREITA)
        self.frame_andar_direita = 0
        self.tempo_andar_direita = 0

    def atualizar_andar_esquerda(self, dt):
        if not self.maquina.eh(EstadoSapo.ANDANDO_ESQUERDA):
            return

        self.tempo_andar_esquerda += dt

        if self.tempo_andar_esquerda < 0.07:
            return

        self.tempo_andar_esquerda = 0
        self.frame_andar_esquerda += 1

        if self.frame_andar_esquerda >= 10:
            self.frame_andar_esquerda = 0

    def atualizar_andar_direita(self, dt):
        if not self.maquina.eh(EstadoSapo.ANDANDO_DIREITA):
            return

        self.tempo_andar_direita += dt

        if self.tempo_andar_direita < 0.07:
            return

        self.tempo_andar_direita = 0
        self.frame_andar_direita += 1

        if self.frame_andar_direita >= 9:
            self.frame_andar_direita = 0
