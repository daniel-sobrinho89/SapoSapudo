# =====================================
# entities/duende_neblina.py
# =====================================

import math
import random

import kivy_adapter
from domains.duende.animacoes import AnimacoesDuende
from domains.duende.arraste_duende import ArrasteDuende
from domains.duende.ia import IADuende

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
        self.movimento_bloqueado = False
        self.iniciar_resgate_monitorado = False
        # =================================
        # COMPONENTES
        # =================================
        self.ia = IADuende()
        self.animacoes = AnimacoesDuende()
        self.teleporte = TeleporteDuende()
        self.arraste = ArrasteDuende()

        # =================================
        # HITBOXES
        # =================================
        self.corpo_rect = kivy_adapter.Rect(0, 0, 0, 0)
        self.cabeca_rect = kivy_adapter.Rect(0, 0, 0, 0)

        self.escolher_novo_destino()

    @property
    def arrastando(self):
        return self.arraste.ativo

    @property
    def teleportando(self):
        return self.teleporte.ativo

    def escolher_novo_destino(self):
        self.alvo_x = random.randint(180, 1100)
        self.alvo_y = random.randint(120, 340)

    def atualizar_movimento(self, dt):
        if self.movimento_bloqueado or self.teleporte.ativo or self.arraste.ativo:
            return

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

    def violao_sendo_arrastado(self):
        return self.arraste.ativo

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
    # MÉTODOS PRIVADOS DE ATUALIZAÇÃO
    # =====================================

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
            return
        flutuacao = math.sin(self.tempo * 1.8) * 10 + math.sin(self.tempo * 0.6) * 4
        self.y += flutuacao * dt * 8

    # =====================================
    # UPDATE PRINCIPAL
    # =====================================
    def atualizar(self, dt, sapo, pote_x, pote_y, clima_service, frasco_rect):
        self.tempo += dt

        # 3. Arraste (bloqueia movimento livre)
        if self.arrastando:
            self.velocidade_x = 0
            self.velocidade_y = 0
            return

        self.animacoes.atualizar(dt)

        # 5. IA e Movimento Livre
        if not self.movimento_bloqueado and not self.teleporte.ativo:
            self._atualizar_ia(dt, sapo.x, sapo.y, pote_x, pote_y)

            self._atualizar_destino_livre(dt)
            self.atualizar_movimento(dt)
            self._atualizar_flutuacao(dt)
