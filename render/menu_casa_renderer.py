import kivy_adapter
from core.mouse_events import Hover
from render.menu_renderer import MenuRenderer


class MenuCasaRenderer:
    def __init__(self, tela, assets, transform, cenario):
        self.tela = tela
        self.aberto = False

        self.menu_renderer = MenuRenderer(
            tela,
            assets,
            transform,
        )

        self.opcoes = [
            cenario.carregar_entidade("avatar_aldeao"),
            cenario.carregar_entidade("avatar_soldado"),
        ]

    def atualizar_carregamento(self):
        self.menu_renderer.atualizar_carregamento()

    def obter_opcao_clicada(self, pos):
        for opcao in self.opcoes:
            if opcao.corpo_rect and opcao.corpo_rect.collidepoint(pos):
                return opcao

        return None

    def renderizar(self, cenario, camera):
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
            renderer = cenario.renderers[opcao.nome]

            opcao.x = slot.centerx
            opcao.y = slot.centery

            alpha = 255 if cenario.personagem_desbloqueado(opcao) else 90

            camera_x = camera.x
            camera_y = camera.y

            camera.x = 0
            camera.y = 0

            renderer.renderizar(opcao, opcao.animacoes, camera, alpha)

            camera.x = camera_x
            camera.y = camera_y

            if Hover.esta_sobre(opcao.corpo_rect):
                kivy_adapter.draw.text(
                    self.tela,
                    f"Carne {cenario.total_carne}/{opcao.custo_carne}",
                    (slot.left - 20, slot.bottom + 5),
                    (255, 255, 255),
                    15,
                )
