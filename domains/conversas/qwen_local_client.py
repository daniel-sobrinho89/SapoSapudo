import os

IS_ANDROID = "ANDROID_ARGUMENT" in os.environ

if IS_ANDROID:
    from jnius import autoclass

    from domains.conversas.model_manager import ModelManager

    QwenBridge = autoclass("domains.voz.java.QwenBridge")

    class QwenLocalClient:
        def __init__(self):
            self.bridge = QwenBridge()
            self.model_manager = ModelManager()
            self.inicializado = False
            self.model_manager.ao_ficar_pronto(self._inicializar_modelo)
            self.model_manager.iniciar_download()

        def gerar(self, prompt, system):
            if not self.inicializado:
                return {
                    "texto": "🐸 Ainda estou reunindo a sabedoria ancestral dos sapos.",
                    "arquivo_audio": None,
                }

            texto = self.bridge.generate(system, prompt)

            return {
                "texto": texto.strip() if texto else "",
                "arquivo_audio": None,
            }

        def _inicializar_modelo(self):
            sucesso = self.bridge.inicializar(self.model_manager.caminho_modelo)
            if not sucesso:
                raise RuntimeError("Falha ao inicializar modelo Qwen.")
            self.inicializado = True
else:

    class QwenLocalClient:
        pass
