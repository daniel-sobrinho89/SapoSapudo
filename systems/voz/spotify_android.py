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
    def abrir_spotify():
        if not IS_ANDROID:
            return False

        try:
            activity = (
                PythonActivity.mActivity
            )
            package_manager = (
                activity.getPackageManager()
            )
            launch_intent = (
                package_manager
                .getLaunchIntentForPackage(
                    "com.spotify.music"
                )
            )

            if launch_intent:
                launch_intent.addFlags(
                    Intent.FLAG_ACTIVITY_NEW_TASK
                )
                activity.startActivity(
                    launch_intent
                )
                return True

        except Exception as ex:
            print(ex)

        return False

    @staticmethod
    def abrir_url(url):

        if not IS_ANDROID:
            return False

        try:

            Uri = autoclass(
                "android.net.Uri"
            )

            Intent = autoclass(
                "android.content.Intent"
            )

            activity =  PythonActivity.mActivity

            intent = Intent(
                Intent.ACTION_VIEW,
                Uri.parse(url)
            )

            activity.startActivity(
                intent
            )

            return True

        except Exception as ex:

            print(
                "[SPOTIFY]",
                ex
            )

        return False

    @staticmethod
    def tocar_uri(uri):

        if not IS_ANDROID:
            return False

        try:

            activity = (
                PythonActivity.mActivity
            )

            url = (
                uri.replace(
                    "spotify:track:",
                    "https://open.spotify.com/track/"
                )
            )

            intent = Intent(
                Intent.ACTION_VIEW,
                Uri.parse(url)
            )

            intent.setPackage(
                "com.spotify.music"
            )

            intent.addFlags(
                Intent.FLAG_ACTIVITY_NEW_TASK
            )

            activity.startActivity(
                intent
            )

            return True

        except Exception as ex:

            print(ex)

            return False

    @staticmethod
    def tocar(
        pesquisa=None
    ):
        if not IS_ANDROID:

            print(
                "[SPOTIFY] Não é Android"
            )

            return False

        try:

            activity = (
                PythonActivity.mActivity
            )

            package_manager = (
                activity.getPackageManager()
            )

            print(
                f"[SPOTIFY] Pesquisa recebida: [{pesquisa}]"
            )

            if (
                pesquisa
                and pesquisa.strip()
            ):

                try:

                    pesquisa = (
                        pesquisa.strip()
                    )

                    print(
                        f"[SPOTIFY] Pesquisando: {pesquisa}"
                    )

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

                    print(
                        "[SPOTIFY] Busca enviada"
                    )

                    return True

                except Exception as ex:

                    print(
                        f"[SPOTIFY] Falha na busca: {ex}"
                    )

                    traceback.print_exc()

            print(
                "[SPOTIFY] Tentando abrir pelo pacote"
            )

            try:

                launch_intent = (
                    package_manager
                    .getLaunchIntentForPackage(
                        "com.spotify.music"
                    )
                )

                if launch_intent is not None:

                    launch_intent.addFlags(
                        Intent.FLAG_ACTIVITY_NEW_TASK
                    )

                    activity.startActivity(
                        launch_intent
                    )

                    print(
                        "[SPOTIFY] Aplicativo aberto pelo pacote"
                    )

                    return True

                print(
                    "[SPOTIFY] LaunchIntent retornou None"
                )

            except Exception as ex:

                print(
                    f"[SPOTIFY] Falha ao abrir pelo pacote: {ex}"
                )

                traceback.print_exc()

            print(
                "[SPOTIFY] Tentando URI direta"
            )

            try:

                intent = Intent(
                    Intent.ACTION_VIEW,
                    Uri.parse(
                        "spotify:"
                    )
                )

                intent.addFlags(
                    Intent.FLAG_ACTIVITY_NEW_TASK
                )

                activity.startActivity(
                    intent
                )

                print(
                    "[SPOTIFY] Spotify aberto por URI"
                )

                return True

            except Exception as ex:
                print(
                    f"[SPOTIFY] URI direta falhou: {ex}"
                )
                traceback.print_exc()

            try:

                termo = ""

                if (
                    pesquisa
                    and pesquisa.strip()
                ):
                    termo = quote(
                        pesquisa.strip()
                    )

                if termo:
                    url = (f"https://open.spotify.com/search/{termo}")
                else:
                    url = ("https://open.spotify.com")

                intent = Intent(
                    Intent.ACTION_VIEW,
                    Uri.parse(url)
                )

                intent.addFlags(
                    Intent.FLAG_ACTIVITY_NEW_TASK
                )

                activity.startActivity(
                    intent
                )

                print(
                    "[SPOTIFY] Spotify Web aberto"
                )

                return True

            except Exception as ex:

                print(
                    f"[SPOTIFY] Spotify Web falhou: {ex}"
                )

                traceback.print_exc()

            return False

        except Exception as ex:
            print(
                f"[SPOTIFY] ERRO GERAL: {ex}"
            )

            traceback.print_exc()

            return False