import os

IS_ANDROID = (
    "ANDROID_ARGUMENT"
    in os.environ
)

if IS_ANDROID:

    from jnius import (
        autoclass,
        PythonJavaClass,
        java_method
    )

    PythonActivity = autoclass(
        "org.kivy.android.PythonActivity"
    )

    Intent = autoclass(
        "android.content.Intent"
    )

    RecognizerIntent = autoclass(
        "android.speech.RecognizerIntent"
    )

    SpeechRecognizer = autoclass(
        "android.speech.SpeechRecognizer"
    )

    String = autoclass(
        "java.lang.String"
    )

    Integer = autoclass(
        "java.lang.Integer"
    )


class ReconhecedorAndroid:

    def __init__(self):

        self.ativo = False
        self.ativo_usuario = False
        self.ultimo_texto = None

        if not IS_ANDROID:
            return

        self.activity = (
            PythonActivity.mActivity
        )

        self.recognizer = None

        self.listener = (
            SpeechRecognitionListener(
                self
            )
        )

    def iniciar(self):

        if not IS_ANDROID:
            return

        self.inicializar_recognizer()

        if self.recognizer is None:
            return

        if self.ativo:
            return

        self.ativo = True

        intent = Intent(
            RecognizerIntent.ACTION_RECOGNIZE_SPEECH
        )

        intent.putExtra(
            RecognizerIntent.EXTRA_LANGUAGE_MODEL,
            RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
        )

        intent.putExtra(
            RecognizerIntent.EXTRA_LANGUAGE,
            String("pt-BR")
        )

        intent.putExtra(
            RecognizerIntent.EXTRA_PARTIAL_RESULTS,
            False
        )

        intent.putExtra(
            RecognizerIntent.EXTRA_MAX_RESULTS,
            Integer(1)
        )

        self.activity.runOnUiThread(
            IniciarEscutaRunnable(
                self,
                intent
            )
        )

    def inicializar_recognizer(self):

        if self.recognizer is not None:
            return

        self.activity.runOnUiThread(
            CriarRecognizerRunnable(
                self
            )
        )

    def parar(self):

        if not IS_ANDROID:
            return

        self.ativo = False

        try:
            self.recognizer.stopListening()
        except Exception:
            pass

    def destruir(self):

        if not IS_ANDROID:
            return

        try:
            self.recognizer.destroy()
        except Exception:
            pass

    def obter_texto(self):

        texto = self.ultimo_texto

        self.ultimo_texto = None

        return texto


if IS_ANDROID:

    class SpeechRecognitionListener(
        PythonJavaClass
    ):

        __javainterfaces__ = [
            "android/speech/RecognitionListener"
        ]

        __javacontext__ = "app"

        def __init__(
            self,
            reconhecedor
        ):

            super().__init__()

            self.reconhecedor = (
                reconhecedor
            )

        @java_method("(Landroid/os/Bundle;)V")
        def onReadyForSpeech(
            self,
            params
        ):
            pass

        @java_method("()V")
        def onBeginningOfSpeech(self):
            pass

        @java_method("(F)V")
        def onRmsChanged(
            self,
            rmsdB
        ):
            pass

        @java_method("([B)V")
        def onBufferReceived(
            self,
            buffer
        ):
            pass

        @java_method("()V")
        def onEndOfSpeech(self):
            pass

        @java_method("(I)V")
        def onError(
            self,
            error
        ):

            ERROR_SPEECH_TIMEOUT = 6
            ERROR_NO_MATCH = 7

            self.reconhecedor.ativo = False

            if (
                error in (
                    ERROR_SPEECH_TIMEOUT,
                    ERROR_NO_MATCH
                )
                and self.reconhecedor.ativo_usuario
            ):
                self.reconhecedor.iniciar()

        @java_method("(Landroid/os/Bundle;)V")
        def onResults(
            self,
            results
        ):

            try:

                lista = results.getStringArrayList(
                    SpeechRecognizer.RESULTS_RECOGNITION
                )

                if (
                    lista
                    and lista.size() > 0
                ):

                    texto = lista.get(
                        0
                    )

                    self.reconhecedor.ultimo_texto = str(texto)

                    self.reconhecedor.ativo = False

                    if self.reconhecedor.ativo_usuario:
                        self.reconhecedor.iniciar()

            except Exception:
                pass

        @java_method("(Landroid/os/Bundle;)V")
        def onPartialResults(
            self,
            partialResults
        ):
            pass

        @java_method("(ILandroid/os/Bundle;)V")
        def onEvent(
            self,
            eventType,
            params
        ):
            pass

if IS_ANDROID:
    class CriarRecognizerRunnable(
        PythonJavaClass
    ):

        __javainterfaces__ = [
            "java/lang/Runnable"
        ]

        __javacontext__ = "app"

        def __init__(
            self,
            reconhecedor
        ):
            super().__init__()
            self.reconhecedor = reconhecedor

        @java_method("()V")
        def run(self):

            self.reconhecedor.recognizer = (
                SpeechRecognizer.createSpeechRecognizer(
                    self.reconhecedor.activity
                )
            )

            self.reconhecedor.recognizer.setRecognitionListener(
                self.reconhecedor.listener
            )

            if self.reconhecedor.ativo_usuario:
                self.reconhecedor.iniciar()

    class IniciarEscutaRunnable(
        PythonJavaClass
    ):

        __javainterfaces__ = [
            "java/lang/Runnable"
        ]

        __javacontext__ = "app"

        def __init__(
            self,
            reconhecedor,
            intent
        ):
            super().__init__()

            self.reconhecedor = reconhecedor
            self.intent = intent

        @java_method("()V")
        def run(self):

            self.reconhecedor.recognizer.startListening(
                self.intent
            )