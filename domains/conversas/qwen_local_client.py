import os

IS_ANDROID = "ANDROID_ARGUMENT" in os.environ

if IS_ANDROID:
    from jnius import autoclass

    from android.storage import app_storage_path

    QwenBridge = autoclass("domains.voz.java.QwenBridge")

    class QwenLocalClient:
        def __init__(self):
            self.bridge = QwenBridge()

            base_path = app_storage_path()

            model_path = os.path.join(
                base_path,
                "app",
                "domains",
                "conversas",
                "qwen2.5-1.5b-instruct-q8_0.gguf",
            )

            print("APP_STORAGE =", base_path)
            print("QWEN_PATH =", model_path)
            print("QWEN_EXISTS =", os.path.exists(model_path))

            if not os.path.exists(model_path):
                raise RuntimeError(f"Modelo não encontrado: {model_path}")

            sucesso = self.bridge.inicializar(model_path)

            if not sucesso:
                raise RuntimeError(f"Falha ao carregar modelo: {model_path}")

        def gerar(self, prompt, system):
            texto = self.bridge.generate(system, prompt)

            return {"texto": texto.strip() if texto else "", "arquivo_audio": None}

else:

    class QwenLocalClient:
        pass
