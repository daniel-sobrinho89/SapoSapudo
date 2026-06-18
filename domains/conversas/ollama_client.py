import requests


class OllamaClient:
    def __init__(self, host, modelo):
        self.host = host
        self.modelo = modelo

        self.session = requests.Session()

    def gerar(self, prompt, system=None):
        try:
            resposta = self.session.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.modelo,
                    "system": system or "",
                    "prompt": prompt,
                    "stream": False,
                    "keep_alive": "24h",
                    "options": {"num_predict": 150, "temperature": 0.5},
                },
                timeout=(10, 300),
            )

            resposta.raise_for_status()

            dados = resposta.json()
            texto = dados.get("response", "").strip()

            if not texto:
                return "As águas da lagoa estão silenciosas hoje."

            return texto

        except Exception as ex:
            print(f"[OLLAMA] Erro: {type(ex).__name__}: {ex}")

            return "A lagoa local parece estar em silêncio."
