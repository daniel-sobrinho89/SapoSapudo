class ViolaoRenderer:

    VIOLAO_SCALE = 0.15

    def __init__(
        self,
        tela,
        assets,
        transform
    ):

        self.tela = tela
        self.transform = transform

        original = assets.carregar(
            "sapudo/violao.webp"
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