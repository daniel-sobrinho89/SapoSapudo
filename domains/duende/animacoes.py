# =====================================
# systems/animacoes_duende.py
# =====================================

import random

from domains.sapudo.animacoes_sapo import Animacao
from domains.sapudo.maquina_estado_sapo import StateMachine


class AnimacoesDuende:
    # ==========================
    # ESTADOS
    # ==========================

    DORMINDO = "dormindo"
    ACORDANDO = "acordando"
    VOANDO = "voando"
    EM_FRENTE_AO_FRASCO = "em_frente_ao_frasco"
    INDO_PARA_FRASCO = "indo_para_frasco"
    DESCENDO_PARA_DORMIR = "descendo_para_dormir"
    PERSEGUINDO_VIOLAO = "perseguindo_violao"
    GUARDANDO_VIOLAO = "guardando_violao"
    INDO_ATRAS_VIOLAO = "indo_atras_violao"
    ESCONDENDO_ATRAS_VIOLAO = "escondendo_atras_violao"
    INDO_ATRAS_ESFERA = "indo_atras_esfera"
    PERSEGUINDO_ESFERA = "perseguindo_esfera"
    COMENDO_ESFERA = "comendo_esfera"
    PERSEGUINDO_LIVRO = "perseguindo_livro"
    GUARDANDO_LIVRO = "guardando_livro"
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
        self.animacao_voando = Animacao(15, 0.20)
        self.animacao_dormindo = Animacao(1, 0.20)
        self.animacao_descendo_para_dormir = Animacao(10, 0.20)
        self.animacao_guardando_violao = Animacao(4, 0.40)
        self.animacao_comendo_esfera = Animacao(60, 0.15)

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
    def em_frente_ao_frasco(self):
        return self.maquina.eh(self.EM_FRENTE_AO_FRASCO)

    @property
    def indo_para_frasco(self):
        return self.maquina.eh(self.INDO_PARA_FRASCO)

    @property
    def descendo_para_dormir(self):
        return self.maquina.eh(self.DESCENDO_PARA_DORMIR)

    @property
    def voando(self):
        return self.maquina.eh(self.VOANDO)

    @property
    def guardando_violao(self):
        return self.maquina.eh(self.GUARDANDO_VIOLAO)

    @property
    def escondendo_atras_violao(self):
        return self.maquina.eh(self.ESCONDENDO_ATRAS_VIOLAO)

    @property
    def comendo_esfera(self):
        return self.maquina.eh(self.COMENDO_ESFERA)

    @property
    def perseguindo_violao(self):
        return self.maquina.eh(self.PERSEGUINDO_VIOLAO)

    @property
    def perseguindo_livro(self):
        return self.maquina.eh(self.PERSEGUINDO_LIVRO)

    @property
    def guardando_livro(self):
        return self.maquina.eh(self.GUARDANDO_LIVRO)

    @property
    def teleportando(self):
        return self.maquina.eh(self.TELEPORTANDO)

    @property
    def indo_atras_esfera(self):
        return self.maquina.eh(self.INDO_ATRAS_ESFERA)

    # =====================================
    # TRANSIÇÕES
    # =====================================

    def iniciar_sono(self):
        self.animacao_dormindo.reset()
        self.estado = self.DORMINDO

    def iniciar_acordar(self):
        self.estado = self.ACORDANDO

    def iniciar_em_frente_ao_frasco(self):
        self.estado = self.EM_FRENTE_AO_FRASCO

    def iniciar_descida(self):
        self.animacao_descendo_para_dormir.reset()
        self.estado = self.DESCENDO_PARA_DORMIR

    def iniciar_entrada_frasco(self):
        self.animacao_descendo_para_dormir.reset()
        self.estado = self.INDO_PARA_FRASCO

    def iniciar_voo(self):
        self.animacao_voando.reset()
        self.estado = self.VOANDO

    def iniciar_perseguindo_violao(self):
        self.estado = self.PERSEGUINDO_VIOLAO

    def iniciar_perseguindo_livro(self):
        self.estado = self.PERSEGUINDO_LIVRO

    def iniciar_guardando_violao(self):
        self.animacao_guardando_violao.reset()
        self.estado = self.GUARDANDO_VIOLAO

    def iniciar_guardando_livro(self):
        self.animacao_guardando_violao.reset()
        self.estado = self.GUARDANDO_LIVRO

    def iniciar_escondendo_atras_violao(self):
        self.estado = self.ESCONDENDO_ATRAS_VIOLAO

    def iniciar_perseguindo_esfera(self):
        self.estado = self.PERSEGUINDO_ESFERA

    def iniciar_comer_esfera(self):
        self.animacao_comendo_esfera.reset()
        self.estado = self.COMENDO_ESFERA

    def iniciar_teleportando(self):
        self.estado = self.TELEPORTANDO

    def obter_selecao_frame(self):
        if self.dormindo:
            return "dormindo", self.animacao_dormindo.frame
        if self.descendo_para_dormir:
            return "descendo_para_dormir", self.animacao_descendo_para_dormir.frame
        if self.indo_para_frasco:
            return "indo_para_frasco", self.animacao_descendo_para_dormir.frame
        if self.guardando_violao:
            return "guardando_violao", self.animacao_guardando_violao.frame
        if self.guardando_livro:
            return "guardando_livro", self.animacao_guardando_violao.frame
        if self.comendo_esfera:
            return "comendo_esfera", self.animacao_comendo_esfera.frame
        return "voando", self.animacao_voando.frame

    # =====================================
    # UPDATE
    # =====================================

    def atualizar(self, dt):
        self.maquina.atualizar(dt)
        self._atualizar_animacoes(dt)

    def _atualizar_animacoes(self, dt):
        if self.voando or self.escondendo_atras_violao or self.indo_atras_esfera:
            self.animacao_voando.atualizar(dt)
        elif self.dormindo:
            self.animacao_dormindo.atualizar(dt)
        elif self.indo_para_frasco or self.descendo_para_dormir:
            self.animacao_descendo_para_dormir.atualizar(dt)
        elif self.guardando_violao or self.guardando_livro:
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
