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
        self.piscando = False
        self.tempo_piscada = 0.0
        self.tempo_espera = 0.0
        self.intervalo = random.uniform(2.0, 5.0)

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
            if self.tempo_espera >= self.intervalo:
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

                self.intervalo = random.uniform(2.0, 5.0)


class CicloSono:
    def __init__(self):
        self.tempo_dormindo = 0.0
        self.tempo_acordando = 0.0
        self.dormir_por_tempo = False
        self.tempo_maximo_dormindo = 420  # 7 minutos
        self.tempo_maximo_acordado = 180  # 3 minutos

    def resetar_tempos(self):
        self.tempo_dormindo = 0
        self.tempo_acordando = 0
