# =====================================
# systems/animacoes_duende.py
# =====================================

import random

from core.animacao_movimento import AnimacaoMovimento
from core.event_bus import event_bus
from domains.sapudo.maquina_estado_sapo import StateMachine


class AnimacoesDuende:
    # ==========================
    # ESTADOS
    # ==========================

    DORMINDO = "dormindo"
    ACORDANDO = "acordando"
    VOANDO = "voando"
    EM_FRENTE_A_CASA = "em_frente_a_casa"
    SAINDO_DA_CASA = "saindo_da_casa"
    INDO_PARA_CASA = "indo_para_casa"
    DESCENDO_PARA_DORMIR = "descendo_para_dormir"
    TELEPORTANDO = "teleportando"

    def __init__(self):
        self.intervalo = random.uniform(2.0, 5.0)
        # ==========================
        # SONO
        # ==========================
        self.fator_sono_visual = 0.0
        self.ciclo_sono = CicloSono()
        self.maquina = StateMachine(self.VOANDO)

        # ====================================
        # CONTROLE TROCA DE FRAMES
        # ====================================
        self.animacao_voando = AnimacaoMovimento(15, 0.20)
        self.animacao_dormindo = AnimacaoMovimento(1, 0.20)
        self.animacao_descendo_para_dormir = AnimacaoMovimento(10, 0.20)

    # =====================================
    # ESTADO
    # =====================================

    @property
    def estado(self):
        return self.maquina.estado

    @estado.setter
    def estado(self, valor):
        self.maquina.trocar(valor)

    @property
    def dormindo(self):
        return self.maquina.eh(self.DORMINDO)

    @property
    def acordando(self):
        return self.maquina.eh(self.ACORDANDO)

    @property
    def em_frente_a_casa(self):
        return self.maquina.eh(self.EM_FRENTE_A_CASA)

    @property
    def saindo_da_casa(self):
        return self.maquina.eh(self.SAINDO_DA_CASA)

    @property
    def indo_para_casa(self):
        return self.maquina.eh(self.INDO_PARA_CASA)

    @property
    def descendo_para_dormir(self):
        return self.maquina.eh(self.DESCENDO_PARA_DORMIR)

    @property
    def voando(self):
        return self.maquina.eh(self.VOANDO)

    @property
    def teleportando(self):
        return self.maquina.eh(self.TELEPORTANDO)

    @property
    def atras_da_casa(self):
        return self._em_estado(self.DESCENDO_PARA_DORMIR, self.SAINDO_DA_CASA)

    def _em_estado(self, *estados):
        return self.estado in estados

    # =====================================
    # TRANSIÇÕES
    # =====================================

    def iniciar_sono(self):
        self.animacao_dormindo.reset()
        self.estado = self.DORMINDO

    def iniciar_acordar(self):
        self.estado = self.ACORDANDO

    def iniciar_em_frente_a_casa(self):
        self.estado = self.EM_FRENTE_A_CASA

    def iniciar_saindo_da_casa(self):
        self.estado = self.SAINDO_DA_CASA

    def iniciar_descida(self):
        self.animacao_descendo_para_dormir.reset()
        self.estado = self.DESCENDO_PARA_DORMIR
        event_bus.publicar("descendo_para_dormir")

    def iniciar_entrada_casa(self):
        self.animacao_descendo_para_dormir.reset()
        self.estado = self.INDO_PARA_CASA

    def iniciar_voo(self):
        self.animacao_voando.reset()
        self.estado = self.VOANDO
        event_bus.publicar("voo_iniciado")

    def iniciar_teleportando(self):
        self.estado = self.TELEPORTANDO

    def obter_selecao_frame(self):
        if self.dormindo:
            return "dormindo", self.animacao_dormindo.frame
        if self.descendo_para_dormir:
            return "descendo_para_dormir", self.animacao_descendo_para_dormir.frame
        if self.indo_para_casa:
            return "indo_para_casa", self.animacao_descendo_para_dormir.frame

        return "voando", self.animacao_voando.frame

    # =====================================
    # UPDATE
    # =====================================

    def atualizar(self, dt):
        self.maquina.atualizar(dt)
        self._atualizar_animacoes(dt)

    def _atualizar_animacoes(self, dt):
        if self.voando:
            self.animacao_voando.atualizar(dt)
        elif self.dormindo:
            self.animacao_dormindo.atualizar(dt)
        elif self.indo_para_casa or self.descendo_para_dormir:
            self.animacao_descendo_para_dormir.atualizar(dt)


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
