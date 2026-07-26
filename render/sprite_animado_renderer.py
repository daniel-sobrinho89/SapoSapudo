import json

import kivy_adapter
from utils.paths import BASE_DIR


class SpriteAnimadoRenderer:
    with open(BASE_DIR / "data/sprites_config.json", encoding="utf8") as f:
        CONFIG = json.load(f)

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
        self._fila = list(config["animacoes"].items())

        for grupo, _ in self._fila:
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

            grupo, dados = self._fila[self._indice]

            self._indice += 1

            spritesheet = self.assets.carregar(dados["arquivo"])

            frames = self.transform.recortar_spritesheet(
                spritesheet,
                linhas=1,
                colunas=dados["frames"],
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

    def obter_tamanho(self, frame, escala=1.0, escala_x=1.0, escala_y=1.0):
        return (
            max(1, int(frame.get_width() * self.escala * escala * escala_x)),
            max(1, int(frame.get_height() * self.escala * escala * escala_y)),
        )

    def calcular_layout(self):
        self.grupo_padrao = self._fila[0][0]
        frame = self.frames[self.grupo_padrao][0]
        self.largura, self.altura = self.obter_tamanho(frame)

    # =====================================
    # FRAME
    # =====================================

    def obter_frame_animacao(self, animacoes):
        if not self.carregado:
            return None

        seletor, indice = animacoes.obter_selecao_frame()

        frames = self.frames.get(
            seletor,
            self.frames[self.grupo_padrao],
        )

        indice = min(indice, len(frames) - 1)

        return frames[indice]

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

        largura, altura = self.obter_tamanho(
            frame,
            escala,
            getattr(entidade, "escala_x", 1.0),
            getattr(entidade, "escala_y", 1.0),
        )

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
