import os

IS_ANDROID = (
    "ANDROID_ARGUMENT"
    in os.environ
)

ULTIMO_CODE = None

if IS_ANDROID:

    from android import activity

class SpotifyCallback:

    @staticmethod
    def iniciar():

        if not IS_ANDROID:
            return

        activity.bind(
            on_new_intent=(
                SpotifyCallback._novo_intent
            )
        )

        print(
            "[SPOTIFY] Callback registrado"
        )

    @staticmethod
    def _novo_intent(*args):
        print("[SPOTIFY] ARGS:", len(args))

        global ULTIMO_CODE

        try:

            intent = args[-1]

            print(
                "[SPOTIFY] NOVO INTENT:",
                intent
            )

            data = intent.getData()

            print(
                "[SPOTIFY] DATA:",
                data
            )

            if not data:
                return

            print(
                "[SPOTIFY] URI:",
                data.toString()
            )

            code = data.getQueryParameter(
                "code"
            )

            print("[SPOTIFY] CODE:", code)

            ULTIMO_CODE = code

        except Exception as ex:
            print("[SPOTIFY] Erro callback:", ex)

            import traceback
            traceback.print_exc()

    @staticmethod
    def obter_code():

        global ULTIMO_CODE

        code = ULTIMO_CODE

        ULTIMO_CODE = None

        return code