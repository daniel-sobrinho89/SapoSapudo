import utils.kivy_adapter as kivy_adapter


class TransformUtils:
    def __init__(self):
        self.cache_escalas = {}
        self.cache_rotacoes = {}
        self.cache_spritesheets = {}

    def escalar(self, imagem, tamanho):
        largura, altura = tamanho

        largura = max(1, int(largura))
        altura = max(1, int(altura))

        key = (id(imagem), largura, altura)

        if key in self.cache_escalas:
            return self.cache_escalas[key]

        if getattr(kivy_adapter, "IS_BROWSER", False):
            escalada = kivy_adapter.transform.scale(
                imagem,
                (largura, altura),
            )
        else:
            escalada = kivy_adapter.transform.smoothscale(
                imagem,
                (largura, altura),
            )

        self.cache_escalas[key] = escalada

        return escalada

    def rotacionar(self, imagem, rotacao):
        rotacao = round(rotacao)

        key = (id(imagem), rotacao)

        if key in self.cache_rotacoes:
            return self.cache_rotacoes[key]

        resultado = kivy_adapter.transform.rotate(imagem, rotacao)

        self.cache_rotacoes[key] = resultado

        return resultado

    def recortar_spritesheet(
        self,
        imagem,
        linhas,
        colunas,
    ):
        key = (
            id(imagem),
            linhas,
            colunas,
        )

        if key in self.cache_spritesheets:
            return self.cache_spritesheets[key]

        largura_frame = imagem.get_width() // colunas
        altura_frame = imagem.get_height() // linhas

        frames = []

        for linha in range(linhas):
            for coluna in range(colunas):
                x = coluna * largura_frame
                y = linha * altura_frame

                frame = kivy_adapter.Surface(
                    (
                        largura_frame,
                        altura_frame,
                    ),
                    kivy_adapter.SRCALPHA,
                )

                frame.blit(
                    imagem,
                    (0, 0),
                    (
                        x,
                        y,
                        largura_frame,
                        altura_frame,
                    ),
                )

                frames.append(frame)

        self.cache_spritesheets[key] = frames

        return frames

    def espelhar(self, imagem):
        key = ("flip_x", id(imagem))

        if key in self.cache_rotacoes:
            return self.cache_rotacoes[key]

        resultado = kivy_adapter.transform.flip(
            imagem,
            True,  # horizontal
            False,  # vertical
        )

        self.cache_rotacoes[key] = resultado

        return resultado
