import math


class ControlarSonoDuendeUseCase:
    def __init__(self, duende, clima_service):
        self.duende = duende
        self.animacoes = self.duende.animacoes
        self.clima_service = clima_service
        self.tempo_respiracao = 0

    def executar(self, dt):
        self._atualizar_sono_programado(dt)
        self._atualizar_fator_visual(dt)
        self._sincronizar_estado_dormindo()
        self._atualizar_estado_acordando(dt)
        self._verificar_inicio_sono_por_clima()
        self._atualizar_acordar_por_clima()

    def _atualizar_sono_programado(self, dt):
        if not self.animacoes.ciclo_sono.dormir_por_tempo:
            return

        if not self._tempo_sono_expirou(dt):
            return

        self._processar_fim_sono_programado()

    def _sincronizar_estado_dormindo(self):
        if not self.animacoes.dormindo or self.duende.arrastando:
            return

        self.duende.escala_visual = 0.60 + math.sin(self.duende.tempo * 2.2) * 0.03
        self.duende.y = self.duende.y_descida_casa
        self.duende.velocidade_x = 0
        self.duende.velocidade_y = 0

    def _processar_fim_sono_programado(self):
        ciclo = self.animacoes.ciclo_sono
        ciclo.tempo_dormindo = 0

        if not self.clima_service.clima_disponivel:
            ciclo.dormir_por_tempo = True
            return

        if self.duende.arraste.ativo:
            return

        ciclo.dormir_por_tempo = False
        self._acordar_duende()
        self.duende.iniciar_saida_casa()

    def _atualizar_fator_visual(self, dt):
        if self.animacoes.em_frente_a_casa:
            self.iniciar_sono_programado()
            return

        if not self.duende.animacoes.em_frente_a_casa and not self.animacoes.dormindo:
            self.duende.escala_visual = min(1.0, self.duende.escala_visual + dt * 0.6)

        if self.animacoes.dormindo:
            self.tempo_respiracao += dt

            self.animacoes.fator_sono_visual = 0.5 + 0.5 * math.sin(
                self.tempo_respiracao * 1.8
            )
        else:
            self.tempo_respiracao = 0
            self.animacoes.fator_sono_visual = max(
                0.0,
                self.animacoes.fator_sono_visual - (2.0 * dt),
            )

    def processar_soltou_duende(self, arraste):
        arraste.ativo = False

        if self.animacoes.dormindo or self.animacoes.descendo_para_dormir:
            self.cancelar_sono_programado()
            return True

        return False

    def _processar_entrada_casa(self):
        self.duende.fluxo_sono_iniciado = True
        self.animacoes.iniciar_entrada_casa()

    def iniciar_sono_programado(self):
        ciclo = self.animacoes.ciclo_sono
        ciclo.dormir_por_tempo = True
        ciclo.resetar_tempos()
        self.duende.movimento_bloqueado = True

        self._processar_entrada_casa()

    def _verificar_inicio_sono_por_clima(self):
        animacoes = self.duende.animacoes

        if (
            not self.clima_service.clima_disponivel
            and not animacoes.dormindo
            and not animacoes.acordando
        ):
            self._processar_entrada_casa()

    def _atualizar_estado_acordando(self, dt):
        if not self.animacoes.acordando:
            return

        ciclo = self.duende.animacoes.ciclo_sono
        ciclo.tempo_acordando += dt

        if ciclo.tempo_acordando < ciclo.tempo_maximo_acordado:
            return

        ciclo.tempo_acordando = 0
        if not self.clima_service.clima_disponivel:
            self._processar_entrada_casa()
            return

        self.duende.animacoes.iniciar_voo()

    def cancelar_sono_programado(self):
        ciclo = self.duende.animacoes.ciclo_sono
        ciclo.dormir_por_tempo = False
        ciclo.resetar_tempos()
        self.duende.iniciar_voo()

    def _acordar_duende(self):
        self.duende.animacoes.ciclo_sono.resetar_tempos()
        self.duende.animacoes.iniciar_acordar()
        self.duende.movimento_bloqueado = True

        if self.animacoes.dormindo:
            self.duende.y = self.duende.y

    def _tempo_sono_expirou(self, dt):
        ciclo = self.duende.animacoes.ciclo_sono
        ciclo.tempo_dormindo += dt

        return ciclo.tempo_dormindo >= ciclo.tempo_maximo_dormindo

    def _atualizar_acordar_por_clima(self):
        if not self.duende.animacoes.dormindo:
            return

        if not self.clima_service.clima_disponivel:
            return

        if self.duende.animacoes.ciclo_sono.dormir_por_tempo:
            return

        self._acordar_duende()
        self.duende.iniciar_saida_casa()
