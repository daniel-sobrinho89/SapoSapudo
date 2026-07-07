# =====================================
# render/duende_renderer.py
# =====================================


class DuendeRenderer:
    MAPA_ANIMACOES = {
        "dormindo": "dormindo",
        "descendo_para_dormir": "descendo_para_dormir",
        "guardando_violao": "guardando_violao",
        "comendo_esfera": "comendo_esfera",
    }

    def __init__(self, tela, assets, transform):
        self.tela = tela
        self.assets = assets
        self.transform = transform
        self._indice = 0
        self.carregado = False

        self.frames = {
            "voando": [],
            "descendo_para_dormir": [],
            "dormindo": [],
            "guardando_violao": [],
            "comendo_esfera": [],
        }

        self._fila = self._criar_fila()

    # =====================================
    # LOAD
    # =====================================

    def _criar_fila(self):
        fila = []

        definicoes = [
            ("voando", "assistente/voando/assistente_{:04d}.webp", 15),
            ("comendo_esfera", "assistente/comendo_esfera/assistente_{:04d}.webp", 60),
        ]

        for grupo, mascara, total in definicoes:
            for i in range(total):
                fila.append((grupo, mascara.format(i)))

        return fila

    def atualizar_carregamento(self, duende, quantidade_por_frame=3):
        if self.carregado:
            return

        for _ in range(quantidade_por_frame):
            if self._indice >= len(self._fila):
                self._finalizar_carregamento(duende)
                return

            grupo, arquivo = self._fila[self._indice]
            self._indice += 1
            self.frames[grupo].append(self.assets.carregar(arquivo))

    def _finalizar_carregamento(self, duende):
        self.frames["descendo_para_dormir"] = self.frames["voando"][3:14]
        self.frames["dormindo"] = [self.frames["voando"][3]]
        self.frames["guardando_violao"] = self.frames["voando"][:4]

        self.carregado = True
        duende.carregado = True

    # =====================================
    # FRAME
    # =====================================

    def obter_frame_animacao(self, animacoes):
        if not self.carregado:
            return None

        seletor, frame = animacoes.obter_selecao_frame()

        chave = self.MAPA_ANIMACOES.get(seletor, "voando")
        return self.frames[chave][frame]

    # =====================================
    # RENDER
    # =====================================

    def renderizar(self, duende, escala):
        if not self.carregado:
            return

        frame = self.obter_frame_animacao(duende.animacoes)

        if frame is None:
            return

        escala *= duende.escala_visual

        self.draw(
            frame,
            duende.x,
            duende.y,
            escala,
            alpha=duende.alpha_visual,
        )

        largura = int(frame.get_width() * escala)
        altura = int(frame.get_height() * escala)

        duende.atualizar_hitboxes(
            duende.x,
            duende.y,
            largura,
            altura,
        )

    # =====================================
    # DRAW
    # =====================================

    def draw(self, imagem, x, y, escala_x, escala_y=None, alpha=255):
        if escala_y is None:
            escala_y = escala_x

        largura = max(1, int(imagem.get_width() * escala_x))
        altura = max(1, int(imagem.get_height() * escala_y))

        imagem = self.transform.escalar(imagem, (largura, altura))
        imagem.set_alpha(alpha)

        rect = imagem.get_rect(center=(x, y))

        self.tela.blit(imagem, rect)
