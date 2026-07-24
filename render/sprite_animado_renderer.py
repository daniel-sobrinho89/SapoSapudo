import kivy_adapter


class SpriteAnimadoRenderer:
    CONFIG = {
        "aldeao": {
            "animacoes": [
                ("ocioso", "aldeao/ocioso/aldeao.png", 8),
                ("ocioso_madeira", "aldeao/ocioso/aldeao_madeira.png", 8),
                ("correndo", "aldeao/correndo/aldeao.png", 6),
                ("correndo_machado", "aldeao/correndo/aldeao_machado.png", 6),
                ("correndo_madeira", "aldeao/correndo/aldeao_madeira.png", 6),
                ("correndo_picareta", "aldeao/correndo/aldeao_picareta.png", 6),
                ("correndo_ouro", "aldeao/correndo/aldeao_ouro.png", 6),
                ("correndo_faca", "aldeao/correndo/aldeao_faca.png", 6),
                ("correndo_carne", "aldeao/correndo/aldeao_carne.png", 6),
                ("usando_machado", "aldeao/obtendo_recursos/aldeao_machado.png", 6),
                ("usando_picareta", "aldeao/obtendo_recursos/aldeao_picareta.png", 6),
                ("usando_faca", "aldeao/obtendo_recursos/aldeao_faca.png", 4),
            ],
            "flip": True,
        },
        "soldado": {
            "animacoes": [
                ("ocioso", "soldado/soldado_ocioso.png", 8),
                ("correndo", "soldado/soldado_correndo.png", 6),
            ],
            "flip": True,
        },
        "madeira": {
            "flip": False,
            "animacoes": [
                ("ocioso", "recursos/madeira.png", 1),
            ],
        },
        "carne": {
            "flip": False,
            "animacoes": [
                ("ocioso", "recursos/carne.png", 1),
            ],
        },
        "ouro": {
            "flip": False,
            "animacoes": [
                ("ocioso", "recursos/ouro.png", 6),
            ],
        },
        "casa": {
            "flip": False,
            "animacoes": [
                ("ocioso", "construcoes/casa.png", 1),
            ],
        },
        "quartel": {
            "flip": False,
            "animacoes": [
                ("ocioso", "construcoes/quartel.png", 1),
            ],
        },
        "castelo": {
            "flip": False,
            "animacoes": [
                ("ocioso", "construcoes/castelo.png", 1),
            ],
        },
        "arvore1": {
            "flip": False,
            "animacoes": [
                ("ocioso", "arvore/arvore_001.png", 8),
                ("cortada", "arvore/arvore_cortada_001.png", 1),
            ],
        },
        "arvore2": {
            "flip": False,
            "animacoes": [
                ("ocioso", "arvore/arvore_002.png", 8),
                ("cortada", "arvore/arvore_cortada_002.png", 1),
            ],
        },
        "arvore3": {
            "flip": False,
            "animacoes": [
                ("ocioso", "arvore/arvore_003.png", 8),
                ("cortada", "arvore/arvore_cortada_003.png", 1),
            ],
        },
        "arvore4": {
            "flip": False,
            "animacoes": [
                ("ocioso", "arvore/arvore_004.png", 8),
                ("cortada", "arvore/arvore_cortada_004.png", 1),
            ],
        },
        "ovelha": {
            "flip": True,
            "animacoes": [
                ("ocioso", "fauna/ovelha_ocioso.png", 6),
                ("comendo", "fauna/ovelha_comendo.png", 12),
                ("correndo", "fauna/ovelha_correndo.png", 4),
            ],
        },
        "mina_ouro": {
            "flip": False,
            "animacoes": [
                ("ocioso", "ouro/mina_ouro_001.png", 6),
                ("nivel_ouro5", "ouro/mina_ouro_002.png", 6),
                ("nivel_ouro4", "ouro/mina_ouro_003.png", 6),
                ("nivel_ouro3", "ouro/mina_ouro_004.png", 6),
                ("nivel_ouro2", "ouro/mina_ouro_005.png", 6),
                ("nivel_ouro1", "ouro/mina_ouro_006.png", 6),
            ],
        },
    }

    def __init__(
        self,
        tela,
        assets,
        transform,
        tipo,
        escala,
    ):
        self.tela = tela
        self.assets = assets
        self.transform = transform

        self.tipo = tipo.lower()

        self.escala = escala
        self.escala_x = escala
        self.escala_y = escala

        self.carregado = False
        self._indice = 0

        self.frames = {}

        config = self.CONFIG[self.tipo]

        self.flip = config["flip"]
        self._fila = config["animacoes"]

        for grupo, *_ in self._fila:
            self.frames[grupo] = []
            if self.flip:
                self.frames[f"{grupo}_flip"] = []

    # =====================================
    # LOAD
    # =====================================

    def atualizar_carregamento(
        self,
        quantidade_por_frame=3,
    ):
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

            if self.flip:
                self.frames[f"{grupo}_flip"] = [
                    self.transform.espelhar(frame) for frame in frames
                ]

    def _finalizar_carregamento(self):
        self.calcular_layout()
        self.carregado = True

    # =====================================
    # LAYOUT
    # =====================================

    def obter_tamanho(self, frame, escala=1.0):
        return (
            max(1, int(frame.get_width() * self.escala * escala)),
            max(1, int(frame.get_height() * self.escala * escala)),
        )

    def calcular_layout(self):
        self.grupo_padrao = self._fila[0][0]
        frame = self.frames[self.grupo_padrao][0]
        self.largura, self.altura = self.obter_tamanho(frame)

    # =====================================
    # FRAME
    # =====================================

    def obter_frame_animacao(
        self,
        animacoes,
    ):
        if not self.carregado:
            return None

        seletor, indice = animacoes.obter_selecao_frame()

        return self.frames.get(
            seletor,
            self.frames[self.grupo_padrao],
        )[indice]

    # =====================================
    # RENDER
    # =====================================

    def renderizar(
        self,
        entidade,
        animacoes,
        camera,
        alpha=255,
        escala=1.0,
    ):
        if not self.carregado:
            return

        frame = self.obter_frame_animacao(animacoes)

        if frame is None:
            return

        largura, altura = self.obter_tamanho(frame, escala)

        if not camera.visivel(
            entidade.x,
            entidade.y,
            largura,
            altura,
        ):
            return

        frame = self.transform.escalar(
            frame,
            (largura, altura),
        )

        frame.set_alpha(alpha)

        bbox = frame.get_bounding_rect()

        x, y = camera.tela(
            entidade.x,
            entidade.y,
        )

        rect = frame.get_rect(center=(x, y))

        self.tela.blit(
            frame,
            rect,
        )

        entidade.corpo_rect = kivy_adapter.Rect(
            entidade.x - frame.get_width() // 2 + bbox.x,
            entidade.y - frame.get_height() // 2 + bbox.y,
            bbox.w,
            bbox.h,
        )
