import kivy_adapter


class CasaDuendeRenderer:
    MAPA_ANIMACOES = {
        "inicial": "inicial",
        "abrir_janela": "abrir_janela",
        "luz_acesa": "luz_acesa",
    }

    def __init__(self, tela, assets, transform):
        self.tela = tela
        self.assets = assets
        self.transform = transform
        self._indice = 0
        self.offset_y = 0
        self.offset_x = -6
        self.escala = 0.13
        self.escala_x = 6.0
        self.escala_y = 6.0

        self.corpo_rect = kivy_adapter.Rect(-1000, -1000, 1, 1)

        self.carregado = False

        self.frames = {
            "inicial": [],
            "abrir_janela": [],
            "luz_acesa": [],
        }

        self._fila = self._criar_fila()

    def _criar_fila(self):
        fila = []

        # Inicial (0 a 6)
        for i in range(0, 7):
            fila.append(("inicial", f"casa_duende/casa_duende_{i:04d}.webp"))

        # Abrir janela (7 a 15)
        for i in range(7, 16):
            fila.append(("abrir_janela", f"casa_duende/casa_duende_{i:04d}.webp"))

        # Luz acesa (43 a 46)
        for i in range(43, 47):
            fila.append(("luz_acesa", f"casa_duende/casa_duende_{i:04d}.webp"))

        return fila

    def atualizar_carregamento(self, casa, quantidade_por_frame=8):
        if self.carregado:
            return

        for _ in range(quantidade_por_frame):
            if self._indice >= len(self._fila):
                self._finalizar_carregamento(casa)
                return

            grupo, arquivo = self._fila[self._indice]
            self._indice += 1
            self.frames[grupo].append(self.assets.carregar(arquivo))

    def _finalizar_carregamento(self, casa):
        self.carregado = True
        layout = self.calcular_layout()

        for grupo in self.frames:
            self.frames[grupo] = [
                self.transform.escalar(
                    frame,
                    (
                        int(frame.get_width() * self.escala * self.escala_x),
                        int(frame.get_height() * self.escala * self.escala_y),
                    ),
                )
                for frame in self.frames[grupo]
            ]

        casa.atualizar_layout_casa(**layout)
        casa.atualizar_posicao()

    def obter_frame_animacao(self, animacoes):
        if not self.carregado:
            return None

        seletor, frame = animacoes.obter_selecao_frame()

        chave = self.MAPA_ANIMACOES.get(seletor, "inicial")
        return self.frames[chave][frame]

    def calcular_layout(self):
        frame = self.frames["inicial"][0]

        self.largura = int(frame.get_width() * self.escala * self.escala_x)
        self.altura = int(frame.get_height() * self.escala * self.escala_y)

        return {"largura": self.largura, "altura": self.altura}

    def draw(self, imagem, x, y, alpha=255):
        imagem.set_alpha(alpha)
        rect = imagem.get_rect(center=(x, y))
        self.tela.blit(imagem, rect)

    def renderizar(self, casa, animacoes):
        if not self.carregado:
            return

        centro_x = casa.x + self.largura // 2
        centro_y = casa.y + self.altura // 2

        frame = self.obter_frame_animacao(animacoes)
        if frame is None:
            return

        self.draw(frame, centro_x, centro_y)

        largura = int(frame.get_width() * self.escala * self.escala_x)
        altura = int(frame.get_height() * self.escala * self.escala_y)

        self.corpo_rect = kivy_adapter.Rect(
            centro_x - largura // 2,
            centro_y - altura // 2,
            largura,
            altura,
        )
