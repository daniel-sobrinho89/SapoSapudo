import kivy_adapter


class ArvoreRenderer:
    MAPA_ANIMACOES = {"ocioso": "ocioso", "cortada": "cortada"}

    def __init__(self, tela, assets, transform, numero_arvore):
        self.tela = tela
        self.assets = assets
        self.transform = transform
        self._indice = 0
        self.carregado = False
        self.escala = 1.0
        self.escala_x = 1.0
        self.escala_y = 1.0
        self.numero_arvore = numero_arvore

        self.frames = {"ocioso": [], "cortada": []}

        self._fila = self._criar_fila()

    # =====================================
    # LOAD
    # =====================================

    def _criar_fila(self):
        numero = f"{self.numero_arvore:03d}"

        return [
            ("ocioso", f"arvore/arvore_{numero}.png", 8),
            ("cortada", f"arvore/arvore_cortada_{numero}.png", 1),
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
        self.carregado = True

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

        largura = max(1, int(frame.get_width() * self.escala_x))
        altura = max(1, int(frame.get_height() * self.escala_y))

        frame = self.transform.escalar(frame, (largura, altura))
        frame.set_alpha(255)

        bbox = frame.get_bounding_rect()

        rect = frame.get_rect(center=(entidade.x, entidade.y))
        self.tela.blit(frame, rect)

        self.corpo_rect = kivy_adapter.Rect(
            rect.x + bbox.x,
            rect.y + bbox.y,
            bbox.w,
            bbox.h,
        )
