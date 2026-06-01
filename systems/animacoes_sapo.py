import random
from datetime import datetime


class AnimacoesSapo:

    def __init__(self):

        # ====================================
        # OLHOS INDIVIDUAIS
        # ====================================

        self.olho_esquerdo_forcado = False
        self.olho_direito_forcado = False

        self.tempo_olho_esquerdo = 0.0
        self.tempo_olho_direito = 0.0

        self.duracao_olho_forcado = 1.2

        # ====================================
        # ESTADOS
        # ====================================

        self.piscando = False

        self.bocejando = False

        self.dormindo = False

        # ====================================
        # CONTROLE SONO
        # ====================================

        self.iniciou_sono_hoje = False

        self.bocejo_pre_sono = False

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

        # ====================================
        # CONTROLE BOCEJO
        # ====================================

        self.ultimo_bocejo_minuto = None

        self.tempo_bocejo = 0.0

        self.duracao_bocejo = 2.8

        # ====================================
        # CONTROLE VIOLÃO
        # ====================================

        self.tocando_violao = False

        self.frame_violao = 0

        self.ultimo_frame_violao = 0

        self.tempo_violao = 0.0

        self.direcao_violao = 1

        self.intervalo_violao = random.uniform(
            0.10,
            0.22
        )

        # ====================================
        # VISUAIS
        # ====================================

        self.olhos_fechados = False

        self.boca_yawn = False

        # ====================================
        # SONO VISUAL
        # ====================================

        self.sleep_offset_y = 0

        self.sleep_body_offset_y = 0

        self.sleep_transition_delay = 0.0

    # ====================================
    # SONO
    # ====================================

    def verificar_horario_sono(self):

        agora = datetime.now()

        horario_atual = (
            agora.hour * 60
        ) + agora.minute

        horario_dormir = (
            22 * 60
        )

        horario_acordar = (
            7 * 60
        ) + 30

        return (
            horario_atual >= horario_dormir
            or horario_atual < horario_acordar
        )

    # ====================================
    # UPDATE
    # ====================================

    def atualizar(self, dt):

        agora = datetime.now()

        self.atualizar_violao(dt)

        if self.olho_esquerdo_forcado:

            self.tempo_olho_esquerdo += dt

            if (
                self.tempo_olho_esquerdo
                >= self.duracao_olho_forcado
            ):
                self.olho_esquerdo_forcado = False


        if self.olho_direito_forcado:

            self.tempo_olho_direito += dt

            if (
                self.tempo_olho_direito
                >= self.duracao_olho_forcado
            ):
                self.olho_direito_forcado = False

        # ====================================
        # RESET
        # ====================================

        if (
            agora.hour == 8
            and agora.minute == 0
        ):

            self.iniciou_sono_hoje = False

        horario_sono = (
            self.verificar_horario_sono()
        )

        # ====================================
        # INICIAR SONO
        # ====================================

        if (
            horario_sono
            and not self.iniciou_sono_hoje
            and not self.bocejando
            and not self.dormindo
        ):

            self.iniciar_bocejo_pre_sono()

            self.iniciou_sono_hoje = True

        # ====================================
        # BOCEJO
        # ====================================

        if self.bocejando:

            self.atualizar_bocejo(dt)

        else:

            # ====================================
            # SONO
            # ====================================

            if horario_sono:

                self.dormindo = True

                self.piscando = False

                self.olhos_fechados = True

                self.boca_yawn = False

                self.tempo_piscada = 0.0

                self.tempo_espera_piscada = 0.0

            else:

                self.dormindo = False

                self.sleep_transition_delay = 0

                # ====================================
                # PISCADA
                # ====================================

                if self.piscando:

                    self.atualizar_piscada(dt)

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

                        self.iniciar_bocejo()

                        self.ultimo_bocejo_minuto = (
                            minuto_base
                        )

                        return

                # ====================================
                # PISCADA
                # ====================================

                if not self.piscando:

                    self.tempo_espera_piscada += dt

                    if (
                        self.tempo_espera_piscada
                        >= self.intervalo_piscada
                    ):

                        self.iniciar_piscada()

        # ====================================
        # DELAY SONO
        # ====================================

        if self.dormindo:

            self.sleep_transition_delay += dt

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

    # ====================================
    # PISCADA
    # ====================================

    def iniciar_piscada(self):

        if (
            self.bocejando
            or self.dormindo
        ):

            return

        self.piscando = True

        self.tempo_piscada = 0.0

        self.olhos_fechados = True

    def atualizar_piscada(self, dt):

        self.tempo_piscada += dt

        if (
            self.tempo_piscada
            >= self.duracao_piscada
        ):

            self.piscando = False

            self.olhos_fechados = False

            self.tempo_espera_piscada = 0.0

            self.intervalo_piscada = random.uniform(
                3.5,
                6.0
            )

    # ====================================
    # BOCEJO NORMAL
    # ====================================

    def iniciar_bocejo(self):

        if self.dormindo:

            return

        self.piscando = False

        self.bocejando = True

        self.bocejo_pre_sono = False

        self.tempo_bocejo = 0.0

        self.duracao_bocejo = 2.8

    # ====================================
    # BOCEJO PRÉ SONO
    # ====================================

    def iniciar_bocejo_pre_sono(self):

        self.piscando = False

        self.bocejando = True

        self.bocejo_pre_sono = True

        self.tempo_bocejo = 0.0

        self.duracao_bocejo = 5.5

    def atualizar_bocejo(self, dt):

        self.tempo_bocejo += dt

        if not self.bocejo_pre_sono:

            if self.tempo_bocejo <= 0.6:

                self.olhos_fechados = True

                self.boca_yawn = False

            elif self.tempo_bocejo <= 2.0:

                self.olhos_fechados = True

                self.boca_yawn = True

            elif self.tempo_bocejo <= self.duracao_bocejo:

                self.olhos_fechados = False

                self.boca_yawn = False

            else:

                self.finalizar_bocejo()

        else:

            if self.tempo_bocejo <= 1.2:

                self.olhos_fechados = True

                self.boca_yawn = False

            elif self.tempo_bocejo <= 4.2:

                self.olhos_fechados = True

                self.boca_yawn = True

            elif self.tempo_bocejo <= self.duracao_bocejo:

                self.olhos_fechados = True

                self.boca_yawn = False

            else:

                self.bocejando = False

                self.boca_yawn = False

                self.olhos_fechados = True

                self.dormindo = True

    # ====================================
    # FINALIZAR BOCEJO
    # ====================================

    def finalizar_bocejo(self):

        self.bocejando = False

        self.olhos_fechados = False

        self.boca_yawn = False

        self.tempo_bocejo = 0.0

        self.tempo_espera_piscada = 0.0

    # ====================================
    # VIOLÃO
    # ====================================

    def iniciar_violao(self):

        self.tocando_violao = True

    def parar_violao(self):

        self.tocando_violao = False
        self.frame_violao = 0
        self.ultimo_frame_violao = 0

    def atualizar_violao(
        self,
        dt
    ):

        if not self.tocando_violao:
            return

        self.tempo_violao += dt

        if self.tempo_violao < self.intervalo_violao:
            return

        self.tempo_violao = 0

        self.intervalo_violao = random.uniform(
            0.10,
            0.22
        )

        frame = self.frame_violao

        possibilidades = []

        if frame > 0:
            possibilidades.append(
                frame - 1
            )

        if frame < 3:
            possibilidades.append(
                frame + 1
            )

        # pequena chance de segurar o movimento

        if random.random() < 0.20:
            possibilidades.append(
                frame
            )

        # evita ficar tremendo entre
        # dois frames

        if (
            len(possibilidades) > 1
            and self.ultimo_frame_violao in possibilidades
            and random.random() < 0.60
        ):
            possibilidades.remove(
                self.ultimo_frame_violao
            )

        self.ultimo_frame_violao = frame

        self.frame_violao = random.choice(
            possibilidades
        )

    # ====================================
    # CLICAR OLHO
    # ====================================

    def clicar_olho_esquerdo(self):

        if self.dormindo:

            self.olho_esquerdo_forcado = False
            return

        self.olho_esquerdo_forcado = True
        self.tempo_olho_esquerdo = 0.0

    def clicar_olho_direito(self):

        if self.dormindo:

            self.olho_direito_forcado = False
            return

        self.olho_direito_forcado = True
        self.tempo_olho_direito = 0.0

    # ====================================
    # HELPERS
    # ====================================

    def obter_asset_olho(
        self,
        olho_aberto,
        olho_fechado
    ):

        if self.olhos_fechados:

            return olho_fechado

        return olho_aberto

    def obter_asset_boca(
        self,
        boca_yawn
    ):

        if self.boca_yawn:

            return boca_yawn

        return None