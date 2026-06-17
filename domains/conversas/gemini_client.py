import requests


class GeminiClient:
    def __init__(self, api_key, modelo="gemini-2.5-flash"):
        self.api_key = api_key
        self.modelo = modelo

        self.session = requests.Session()

        self.url = (
            "https://generativelanguage.googleapis.com"
            f"/v1beta/models/{modelo}:generateContent"
        )

    def gerar(self, prompt):
        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.8,
                    "topP": 0.95,
                    "maxOutputTokens": 2000,
                },
                "safetySettings": [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE",
                    },
                ],
            }

            resposta = self.session.post(
                f"{self.url}?key={self.api_key}", json=payload, timeout=(5, 30)
            )

            resposta.raise_for_status()

            dados = resposta.json()

            candidates = dados.get("candidates", [])

            if not candidates:
                return "Fiquei sem palavras."

            return dados["candidates"][0]["content"]["parts"][0]["text"]

        except Exception as ex:
            print(f"[GEMINI] Erro: {type(ex).__name__}: {ex}")

            if hasattr(ex, "response") and ex.response is not None:
                print("[GEMINI] Status:", ex.response.status_code)
                print("[GEMINI] Body:", ex.response.text)

            return "A lagoa está sem conexão com os espíritos da internet."
