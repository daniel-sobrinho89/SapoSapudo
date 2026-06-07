import pygame_adapter

from config import (
    AUDIO_HABILITADO,
    MUSICA_FUNDO,
    VOLUME_MUSICA
)
from utils.paths import BASE_DIR


class AudioManager:

    def __init__(self):

        self.habilitado = AUDIO_HABILITADO
        self.inicializado = False

    def inicializar(self):
        if self.inicializado:
            return

        pygame_adapter.mixer.init()

        pygame_adapter.mixer.music.load(
            str(BASE_DIR / MUSICA_FUNDO)
        )

        pygame_adapter.mixer.music.set_volume(
            VOLUME_MUSICA
        )

        self.inicializado = True

    def iniciar(self):

        self.inicializar()

        if not self.habilitado:
            return

        pygame_adapter.mixer.music.play(-1)

    def alternar(self):

        if self.habilitado:
            self.desligar()
        else:
            self.ligar()

    def ligar(self):

        if not self.habilitado:

            self.habilitado = True

            pygame_adapter.mixer.music.unpause()

            self.iniciar()

    def desligar(self):

        if not self.habilitado:
            return

        pygame_adapter.mixer.music.pause()

        self.habilitado = False