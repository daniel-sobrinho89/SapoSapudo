import math

import pygame

class SementeRenderer:

    def __init__(
        self,
        tela,
        assets
    ):

        self.tela = tela
        self.assets = assets

        self.corpo_aberto = (
            assets.carregar(
                "semente/corpo_boca_aberta.png"
            )
        )

        self.corpo_sorrindo = (
            assets.carregar(
                "semente/corpo_boca_sorrindo.png"
            )
        )

        self.olho_esquerdo = (
            assets.carregar(
                "semente/olho_esquerdo.png"
            )
        )

        self.olho_direito = (
            assets.carregar(
                "semente/olho_direito.png"
            )
        )

    def draw(
        self,
        imagem,
        x,
        y,
        escala,
        rotacao=0
    ):

        largura = int(
            imagem.get_width()
            * escala
        )

        altura = int(
            imagem.get_height()
            * escala
        )

        sprite = pygame.transform.smoothscale(
            imagem,
            (
                largura,
                altura
            )
        )

        sprite = pygame.transform.rotate(
            sprite,
            rotacao
        )

        rect = sprite.get_rect(
            center=(x, y)
        )

        self.tela.blit(
            sprite,
            rect
        )

    def renderizar(
        self,
        semente
    ):

        escala_corpo = 0.08
        escala_olho = 0.035

        corpo = (
            self.corpo_sorrindo
            if semente.sorrindo
            else self.corpo_aberto
        )

        x_render = (
            semente.x
            + semente.offset_flutuacao_x
        )

        y_render = (
            semente.y
            + semente.offset_flutuacao_y
        )

        if semente.flutuando:

            rotacao = (
                math.sin(
                    semente.fase_flutuacao
                )
                * 10
            )

        else:

            rotacao = max(
                -12,
                min(
                    12,
                    semente.vel_x * 0.4
                )
            )

        self.draw(
            corpo,
            x_render,
            y_render,
            escala_corpo,
            -rotacao
        )

        if semente.sorrindo:

            olho_esq_x = 6
            olho_esq_y = 1.5

            olho_dir_x = -11
            olho_dir_y = 2

        else:

            olho_esq_x = 7
            olho_esq_y = 2

            olho_dir_x = -8
            olho_dir_y = 2

        if not semente.piscando:

            self.draw(
                self.olho_esquerdo,
                x_render + olho_esq_x,
                y_render + olho_esq_y,
                escala_olho
            )

            self.draw(
                self.olho_direito,
                x_render + olho_dir_x,
                y_render + olho_dir_y,
                escala_olho
            )