import kivy_adapter


class OvelhaRenderer:
    MAPA_ANIMACOES = {
        "ocioso": "ocioso",
        "ocioso_flip": "ocioso_flip",
        "comendo": "comendo",
        "comendo_flip": "comendo_flip",
        "correndo": "correndo",
        "correndo_flip": "correndo_flip",
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
            "ocioso_flip": [],
            "comendo": [],
            "comendo_flip": [],
            "correndo": [],
            "correndo_flip": [],
        }

        self._fila = self._criar_fila()

    # =====================================
    # LOAD
    # =====================================

    def _criar_fila(self):
        return [
            ("ocioso", "fauna/ovelha_ocioso.png", 6),
            ("comendo", "fauna/ovelha_comendo.png", 12),
            ("correndo", "fauna/ovelha_correndo.png", 4),
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

            self.frames[f"{grupo}_flip"] = [
                self.transform.espelhar(frame) for frame in frames
            ]

    def _finalizar_carregamento(self):
        self.calcular_layout()

        self.carregado = True

    def espelhar(self, imagem):
        return kivy_adapter.transform.flip(
            imagem,
            True,
            False,
        )

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

    def renderizar(self, entidade, animacoes):
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

        centro_x = entidade.x + frame.get_width() // 2
        centro_y = entidade.y + frame.get_height() // 2

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
