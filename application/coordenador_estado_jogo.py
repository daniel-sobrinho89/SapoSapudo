from application.usecases import (
    ConstruirUseCase,
    ProcessarComandoSpotifyUseCase,
)
from core.mouse_events import DoubleClickDetector


class CoordenadorEstadoJogo:
    def __init__(
        self,
        clima_service,
        spotify,
        audio,
        gerenciador_cenarios,
    ):
        self.duende = gerenciador_cenarios.duende
        self.clima_service = clima_service
        self.spotify = spotify
        self.audio = audio
        self.gerenciador_cenarios = gerenciador_cenarios
        self.double_click = DoubleClickDetector()
        self.controladores = {}
        self.processar_comando_spotify = ProcessarComandoSpotifyUseCase(self.spotify)

        self.construir = ConstruirUseCase()

    def executar(self, dt):
        self._executar_fluxo_sapudo(dt)

        for personagem in (
            self.gerenciador_cenarios.personagens
            + self.gerenciador_cenarios.personagens_hostis
        ):
            self._executar_fluxo_personagem(personagem, dt)

        for personagem in self.gerenciador_cenarios.ovelhas:
            ctrl = self.gerenciador_cenarios.controladores[personagem]

            if personagem.vida <= 0:
                if ctrl["morte"].entidade_alvo is None:
                    ctrl["morte"].iniciar(personagem)
                else:
                    ctrl["morte"].executar(dt)

            for acao in ctrl["acoes"].values():
                acao["usecase"].executar(dt)
                break
            else:
                ctrl["padrao"].executar(dt, personagem)

    def _executar_fluxo_personagem(self, personagem, dt):
        ctrl = self.gerenciador_cenarios.controladores[personagem]

        if personagem.vida <= 0:
            if ctrl["morte"].entidade_alvo is None:
                ctrl["morte"].iniciar(personagem)
            else:
                ctrl["morte"].executar(dt)
            return

        if personagem.fugindo:
            for acao in ctrl["acoes"].values():
                acao["usecase"].entidade_alvo = None

            ctrl["padrao"].executar(dt, personagem)
            return

        for acao in ctrl["acoes"].values():
            if acao["usecase"].entidade_alvo:
                acao["usecase"].executar(dt)
                return

        ctrl["padrao"].executar(dt, personagem)

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
                    self.gerenciador_cenarios.menu_construcoes.aberto = (
                        not self.gerenciador_cenarios.menu_construcoes.aberto
                    )
                    self.gerenciador_cenarios.menu_casa_renderer.aberto = False
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
                    if item.corpo_rect is not None and item.corpo_rect.collidepoint(
                        mouse_mundo
                    ):
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
            if (
                construcao.corpo_rect is not None
                and construcao.corpo_rect.collidepoint(mouse_mundo)
                and self.double_click.detectar(mouse_mundo)
            ):
                self.gerenciador_cenarios.menu_casa_renderer.aberto = (
                    not self.gerenciador_cenarios.menu_casa_renderer.aberto
                )
                self.gerenciador_cenarios.menu_construcoes.aberto = False
                return

        if self.gerenciador_cenarios.menu_construcoes.aberto:
            construcao = self.gerenciador_cenarios.menu_construcoes.obter_opcao_clicada(
                pos_virtual
            )

            if construcao:
                self.construir.iniciar_arraste(
                    mouse_mundo, self.gerenciador_cenarios, construcao=construcao
                )
                return

        if self.gerenciador_cenarios.menu_casa_renderer.aberto:
            personagem = (
                self.gerenciador_cenarios.menu_casa_renderer.obter_opcao_clicada(
                    pos_virtual
                )
            )

            if personagem:
                self.construir.iniciar_arraste(
                    mouse_mundo, self.gerenciador_cenarios, personagem=personagem
                )
                return

        camera = self.gerenciador_cenarios.camera
        camera.arrastando = True
        camera.ultimo_mouse = pos_virtual

    def processar_toque_up(self, pos_virtual):
        camera = self.gerenciador_cenarios.camera
        camera.arrastando = False
        camera.ultimo_mouse = None
        mouse_mundo = self.gerenciador_cenarios.camera.mundo(*pos_virtual)

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
