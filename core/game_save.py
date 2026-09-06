from __future__ import annotations

import json
import sys

from utils.paths import BASE_DIR


class GameSaveManager:
    VERSION = 3
    """Persistência simples e portátil do estado lógico da partida.

    No desktop/Android grava JSON no diretório do jogo. No Web usa localStorage
    do navegador para que o save sobreviva a recarregamentos da página.
    """

    CHAVE_WEB = "sapo_sapudo_save_v1"
    ARQUIVO = "savegame.json"

    def __init__(self):
        self.path = BASE_DIR / self.ARQUIVO

    @staticmethod
    def _web_storage():
        if sys.platform != "emscripten":
            return None
        try:
            import platform

            return platform.window.localStorage
        except Exception:
            return None

    def salvar(self, estado):
        dados = json.dumps(estado, ensure_ascii=False, separators=(",", ":"))
        storage = self._web_storage()
        if storage is not None:
            storage.setItem(self.CHAVE_WEB, dados)
            return True
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.path.with_suffix(".tmp")
        temporario.write_text(dados, encoding="utf-8")
        temporario.replace(self.path)
        return True

    def existe(self):
        storage = self._web_storage()
        if storage is not None:
            try:
                return bool(storage.getItem(self.CHAVE_WEB))
            except Exception:
                return False
        return self.path.exists()

    def carregar(self):
        storage = self._web_storage()
        if storage is not None:
            dados = storage.getItem(self.CHAVE_WEB)
            if not dados:
                return None
            return json.loads(dados)
        if not self.path.exists():
            return None
        return json.loads(self.path.read_text(encoding="utf-8"))
