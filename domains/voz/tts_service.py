from contextlib import suppress

from core.event_bus import event_bus
from core.platform import IS_ANDROID

PALAVRAS_BLOQUEADAS = ("estou ouvindo", "lá lá lá")

if IS_ANDROID:
    from jnius import PythonJavaClass, autoclass, java_method

    Locale = autoclass("java.util.Locale")
    TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Bundle = autoclass("android.os.Bundle")
    JavaString = autoclass("java.lang.String")
    UtteranceProgressListener = autoclass(
        "android.speech.tts.UtteranceProgressListener"
    )

    class _TTSListener(PythonJavaClass):
        __javainterfaces__ = ["android/speech/tts/TextToSpeech$OnInitListener"]

        def __init__(self, service):
            super().__init__()
            self.service = service

        @java_method("(I)V")
        def onInit(self, status):
            if status == TextToSpeech.SUCCESS:
                self.service.tts.setLanguage(Locale("pt", "BR"))
                self.service.pronto = True
                self.service.disponivel = True
                print("TTS pronto")
            else:
                print("Falha ao inicializar TTS:", status)

    class _UtteranceListener(PythonJavaClass):
        __javainterfaces__ = ["android/speech/tts/UtteranceProgressListener"]

        def __init__(self, service):
            super().__init__()
            self.service = service

        @java_method("(Ljava/lang/String;)V")
        def onStart(self, utteranceId):
            self.service.on_start()

        @java_method("(Ljava/lang/String;)V")
        def onDone(self, utteranceId):
            self.service.on_done()

        @java_method("(Ljava/lang/String;)V")
        def onError(self, utteranceId):
            self.service.on_done()

else:

    class _TTSListener:
        pass

    class _UtteranceListener:
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
            self.disponivel = False

            self.listener = _TTSListener(self)

            self.tts = TextToSpeech(activity, self.listener)

            self.progress_listener = _UtteranceListener(self)
            self.tts.setOnUtteranceProgressListener(self.progress_listener)

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
            params = Bundle()

            self.tts.speak(
                JavaString(texto), TextToSpeech.QUEUE_ADD, params, JavaString("sapudo")
            )

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

    def on_start(self):
        event_bus.publicar("tts_iniciado")

    def on_done(self):
        event_bus.publicar("tts_finalizado")
