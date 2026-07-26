import kivy_adapter
from core.mouse_events import Hover
from render.menu_renderer import MenuRenderer


class MenuConstrucoesRenderer:
    def __init__(self, tela, assets, transform, cenario):
        self.tela = tela
        self.assets = assets
        self.transform = transform
        self.aberto = False

        self.menu_renderer = MenuRenderer(
            tela,
            assets,
            transform,
        )
        self.opcoes = [
            {
                "construcao": cenario.castelo,
                "renderer": cenario.renderer_castelo,
            },
            {
                "construcao": cenario.casa,
                "renderer": cenario.renderer_casa,
            },
            {
                "construcao": cenario.quartel,
                "renderer": cenario.renderer_quartel,
            },
        ]

    def atualizar_carregamento(self):
        self.menu_renderer.atualizar_carregamento()

    def obter_opcao_clicada(self, pos):
        for opcao in self.opcoes:
            construcao = opcao["construcao"]
            if construcao.corpo_rect and construcao.corpo_rect.collidepoint(pos):
                return construcao

        return None

    def renderizar(
        self,
        cenario,
        camera,
    ):
        if not self.aberto:
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
