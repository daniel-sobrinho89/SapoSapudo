# =====================================
# entities/duende_neblina.py
# =====================================

import math
import random
import pygame

from systems.ia_duende import IADuende
from systems.animacoes_duende import AnimacoesDuende
from systems.respiracao_duende import RespiracaoDuende
from systems.animacao_folha import AnimacaoFolha
from utils.drag import iniciar_drag
from utils.drag import mover_com_offset
from systems.system_utils import atualizar_sistemas_basicos

class DuendeNeblina:

    def __init__(self):

        # =================================
        # POSIÇÃO
        # =================================

        self.x = 500
        self.y = 260

        self.base_y = self.y

        # =================================
        # SONO
        # =================================

        self.x_entrada_frasco = 0
        self.y_entrada_frasco = 0

        self.y_voo = self.y

        self.y_sono = 520

        self.velocidade_descida = 40

        self.y_sono_offset = 25

        # =================================
        # RESGTATE
        # =================================
        
        self.resgatando_violao = False

        self.retornando_violao = False

        self.violao_em_maos = False

        self.alvo_violao = None

        self.velocidade_resgate = 350

        # =================================
        # DRAG AND DROP
        # =================================

        self.arrastando = False

        self.offset_drag_x = 0
        self.offset_drag_y = 0

        self.cabeca_rect = pygame.Rect(
            0,
            0,
            0,
            0
        )

        # =================================
        # MOVIMENTO
        # =================================

        self.velocidade = 35

        self.velocidade_x = 0
        self.velocidade_y = 0

        # =================================
        # DESTINO
        # =================================

        self.alvo_x = self.x
        self.alvo_y = self.y

        self.tempo_novo_destino = 0.0

        # =================================
        # VIDA
        # =================================

        self.tempo = random.uniform(
            0,
            999
        )

        self.batimento_asas = 0.0

        self.ia = IADuende()

        self.animacoes = AnimacoesDuende()

        self.respiracao = RespiracaoDuende()

        # =================================
        # FOLHA
        # =================================

        self.animacao_folha = AnimacaoFolha()

        # =================================
        # ESCALA
        # =================================

        self.escala = 0.09

        # =================================
        # TRANSFORMAÇÃO SONO
        # =================================

        self.velocidade_transformacao_sono = 0.40

        # =================================
        # PRIMEIRO DESTINO
        # =================================

        self.escolher_novo_destino()

    # =====================================
    # NOVO DESTINO
    # =====================================

    def escolher_novo_destino(self):

        self.alvo_x = random.randint(
            180,
            1100
        )

        self.alvo_y = random.randint(
            120,
            340
        )

    # =====================================
    # ATUALIZAR MOVIMENTO
    # =====================================

    def atualizar_movimento(self, dt):

        dx = (
            self.alvo_x - self.x
        )

        dy = (
            self.alvo_y - self.y
        )

        distancia = math.hypot(
            dx,
            dy
        )

        if distancia > 1:

            dir_x = dx / distancia
            dir_y = dy / distancia

            aceleracao = 2.2

            self.velocidade_x += (
                (
                    dir_x * self.velocidade
                )
                - self.velocidade_x
            ) * aceleracao * dt

            self.velocidade_y += (
                (
                    dir_y * self.velocidade
                )
                - self.velocidade_y
            ) * aceleracao * dt

        self.x += (
            self.velocidade_x * dt
        )

        self.y += (
            self.velocidade_y * dt
        )

    # =====================================
    # DENTRO DO VIDRO
    # =====================================

    def esta_dentro_do_frasco(
        self,
        area_frasco
    ):
        return area_frasco.collidepoint(
            int(self.x),
            int(self.y)
        )

    # =====================================
    # AÇÕES MOUSE
    # =====================================

    def iniciar_arraste(
        self,
        mouse_x,
        mouse_y
    ):
        self.arrastando = True

        self.offset_drag_x, self.offset_drag_y = iniciar_drag(
            self.x,
            self.y,
            mouse_x,
            mouse_y
        )

    def mover_arraste(
        self,
        mouse_x,
        mouse_y
    ):
        if not self.arrastando:
            return

        self.x, self.y = mover_com_offset(
            mouse_x,
            mouse_y,
            self.offset_drag_x,
            self.offset_drag_y
        )

    def finalizar_arraste(self):
        self.arrastando = False

    def atualizar_hitboxes(
        self,
        head_x,
        head_y,
        head_width,
        head_height
    ):
        self.cabeca_rect.update(
            int(head_x - head_width * 0.15),
            int(head_y - head_height * 0.15),
            int(head_width * 0.30),
            int(head_height * 0.30)
        )

    # =====================================
    # RESGATE VIOLÃO
    # =====================================

    def pode_resgatar_violao(self):

        return (
            not self.animacoes.dormindo
            and not self.animacoes.indo_para_frasco
            and not self.animacoes.descendo_para_dormir
            and not self.animacoes.acordando
            and not self.animacoes.ciclo_sono.dormir_por_tempo
            and not self.arrastando
        )

    def iniciar_resgate_violao(self, violao):

        self.resgatando_violao = True

        self.retornando_violao = False

        self.violao_em_maos = False

        self.alvo_violao = violao

    def consegue_alcancar_antes_da_queda(self, violao):

        distancia = math.hypot(
            violao.x - self.x,
            violao.y - self.y
        )

        tempo_voo = (
            distancia
            / self.velocidade_resgate
        )

        altura_restante = max(
            1,
            violao.chao_y - violao.y
        )

        gravidade = 900

        tempo_queda = math.sqrt(
            (2 * altura_restante)
            / gravidade
        )

        return tempo_voo < tempo_queda

    def teleportar_para_violao(self, violao):

        self.x = violao.x

        self.y = violao.y - 40

    def atualizar_resgate(self, dt):

        if not self.resgatando_violao:
            return False

        violao = self.alvo_violao

        if violao is None:
            return False

        # ===================
        # INDO BUSCAR
        # ===================

        if not self.violao_em_maos:

            dx = violao.x - self.x
            dy = violao.y - self.y

            distancia = math.hypot(dx, dy)

            if distancia < 60:

                self.violao_em_maos = True

                violao.caindo = False

                return True

            self.x += (
                dx / max(1, distancia)
            ) * self.velocidade_resgate * dt

            self.y += (
                dy / max(1, distancia)
            ) * self.velocidade_resgate * dt

            return True

        # ===================
        # LEVANDO PARA CASA
        # ===================

        destino_x = violao.x_inicial
        destino_y = violao.y_inicial

        dx = destino_x - self.x
        dy = destino_y - self.y

        distancia = math.hypot(dx, dy)

        violao.x = self.x
        violao.y = self.y

        if distancia < 15:

            violao.voltar_origem()

            self.resgatando_violao = False

            self.violao_em_maos = False

            self.alvo_violao = None

            return True

        self.x += (
            dx / max(1, distancia)
        ) * self.velocidade_resgate * dt

        self.y += (
            dy / max(1, distancia)
        ) * self.velocidade_resgate * dt

        return True

    # =====================================
    # AUXILIARES ATUALIZAÇÃO
    # =====================================

    def _atualizar_sistemas(
        self,
        dt,
        clima_service,
        frasco_rect,
        ambiente
    ):
        atualizar_sistemas_basicos(
            self.animacoes,
            self.respiracao,
            self.animacao_folha,
            dt,
            ambiente,
            entity=self,
            clima_service=clima_service,
            frasco_rect=frasco_rect
        )

    def _atualizar_fator_sono_visual(
        self,
        dt
    ):
        if self.animacoes.dormindo:

            self.animacoes.fator_sono_visual = min(
                1.0,
                self.animacoes.fator_sono_visual
                + (0.25 * dt)
            )

        else:

            self.animacoes.fator_sono_visual = max(
                0.0,
                self.animacoes.fator_sono_visual
                - (0.50 * dt)
            )

    def _atualizar_estado_dormindo(
        self,
        dt,
        clima_service,
        frasco_rect
    ):
        self.y = self.y_sono

        self.velocidade_x = 0
        self.velocidade_y = 0

        self.animacoes.atualizar_sono_programado(
            dt,
            self,
            clima_service.clima_disponivel,
            frasco_rect
        )
    
    def _atualizar_ia(
        self,
        dt,
        sapo_x,
        sapo_y,
        pote_x,
        pote_y
    ):
        acao = self.ia.obter_acao(dt)

        if acao == self.ia.OBSERVANDO_SAPO:

            self.alvo_x = (
                sapo_x
                + random.randint(-60, 60)
            )

            self.alvo_y = (
                sapo_y
                - 180
                + random.randint(-40, 40)
            )

        elif acao == self.ia.OBSERVANDO_POTE:

            self.alvo_x = (
                pote_x
                + random.randint(-40, 40)
            )

            self.alvo_y = (
                pote_y
                - 120
                + random.randint(-40, 40)
            )

        elif acao == self.ia.ORBITANDO:

            self.ia.orbita_angulo += dt * 1.8

            self.alvo_x = (
                sapo_x
                + math.cos(
                    self.ia.orbita_angulo
                ) * self.ia.orbita_raio
            )

            self.alvo_y = (
                sapo_y
                - 140
                + math.sin(
                    self.ia.orbita_angulo
                ) * 35
            )

        elif acao == self.ia.FUGINDO:

            self.alvo_x = random.randint(
                80,
                1150
            )

            self.alvo_y = random.randint(
                50,
                220
            )
    
    def _atualizar_entrada_frasco(
        self,
        dt
    ):
        if not self.animacoes.indo_para_frasco:
            return False

        dx = (
            self.x_entrada_frasco
            - self.x
        )

        dy = (
            self.y_entrada_frasco
            - self.y
        )

        distancia = math.hypot(
            dx,
            dy
        )

        velocidade_base = 30

        velocidade_aproximacao = min(
            50,
            velocidade_base
            + distancia * 0.15
        )

        if distancia > 5:

            self.x += (
                dx / distancia
            ) * velocidade_aproximacao * dt

            self.y += (
                dy / distancia
            ) * velocidade_aproximacao * dt

            self.batimento_asas = math.sin(
                self.tempo * 10
            )

        else:

            self.animacoes.iniciar_descida()

        return True

    def _atualizar_descida_sono(
        self,
        dt
    ):
        if not self.animacoes.descendo_para_dormir:
            return False

        self.y += (
            self.velocidade_descida * dt
        )

        altura_restante = max(
            0,
            self.y_sono - self.y
        )

        fator_voo = max(
            0,
            min(
                1,
                altura_restante / 80
            )
        )

        self.y += (
            math.sin(self.tempo * 8)
            * fator_voo
        )

        self.velocidade_x *= 0.95
        self.velocidade_y *= 0.95

        self.batimento_asas = math.sin(
            self.tempo * 8.0
        )

        if self.y >= self.y_sono:

            self.y = self.y_sono

            self.animacoes.iniciar_sono()

            self.velocidade_x = 0
            self.velocidade_y = 0

            self.batimento_asas = 0

        return True

    def _atualizar_destino_livre(
        self,
        dt
    ):
        self.tempo_novo_destino += dt

        if self.tempo_novo_destino >= random.uniform(
            3.0,
            6.0
        ):

            self.tempo_novo_destino = 0.0

            self.escolher_novo_destino()
            
    def _atualizar_flutuacao(
        self,
        dt
    ):
        if self.animacoes.dormindo:

            self.y = self.y_sono

            return

        flutuacao = (
            math.sin(self.tempo * 1.8) * 10
            +
            math.sin(self.tempo * 0.6) * 4
        )

        self.y += flutuacao * dt * 8

    def _atualizar_batimento_asas(self):

        velocidade_real = math.hypot(
            self.velocidade_x,
            self.velocidade_y
        )

        intensidade_batida = (
            7.5
            + (
                velocidade_real * 0.05
            )
        )

        self.batimento_asas = math.sin(
            self.tempo
            * intensidade_batida
        )

    # =====================================
    # UPDATE
    # =====================================

    def atualizar(
        self,
        dt,
        sapo_x,
        sapo_y,
        pote_x,
        pote_y,
        clima_service,
        frasco_rect,
        ambiente
    ):

        self.tempo += dt

        if self.atualizar_resgate(dt):
            return

        if self.arrastando:

            self.velocidade_x = 0
            self.velocidade_y = 0

            return

        self._atualizar_sistemas(
            dt,
            clima_service,
            frasco_rect,
            ambiente
        )

        self._atualizar_fator_sono_visual(dt)

        if self.animacoes.dormindo:

            self._atualizar_estado_dormindo(
                dt,
                clima_service,
                frasco_rect
            )

            return

        self._atualizar_ia(
            dt,
            sapo_x,
            sapo_y,
            pote_x,
            pote_y
        )

        if self._atualizar_entrada_frasco(dt):
                return
        
        if self._atualizar_descida_sono(dt):
            return

        self._atualizar_destino_livre(dt)

        self.atualizar_movimento(dt)

        self._atualizar_flutuacao(dt)

        self._atualizar_batimento_asas()