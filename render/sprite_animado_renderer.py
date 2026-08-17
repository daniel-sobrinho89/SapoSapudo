import json

import utils.kivy_adapter as kivy_adapter
from utils.paths import BASE_DIR


class SpriteAnimadoRenderer:
    LARGURA_BARRA_VIDA = 100
    ALTURA_BARRA_VIDA = 20
    OFFSET_Y_BARRA_VIDA = 50

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
        self._partes_barra_vida = None

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
        cor=None,
    ):
        if not self.carregado:
            return

        frame = self.obter_frame_animacao(animacoes)

        if frame is None:
            return

        largura, altura = self.obter_tamanho(
            frame,
            escala,
            getattr(entidade, "escala_x", 0.9),
            getattr(entidade, "escala_y", 0.9),
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
            (
                int(largura * camera.zoom),
                int(altura * camera.zoom),
            ),
        )

        # O sprite escalado pode estar no cache compartilhado. Copia apenas
        # quando precisamos aplicar uma transformação visual temporária,
        # evitando contaminar as próximas renderizações.
        if cor is not None or alpha != 255:
            frame = frame.copy()

        if cor is not None:
            frame.multiplicar_cor(cor)

        frame.set_alpha(alpha)

        bbox = frame.get_bounding_rect()

        x, y = camera.tela(
            entidade.x,
            entidade.y,
        )

        x *= camera.zoom
        y *= camera.zoom

        rect = frame.get_rect(center=(x, y))
        entidade.render_rect = rect
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

        entidade.base_pe_y = entidade.corpo_rect.bottom

    def renderizar_barra_vida(
        self,
        personagem,
        camera,
        proporcao_vida,
        renderer_preenchimento,
    ):
        if not self.carregado or not renderer_preenchimento.carregado:
            return

        preenchimento = renderer_preenchimento.frames["ocioso"][0]
        esquerda, centro, direita = self._obter_partes_barra_vida()

        largura_barra = self.LARGURA_BARRA_VIDA
        altura_barra = self.ALTURA_BARRA_VIDA
        largura_lateral = altura_barra
        largura_centro = largura_barra - (largura_lateral * 2)

        barra = kivy_adapter.Surface(
            (largura_barra, altura_barra),
            kivy_adapter.SRCALPHA,
        )
        largura_preenchimento = int(largura_centro * max(0.0, min(1.0, proporcao_vida)))

        barra.blit(
            self.transform.escalar(esquerda, (largura_lateral, altura_barra)),
            (0, 0),
        )
        barra.blit(
            self.transform.escalar(centro, (largura_centro, altura_barra)),
            (largura_lateral, 0),
        )
        barra.blit(
            self.transform.escalar(direita, (largura_lateral, altura_barra)),
            (largura_lateral + largura_centro, 0),
        )

        if largura_preenchimento:
            barra.blit(
                self.transform.escalar(
                    preenchimento,
                    (largura_preenchimento, altura_barra),
                ),
                (largura_lateral, 0),
            )

        x, y = camera.tela(
            personagem.x,
            personagem.y + self.OFFSET_Y_BARRA_VIDA,
        )
        self.tela.blit(barra, barra.get_rect(center=(x, y)))

    def _obter_partes_barra_vida(self):
        if getattr(self, "_partes_barra_vida", None) is not None:
            return self._partes_barra_vida

        base = self.frames["ocioso"][0]
        largura_componente = base.get_width() // 5
        altura = base.get_height()

        self._partes_barra_vida = (
            base.subsurface((0, 0, largura_componente, altura)),
            base.subsurface((largura_componente * 2, 0, largura_componente, altura)),
            base.subsurface((largura_componente * 4, 0, largura_componente, altura)),
        )

        return self._partes_barra_vida
