import kivy_adapter
from config import AUDIO_HABILITADO, MUSICA_FUNDO, VOLUME_MUSICA
from utils.paths import BASE_DIR


class AudioManager:
    def __init__(self):
        self.habilitado = AUDIO_HABILITADO
        self.inicializado = False

        self.musica_atual = None
        self.pilha_musicas = []

        self.callback_spotify_tocando = None

    # =====================================
    # INIT
    # =====================================

    def inicializar(self):
        if self.inicializado:
            return

        kivy_adapter.mixer.init()

        kivy_adapter.mixer.music.load(str(BASE_DIR / MUSICA_FUNDO))
        kivy_adapter.mixer.music.set_volume(VOLUME_MUSICA)

        self.musica_atual = MUSICA_FUNDO
        self.inicializado = True

    # =====================================
    # PLAY
    # =====================================

    def iniciar(self):
        self.inicializar()

        if not self.habilitado:
            return

        if not kivy_adapter.mixer.music.get_busy():
            kivy_adapter.mixer.music.play(-1)

    def tocar_musica_fundo(self, arquivo):
        self.inicializar()

        if self.musica_atual == arquivo:
            return

        self.musica_atual = arquivo

        kivy_adapter.mixer.music.load(str(arquivo))
        kivy_adapter.mixer.music.set_volume(VOLUME_MUSICA)
        kivy_adapter.mixer.music.play(-1)

    def tocar_musica_temporaria(self, arquivo):
        self.inicializar()

        if self.musica_atual:
            self.pilha_musicas.append(self.musica_atual)

        self.musica_atual = arquivo

        kivy_adapter.mixer.music.load(str(arquivo))
        kivy_adapter.mixer.music.set_volume(VOLUME_MUSICA)
        kivy_adapter.mixer.music.play()

    def tocar_passeio_sapudo(self):
        self.inicializar()

        arquivo = BASE_DIR / "assets/musica/o_passeio_do_sapudo.mp3"

        self.musica_atual = arquivo

        kivy_adapter.mixer.music.load(str(arquivo))
        kivy_adapter.mixer.music.set_volume(VOLUME_MUSICA)
        kivy_adapter.mixer.music.play()

    def voltar_musica_fundo(self):
        if self.habilitado and self.musica_atual == MUSICA_FUNDO:
            return

        self.habilitado = True
        self.musica_atual = MUSICA_FUNDO

        kivy_adapter.mixer.music.pause()
        kivy_adapter.mixer.music._sound = None

        kivy_adapter.mixer.music.load(str(BASE_DIR / MUSICA_FUNDO))
        kivy_adapter.mixer.music.set_volume(VOLUME_MUSICA)
        kivy_adapter.mixer.music.play(-1)

    # =====================================
    # CONTROLE
    # =====================================

    def alternar_musica_violao(self):
        if self.habilitado:
            self.desligar()
            return

        spotify_tocando = False

        if self.callback_spotify_tocando:
            spotify_tocando = self.callback_spotify_tocando()

        if spotify_tocando:
            return

        self.ligar()

    def ligar(self):
        if self.habilitado:
            return

        self.habilitado = True

        if kivy_adapter.mixer.music.get_busy():
            kivy_adapter.mixer.music.unpause()
        else:
            self.iniciar()

    def desligar(self):
        if not self.habilitado:
            return

        kivy_adapter.mixer.music.pause()

        self.habilitado = False
