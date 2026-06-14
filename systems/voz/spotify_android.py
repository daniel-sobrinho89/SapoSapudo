import os

IS_ANDROID = (
    "ANDROID_ARGUMENT"
    in os.environ
)

if IS_ANDROID:
    from jnius import autoclass
    from urllib.parse import quote
    import traceback
    
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
        if not IS_ANDROID:
            print("[SPOTIFY] Não é Android")
            return False

        if not SpotifyAndroid.instalado():
            print("[SPOTIFY] Spotify não instalado")
            return False

        try:
            activity = PythonActivity.mActivity

            if (
                pesquisa
                and pesquisa.strip()
            ):
                pesquisa = pesquisa.strip()
                print(f"[SPOTIFY] Pesquisando: {pesquisa}")

                try:
                    intent = Intent(
                        Intent.ACTION_VIEW,
                        Uri.parse(
                            f"spotify:search:{quote(pesquisa)}"
                        )
                    )
                    intent.addFlags(
                        Intent.FLAG_ACTIVITY_NEW_TASK
                    )

                    activity.startActivity(
                        intent
                    )

                    print("[SPOTIFY] Busca enviada")
                    return True

                except Exception as ex:
                    print(f"[SPOTIFY] Falha na busca: {ex}")
                    traceback.print_exc()

            print("[SPOTIFY] Abrindo aplicativo")

            intent = (
                activity
                .getPackageManager()
                .getLaunchIntentForPackage(
                    "com.spotify.music"
                )
            )

            if intent is None:
                print("[SPOTIFY] LaunchIntent retornou None")

                return False

            intent.addFlags(
                Intent.FLAG_ACTIVITY_NEW_TASK
            )

            activity.startActivity(
                intent
            )

            print("[SPOTIFY] Aplicativo aberto")

            return True

        except Exception as ex:
            print(f"[SPOTIFY] ERRO GERAL: {ex}")
            traceback.print_exc()

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
        except Exception as ex:
            print(f"[SPOTIFY] Não instalado: {ex}")
            return False