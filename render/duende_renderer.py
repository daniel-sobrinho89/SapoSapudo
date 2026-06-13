# =====================================
# render/duende_renderer.py
# =====================================

import math
import kivy_adapter


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

        eye_scale = body_scale * 0.40

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

        olho_offset_x = body_width * 0.07
        olho_offset_y = body_height * 0.06

        olho_esq_x = body_x + olho_offset_x + 1
        olho_dir_x = body_x - olho_offset_x

        olho_esq_y = body_y - olho_offset_y + 4
        olho_dir_y = body_y - olho_offset_y + 5

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