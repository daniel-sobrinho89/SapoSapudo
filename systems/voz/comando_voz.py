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
    
    @classmethod
    def obter_comando_spotify(
        cls,
        texto
    ):

        texto = cls.normalizar(
            texto
        )

        if not texto.startswith(
            "sapudo"
        ):
            return None

        comandos = [
            "iniciar musica",
            "inicia musica",
            "tocar musica",
            "toque musica",
            "toca musica",
            "toque alguma musica"
        ]

        for comando in comandos:
            if comando in texto:
                posicao = texto.find(
                    comando
                )

                pesquisa = texto[
                    posicao
                    + len(comando):
                ].strip()

                return {
                    "tipo": "spotify",
                    "pesquisa": pesquisa
                }

        return None