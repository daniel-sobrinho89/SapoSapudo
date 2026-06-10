import pygame_adapter


class SapoRenderer:

    def __init__(
        self,
        tela,
        assets,
        transform
    ):

        self.tela = tela
        self.assets = assets
        self.transform = transform

        self.corpo_rect = pygame_adapter.Rect(
            -1000,
            -1000,
            1,
            1
        )

        self.carregar_assets()

    # =====================================
    # LOAD
    # =====================================

    def carregar_assets(self):

        self.frames_acordar = []
        for i in range(60):

            self.frames_acordar.append(
                self.assets.carregar(
                    f"sapudo/acordar/sapudo_{i:04d}.webp"
                )
            )

        self.frames_parado = []
        for i in range(60):

            self.frames_parado.append(
                self.assets.carregar(
                    f"sapudo/parado/sapudo_{i:04d}.webp"
                )
            )

        self.frames_dormir = []
        for i in range(60):

            self.frames_dormir.append(
                self.assets.carregar(
                    f"sapudo/dormir/sapudo_{i:04d}.webp"
                )
            )

        self.frames_dormindo = []
        for i in range(9):

            self.frames_dormindo.append(
                self.assets.carregar(
                    f"sapudo/dormindo/sapudo_{i:04d}.webp"
                )
            )

        self.frames_pegar_violao = []
        for i in range(15):

            self.frames_pegar_violao.append(
                self.assets.carregar(
                    f"sapudo/pegar_violao/sapudo_{i:04d}.webp"
                )
            )

        self.frames_tocar_violao = []
        for i in range(10):

            self.frames_tocar_violao.append(
                self.assets.carregar(
                    f"sapudo/tocar_violao/sapudo_{i:04d}.webp"
                )
            )

        self.frames_levantar_violao = []
        for i in range(15):
            self.frames_levantar_violao.append(
                self.assets.carregar(
                    f"sapudo/levantar_violao/sapudo_{i:04d}.webp"
                )
            )

        self.frames_guardar_violao = []
        for i in range(9):
            self.frames_guardar_violao.append(
                self.assets.carregar(
                    f"sapudo/guardar_violao/sapudo_{i:04d}.webp"
                )
            )

        self.frames_soltar_violao = []
        for i in range(9):
            self.frames_soltar_violao.append(
                self.assets.carregar(
                    f"sapudo/soltar_violao/sapudo_{i:04d}.webp"
                )
            )

        self.frames_andar_esquerda = []
        for i in range(10):
            self.frames_andar_esquerda.append(
                self.assets.carregar(
                    f"sapudo/andar_esquerda/sapudo_{i:04d}.webp"
                )
            )

    # =====================================
    # DRAW
    # =====================================

    def draw(
        self,
        imagem,
        x,
        y,
        escala_x,
        escala_y=None,
        alpha=255
    ):

        if escala_y is None:
            escala_y = escala_x

        largura = max(
            1,
            int(imagem.get_width() * escala_x)
        )

        altura = max(
            1,
            int(imagem.get_height() * escala_y)
        )

        imagem = self.transform.escalar(
            imagem,
            (
                largura,
                altura
            )
        )

        imagem.set_alpha(alpha)

        rect = imagem.get_rect(
            center=(x, y)
        )

        self.tela.blit(
            imagem,
            rect
        )


    # =====================================
    # RENDER
    # =====================================

    def renderizar(
        self,
        centro_x,
        centro_y,
        escala,
        animacoes
    ):
        if animacoes.adormecendo:

            frame = self.frames_dormir[
                animacoes.frame_dormir
            ]

        elif animacoes.dormindo:

            frame = self.frames_dormindo[
                animacoes.frame_dormindo
            ]

        elif animacoes.pegando_violao:

            frame = self.frames_pegar_violao[
                animacoes.frame_pegar_violao
            ]

        elif animacoes.tocando_violao:
            frame = self.frames_tocar_violao[
                animacoes.frame_violao
            ]

        elif animacoes.acordando:
            frame = self.frames_acordar[
                animacoes.frame_acordar
            ]

        elif animacoes.levantando_violao:
            frame = self.frames_levantar_violao[
                animacoes.frame_levantar_violao
            ]
            
        elif animacoes.andando_esquerda:
            frame = self.frames_andar_esquerda[
                animacoes.frame_andar_esquerda
            ]

        elif animacoes.guardando_violao:
            frame = self.frames_guardar_violao[
                animacoes.frame_guardar_violao
            ]

        elif animacoes.soltando_violao:

            frame = self.frames_soltar_violao[
                animacoes.frame_soltar_violao
            ]

        else:

            frame = self.frames_parado[
                animacoes.frame_parado
            ]

        self.draw(
            frame,
            centro_x,
            centro_y,
            escala
        )

        largura = int(
            frame.get_width() * escala
        )

        altura = int(
            frame.get_height() * escala
        )

        self.corpo_rect = pygame_adapter.Rect(
            centro_x - largura // 2,
            centro_y - altura // 2,
            largura,
            altura
        )