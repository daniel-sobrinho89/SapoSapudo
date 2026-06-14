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

        texto = cls.normalizar(texto)

        if not texto.startswith(
            "sapudo"
        ):
            return None

        if (
            "proxima musica" in texto
            or "próxima música" in texto
        ):
            return {
                "tipo": "spotify",
                "acao": "next"
            }

        if (
            "musica anterior" in texto
            or "música anterior" in texto
        ):
            return {
                "tipo": "spotify",
                "acao": "previous"
            }

        if (
            "parar musica" in texto
            or "pausar musica" in texto
        ):
            return {
                "tipo": "spotify",
                "acao": "pause"
            }

        if (
            texto == "sapudo tocar"
            or texto == "sapudo tocar musica"
            or texto == "sapudo continuar"
            or texto == "sapudo continuar musica"
            or texto == "sapudo retomar"
            or texto == "sapudo retomar musica"
        ):
            return {
                "tipo": "spotify",
                "acao": "play"
            }

        if texto.startswith(
            "sapudo tocar "
        ):

            pesquisa = texto.replace(
                "sapudo tocar ",
                ""
            ).strip()

            return {
                "tipo": "spotify",
                "acao": "buscar",
                "pesquisa": pesquisa
            }

        if texto.startswith(
            "sapudo toque "
        ):

            pesquisa = texto.replace(
                "sapudo toque ",
                ""
            ).strip()

            return {
                "tipo": "spotify",
                "acao": "buscar",
                "pesquisa": pesquisa
            }

        if texto.startswith(
            "sapudo toca "
        ):

            pesquisa = texto.replace(
                "sapudo toca ",
                ""
            ).strip()

            return {
                "tipo": "spotify",
                "acao": "buscar",
                "pesquisa": pesquisa
            }

        return None