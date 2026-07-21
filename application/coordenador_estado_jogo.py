from application.usecases import (
    AcoplarViolaoUseCase,
    AtualizarFluxoViolaoUseCase,
    ComerEsferaUseCase,
    ControlarComportamentoAldeaoUseCase,
    ControlarComportamentoDuendeUseCase,
    ControlarComportamentoOvelhaUseCase,
    ControlarSonoDuendeUseCase,
    CortarArvoreUseCase,
    DesacoplarViolaoUseCase,
    EntrandoNaCasaUseCase,
    EsconderAtrasViolaoUseCase,
    ObterOuroUseCase,
    ProcessarComandoSpotifyUseCase,
    ResgatarLivroUseCase,
    ResgatarViolaoUseCase,
    SaindoDaCasaUseCase,
)
from domains.sapudo.maquina_estado_sapo import EstadoSapo


class CoordenadorEstadoJogo:
    def __init__(
        self,
        sapo,
        duende,
        violao,
        livro,
        esferas,
        clima_service,
        casa_duende,
        evento_livro,
        spotify,
        audio,
        gerenciador_cenarios,
    ):
        self.sapo = sapo
        self.duende = duende
        self.violao = violao
        self.livro = livro
        self.esferas = esferas
        self.clima_service = clima_service
        self.casa_duende = casa_duende
        self.evento_livro = evento_livro
        self.spotify = spotify
        self.audio = audio
        self.gerenciador_cenarios = gerenciador_cenarios

        self.resgatar_violao = ResgatarViolaoUseCase(self.duende, self.violao)
        self.resgatar_livro = ResgatarLivroUseCase(self.duende, self.sapo, self.livro)
        self.controlar_sono_duende = ControlarSonoDuendeUseCase(
            self.sapo,
            self.duende,
            self.violao,
            self.clima_service,
            self.casa_duende,
        )
        self.esconder_atras_violao = EsconderAtrasViolaoUseCase(
            self.duende, self.violao
        )
        self.comer_esfera = ComerEsferaUseCase(
            self.duende, self.casa_duende, self.esferas, self.evento_livro
        )
        self.entrando_na_casa = EntrandoNaCasaUseCase(
            self.casa_duende, self.gerenciador_cenarios
        )
        self.saindo_da_casa = SaindoDaCasaUseCase(self.casa_duende)
        self.controlar_comportamento_duende = ControlarComportamentoDuendeUseCase(
            self.duende, self.sapo, self.violao
        )

        self.acoplar_violao = AcoplarViolaoUseCase(
            self.violao, self.sapo, self.duende, self.spotify
        )
        self.desacoplar_violao = DesacoplarViolaoUseCase(
            self.violao, self.sapo, self.spotify, self.audio
        )
        self.processar_comando_spotify = ProcessarComandoSpotifyUseCase(
            self.spotify, self.desacoplar_violao
        )
        self.atualizar_fluxo_violao = AtualizarFluxoViolaoUseCase(
            self.sapo, self.violao, self.spotify, self.audio
        )

        self.controlar_comportamento_ovelha = ControlarComportamentoOvelhaUseCase()

        self.obter_ouro = ObterOuroUseCase(self.gerenciador_cenarios)
        self.cortar_arvore = CortarArvoreUseCase(self.gerenciador_cenarios)
        self.controlar_comportamento_aldeao = ControlarComportamentoAldeaoUseCase(
            self.gerenciador_cenarios.aldeao
        )

    def executar(self, dt):
        if self.duende.carregado:
            self._executar_fluxo_duende(dt)
            self._executar_fluxo_duende_clones(dt)
            self._executar_fluxo_sapudo(dt)
            self.evento_livro.atualizar(dt, self.sapo, self.duende)

            if self.gerenciador_cenarios.aldeao.animacoes.maquina.interagindo_arvore():
                self.cortar_arvore.executar(dt)
            elif self.gerenciador_cenarios.aldeao.animacoes.maquina.interagindo_ouro():
                self.obter_ouro.executar(dt)
            else:
                self.controlar_comportamento_aldeao.executar(dt)

        for ovelha in self.gerenciador_cenarios.ovelhas:
            self.controlar_comportamento_ovelha.executar(dt, ovelha)

    def _executar_fluxo_duende(self, dt):
        # TODO! Ajustar para verificar se duende existe

        if (
            self.duende.animacoes.indo_para_casa
            or self.duende.animacoes.descendo_para_dormir
        ):
            self.entrando_na_casa.executar(dt, self.duende)
        elif self.duende.animacoes.saindo_da_casa:
            self.saindo_da_casa.executar(dt, self.duende)
        elif (
            not self.clima_service.clima_disponivel
            or not self.duende
            or self.duende.animacoes.em_frente_a_casa
            or self.duende.animacoes.dormindo
            or self.duende.animacoes.acordando
        ):
            self.controlar_sono_duende.executar(dt)
        elif (
            self.violao.caindo
            or self.violao.fora_do_lugar
            or self.duende.animacoes.perseguindo_violao
            or self.duende.animacoes.guardando_violao
        ):
            self.resgatar_violao.executar(dt)
        elif self.livro.visivel or (
            self.duende.animacoes.perseguindo_livro
            or self.duende.animacoes.guardando_livro
        ):
            self.resgatar_livro.executar(dt)
        elif (
            self.duende.animacoes.estado == self.duende.animacoes.INDO_ATRAS_VIOLAO
            or self.duende.animacoes.estado
            == self.duende.animacoes.ESCONDENDO_ATRAS_VIOLAO
        ):
            self.esconder_atras_violao.executar(dt)
        elif (
            self.duende.animacoes.estado == self.duende.animacoes.INDO_ATRAS_ESFERA
            or self.duende.animacoes.estado == self.duende.animacoes.PERSEGUINDO_ESFERA
            or self.duende.animacoes.estado == self.duende.animacoes.COMENDO_ESFERA
        ):
            self.comer_esfera.executar(dt)
        elif not self.duende.movimento_bloqueado and not self.duende.teleporte.ativo:
            self.controlar_comportamento_duende.executar(dt)

    def _executar_fluxo_duende_clones(self, dt):
        for duende in self.gerenciador_cenarios.duendes:
            if duende.animacoes.saindo_da_casa:
                self.saindo_da_casa.executar(dt, duende)

    def _executar_fluxo_sapudo(self, dt):
        if self.violao.acoplado or self.sapo.animacoes.maquina.eh(
            EstadoSapo.CHEGOU_AO_VIOLAO
        ):
            self.atualizar_fluxo_violao.executar(dt)

    def executar_comando_spotify(self, rota, finalizar_comando):
        self.processar_comando_spotify.executar(rota["dados"], finalizar_comando)

    def processar_toque_down(self, pos_virtual, renderer_violao):
        renderer_aldeao = self.gerenciador_cenarios.renderer_aldeao

        if renderer_aldeao.corpo_rect.collidepoint(pos_virtual):
            print("Selecionou aldeao")
            self.gerenciador_cenarios.aldeao.selecionado = True
            return

        for arvore, renderer in zip(
            self.gerenciador_cenarios.arvores,
            self.gerenciador_cenarios.renderers_arvores,
        ):
            if renderer.corpo_rect.collidepoint(pos_virtual):
                print("Arvore selecionada", id(arvore))
                if self.gerenciador_cenarios.aldeao.selecionado:
                    self.cortar_arvore.iniciar(arvore)

                self.gerenciador_cenarios.aldeao.selecionado = False
                return

        for ouro, renderer in zip(
            self.gerenciador_cenarios.ouro,
            self.gerenciador_cenarios.renderers_ouro,
        ):
            if renderer.corpo_rect.collidepoint(pos_virtual):
                if self.gerenciador_cenarios.aldeao.selecionado:
                    self.obter_ouro.iniciar(ouro, renderer)

                self.gerenciador_cenarios.aldeao.selecionado = False
                return

        self.gerenciador_cenarios.aldeao.selecionado = False

        if self.desacoplar_violao.executar(
            mouse_pos=pos_virtual,
            iniciar_arraste=True,
        ):
            return

        if (
            not self.duende.animacoes.teleportando
            and not self.duende.animacoes.perseguindo_livro
            and not self.duende.animacoes.guardando_livro
            and self.duende.processar_toque_down(pos_virtual)
        ):
            return

        # violao_rect
        if renderer_violao.obter_rect(self.violao).collidepoint(pos_virtual):
            self.violao.iniciar_arraste(*pos_virtual)
            return

        if self.duende and self.evento_livro.processar_toque(
            pos_virtual, self.duende, self.sapo
        ):
            return True

    def processar_toque_up(self):
        if self.duende.arraste.ativo and not (self.duende.animacoes.teleportando):
            duende_indo_dormir = self.controlar_sono_duende.processar_soltou_duende(
                self.duende.arraste,
            )

            if duende_indo_dormir:
                return

        violao_acoplado = self.acoplar_violao.executar(self.sapo.area_violao())
        if violao_acoplado:
            return
