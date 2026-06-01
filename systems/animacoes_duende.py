# =====================================
# systems/animacoes_duende.py
# =====================================

import random


class AnimacoesDuende:

    # ==========================
    # ESTADOS
    # ==========================

    DORMINDO = "dormindo"
    ACORDANDO = "acordando"
    VOANDO = "voando"
    INDO_PARA_FRASCO = "indo_para_frasco"
    DESCENDO_PARA_DORMIR = "descendo_para_dormir"

    def __init__(self):

        # ==========================
        # OLHOS
        # ==========================

        self.piscando = False

        self.tempo_piscada = 0.0

        self.tempo_espera = 0.0

        self.intervalo = random.uniform(
            2.0,
            5.0
        )

        # ==========================
        # SONO
        # ==========================

        self.fator_sono_visual = 0.0

        self.ciclo_sono = CicloSono()

        self.estado = self.VOANDO

    # =====================================
    # ESTADO
    # =====================================

    @property
    def dormindo(self):
        return self.estado == self.DORMINDO


    @property
    def acordando(self):
        return self.estado == self.ACORDANDO


    @property
    def indo_para_frasco(self):
        return self.estado == self.INDO_PARA_FRASCO


    @property
    def descendo_para_dormir(self):
        return self.estado == self.DESCENDO_PARA_DORMIR

    @property
    def voando(self):
        return self.estado == self.VOANDO

    # =====================================
    # TRANSIÇÕES
    # =====================================

    def iniciar_sono(self):
        self.estado = self.DORMINDO


    def iniciar_acordar(self):
        self.estado = self.ACORDANDO


    def iniciar_descida(self):
        self.estado = self.DESCENDO_PARA_DORMIR


    def iniciar_entrada_frasco(self):
        self.estado = self.INDO_PARA_FRASCO


    def iniciar_voo(self):
        self.estado = self.VOANDO

    def atualizar_transicoes(
        self,
        dt,
        duende,
        clima_disponivel,
        frasco_rect
    ):
        if self.acordando:

            self.ciclo_sono.tempo_acordando += dt

            if (
                self.ciclo_sono.tempo_acordando
                >= self.ciclo_sono.tempo_maximo_acordado
            ):

                self.iniciar_voo()
                self.ciclo_sono.tempo_acordando = 0

                if not clima_disponivel:

                    duende.x_entrada_frasco = (
                        frasco_rect.centerx
                    )

                    duende.y_entrada_frasco = (
                        frasco_rect.top - 30
                    )

                    self.iniciar_entrada_frasco()

        if (
            not clima_disponivel
            and
            not self.dormindo
            and
            not self.descendo_para_dormir
            and
            not self.indo_para_frasco
            and
            not self.acordando
        ):

            duende.x_entrada_frasco = (
                frasco_rect.centerx
            )

            duende.y_entrada_frasco = (
                frasco_rect.top - 30
            )

            self.iniciar_entrada_frasco()

        if (
            clima_disponivel
            and not self.ciclo_sono.dormir_por_tempo
            and not self.dormindo
        ):

            self.iniciar_voo()

    def iniciar_sono_programado(self):

        self.ciclo_sono.dormir_por_tempo = True

        self.ciclo_sono.resetar_tempos()

    def cancelar_sono_programado(self):

        self.ciclo_sono.dormir_por_tempo = False

        self.ciclo_sono.resetar_tempos()

    def atualizar_sono_programado(
        self,
        dt,
        duende,
        clima_disponivel,
        frasco_rect
    ):
        if self.ciclo_sono.dormir_por_tempo:

            self.ciclo_sono.tempo_dormindo += dt

            if (
                self.ciclo_sono.tempo_dormindo
                >= self.ciclo_sono.tempo_maximo_dormindo
            ):

                self.ciclo_sono.tempo_dormindo = 0
                self.ciclo_sono.dormir_por_tempo = False

                if clima_disponivel:

                    self.ciclo_sono.resetar_tempos()

                    self.iniciar_acordar()

                    duende.y = (
                        frasco_rect.top
                        - 50
                    )

                    duende.escolher_novo_destino()

                else:

                    self.ciclo_sono.tempo_dormindo = 0

                    self.ciclo_sono.dormir_por_tempo = True

    # =====================================
    # UPDATE
    # =====================================

    def atualizar(self, dt):

        # =================================
        # DORMINDO
        # =================================

        if self.dormindo:

            self.piscando = False

            return

        # =================================
        # ESPERA
        # =================================

        self.tempo_espera += dt

        # =================================
        # INICIAR PISCADA
        # =================================

        if not self.piscando:

            if (
                self.tempo_espera
                >= self.intervalo
            ):

                self.piscando = True

                self.tempo_piscada = 0.0

        # =================================
        # FINALIZAR PISCADA
        # =================================

        else:

            self.tempo_piscada += dt

            if self.tempo_piscada >= 0.12:

                self.piscando = False

                self.tempo_espera = 0.0

                self.intervalo = random.uniform(
                    2.0,
                    5.0
                )


class CicloSono:

    def __init__(self):

        self.tempo_dormindo = 0.0

        self.tempo_acordando = 0.0

        self.dormir_por_tempo = False

        self.tempo_maximo_dormindo = 420    # 7 minutos

        self.tempo_maximo_acordado = 180    # 3 minutos

    def resetar_tempos(self):
        self.tempo_dormindo = 0
        self.tempo_acordando = 0