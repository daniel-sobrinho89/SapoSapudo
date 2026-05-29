# =====================================
# render/duende_renderer.py
# =====================================

import math
import pygame


class DuendeRenderer:

    def __init__(
        self,
        tela,
        assets
    ):

        self.tela = tela
        self.assets = assets

        self.carregar_assets()

    # =====================================
    # LOAD
    # =====================================

    def carregar_assets(self):

        # =================================
        # BODY
        # =================================

        self.body = self.assets.carregar(
            "clima/duende_neblina/corpo.png"
        )

        self.body_aceso = self.assets.carregar(
            "clima/duende_neblina/corpo_aceso.png"
        )

        # =================================
        # HEAD
        # =================================

        self.head = self.assets.carregar(
            "clima/duende_neblina/cabeca.png"
        )

        # =================================
        # EYES
        # =================================

        self.olho_esq_aberto = self.assets.carregar(
            "clima/duende_neblina/olho_esquerdo_aberto.png"
        )

        self.olho_dir_aberto = self.assets.carregar(
            "clima/duende_neblina/olho_direito_aberto.png"
        )

        self.olho_esq_fechado = self.assets.carregar(
            "clima/duende_neblina/olho_esquerdo_fechado.png"
        )

        self.olho_dir_fechado = self.assets.carregar(
            "clima/duende_neblina/olho_direito_fechado.png"
        )

        # =================================
        # ASAS SUPERIORES
        # =================================

        self.asa_sup_esq = self.assets.carregar(
            "clima/duende_neblina/asa_esquerda_superior.png"
        )

        self.asa_sup_dir = self.assets.carregar(
            "clima/duende_neblina/asa_direita_superior.png"
        )

        # =================================
        # ASAS INFERIORES
        # =================================

        self.asa_inf_esq = self.assets.carregar(
            "clima/duende_neblina/asa_esquerda_inferior.png"
        )

        self.asa_inf_dir = self.assets.carregar(
            "clima/duende_neblina/asa_direita_inferior.png"
        )

        # =================================
        # ASAS FECHADAS
        # =================================

        self.asa_sup_esq_fechada = self.assets.carregar(
            "clima/duende_neblina/asa_esquerda_superior_fechada.png"
        )

        self.asa_sup_dir_fechada = self.assets.carregar(
            "clima/duende_neblina/asa_direita_superior_fechada.png"
        )

        # =================================
        # ASAS INCLINADAS
        # =================================

        self.asa_sup_esq_inclinada = self.assets.carregar(
            "clima/duende_neblina/asa_esquerda_superior_inclinada.png"
        )

        self.asa_sup_dir_inclinada = self.assets.carregar(
            "clima/duende_neblina/asa_direita_superior_inclinada.png"
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

        imagem = pygame.transform.smoothscale(
            imagem,
            (largura, altura)
        ).convert_alpha()

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

        intensidade = (
            duende.respiracao.intensidade
        )

        fator_asa = (
            duende.batimento_asas + 1
        ) / 2

        escala = duende.escala

        # =================================
        # ESCALAS
        # =================================

        body_scale = escala * (
            1.0 + (
                intensidade * 0.010
            )
        )

        head_scale = escala * 0.82 * (
            1.0 + (
                intensidade * 0.004
            )
        )

        eye_scale = escala * (
            0.34
            + (
                intensidade * 0.004
            )
        )

        wing_scale_sup = (escala * 0.80) * (
            1.0
            + (
                intensidade * 0.015
            )
            - (
                fator_asa * 0.08
            )
        )

        wing_scale_sup_dir_fechada = wing_scale_sup * 0.70
        wing_scale_sup_esq_fechada = wing_scale_sup * 0.65

        wing_scale_inf = (
            wing_scale_sup * 0.72
        )

        # =================================
        # POSIÇÕES BASE
        # =================================

        body_x = duende.x
        body_y = duende.y

        # =================================
        # CABEÇA
        # =================================

        head_float_y = intensidade * (
            0.8 * escala
        )

        head_float_x = math.sin(
            duende.respiracao.tempo * 1.2
        ) * (
            0.4 * escala
        )

        head_x = (
            body_x
            + head_float_x
        )

        head_y = (
            body_y
            - (320 * escala)
            + head_float_y
        )

        # =================================
        # OLHOS
        # =================================

        eyes_y = (
            head_y
            - (15 * escala)
        )

        eye_offset_x = (
            100 * escala
        )

        olho_dir_x = (
            head_x
            - eye_offset_x
        )

        olho_esq_x = (
            head_x
            + eye_offset_x
        )

        # =================================
        # SOMBRA
        # =================================

        shadow_surface = pygame.Surface(
            (140, 60),
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(
            shadow_surface,
            (0, 0, 0, 45),
            (0, 0, 140, 60)
        )

        shadow_surface = pygame.transform.smoothscale(
            shadow_surface,
            (
                int(140 * escala),
                int(60 * escala)
            )
        )

        self.tela.blit(
            shadow_surface,
            (
                body_x - shadow_surface.get_width() // 2,
                body_y + (20 * escala)
            )
        )

        # =================================
        # POSIÇÃO DAS ASAS
        # =================================

        # SUPERIORES

        asa_sup_dir_x = (
            body_x - (78 * escala)
        )

        asa_sup_esq_x = (
            body_x + (95 * escala)
        )

        asa_sup_dir_y = (
            body_y - (185 * escala)
        )

        asa_sup_esq_y = (
            body_y - (85 * escala)
        )

        asa_sup_dir_y_fechada = (
            asa_sup_dir_y
            + (90 * escala)
        )

        asa_sup_esq_y_fechada = (
            asa_sup_esq_y
            + (40 * escala)
        )

        # INFERIORES

        asa_inf_dir_x = (
            body_x - (90 * escala)
        )

        asa_inf_esq_x = (
            body_x + (78 * escala)
        )

        asa_inf_dir_y = (
            body_y - (140 * escala)
        )

        asa_inf_esq_y = (
            body_y - (120 * escala)
        )

        # =================================
        # NORMAL
        # =================================

        if not duende.animacoes.dormindo:

            # =============================
            # ASAS INFERIORES
            # =============================

            self.draw(
                self.asa_inf_dir,
                asa_inf_dir_x,
                asa_inf_dir_y,
                wing_scale_inf
            )

            self.draw(
                self.asa_inf_esq,
                asa_inf_esq_x,
                asa_inf_esq_y,
                wing_scale_inf
            )

            # =============================
            # ASAS SUPERIORES
            # =============================

            self.draw(
                self.asa_sup_dir,
                asa_sup_dir_x,
                asa_sup_dir_y,
                wing_scale_sup
            )

            self.draw(
                self.asa_sup_esq,
                asa_sup_esq_x,
                asa_sup_esq_y,
                wing_scale_sup
            )

        # =================================
        # BRILHO MÁGICO
        # =================================

        transicao_luz = (
            math.sin(
                duende.respiracao.tempo * 0.7
            ) + 1
        ) / 2

        transicao_luz = transicao_luz ** 4

        # =================================
        # BODY
        # =================================

        alpha_normal = int(
            255 * (1 - transicao_luz)
        )

        alpha_aceso = int(
            255 * transicao_luz
        )

        self.draw(
            self.body,
            body_x,
            body_y,
            body_scale,
            alpha=alpha_normal
        )

        self.draw(
            self.body_aceso,
            body_x,
            body_y,
            body_scale,
            alpha=alpha_aceso
        )

        # =================================
        # DORMINDO
        # =================================

        if duende.animacoes.dormindo:

            self.draw(
                self.asa_sup_esq_fechada,
                asa_sup_esq_x,
                asa_sup_esq_y_fechada,
                wing_scale_sup_esq_fechada
            )

            self.draw(
                self.asa_sup_dir_fechada,
                asa_sup_dir_x,
                asa_sup_dir_y_fechada,
                wing_scale_sup_dir_fechada
            )

        # =================================
        # HEAD
        # =================================

        self.draw(
            self.head,
            head_x,
            head_y,
            head_scale
        )

        # =================================
        # EYES
        # =================================

        if (
            duende.animacoes.piscando
            or duende.animacoes.dormindo
        ):

            olho_esq = (
                self.olho_esq_fechado
            )

            olho_dir = (
                self.olho_dir_fechado
            )

        else:

            olho_esq = (
                self.olho_esq_aberto
            )

            olho_dir = (
                self.olho_dir_aberto
            )

        eye_scale_dir = eye_scale
        eye_scale_esq = eye_scale * 0.93

        self.draw(
            olho_dir,
            olho_dir_x,
            eyes_y,
            eye_scale_dir
        )

        self.draw(
            olho_esq,
            olho_esq_x,
            eyes_y,
            eye_scale_esq
        )

        # =================================
        # MOUTH
        # =================================

        mouth_x = head_x

        mouth_y = (
            head_y
            + (110 * head_scale)
        )

        mouth_size = int(
            12 * escala
        )

        p1 = (
            mouth_x - mouth_size // 2,
            mouth_y
        )

        p2 = (
            mouth_x,
            mouth_y + int(1 * escala)
        )

        p3 = (
            mouth_x + mouth_size // 2,
            mouth_y
        )

        pygame.draw.aaline(
            self.tela,
            (45, 65, 65),
            p1,
            p2
        )

        pygame.draw.aaline(
            self.tela,
            (45, 65, 65),
            p2,
            p3
        )