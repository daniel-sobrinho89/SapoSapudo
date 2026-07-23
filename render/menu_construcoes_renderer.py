import kivy_adapter
from core.mouse_events import Hover
from domains.construcao.entity import criar_casa, criar_castelo
from render.construcao_render import ConstrucaoRenderer
from render.menu_renderer import MenuRenderer


class MenuConstrucoesRenderer:
    def __init__(
        self,
        tela,
        assets,
        transform,
    ):
        self.tela = tela
        self.assets = assets
        self.transform = transform

        self.castelo = criar_castelo()
        self.renderer_castelo = ConstrucaoRenderer(
            tela, assets, transform, "castelo", 1, 0.25
        )
        self.casa = criar_casa()
        self.renderer_casa = ConstrucaoRenderer(
            tela, assets, transform, "casa", 1, 0.25
        )

        self.menu_renderer = MenuRenderer(
            tela,
            assets,
            transform,
        )
        self.opcoes = [
            {
                "construcao": self.castelo,
                "renderer": self.renderer_castelo,
            },
            {
                "construcao": self.casa,
                "renderer": self.renderer_casa,
            },
        ]

    def atualizar_carregamento(self):
        self.menu_renderer.atualizar_carregamento()
        self.renderer_castelo.atualizar_carregamento()
        self.renderer_casa.atualizar_carregamento()

    def obter_opcao_clicada(self, pos):
        for opcao in self.opcoes:
            construcao = opcao["construcao"]
            if construcao.corpo_rect and construcao.corpo_rect.collidepoint(pos):
                return construcao

        return None

    def obter_renderer(self, construcao):
        for opcao in self.opcoes:
            if opcao["construcao"].nome == construcao.nome:
                return opcao["renderer"]

    def renderizar(
        self,
        aldeao,
        cenario,
    ):
        if not aldeao.menu_construcoes_aberto:
            return

        MENU_X = self.tela.get_width() - 220
        MENU_Y = 20

        slots = self.menu_renderer.renderizar(
            MENU_X,
            MENU_Y,
            len(self.opcoes),
        )

        for (slot_x, slot_y), opcao in zip(slots, self.opcoes):
            construcao = opcao["construcao"]
            renderer = opcao["renderer"]

            construcao.x = slot_x
            construcao.y = slot_y

            alpha = 255 if cenario.construcao_desbloqueada(construcao) else 90

            if construcao.nome == "Castelo" and cenario.possui_castelo:
                alpha = 90

            construcao.x = slot_x
            construcao.y = slot_y

            renderer.renderizar(
                construcao,
                construcao.animacoes,
                alpha,
            )

            if Hover.esta_sobre(construcao.corpo_rect):
                kivy_adapter.draw.text(
                    self.tela,
                    f"Madeira {cenario.total_madeira}/{construcao.custo_madeira}",
                    (slot_x - 25, slot_y + 35),
                    (255, 255, 255),
                    15,
                )

                kivy_adapter.draw.text(
                    self.tela,
                    f"Ouro {cenario.total_ouro}/{construcao.custo_ouro}",
                    (slot_x - 25, slot_y + 52),
                    (255, 255, 255),
                    15,
                )
