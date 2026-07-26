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

import kivy_adapter
from config import ALTURA, CENTRO_Y, FPS, IS_ANDROID, LARGURA
from core.ambiente import Ambiente
from core.audio_manager import AudioManager
from core.event_bus import event_bus
from core.mouse_events import DoubleClickDetector
from domains.cenario import EstadoJogo, GerenciadorCenarios
from domains.clima.clima_service import ClimaService
from domains.clima.nuvem import Nuvem
from domains.clima.sistema_nuvens import SistemaNuvens
from domains.conversas.conversa_sapudo import ConversaSapudo
from domains.conversas.qwen_local_client import QwenLocalClient
from domains.sapudo.entity import Sapo
from domains.spotify.controller import ControladorVozMusical, ControladorVozMusicalNulo
from domains.spotify.spotify_manager import SpotifyManager
from domains.voz.tts_service import TTSService
from render.asset_manager import asset_manager
from render.background_renderer import BackgroundRenderer
from render.controle_renderer import ControleRenderer
from render.pensamento_sapo_renderer import PensamentoSapoRenderer
from render.transform_utils import TransformUtils
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
        self._inicializar_controles()
        self._inicializar_sistemas_base()
        self._inicializar_clima_e_ambiente()
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

    def _inicializar_controles(self):
        self.tecla_esquerda_pressionada = False
        self.tecla_direita_pressionada = False
        Window.bind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)

    def _inicializar_sistemas_base(self):
        self.transform = TransformUtils()
        self.ambiente = Ambiente()
        self.pensamento_renderer = PensamentoSapoRenderer()
        self.tts = TTSService()

    def _inicializar_clima_e_ambiente(self):
        self.clima_service = ClimaService()

        self.background_renderer = BackgroundRenderer(
            tela, LARGURA, ALTURA, self.transform, self.clima_service, self.ambiente
        )
        self.controle_renderer = ControleRenderer(tela, asset_manager, self.transform)
        self.sistema_nuvens = SistemaNuvens(self.transform)

    def _inicializar_interacao(self):
        self.sapo = Sapo(
            centro_x,
            CENTRO_Y,
            self.spotify,
            self.clima_service,
        )
        self.sapo.background_renderer = self.background_renderer

        self.gerenciador_cenarios = GerenciadorCenarios(
            tela,
            self.transform,
            self.clima_service,
            self.background_renderer,
            self.sistema_nuvens,
            self.sapo,
            self.ambiente,
        )

        self.gerenciador_cenarios.cenario_principal.carregar()

        self.client = QwenLocalClient()
        self.conversa_sapudo = ConversaSapudo(self.client)

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

        # Resetar estados visuais dos botões se sair da área
        if not self.controle_renderer.rect_clique_esquerda.collidepoint(pos_virtual):
            self.controle_renderer.botao_esquerda_pressionado = False

        if not self.controle_renderer.rect_clique_direita.collidepoint(pos_virtual):
            self.controle_renderer.botao_direita_pressionado = False

    def on_touch_up(self, touch):
        pos_virtual = real_to_virtual(touch.pos)

        # Resetar Controles do Sapo
        self.controle_renderer.botao_esquerda_pressionado = False
        self.controle_renderer.botao_direita_pressionado = False

        self.controlador_voz_musical.processar_toque_up(pos_virtual)

    def on_key_down(self, window, key, scancode, codepoint, modifiers):
        # seta esquerda
        if key == 276:
            self.tecla_esquerda_pressionada = True
            self.controlador_voz_musical.iniciar_controle_esquerda()

        # seta direita
        if key == 275:
            self.tecla_direita_pressionada = True
            self.controlador_voz_musical.iniciar_controle_direita()

        return True

    def on_key_up(self, window, key, scancode):
        if key == 276:
            self.tecla_esquerda_pressionada = False
            self.controlador_voz_musical.parar_controle_esquerda()

        if key == 275:
            self.tecla_direita_pressionada = False
            self.controlador_voz_musical.parar_controle_direita()

        return True

    def _atualizar_clima(self, dt):
        if self.clima_service.precisa_atualizar():

            def atualizar_clima():
                self.clima_service.atualizar()

            threading.Thread(target=atualizar_clima, daemon=True).start()

        self.clima_service.atualizar_visual(dt)

    def update(self, dt):
        dt = min(dt, 0.05)

        self._atualizar_clima(dt)
        self.sapo.atualizar(dt)

        if self.clima_service.precisa_atualizar():
            event_bus.publicar("clima_atualizado", clima_data=self.clima_service)

        self.spotify.atualizar_spotify(dt)

        if not self.controlador_voz_musical.inicializado and self.cenario.carregado:
            self.controlador_voz_musical = ControladorVozMusical(
                self.sapo,
                self.spotify,
                self.audio,
                self.controle_renderer,
                self.cenario,
                self.clima_service,
                self.conversa_sapudo,
                self.tts,
            )

        self.controlador_voz_musical.atualizar(dt)

        self.ambiente.atualizar(dt, self.clima_service)
        self.gerenciador_cenarios.atualizar(dt)
        self.sistema_nuvens.atualizar_area_interna()

        Nuvem.finalizar_carregamento()
        self.sistema_nuvens.atualizar(
            dt,
            self.clima_service.cloudiness_visual,
            self.clima_service.future_cloudiness_1h,
            self.clima_service.future_cloudiness_2h,
            self.clima_service.future_cloudiness_3h,
            self.clima_service.wind_direction,
            self.clima_service.wind_speed,
        )

        self.gerenciador_cenarios.renderizar(dt)
        self.pensamento_renderer.renderizar(tela, self.sapo, dt)

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
