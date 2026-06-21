import os

from jnius import autoclass

QwenBridge = autoclass("domains.voz.java.QwenBridge")


class QwenLocalClient:
    def __init__(self):
        self.bridge = QwenBridge()

        model_path = (
            "/data/data/"
            "br.com.saposapudo.saposapudo/"
            "files/app/"
            "domains/conversas/"
            "qwen2.5-1.5b-instruct-q8_0.gguf"
        )

        if not os.path.exists(model_path):
            raise RuntimeError(f"Modelo não encontrado: {model_path}")

        sucesso = self.bridge.inicializar(model_path)

        if not sucesso:
            raise RuntimeError(f"Falha ao carregar modelo: {model_path}")

    def gerar(self, prompt, system):
        texto = self.bridge.generate(system, prompt)

        return {"texto": texto.strip() if texto else "", "arquivo_audio": None}
