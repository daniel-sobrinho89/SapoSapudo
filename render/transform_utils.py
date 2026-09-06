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

        cache_entry = self.cache_escalas.get(key)
        if cache_entry is not None:
            fonte_cacheada, resultado = cache_entry
            if fonte_cacheada is imagem:
                return resultado
            # Nunca reutilizar o resultado de outra Surface mesmo que o Python
            # tenha reaproveitado o mesmo id().
            self.cache_escalas.pop(key, None)

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

        # Guardar a referência da fonte impede colisões por reutilização de id().
        self.cache_escalas[key] = (imagem, escalada)

        return escalada

    def rotacionar(self, imagem, rotacao):
        rotacao = round(rotacao)

        key = (id(imagem), rotacao)

        cache_entry = self.cache_rotacoes.get(key)
        if cache_entry is not None:
            fonte_cacheada, resultado = cache_entry
            if fonte_cacheada is imagem:
                return resultado
            self.cache_rotacoes.pop(key, None)

        resultado = kivy_adapter.transform.rotate(imagem, rotacao)

        self.cache_rotacoes[key] = (imagem, resultado)

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

        cache_entry = self.cache_spritesheets.get(key)
        if cache_entry is not None:
            fonte_cacheada, frames = cache_entry
            if fonte_cacheada is imagem:
                return frames
            self.cache_spritesheets.pop(key, None)

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

        self.cache_spritesheets[key] = (imagem, frames)

        return frames

    def espelhar(self, imagem):
        key = ("flip_x", id(imagem))

        cache_entry = self.cache_rotacoes.get(key)
        if cache_entry is not None:
            fonte_cacheada, resultado = cache_entry
            if fonte_cacheada is imagem:
                return resultado
            self.cache_rotacoes.pop(key, None)

        resultado = kivy_adapter.transform.flip(
            imagem,
            True,  # horizontal
            False,  # vertical
        )

        self.cache_rotacoes[key] = (imagem, resultado)

        return resultado
