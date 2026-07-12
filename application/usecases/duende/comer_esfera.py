import math


class ComerEsferaUseCase:
    INDO_FRASCO = "indo_frasco"

    def __init__(
        self, duende, casa_duende, esferas, evento_livro, gerenciador_cenarios
    ):
        self.duende = duende
        self.casa_duende = casa_duende
        self.esferas = esferas
        self.evento_livro = evento_livro
        self.gerenciador_cenarios = gerenciador_cenarios

        self.tempo = 0.0
        self.esfera_alvo = None
        self.casa_duende_rect = self.casa_duende.area_interna
        self.x_entrada_frasco = self.casa_duende_rect.centerx
        self.y_entrada_frasco = self.casa_duende_rect.top - 60
        self.y_descida_frasco = 490

    def executar(self):
        self.tempo = 0.0

        esferas = [e for e in self.esferas if e.ativa and e.saiu_da_casa]

        if not esferas:
            self.esfera_alvo = None
            return

        self.esfera_alvo = min(
            esferas,
            key=lambda e: math.hypot(
                e.x - self.duende.x,
                e.y - self.duende.y,
            ),
        )

        self.duende.animacoes.iniciar_perseguindo_esfera()

    def atualizar(self, dt):
        if self.esfera_alvo is None:
            self.duende.animacoes.iniciar_voo()
        elif self.duende.animacoes.estado == self.duende.animacoes.PERSEGUINDO_ESFERA:
            alvo_x = self.esfera_alvo.x
            alvo_y = self.esfera_alvo.y
            dx = alvo_x - self.duende.x
            dy = alvo_y - self.duende.y

            distancia = math.hypot(dx, dy)

            if distancia > 6:
                velocidade = 180
                self.duende.x += (dx / distancia) * velocidade * dt
                self.duende.y += (dy / distancia) * velocidade * dt
            else:
                self.esfera_alvo.ativa = False
                self.duende.movimento_bloqueado = True
                self.evento_livro.registrar_clique_esfera()
                self.duende.animacoes.iniciar_comer_esfera()
        elif self.duende.animacoes.estado == self.duende.animacoes.COMENDO_ESFERA:
            terminou = self.duende.animacoes.animacao_comendo_esfera.atualizar(dt)
            if terminou:
                self.duende.animacoes.iniciar_indo_frasco_duplicar()
        elif self.duende.animacoes.estado == self.duende.animacoes.INDO_FRASCO_DUPLICAR:
            terminou = self._atualizar_entrada_frasco(dt)
            if terminou:
                self.duende.animacoes.iniciar_descendo_frasco_duplicar()
        elif (
            self.duende.animacoes.estado
            == self.duende.animacoes.DESCENDO_FRASCO_DUPLICAR
        ):
            terminou = self._atualizar_descida_frasco(dt)
            if terminou:
                novo_duende = self.duende.duplicar()
                self.duende.iniciar_saida_frasco()
                self.gerenciador_cenarios.adicionar_duende(novo_duende)

    def _atualizar_entrada_frasco(self, dt):
        dx = self.x_entrada_frasco - self.duende.x
        dy = self.y_entrada_frasco - self.duende.y
        distancia = math.hypot(dx, dy)

        velocidade_base = 30
        velocidade_aproximacao = min(50, velocidade_base + distancia * 0.15)

        if distancia > 5:
            self.duende.x += (dx / distancia) * velocidade_aproximacao * dt
            self.duende.y += (dy / distancia) * velocidade_aproximacao * dt
        else:
            return True

        if distancia < 60:
            self.duende.escala_visual = max(0.7, self.duende.escala_visual - dt * 0.6)

        return False

    def _atualizar_descida_frasco(self, dt):
        self.duende.escala_visual = max(0.7, self.duende.escala_visual - dt * 0.6)

        self.duende.y += self.duende.velodidade_descina_sono * dt
        altura_restante = max(0, self.y_descida_frasco - self.duende.y)
        fator_voo = max(0, min(1, altura_restante / 80))

        self.duende.y += math.sin(self.duende.tempo * 8) * fator_voo

        # Reduz velocidade residual
        self.duende.velocidade_x *= 0.95
        self.duende.velocidade_y *= 0.95

        if self.duende.y >= self.y_descida_frasco:
            self.duende.y = self.y_descida_frasco
            self.duende.velocidade_x = 0
            self.duende.velocidade_y = 0
            return True

        return False
