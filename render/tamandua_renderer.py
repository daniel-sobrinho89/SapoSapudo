from render.asset_manager import asset_manager


class TamanduaRenderer:

    def __init__(self, tela, transform):

        self.tela = tela
        self.transform = transform

        self.frames = []

        for i in range(60):
            nome = (
                f"tamandudo/parado/tamanduo_{i:04d}.webp"
            )

            frame = asset_manager.carregar(nome)

            frame = transform.escalar(
                frame,
                (180, 180)
            )

            self.frames.append(frame)

        self.frame_atual = 0
        self.tempo = 0

        # NOVO
        self.x = 0
        self.y = 0

    def definir_posicao(
        self,
        x,
        y
    ):
        self.x = x
        self.y = y

    def atualizar(self, dt):

        self.tempo += dt

        if self.tempo >= 0.12:
            self.tempo = 0

            self.frame_atual = (
                self.frame_atual + 1
            ) % len(self.frames)

    def renderizar(self):

        self.tela.blit(
            self.frames[self.frame_atual],
            (
                self.x,
                self.y
            )
        )