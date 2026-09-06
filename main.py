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
from application.cenario import EstadoJogo, GerenciadorCenarios
from application.coordenador_estado_jogo import CoordenadorEstadoJogo
from core.input_teclas import normalizar_tecla
from render.transform_utils import TransformUtils
from utils.config import ALTURA, FPS, IS_ANDROID, LARGURA
from utils.input import init_scaling, real_to_virtual

logging.getLogger().setLevel(logging.INFO)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)


if not IS_ANDROID:
    os.environ["SDL_AUDIODRIVER"] = "alsa"
    os.environ["AUDIODEV"] = "hw:2,0"

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._toques = {}
        self._distancia_pinca = None
        self.teclas_pressionadas = set()
        Window.bind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)
        Window.bind(on_focus=self._on_window_focus)
        self._inicializar_sistemas_base()
        self._inicializar_interacao()
        self._configurar_graficos()
        self._carregamento_iniciado = True

        # schedule updates
        Clock.schedule_interval(self.update, 1.0 / FPS)

    def _inicializar_sistemas_base(self):
        self.transform = TransformUtils()

    def _inicializar_interacao(self):
        self.gerenciador_cenarios = GerenciadorCenarios(tela, self.transform)

        self.gerenciador_cenarios.estado = EstadoJogo.JOGANDO
        self.gerenciador_cenarios.cenario_principal.iniciar_carregamento()
        self.coordenador_estado_jogo = CoordenadorEstadoJogo(self.gerenciador_cenarios)

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
        if getattr(self, "gerenciador_cenarios", None) is not None:
            pos = real_to_virtual(touch.pos)
            if self.gerenciador_cenarios.world_editor_ativo:
                self.gerenciador_cenarios.world_editor_set_mouse_button(
                    getattr(touch, "button", None)
                )
                self.gerenciador_cenarios.world_editor_touch_down(pos)
                self.gerenciador_cenarios.world_editor_set_mouse_button(None)
                return True

            self.coordenador_estado_jogo.processar_toque_down(pos)
            return True
        return True

    def on_touch_move(self, touch):
        if getattr(self, "gerenciador_cenarios", None) is not None:
            pos = real_to_virtual(touch.pos)
            if self.gerenciador_cenarios.world_editor_ativo:
                self.gerenciador_cenarios.world_editor_touch_move(pos)
                return True

            self.coordenador_estado_jogo.processar_on_touch_move(pos)
            return True
        return True

    def on_touch_up(self, touch):
        if getattr(self, "gerenciador_cenarios", None) is not None:
            pos = real_to_virtual(touch.pos)
            if self.gerenciador_cenarios.world_editor_ativo:
                self.gerenciador_cenarios.world_editor_touch_up(pos)
                return True

            self.coordenador_estado_jogo.processar_toque_up(pos)
            return True
        return True

    @staticmethod
    def _normalizar_tecla(keycode, text):
        return normalizar_tecla(keycode, text)

    def _on_key_down(self, _window, keycode, _scancode, text, _modifiers):
        tecla = self._normalizar_tecla(keycode, text)
        self.teclas_pressionadas.add(tecla)
        if tecla == "escape" and self.cenario.conversa_controller.aberta:
            self.cenario.conversa_controller.cancelar_dialogo()
            return True
        self.coordenador_estado_jogo.processar_tecla_down(tecla)
        return True

    def _on_window_focus(self, _window, focus):
        # Alguns backends perdem KEYUP ao trocar foco/janela. Nunca deixamos
        # uma tecla de movimento ficar presa nesse caso.
        if not focus:
            self.teclas_pressionadas.clear()
            if getattr(self, "coordenador_estado_jogo", None) is not None:
                self.coordenador_estado_jogo.sapudo_manual.teclas.clear()

    def _on_key_up(self, _window, keycode, _scancode):
        tecla = self._normalizar_tecla(keycode, "")
        self.teclas_pressionadas.discard(tecla)
        self.coordenador_estado_jogo.processar_tecla_up(tecla)
        return True

    def _renderizar_relogio_dia_noite(self):
        """Mostra a hora do mundo sem participar da iluminação do cenário."""
        ciclo = getattr(self.cenario, "ciclo_dia_noite", None)
        if ciclo is None:
            return

        periodo = {
            "manha": "Manhã",
            "tarde": "Tarde",
            "noite": "Noite",
        }.get(ciclo.periodo, ciclo.periodo.capitalize())

        largura = 150
        altura = 42
        margem = 12
        x = LARGURA - largura - margem
        y = margem

        kivy_adapter.draw.rect(
            self.cenario.tela,
            (20, 28, 34, 215),
            kivy_adapter.Rect(x, y, largura, altura),
        )
        kivy_adapter.draw.text(
            self.cenario.tela,
            f"{ciclo.horario_formatado}  {periodo}",
            (x + 12, y + 11),
            (245, 238, 205),
            18,
        )

    def _renderizar_tela_carregamento(self, progresso):
        tela = self.cenario.tela
        tela.fill((18, 28, 34, 255))
        kivy_adapter.draw.text(
            tela,
            "SapoSapudo",
            (LARGURA // 2 - 92, ALTURA // 2 - 80),
            (235, 220, 165),
            30,
        )
        kivy_adapter.draw.text(
            tela,
            "Carregando o mundo...",
            (LARGURA // 2 - 105, ALTURA // 2 - 38),
            (225, 230, 232),
            20,
        )

        largura = 520
        altura = 18
        x = (LARGURA - largura) // 2
        y = ALTURA // 2 + 8
        kivy_adapter.draw.rect(
            tela,
            (35, 48, 56, 255),
            kivy_adapter.Rect(x, y, largura, altura),
        )
        preenchida = max(0, min(largura, int(largura * progresso)))
        if preenchida:
            kivy_adapter.draw.rect(
                tela,
                (139, 211, 107, 255),
                kivy_adapter.Rect(x, y, preenchida, altura),
            )

        kivy_adapter.draw.text(
            tela,
            f"{int(progresso * 100):02d}%",
            (LARGURA // 2 - 18, y + 28),
            (190, 205, 210),
            16,
        )

    def update(self, dt):
        dt = min(dt, 0.05)

        if not self.cenario.carregado:
            self.cenario.processar_carregamento(max_tipos=1)
            self.gerenciador_cenarios.renderizar(dt)
            self._renderizar_tela_carregamento(self.cenario.progresso_carregamento())
        else:
            self.coordenador_estado_jogo.executar(dt, self.teclas_pressionadas)
            self.gerenciador_cenarios.atualizar(dt)
            self.gerenciador_cenarios.renderizar(dt)
            self._renderizar_relogio_dia_noite()

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
