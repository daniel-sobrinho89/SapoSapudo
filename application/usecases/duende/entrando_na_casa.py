import math


class EntrandoNaCasaUseCase:
    def __init__(self, casa_duende, gerenciador_cenarios):
        self.casa_duende = casa_duende
        self.casa_duende_rect = casa_duende.area_interna
        self.gerenciador_cenarios = gerenciador_cenarios
        self.y_inicio_corte = 245
        self.y_fim_corte = 370

    def executar(self, dt, duende):
        if duende.animacoes.indo_para_casa:
            self._atualizar_entrada_casa(dt, duende)
        else:
            self._atualizar_descida_casa(dt, duende)

    def _atualizar_entrada_casa(self, dt, duende):
        dx = self.casa_duende_rect.centerx - duende.x
        dy = (self.casa_duende_rect.top - 90) - duende.y
        distancia = math.hypot(dx, dy)

        velocidade_base = 30
        velocidade_aproximacao = min(50, velocidade_base + distancia * 0.15)

        if distancia > 5:
            duende.x += (dx / distancia) * velocidade_aproximacao * dt
            duende.y += (dy / distancia) * velocidade_aproximacao * dt
        else:
            duende.animacoes.iniciar_descida()

        if distancia < 60:
            duende.escala_visual = max(0.7, duende.escala_visual - dt * 0.6)

    def _atualizar_descida_casa(self, dt, duende):
        duende.escala_visual = max(0.7, duende.escala_visual - dt * 0.6)

        altura_restante = max(0, duende.y_descida_casa - duende.y)
        fator_voo = max(0, min(1, altura_restante / 80))

        duende.y += math.sin(duende.tempo * 8) * fator_voo

        # Reduz velocidade residual
        duende.velocidade_x *= 0.95
        duende.velocidade_y *= 0.95

        y_base = (
            duende.y + duende.velodidade_descina_sono * dt + duende.altura_render / 2
        )

        distancia = self.y_fim_corte - y_base
        distancia_corte = self.y_fim_corte - self.y_inicio_corte

        percentual = max(0, min(1, distancia / distancia_corte))

        percentual = percentual**0.44

        duende.percentual_visivel = percentual
        duende.y += duende.velodidade_descina_sono * dt

        if duende.y >= duende.y_descida_casa:
            duende.y = duende.y_descida_casa
            duende.velocidade_x = 0
            duende.velocidade_y = 0
            duende.percentual_visivel = 1.0
            if duende.fluxo_sono_iniciado:
                self.casa_duende.abrir_janela_superior()
                duende.animacoes.iniciar_sono()
            else:
                novo_duende = duende.duplicar()
                duende.iniciar_saida_casa()
                self.gerenciador_cenarios.adicionar_duende(novo_duende)
