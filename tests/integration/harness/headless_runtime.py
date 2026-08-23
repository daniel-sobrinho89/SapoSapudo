"""Compatibilidade mínima para executar a suíte integrada sem Kivy.

Os testes integrados exercitam o domínio, UseCases, navegação e coordenador,
mas não precisam abrir janela, carregar textura ou reproduzir áudio. Quando
Kivy não está instalado, criamos somente os módulos de import necessários
para que o adapter existente do projeto possa ser importado.

Nada deste arquivo é importado pelo jogo normal.
"""

from __future__ import annotations

import importlib.util
import sys
import types


def garantir_runtime_headless() -> None:
    if importlib.util.find_spec("kivy") is not None:
        return

    kivy = types.ModuleType("kivy")
    core = types.ModuleType("kivy.core")
    image = types.ModuleType("kivy.core.image")
    window = types.ModuleType("kivy.core.window")
    audio = types.ModuleType("kivy.core.audio")

    class CoreImage:
        def __init__(self, *args, **kwargs):
            self.texture = None

    class _Window:
        width = 1280
        height = 720
        mouse_pos = (0, 0)

    class _SoundLoader:
        @staticmethod
        def load(*args, **kwargs):
            return None

    image.Image = CoreImage
    window.Window = _Window()
    audio.SoundLoader = _SoundLoader

    kivy.core = core
    core.image = image
    core.window = window
    core.audio = audio

    sys.modules.setdefault("kivy", kivy)
    sys.modules.setdefault("kivy.core", core)
    sys.modules.setdefault("kivy.core.image", image)
    sys.modules.setdefault("kivy.core.window", window)
    sys.modules.setdefault("kivy.core.audio", audio)
