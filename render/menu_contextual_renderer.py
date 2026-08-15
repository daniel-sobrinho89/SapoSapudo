import utils.kivy_adapter as kivy_adapter
from core.game_config import obter_config
from core.mouse_events import Hover
from render.menu_renderer import MenuRenderer


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
        self.opcoes = []

        self._opcoes_construcoes = [
            cenario.carregar_entidade_temporaria("castelo"),
            cenario.carregar_entidade_temporaria("casa"),
            cenario.carregar_entidade_temporaria("quartel"),
        ]

        self._temporarias = {opcao.nome: opcao for opcao in self._opcoes_construcoes}

        for nome in ("avatar_aldeao", "avatar_soldado"):
            opcao = cenario.carregar_entidade_temporaria(nome)
            self._temporarias[nome] = opcao

    def atualizar_carregamento(self):
        self.menu_renderer.atualizar_carregamento()

    def abrir_construcoes(self):
        self.aberto = True
        self.modo = "construcoes"
        self.construcao_alvo = None
        self.opcoes = self._opcoes_construcoes

    def abrir_personagens(self, construcao):
        nomes = self.OPCOES_PERSONAGENS.get(construcao.nome, ())
        self.aberto = bool(nomes)
        self.modo = "personagens" if self.aberto else None
        self.construcao_alvo = construcao if self.aberto else None
        self.opcoes = [self._temporarias[nome] for nome in nomes]

    def fechar(self):
        self.aberto = False
        self.modo = None
        self.construcao_alvo = None
        self.opcoes = []

    def obter_opcao_clicada(self, pos):
        for opcao in self.opcoes:
            if opcao.corpo_rect and opcao.corpo_rect.collidepoint(pos):
                return opcao
        return None

    def renderizar(self, cenario, camera):
        if not self.aberto:
            return

        self.menu_renderer.atualizar_carregamento()

        # Mantém um único menu no centro da tela, independente do conteúdo.
        self.menu_renderer.renderizar(
            self.tela.get_width() // 2 - self.menu_renderer.passo_x,
            35,
            len(self.opcoes),
        )

        slots = self.menu_renderer.ultimo_slots

        for slot, opcao in zip(slots, self.opcoes):
            renderer = cenario.renderers[opcao.nome]

            opcao.x = slot.centerx
            opcao.y = slot.centery

            camera_x = camera.x
            camera_y = camera.y
            camera.x = 0
            camera.y = 0

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
            else:
                alpha = 255 if cenario.personagem_desbloqueado(opcao) else 90
                renderer.renderizar(
                    opcao,
                    opcao.animacoes,
                    camera,
                    alpha,
                )

            camera.x = camera_x
            camera.y = camera_y

            if not Hover.esta_sobre(opcao.corpo_rect):
                continue

            if self.modo == "construcoes":
                kivy_adapter.draw.text(
                    self.tela,
                    f"Madeira {cenario.total_madeira}/{opcao.custo_madeira}",
                    (slot.left - 20, slot.bottom + 5),
                    (255, 255, 255),
                    15,
                )
                kivy_adapter.draw.text(
                    self.tela,
                    f"Ouro {cenario.total_ouro}/{opcao.custo_ouro}",
                    (slot.left - 20, slot.bottom + 22),
                    (255, 255, 255),
                    15,
                )
                continue

            kivy_adapter.draw.text(
                self.tela,
                f"Carne {cenario.total_carne}/{opcao.custo_carne}",
                (slot.left - 20, slot.bottom + 5),
                (255, 255, 255),
                15,
            )
