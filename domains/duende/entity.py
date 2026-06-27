# =====================================
# entities/duende_neblina.py
# =====================================

import math
import random

import kivy_adapter
from core.event_bus import event_bus
from core.system_utils import atualizar_sistemas_basicos
from domains.duende.animacoes import AnimacoesDuende
from domains.duende.arraste_duende import ArrasteDuende
from domains.duende.gestor_sono_duende import GestorSonoDuende
from domains.duende.ia import IADuende
from domains.duende.resgate_duende import ResgateDuende
from domains.duende.respiracao import RespiracaoDuende

# Novos componentes
from domains.duende.teleporte_duende import TeleporteDuende


class DuendeNeblina:
    def __init__(self):
        # =================================
        # POSIÇÃO E ESTADO BÁSICO
        # =================================
        self.x = 500
        self.y = 260
        self.base_y = self.y
        self.velocidade = 35
        self.velocidade_x = 0
        self.velocidade_y = 0
        self.alvo_x = self.x
        self.alvo_y = self.y
        self.tempo_novo_destino = 0.0
        self.tempo = random.uniform(0, 999)
        self.escala = 0.40
        self.alpha_visual = 255
        self.escala_visual = 1.0

        # =================================
        # COMPONENTES
        # =================================
        self.ia = IADuende()
        self.animacoes = AnimacoesDuende()
        self.respiracao = RespiracaoDuende()
        self.teleporte = TeleporteDuende()
        self.resgate = ResgateDuende()
        self.arraste = ArrasteDuende()
        self.sono = GestorSonoDuende()

        # =================================
        # HITBOXES
        # =================================
        self.corpo_rect = kivy_adapter.Rect(0, 0, 0, 0)
        self.cabeca_rect = kivy_adapter.Rect(0, 0, 0, 0)

        self.escolher_novo_destino()
        event_bus.assinar("violao_solto", self.decidir_forma_resgatar_violao)

    @property
    def arrastando(self):
        return self.arraste.ativo

    @property
    def resgatando_violao(self):
        return self.resgate.ativo

    @property
    def teleportando(self):
        return self.teleporte.ativo

    def escolher_novo_destino(self):
        self.alvo_x = random.randint(180, 1100)
        self.alvo_y = random.randint(120, 340)

    def atualizar_movimento(self, dt):
        dx = self.alvo_x - self.x
        dy = self.alvo_y - self.y
        distancia = math.hypot(dx, dy)

        if distancia > 1:
            dir_x = dx / distancia
            dir_y = dy / distancia
            aceleracao = 2.2
            self.velocidade_x += (
                ((dir_x * self.velocidade) - self.velocidade_x) * aceleracao * dt
            )
            self.velocidade_y += (
                ((dir_y * self.velocidade) - self.velocidade_y) * aceleracao * dt
            )

        self.x += self.velocidade_x * dt
        self.y += self.velocidade_y * dt

    def esta_dentro_do_frasco(self, area_frasco):
        return area_frasco.collidepoint(int(self.x), int(self.y))

    # =====================================
    # INTERAÇÃO (Delegação)
    # =====================================
    def iniciar_arraste(self, mouse_x, mouse_y):
        self.arraste.iniciar(self.x, self.y, mouse_x, mouse_y)

    def mover_arraste(self, mouse_x, mouse_y):
        self.arraste.mover(mouse_x, mouse_y, self)

    def finalizar_arraste(self, frasco_rect=None):
        self.arraste.finalizar(self.x, self.y, frasco_rect)

    def processar_toque_down(self, pos_virtual):
        return self.arraste.processar_toque_down(
            pos_virtual, self.corpo_rect, self.x, self.y
        )

    def processar_toque_move(self, pos_virtual):
        return self.arraste.processar_toque_move(pos_virtual, self)

    def processar_toque_up(self, frasco_rect):
        return self.arraste.processar_toque_up(
            frasco_rect, self.x, self.y, self.animacoes, self.escolher_novo_destino
        )

    def atualizar_hitboxes(self, body_x, body_y, body_width, body_height):
        cabeca_w = int(body_width * 0.30)
        cabeca_h = int(body_height * 0.30)
        cabeca_x = int(body_x - cabeca_w / 2)
        cabeca_y = int(body_y - body_height * 0.25 - cabeca_h / 2)
        self.cabeca_rect.update(cabeca_x, cabeca_y, cabeca_w, cabeca_h)
        self.corpo_rect.update(
            body_x - body_width // 2, body_y - body_height // 2, body_width, body_height
        )

    # =====================================
    # RESGATE (Delegação)
    # =====================================
    def decidir_forma_resgatar_violao(self, evento):
        if self.teleportando or self.resgatando_violao:
            return

        estado = evento.estado

        if not self.pode_resgatar_violao():
            return

        distancia = abs(estado.x - self.x)

        MIN_TELEPORT_DIST = 120

        if (
            not self.consegue_alcancar_antes_da_queda(estado)
            and distancia > MIN_TELEPORT_DIST
        ):
            self.teleportar_para_violao(estado)
            return

        self.iniciar_resgate_violao(estado)

    def pode_resgatar_violao(self):
        return (
            self.resgate.pode_resgatar(
                self.animacoes,
                self.arrastando,
            )
            and not self.teleportando
        )

    def iniciar_resgate_violao(self, _estado_violao):
        self.resgate.iniciar()

    def consegue_alcancar_antes_da_queda(self, estado_violao):
        return self.resgate.consegue_alcancar(
            self.x,
            self.y,
            estado_violao,
        )

    def teleportar_para_violao(self, estado_violao):
        self.teleporte.iniciar(
            estado_violao.x,
            estado_violao.y,
            self.resgate.violao_monitorado,
        )

    # =====================================
    # MÉTODOS PRIVADOS DE ATUALIZAÇÃO
    # =====================================
    def _atualizar_sistemas(self, dt, clima_service, frasco_rect, ambiente):
        atualizar_sistemas_basicos(
            self.animacoes,
            self.respiracao,
            dt,
            ambiente,
            entity=self,
            clima_service=clima_service,
            frasco_rect=frasco_rect,
        )

    def _atualizar_ia(self, dt, sapo_x, sapo_y, pote_x, pote_y):
        acao = self.ia.obter_acao(dt)
        if acao == self.ia.OBSERVANDO_SAPO:
            self.alvo_x = sapo_x + random.randint(-60, 60)
            self.alvo_y = sapo_y - 180 + random.randint(-40, 40)
        elif acao == self.ia.OBSERVANDO_POTE:
            self.alvo_x = pote_x + random.randint(-40, 40)
            self.alvo_y = pote_y - 120 + random.randint(-40, 40)
        elif acao == self.ia.ORBITANDO:
            self.ia.orbita_angulo += dt * 1.8
            self.alvo_x = sapo_x + math.cos(self.ia.orbita_angulo) * self.ia.orbita_raio
            self.alvo_y = sapo_y - 140 + math.sin(self.ia.orbita_angulo) * 35
        elif acao == self.ia.FUGINDO:
            self.alvo_x = random.randint(80, 1150)
            self.alvo_y = random.randint(50, 220)

    def _atualizar_destino_livre(self, dt):
        self.tempo_novo_destino += dt
        if self.tempo_novo_destino >= random.uniform(3.0, 6.0):
            self.tempo_novo_destino = 0.0
            self.escolher_novo_destino()

    def _atualizar_flutuacao(self, dt):
        if self.animacoes.dormindo:
            self.y = self.sono.y_sono
            return
        flutuacao = math.sin(self.tempo * 1.8) * 10 + math.sin(self.tempo * 0.6) * 4
        self.y += flutuacao * dt * 8

    # =====================================
    # UPDATE PRINCIPAL
    # =====================================
    def atualizar(self, dt, sapo, pote_x, pote_y, clima_service, frasco_rect, ambiente):
        self.tempo += dt

        # 1. Teleporte (bloqueia o resto)
        if self.teleporte.atualizar(dt, self):
            self.alpha_visual = self.teleporte.alpha_visual
            self.escala_visual = self.teleporte.escala_visual
            return

        # 2. Resgate (bloqueia o resto)
        if self.resgate.atualizar(dt, self):
            return

        # 3. Arraste (bloqueia movimento livre)
        if self.arrastando:
            self.velocidade_x = 0
            self.velocidade_y = 0
            return

        self._atualizar_sistemas(dt, clima_service, frasco_rect, ambiente)

        # 4. Clima / Sono
        if (
            self.animacoes.dormindo
            and clima_service.clima_disponivel
            and not self.animacoes.ciclo_sono.dormir_por_tempo
        ):
            self.animacoes.iniciar_acordar()

        self.sono.atualizar_fator_visual(
            dt, self.animacoes, self.esta_dentro_do_frasco(frasco_rect)
        )

        # Sincroniza escala visual com componentes
        if self.animacoes.indo_para_frasco or self.animacoes.descendo_para_dormir:
            self.escala_visual = self.sono.escala_visual
        else:
            self.sono.escala_visual = self.escala_visual

        if self.animacoes.dormindo:
            self.y = self.sono.y_sono
            self.velocidade_x = 0
            self.velocidade_y = 0
            self.animacoes.atualizar_sono_programado(
                dt, self, clima_service.clima_disponivel, frasco_rect
            )
            self.resgate.verificado_apos_acordar = False
            return

        # 5. IA e Movimento Livre
        self._atualizar_ia(dt, sapo.x, sapo.y, pote_x, pote_y)

        # Transições de sono
        self.sono.x_entrada_frasco = frasco_rect.centerx
        self.sono.y_entrada_frasco = frasco_rect.top - 30

        if self.sono.atualizar_entrada_frasco(dt, self, self.animacoes):
            return

        if self.sono.atualizar_descida_sono(dt, self, self.animacoes, self.tempo):
            return

        self._atualizar_destino_livre(dt)
        self.atualizar_movimento(dt)
        self._atualizar_flutuacao(dt)

        # Verificação pós-sono
        if (
            not self.resgate.verificado_apos_acordar
            and not self.animacoes.dormindo
            and self.animacoes.fator_sono_visual <= 0.05
        ):
            self.resgate.verificado_apos_acordar = True
            self.resgate.verificar_apos_acordar(sapo)

        # Escala visual final perto do frasco
        if self.esta_dentro_do_frasco(frasco_rect) and (
            self.animacoes.descendo_para_dormir or self.arraste.soltou_frente_pote
        ):
            self.escala_visual = max(0.20, self.escala_visual - dt * 0.6)
        else:
            self.escala_visual = min(1.0, self.escala_visual + dt * 0.6)
