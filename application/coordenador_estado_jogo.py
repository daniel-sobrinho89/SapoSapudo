from application.usecases import (
    ConstruirUseCase,
    TrocarComportamentoUseCase,
)
from core.mouse_events import DoubleClickDetector
from domains.personagem.maquina_estado_soldado import EstadoSoldado


class CoordenadorEstadoJogo:
    def __init__(
        self,
        gerenciador_cenarios,
    ):
        self.gerenciador_cenarios = gerenciador_cenarios
        self.double_click = DoubleClickDetector()
        self.controladores = {}
        self._tempo_proxima_busca_alvo = {}
        # Decisão automática em 4 Hz. A execução de ações continua por frame.
        self._intervalo_busca_alvo = 0.25

        self.construir = ConstruirUseCase()
        self.trocar_comportamento = TrocarComportamentoUseCase()

    def executar(self, dt):
        metricas = getattr(self.gerenciador_cenarios, "metricas_desempenho", None)
        if metricas is not None:
            metricas.contar("ticks_coordenador")

        for personagem in (
            self.gerenciador_cenarios.personagens
            + self.gerenciador_cenarios.personagens_hostis
        ):
            if metricas is not None:
                metricas.contar("personagens_processados")
            self._executar_fluxo_personagem(personagem, dt)

        for personagem in self.gerenciador_cenarios.ovelhas:
            ctrl = self.gerenciador_cenarios.controladores[personagem]

            if personagem.vida <= 0 and ctrl.get("morte") is not None:
                if ctrl["morte"].entidade_alvo is None:
                    ctrl["morte"].iniciar(personagem)
                else:
                    ctrl["morte"].executar(dt)

            for acao in ctrl["acoes"].values():
                acao["usecase"].executar(dt)
                break
            else:
                ctrl["padrao"].executar(dt, personagem)

        for entidade in (
            self.gerenciador_cenarios.construcoes
            + self.gerenciador_cenarios.construcoes_hostis
        ):
            # Preview de construção não participa da IA até ser colocado.
            if entidade is self.gerenciador_cenarios.construcao_arrastando:
                continue

            ctrl = self.gerenciador_cenarios.controladores[entidade]

            if entidade.vida <= 0 and ctrl.get("morte") is not None:
                if ctrl["morte"].entidade_alvo is None:
                    ctrl["morte"].iniciar(entidade)
                else:
                    ctrl["morte"].executar(dt)

            ctrl["padrao"].executar(dt)

    def _executar_fluxo_personagem(self, personagem, dt):
        ctrl = self.gerenciador_cenarios.controladores[personagem]
        metricas = getattr(self.gerenciador_cenarios, "metricas_desempenho", None)

        proxima_busca = self._tempo_proxima_busca_alvo.get(personagem, 0.0)
        proxima_busca -= dt
        self._tempo_proxima_busca_alvo[personagem] = proxima_busca

        if personagem.vida <= 0 and ctrl.get("morte") is not None:
            # Não apagar os alvos das ações antes da máquina de morte executar.
            # O fluxo de morte precisa saber, por exemplo, se este personagem
            # era a ovelha que um aldeão estava caçando para poder redirecioná-lo
            # para a carne recém-dropada. O próprio use case de morte cancela as
            # ações no momento correto, depois de capturar essa informação.
            if ctrl["morte"].entidade_alvo is None:
                ctrl["morte"].iniciar(personagem)
                return
            else:
                ctrl["morte"].executar(dt)
                return

        defendendo = personagem.animacoes.estado in (
            EstadoSoldado.DEFENDENDO,
            EstadoSoldado.DEFENDENDO_FLIP,
        )

        for acao in ctrl["acoes"].values():
            usecase = acao["usecase"]

            if usecase.entidade_alvo:
                usecase.executar(dt)
                return

            if defendendo:
                continue

            adquirir_alvo = getattr(usecase, "tentar_adquirir_inimigo_proximo", None)
            adquirir_recurso = getattr(usecase, "tentar_adquirir_recurso", None)
            pode_buscar = getattr(
                usecase,
                "pode_adquirir_alvo_automaticamente",
                None,
            )

            if (
                adquirir_alvo is not None
                and (pode_buscar is None or pode_buscar())
                and self._tempo_proxima_busca_alvo[personagem] <= 0.0
            ):
                self._tempo_proxima_busca_alvo[personagem] = self._intervalo_busca_alvo
                if metricas is not None:
                    metricas.contar("buscas_alvo")
                if adquirir_alvo(personagem):
                    usecase.executar(dt)
                    return

            if (
                adquirir_recurso is not None
                and self._tempo_proxima_busca_alvo[personagem] <= 0.0
            ):
                self._tempo_proxima_busca_alvo[personagem] = self._intervalo_busca_alvo
                if metricas is not None:
                    metricas.contar("buscas_recurso")
                if adquirir_recurso(personagem):
                    usecase.executar(dt)
                    return

        if defendendo:
            return

        ctrl["padrao"].executar(dt, personagem)

    @staticmethod
    def _defender_soldado(soldado):
        estado = (
            EstadoSoldado.DEFENDENDO_FLIP
            if soldado.animacoes.maquina.flip
            else EstadoSoldado.DEFENDENDO
        )
        soldado.destino_x = soldado.x
        soldado.destino_y = soldado.y
        soldado.animacoes.estado = estado

    def processar_toque_down(self, pos_virtual, permitir_duplo_clique=True):
        menu = self.gerenciador_cenarios.menu_contextual
        camera = self.gerenciador_cenarios.camera
        mouse_mundo = camera.mundo(*pos_virtual)
        detectar_duplo = (
            self.double_click.detectar
            if permitir_duplo_clique
            else (lambda _pos: False)
        )

        audio_rect = getattr(self.gerenciador_cenarios, "audio_hud_rect", None)
        # Todas as entradas de toque chegam aqui em coordenadas virtuais
        # com origem no topo. O HUD também é desenhado com origem no topo,
        # portanto o retângulo do ícone pode ser usado diretamente.
        if audio_rect is not None and audio_rect.collidepoint(pos_virtual):
            self.gerenciador_cenarios.audio_manager.alternar_musica_vila_duendes()
            camera.arrastando = False
            camera.ultimo_mouse = None
            return

        if not menu.aberto:
            for construcao in self.gerenciador_cenarios.construcoes:
                if (
                    construcao.corpo_rect is not None
                    and construcao.corpo_rect.collidepoint(mouse_mundo)
                ):
                    if detectar_duplo(mouse_mundo):
                        menu.abrir_personagens(construcao)
                        camera.arrastando = False
                        camera.ultimo_mouse = None
                        return
                    break

        if menu.aberto:
            opcao = menu.obter_opcao_clicada(pos_virtual)

            if opcao:
                if menu.modo == "soldado":
                    if detectar_duplo(pos_virtual):
                        if menu.soldado_alvo is not None:
                            self._defender_soldado(menu.soldado_alvo)
                            menu.soldado_alvo.selecionado = False
                        menu.fechar()
                    return

                if menu.modo == "personagens":
                    if detectar_duplo(pos_virtual):
                        self.construir.criar_personagem_na_construcao(
                            self.gerenciador_cenarios,
                            opcao,
                            menu.construcao_alvo,
                        )
                    return

                # Construções continuam sendo posicionadas por arraste.
                self.construir.iniciar_arraste(
                    mouse_mundo,
                    self.gerenciador_cenarios,
                    construcao=opcao,
                )
                return

            if detectar_duplo(pos_virtual):
                # Um duplo clique em um personagem, mesmo com outro menu
                # aberto, troca imediatamente para o menu de construções.
                for personagem in self.gerenciador_cenarios.personagens:
                    if (
                        personagem.corpo_rect is not None
                        and personagem.corpo_rect.collidepoint(mouse_mundo)
                    ):
                        if personagem.nome == "soldado":
                            menu.abrir_soldado(personagem)
                        else:
                            menu.abrir_construcoes()
                        personagem.selecionado = False
                        camera.arrastando = False
                        camera.ultimo_mouse = None
                        return

                # Um duplo clique em uma construção troca imediatamente
                # para o menu de recrutamento daquela construção.
                for construcao in self.gerenciador_cenarios.construcoes:
                    if (
                        construcao.corpo_rect is not None
                        and construcao.corpo_rect.collidepoint(mouse_mundo)
                    ):
                        menu.abrir_personagens(construcao)
                        camera.arrastando = False
                        camera.ultimo_mouse = None
                        return

                # Duplo clique fora do menu fecha o menu atual.
                menu.fechar()
                camera.arrastando = False
                camera.ultimo_mouse = None
                return

            # Clique fora do painel não é bloqueado pelo menu.
            # O mapa continua podendo ser arrastado normalmente.
            camera.arrastando = True
            camera.ultimo_mouse = pos_virtual
            return

        for personagem in self.gerenciador_cenarios.personagens:
            if personagem.corpo_rect and personagem.corpo_rect.collidepoint(
                mouse_mundo
            ):
                if detectar_duplo(mouse_mundo):
                    if personagem.nome == "soldado":
                        menu.abrir_soldado(personagem)
                    else:
                        menu.abrir_construcoes()
                    personagem.selecionado = False
                    return

                if not personagem.animacoes.maquina.carregando_recuso():
                    for p in self.gerenciador_cenarios.personagens:
                        p.selecionado = False

                    personagem.selecionado = True
                    return

        # ==========================================================
        # Descobre quem está selecionado
        # ==========================================================
        personagem = next(
            (p for p in self.gerenciador_cenarios.personagens if p.selecionado),
            None,
        )

        if personagem and not personagem.animacoes.maquina.carregando_recuso():
            personagem_hostil = (
                personagem in self.gerenciador_cenarios.personagens_hostis
            )

            if personagem_hostil:
                construcoes_alvo = self.gerenciador_cenarios.construcoes
            else:
                construcoes_alvo = self.gerenciador_cenarios.construcoes_hostis

            for construcao in construcoes_alvo:
                rect = self.gerenciador_cenarios.obter_rect_colisao(construcao)
                if rect is None or not rect.collidepoint(mouse_mundo):
                    continue

                ctrl = self.gerenciador_cenarios.controladores.get(personagem)
                if ctrl is None:
                    continue

                atacar = ctrl["acoes"].get("atacar")
                if atacar is None:
                    continue

                atacar["usecase"].iniciar(construcao, personagem, manual=True)
                personagem.selecionado = False
                return

        # ==========================================================
        # Recursos
        # ==========================================================
        if personagem and not personagem.animacoes.maquina.carregando_recuso():
            ctrl = self.gerenciador_cenarios.controladores[personagem]

            for outra_acao in ctrl["acoes"].values():
                usecase = outra_acao["usecase"]
                cancelar = getattr(usecase, "cancelar", None)
                if cancelar is not None:
                    cancelar()
                else:
                    usecase.entidade_alvo = None

            for acao in ctrl["acoes"].values():
                itens = acao["itens"]

                if itens and isinstance(itens[0], list):
                    listas = itens
                else:
                    listas = [itens]

                for lista in listas:
                    for item in lista:
                        if item.corpo_rect is not None and item.corpo_rect.collidepoint(
                            mouse_mundo
                        ):
                            iniciar = acao["usecase"].iniciar
                            manual = getattr(item, "nome", None) == "carne"
                            iniciou = iniciar(
                                item,
                                personagem,
                                manual=manual,
                            )

                            if iniciou is not False:
                                personagem.selecionado = False
                                return

        # ==========================================================
        # Clique no chão
        # ==========================================================
        if personagem and not personagem.animacoes.maquina.carregando_recuso():
            self.trocar_comportamento.executar(
                controlador=ctrl,
                personagem=personagem,
                navegacao=self.gerenciador_cenarios.navegacao,
                destino_x=mouse_mundo[0],
                destino_y=mouse_mundo[1],
            )

            personagem.selecionado = False
            return

        camera.arrastando = True
        camera.ultimo_mouse = pos_virtual

    def processar_toque_up(self, pos_virtual):
        camera = self.gerenciador_cenarios.camera
        camera.arrastando = False
        camera.ultimo_mouse = None
        mouse_mundo = self.gerenciador_cenarios.camera.mundo(*pos_virtual)

        if self.gerenciador_cenarios.construcao_arrastando:
            self.construir.finalizar_arraste(
                mouse_mundo,
                self.gerenciador_cenarios,
            )

    def processar_on_touch_move(self, pos_virtual):
        camera = self.gerenciador_cenarios.camera

        if camera.arrastando:
            dx = pos_virtual[0] - camera.ultimo_mouse[0]
            dy = pos_virtual[1] - camera.ultimo_mouse[1]

            camera.arrastar(dx, dy)

            camera.ultimo_mouse = pos_virtual
            return

        mouse_mundo = camera.mundo(*pos_virtual)

        if self.gerenciador_cenarios.construcao_arrastando:
            self.construir.atualizar_arraste(
                mouse_mundo,
                self.gerenciador_cenarios,
            )
            return
