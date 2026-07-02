# =====================================
# systems/animacoes_duende.py
# =====================================

import random

from domains.sapudo.animacoes_sapo import Animacao


class AnimacoesDuende:
    # ==========================
    # ESTADOS
    # ==========================

    DORMINDO = "dormindo"
    ACORDANDO = "acordando"
    VOANDO = "voando"
    INDO_PARA_FRASCO = "indo_para_frasco"
    DESCENDO_PARA_DORMIR = "descendo_para_dormir"
    GUARDANDO_VIOLAO = "guardando_violao"
    ESCONDENDO_ATRAS_VIOLAO = "escondendo_atras_violao"
    PERSEGUINDO_ESFERA = "perseguindo_esfera"
    COMENDO_ESFERA = "comendo_esfera"

    def __init__(self):
        self.intervalo = random.uniform(2.0, 5.0)
        # ==========================
        # SONO
        # ==========================
        self.fator_sono_visual = 0.0
        self.ciclo_sono = CicloSono()
        self.estado = self.VOANDO

        # ====================================
        # CONTROLE TROCA DE FRAMES
        # ====================================
        self.animacao_voando = Animacao(15, 0.20)
        self.animacao_dormindo = Animacao(1, 0.20)
        self.animacao_descendo_para_dormir = Animacao(10, 0.20)
        self.animacao_guardando_violao = Animacao(4, 0.40)
        self.animacao_comendo_esfera = Animacao(60, 0.15)

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

    @property
    def guardando_violao(self):
        return self.estado == self.GUARDANDO_VIOLAO

    @property
    def escondendo_atras_violao(self):
        return self.estado == self.ESCONDENDO_ATRAS_VIOLAO

    @property
    def comendo_esfera(self):
        return self.estado == self.COMENDO_ESFERA

    # =====================================
    # TRANSIÇÕES
    # =====================================

    def iniciar_sono(self):
        self.animacao_dormindo.reset()
        self.estado = self.DORMINDO

    def iniciar_acordar(self):
        self.estado = self.ACORDANDO

    def iniciar_descida(self):
        self.animacao_descendo_para_dormir.reset()
        self.estado = self.DESCENDO_PARA_DORMIR

    def iniciar_entrada_frasco(self):
        self.estado = self.INDO_PARA_FRASCO

    def iniciar_voo(self):
        self.animacao_voando.reset()
        self.estado = self.VOANDO

    def iniciar_guardando_violao(self):
        self.animacao_guardando_violao.reset()
        self.estado = self.GUARDANDO_VIOLAO

    def iniciar_escondendo_atras_violao(self):
        self.estado = self.ESCONDENDO_ATRAS_VIOLAO

    def iniciar_perseguindo_esfera(self):
        self.estado = self.PERSEGUINDO_ESFERA

    def iniciar_comer_esfera(self):
        self.animacao_comendo_esfera.reset()
        self.estado = self.COMENDO_ESFERA

    # =====================================
    # UPDATE
    # =====================================

    def atualizar(self, dt):
        self._atualizar_animacoes(dt)

    def _atualizar_animacoes(self, dt):
        if self.voando or self.escondendo_atras_violao:
            self.animacao_voando.atualizar(dt)
        elif self.dormindo:
            self.animacao_dormindo.atualizar(dt)
        elif self.descendo_para_dormir:
            self.animacao_descendo_para_dormir.atualizar(dt)
        elif self.guardando_violao:
            self.animacao_guardando_violao.atualizar(dt)


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
