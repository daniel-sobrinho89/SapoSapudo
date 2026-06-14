import os

IS_ANDROID = (
    "ANDROID_ARGUMENT"
    in os.environ
)

if IS_ANDROID:
    from jnius import autoclass
    from urllib.parse import quote

    PythonActivity = autoclass(
        "org.kivy.android.PythonActivity"
    )

    Intent = autoclass(
        "android.content.Intent"
    )

    Uri = autoclass(
        "android.net.Uri"
    )

class SpotifyAndroid:

    @staticmethod
    def tocar(
        pesquisa=None
    ):
        if (
            not IS_ANDROID
            or not SpotifyAndroid.instalado()
        ):
            return False

        try:

            activity = (
                PythonActivity.mActivity
            )

            if (
                pesquisa
                and pesquisa.strip()
            ):
                intent = Intent(
                    Intent.ACTION_VIEW,
                    Uri.parse(
                        f"spotify:search:{quote(pesquisa)}"
                    )
                )
            else:
                intent = Intent(
                    Intent.ACTION_VIEW,
                    Uri.parse(
                        "spotify:home"
                    )
                )

            intent.addFlags(
                Intent.FLAG_ACTIVITY_NEW_TASK
            )

            activity.startActivity(
                intent
            )

            return True

        except Exception:
            return False
        
    @staticmethod
    def instalado():
        if not IS_ANDROID:
            return False

        try:
            activity = PythonActivity.mActivity
            package_manager = activity.getPackageManager()
            package_manager.getPackageInfo("com.spotify.music", 0)

            return True
        except Exception:
            return False