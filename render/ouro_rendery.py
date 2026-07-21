import kivy_adapter


class OuroRenderer:
    MAPA_ANIMACOES = {
        "ocioso": "ocioso",
        "nivel_ouro5": "nivel_ouro5",
        "nivel_ouro4": "nivel_ouro4",
        "nivel_ouro3": "nivel_ouro3",
        "nivel_ouro2": "nivel_ouro2",
        "nivel_ouro1": "nivel_ouro1",
        "obtido": "obtido",
    }

    def __init__(self, tela, assets, transform):
        self.tela = tela
        self.assets = assets
        self.transform = transform
        self._indice = 0
        self.carregado = False
        self.escala = 1.0
        self.escala_x = 1.0
        self.escala_y = 1.0

        self.frames = {
            "ocioso": [],
            "nivel_ouro5": [],
            "nivel_ouro4": [],
            "nivel_ouro3": [],
            "nivel_ouro2": [],
            "nivel_ouro1": [],
        }

        self._fila = self._criar_fila()

    # =====================================
    # LOAD
    # =====================================

    def _criar_fila(self):
        return [
            ("ocioso", "ouro/mina_ouro_001.png", 6),
            ("nivel_ouro5", "ouro/mina_ouro_002.png", 6),
            ("nivel_ouro4", "ouro/mina_ouro_003.png", 6),
            ("nivel_ouro3", "ouro/mina_ouro_004.png", 6),
            ("nivel_ouro2", "ouro/mina_ouro_005.png", 6),
            ("nivel_ouro1", "ouro/mina_ouro_006.png", 6),
        ]

    def atualizar_carregamento(self, quantidade_por_frame=3):
        if self.carregado:
            return

        for _ in range(quantidade_por_frame):
            if self._indice >= len(self._fila):
                self._finalizar_carregamento()
                return

            grupo, arquivo, total_frames = self._fila[self._indice]
            self._indice += 1

            spritesheet = self.assets.carregar(arquivo)
            frames = self.transform.recortar_spritesheet(
                spritesheet,
                linhas=1,
                colunas=total_frames,
            )

            self.frames[grupo] = frames

    def _finalizar_carregamento(self):
        self.calcular_layout()

        self.carregado = True

    def calcular_layout(self):
        frame = self.frames["ocioso"][0]

        self.largura = int(frame.get_width() * self.escala * self.escala_x)
        self.altura = int(frame.get_height() * self.escala * self.escala_y)

    # =====================================
    # FRAME
    # =====================================

    def obter_frame_animacao(self, animacoes):
        if not self.carregado:
            return None

        seletor, frame = animacoes.obter_selecao_frame()

        chave = self.MAPA_ANIMACOES.get(seletor, "ocioso")
        return self.frames[chave][frame]

    # =====================================
    # RENDER
    # =====================================

    def renderizar(self, arvore, animacoes):
        if not self.carregado:
            return

        frame = self.obter_frame_animacao(animacoes)
        if frame is None:
            return

        frame = self.transform.escalar(
            frame,
            (
                int(frame.get_width() * self.escala * self.escala_x),
                int(frame.get_height() * self.escala * self.escala_y),
            ),
        )

        centro_x = arvore.x + frame.get_width() // 2
        centro_y = arvore.y + frame.get_height() // 2

        frame.set_alpha(255)
        rect = frame.get_rect(center=(centro_x, centro_y))
        self.tela.blit(frame, rect)

        largura = int(frame.get_width() * 0.32)
        altura = int(frame.get_height() * 0.38)

        x = rect.centerx - largura // 2
        y = rect.centery - (altura // 2)

        self.corpo_rect = kivy_adapter.Rect(
            x,
            y,
            largura,
            altura,
        )

        # kivy_adapter.draw.rect(
        #     self.tela,
        #     (255, 0, 0),
        #     self.corpo_rect,
        #     2,
        # )
