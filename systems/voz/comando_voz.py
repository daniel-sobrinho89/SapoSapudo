import unicodedata


class ComandoVoz:

    @staticmethod
    def normalizar(texto):

        texto = texto.lower()

        texto = ''.join(
            c
            for c in unicodedata.normalize(
                'NFD',
                texto
            )
            if unicodedata.category(c) != 'Mn'
        )

        return texto

    @classmethod
    def eh_comando_feira(
        cls,
        texto
    ):

        texto = cls.normalizar(texto)

        if "sapudo" not in texto:
            return False

        return "feira" in texto