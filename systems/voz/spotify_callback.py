import os

IS_ANDROID = (
    "ANDROID_ARGUMENT"
    in os.environ
)

if IS_ANDROID:

    from jnius import autoclass

    PythonActivity = autoclass(
        "org.kivy.android.PythonActivity"
    )


class SpotifyCallback:

    @staticmethod
    def obter_code():

        if not IS_ANDROID:
            return None

        try:

            activity = PythonActivity.mActivity
            print("[SPOTIFY] Activity:", activity)
            print("[SPOTIFY] TASK ID:", activity.getTaskId())

            intent =  activity.getIntent()
            print("[SPOTIFY] Intent:", intent)
            print("[SPOTIFY] ACTION:", intent.getAction())
            print("[SPOTIFY] INTENT:", intent.toString())

            if intent is None:
                print("[SPOTIFY] Intent é None")
                return None

            data = intent.getData()

            print("[SPOTIFY] Data:", data)

            if data is None:
                print("[SPOTIFY] Data é None")
                return None

            try:
                print("[SPOTIFY] URI:", data.toString())
            except Exception:
                pass

            code = data.getQueryParameter("code")

            print("[SPOTIFY] Code:", code)

            intent.setData(None)

            return code

        except Exception as ex:

            import traceback

            print("[SPOTIFY] Erro obter_code:", ex)

            traceback.print_exc()

            return None