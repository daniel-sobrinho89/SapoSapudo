# =====================================
# entities/duende_neblina.py
# =====================================

import math
import random

import kivy_adapter
from domains.duende.animacoes import AnimacoesDuende
from domains.duende.arraste_duende import ArrasteDuende

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
        self.percentual_visivel = 1.0
        self.escala_visual = 0.9
        self.y_descida_casa = 275
        self.altura_render = 0
        self.velodidade_descina_sono = 40
        self.movimento_bloqueado = False
        self.carregado = False
        self.fluxo_sono_iniciado = False
        self.cor = (255, 255, 255)
        # =================================
        # COMPONENTES
        # =================================
        self.animacoes = AnimacoesDuende()
        self.teleporte = TeleporteDuende()
        self.arraste = ArrasteDuende()

        # =================================
        # HITBOXES
        # =================================
        self.corpo_rect = kivy_adapter.Rect(0, 0, 0, 0)
        self.cabeca_rect = kivy_adapter.Rect(0, 0, 0, 0)

    @property
    def arrastando(self):
        return self.arraste.ativo

    def esta_dentro_da_casa(self, area_casa):
        return area_casa.collidepoint(int(self.x), int(self.y))

    # =====================================
    # INTERAÇÃO (Delegação)
    # =====================================
    def iniciar_arraste(self, mouse_x, mouse_y):
        self.arraste.iniciar(self.x, self.y, mouse_x, mouse_y)

    def mover_arraste(self, mouse_x, mouse_y):
        self.arraste.mover(mouse_x, mouse_y, self)

    def finalizar_arraste(self, casa_duende_rect=None):
        self.arraste.finalizar(self.x, self.y, casa_duende_rect)

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
    def _atualizar_destino_livre(self, dt):
        self.tempo_novo_destino += dt
        if self.tempo_novo_destino >= random.uniform(3.0, 6.0):
            self.tempo_novo_destino = 0.0
            self.escolher_novo_destino()

    def _atualizar_movimento(self, dt):
        if self.arraste.ativo:
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

    def _atualizar_flutuacao(self, dt):
        flutuacao = math.sin(self.tempo * 1.8) * 10 + math.sin(self.tempo * 0.6) * 4
        self.y += flutuacao * dt * 8

    def mover(self, dx, dy, distancia, dt, velocidade):
        self.x += (dx / max(1, distancia)) * velocidade * dt
        self.y += (dy / max(1, distancia)) * velocidade * dt
        self.base_y = self.y

    def duplicar(self):
        novo = DuendeNeblina()

        novo.cor = (200, 235, 255)

        novo.x = self.x
        novo.y = self.y
        novo.base_y = self.base_y

        novo.escala_visual = self.escala_visual
        novo.escala = self.escala

        novo.alpha_visual = self.alpha_visual

        novo.velocidade_x = 0
        novo.velocidade_y = 0

        novo.iniciar_saida_casa()

        return novo

    def resetar_escala_visual(self):
        self.escala_visual = 0.9

    # =====================================
    # UPDATE PRINCIPAL
    # =====================================
    def atualizar(self, dt):
        self.tempo += dt

        # 3. Arraste (bloqueia movimento livre)
        if self.arrastando:
            self.velocidade_x = 0
            self.velocidade_y = 0
            return

        self.animacoes.atualizar(dt)

        if self.animacoes.teleportando:
            self._atualizar_teleporte(dt)
            return

        # 5. e Movimento Livre
        if not self.movimento_bloqueado and not self.animacoes.teleportando:
            self._atualizar_destino_livre(dt)
            self._atualizar_movimento(dt)
            self._atualizar_flutuacao(dt)

    def iniciar_saida_casa(self):
        self.animacoes.iniciar_saindo_da_casa()
        self.movimento_bloqueado = True

    def iniciar_voo(self):
        self.animacoes.iniciar_voo()
        self.movimento_bloqueado = False
        self.fluxo_sono_iniciado = False
        self.percentual_visivel = 1.0
        self.resetar_escala_visual()

    def escolher_novo_destino(self):
        self.alvo_x = random.randint(180, 1100)
        self.alvo_y = random.randint(120, 340)

    def teleportar(
        self,
        destino_x=None,
        destino_y=None,
        ao_teleportar=None,
        ao_finalizar=None,
        duracao=None,
        duracao_sumido=None,
    ):
        self.animacoes.iniciar_teleportando()
        self.teleporte.iniciar(
            destino_x,
            destino_y,
            ao_teleportar,
            ao_finalizar,
            duracao,
            duracao_sumido,
        )

    def _atualizar_teleporte(self, dt):
        if not (self.teleporte.atualizar(dt, self)):
            self.alpha_visual = self.teleporte.alpha_visual
            self.escala_visual = self.teleporte.escala_visual
        else:
            self.alpha_visual = 255
            self.animacoes.iniciar_voo()
