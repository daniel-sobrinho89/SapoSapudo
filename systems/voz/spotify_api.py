import requests


class SpotifyApi:

    @classmethod
    def obter_dispositivo_ativo(
        cls,
        token
    ):

        resposta = requests.get(
            "https://api.spotify.com/v1/me/player/devices",
            headers={
                "Authorization":
                f"Bearer {token}"
            },
            timeout=10
        )

        if resposta.status_code != 200:
            print("[SPOTIFY] DEVICES:", resposta.status_code)
            print("[SPOTIFY] DEVICES BODY:", resposta.text)

            return None

        dispositivos = (
            resposta
            .json()
            .get(
                "devices",
                []
            )
        )

        print("[SPOTIFY] DEVICES:", dispositivos)

        for dispositivo in dispositivos:
            if dispositivo.get(
                "is_active"
            ):
                return dispositivo[
                    "id"
                ]

        if dispositivos:
            return dispositivos[0]["id"]

        return None

    @classmethod
    def transferir_playback(
        cls,
        token,
        device_id
    ):

        resposta = requests.put(
            "https://api.spotify.com/v1/me/player",
            headers={
                "Authorization":
                f"Bearer {token}"
            },
            json={
                "device_ids": [
                    device_id
                ],
                "play": False
            },
            timeout=10
        )

        print(
            "[SPOTIFY] TRANSFER:",
            resposta.status_code,
            resposta.text
        )

        return resposta.status_code in (
            200,
            202,
            204
        )

    @classmethod
    def buscar_faixa(
        cls,
        token,
        pesquisa
    ):

        try:

            resposta = requests.get(
                "https://api.spotify.com/v1/search",
                headers={
                    "Authorization":
                    f"Bearer {token}"
                },
                params={
                    "q": pesquisa,
                    "type": "track",
                    "limit": 1
                },
                timeout=10
            )

            if resposta.status_code != 200:

                print(
                    "[SPOTIFY] Erro busca:",
                    resposta.status_code,
                    resposta.text
                )

                return None

            dados = resposta.json()

            itens = (
                dados
                .get("tracks", {})
                .get("items", [])
            )

            if not itens:
                return None

            return itens[0]["uri"]

        except Exception as ex:

            print(
                f"[SPOTIFY] Falha busca: {ex}"
            )

            return None
        
    @classmethod
    def tocar_faixa(
        cls,
        token,
        device_id,
        uri
    ):
        resposta = requests.put(
            (
                "https://api.spotify.com/v1/me/player/play"
                f"?device_id={device_id}"
            ),
            headers={
                "Authorization":
                f"Bearer {token}"
            },
            json={
                "uris": [
                    uri
                ]
            },
            timeout=10
        )

        return (
            resposta.status_code
            in (
                200,
                202,
                204
            )
        )
    
    @classmethod
    def play(
        cls,
        token,
        device_id
    ):

        resposta = requests.put(
            (
                "https://api.spotify.com/v1/me/player/play"
                f"?device_id={device_id}"
            ),
            headers={
                "Authorization":
                f"Bearer {token}"
            },
            timeout=10
        )

        return resposta.status_code in (
            200,
            202,
            204
        )

    @classmethod
    def pause(
        cls,
        token
    ):

        resposta = requests.put(
            "https://api.spotify.com/v1/me/player/pause",
            headers={
                "Authorization":
                f"Bearer {token}"
            },
            timeout=10
        )

        return resposta.status_code in (
            200,
            202,
            204
        )

    @classmethod
    def next(
        cls,
        token
    ):

        resposta = requests.post(
            "https://api.spotify.com/v1/me/player/next",
            headers={
                "Authorization":
                f"Bearer {token}"
            },
            timeout=10
        )

        return resposta.status_code in (
            200,
            202,
            204
        )

    @classmethod
    def previous(
        cls,
        token
    ):

        resposta = requests.post(
            "https://api.spotify.com/v1/me/player/previous",
            headers={
                "Authorization":
                f"Bearer {token}"
            },
            timeout=10
        )

        return resposta.status_code in (
            200,
            202,
            204
        )