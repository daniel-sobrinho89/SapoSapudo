import pygame


class AudioManager:

    def __init__(self):

        pygame.mixer.init()

    def tocar_musica(
        self,
        arquivo,
        volume=0.3
    ):

        pygame.mixer.music.load(
            arquivo
        )

        pygame.mixer.music.set_volume(
            volume
        )

        pygame.mixer.music.play(
            -1
        )  # loop infinito