import kivy_adapter


class SapoRenderer:
    MAPA_ANIMACOES = {
        "dormir": "dormir",
        "dormindo": "dormindo",
        "acordar": "acordar",
        "andar_esquerda": "andar_esquerda",
        "andar_direita": "andar_direita",
        "conversar": "conversar",
    }

    def __init__(self, tela, assets, transform):
        self.tela = tela
        self.assets = assets
        self.transform = transform
        self._indice = 0
        self.escala = 0.3
        self.escala_x = 0.3
        self.escala_y = 0.3

        self.corpo_rect = kivy_adapter.Rect(-1000, -1000, 1, 1)

        self.carregado = False

        self.frames = {
            "parado": [],
            "acordar": [],
            "dormir": [],
            "dormindo": [],
            "andar_esquerda": [],
            "andar_direita": [],
            "conversar": [],
        }

        self._fila = self._criar_fila()

    def _criar_fila(self):
        fila = []

        definicoes = [
            ("parado", "sapudo_old/parado/sapudo_{:04d}.webp", 60),
            ("acordar", "sapudo_old/acordar/sapudo_{:04d}.webp", 60),
            ("andar_esquerda", "sapudo_old/andar_esquerda/sapudo_{:04d}.webp", 10),
            ("conversar", "sapudo_old/conversar/sapudo_{:04d}.webp", 60),
        ]

        for grupo, mascara, total in definicoes:
            for i in range(total):
                fila.append((grupo, mascara.format(i)))

        return fila

    def atualizar_carregamento(self, quantidade_por_frame=8):
        if self.carregado:
            return

        for _ in range(quantidade_por_frame):
            if self._indice >= len(self._fila):
                self._finalizar_carregamento()
                return

            grupo, arquivo = self._fila[self._indice]
            self._indice += 1
            self.frames[grupo].append(self.assets.carregar(arquivo))

    def _finalizar_carregamento(self):
        self.frames["dormir"] = list(reversed(self.frames["acordar"]))
        self.frames["dormindo"] = list(reversed(self.frames["acordar"][:9]))
        self.frames["andar_direita"] = [
            kivy_adapter.transform.flip(f, True, False)
            for f in self.frames["andar_esquerda"]
        ]
        self.carregado = True

    def obter_frame_animacao(self, animacoes):
        if not self.carregado:
            return None

        seletor, frame = animacoes.obter_selecao_frame()

        chave = self.MAPA_ANIMACOES.get(seletor, "parado")
        return self.frames[chave][frame]

    def draw(self, imagem, x, y, alpha=255):
        largura = max(1, int(imagem.get_width() * self.escala_x))
        altura = max(1, int(imagem.get_height() * self.escala_y))

        imagem = self.transform.escalar(imagem, (largura, altura))
        imagem.set_alpha(alpha)

        rect = imagem.get_rect(center=(x, y))
        self.tela.blit(imagem, rect)

    def renderizar(self, centro_x, centro_y, animacoes):
        if not self.carregado:
            return

        frame = self.obter_frame_animacao(animacoes)
        if frame is None:
            return

        largura = max(1, int(frame.get_width() * self.escala_x))
        altura = max(1, int(frame.get_height() * self.escala_y))

        frame = self.transform.escalar(frame, (largura, altura))
        frame.set_alpha(255)

        rect = frame.get_rect(center=(centro_x, centro_y))
        self.tela.blit(frame, rect)

        self.corpo_rect = kivy_adapter.Rect(
            centro_x - largura // 2,
            centro_y - altura // 2,
            largura,
            altura,
        )
