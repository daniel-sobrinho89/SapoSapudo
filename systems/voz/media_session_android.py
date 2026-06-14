import os

IS_ANDROID = (
    "ANDROID_ARGUMENT"
    in os.environ
)

if IS_ANDROID:

    from jnius import autoclass

    KeyEvent = autoclass(
        "android.view.KeyEvent"
    )

    AudioManager = autoclass(
        "android.media.AudioManager"
    )

    PythonActivity = autoclass(
        "org.kivy.android.PythonActivity"
    )


class MediaSessionAndroid:

    @staticmethod
    def enviar(keycode):

        if not IS_ANDROID:
            return

        try:

            activity = (
                PythonActivity.mActivity
            )

            audio_manager = (
                activity.getSystemService(
                    activity.AUDIO_SERVICE
                )
            )

            down = KeyEvent(
                KeyEvent.ACTION_DOWN,
                keycode
            )

            up = KeyEvent(
                KeyEvent.ACTION_UP,
                keycode
            )

            audio_manager.dispatchMediaKeyEvent(
                down
            )

            audio_manager.dispatchMediaKeyEvent(
                up
            )

        except Exception as ex:

            print(
                f"MediaSession erro: {ex}"
            )

    @classmethod
    def pause(cls):

        cls.enviar(
            KeyEvent.KEYCODE_MEDIA_PAUSE
        )

    @classmethod
    def play(cls):

        cls.enviar(
            KeyEvent.KEYCODE_MEDIA_PLAY
        )

    @classmethod
    def next(cls):

        cls.enviar(
            KeyEvent.KEYCODE_MEDIA_NEXT
        )

    @classmethod
    def previous(cls):

        cls.enviar(
            KeyEvent.KEYCODE_MEDIA_PREVIOUS
        )