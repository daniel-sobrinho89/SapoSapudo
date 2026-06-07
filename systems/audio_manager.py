import pygame

from config import (
    AUDIO_HABILITADO,
    MUSICA_FUNDO,
    VOLUME_MUSICA
)
from utils.paths import BASE_DIR


class AudioManager:

    def __init__(self):

        self.habilitado = AUDIO_HABILITADO

        pygame.mixer.init()

        pygame.mixer.music.load(
            str(BASE_DIR / MUSICA_FUNDO)
        )

        pygame.mixer.music.set_volume(
            VOLUME_MUSICA
        )

        if self.habilitado:
            pygame.mixer.music.play(-1)

    def iniciar(self):

        if not self.habilitado:
            return

        pygame.mixer.music.play(-1)

    def alternar(self):

        if self.habilitado:
            self.desligar()
        else:
            self.ligar()

    def ligar(self):

        if not self.habilitado:

            self.habilitado = True

            pygame.mixer.music.unpause()

            self.iniciar()

    def desligar(self):

        if not self.habilitado:
            return

        pygame.mixer.music.pause()

        self.habilitado = False