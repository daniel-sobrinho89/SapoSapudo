import pygame


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

        self.olho_esquerdo_rect = pygame.Rect(
            -1000,
            -1000,
            1,
            1
        )

        self.olho_direito_rect = pygame.Rect(
            -1000,
            -1000,
            1,
            1
        )

        self.corpo_rect = pygame.Rect(
            -1000,
            -1000,
            1,
            1
        )

        self.respiracao_violao = 1.0
        self.frame_violao_anterior = 0

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

        self.corpo_violao1 = self.assets.carregar(
            "sapudo/corpo_violao1.png"
        )

        self.corpo_violao2 = self.assets.carregar(
            "sapudo/corpo_violao2.png"
        )

        self.corpo_violao3 = self.assets.carregar(
            "sapudo/corpo_violao3.png"
        )

        self.corpo_violao4 = self.assets.carregar(
            "sapudo/corpo_violao4.png"
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

        self.eye_right_open = self.assets.carregar(
            "eye_right_open.png"
        )

        # =================================
        # BOCA
        # =================================

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
        animacoes,
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

        VIOLAO_BODY_SCALE = 0.50
        VIOLAO_BODY_OFFSET_Y = 55

        if animacoes.tocando_violao:

            frame_atual = (
                animacoes.frame_violao
            )

            if (
                frame_atual == 0
                and self.frame_violao_anterior != 0
            ):
                self.respiracao_violao = (
                    escalas["body"] / escala
                )

            self.frame_violao_anterior = frame_atual

            body_scale = (
                escala
                * self.respiracao_violao
                * 1.06
            )

        else:

            self.frame_violao_anterior = 0

            body_scale = (
                escalas["body"] * 1.06
            )

        head_scale = escalas["head"] * 0.93

        shadow_scale = escalas["shadow"]

        body_y = centro_y

        sleep_offset_y = (
            animacoes.sleep_offset_y
        )

        head_y = (
            centro_y
            - (
                6 * escala_personagem
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

        body = self.body

        if animacoes.tocando_violao:

            frames = [
                self.corpo_violao1,
                self.corpo_violao2,
                self.corpo_violao3,
                self.corpo_violao4
            ]

            body = frames[
                animacoes.frame_violao
            ]

            body_scale *= VIOLAO_BODY_SCALE

            body_y += VIOLAO_BODY_OFFSET_Y

        self.draw(
            body,
            centro_x,
            body_y,
            body_scale
        )

        largura_corpo = max(
            1,
            int(body.get_width() * body_scale)
        )

        altura_corpo = max(
            1,
            int(body.get_height() * body_scale)
        )

        margem_x = int(largura_corpo * 0.15)
        margem_y = int(altura_corpo * 0.10)

        self.corpo_rect = pygame.Rect(
            centro_x - largura_corpo // 2 + margem_x,
            body_y - altura_corpo // 2 + margem_y,
            largura_corpo - margem_x * 2,
            altura_corpo - margem_y * 2
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
                    24.7 * escala_personagem
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
                37 * escala_personagem
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
            animacoes.olhos_fechados
        )

        olho_esquerdo_fechado = (
            animacoes.olhos_fechados
            or animacoes.olho_esquerdo_forcado
        )

        olho_direito_fechado = (
            animacoes.olhos_fechados
            or animacoes.olho_direito_forcado
        )

        olho_esquerdo = self.eye_left_open
        olho_direito = self.eye_right_open

        # =================================
        # POSIÇÕES BASE
        # =================================

        olho_esquerdo_x = (
            centro_x - (
                21 * escala_personagem
            )
        )

        olho_direito_x = (
            centro_x + (
                20 * escala_personagem
            )
        )

        # =================================
        # CONFIG GERAL
        # =================================

        alpha_sombra = 140

        offset_y_olhos = (
            -14 * escala_personagem
        )

        escala_olhos = (
            escala
            * 0.30
            * (
                1.0
                + (
                    0.015
                    * respiracao.intensidade
                )
            )
        )

        # =================================
        # POSIÇÃO FINAL OLHOS
        # =================================

        olhos_y = (
            head_y + offset_y_olhos
        )

        largura_hitbox = int(
            30 * escala_personagem
        )

        altura_hitbox = int(
            30 * escala_personagem
        )

        self.olho_esquerdo_rect = pygame.Rect(
            olho_esquerdo_x - largura_hitbox // 2,
            olhos_y - altura_hitbox // 2,
            largura_hitbox,
            altura_hitbox
        )

        self.olho_direito_rect = pygame.Rect(
            olho_direito_x - largura_hitbox // 2,
            olhos_y - altura_hitbox // 2,
            largura_hitbox,
            altura_hitbox
        )

        # =================================
        # DRAW EYES
        # =================================

        if not olho_esquerdo_fechado:

            self.draw(
                olho_esquerdo,
                olho_esquerdo_x,
                olhos_y,
                escala_olhos
            )

        if not olho_direito_fechado:

            self.draw(
                olho_direito,
                olho_direito_x,
                olhos_y,
                escala_olhos
            )

        # =================================
        # MOUTH
        # =================================

        boca = (
            animacoes.obter_asset_boca(
                self.mouth_yawn
            )
        )

        if animacoes.boca_yawn:

            escala_boca_x = (
                escala
                * 0.20
                * (
                    1.0
                    + (
                        0.015
                        * respiracao.intensidade
                    )
                )
            )

            escala_boca_y = (
                escala
                * 0.18
                * (
                    1.0
                    + (
                        0.015
                        * respiracao.intensidade
                    )
                )
            )

            offset_y_boca = (
                8 * escala_personagem
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
        if boca:

            self.draw(
                boca,
                centro_x,
                head_y + offset_y_boca,
                escala_boca_x,
                escala_boca_y
            )