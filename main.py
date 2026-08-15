# =========================================
# MAIN.PY
# =========================================


import logging
import os

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Rectangle
from kivy.graphics.texture import Texture
from kivy.uix.widget import Widget

import utils.kivy_adapter as kivy_adapter
from application.coordenador_estado_jogo import CoordenadorEstadoJogo
from core.mouse_events import DoubleClickDetector
from domains.cenario import EstadoJogo, GerenciadorCenarios
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

        self._toques = {}
        self._distancia_pinca = None
        self.double_click = DoubleClickDetector()
        self._inicializar_sistemas_base()
        self._inicializar_interacao()
        self._configurar_graficos()

        # schedule updates
        Clock.schedule_interval(self.update, 1.0 / FPS)

    def _inicializar_sistemas_base(self):
        self.transform = TransformUtils()
        self.pensamento_renderer = PensamentoSapoRenderer()

    def _inicializar_interacao(self):
        self.gerenciador_cenarios = GerenciadorCenarios(tela, self.transform)

        self.gerenciador_cenarios.cenario_principal.carregar()
        self.coordenador_estado_jogo = CoordenadorEstadoJogo(
            self.gerenciador_cenarios.cenario_principal
        )

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
        self._toques[touch.uid] = touch
        pos_virtual = real_to_virtual(touch.pos)

        camera = self.cenario.camera
        # Scroll do mouse
        if "button" in touch.profile:
            if touch.button == "scrolldown":
                camera.afastar()
                return True

            if touch.button == "scrollup":
                camera.aproximar()
                return True

        if (
            self.gerenciador_cenarios.estado == EstadoJogo.ABERTURA
            and self.double_click.detectar(pos_virtual)
        ):
            self.gerenciador_cenarios.estado = EstadoJogo.JOGANDO
            return True

        if self.cenario.carregado:
            self.coordenador_estado_jogo.processar_toque_down(pos_virtual)

        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        pos_virtual = real_to_virtual(touch.pos)

        self._toques[touch.uid] = touch

        if len(self._toques) == 2:
            dedos = list(self._toques.values())

            x1, y1 = dedos[0].pos
            x2, y2 = dedos[1].pos

            distancia = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

            if self._distancia_pinca is not None:
                delta = distancia - self._distancia_pinca

                if abs(delta) > 10:
                    camera = self.cenario.camera

                    camera.definir_zoom(camera.zoom + delta * 0.002)

            self._distancia_pinca = distancia

        if self.cenario.carregado:
            self.coordenador_estado_jogo.processar_on_touch_move(pos_virtual)

    def on_touch_up(self, touch):
        pos_virtual = real_to_virtual(touch.pos)

        self._toques.pop(touch.uid, None)

        if len(self._toques) < 2:
            self._distancia_pinca = None

        if self.cenario.carregado:
            self.coordenador_estado_jogo.processar_toque_up(pos_virtual)

    def update(self, dt):
        dt = min(dt, 0.05)

        if self.cenario.carregado:
            self.coordenador_estado_jogo.executar(dt)

        self.gerenciador_cenarios.atualizar(dt)

        self.gerenciador_cenarios.renderizar(dt)
        self.pensamento_renderer.renderizar(tela, dt)

        # escalonar e apresentar
        img = tela._img
        self.texture.blit_buffer(img.tobytes(), colorfmt="rgba", bufferfmt="ubyte")
        self.canvas.ask_update()


class GameApp(App):
    def build(self):
        return GameWidget()

    def on_stop(self):
        pass


if __name__ == "__main__":
    GameApp().run()
