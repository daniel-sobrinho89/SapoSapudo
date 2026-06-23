# domains/conversas/qwen_proxy.py

import threading

from domains.conversas.qwen_local_client import QwenLocalClient


class QwenProxy:
    def __init__(self):
        self.client = None
        self.pronto = False

        threading.Thread(target=self._carregar, daemon=True).start()

    def _carregar(self):
        self.client = QwenLocalClient()
        self.pronto = True

    def gerar(self, prompt, system):
        if not self.pronto:
            return {"texto": "Ainda estou acordando.", "arquivo_audio": None}

        return self.client.gerar(prompt, system)
