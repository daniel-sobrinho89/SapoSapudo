from application.usecases import (
    ConstruirUseCase,
    TrocarComportamentoUseCase,
)
from application.usecases.sapudo.controlar_sapudo_manual import (
    ControlarSapudoManualUseCase,
)
from core.mouse_events import DoubleClickDetector
from utils.kivy_adapter import Rect


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
        self.sapudo_manual = ControlarSapudoManualUseCase(gerenciador_cenarios)

    def executar(self, dt, teclas=None):
        sapudo = self._obter_sapudo()
        if sapudo is not None and self.sapudo_manual.sapudo is not sapudo:
            self.sapudo_manual.definir_sapudo(sapudo)

        if teclas is not None:
            self.sapudo_manual.teclas = set(teclas)

        conversa = self.gerenciador_cenarios.conversa_controller
        conversa_aberta = conversa.aberta
        if getattr(conversa, "evolucao_pendente", False):
            self._deixar_personagens_ociosos()
            return
        if conversa_aberta:
            self._deixar_personagens_ociosos()
            return

        self.sapudo_manual.atualizar(dt)
        # Durante o editor visual, a câmera pertence ao editor. Não deixe o
        # acompanhamento automático do Sapudo sobrescrever o foco escolhido.
        if not self.gerenciador_cenarios.world_editor_ativo:
            sapudo_atual = self._obter_sapudo()
            if sapudo_atual is not None and getattr(sapudo_atual, "visivel", True):
                self.gerenciador_cenarios.camera.seguir(sapudo_atual)
        metricas = getattr(self.gerenciador_cenarios, "metricas_desempenho", None)
        if metricas is not None:
            metricas.contar("ticks_coordenador")

        for personagem in (
            self.gerenciador_cenarios.personagens
            + self.gerenciador_cenarios.personagens_hostis
        ):
            if getattr(personagem, "visivel", True) is False:
                continue
            if personagem.nome == "sapudo":
                continue
            if (
                personagem.nome == "aldeao"
                and self.gerenciador_cenarios.conversa_controller.bernardo_ocupado_pela_quest
            ):
                continue

            # Roubão é controlado diretamente pela missão enquanto aparece,
            # conversa, retorna do combate e corre até a caverna. A IA hostil
            # genérica não pode transformar Sapudo em alvo durante esse fluxo.
            if (
                personagem
                is getattr(
                    self.gerenciador_cenarios.conversa_controller, "roubao", None
                )
                and self.gerenciador_cenarios.conversa_controller.roubao_controlado_pela_quest
            ):
                continue
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

            if entidade.nome == "casa_construindo":
                continue

            ctrl = self.gerenciador_cenarios.controladores.get(entidade)
            if ctrl is None:
                continue

            if entidade.vida <= 0 and ctrl.get("morte") is not None:
                if ctrl["morte"].entidade_alvo is None:
                    ctrl["morte"].iniciar(entidade)
                else:
                    ctrl["morte"].executar(dt)

            ctrl["padrao"].executar(dt)

    def _executar_fluxo_personagem(self, personagem, dt):
        ctrl = self.gerenciador_cenarios.controladores[personagem]
        metricas = getattr(self.gerenciador_cenarios, "metricas_desempenho", None)

        # Uma agressão recebida é uma ordem explícita de combate. Ela tem
        # prioridade sobre a IA autônoma e funciona mesmo durante patrulha.
        agressor = getattr(personagem, "_agressor_pendente", None)
        if agressor is not None and personagem.vida > 0:
            ataque_ctrl = ctrl.get("acoes", {}).get("atacar")
            if ataque_ctrl is not None:
                ataque_ctrl["usecase"].iniciar(agressor, personagem)
            personagem._agressor_pendente = None

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

        defendendo = personagem.animacoes.esta_em("defendendo")

        # Enquanto uma entidade está na guarda, não inicia nem continua uma
        # ação de ataque. A própria animação/estado termina a defesa.
        if defendendo:
            personagem.destino_x = personagem.x
            personagem.destino_y = personagem.y
            return

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
        estado = "defendendo_flip" if soldado.animacoes.flip else "defendendo"
        soldado.destino_x = soldado.x
        soldado.destino_y = soldado.y
        soldado.animacoes.definir(estado)

    def _obter_sapudo(self):
        return next(
            (p for p in self.gerenciador_cenarios.personagens if p.nome == "sapudo"),
            None,
        )

    def _deixar_personagens_ociosos(self):
        for personagem in (
            self.gerenciador_cenarios.personagens
            + self.gerenciador_cenarios.personagens_hostis
        ):
            if getattr(personagem, "visivel", True) is False:
                continue
            personagem.destino_x = personagem.x
            personagem.destino_y = personagem.y
            personagem.animacoes.definir("ocioso", flip=personagem.animacoes.flip)

    def processar_tecla_down(self, tecla):
        conversa = self.gerenciador_cenarios.conversa_controller
        if getattr(conversa, "evolucao_pendente", False):
            if tecla in ("1", "numpad1"):
                conversa.escolher_evolucao("ataque")
            elif tecla in ("2", "numpad2"):
                conversa.escolher_evolucao("defesa")
            return
        if tecla == "f3":
            self.gerenciador_cenarios.alternar_world_debug()
            return
        if tecla == "f4":
            self.gerenciador_cenarios.alternar_world_editor()
            return
        if self.gerenciador_cenarios.world_editor_ativo and tecla in ("+", "igual"):
            self.gerenciador_cenarios.camera.aproximar()
            return
        if self.gerenciador_cenarios.world_editor_ativo and tecla in ("-", "minus"):
            self.gerenciador_cenarios.camera.afastar()
            return
        if (
            tecla == "e"
            or tecla == "enter"
            and self.gerenciador_cenarios.conversa_controller.aberta
        ):
            self.gerenciador_cenarios.conversa_controller.tecla_interagir()
        else:
            self.sapudo_manual.tecla_down(tecla)

    def processar_tecla_up(self, tecla):
        self.sapudo_manual.tecla_up(tecla)

    @staticmethod
    def _personagem_em_coleta(personagem):
        """Indica se o personagem está executando uma coleta de recurso."""
        if personagem is None:
            return False
        animacoes = personagem.animacoes
        return any(
            animacoes.esta_em(nome)
            for nome in (
                "correndo_madeira",
                "correndo_ouro",
                "correndo_carne",
            )
        )

    def processar_toque_down(self, pos_virtual, permitir_duplo_clique=True):
        conversa = self.gerenciador_cenarios.conversa_controller

        if getattr(conversa, "evolucao_pendente", False):
            x, y = 610, 108
            ataque_rect = (x + 22, y + 76, 54, 54)
            defesa_rect = (x + 210, y + 76, 54, 54)
            px, py = pos_virtual

            def _dentro(rect):
                rx, ry, rw, rh = rect
                return rx <= px <= rx + rw and ry <= py <= ry + rh

            if _dentro(ataque_rect):
                conversa.escolher_evolucao("ataque")
                return True
            if _dentro(defesa_rect):
                conversa.escolher_evolucao("defesa")
                return True
            return True

        menu = self.gerenciador_cenarios.menu_contextual
        camera = self.gerenciador_cenarios.camera
        if menu is None:
            camera.arrastando = False
            camera.ultimo_mouse = None
            return True
        mouse_mundo = camera.mundo(*pos_virtual)
        detectar_duplo = (
            self.double_click.detectar
            if permitir_duplo_clique
            else (lambda _pos: False)
        )

        audio_rect = getattr(self.gerenciador_cenarios, "audio_hud_rect", None)
        if audio_rect is not None and audio_rect.collidepoint(pos_virtual):
            cenario = self.gerenciador_cenarios.cenario_principal
            cenario.menu_jogo_aberto = not getattr(cenario, "menu_jogo_aberto", False)
            camera.arrastando = False
            camera.ultimo_mouse = None
            return True

        cenario = self.gerenciador_cenarios.cenario_principal
        if getattr(cenario, "menu_jogo_aberto", False):
            botoes = getattr(cenario, "menu_jogo_botoes", {})
            for nome, rect in botoes.items():
                if rect.collidepoint(pos_virtual):
                    if nome == "salvar":
                        cenario.save_game.salvar()
                    elif nome == "carregar":
                        cenario.save_game.carregar()
                    elif nome == "musica":
                        cenario.audio_manager.alternar_musica_vila_duendes()
                    cenario.menu_jogo_status = (
                        getattr(cenario.save_game, "ultimo_status", "")
                        if nome != "musica"
                        else (
                            "Música ligada"
                            if cenario.audio_manager.musica_vila_tocando
                            else "Música desligada"
                        )
                    )
                    camera.arrastando = False
                    camera.ultimo_mouse = None
                    return True
            menu_rect = (
                Rect(
                    min(r.x for r in botoes.values()),
                    min(r.y for r in botoes.values()),
                    220,
                    172,
                )
                if botoes
                else None
            )
            if menu_rect is not None and menu_rect.collidepoint(pos_virtual):
                camera.arrastando = False
                camera.ultimo_mouse = None
                return True

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

                self.construir.iniciar_arraste(
                    mouse_mundo,
                    self.gerenciador_cenarios,
                    construcao=opcao,
                )
                return

            if detectar_duplo(pos_virtual):
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

                for construcao in self.gerenciador_cenarios.construcoes:
                    if (
                        construcao.corpo_rect is not None
                        and construcao.corpo_rect.collidepoint(mouse_mundo)
                    ):
                        menu.abrir_personagens(construcao)
                        camera.arrastando = False
                        camera.ultimo_mouse = None
                        return

                menu.fechar()
                camera.arrastando = False
                camera.ultimo_mouse = None
                return

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

                if not self._personagem_em_coleta(personagem):
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

        if personagem and not self._personagem_em_coleta(personagem):
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

                if getattr(construcao, "nome", None) == "caverna":
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
        if personagem and not self._personagem_em_coleta(personagem):
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
        if personagem and not self._personagem_em_coleta(personagem):
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
