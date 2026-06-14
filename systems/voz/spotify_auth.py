import requests
import secrets
import hashlib
import base64


class SpotifyAuth:

    CLIENT_ID = (
        "67fd20c2208342bda350184a50ddb4b2"
    )

    REDIRECT_URI = (
        "br.com.saposapudo://callback"
    )

    SCOPES = (
        "user-read-playback-state "
        "user-read-currently-playing "
        "user-modify-playback-state"
    )

    @staticmethod
    def gerar_code_verifier():

        return secrets.token_urlsafe(
            64
        )

    @staticmethod
    def gerar_code_challenge(
        verifier
    ):

        digest = hashlib.sha256(
            verifier.encode()
        ).digest()

        return (
            base64.urlsafe_b64encode(
                digest
            )
            .decode()
            .replace("=", "")
        )

    @classmethod
    def obter_url_login(
        cls,
        verifier
    ):

        challenge = (
            cls.gerar_code_challenge(
                verifier
            )
        )

        return (
            "https://accounts.spotify.com/authorize"
            f"?client_id={cls.CLIENT_ID}"
            "&response_type=code"
            f"&redirect_uri={cls.REDIRECT_URI}"
            f"&scope={cls.SCOPES}"
            f"&code_challenge={challenge}"
            "&code_challenge_method=S256"
        )

    @classmethod
    def trocar_code_por_token(
        cls,
        code,
        verifier
    ):

        resposta = requests.post(
            "https://accounts.spotify.com/api/token",
            data={
                "client_id": cls.CLIENT_ID,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": cls.REDIRECT_URI,
                "code_verifier": verifier
            }
        )

        if resposta.status_code != 200:
            print("[SPOTIFY] Falha token:", resposta.text)
            return None

        return resposta.json()
    
    @classmethod
    def renovar_token(
        cls,
        refresh_token
    ):

        resposta = requests.post(
            "https://accounts.spotify.com/api/token",
            data={
                "client_id":
                cls.CLIENT_ID,

                "grant_type":
                "refresh_token",

                "refresh_token":
                refresh_token
            }
        )

        if resposta.status_code != 200:
            return None

        return resposta.json()