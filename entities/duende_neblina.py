# =====================================
# entities/duende_neblina.py
# =====================================

import math
import random
import pygame

from systems.ia_duende import IADuende
from systems.animacoes_duende import AnimacoesDuende
from systems.respiracao_duende import RespiracaoDuende
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

        self.escala_visual = 1.0

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

        self.offset_violao_x = 0
        self.offset_violao_y = 15

        self.resgate_verificado_apos_acordar = False
        self.violao_monitorado = None

        self.teleportando = False

        self.teleporte_fase = "sumindo"

        self.teleporte_tempo = 0.0

        self.teleporte_duracao = 0.35

        self.teleporte_destino_x = 0
        self.teleporte_destino_y = 0

        self.teleporte_violao_alvo = None

        self.alpha_visual = 255

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

        self.ia = IADuende()

        self.animacoes = AnimacoesDuende()

        self.respiracao = RespiracaoDuende()

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

    def finalizar_arraste(self, frasco_rect=None):
        self.arrastando = False

        # se foi solto em frente ao pote (dentro da área), sinaliza para reduzir
        if frasco_rect is not None and self.esta_dentro_do_frasco(frasco_rect):
            self.solta_frente_pote = True
        else:
            self.solta_frente_pote = False

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
            and not self.animacoes.descendo_para_dormir
            and not self.animacoes.ciclo_sono.dormir_por_tempo
            and not self.arrastando
            and not self.resgatando_violao
        )

    def iniciar_teleporte(
        self,
        destino_x,
        destino_y
    ):

        self.teleportando = True

        self.teleporte_fase = "sumindo"

        self.teleporte_tempo = 0

        self.teleporte_destino_x = destino_x

        self.teleporte_destino_y = destino_y

    def atualizar_teleporte(self, dt):

        if not self.teleportando:
            return False

        self.teleporte_tempo += dt

        progresso = (
            self.teleporte_tempo
            / self.teleporte_duracao
        )

        # =====================
        # SUMINDO
        # =====================

        if self.teleporte_fase == "sumindo":

            self.alpha_visual = int(
                255 * (1 - progresso)
            )

            self.escala_visual = (
                1.0
                - (progresso * 0.4)
            )

            if progresso >= 1:

                if (
                    self.teleporte_violao_alvo
                    and self.teleporte_violao_alvo.caindo
                ):

                    violao = self.teleporte_violao_alvo

                    queda_prevista = (
                        violao.velocidade_queda
                        * self.teleporte_duracao
                    )

                    destino_y = min(
                        violao.chao_y - 90,
                        violao.y + queda_prevista + 70
                    )

                    self.x = violao.x

                    self.y = destino_y

                else:

                    self.x = (
                        self.teleporte_destino_x
                    )

                    self.y = (
                        self.teleporte_destino_y
                    )

                self.teleporte_fase = "aparecendo"

                self.teleporte_tempo = 0

        # =====================
        # APARECENDO
        # =====================

        else:

            self.alpha_visual = int(
                255 * progresso
            )

            self.escala_visual = (
                0.6
                + (progresso * 0.4)
            )

            if progresso >= 1:

                self.alpha_visual = 255

                self.escala_visual = 1.0

                self.teleportando = False

                self.teleporte_violao_alvo = None

        return True


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

        gravidade = 900

        altura_restante = max(
            1,
            violao.chao_y - violao.y
        )

        velocidade_queda = max(
            0,
            violao.velocidade_queda
        )

        if velocidade_queda > 0:

            tempo_queda = (
                altura_restante
                / velocidade_queda
            )

        else:

            tempo_queda = math.sqrt(
                (2 * altura_restante)
                / gravidade
            )

        tempo_queda *= 0.75

        if velocidade_queda > 250:
            tempo_queda *= 0.6

        return tempo_voo < tempo_queda

    def teleportar_para_violao(
        self,
        violao
    ):

        self.teleporte_violao_alvo = violao

        self.iniciar_teleporte(
            violao.x,
            violao.y
        )

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

            if distancia < 80:

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

        violao.x = (
            self.x
            + self.offset_violao_x
        )

        violao.y = (
            self.y
            + self.offset_violao_y
        )
        
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

    def verificar_violao_apos_acordar(self, sapo):

        violao = self.violao_monitorado

        if violao is None:
            return

        if sapo.animacoes.tocando_violao:
            return

        tolerancia = 10

        fora_do_lugar = (
            abs(violao.x - violao.x_inicial)
            > tolerancia
            or
            abs(violao.y - violao.y_inicial)
            > tolerancia
        )

        if fora_do_lugar:

            self.iniciar_resgate_violao(
                violao
            )

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
            dt,
            ambiente,
            entity=self,
            clima_service=clima_service,
            frasco_rect=frasco_rect
        )

    def _atualizar_fator_sono_visual(
        self,
        dt,
        sapo
    ):
        
        if (
            not self.animacoes.indo_para_frasco
            and not self.animacoes.descendo_para_dormir
            and not self.animacoes.dormindo
            and not self.esta_dentro_do_frasco(
                self.area_frasco_atual
            )
        ):
            self.escala_visual = min(
                1.0,
                self.escala_visual + dt * 0.6
            )

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

            if (
                not self.resgate_verificado_apos_acordar
                and not self.animacoes.dormindo
                and self.animacoes.fator_sono_visual <= 0.05
            ):
                self.resgate_verificado_apos_acordar = True

                self.verificar_violao_apos_acordar(sapo)

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

        self.resgate_verificado_apos_acordar = False

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

        else:

            self.animacoes.iniciar_descida()

        if distancia < 60:

            self.escala_visual = max(
                0.90,
                self.escala_visual - dt * 0.6
            )

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


        if self.y >= self.y_sono:

            self.y = self.y_sono

            self.animacoes.iniciar_sono()

            self.velocidade_x = 0
            self.velocidade_y = 0

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

    # =====================================
    # UPDATE
    # =====================================

    def atualizar(
        self,
        dt,
        sapo,
        pote_x,
        pote_y,
        clima_service,
        frasco_rect,
        ambiente
    ):

        self.tempo += dt

        if self.atualizar_teleporte(dt):
            return

        self.area_frasco_atual = frasco_rect

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

        # Se estava dormindo por falta de clima e o clima voltou, iniciar acordar
        if getattr(self, 'animacoes', None) is not None and self.animacoes.dormindo:
            if clima_service.clima_disponivel and not self.animacoes.ciclo_sono.dormir_por_tempo:
                self.animacoes.iniciar_acordar()

        self._atualizar_fator_sono_visual(dt, sapo)

        if self.animacoes.dormindo:

            self._atualizar_estado_dormindo(
                dt,
                clima_service,
                frasco_rect
            )

            return

        self._atualizar_ia(
            dt,
            sapo.x,
            sapo.y,
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

        if (
            self.esta_dentro_do_frasco(frasco_rect)
            and (
                self.animacoes.descendo_para_dormir
                or getattr(self, 'solta_frente_pote', False)
            )
        ):

            self.escala_visual = max(
                0.20,
                self.escala_visual - dt * 0.6
            )

        else:

            self.escala_visual = min(
                1.0,
                self.escala_visual + dt * 0.6
            )