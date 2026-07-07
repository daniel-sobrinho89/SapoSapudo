class CoordenadorEstadoJogo:
    def __init__(
        self,
        duende,
        violao,
        livro,
        clima_service,
        resgatar_violao,
        resgatar_livro,
        controlar_sono_duende,
        esconder_atras_violao,
        comer_esfera,
        controlar_comportamento_duende,
    ):
        self.duende = duende
        self.violao = violao
        self.livro = livro
        self.clima_service = clima_service

        self.resgatar_violao = resgatar_violao
        self.resgatar_livro = resgatar_livro
        self.controlar_sono_duende = controlar_sono_duende
        self.esconder_atras_violao = esconder_atras_violao
        self.comer_esfera = comer_esfera
        self.controlar_comportamento_duende = controlar_comportamento_duende

    def executar(self, dt):
        if self.duende.carregado:
            self._executar_fluxo_duende(dt)

    def _executar_fluxo_duende(self, dt):
        if (
            not self.clima_service.clima_disponivel
            or self.duende.animacoes.em_frente_ao_frasco
            or self.duende.animacoes.indo_para_frasco
            or self.duende.animacoes.descendo_para_dormir
            or self.duende.animacoes.dormindo
            or self.duende.animacoes.acordando
        ):
            self.controlar_sono_duende.executar(dt)
        elif (
            (self.violao.caindo or self.violao.fora_do_lugar)
            and not (self.violao.acoplado)
            and not (
                self.duende.animacoes.perseguindo_violao
                or self.duende.animacoes.guardando_violao
            )
        ):
            self.resgatar_violao.executar()
        elif (
            self.duende.animacoes.perseguindo_violao
            or self.duende.animacoes.guardando_violao
        ):
            self.resgatar_violao.atualizar(dt)
        elif self.livro.visivel and not (
            self.duende.animacoes.perseguindo_livro
            or self.duende.animacoes.guardando_livro
        ):
            self.resgatar_livro.executar()
        elif (
            self.duende.animacoes.perseguindo_livro
            or self.duende.animacoes.guardando_livro
        ):
            self.resgatar_livro.atualizar(dt)
        elif self.duende.animacoes.estado == self.duende.animacoes.INDO_ATRAS_VIOLAO:
            self.esconder_atras_violao.executar()
        elif (
            self.duende.animacoes.estado
            == self.duende.animacoes.ESCONDENDO_ATRAS_VIOLAO
        ):
            self.esconder_atras_violao.atualizar(dt)
        elif self.duende.animacoes.estado == self.duende.animacoes.INDO_ATRAS_ESFERA:
            self.comer_esfera.executar()
        elif (
            self.duende.animacoes.estado == self.duende.animacoes.PERSEGUINDO_ESFERA
            or self.duende.animacoes.estado == self.duende.animacoes.COMENDO_ESFERA
        ):
            self.comer_esfera.atualizar(dt)
        elif not self.duende.movimento_bloqueado and not self.duende.teleporte.ativo:
            self.controlar_comportamento_duende.executar(dt)

    def processar_soltou_duende(self):
        self.controlar_sono_duende.processar_soltou_duende(
            self.duende.arraste,
        )
