# =====================================
# render/duende_renderer.py
# =====================================

import math
import pygame_adapter


class DuendeRenderer:

    def __init__(
        self,
        tela,
        assets,
        transform
    ):

        self.tela = tela
        self.assets = assets
        self.transform = transform
        self.cache_sombras = {}

        self.carregar_assets()

    # =====================================
    # LOAD
    # =====================================

    def carregar_assets(self):

        # =================================
        # BODY
        # =================================

        self.nuvem1 = self.assets.carregar(
            "clima/duende_neblina/nuvem1.png"
        )

        self.nuvem2 = self.assets.carregar(
            "clima/duende_neblina/nuvem2.png"
        )

        self.olho_esquerdo = self.assets.carregar(
            "clima/duende_neblina/olho_esquerdo.png"
        )

        self.olho_direito = self.assets.carregar(
            "clima/duende_neblina/olho_direito.png"
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
        alpha=255,
        rotacao=0
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
            (largura, altura)
        )

        imagem.set_alpha(alpha)

        

        # =================================
        # SPRITE
        # =================================

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

    def obter_sombra(
        self,
        escala
    ):

        chave = round(
            escala,
            2
        )

        if chave in self.cache_sombras:
            return self.cache_sombras[chave]

        sombra = pygame_adapter.Surface(
            (140, 60),
            pygame_adapter.SRCALPHA
        )

        pygame_adapter.draw.ellipse(
            sombra,
            (0, 0, 0, 45),
            (0, 0, 140, 60)
        )

        sombra = self.transform.escalar(
            sombra,
            (
                int(140 * escala),
                int(60 * escala)
            )
        )

        self.cache_sombras[chave] = sombra

        return sombra

    def renderizar(
        self,
        duende
    ):

        escala = (
            duende.escala
            * duende.escala_visual
        )

        fator_sono = duende.animacoes.fator_sono_visual

        # =================================
        # ESCALAS
        # =================================

        body_scale = (
            escala
            * (
                1.0
                - (0.20 * fator_sono)
            )
        )

        eye_scale = body_scale * 0.52

        # =================================
        # POSIÇÕES BASE
        # =================================

        body_x = duende.x

        body_y = duende.y

        imagem_corpo = self.nuvem1

        body_width = int(
            imagem_corpo.get_width() * body_scale
        )

        body_height = int(
            imagem_corpo.get_height() * body_scale
        )

        duende.atualizar_hitboxes(
            body_x,
            body_y,
            body_width,
            body_height
        )

        # =================================
        # OLHOS
        # =================================

        olho_esq_x = body_x + (10 * escala * 15)
        olho_dir_x = body_x - (10 * escala * 12)

        olho_esq_y = body_y - (3 * escala * 11)
        olho_dir_y = body_y - (3 * escala * 8)

        # =================================
        # SOMBRA
        # =================================

        shadow_surface = self.obter_sombra(
            escala
        )

        self.tela.blit(
            shadow_surface,
            (
                body_x - shadow_surface.get_width() // 2,
                body_y + (20 * escala)
            )
        )

        # =================================
        # BRILHO MÁGICO
        # =================================

        transicao_luz = (
            math.sin(
                duende.respiracao.tempo * 1.9
            ) + 1
        ) / 2

        transicao_luz = transicao_luz ** 2

        # =================================
        # BODY
        # =================================

        imagem_corpo = (
            self.nuvem1
            if transicao_luz < 0.5
            else self.nuvem2
        )

        self.draw(
            imagem_corpo,
            body_x,
            body_y,
            body_scale,
            alpha=duende.alpha_visual
        )

        # =================================
        # EYES
        # =================================

        if (
            not duende.animacoes.dormindo
            and not duende.animacoes.piscando
            and duende.escala_visual >= 0.98
        ):

            self.draw(
                self.olho_esquerdo,
                olho_esq_x,
                olho_esq_y,
                eye_scale
            )

            self.draw(
                self.olho_direito,
                olho_dir_x,
                olho_dir_y,
                eye_scale
            )