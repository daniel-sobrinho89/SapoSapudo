# =========================================
# MAIN.PY
# =========================================

import os
IS_ANDROID = 'ANDROID_ARGUMENT' in os.environ

if not IS_ANDROID:
    os.environ["SDL_AUDIODRIVER"] = "alsa"
    os.environ["AUDIODEV"] = "hw:2,0"

import logging
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.core.window import Window

import pygame
import threading
import math

from config import *
from constants import *

from entities.sapo import Sapo
from systems.animacoes_folha import AnimacoesFolha
from systems.ambiente import Ambiente
from systems.particulas.poeira import ParticulaPoeira
from systems.clima.frasco import FrascoClimatico

from render.asset_manager import AssetManager
from render.transform_utils import TransformUtils
from render.background_renderer import BackgroundRenderer
from render.sapo_renderer import SapoRenderer

from systems.clima.clima_service import ClimaService
from systems.clima.sistema_nuvens import SistemaNuvens

from render.duende_renderer import DuendeRenderer
from entities.duende_neblina import DuendeNeblina
from systems.audio_manager import AudioManager

from entities.violao import Violao
from render.violao_renderer import ViolaoRenderer
from entities.semente import Semente
from render.semente_renderer import SementeRenderer

# =========================================
# INIT
# =========================================

# Kivy-based application: window size
info_w, info_h = Window.width, Window.height
LARGURA_REAL = int(info_w)
ALTURA_REAL = int(info_h)

# superficie virtual usada por todo o jogo (resolução lógica fixa)

# manter a variável `tela` como a superfície virtual para compatibilidade
tela_virtual = pygame.Surface((LARGURA, ALTURA))
tela = tela_virtual

clock = pygame.Clock()

from utils.input import (
    init_scaling,
    real_to_virtual
)

# inicializar escala para helpers de input
init_scaling(LARGURA_REAL, ALTURA_REAL, LARGURA, ALTURA)

# detectar se estamos rodando no Android (Buildozer)
IS_ANDROID = 'ANDROID_ARGUMENT' in os.environ


# =========================================
# POSITION
# =========================================

centro_x = LARGURA // 2

centro_y = (
    ALTURA // 2
    + CENTRO_OFFSET_Y
)

# =========================================
# Kivy App wrapper
# =========================================

class GameWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.audio = AudioManager()

        Clock.schedule_once(
            lambda dt: self.audio.iniciar(),
            2
        )
        # initialize game state (mirrors previous top-level init)
        self.assets = AssetManager()
        self.transform = TransformUtils()
        self.background_renderer = BackgroundRenderer(tela, LARGURA, ALTURA, self.transform)
        self.ambiente = Ambiente()
        self.sapo_renderer = SapoRenderer(tela, self.assets, self.transform)
        self.animacoes_folha = AnimacoesFolha()
        self.duende = DuendeNeblina()
        self.renderer_duende = DuendeRenderer(tela, self.assets, self.transform)
        self.violao = Violao()
        self.renderer_violao = ViolaoRenderer(tela, self.assets, self.transform)
        self.duende.violao_monitorado = self.violao
        self.semente = Semente()
        self.renderer_semente = SementeRenderer(tela, self.assets, self.transform)
        self.frasco_climatico = FrascoClimatico(self.transform)
        self.frasco_climatico.atualizar_posicao(centro_y)
        self.particulas = [ParticulaPoeira(self.frasco_climatico.area_particulas, self.frasco_climatico.area_pote) for _ in range(QUANTIDADE_POEIRA)]
        for p in self.particulas:
            p.area_protegida = self.frasco_climatico.area_pote
            p.protegido = p.area_protegida.collidepoint(int(p.x), int(p.y))
        self.clima_service = ClimaService()
        self.sistema_nuvens = SistemaNuvens(self.frasco_climatico.area_interna, self.transform)
        self.sapo = Sapo(centro_x, centro_y)

        # interaction state
        self.drag_duende = False
        self.drag_violao = False

        # drawing setup
        with self.canvas:
            self.texture = Texture.create(
                size=(
                    int(Window.width),
                    int(Window.height)
                ),
                colorfmt='rgba'
            )
            self.texture.flip_vertical()
            self.rect = Rectangle(texture=self.texture, pos=self.pos, size=(LARGURA_REAL, ALTURA_REAL))

        # schedule updates
        Clock.schedule_interval(self.update, 1.0 / FPS)

    def on_size(self, *args):
        self.rect.size = (self.width, self.height)

        init_scaling(
            self.width,
            self.height,
            LARGURA,
            ALTURA
        )

    def on_pos(self, *args):
        self.rect.pos = self.pos

    def on_touch_down(self, touch):
        pos_virtual = real_to_virtual(touch.pos)

        if self.duende.corpo_rect.collidepoint(pos_virtual):
            self.drag_duende = True
            self.duende.iniciar_arraste(*pos_virtual)
            return True

        elif self.renderer_violao.obter_rect(self.violao).collidepoint(pos_virtual):
            self.drag_violao = True
            self.violao.iniciar_arraste(*pos_virtual)
            return True

        if (self.violao.acoplado and self.sapo_renderer.corpo_rect.collidepoint(pos_virtual)):
            self.violao.acoplado = False
            self.sapo.parar_violao()
            self.drag_violao = True
            self.audio.alternar()
            self.violao.iniciar_arraste(*pos_virtual)
            return True

        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        pos_virtual = real_to_virtual(touch.pos)

        if self.drag_violao:
            self.violao.mover_arraste(*pos_virtual)
        if self.drag_duende:
            self.duende.mover_arraste(*pos_virtual)

    def on_touch_up(self, touch):
        pos_virtual = real_to_virtual(touch.pos)

        if self.drag_violao:
            self.drag_violao = False
            self.violao.finalizar_arraste()
            area_sapo = pygame.Rect(centro_x - 80, centro_y - 80, 160, 160)
            if area_sapo.collidepoint(self.violao.x, self.violao.y) and self.sapo.pode_receber_violao():
                self.violao.acoplado = True
                self.sapo.iniciar_violao()
                self.violao.x = centro_x + 5
                self.violao.y = centro_y + 20
            else:
                self.violao.iniciar_queda()
                if self.duende.pode_resgatar_violao():
                    distancia_violao = abs(self.violao.x - self.duende.x)
                    MIN_TELEPORT_DIST = 120
                    if not self.duende.consegue_alcancar_antes_da_queda(self.violao) and distancia_violao > MIN_TELEPORT_DIST:
                        self.duende.teleportar_para_violao(self.violao)
                    self.duende.iniciar_resgate_violao(self.violao)

        if self.drag_duende:
            self.drag_duende = False
            self.duende.finalizar_arraste(self.frasco_climatico.area_interna)
            if self.duende.esta_dentro_do_frasco(self.frasco_climatico.area_interna):
                self.duende.animacoes.iniciar_sono()
                self.duende.animacoes.iniciar_sono_programado()
            elif self.duende.animacoes.dormindo:
                self.duende.animacoes.iniciar_acordar()
                self.duende.animacoes.cancelar_sono_programado()
                self.duende.escolher_novo_destino()

    def update(self, dt):
        # cap dt
        dt = min(dt, 0.05)

        # clima update
        if self.clima_service.precisa_atualizar():
            def atualizar_clima():
                self.clima_service.atualizar()
            threading.Thread(target=atualizar_clima, daemon=True).start()

        self.clima_service.atualizar_visual(dt)

        direcao_rad = math.radians(self.clima_service.wind_direction + 180)
        sinal_direcao = math.sin(direcao_rad)
        influencia_clima = sinal_direcao * self.clima_service.wind_speed * 0.15
        if getattr(self.clima_service, 'rajada_ativa', False):
            influencia_clima += sinal_direcao * self.clima_service.wind_speed * 0.35

        if getattr(self.clima_service, 'rajada_ativa', False):
            self.animacoes_folha.intensidade_vento = 5.0
        else:
            self.animacoes_folha.intensidade_vento = 1.8

        # updates
        from systems.fisica import sistema_fisica
        if self.violao.caindo:
            sistema_fisica.aplicar_forca_vento(self.violao, self.clima_service, dt, sensibilidade=0.6)

        self.violao.atualizar(dt)
        self.sistema_nuvens.atualizar_area_interna(self.frasco_climatico.area_interna)
        self.sistema_nuvens.atualizar(dt, self.clima_service.cloudiness_visual, self.clima_service.future_cloudiness_1h, self.clima_service.future_cloudiness_2h, self.clima_service.future_cloudiness_3h, self.clima_service.wind_direction, self.clima_service.wind_speed)

        events = self.sapo.atualizar(dt, self.ambiente, self.animacoes_folha, self.violao)

        if events.get('start_audio'):
            self.audio.alternar()
        if events.get('stop_audio'):
            self.audio.alternar()

        sistema_fisica.aplicar_forca_vento(self.sapo, self.clima_service, dt, sensibilidade=0.25)

        sapo_x = self.sapo.x
        sapo_y = self.sapo.y
        pote_x = centro_x - 260
        pote_y = centro_y + 40

        self.duende.atualizar(dt, self.sapo, pote_x, pote_y, self.clima_service, self.frasco_climatico.area_interna, self.ambiente)
        sistema_fisica.aplicar_forca_vento(self.duende, self.clima_service, dt, sensibilidade=0.5)
        self.semente.atualizar(dt, self.clima_service)

        for particula in self.particulas:
            particula.atualizar(self.ambiente, dt)

        # render
        self.background_renderer.desenhar()
        self.sistema_nuvens.renderizar(tela, self.background_renderer.eh_dia())
        self.frasco_climatico.renderizar(tela, centro_y)
        for particula in self.particulas:
            particula.desenhar(tela)
        self.sapo_renderer.renderizar(self.sapo.x, self.sapo.y, ESCALA, self.sapo.animacoes)
        self.renderer_duende.renderizar(self.duende)
        self.renderer_semente.renderizar(self.semente)
        if not self.violao.acoplado:
            self.renderer_violao.renderizar(self.violao)

        # escalonar e apresentar
        scaled = pygame.transform.scale(
            tela,
            (LARGURA_REAL, ALTURA_REAL)
        )

        pil = scaled.pil_image()

        self.texture.blit_buffer(
            pil.tobytes(),
            colorfmt='rgba',
            bufferfmt='ubyte'
        )

        self.rect.texture = self.texture


class GameApp(App):
    def build(self):
        return GameWidget()


if __name__ == '__main__':
    GameApp().run()

pygame.quit()