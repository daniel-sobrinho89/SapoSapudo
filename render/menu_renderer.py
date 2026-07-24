import math


class MenuRenderer:
    TL = 0
    T = 1
    TR = 2
    L = 3
    C = 4
    R = 5
    BL = 6
    B = 7
    BR = 8

    CONFIG = {
        TL: {"x": 45, "y": 55},
        T: {"x": 43, "y": 55},
        TR: {"x": 22, "y": 55},
        L: {"x": 45, "y": 43},
        C: {"x": 43, "y": 43},
        R: {"x": 22, "y": 43},
        BL: {"x": 44, "y": 22},
        B: {"x": 43, "y": 22},
        BR: {"x": 22, "y": 22},
    }

    def __init__(self, tela, assets, transform):
        self.tela = tela
        self.assets = assets
        self.transform = transform

        self.carregado = False

        self.frames = []

        self.slot = None

        self.passo_x = 0
        self.passo_y = 0

    def atualizar_carregamento(self):
        if self.carregado:
            return

        spritesheet = self.assets.carregar("ui/menu.png")

        self.frames = self.transform.recortar_spritesheet(
            spritesheet,
            linhas=3,
            colunas=3,
        )

        #
        # PASSO = TAMANHO ORIGINAL DA CÉLULA DO SPRITESHEET
        #
        bbox = self.frames[self.C].get_bounding_rect()

        self.passo_x = bbox.w
        self.passo_y = bbox.h

        slot = self.assets.carregar("ui/menu_slots.png")

        escala = min(
            (64 * 0.90) / slot.get_width(),
            (64 * 0.90) / slot.get_height(),
        )

        self.slot = self.transform.escalar(
            slot,
            (
                int(slot.get_width() * escala),
                int(slot.get_height() * escala),
            ),
        )

        self.carregado = True

    def _frame(self, linha, coluna, linhas, colunas):
        if linha == 0:
            if coluna == 0:
                return self.TL

            if coluna == colunas - 1:
                return self.TR

            return self.T

        if linha == linhas - 1:
            if coluna == 0:
                return self.BL

            if coluna == colunas - 1:
                return self.BR

            return self.B

        if coluna == 0:
            return self.L

        if coluna == colunas - 1:
            return self.R

        return self.C

    def renderizar(
        self,
        x,
        y,
        quantidade_itens,
    ):
        if not self.carregado:
            return []

        COLUNAS = 3

        linhas_slots = max(
            1,
            math.ceil(quantidade_itens / COLUNAS),
        )

        linhas = linhas_slots + 2

        slots = []

        for linha in range(linhas):
            for coluna in range(COLUNAS):
                indice = self._frame(
                    linha,
                    coluna,
                    linhas,
                    COLUNAS,
                )

                frame = self.frames[indice]

                cfg = self.CONFIG[indice]

                px = x + coluna * self.passo_x - cfg["x"]

                py = y + linha * self.passo_y - cfg["y"]

                self.tela.blit(
                    frame,
                    (px, py),
                )

                if (
                    linha < linhas_slots
                    and (linha * COLUNAS + coluna) < quantidade_itens
                ):
                    SLOT_OFFSET_X = -13 if coluna == 2 else 14

                    SLOT_OFFSET_Y = 18

                    rect = self.slot.get_rect(
                        center=(
                            px + frame.get_width() // 2 + SLOT_OFFSET_X,
                            py + frame.get_height() // 2 + SLOT_OFFSET_Y,
                        )
                    )

                    self.tela.blit(
                        self.slot,
                        rect,
                    )

                    slots.append(rect)

        return slots
