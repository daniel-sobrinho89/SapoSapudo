import kivy_adapter
from core.mouse_events import Hover
from domains.aldeao.entity import criar_aldeao
from render.aldeao_renderer import AldeaoRenderer
from render.menu_renderer import MenuRenderer


class MenuCasaRenderer:
    def __init__(self, tela, assets, transform):
        self.tela = tela

        self.aldeao_preview = criar_aldeao()
        self.renderer_aldeao = AldeaoRenderer(tela, assets, transform, 1.0)
        self.menu_renderer = MenuRenderer(
            tela,
            assets,
            transform,
        )

    def atualizar_carregamento(self):
        self.menu_renderer.atualizar_carregamento()
        self.renderer_aldeao.atualizar_carregamento(10)

    def obter_opcao_clicada(self, pos):
        if (
            self.aldeao_preview.corpo_rect
            and self.aldeao_preview.corpo_rect.collidepoint(pos)
        ):
            return self.aldeao_preview

        return None

    def obter_renderer(self, personagem):
        if personagem.nome == "Aldeao":
            return self.renderer_aldeao

    def renderizar(
        self,
        construcao,
        cenario,
    ):
        if not construcao.menu_aberto:
            return

        MENU_X = self.tela.get_width() - 220
        MENU_Y = 40

        slots = self.menu_renderer.renderizar(MENU_X, MENU_Y, 1)

        slot_x, slot_y = slots[0]

        self.aldeao_preview.x = slot_x
        self.aldeao_preview.y = slot_y

        self.renderer_aldeao.renderizar(
            self.aldeao_preview,
            self.aldeao_preview.animacoes,
            alpha=255 if cenario.total_carne >= self.aldeao_preview.custo_carne else 90,
            x=slot_x,
            y=slot_y,
        )

        if Hover.esta_sobre(self.aldeao_preview.corpo_rect):
            kivy_adapter.draw.text(
                self.tela,
                f"Carne {cenario.total_carne}/{self.aldeao_preview.custo_carne}",
                (slot_x - 25, slot_y + 35),
                (255, 255, 255),
                15,
            )
