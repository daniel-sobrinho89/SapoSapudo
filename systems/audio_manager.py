import kivy_adapter

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
        self.musica_atual = None

    def inicializar(self):
        if self.inicializado:
            return

        kivy_adapter.mixer.init()

        kivy_adapter.mixer.music.load(
            str(BASE_DIR / MUSICA_FUNDO)
        )

        kivy_adapter.mixer.music.set_volume(
            VOLUME_MUSICA
        )

        self.inicializado = True

    def iniciar(self):

        self.inicializar()

        if not self.habilitado:
            return

        kivy_adapter.mixer.music.play(-1)

    def alternar_musica_violao(self):

        if self.habilitado:
            self.desligar()
        else:
            self.habilitado = True
            self.voltar_musica_fundo()

    def tocar_musica_fundo(self, arquivo):
        self.musica_atual = arquivo

        kivy_adapter.mixer.music.load(arquivo)
        kivy_adapter.mixer.music.play(-1)

    def tocar_musica_temporaria(self, arquivo):

        if self.musica_atual:
            self.pilha_musicas.append(self.musica_atual)

        self.musica_atual = arquivo

        kivy_adapter.mixer.music.load(arquivo)
        kivy_adapter.mixer.music.play()

    def tocar_passeio_sapudo(self):
        kivy_adapter.mixer.music.load(
            str(BASE_DIR / "assets/musica/o_passeio_do_sapudo.mp3")
        )

        kivy_adapter.mixer.music.set_volume(
            VOLUME_MUSICA
        )

        kivy_adapter.mixer.music.play()

    def voltar_musica_fundo(self):
        kivy_adapter.mixer.music.pause()
        kivy_adapter.mixer.music._sound = None
        kivy_adapter.mixer.music.load(
            str(BASE_DIR / MUSICA_FUNDO)
        )

        kivy_adapter.mixer.music.set_volume(
            VOLUME_MUSICA
        )

        kivy_adapter.mixer.music.play(-1)

    def ligar(self):

        if not self.habilitado:

            self.habilitado = True

            kivy_adapter.mixer.music.unpause()

            self.iniciar()

    def desligar(self):

        if not self.habilitado:
            return

        kivy_adapter.mixer.music.pause()

        self.habilitado = False