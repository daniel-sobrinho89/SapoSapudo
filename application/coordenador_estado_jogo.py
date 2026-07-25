from application.usecases import (
    ComerEsferaUseCase,
    ConstruirUseCase,
    ControlarComportamentoDuendeUseCase,
    ControlarSonoDuendeUseCase,
    ProcessarComandoSpotifyUseCase,
)
from core.mouse_events import DoubleClickDetector


class CoordenadorEstadoJogo:
    def __init__(
        self,
        sapo,
        duende,
        esferas,
        clima_service,
        spotify,
        audio,
        gerenciador_cenarios,
    ):
        self.sapo = sapo
        self.duende = duende
        self.esferas = esferas
        self.clima_service = clima_service
        self.spotify = spotify
        self.audio = audio
        self.gerenciador_cenarios = gerenciador_cenarios
        self.double_click = DoubleClickDetector()
        self.controladores = {}
        self.controlar_sono_duende = ControlarSonoDuendeUseCase(
            self.sapo,
            self.duende,
            self.clima_service,
        )
        self.comer_esfera = ComerEsferaUseCase(self.duende, self.esferas)
        self.controlar_comportamento_duende = ControlarComportamentoDuendeUseCase(
            self.duende, self.sapo
        )
        self.processar_comando_spotify = ProcessarComandoSpotifyUseCase(self.spotify)

        self.construir = ConstruirUseCase()

    def executar(self, dt):
        if self.duende.carregado:
            self._executar_fluxo_duende(dt)
            self._executar_fluxo_sapudo(dt)

        for personagem in self.gerenciador_cenarios.personagens:
            ctrl = self.gerenciador_cenarios.controladores[personagem]

            for acao in ctrl["acoes"].values():
                if acao["usecase"].entidade_alvo is not None:
                    acao["usecase"].executar(dt)
                    break
            else:
                ctrl["padrao"].executar(dt, personagem)

        for personagem in self.gerenciador_cenarios.personagens_hostis:
            ctrl = self.gerenciador_cenarios.controladores[personagem]

            for acao in ctrl["acoes"].values():
                if acao["usecase"].entidade_alvo is not None:
                    acao["usecase"].executar(dt)
                    break
            else:
                ctrl["padrao"].executar(dt, personagem)

        for personagem in self.gerenciador_cenarios.ovelhas:
            ctrl = self.gerenciador_cenarios.controladores[personagem]

            for acao in ctrl["acoes"].values():
                acao["usecase"].executar(dt)
                break
            else:
                ctrl["padrao"].executar(dt, personagem)

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
            self.duende.animacoes.estado == self.duende.animacoes.INDO_ATRAS_ESFERA
            or self.duende.animacoes.estado == self.duende.animacoes.PERSEGUINDO_ESFERA
            or self.duende.animacoes.estado == self.duende.animacoes.COMENDO_ESFERA
        ):
            self.comer_esfera.executar(dt)
        elif not self.duende.movimento_bloqueado and not self.duende.teleporte.ativo:
            self.controlar_comportamento_duende.executar(dt)

    def _executar_fluxo_sapudo(self, dt):
        pass

    def executar_comando_spotify(self, rota, finalizar_comando):
        self.processar_comando_spotify.executar(rota["dados"], finalizar_comando)

    def processar_toque_down(self, pos_virtual):
        mouse_mundo = self.gerenciador_cenarios.camera.mundo(*pos_virtual)
        # ==========================================================
        # Seleção de aldeão / duplo clique na casa
        # ==========================================================
        for personagem in self.gerenciador_cenarios.personagens:
            if personagem.corpo_rect and personagem.corpo_rect.collidepoint(
                mouse_mundo
            ):
                if self.double_click.detectar(mouse_mundo):
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

            for outra_acao in ctrl["acoes"].values():
                outra_acao["usecase"].entidade_alvo = None

            for acao in ctrl["acoes"].values():
                for item in acao["itens"]:
                    if item.corpo_rect.collidepoint(mouse_mundo):
                        acao["usecase"].iniciar(
                            item,
                            personagem,
                        )

                        personagem.selecionado = False
                        return

        # ==========================================================
        # Construções
        # ==========================================================
        for construcao in self.gerenciador_cenarios.construcoes:
            if construcao.corpo_rect.collidepoint(
                mouse_mundo
            ) and self.double_click.detectar(mouse_mundo):
                construcao.menu_aberto = not construcao.menu_aberto
                return

        construcao = self.gerenciador_cenarios.menu_construcoes.obter_opcao_clicada(
            pos_virtual
        )

        if construcao:
            self.construir.iniciar_arraste(
                mouse_mundo, self.gerenciador_cenarios, construcao=construcao
            )
            return

        personagem = self.gerenciador_cenarios.menu_casa_renderer.obter_opcao_clicada(
            pos_virtual, self.gerenciador_cenarios
        )

        if personagem:
            self.construir.iniciar_arraste(
                mouse_mundo, self.gerenciador_cenarios, personagem=personagem
            )
            return

        if not self.duende.animacoes.teleportando and self.duende.processar_toque_down(
            pos_virtual
        ):
            return

        camera = self.gerenciador_cenarios.camera
        camera.arrastando = True
        camera.ultimo_mouse = pos_virtual

    def processar_toque_up(self, pos_virtual):
        camera = self.gerenciador_cenarios.camera
        camera.arrastando = False
        camera.ultimo_mouse = None
        mouse_mundo = self.gerenciador_cenarios.camera.mundo(*pos_virtual)

        if self.duende.arraste.ativo and not (self.duende.animacoes.teleportando):
            duende_indo_dormir = self.controlar_sono_duende.processar_soltou_duende(
                self.duende.arraste,
            )

            if duende_indo_dormir:
                return

        if (
            self.gerenciador_cenarios.construcao_arrastando
            or self.gerenciador_cenarios.personagem_arrastando
        ):
            self.construir.finalizar_arraste(
                mouse_mundo,
                self.gerenciador_cenarios,
            )

    def processar_on_touch_move(self, pos_virtual):
        camera = self.gerenciador_cenarios.camera

        if camera.arrastando:
            dx = pos_virtual[0] - camera.ultimo_mouse[0]
            dy = pos_virtual[1] - camera.ultimo_mouse[1]

            camera.x -= dx
            camera.y -= dy

            camera.ultimo_mouse = pos_virtual
            return

        mouse_mundo = camera.mundo(*pos_virtual)

        if (
            self.gerenciador_cenarios.construcao_arrastando
            or self.gerenciador_cenarios.personagem_arrastando
        ):
            self.construir.atualizar_arraste(
                mouse_mundo,
                self.gerenciador_cenarios,
            )
            return
