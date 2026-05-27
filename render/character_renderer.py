import pygame


class CharacterRenderer:

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

        self.shadow = self.assets.carregar(
            "shadow.png"
        )

        self.body = self.assets.carregar(
            "body.png"
        )

        self.head = self.assets.carregar(
            "head.png"
        )

        self.leaf = self.assets.carregar(
            "leaf.png"
        )

        # =================================
        # OLHOS
        # =================================

        self.eye_left_open = self.assets.carregar(
            "eye_left_open.png"
        )

        self.eye_left_closed = self.assets.carregar(
            "eye_left_closed.png"
        )

        self.eye_right_open = self.assets.carregar(
            "eye_right_open.png"
        )

        self.eye_right_closed = self.assets.carregar(
            "eye_right_closed.png"
        )

        # =================================
        # SOMBRAS
        # =================================

        self.eye_left_shadow_open = self.assets.carregar(
            "eye_left_shadow_open.png"
        )

        self.eye_right_shadow_open = self.assets.carregar(
            "eye_right_shadow_open.png"
        )

        self.eye_left_shadow_closed = self.assets.carregar(
            "eye_left_shadow_closed.png"
        )

        self.eye_right_shadow_closed = self.assets.carregar(
            "eye_right_shadow_closed.png"
        )

        # =================================
        # BLUSH
        # =================================

        self.blush_left = self.assets.carregar(
            "blush_left.png"
        )

        self.blush_right = self.assets.carregar(
            "blush_right.png"
        )

        # =================================
        # NARIZ
        # =================================

        self.nose = self.assets.carregar(
            "nose.png"
        )

        # =================================
        # BOCA
        # =================================

        self.mouth_normal = self.assets.carregar(
            "mouth_smiling.png"
        )

        self.mouth_yawn = self.assets.carregar(
            "mouth_yawn.png"
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
            (
                largura,
                altura
            )
        ).convert_alpha()

        imagem.set_alpha(alpha)

        rect = imagem.get_rect(
            center=(x, y)
        )

        self.tela.blit(
            imagem,
            rect
        )

    # =====================================
    # HEAD DEPTH SHADOW
    # =====================================

    def desenhar_sombra_cabeca(
        self,
        x,
        y,
        largura,
        altura,
        alpha
    ):

        sombra = pygame.Surface(
            (largura, altura),
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(
            sombra,
            (0, 0, 0, alpha),
            (
                0,
                0,
                largura,
                altura
            )
        )

        rect = sombra.get_rect(
            center=(x, y)
        )

        self.tela.blit(
            sombra,
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
        escala_personagem,
        respiracao,
        animacoes_faciais,
        animacao_folha,
        ambiente
    ):

        escalas = respiracao.obter_escalas(
            escala
        )

        # =================================
        # OFFSET SOMBRA CABEÇA
        # =================================

        offset_sombra_cabeca = (
            respiracao.obter_offset_sombra_cabeca()
        )

        # =================================
        # PROPORÇÕES
        # =================================

        body_scale = escalas["body"] * 1.06

        head_scale = escalas["head"] * 0.93

        shadow_scale = escalas["shadow"]

        body_y = centro_y

        sleep_offset_y = (
            animacoes_faciais.sleep_offset_y
        )

        head_y = (
            centro_y
            - (
                36 * escala_personagem
            )
            + sleep_offset_y
        )

        shadow_y = (
            centro_y
            + (
                12 * escala_personagem
            )
        )

        # =================================
        # SHADOW BODY
        # =================================

        self.draw(
            self.shadow,
            centro_x,
            shadow_y,
            shadow_scale,
            alpha=95
        )

        # =================================
        # BODY
        # =================================

        self.draw(
            self.body,
            centro_x,
            body_y,
            body_scale
        )

        # =================================
        # HEAD
        # =================================

        self.draw(
            self.head,
            centro_x,
            head_y,
            head_scale
        )

        # =================================
        # HEAD DEPTH SHADOW
        # =================================

        self.desenhar_sombra_cabeca(
            centro_x,
            (
                head_y
                + (
                    37.5 * escala_personagem
                )
                + offset_sombra_cabeca
            ),
            int(escala * 152),
            int(escala * 7),
            28
        )

        # =================================
        # FOLHA
        # =================================

        rotacao_folha = (
            animacao_folha.obter_rotacao()
        )

        # =================================
        # MICRO MOVIMENTO NATURAL
        # =================================

        offset_folha_x = (
            animacao_folha.obter_offset_x()
        )

        offset_folha_y = (
            animacao_folha.obter_offset_y()
        )

        # =================================
        # MOVIMENTO HERDADO
        # DA RESPIRAÇÃO
        # =================================

        resp_folha_x, resp_folha_y = (
            animacao_folha.obter_offset_respiracao(
                respiracao.intensidade
            )
        )

        # =================================
        # POSIÇÃO BASE
        # =================================

        inclinacao_folha = (
            rotacao_folha * 0.12
        )

        folha_x = (
            centro_x
            + offset_folha_x
            + resp_folha_x
            + inclinacao_folha
        )

        folha_y = (
            head_y
            - (
                44 * escala_personagem
            )
            + offset_folha_y
            + resp_folha_y
            - abs(inclinacao_folha * 0.15)
        )

        # =================================
        # ESCALA
        # =================================

        folha = self.transform.escalar(
            self.leaf,
            escala * 0.40
        )

        # =================================
        # ROTAÇÃO
        # =================================

        folha = self.transform.rotacionar(
            folha,
            rotacao_folha
        )

        # =================================
        # ALPHA
        # =================================

        folha.set_alpha(235)

        # =================================
        # RECT
        # =================================

        folha_rect = folha.get_rect(
            center=(
                folha_x,
                folha_y
            )
        )

        # =================================
        # DRAW
        # =================================

        self.tela.blit(
            folha,
            folha_rect
        )

        # =================================
        # ESTADO DOS OLHOS
        # =================================

        olhos_fechados = (
            animacoes_faciais.olhos_fechados
        )

        olho_esquerdo = (
            animacoes_faciais.obter_asset_olho(
                self.eye_left_open,
                self.eye_left_closed
            )
        )

        olho_direito = (
            animacoes_faciais.obter_asset_olho(
                self.eye_right_open,
                self.eye_right_closed
            )
        )

        # =================================
        # POSIÇÕES BASE
        # =================================

        olho_esquerdo_x = (
            centro_x - (
                26 * escala_personagem
            )
        )

        olho_direito_x = (
            centro_x + (
                26 * escala_personagem
            )
        )

        # =================================
        # CONFIG OLHOS
        # =================================

        if not olhos_fechados:

            offset_y_olhos = (
                -8 * escala_personagem
            )

            escala_olhos = (
                escala * 0.34
            )

            sombra_esquerda = (
                self.eye_left_shadow_open
            )

            sombra_direita = (
                self.eye_right_shadow_open
            )

            alpha_sombra = 140

        else:

            offset_y_olhos = (
                -3 * escala_personagem
            )

            escala_olhos = (
                escala * 0.22
            )

            olho_esquerdo = pygame.transform.rotate(
                olho_esquerdo,
                -5
            )

            olho_direito = pygame.transform.rotate(
                olho_direito,
                5
            )

            sombra_esquerda = (
                self.eye_left_shadow_closed
            )

            sombra_direita = (
                self.eye_right_shadow_closed
            )

            alpha_sombra = 70

        # =================================
        # POSIÇÃO FINAL OLHOS
        # =================================

        olhos_y = (
            head_y + offset_y_olhos
        )

        # =================================
        # SOMBRAS
        # =================================

        if not olhos_fechados:
            
            # =================================
            # SOMBRA ESQUERDA
            # =================================
            offset_sombra_esquerda_x = 0
            offset_sombra_esquerda_y = 9.8

            sombra_esquerda_x = (
                olho_esquerdo_x
                + (offset_sombra_esquerda_x * escala_personagem)
            )

            sombra_esquerda_y = (
                olhos_y
                + (offset_sombra_esquerda_y * escala_personagem)
            )

            sombra_esquerda_scale_x = (
                escala * 0.150
            )

            sombra_esquerda_scale_y = (
                escala * 0.112
            )
            
            # =================================
            # SOMBRA DIREITA
            # =================================
            offset_sombra_direita_x = 1
            offset_sombra_direita_y = 9

            sombra_direita_x = (
                olho_direito_x
                + (offset_sombra_direita_x * escala_personagem)
            )

            sombra_direita_y = (
                olhos_y
                + (offset_sombra_direita_y * escala_personagem)
            )

            sombra_direita_scale_x = (
                escala * 0.23
            )

            sombra_direita_scale_y = (
                escala * 0.18
            )

        else:

            sombra_esquerda_x = olho_esquerdo_x

            sombra_direita_x = olho_direito_x

            sombra_esquerda_y = (
                olhos_y + (
                    1 * escala_personagem
                )
            )

            sombra_direita_y = (
                olhos_y + (
                    1 * escala_personagem
                )
            )

            sombra_esquerda_scale_x = (
                escala * 0.13
            )

            sombra_esquerda_scale_y = (
                escala * 0.07
            )

            sombra_direita_scale_x = (
                escala * 0.13
            )

            sombra_direita_scale_y = (
                escala * 0.07
            )

        # =================================
        # DRAW SHADOWS
        # =================================

        self.draw(
            sombra_esquerda,
            sombra_esquerda_x,
            sombra_esquerda_y,
            sombra_esquerda_scale_x,
            sombra_esquerda_scale_y,
            alpha_sombra
        )

        self.draw(
            sombra_direita,
            sombra_direita_x,
            sombra_direita_y,
            sombra_direita_scale_x,
            sombra_direita_scale_y,
            alpha_sombra
        )

        # =================================
        # DRAW EYES
        # =================================

        self.draw(
            olho_esquerdo,
            olho_esquerdo_x,
            olhos_y,
            escala_olhos
        )

        self.draw(
            olho_direito,
            olho_direito_x,
            olhos_y,
            escala_olhos
        )

        # =================================
        # BLUSH
        # =================================

        self.draw(
            self.blush_left,
            centro_x - (
                42 * escala_personagem
            ),
            head_y + (
                15 * escala_personagem
            ),
            escala * 0.24,
            alpha=180
        )

        self.draw(
            self.blush_right,
            centro_x + (
                39 * escala_personagem
            ),
            head_y + (
                15 * escala_personagem
            ),
            escala * 0.21,
            alpha=180
        )

        # =================================
        # NOSE
        # =================================

        self.draw(
            self.nose,
            centro_x,
            head_y + (
                5 * escala_personagem
            ),
            escala * 0.16
        )

        # =================================
        # MOUTH
        # =================================

        boca = (
            animacoes_faciais.obter_asset_boca(
                self.mouth_normal,
                self.mouth_yawn
            )
        )

        if animacoes_faciais.boca_yawn:

            escala_boca_x = (
                escala * 0.28
            )

            escala_boca_y = (
                escala * 0.24
            )

            offset_y_boca = (
                25 * escala_personagem
            )

        else:

            escala_boca_x = (
                escala * 0.36
            )

            escala_boca_y = (
                escala * 0.36
            )

            offset_y_boca = (
                24 * escala_personagem
            )

        # =================================
        # DRAW MOUTH
        # =================================

        self.draw(
            boca,
            centro_x,
            head_y + offset_y_boca,
            escala_boca_x,
            escala_boca_y
        )