from kivy.utils import platform

try:
    IS_ANDROID = platform == "android"

except Exception:
    IS_ANDROID = False
