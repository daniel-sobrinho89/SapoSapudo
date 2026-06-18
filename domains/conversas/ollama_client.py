import requests


class OllamaClient:
    def __init__(self, host, modelo):
        self.host = host
        self.modelo = modelo

        self.session = requests.Session()

    def gerar(self, prompt):
        try:
            resposta = self.session.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.modelo,
                    "prompt": prompt,
                    "stream": False,
                    "keep_alive": "24h",
                    "options": {"num_predict": 70, "temperature": 0.7},
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
