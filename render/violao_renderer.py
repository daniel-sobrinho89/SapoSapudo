import pygame


class ViolaoRenderer:

    VIOLAO_SCALE = 0.10

    def __init__(
        self,
        tela,
        assets,
        transform
    ):

        self.tela = tela
        self.transform = transform

        original = assets.carregar(
            "sapudo/violao.png"
        )

        largura = int(
            original.get_width()
            * self.VIOLAO_SCALE
        )

        altura = int(
            original.get_height()
            * self.VIOLAO_SCALE
        )

        self.violao = self.transform.escalar(
            original,
            (
                largura,
                altura
            )
        )

    def renderizar(
        self,
        entidade
    ):

        rect = self.violao.get_rect(
            center=(
                entidade.x,
                entidade.y
            )
        )
        # Não atribuir rect à entidade — entidade não deve depender de pygame
        self.tela.blit(
            self.violao,
            rect
        )

    def obter_rect(self, entidade):
        return self.violao.get_rect(
            center=(
                entidade.x,
                entidade.y
            )
        )