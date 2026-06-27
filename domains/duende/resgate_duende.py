# =====================================
# domains.duende/resgate_duende.py
# =====================================

import math


class ResgateDuende:
    """
    Gerencia o sistema de resgate do violão pelo Duende.
    """

    def __init__(self):
        self.ativo = False
        self.violao_em_maos = False
        self.velocidade = 450
        self.offset_x = 0
        self.offset_y = 15

        self.verificado_apos_acordar = False
        self.violao_monitorado = None

    def pode_resgatar(self, animacoes, arrastando):
        return (
            not animacoes.dormindo
            and not animacoes.descendo_para_dormir
            and not animacoes.ciclo_sono.dormir_por_tempo
            and not arrastando
            and not self.ativo
        )

    def iniciar(self):
        self.ativo = True
        self.violao_em_maos = False

    def consegue_alcancar(self, duende_x, duende_y, violao):
        distancia = math.hypot(violao.x - duende_x, violao.y - duende_y)
        tempo_voo = distancia / self.velocidade

        gravidade = 900
        altura_restante = max(1, violao.chao_y - violao.y)
        velocidade_queda = max(0, violao.velocidade_queda)

        if velocidade_queda > 0:
            tempo_queda = altura_restante / velocidade_queda
        else:
            tempo_queda = math.sqrt((2 * altura_restante) / gravidade)

        tempo_queda *= 0.75
        if velocidade_queda > 250:
            tempo_queda *= 0.6

        return tempo_voo < tempo_queda

    def atualizar(self, dt, entity):
        if not self.ativo:
            return False

        violao = self.violao_monitorado

        if violao is None:
            return False

        if not self.violao_em_maos:
            alvo_x = violao.x
            alvo_y = violao.y

            dx = alvo_x - entity.x
            dy = alvo_y - entity.y
            distancia = math.hypot(alvo_x - entity.x, alvo_y - entity.y)

            DISTANCIA_PEGAR = 18
            if distancia <= DISTANCIA_PEGAR:
                self.violao_em_maos = True
                violao.caindo = False
                violao.x = entity.x + self.offset_x
                violao.y = entity.y + self.offset_y

                return True

            entity.x += (dx / max(1, distancia)) * self.velocidade * dt
            entity.y += (dy / max(1, distancia)) * self.velocidade * dt
            return True

        # LEVANDO PARA CASA
        destino_x = violao.x_inicial
        destino_y = violao.y_inicial
        dx = destino_x - entity.x
        dy = destino_y - entity.y
        distancia = math.hypot(dx, dy)

        violao.x = entity.x + self.offset_x
        violao.y = entity.y + self.offset_y

        if distancia < 15:
            violao.voltar_origem()
            self.ativo = False
            self.violao_em_maos = False
            return True

        entity.x += (dx / max(1, distancia)) * self.velocidade * dt
        entity.y += (dy / max(1, distancia)) * self.velocidade * dt
        return True

    def verificar_apos_acordar(self, sapo):
        violao = self.violao_monitorado
        if violao is None or sapo.esta_tocando_violao():
            return

        tolerancia = 10
        fora_do_lugar = (
            abs(violao.x - violao.x_inicial) > tolerancia
            or abs(violao.y - violao.y_inicial) > tolerancia
        )

        if fora_do_lugar:
            self.iniciar()
