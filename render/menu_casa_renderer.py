import kivy_adapter
from core.mouse_events import Hover
from domains.personagem.entity import criar_aldeao, criar_goblin_tocha, criar_soldado
from render.menu_renderer import MenuRenderer
from render.sprite_animado_renderer import SpriteAnimadoRenderer


class MenuCasaRenderer:
    def __init__(self, tela, assets, transform):
        self.tela = tela

        self.aldeao = criar_aldeao()
        self.soldado = criar_soldado()
        self.goblin_tocha = criar_goblin_tocha()

        self.renderer_aldeao = SpriteAnimadoRenderer(
            tela,
            assets,
            transform,
            "aldeao",
            1.0,
        )

        self.renderer_soldado = SpriteAnimadoRenderer(
            tela,
            assets,
            transform,
            "soldado",
            1.0,
        )

        self.renderer_goblin_tocha = SpriteAnimadoRenderer(
            tela,
            assets,
            transform,
            "goblin_tocha",
            1.0,
        )

        self.menu_renderer = MenuRenderer(
            tela,
            assets,
            transform,
        )

        self.opcoes = [
            {
                "personagem": self.aldeao,
                "renderer": self.renderer_aldeao,
                "frames": 10,
            },
            {
                "personagem": self.soldado,
                "renderer": self.renderer_soldado,
                "frames": 5,
            },
            {
                "personagem": self.goblin_tocha,
                "renderer": self.renderer_goblin_tocha,
                "frames": 5,
            },
        ]

    def atualizar_carregamento(self):
        self.menu_renderer.atualizar_carregamento()

        for opcao in self.opcoes:
            opcao["renderer"].atualizar_carregamento(
                opcao["frames"],
            )

    def obter_opcao_clicada(self, pos, cenario):
        for opcao in self.opcoes:
            personagem = opcao["personagem"]

            if not cenario.personagem_desbloqueado(personagem):
                continue

            if personagem.corpo_rect and personagem.corpo_rect.collidepoint(pos):
                return personagem

        return None

    def obter_renderer(self, personagem):
        for opcao in self.opcoes:
            if opcao["personagem"].nome == personagem.nome:
                return opcao["renderer"]

    def renderizar(self, construcao, cenario, camera):
        if not construcao.menu_aberto:
            return

        MENU_X = self.tela.get_width() - 220
        MENU_Y = 40

        slots = self.menu_renderer.renderizar(
            MENU_X,
            MENU_Y,
            len(self.opcoes),
        )

        for slot, opcao in zip(slots, self.opcoes):
            personagem = opcao["personagem"]
            renderer = opcao["renderer"]

            personagem.x = slot.centerx
            personagem.y = slot.centery

            alpha = 255 if cenario.personagem_desbloqueado(personagem) else 90

            camera_x = camera.x
            camera_y = camera.y

            camera.x = 0
            camera.y = 0

            renderer.renderizar(
                personagem,
                personagem.animacoes,
                camera,
                alpha,
            )

            camera.x = camera_x
            camera.y = camera_y

            if Hover.esta_sobre(personagem.corpo_rect):
                kivy_adapter.draw.text(
                    self.tela,
                    f"Carne {cenario.total_carne}/{personagem.custo_carne}",
                    (slot.left - 20, slot.bottom + 5),
                    (255, 255, 255),
                    15,
                )
