from contextlib import suppress

from core.platform import IS_ANDROID

PALAVRAS_BLOQUEADAS = ("estou ouvindo", "lá lá lá")

if IS_ANDROID:
    from jnius import PythonJavaClass, autoclass, java_method

    Locale = autoclass("java.util.Locale")
    TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
    PythonActivity = autoclass("org.kivy.android.PythonActivity")

    class _TTSListener(PythonJavaClass):
        __javainterfaces__ = ["android/speech/tts/TextToSpeech$OnInitListener"]

        def __init__(self, service):
            super().__init__()
            self.service = service

        @java_method("(I)V")
        def onInit(self, status):
            if status == TextToSpeech.SUCCESS:
                self.service.pronto = True
                print("TTS pronto")

else:

    class _TTSListener:
        pass


class TTSService:
    def __init__(self):
        self.tts = None
        self.listener = None
        self.disponivel = False
        self.pronto = False

        if not IS_ANDROID:
            return

        try:
            activity = PythonActivity.mActivity
            self.pronto = False

            self.listener = _TTSListener(self)

            self.tts = TextToSpeech(activity, self.listener)

            self.tts.setLanguage(Locale("pt", "BR"))

            self.disponivel = True

        except Exception as ex:
            print("Erro inicializando TTS:", ex)

    def falar(self, texto):
        if not self.disponivel or not self.pronto:
            return

        if not texto:
            return

        texto_lower = texto.lower()

        for bloqueada in PALAVRAS_BLOQUEADAS:
            if bloqueada in texto_lower:
                return

        try:
            self.tts.speak(texto, TextToSpeech.QUEUE_ADD, None, "sapudo")

        except Exception as ex:
            print("Erro TTS:", ex)

    def parar(self):
        if not self.disponivel:
            return

        with suppress(Exception):
            self.tts.stop()

    def destruir(self):
        if not self.disponivel:
            return

        with suppress(Exception):
            self.tts.stop()
            self.tts.shutdown()
