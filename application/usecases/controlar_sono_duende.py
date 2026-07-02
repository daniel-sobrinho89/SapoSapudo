import math


class ControlarSonoDuendeUseCase:
    def __init__(self, sapo, duende, violao, clima_service, frasco_rect):
        self.sapo = sapo
        self.duende = duende
        self.animacoes = self.duende.animacoes
        self.violao = violao
        self.clima_service = clima_service
        self.frasco_rect = frasco_rect
        self.saindo_do_frasco = False
        self.x_entrada_frasco = 0
        self.y_entrada_frasco = 0
        self.y_sono = 490
        self.velocidade_descida = 40
        self.soltou_frente_pote = False

    def executar(self, dt):
        self._atualizar_sono_programado(dt)
        self._atualizar_fator_visual(dt)
        self._atualizar_entrada_frasco(dt)
        self._atualizar_descida_sono(dt)
        self._sincronizar_estado_dormindo()
        self._atualizar_saida_frasco(dt)
        self._atualizar_estado_acordando(dt)
        self._verificar_inicio_sono_por_clima()
        self._verificar_retorno_voo()
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

        self.duende.escala_visual = 0.74 + math.sin(self.duende.tempo * 2.2) * 0.03
        self.duende.y = self.y_sono
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
        self.saindo_do_frasco = True

    def _atualizar_fator_visual(self, dt):
        if self.soltou_frente_pote:
            self.soltou_frente_pote = False
            self.iniciar_sono_programado()

            return

        if (
            not self.soltou_frente_pote
            and not self.animacoes.indo_para_frasco
            and not self.animacoes.escondendo_atras_violao
            and not self.animacoes.comendo_esfera
            and not self.animacoes.descendo_para_dormir
            and not self.animacoes.dormindo
            and not self.duende.esta_dentro_do_frasco(self.frasco_rect)
        ):
            self.duende.escala_visual = min(1.0, self.duende.escala_visual + dt * 0.6)

        if self.animacoes.dormindo:
            self.animacoes.fator_sono_visual = min(
                1.0, self.animacoes.fator_sono_visual + (0.25 * dt)
            )
        else:
            self.animacoes.fator_sono_visual = max(
                0.0, self.animacoes.fator_sono_visual - (0.50 * dt)
            )

    def _atualizar_entrada_frasco(self, dt):
        if not self.animacoes.indo_para_frasco:
            return False

        dx = self.x_entrada_frasco - self.duende.x
        dy = self.y_entrada_frasco - self.duende.y
        distancia = math.hypot(dx, dy)

        velocidade_base = 30
        velocidade_aproximacao = min(50, velocidade_base + distancia * 0.15)

        if distancia > 5:
            self.duende.x += (dx / distancia) * velocidade_aproximacao * dt
            self.duende.y += (dy / distancia) * velocidade_aproximacao * dt
        else:
            self.animacoes.iniciar_descida()

        if distancia < 60:
            self.duende.escala_visual = max(0.7, self.duende.escala_visual - dt * 0.6)

        return True

    def _atualizar_descida_sono(self, dt):
        if (
            not self.animacoes.descendo_para_dormir
            or self.duende.arrastando
            or self.saindo_do_frasco
        ):
            return False

        self.duende.escala_visual = max(
            0.7,
            self.duende.escala_visual - dt * 0.6,
        )

        self.duende.y += self.velocidade_descida * dt
        altura_restante = max(0, self.y_sono - self.duende.y)
        fator_voo = max(0, min(1, altura_restante / 80))

        self.duende.y += math.sin(self.duende.tempo * 8) * fator_voo

        # Reduz velocidade residual
        self.duende.velocidade_x *= 0.95
        self.duende.velocidade_y *= 0.95

        if self.duende.y >= self.y_sono:
            self.duende.y = self.y_sono
            self.animacoes.iniciar_sono()
            self.duende.velocidade_x = 0
            self.duende.velocidade_y = 0

        return True

    def processar_soltou_duende(self, arraste):
        arraste.ativo = False

        self.soltou_frente_pote = self.frasco_rect.collidepoint(
            int(self.duende.x),
            int(self.duende.y),
        )

        if self.soltou_frente_pote:
            self.duende.movimento_bloqueado = True
            return True

        if (
            self.animacoes.dormindo
            or self.animacoes.descendo_para_dormir
            or self.animacoes.indo_para_frasco
        ):
            self.cancelar_sono_programado()
            return True

        return False

    def _processar_entrada_frasco(self):
        self.x_entrada_frasco = self.frasco_rect.centerx
        self.y_entrada_frasco = self.frasco_rect.top - 60
        self.animacoes.iniciar_entrada_frasco()

    def iniciar_sono_programado(self):
        ciclo = self.animacoes.ciclo_sono
        ciclo.dormir_por_tempo = True
        ciclo.resetar_tempos()
        self.duende.movimento_bloqueado = True

        self._processar_entrada_frasco()

    def _verificar_inicio_sono_por_clima(self):
        animacoes = self.duende.animacoes

        if (
            not self.clima_service.clima_disponivel
            and not animacoes.dormindo
            and not animacoes.descendo_para_dormir
            and not animacoes.indo_para_frasco
            and not animacoes.acordando
        ):
            self._processar_entrada_frasco()

    def _verificar_retorno_voo(self):
        animacoes = self.duende.animacoes

        if (
            self.clima_service.clima_disponivel
            and not animacoes.ciclo_sono.dormir_por_tempo
            and not animacoes.dormindo
            and not animacoes.voando
            and not animacoes.guardando_violao
            and not animacoes.escondendo_atras_violao
            and not self.animacoes.comendo_esfera
        ):
            self.duende.animacoes.iniciar_voo()

    def _atualizar_estado_acordando(self, dt):
        if self.saindo_do_frasco or not self.animacoes.acordando:
            return

        ciclo = self.duende.animacoes.ciclo_sono
        ciclo.tempo_acordando += dt

        if ciclo.tempo_acordando < ciclo.tempo_maximo_acordado:
            return

        ciclo.tempo_acordando = 0
        if not self.clima_service.clima_disponivel:
            self._processar_entrada_frasco()
            return

        self.duende.animacoes.iniciar_voo()

    def cancelar_sono_programado(self):
        ciclo = self.duende.animacoes.ciclo_sono
        ciclo.dormir_por_tempo = False
        ciclo.resetar_tempos()
        self._acordar_duende()
        self._preparar_duende_acordado()

    def _acordar_duende(self):
        self.duende.animacoes.ciclo_sono.resetar_tempos()
        self.duende.animacoes.iniciar_acordar()
        self.duende.movimento_bloqueado = True

        if self.animacoes.dormindo:
            self.duende.x = self.frasco_rect.centerx
            self.duende.y = self.duende.y

    def _atualizar_saida_frasco(self, dt):
        if not self.saindo_do_frasco:
            return

        destino_y = self.frasco_rect.top - 50
        velocidade = 55

        if self.duende.y > destino_y:
            self.duende.y -= velocidade * dt
            return

        self.duende.y = destino_y
        self.saindo_do_frasco = False

        self.duende.y = self.frasco_rect.top - 50
        self._preparar_duende_acordado()

    def _preparar_duende_acordado(self):
        self.duende.movimento_bloqueado = False
        self.duende.escala_visual = 1.0
        self.duende.animacoes.fator_sono_visual = 0.0
        self.duende.base_y = self.duende.y
        self.duende.velocidade_x = 0
        self.duende.velocidade_y = 0
        self.duende.escolher_novo_destino()
        self.duende.animacoes.iniciar_voo()

        if self._precisa_resgatar_apos_acordar():
            self.duende.iniciar_resgate_monitorado = True

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
        self.saindo_do_frasco = True

    def _precisa_resgatar_apos_acordar(self):
        if (
            self.violao is None
            or self.violao.acoplado
            or self.sapo.esta_tocando_violao()
        ):
            return False

        tolerancia = 10

        return (
            abs(self.violao.x - self.violao.x_inicial) > tolerancia
            or abs(self.violao.y - self.violao.y_inicial) > tolerancia
        )
