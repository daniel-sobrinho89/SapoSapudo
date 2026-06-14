import random
from datetime import datetime


class AnimacoesSapo:

    def __init__(self):

        # ====================================
        # ESTADOS
        # ====================================

        self.piscando = False

        self.dormindo = False

        self.acordando = False

        # ====================================
        # CONTROLE SONO
        # ====================================

        self.iniciou_sono_hoje = False

        # ====================================
        # CONTROLE PISCADA
        # ====================================

        self.tempo_espera_piscada = 0.0

        self.intervalo_piscada = random.uniform(
            3.5,
            6.0
        )

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

        self.adormecendo = False

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

        self.pegando_violao = False
        self.tocando_violao = False
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


        # ====================================
        # SONO VISUAL
        # ====================================

        self.sleep_offset_y = 0

        self.sleep_body_offset_y = 0

        self.sleep_transition_delay = 0.0

        # ====================================
        # ACORDAR (PNG)
        # ====================================

        self.acordando = False

        self.frame_acordar = 0

        self.tempo_acordar = 0.0
        
        self.executou_acordar_hoje = False

        self.iniciou_tocar_violao = False

        self.levantando_violao = False
        self.guardando_violao = False
        self.soltando_violao = False
        self.finalizou_soltar_violao = False

        self.frame_levantar_violao = 0
        self.frame_guardar_violao = 0
        self.frame_soltar_violao = 0

        self.tempo_levantar_violao = 0
        self.tempo_guardar_violao = 0
        self.tempo_soltar_violao = 0

        self.tempo_tocando_violao = 0

        self.iniciou_guardar_violao = False

        # ====================================
        # CAMINHADA ESQUERDA
        # ====================================

        self.andando_esquerda = False
        self.frame_andar_esquerda = 0
        self.tempo_andar_esquerda = 0.0

        self.andando_direita = False
        self.frame_andar_direita = 0
        self.tempo_andar_direita = 0.0

        # horários planejados
        self.horarios_caminhada = [
            (8, 0),
            (14, 0),
            (18, 0)
        ]

        # retry quando não puder caminhar
        self.proxima_tentativa_caminhada = None

        # evita disparar várias vezes no mesmo minuto
        self.ultima_execucao_caminhada = None
        self.iniciou_andar_esquerda = False

    # ====================================
    # SONO
    # ====================================

    def verificar_horario_sono(self):

        agora = datetime.now()

        horario_atual = (
            agora.hour * 60
        ) + agora.minute

        horario_dormir = (
            23 * 60
        ) + 59

        horario_acordar = (
            7* 60
        ) + 30

        if horario_dormir < horario_acordar:

            return (
                horario_dormir
                <= horario_atual
                < horario_acordar
            )

        return (
            horario_atual >= horario_dormir
            or horario_atual < horario_acordar
        )

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

        horario_sono = (
            self.verificar_horario_sono()
        )

        if self.tempo_parado >= 0.15:
            self.tempo_parado = 0
            self.frame_parado += 1

            if self.frame_parado >= 60:
                self.frame_parado = 0

        if self.acordando:

            self.tempo_acordar += dt

            if self.tempo_acordar >= 0.15:

                self.tempo_acordar = 0

                self.frame_acordar += 1

                if self.frame_acordar >= 60:

                    self.frame_acordar = 59

                    self.acordando = False

                    self.dormindo = False


            return

        if self.adormecendo:

            self.tempo_dormir += dt

            if not horario_sono:

                self.adormecendo = False

                self.iniciar_acordar()

                return

            if self.tempo_dormir >= 0.15:

                self.tempo_dormir = 0

                self.frame_dormir += 1

                if self.frame_dormir >= 60:

                    self.frame_dormir = 59

                    self.adormecendo = False

                    self.dormindo = True

            return


        # ====================================
        # RESET
        # ====================================
        if (
            agora.hour == 8
            and agora.minute == 0
        ):

            self.iniciou_sono_hoje = False

            self.executou_acordar_hoje = False

        if (
            not horario_sono
            and (
                self.dormindo
                or self.adormecendo
            )
            and not self.acordando
            and not self.executou_acordar_hoje
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
            and not self.dormindo
            and not self.adormecendo
        ):

            self.iniciou_sono_hoje = True

            self.iniciar_dormir()

            return

        # ====================================
        # SONO
        # ====================================

        if horario_sono:
            self.dormindo = True
            self.piscando = False
            self.tempo_piscada = 0.0
            self.tempo_espera_piscada = 0.0

        else:
            self.dormindo = False
            self.sleep_transition_delay = 0

            # ====================================
            # HORÁRIO
            # ====================================
            hora = agora.hour
            minuto = agora.minute

            if hora >= 19:
                minuto_base = (
                    minuto // 5
                ) * 5
                pode_bocejar = (
                    minuto % 5 == 0
                    and self.ultimo_bocejo_minuto
                    != minuto_base
                )
                if pode_bocejar:

                    self.ultimo_bocejo_minuto = (
                        minuto_base
                    )

                    return


        # ====================================
        # DELAY SONO
        # ====================================

        if self.dormindo:

            self.tempo_dormindo += dt

            if self.tempo_dormindo >= 0.5:

                self.tempo_dormindo = 0

                self.frame_dormindo += 1

                if self.frame_dormindo >= 9:

                    self.frame_dormindo = 0

        else:

            self.sleep_transition_delay = 0

        # ====================================
        # TARGETS
        # ====================================

        target_head_offset = 0
        target_body_offset = 0

        if (
            self.dormindo
            and self.sleep_transition_delay >= 0.45
        ):

            target_head_offset = 28

            target_body_offset = 4

        # ====================================
        # INTERPOLAÇÃO
        # ====================================
        velocidade = dt * 2.0

        self.sleep_offset_y += (
            target_head_offset
            - self.sleep_offset_y
        ) * velocidade

        self.sleep_body_offset_y += (
            target_body_offset
            - self.sleep_body_offset_y
        ) * velocidade

    def iniciar_dormir(self):

        self.adormecendo = True

        self.frame_dormir = 0

        self.tempo_dormir = 0

    # ====================================
    # ACORDAR
    # ====================================

    def iniciar_acordar(self):

        self.dormindo = False

        self.adormecendo = False

        self.acordando = True

        self.frame_acordar = 0

        self.tempo_acordar = 0

    # ====================================
    # VIOLÃO
    # ====================================

    def atualizar_pegar_violao(self, dt):

        if not self.pegando_violao:
            return

        self.tempo_pegar_violao += dt

        if self.tempo_pegar_violao < 0.16:
            return

        self.tempo_pegar_violao = 0

        self.frame_pegar_violao += 1

        if self.frame_pegar_violao >= 15:

            self.frame_pegar_violao = 14

            self.pegando_violao = False
            self.tocando_violao = True

            self.frame_violao = 0
            self.direcao_violao = 1

            self.iniciou_tocar_violao = True

    def iniciar_violao(self):

        if self.tocando_violao or self.pegando_violao:
            return

        self.iniciou_tocar_violao = False

        self.pegando_violao = True
        self.tocando_violao = False

        self.frame_pegar_violao = 0
        self.tempo_pegar_violao = 0

        self.frame_violao = 0
        self.direcao_violao = 1

    def parar_violao(self):

        self.iniciou_tocar_violao = False

        self.pegando_violao = False
        self.tocando_violao = False

        self.frame_pegar_violao = 0
        self.frame_violao = 0
        self.ultimo_frame_violao = 0

    def atualizar_violao(self, dt):

        if not self.tocando_violao:
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

        self.parar_audio_violao = True

        self.tocando_violao = False

        self.levantando_violao = True

        self.frame_levantar_violao = 0

        self.tempo_levantar_violao = 0

    def atualizar_levantar_violao(self, dt):

        if not self.levantando_violao:
            return

        self.tempo_levantar_violao += dt

        if self.tempo_levantar_violao < 0.14:
            return

        self.tempo_levantar_violao = 0

        self.frame_levantar_violao += 1

        if self.frame_levantar_violao >= 15:

            self.frame_levantar_violao = 14

            self.levantando_violao = False

            self.guardando_violao = True

            self.frame_guardar_violao = 0

            self.tempo_guardar_violao = 0

            self.ultimo_frame_guardar = -1

            self.iniciou_guardar_violao = True

    def atualizar_guardar_violao(self, dt):

        if not self.guardando_violao:
            return

        self.tempo_guardar_violao += dt

        if self.tempo_guardar_violao < 0.14:
            return

        self.tempo_guardar_violao = 0

        self.frame_guardar_violao += 1

        if self.frame_guardar_violao >= 9:
            self.frame_guardar_violao = 0

    def atualizar_soltar_violao(self, dt):

        if not self.soltando_violao:
            return

        self.tempo_soltar_violao += dt

        if self.tempo_soltar_violao < 0.14:
            return

        self.tempo_soltar_violao = 0

        self.frame_soltar_violao += 1

        if self.frame_soltar_violao >= 9:

            self.frame_soltar_violao = 8

            self.soltando_violao = False

            self.finalizou_soltar_violao = True

            self.tempo_tocando_violao = 0

    def iniciar_andar_esquerda(self):
        self.andando_esquerda = True
        self.frame_andar_esquerda = 0
        self.tempo_andar_esquerda = 0
        self.iniciou_andar_esquerda = True

    def iniciar_andar_direita(self):
        self.andando_direita = True
        self.frame_andar_direita = 0
        self.tempo_andar_direita = 0
        self.iniciou_andar_direita = True


    def atualizar_andar_esquerda(self, dt):

        if not self.andando_esquerda:
            return

        self.tempo_andar_esquerda += dt

        if self.tempo_andar_esquerda < 0.07:
            return

        self.tempo_andar_esquerda = 0
        self.frame_andar_esquerda += 1

        if self.frame_andar_esquerda >= 10:
            self.frame_andar_esquerda = 0


    def atualizar_andar_direita(self, dt):

        if not self.andando_direita:
            return

        self.tempo_andar_direita += dt

        if self.tempo_andar_direita < 0.07:
            return

        self.tempo_andar_direita = 0
        self.frame_andar_direita += 1

        if self.frame_andar_direita >= 9:
            self.frame_andar_direita = 0