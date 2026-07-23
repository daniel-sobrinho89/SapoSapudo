from application.usecases import (
    AcoplarViolaoUseCase,
    AtualizarFluxoViolaoUseCase,
    ComerEsferaUseCase,
    ConstruirUseCase,
    ControlarComportamentoDuendeUseCase,
    ControlarComportamentoOvelhaUseCase,
    ControlarSonoDuendeUseCase,
    DesacoplarViolaoUseCase,
    EsconderAtrasViolaoUseCase,
    ProcessarComandoSpotifyUseCase,
    ResgatarLivroUseCase,
    ResgatarViolaoUseCase,
)
from core.mouse_events import DoubleClickDetector
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
        self.evento_livro = evento_livro
        self.spotify = spotify
        self.audio = audio
        self.gerenciador_cenarios = gerenciador_cenarios
        self.double_click = DoubleClickDetector()
        self.controladores = {}

        self.resgatar_violao = ResgatarViolaoUseCase(self.duende, self.violao)
        self.resgatar_livro = ResgatarLivroUseCase(self.duende, self.sapo, self.livro)
        self.controlar_sono_duende = ControlarSonoDuendeUseCase(
            self.sapo,
            self.duende,
            self.violao,
            self.clima_service,
        )
        self.esconder_atras_violao = EsconderAtrasViolaoUseCase(
            self.duende, self.violao
        )
        self.comer_esfera = ComerEsferaUseCase(
            self.duende, self.esferas, self.evento_livro
        )
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

        self.construir = ConstruirUseCase()

    def executar(self, dt):
        if self.duende.carregado:
            self._executar_fluxo_duende(dt)
            self._executar_fluxo_sapudo(dt)
            self.evento_livro.atualizar(dt, self.sapo, self.duende)

        for personagem in self.gerenciador_cenarios.personagens:
            ctrl = self.gerenciador_cenarios.controladores[personagem]

            if personagem.animacoes.maquina.interagindo_arvore():
                ctrl["corte"].executar(dt)
            elif personagem.animacoes.maquina.interagindo_ouro():
                ctrl["ouro"].executar(dt)
            elif personagem.animacoes.maquina.interagindo_carne():
                ctrl["carne"].executar(dt)
            else:
                ctrl["ia"].executar(dt, personagem)

        for ovelha in self.gerenciador_cenarios.ovelhas:
            self.controlar_comportamento_ovelha.executar(dt, ovelha)

    def _executar_fluxo_duende(self, dt):
        # TODO! Ajustar para verificar se duende existe

        if (
            not self.clima_service.clima_disponivel
            or not self.duende
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

    def _executar_fluxo_sapudo(self, dt):
        if self.violao.acoplado or self.sapo.animacoes.maquina.eh(
            EstadoSapo.CHEGOU_AO_VIOLAO
        ):
            self.atualizar_fluxo_violao.executar(dt)

    def executar_comando_spotify(self, rota, finalizar_comando):
        self.processar_comando_spotify.executar(rota["dados"], finalizar_comando)

    def processar_toque_down(self, pos_virtual, renderer_violao):
        # ==========================================================
        # Seleção de aldeão / duplo clique na casa
        # ==========================================================
        for personagem in self.gerenciador_cenarios.personagens:
            if personagem.corpo_rect and personagem.corpo_rect.collidepoint(
                pos_virtual
            ):
                if self.double_click.detectar(pos_virtual):
                    personagem.menu_construcoes_aberto = (
                        not personagem.menu_construcoes_aberto
                    )
                    return

                if not personagem.animacoes.maquina.carregando_recuso():
                    # Apenas um aldeão fica selecionado
                    for p in self.gerenciador_cenarios.personagens:
                        p.selecionado = False

                    personagem.selecionado = True
                    return

        # ==========================================================
        # Descobre quem está selecionado
        # ==========================================================
        personagem = next(
            (p for p in self.gerenciador_cenarios.personagens if p.selecionado), None
        )

        # ==========================================================
        # Recursos
        # ==========================================================
        if personagem and not personagem.animacoes.maquina.carregando_recuso():
            ctrl = self.gerenciador_cenarios.controladores[personagem]

            for arvore, renderer in zip(
                self.gerenciador_cenarios.arvores,
                self.gerenciador_cenarios.renderers_arvores,
            ):
                if renderer.corpo_rect.collidepoint(pos_virtual):
                    ctrl["corte"].iniciar(arvore, renderer, personagem)
                    personagem.selecionado = False
                    return

            for ouro, renderer in zip(
                self.gerenciador_cenarios.ouro,
                self.gerenciador_cenarios.renderers_ouro,
            ):
                if renderer.corpo_rect.collidepoint(pos_virtual):
                    ctrl["ouro"].iniciar(ouro, renderer, personagem)
                    personagem.selecionado = False
                    return

            for ovelha, renderer in zip(
                self.gerenciador_cenarios.ovelhas,
                self.gerenciador_cenarios.renderers_ovelhas,
            ):
                if renderer.corpo_rect.collidepoint(pos_virtual):
                    ctrl["carne"].iniciar(ovelha, renderer, personagem)
                    personagem.selecionado = False
                    return

        # ==========================================================
        # Construções
        # ==========================================================
        for construcao in self.gerenciador_cenarios.construcoes:
            renderer = self.gerenciador_cenarios.menu_construcoes.obter_renderer(
                construcao
            )

            if renderer.corpo_rect.collidepoint(
                pos_virtual
            ) and self.double_click.detectar(pos_virtual):
                construcao.menu_aberto = not construcao.menu_aberto
                return

        construcao = self.gerenciador_cenarios.menu_construcoes.obter_opcao_clicada(
            pos_virtual
        )

        if construcao:
            self.construir.iniciar_arraste(
                pos_virtual, self.gerenciador_cenarios, construcao=construcao
            )
            return

        personagem = self.gerenciador_cenarios.menu_casa_renderer.obter_opcao_clicada(
            pos_virtual
        )

        if personagem:
            self.construir.iniciar_arraste(
                pos_virtual, self.gerenciador_cenarios, personagem=personagem
            )
            return

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

        if renderer_violao.obter_rect(self.violao).collidepoint(pos_virtual):
            self.violao.iniciar_arraste(*pos_virtual)
            return

        if self.duende and self.evento_livro.processar_toque(
            pos_virtual, self.duende, self.sapo
        ):
            return True

    def processar_toque_up(self, pos_virtual):
        if self.duende.arraste.ativo and not (self.duende.animacoes.teleportando):
            duende_indo_dormir = self.controlar_sono_duende.processar_soltou_duende(
                self.duende.arraste,
            )

            if duende_indo_dormir:
                return

        violao_acoplado = self.acoplar_violao.executar(self.sapo.area_violao())
        if violao_acoplado:
            return

        if (
            self.gerenciador_cenarios.construcao_arrastando
            or self.gerenciador_cenarios.personagem_arrastando
        ):
            self.construir.finalizar_arraste(
                pos_virtual,
                self.gerenciador_cenarios,
            )

    def processar_on_touch_move(self, pos_virtual):
        if (
            self.gerenciador_cenarios.construcao_arrastando
            or self.gerenciador_cenarios.personagem_arrastando
        ):
            self.construir.atualizar_arraste(
                pos_virtual,
                self.gerenciador_cenarios,
            )
