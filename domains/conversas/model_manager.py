import os

IS_ANDROID = "ANDROID_ARGUMENT" in os.environ

if IS_ANDROID:
    import json
    import threading
    from pathlib import Path

    import requests
    from kivy.clock import Clock

    MODEL_VERSION = "1"

    MIN_MODEL_SIZE = 1_500_000_000

    MODEL_URL = (
        "https://huggingface.co/Qwen/"
        "Qwen2.5-1.5B-Instruct-GGUF/resolve/main/"
        "qwen2.5-1.5b-instruct-q8_0.gguf"
    )

    from android.storage import app_storage_path

    BASE_DIR = Path(app_storage_path()) / "models"
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    MODEL_FILE = BASE_DIR / "qwen.gguf"
    VERSION_FILE = BASE_DIR / "model_version.json"
    TEMP_MODEL_FILE = BASE_DIR / "qwen.gguf.download"

    class ModelManager:
        def __init__(self):
            self.status = ""
            self.progresso = 0

            self.pronto = False
            self.baixando = False

            self._callbacks_pronto = []

        @property
        def caminho_modelo(self):
            return str(MODEL_FILE)

        def ao_ficar_pronto(self, callback):
            self._callbacks_pronto.append(callback)

        def _modelo_valido(self):
            if not MODEL_FILE.exists():
                return False

            if MODEL_FILE.stat().st_size < MIN_MODEL_SIZE:
                return False

            if not VERSION_FILE.exists():
                return False

            try:
                dados = json.loads(VERSION_FILE.read_text(encoding="utf-8"))

                return dados.get("version") == MODEL_VERSION

            except Exception:
                return False

        def iniciar_download(self):
            if self._modelo_valido():
                self.pronto = True
                self.status = "🐸 A lagoa está pronta para conversar."

                for callback in self._callbacks_pronto:
                    Clock.schedule_once(lambda dt, cb=callback: cb())

                return

            if self.baixando:
                return

            self.baixando = True

            threading.Thread(target=self._baixar_modelo, daemon=True).start()

        def _baixar_modelo(self):
            try:
                if TEMP_MODEL_FILE.exists():
                    TEMP_MODEL_FILE.unlink()

                self.status = "🐸 Baixando sabedoria dos sapos..."

                resposta = requests.get(MODEL_URL, stream=True, timeout=(30, 7200))

                resposta.raise_for_status()

                total = int(resposta.headers.get("content-length", 0))

                baixado = 0

                with open(TEMP_MODEL_FILE, "wb") as f:
                    for chunk in resposta.iter_content(chunk_size=1024 * 1024):
                        if not chunk:
                            continue

                        f.write(chunk)

                        baixado += len(chunk)

                        if total:
                            self.progresso = int(baixado * 100 / total)

                            self.status = (
                                f"🐸 Baixando sabedoria dos sapos... {self.progresso}%"
                            )

                TEMP_MODEL_FILE.replace(MODEL_FILE)

                self._salvar_versao()

                self.pronto = True

                self.status = "🐸 A lagoa está pronta para conversar."

                for callback in self._callbacks_pronto:
                    Clock.schedule_once(lambda dt, cb=callback: cb())

            except Exception as ex:
                print(f"[MODEL_MANAGER] erro download: {ex}")

                if TEMP_MODEL_FILE.exists():
                    TEMP_MODEL_FILE.unlink()

                self.status = "🐸 Não consegui reunir a sabedoria dos sapos."

            finally:
                self.baixando = False

        def _salvar_versao(self):
            VERSION_FILE.write_text(
                json.dumps({"version": MODEL_VERSION}), encoding="utf-8"
            )

else:

    class ModelManager:
        pass
