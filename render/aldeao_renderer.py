import kivy_adapter


class AldeaoRenderer:
    MAPA_ANIMACOES = {
        "ocioso": "ocioso",
        "ocioso_flip": "ocioso_flip",
        "ocioso_madeira": "ocioso_madeira",
        "ocioso_madeira_flip": "ocioso_madeira_flip",
        "correndo": "correndo",
        "correndo_flip": "correndo_flip",
        "correndo_machado": "correndo_machado",
        "correndo_machado_flip": "correndo_machado_flip",
        "correndo_madeira": "correndo_madeira",
        "correndo_madeira_flip": "correndo_madeira_flip",
        "usando_machado": "usando_machado",
        "usando_machado_flip": "usando_machado_flip",
        "correndo_picareta": "correndo_picareta",
        "correndo_picareta_flip": "correndo_picareta_flip",
        "usando_picareta": "usando_picareta",
        "usando_picareta_flip": "usando_picareta_flip",
        "correndo_ouro": "correndo_ouro",
        "correndo_ouro_flip": "correndo_ouro_flip",
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
            "ocioso_madeira": [],
            "ocioso_madeira_flip": [],
            "correndo": [],
            "correndo_flip": [],
            "correndo_machado": [],
            "correndo_machado_flip": [],
            "correndo_madeira": [],
            "correndo_madeira_flip": [],
            "usando_machado": [],
            "usando_machado_flip": [],
            "correndo_picareta": [],
            "correndo_picareta_flip": [],
            "usando_picareta": [],
            "usando_picareta_flip": [],
            "correndo_ouro": [],
            "correndo_ouro_flip": [],
        }

        self._fila = self._criar_fila()

    # =====================================
    # LOAD
    # =====================================

    def _criar_fila(self):
        return [
            ("ocioso", "aldeao/ocioso/aldeao.png", 8),
            ("ocioso_madeira", "aldeao/ocioso/aldeao_madeira.png", 8),
            ("correndo", "aldeao/correndo/aldeao.png", 6),
            ("correndo_machado", "aldeao/correndo/aldeao_machado.png", 6),
            ("correndo_madeira", "aldeao/correndo/aldeao_madeira.png", 6),
            ("correndo_picareta", "aldeao/correndo/aldeao_picareta.png", 6),
            ("correndo_ouro", "aldeao/correndo/aldeao_ouro.png", 6),
            ("usando_machado", "aldeao/obtendo_recursos/aldeao_machado.png", 6),
            ("usando_picareta", "aldeao/obtendo_recursos/aldeao_picareta.png", 6),
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

    def renderizar(self, aldeao, animacoes):
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

        centro_x = aldeao.x + frame.get_width() // 2
        centro_y = aldeao.y + frame.get_height() // 2

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
