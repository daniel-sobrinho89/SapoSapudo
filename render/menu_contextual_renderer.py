import utils.kivy_adapter as kivy_adapter
from core.game_config import obter_config
from render.menu_renderer import MenuRenderer
from utils.input import obter_posicao_ponteiro


class MenuContextualRenderer:
    """Menu único para construção de estruturas e recrutamento."""

    OPCOES_PERSONAGENS = {
        "casa": ("avatar_aldeao",),
        "quartel": ("avatar_soldado",),
    }

    def __init__(self, tela, assets, transform, cenario):
        self.tela = tela
        self.cenario = cenario
        self.menu_renderer = MenuRenderer(tela, assets, transform)

        self.aberto = False
        self.modo = None
        self.construcao_alvo = None
        self.soldado_alvo = None
        self.opcoes = []

        self._opcoes_construcoes = [
            cenario.carregar_entidade_temporaria("castelo"),
            cenario.carregar_entidade_temporaria("casa"),
            cenario.carregar_entidade_temporaria("quartel"),
        ]

        self._temporarias = {opcao.nome: opcao for opcao in self._opcoes_construcoes}

        self._renderers_temporarias = {
            nome: cenario.renderers[nome] for nome in ("castelo", "casa", "quartel")
        }

        for nome in ("avatar_aldeao", "avatar_soldado", "escudo"):
            opcao = cenario.carregar_entidade_temporaria(nome)
            self._temporarias[nome] = opcao

    def atualizar_carregamento(self):
        self.menu_renderer.atualizar_carregamento()

        for nome in (
            "castelo",
            "casa",
            "quartel",
            "avatar_aldeao",
            "avatar_soldado",
            "escudo",
        ):
            renderer = self.cenario.renderers.get(nome)
            if renderer is None or renderer.carregado:
                continue

            config = obter_config(nome)
            renderer.atualizar_carregamento(
                max(1, min(int(config["renderer"]["frames_carregamento"]), 2))
            )

    def abrir_construcoes(self):
        self.aberto = True
        self.modo = "construcoes"
        self.construcao_alvo = None
        self.soldado_alvo = None
        self.opcoes = self._opcoes_construcoes

    def abrir_soldado(self, soldado):
        self.aberto = True
        self.modo = "soldado"
        self.construcao_alvo = None
        self.soldado_alvo = soldado
        self.opcoes = [self._temporarias["escudo"]]

    def abrir_personagens(self, construcao):
        nomes = self.OPCOES_PERSONAGENS.get(construcao.nome, ())
        self.aberto = bool(nomes)
        self.modo = "personagens" if self.aberto else None
        self.construcao_alvo = construcao if self.aberto else None
        self.soldado_alvo = None
        self.opcoes = [self._temporarias[nome] for nome in nomes]

    def fechar(self):
        self.aberto = False
        self.modo = None
        self.construcao_alvo = None
        self.soldado_alvo = None
        self.opcoes = []

    def _posicao_mouse_menu(self):
        """Retorna o ponteiro no mesmo sistema de coordenadas dos slots.

        O backend web ja fornece o mouse em coordenadas de tela com origem no
        topo, exatamente como o ``MenuRenderer`` grava em ``_menu_slot_rect``.
        Nao passamos pelo helper global de input no web porque ele converte
        coordenadas para o sistema Kivy e inverte o eixo Y. No desktop/Kivy,
        mantemos o comportamento anterior.
        """
        if getattr(kivy_adapter, "IS_BROWSER", False):
            try:
                return tuple(map(int, kivy_adapter.mouse.get_pos()))
            except Exception:
                return (0, 0)

        return obter_posicao_ponteiro()

    def obter_opcao_clicada(self, pos):
        # O HUD e os eventos de toque usam o mesmo sistema de coordenadas.
        # O ponto recebido já está pronto para testar contra o retângulo
        # visual do slot.
        pos_menu = pos

        for opcao in self.opcoes:
            slot = getattr(opcao, "_menu_slot_rect", None)
            if slot is not None and slot.collidepoint(pos_menu):
                return opcao
        return None

    def renderizar(self, cenario, camera):
        if not self.aberto:
            return

        self.menu_renderer.atualizar_carregamento()

        centralizar_itens = self.modo not in ("personagens", "soldado")

        largura_menu, altura_menu = self.menu_renderer.obter_dimensoes(
            len(self.opcoes),
            centralizar_itens=centralizar_itens,
        )

        margem_direita = -40
        margem_topo = -40

        x_menu = max(
            0,
            self.tela.get_width() - largura_menu - margem_direita,
        )
        y_menu = margem_topo

        self.menu_renderer.renderizar(
            x_menu,
            y_menu,
            len(self.opcoes),
            centralizar_itens=centralizar_itens,
        )

        slots = self.menu_renderer.ultimo_slots

        for slot, opcao in zip(slots, self.opcoes):
            renderer = cenario.renderers[opcao.nome]

            # O renderer do personagem usa coordenadas de mundo, mas o slot
            # do HUD precisa permanecer em coordenadas de tela. Guardamos o
            # retangulo real do slot para hover/click.
            opcao._menu_slot_rect = slot
            opcao.x = slot.centerx
            # O renderer do menu desenha diretamente no Surface, cujo eixo Y
            # tem origem no topo. Mantemos a posição visual do sprite alinhada
            # ao slot, sem convertê-la para as coordenadas de entrada.
            opcao.y = slot.centery

            camera_x = camera.x
            camera_y = camera.y
            camera_zoom = camera.zoom

            # HUD: o menu não herda o zoom do mapa.
            camera.x = 0
            camera.y = 0
            camera.zoom = 1.0

            if self.modo == "construcoes":
                config = obter_config(opcao.nome)
                escala = config["renderer"]["escala_menu"]
                alpha = 255 if cenario.construcao_desbloqueada(opcao) else 90
                renderer.renderizar(
                    opcao,
                    opcao.animacoes,
                    camera,
                    alpha,
                    escala,
                )
            elif self.modo == "personagens":
                alpha = 255 if cenario.personagem_desbloqueado(opcao) else 90
                renderer.renderizar(
                    opcao,
                    opcao.animacoes,
                    camera,
                    alpha,
                )
            else:
                renderer.renderizar(
                    opcao,
                    opcao.animacoes,
                    camera,
                    255,
                )

            camera.x = camera_x
            camera.y = camera_y
            camera.zoom = camera_zoom

            mouse_menu = self._posicao_mouse_menu()
            if not slot.collidepoint(mouse_menu):
                continue

            if self.modo == "soldado":
                kivy_adapter.draw.text(
                    self.tela,
                    "Defender",
                    (slot.left - 20, slot.bottom + 5),
                    (255, 255, 255),
                    15,
                )
                continue

            # Todos os personagens e construções usam a mesma exibição de
            # custos. Recursos com custo zero continuam visíveis para deixar
            # explícito que não são exigidos para aquela opção.
            custos = (
                ("Madeira", cenario.total_madeira, getattr(opcao, "custo_madeira", 0)),
                ("Ouro", cenario.total_ouro, getattr(opcao, "custo_ouro", 0)),
                ("Carne", cenario.total_carne, getattr(opcao, "custo_carne", 0)),
            )
            base_x = max(4, slot.left - 20)
            base_y = slot.bottom + 6

            # Sempre desenha o bloco abaixo do slot. Se a ultima linha passar
            # do limite inferior do HUD, sobe o bloco inteiro para permanecer
            # visivel.
            altura_texto = len(custos) * 17
            if base_y + altura_texto > self.tela.get_height() - 4:
                base_y = max(4, self.tela.get_height() - 4 - altura_texto)

            for indice, (nome_recurso, disponivel, necessario) in enumerate(custos):
                kivy_adapter.draw.text(
                    self.tela,
                    f"{nome_recurso} {disponivel}/{necessario}",
                    (base_x, base_y + indice * 17),
                    (255, 255, 255),
                    15,
                )
