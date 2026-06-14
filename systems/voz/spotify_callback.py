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

            activity = (
                PythonActivity.mActivity
            )

            intent = (
                activity.getIntent()
            )

            data = intent.getData()

            if data is None:
                return None

            code = data.getQueryParameter(
                "code"
            )

            intent.setData(None)

            return code

        except Exception:
            return None