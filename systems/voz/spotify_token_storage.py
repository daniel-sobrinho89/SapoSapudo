import json
import os


class SpotifyTokenStorage:

    ARQUIVO = "spotify_token.json"

    @classmethod
    def salvar(
        cls,
        access_token,
        refresh_token
    ):

        with open(
            cls.ARQUIVO,
            "w",
            encoding="utf-8"
        ) as arquivo:

            json.dump(
                {
                    "access_token":
                    access_token,

                    "refresh_token":
                    refresh_token
                },
                arquivo,
                ensure_ascii=False,
                indent=4
            )

    @classmethod
    def carregar(cls):

        if not os.path.exists(
            cls.ARQUIVO
        ):
            return None

        try:

            with open(
                cls.ARQUIVO,
                "r",
                encoding="utf-8"
            ) as arquivo:

                return json.load(
                    arquivo
                )

        except Exception:

            return None