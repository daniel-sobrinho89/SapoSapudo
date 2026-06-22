from domains.voz.comando_voz import ComandoVoz


class RoteadorVoz:
    @staticmethod
    def identificar(texto):
        comando_spotify = ComandoVoz.obter_comando_spotify(texto)

        if comando_spotify:
            return {
                "tipo": "spotify",
                "dados": comando_spotify,
            }

        if ComandoVoz.eh_comando_feira(texto):
            return {"tipo": "feira"}

        return {
            "tipo": "conversa",
            "texto": texto,
        }
