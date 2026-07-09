import kivy_adapter


class SapoRenderer:
    MAPA_ANIMACOES = {
        "dormir": "dormir",
        "dormindo": "dormindo",
        "acordar": "acordar",
        "pegar_violao": "pegar_violao",
        "levantar_violao": "levantar_violao",
        "guardar_violao": "guardar_violao",
        "soltar_violao": "soltar_violao",
        "andar_esquerda": "andar_esquerda",
        "andar_direita": "andar_direita",
        "conversar": "conversar",
        "pegar_livro": "pegar_livro",
        "lendo_livro": "lendo_livro",
        "tocar_violao": "tocar_violao",
        "levantar_livro": "levantar_livro",
    }

    def __init__(self, tela, assets, transform):
        self.tela = tela
        self.assets = assets
        self.transform = transform
        self._indice = 0

        self.corpo_rect = kivy_adapter.Rect(-1000, -1000, 1, 1)

        self.carregado = False

        self.frames = {
            "parado": [],
            "acordar": [],
            "dormir": [],
            "dormindo": [],
            "pegar_violao": [],
            "levantar_violao": [],
            "tocar_violao": [],
            "guardar_violao": [],
            "soltar_violao": [],
            "andar_esquerda": [],
            "andar_direita": [],
            "conversar": [],
            "pegar_livro": [],
            "lendo_livro": [],
            "levantar_livro": [],
        }

        self._fila = self._criar_fila()

    def _criar_fila(self):
        fila = []

        definicoes = [
            ("parado", "sapudo/parado/sapudo_{:04d}.webp", 60),
            ("acordar", "sapudo/acordar/sapudo_{:04d}.webp", 60),
            ("pegar_violao", "sapudo/pegar_violao/sapudo_{:04d}.webp", 15),
            ("tocar_violao", "sapudo/tocar_violao/sapudo_{:04d}.webp", 10),
            ("guardar_violao", "sapudo/guardar_violao/sapudo_{:04d}.webp", 9),
            ("soltar_violao", "sapudo/soltar_violao/sapudo_{:04d}.webp", 9),
            ("andar_esquerda", "sapudo/andar_esquerda/sapudo_{:04d}.webp", 10),
            ("conversar", "sapudo/conversar/sapudo_{:04d}.webp", 60),
            ("pegar_livro", "sapudo/pegar_livro/sapudo_{:04d}.webp", 20),
            ("lendo_livro", "sapudo/lendo_livro/sapudo_{:04d}.webp", 30),
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
        self.frames["levantar_violao"] = list(reversed(self.frames["pegar_violao"]))
        self.frames["andar_direita"] = [
            kivy_adapter.transform.flip(f, True, False)
            for f in self.frames["andar_esquerda"]
        ]
        self.frames["levantar_livro"] = list(reversed(self.frames["pegar_livro"]))
        self.carregado = True

    def obter_frame_animacao(self, animacoes):
        if not self.carregado:
            return None

        seletor, frame = animacoes.obter_selecao_frame()

        chave = self.MAPA_ANIMACOES.get(seletor, "parado")
        return self.frames[chave][frame]

    def draw(self, imagem, x, y, escala_x, escala_y=None, alpha=255):
        if escala_y is None:
            escala_y = escala_x

        largura = max(1, int(imagem.get_width() * escala_x))
        altura = max(1, int(imagem.get_height() * escala_y))

        imagem = self.transform.escalar(imagem, (largura, altura))
        imagem.set_alpha(alpha)

        rect = imagem.get_rect(center=(x, y))
        self.tela.blit(imagem, rect)

    def renderizar(self, centro_x, centro_y, escala, animacoes):
        if not self.carregado:
            return

        frame = self.obter_frame_animacao(animacoes)
        if frame is None:
            return

        self.draw(frame, centro_x, centro_y, escala)

        largura = int(frame.get_width() * escala)
        altura = int(frame.get_height() * escala)

        self.corpo_rect = kivy_adapter.Rect(
            centro_x - largura // 2,
            centro_y - altura // 2,
            largura,
            altura,
        )
