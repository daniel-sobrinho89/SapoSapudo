from render.asset_manager import asset_manager


class BarracaRenderer:

    def __init__(
        self,
        tela,
        transform,
        largura_tela,
        altura_tela
    ):

        self.tela = tela

        imagem = asset_manager.carregar(
            "tamandudo/barraca.png"
        )

        self.imagem = transform.escalar(
            imagem,
            (260, 180)
        )

        # Posição inicial:
        # um pouco à esquerda do centro
        self.x = (largura_tela // 2) - 260

        # apoiada no chão
        self.y = altura_tela - self.imagem.get_height() - 20

    def definir_posicao(self, x, y):

        self.x = x
        self.y = y

    def obter_posicao(self):

        return self.x, self.y

    def obter_rect(self):

        return self.imagem.get_rect(
            topleft=(self.x, self.y)
        )

    def renderizar(self):

        self.tela.blit(
            self.imagem,
            (self.x, self.y)
        )