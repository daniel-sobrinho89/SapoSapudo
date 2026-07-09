from contextlib import suppress

from kivy.clock import Clock

from core.event_bus import event_bus
from core.platform import IS_ANDROID

PALAVRAS_BLOQUEADAS = ("estou ouvindo", "lá lá lá")

if IS_ANDROID:
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    SapudoTTS = autoclass("domains.voz.java.TTS")


class TTSService:
    def __init__(self):
        self.tts = None
        self.disponivel = False
        self.pronto = False
        self.estava_falando = False
        self._ao_finalizar = None

        if not IS_ANDROID:
            return

        try:
            activity = PythonActivity.mActivity

            self.tts = SapudoTTS(activity)

            Clock.schedule_interval(self._verificar_pronto, 0.1)

            Clock.schedule_interval(self._verificar_tts, 0.1)

        except Exception as ex:
            print("Erro TTS:", ex)

    def _verificar_tts(self, dt):
        if not self.pronto:
            return

        if not self.tts:
            return

        try:
            falando = bool(self.tts.isSpeaking())

            if falando and not self.estava_falando:
                self.estava_falando = True

                event_bus.publicar("tts_iniciado")

            elif not falando and self.estava_falando:
                self.estava_falando = False

                event_bus.publicar("tts_finalizado")
                callback = self._ao_finalizar
                self._ao_finalizar = None

                if callback:
                    callback()

        except Exception:
            pass

    def falar(self, texto, ao_finalizar=None):
        if not self.pronto or not texto:
            self._ao_finalizar = None
            return

        texto_lower = texto.lower()

        for bloqueada in PALAVRAS_BLOQUEADAS:
            if bloqueada in texto_lower:
                return

        try:
            self.tts.speak(texto)
            self._ao_finalizar = ao_finalizar
        except Exception as ex:
            print(ex)

    def parar(self):
        self._ao_finalizar = None

        if not self.tts:
            return

        with suppress(Exception):
            self.tts.stop()

    def destruir(self):
        if not self.tts:
            return

        with suppress(Exception):
            Clock.unschedule(self._verificar_tts)

            Clock.unschedule(self._verificar_pronto)

            self.tts.shutdown()

    def _verificar_pronto(self, dt):
        if not self.tts:
            return

        try:
            if self.tts.isReady():
                self.pronto = True
                self.disponivel = True

                Clock.unschedule(self._verificar_pronto)

        except Exception:
            pass
