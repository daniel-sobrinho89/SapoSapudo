# =====================================
# systems/duende/gestor_sono_duende.py
# =====================================

import math


class GestorSonoDuende:
    """
    Gerencia a lógica de descida e entrada no frasco do Duende.
    """

    def __init__(self):
        self.x_entrada_frasco = 0
        self.y_entrada_frasco = 0
        self.y_sono = 520
        self.velocidade_descida = 40
        self.escala_visual = 1.0

    def atualizar_entrada_frasco(self, dt, entity, animacoes):
        if not animacoes.indo_para_frasco:
            return False

        dx = self.x_entrada_frasco - entity.x
        dy = self.y_entrada_frasco - entity.y
        distancia = math.hypot(dx, dy)

        velocidade_base = 30
        velocidade_aproximacao = min(50, velocidade_base + distancia * 0.15)

        if distancia > 5:
            entity.x += (dx / distancia) * velocidade_aproximacao * dt
            entity.y += (dy / distancia) * velocidade_aproximacao * dt
        else:
            animacoes.iniciar_descida()

        if distancia < 60:
            self.escala_visual = max(0.90, self.escala_visual - dt * 0.6)

        return True

    def atualizar_descida_sono(self, dt, entity, animacoes, tempo):
        if not animacoes.descendo_para_dormir:
            return False

        entity.y += self.velocidade_descida * dt
        altura_restante = max(0, self.y_sono - entity.y)
        fator_voo = max(0, min(1, altura_restante / 80))

        entity.y += math.sin(tempo * 8) * fator_voo

        # Reduz velocidade residual
        entity.velocidade_x *= 0.95
        entity.velocidade_y *= 0.95

        if entity.y >= self.y_sono:
            entity.y = self.y_sono
            animacoes.iniciar_sono()
            entity.velocidade_x = 0
            entity.velocidade_y = 0

        return True

    def atualizar_fator_visual(self, dt, animacoes, esta_perto_frasco):
        if (
            not animacoes.indo_para_frasco
            and not animacoes.descendo_para_dormir
            and not animacoes.dormindo
            and not esta_perto_frasco
        ):
            self.escala_visual = min(1.0, self.escala_visual + dt * 0.6)

        if animacoes.dormindo:
            animacoes.fator_sono_visual = min(
                1.0, animacoes.fator_sono_visual + (0.25 * dt)
            )
        else:
            animacoes.fator_sono_visual = max(
                0.0, animacoes.fator_sono_visual - (0.50 * dt)
            )
