# =========================================
# MAIN.PY
# =========================================


import logging
import os
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Rectangle
from kivy.graphics.texture import Texture
from kivy.uix.widget import Widget

import utils.kivy_adapter as kivy_adapter
from core.audio_manager import AudioManager
from core.event_bus import event_bus
from core.mouse_events import DoubleClickDetector
from domains.cenario import EstadoJogo, GerenciadorCenarios
from domains.clima.clima_service import ClimaService
from domains.spotify.controller import ControladorVozMusical, ControladorVozMusicalNulo
from domains.spotify.spotify_manager import SpotifyManager
from domains.voz.tts_service import TTSService
from render.asset_manager import asset_manager
from render.controle_renderer import ControleRenderer
from render.pensamento_sapo_renderer import PensamentoSapoRenderer
from render.transform_utils import TransformUtils
from utils.config import ALTURA, FPS, IS_ANDROID, LARGURA
from utils.input import init_scaling, real_to_virtual

logging.getLogger().setLevel(logging.INFO)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)


if not IS_ANDROID:
    os.environ["SDL_AUDIODRIVER"] = "alsa"
    os.environ["AUDIODEV"] = "hw:2,0"

if IS_ANDROID:
    from android.permissions import Permission, request_permissions

    request_permissions([Permission.RECORD_AUDIO])


# =========================================
# INIT
# =========================================

# Kivy-based application: window size
info_w, info_h = Window.width, Window.height
LARGURA_REAL = int(info_w)
ALTURA_REAL = int(info_h)

# superficie virtual usada por todo o jogo (resolução lógica fixa)

# manter a variável `tela` como a superfície virtual para compatibilidade
tela_virtual = kivy_adapter.Surface((LARGURA, ALTURA))
tela = tela_virtual

clock = kivy_adapter.Clock()

# inicializar escala para helpers de input
init_scaling(LARGURA_REAL, ALTURA_REAL, LARGURA, ALTURA)


# =========================================
# POSITION
# =========================================

centro_x = LARGURA // 2

# =========================================
# Kivy App wrapper
# =========================================


class GameWidget(Widget):
    @property
    def cenario(self):
        return self.gerenciador_cenarios.cenario_principal

    @property
    def reconhecedor_voz(self):
        return self.controlador_voz_musical.reconhecedor_voz

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        Clock.schedule_once(
            lambda dt: self.tts.falar("A lagoa continua a mesma, mas o dia nunca é..."),
            10,
        )

        self.double_click = DoubleClickDetector()
        self._inicializar_audio_spotify()
        self._inicializar_sistemas_base()
        self._inicializar_clima()
        self._inicializar_interacao()
        self._configurar_graficos()

        # schedule updates
        Clock.schedule_interval(self.update, 1.0 / FPS)

    def _inicializar_audio_spotify(self):
        self.spotify = SpotifyManager()
        self.spotify.iniciar()

        self.audio = AudioManager()
        self.audio.callback_spotify_tocando = self.spotify.spotify_esta_tocando

        Clock.schedule_once(lambda dt: self.audio.iniciar(), 2)

    def _inicializar_sistemas_base(self):
        self.transform = TransformUtils()
        self.pensamento_renderer = PensamentoSapoRenderer()
        self.tts = TTSService()

    def _inicializar_clima(self):
        self.clima_service = ClimaService()
        self.controle_renderer = ControleRenderer(tela, asset_manager, self.transform)

    def _inicializar_interacao(self):
        self.gerenciador_cenarios = GerenciadorCenarios(
            tela,
            self.transform,
            self.clima_service,
        )

        self.gerenciador_cenarios.cenario_principal.carregar()

        self.controlador_voz_musical = ControladorVozMusicalNulo()

    def _configurar_graficos(self):
        with self.canvas:
            self.texture = Texture.create(size=(LARGURA, ALTURA), colorfmt="rgba")
            self.texture.flip_vertical()
            self.rect = Rectangle(texture=self.texture, pos=(0, 0), size=Window.size)

    def on_size(self, *args):
        self.rect.size = (self.width, self.height)

        init_scaling(self.width, self.height, LARGURA, ALTURA)

    def on_pos(self, *args):
        self.rect.pos = self.pos

    def on_touch_down(self, touch):
        pos_virtual = real_to_virtual(touch.pos)

        if (
            self.gerenciador_cenarios.estado == EstadoJogo.ABERTURA
            and self.double_click.detectar(pos_virtual)
        ):
            self.gerenciador_cenarios.estado = EstadoJogo.JOGANDO
            return True

        self.controlador_voz_musical.processar_toque_down(pos_virtual)

        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        pos_virtual = real_to_virtual(touch.pos)

        # Atualizar Arrastes
        if self.gerenciador_cenarios.tem_duende and self.cenario.duende.arrastando:
            self.cenario.duende.mover_arraste(*pos_virtual)

        self.controlador_voz_musical.processar_on_touch_move(pos_virtual)

    def on_touch_up(self, touch):
        pos_virtual = real_to_virtual(touch.pos)

        self.controlador_voz_musical.processar_toque_up(pos_virtual)

    def _atualizar_clima(self, dt):
        if self.clima_service.precisa_atualizar():

            def atualizar_clima():
                self.clima_service.atualizar()

            threading.Thread(target=atualizar_clima, daemon=True).start()

        self.clima_service.atualizar_visual(dt)

    def update(self, dt):
        dt = min(dt, 0.05)

        self._atualizar_clima(dt)

        if self.clima_service.precisa_atualizar():
            event_bus.publicar("clima_atualizado", clima_data=self.clima_service)

        self.spotify.atualizar_spotify(dt)

        if not self.controlador_voz_musical.inicializado and self.cenario.carregado:
            self.controlador_voz_musical = ControladorVozMusical(
                self.spotify,
                self.audio,
                self.controle_renderer,
                self.cenario,
                self.clima_service,
                self.tts,
            )

        self.controlador_voz_musical.atualizar(dt)
        self.gerenciador_cenarios.atualizar(dt)

        self.gerenciador_cenarios.renderizar(dt)
        self.pensamento_renderer.renderizar(tela, dt)

        # escalonar e apresentar
        img = tela._img

        self.controle_renderer.renderizar()

        self.texture.blit_buffer(img.tobytes(), colorfmt="rgba", bufferfmt="ubyte")

        self.canvas.ask_update()


class GameApp(App):
    def build(self):
        return GameWidget()

    def on_stop(self):
        if hasattr(self.root, "tts"):
            self.root.tts.destruir()

        if hasattr(self.root, "reconhecedor_voz"):
            self.root.reconhecedor_voz.destruir()


if __name__ == "__main__":
    GameApp().run()
