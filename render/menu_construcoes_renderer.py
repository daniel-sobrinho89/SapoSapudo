import kivy_adapter
from core.mouse_events import Hover
from domains.construcao.entity import criar_casa, criar_castelo, criar_quartel
from render.menu_renderer import MenuRenderer
from render.sprite_animado_renderer import SpriteAnimadoRenderer


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
        self.renderer_castelo = SpriteAnimadoRenderer(
            tela, assets, transform, "castelo", 0.25
        )
        self.casa = criar_casa()
        self.renderer_casa = SpriteAnimadoRenderer(
            tela, assets, transform, "casa", 0.25
        )
        self.quartel = criar_quartel()
        self.renderer_quartel = SpriteAnimadoRenderer(
            tela, assets, transform, "quartel", 0.25
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
            {
                "construcao": self.quartel,
                "renderer": self.renderer_quartel,
            },
        ]

    def atualizar_carregamento(self):
        self.menu_renderer.atualizar_carregamento()
        self.renderer_castelo.atualizar_carregamento()
        self.renderer_casa.atualizar_carregamento()
        self.renderer_quartel.atualizar_carregamento()

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
        camera,
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

        for slot, opcao in zip(slots, self.opcoes):
            construcao = opcao["construcao"]
            renderer = opcao["renderer"]

            construcao.x = slot.centerx
            construcao.y = slot.centery

            alpha = 255 if cenario.construcao_desbloqueada(construcao) else 90

            if construcao.nome == "Castelo" and cenario.possui_castelo:
                alpha = 90

            camera_x = camera.x
            camera_y = camera.y

            camera.x = 0
            camera.y = 0

            renderer.renderizar(
                construcao,
                construcao.animacoes,
                camera,
                alpha,
            )

            camera.x = camera_x
            camera.y = camera_y

            if Hover.esta_sobre(construcao.corpo_rect):
                kivy_adapter.draw.text(
                    self.tela,
                    f"Madeira {cenario.total_madeira}/{construcao.custo_madeira}",
                    (slot.left - 20, slot.bottom + 5),
                    (255, 255, 255),
                    15,
                )

                kivy_adapter.draw.text(
                    self.tela,
                    f"Ouro {cenario.total_ouro}/{construcao.custo_ouro}",
                    (slot.left - 20, slot.bottom + 22),
                    (255, 255, 255),
                    15,
                )
