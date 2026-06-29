class ResgatarViolaoUseCase:
    MIN_TELEPORT_DIST = 120

    def __init__(self, sapo, duende, clima_service, frasco_rect):
        self.sapo = sapo
        self.duende = duende
        self.clima_service = clima_service
        self.frasco_rect = frasco_rect

    def executar(self, estado_violao):
        if (
            self.duende.teleportando
            or self.duende.resgatando_violao
            or estado_violao.acoplado
            or not self.duende.pode_resgatar_violao()
        ):
            return

        distancia = abs(estado_violao.x - self.duende.x)

        if (
            not self.duende.consegue_alcancar_antes_da_queda(estado_violao)
            and distancia > self.MIN_TELEPORT_DIST
        ):
            self.duende.teleportar_para_violao(estado_violao)
            return

        self.duende.iniciar_resgate_violao(estado_violao)

    def atualizar(self, dt):
        self._atualizar_sono_programado(dt)

        if self.duende.animacoes.acabou_de_acordar:
            self.duende.animacoes.acabou_de_acordar = False
            self._verificar_apos_acordar()

        if self.duende.teleportando:
            self._atualizar_teleporte(dt)
            return

        if self.duende.resgatando_violao:
            self._atualizar_resgate(dt)
            return

    def _verificar_apos_acordar(self):
        if not self._precisa_resgatar_apos_acordar():
            return

        self._iniciar_resgate()

    def _iniciar_resgate(self):
        violao = self.duende.resgate.violao_monitorado

        if violao is None:
            return

        self.duende.iniciar_resgate_violao(violao.estado())

    def _atualizar_teleporte(self, dt):
        teleporte_concluido = self.duende.teleporte.atualizar(dt, self.duende)

        self.duende.alpha_visual = self.duende.teleporte.alpha_visual

        self.duende.escala_visual = self.duende.teleporte.escala_visual

        if teleporte_concluido:
            self._iniciar_resgate()

    def _atualizar_resgate(self, dt):
        resgate_concluido = self.duende.resgate.atualizar(dt, self.duende)

        if resgate_concluido:
            self._finalizar_resgate()

    def _atualizar_sono_programado(self, dt):
        if not self.duende.animacoes.ciclo_sono.dormir_por_tempo:
            return

        self.duende.animacoes.ciclo_sono.tempo_dormindo += dt

        if (
            self.duende.animacoes.ciclo_sono.tempo_dormindo
            < self.duende.animacoes.ciclo_sono.tempo_maximo_dormindo
        ):
            return

        self.duende.animacoes.ciclo_sono.tempo_dormindo = 0
        self.duende.animacoes.ciclo_sono.dormir_por_tempo = False

        if not self.clima_service.clima_disponivel:
            self.duende.animacoes.ciclo_sono.dormir_por_tempo = True
            return

        self.duende.animacoes.ciclo_sono.resetar_tempos()

        self.duende.iniciar_acordar()
        self.duende.y = self.frasco_rect.top - 50
        self.duende.escolher_novo_destino()

    def _precisa_resgatar_apos_acordar(self):
        violao = self.duende.resgate.violao_monitorado

        if violao is None or violao.acoplado or self.sapo.esta_tocando_violao():
            return False

        tolerancia = 10

        return (
            abs(violao.x - violao.x_inicial) > tolerancia
            or abs(violao.y - violao.y_inicial) > tolerancia
        )

    def _finalizar_resgate(self):
        violao = self.duende.resgate.violao_monitorado

        if violao is not None:
            violao.voltar_origem()

        self.duende.resgate.ativo = False
        self.duende.resgate.violao_em_maos = False

        self.duende.velocidade_x = 0
        self.duende.velocidade_y = 0
