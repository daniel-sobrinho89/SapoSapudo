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
        # FOLHA
        # =================================

        self.leaf = self.assets.carregar(
            "leaf.png"
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

    def desenhar_olho_fechado(
        self,
        x,
        y,
        dormindo=False
    ):

        if dormindo:

            pygame.draw.arc(
                self.tela,
                (25, 45, 55),
                (
                    int(x - 4),
                    int(y - 2),
                    8,
                    4
                ),
                math.pi,
                math.pi * 2,
                1
            )

        else:

            pygame.draw.arc(
                self.tela,
                (25, 45, 55),
                (
                    int(x - 3),
                    int(y - 1),
                    7,
                    4
                ),
                0,
                math.pi,
                1
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

        fator_sono = duende.animacoes.fator_sono_visual

        fator_semente = fator_sono ** 2

        # =================================
        # ESCALAS
        # =================================

        body_scale = (
            escala
            * (
                1.0
                - (0.99 * fator_sono)
            )
        )

        head_scale = (
            escala
            * (
                0.90
                + (
                    0.25 * fator_sono
                )
            )
            * (
                1.0
                + intensidade * 0.004
            )
        )

        wing_scale_sup = (
            (escala * 0.80)
            * (
                1.0
                - (0.98 * fator_sono)
            )
            * (
                1.0
                + (
                    intensidade * 0.015
                )
                - (
                    fator_asa * 0.08
                )
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

        body_y = (
            duende.y
            - (
                320 * escala
                * fator_semente
            )
        )

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
            duende.y
            - (320 * escala)
            + head_float_y
            + (
                220
                * escala
                * fator_semente
            )
        )

        head_width = int(
            self.head.get_width() * head_scale
        )

        head_height = int(
            self.head.get_height() * head_scale
        )

        duende.atualizar_hitboxes(
            head_x,
            head_y,
            head_width,
            head_height
        )

        # =================================
        # FOLHA
        # =================================

        rotacao_folha = (
            duende.animacao_folha.obter_rotacao()
        )

        offset_folha_x = (
            duende.animacao_folha.obter_offset_x()
        )

        offset_folha_y = (
            duende.animacao_folha.obter_offset_y()
        )

        resp_folha_x, resp_folha_y = (
            duende.animacao_folha.obter_offset_respiracao(
                duende.respiracao.intensidade
            )
        )

        # =================================
        # OLHOS
        # =================================

        eyes_y = head_y - 4

        eye_offset_x = 7.7

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
            body_x - (140 * escala)
        )

        asa_inf_esq_x = (
            body_x + (118 * escala)
        )

        asa_inf_dir_y = (
            body_y - (150 * escala)
        )

        asa_inf_esq_y = (
            body_y - (130 * escala)
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
                duende.respiracao.tempo * 1.9
            ) + 1
        ) / 2

        transicao_luz = transicao_luz ** 2

        # =================================
        # BODY
        # =================================

        if duende.animacoes.dormindo:

            self.draw(
                self.body,
                body_x,
                body_y,
                body_scale,
                alpha=255
            )

        else:

            alpha_normal = int(
                255 * (1 - transicao_luz * 0.8)
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
        # FOLHA
        # =================================

        inclinacao_folha = (
            rotacao_folha * 0.12
        )

        folha_x = (
            head_x
            + offset_folha_x
            + resp_folha_x
            + inclinacao_folha
            - 2
        )

        folha_y = (
            head_y
            - 34
            + offset_folha_y
            + resp_folha_y
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
        # DESENHO DA FOLHA
        # =================================

        escala_folha = (
            escala
            * (
                0.65
                + (
                    0.45 * fator_sono
                )
            )
        )

        folha = pygame.transform.smoothscale(
            self.leaf,
            (
                int(
                    self.leaf.get_width()
                    * escala_folha
                ),
                int(
                    self.leaf.get_height()
                    * escala_folha
                )
            )
        )

        folha = pygame.transform.rotate(
            folha,
            rotacao_folha
        )

        folha_rect = folha.get_rect(
            center=(
                folha_x,
                folha_y
            )
        )

        self.tela.blit(
            folha,
            folha_rect
        )

        # =================================
        # EYES
        # =================================

        raio_olho = 3

        if duende.animacoes.dormindo:

            self.desenhar_olho_fechado(
                olho_esq_x,
                eyes_y,
                dormindo=True
            )

            self.desenhar_olho_fechado(
                olho_dir_x,
                eyes_y,
                dormindo=True
            )

        elif duende.animacoes.piscando:

            self.desenhar_olho_fechado(
                olho_esq_x,
                eyes_y,
                dormindo=False
            )

            self.desenhar_olho_fechado(
                olho_dir_x,
                eyes_y,
                dormindo=False
            )

        else:

            pygame.draw.ellipse(
                self.tela,
                (25, 45, 55),
                (
                    olho_esq_x - 4 * escala,
                    eyes_y - 2 * escala,
                    8 * escala,
                    5 * escala
                )
            )

            pygame.draw.ellipse(
                self.tela,
                (25, 45, 55),
                (
                    olho_dir_x - 4 * escala,
                    eyes_y - 2 * escala,
                    8 * escala,
                    5 * escala
                )
            )

        # =================================
        # BOCA
        # =================================

        mouth_x = head_x

        mouth_y = (
            head_y
            + (65 * head_scale)
        )

        mouth_size = int(
            23 * escala
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