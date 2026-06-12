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

import pygame_adapter
import threading
import math

from config import *
from constants import *

from entities.sapo import Sapo
from systems.animacoes_folha import AnimacoesFolha
from systems.ambiente import Ambiente
from systems.particulas.poeira import ParticulaPoeira
from systems.clima.frasco import FrascoClimatico
from systems.clima.evento_livro import EventoLivro

from render.asset_manager import asset_manager
from render.transform_utils import TransformUtils
from render.background_renderer import BackgroundRenderer
from render.sapo_renderer import SapoRenderer, PensamentoSapoRenderer
from render.tamandua_renderer import TamanduaRenderer
from render.barraca_renderer import BarracaRenderer

from systems.clima.clima_service import ClimaService
from systems.clima.sistema_nuvens import SistemaNuvens
from systems.clima.nuvem import Nuvem

from render.duende_renderer import DuendeRenderer
from entities.duende_neblina import DuendeNeblina
from systems.audio_manager import AudioManager

from entities.violao import Violao
from render.violao_renderer import ViolaoRenderer
from entities.semente import Semente
from render.semente_renderer import SementeRenderer
from render.controle_renderer import ControleRenderer

# =========================================
# INIT
# =========================================

# Kivy-based application: window size
info_w, info_h = Window.width, Window.height
LARGURA_REAL = int(info_w)
ALTURA_REAL = int(info_h)

# superficie virtual usada por todo o jogo (resolução lógica fixa)

# manter a variável `tela` como a superfície virtual para compatibilidade
tela_virtual = pygame_adapter.Surface((LARGURA, ALTURA))
tela = tela_virtual

clock = pygame_adapter.Clock()

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
    @property
    def tem_duende(self):
        return self.duende is not None

    @property
    def tem_feira(self):
        return self.tamandua_renderer is not None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.audio = AudioManager()

        Clock.schedule_once(
            lambda dt: self.audio.iniciar(),
            2
        )

        self.tecla_esquerda_pressionada = False

        Window.bind(
            on_key_down=self.on_key_down,
            on_key_up=self.on_key_up
        )

        # initialize game state (mirrors previous top-level init)
        self.transform = TransformUtils()
        self.ambiente = Ambiente()
        self.sapo_renderer = SapoRenderer(tela, asset_manager, self.transform)
        self.pensamento_renderer = PensamentoSapoRenderer()
        self.animacoes_folha = AnimacoesFolha()
        self.duende = None
        self.renderer_duende = None
        self.violao = Violao()
        self.renderer_violao = ViolaoRenderer(tela, asset_manager, self.transform)
        self.semente = None
        self.renderer_semente = None
        self.frasco_climatico = FrascoClimatico(self.transform)
        self.frasco_climatico.atualizar_posicao(centro_y)
        self.particulas = [ParticulaPoeira(self.frasco_climatico.area_particulas, self.frasco_climatico.area_pote) for _ in range(QUANTIDADE_POEIRA)]
        self.evento_livro = EventoLivro(asset_manager, self.transform)        
        self.evento_livro.particulas = self.particulas
        for p in self.particulas:
            p.area_protegida = self.frasco_climatico.area_pote
            p.protegido = p.area_protegida.collidepoint(int(p.x), int(p.y))
        

        self.clima_service = ClimaService()

        self.background_renderer = BackgroundRenderer(tela, LARGURA, ALTURA, self.transform, self.clima_service)
        self.controle_renderer = ControleRenderer(
            tela,
            asset_manager,
            self.transform
        )

        self.tamandua_renderer = None
        self.barraca_renderer = None
        if self.background_renderer.cenario_feira:
            self.carregar_cenario_feira()
        else:
            self.carregar_cenario_principal()

        self.sistema_nuvens = SistemaNuvens(self.transform)
        self.sapo = Sapo(centro_x, centro_y, self.clima_service)
        self.sapo.background_renderer = (self.background_renderer)
        # interaction state
        self.drag_duende = False
        self.drag_violao = False
        self.cenario_feira_anterior = False

        # drawing setup
        with self.canvas:
            self.texture = Texture.create(
                size=(LARGURA, ALTURA),
                colorfmt='rgba'
            )
            self.texture.flip_vertical()
            self.rect = Rectangle(
                texture=self.texture,
                pos=(0, 0),
                size=Window.size
            )

        # schedule updates
        Clock.schedule_interval(self.update, 1.0 / FPS)

    def carregar_cenario_feira(self):

        self.tamandua_renderer = TamanduaRenderer(
            tela,
            self.transform
        )

        self.barraca_renderer = BarracaRenderer(
            tela,
            self.transform,
            LARGURA,
            ALTURA
        )

        x_barraca, y_barraca = (
            self.barraca_renderer.obter_posicao()
        )

        self.tamandua_renderer.definir_posicao(
            x_barraca + 33,
            y_barraca - 25
        )

    def descarregar_cenario_feira(self):

        self.tamandua_renderer = None
        self.barraca_renderer = None

    def carregar_cenario_principal(self):

        self.duende = DuendeNeblina()
        self.renderer_duende = DuendeRenderer(
            tela,
            asset_manager,
            self.transform
        )
        self.duende.violao_monitorado = self.violao

        self.semente = Semente()

        self.renderer_semente = SementeRenderer(
            tela,
            asset_manager,
            self.transform
        )

    def descarregar_cenario_principal(self):

        self.duende = None
        self.renderer_duende = None

        self.semente = None
        self.renderer_semente = None

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

        if (
            IS_ANDROID
            and self.controle_renderer.rect.collidepoint(
                pos_virtual
            )
        ):
            self.sapo.iniciar_controle_esquerda()
            return True

        # =========================
        # LIVRO
        # =========================
        if self.evento_livro.livro_aberto_visivel:
            self.evento_livro.fechar_livro_aberto()
            return True

        if self.evento_livro.livro_visivel:
            if (
                self.evento_livro.rect_livro
                and self.evento_livro.rect_livro.collidepoint(pos_virtual)
            ):
                self.evento_livro.ocultar_livro_por_clique()
                return True

        # =========================
        # POEIRA
        # =========================
        if not self.evento_livro.livro_visivel:
            for particula in self.particulas:
                if (
                    particula.ativa
                    and particula.obter_rect().collidepoint(pos_virtual)
                ):
                    particula.ativa = False
                    self.evento_livro.registrar_clique_poeira()
                    return True

        # =========================
        # DUENDE
        # =========================

        if (
            self.tem_duende
            and self.duende.corpo_rect.collidepoint(pos_virtual)
        ):
            self.drag_duende = True
            self.duende.iniciar_arraste(*pos_virtual)

            return True

        # =========================
        # VIOLÃO ACOPLADO AO SAPO
        # =========================

        if self.violao.acoplado:
            distancia = (
                (pos_virtual[0] - self.sapo.x) ** 2 +
                (pos_virtual[1] - self.sapo.y) ** 2
            ) ** 0.5

            if distancia < 120:
                self.violao.acoplado = False
                self.sapo.parar_violao()
                self.drag_violao = True
                self.audio.alternar_musica_violao()
                self.violao.iniciar_arraste(*pos_virtual)
                return True

        # =========================
        # VIOLÃO NORMAL
        # =========================

        if self.renderer_violao.obter_rect(self.violao).collidepoint(pos_virtual):
            self.drag_violao = True
            self.violao.iniciar_arraste(*pos_virtual)

            return True

        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        pos_virtual = real_to_virtual(touch.pos)

        if self.drag_violao:
            self.violao.mover_arraste(*pos_virtual)
        if (
            self.drag_duende
            and self.tem_duende
        ):
            self.duende.mover_arraste(*pos_virtual)

    def on_touch_up(self, touch):
        pos_virtual = real_to_virtual(touch.pos)

        self.sapo.parar_controle_esquerda()

        if self.drag_violao:
            self.drag_violao = False
            self.violao.finalizar_arraste()
            area_sapo = pygame_adapter.Rect(self.sapo.x - 80, self.sapo.y - 80, 160, 160)
            if area_sapo.collidepoint(self.violao.x, self.violao.y) and self.sapo.pode_receber_violao():
                self.violao.acoplado = True
                self.sapo.iniciar_violao()
                self.violao.x = self.sapo.x + 5
                self.violao.y = self.sapo.y + 20
            else:
                self.violao.iniciar_queda()
                if (
                    self.tem_duende
                    and self.duende.pode_resgatar_violao()
                ):
                    distancia_violao = abs(self.violao.x - self.duende.x)
                    MIN_TELEPORT_DIST = 120
                    if not self.duende.consegue_alcancar_antes_da_queda(self.violao) and distancia_violao > MIN_TELEPORT_DIST:
                        self.duende.teleportar_para_violao(self.violao)
                    self.duende.iniciar_resgate_violao(self.violao)

        if (
            self.drag_duende
            and self.tem_duende
        ):
            self.drag_duende = False
            self.duende.finalizar_arraste(self.frasco_climatico.area_interna)
            if self.duende.esta_dentro_do_frasco(self.frasco_climatico.area_interna):
                self.duende.animacoes.iniciar_sono()
                self.duende.animacoes.iniciar_sono_programado()
            elif self.duende.animacoes.dormindo:
                self.duende.animacoes.iniciar_acordar()
                self.duende.animacoes.cancelar_sono_programado()
                self.duende.escolher_novo_destino()

    def on_key_down(
        self,
        window,
        key,
        scancode,
        codepoint,
        modifiers
    ):
        # seta esquerda
        if key == 276:
            self.tecla_esquerda_pressionada = True
            self.sapo.iniciar_controle_esquerda()

        return True

    def on_key_up(
        self,
        window,
        key,
        scancode
    ):
        if key == 276:
            self.tecla_esquerda_pressionada = False
            self.sapo.parar_controle_esquerda()

        return True

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
        self.ambiente.atualizar(
            dt,
            influencia_clima
        )

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
        self.frasco_climatico.atualizar(dt)
        self.evento_livro.atualizar(dt)
        self.sistema_nuvens.atualizar_area_interna()

        Nuvem.finalizar_carregamento()
        self.sistema_nuvens.atualizar(dt, self.clima_service.cloudiness_visual, self.clima_service.future_cloudiness_1h, self.clima_service.future_cloudiness_2h, self.clima_service.future_cloudiness_3h, self.clima_service.wind_direction, self.clima_service.wind_speed)

        events = self.sapo.atualizar(dt, self.ambiente, self.animacoes_folha, self.violao)

        if (
            not self.cenario_feira_anterior
            and self.background_renderer.cenario_feira
        ):
            self.sistema_nuvens.limpar()
            self.descarregar_cenario_principal()

            import gc
            gc.collect()

            self.carregar_cenario_feira()

        if (
            self.cenario_feira_anterior
            and not self.background_renderer.cenario_feira
        ):
            self.sistema_nuvens.limpar()
            self.descarregar_cenario_feira()

            import gc
            gc.collect()

            self.carregar_cenario_principal()

        self.cenario_feira_anterior = (
            self.background_renderer.cenario_feira
        )

        if events.get('start_audio_violao'):
            self.audio.alternar_musica_violao()
        if events.get('stop_audio_violao'):
            self.audio.alternar_musica_violao()
        if events.get("start_audio_passeio"):
            self.audio.tocar_passeio_sapudo()

        sistema_fisica.aplicar_forca_vento(self.sapo, self.clima_service, dt, sensibilidade=0.25)

        pote_x = centro_x - 260
        pote_y = centro_y + 40

        if not self.background_renderer.cenario_feira:
            self.duende.atualizar(dt, self.sapo, pote_x, pote_y, self.clima_service, self.frasco_climatico.area_interna, self.ambiente)
            sistema_fisica.aplicar_forca_vento(self.duende, self.clima_service, dt, sensibilidade=0.5)

            self.semente.atualizar(dt, self.clima_service)

            for particula in self.particulas:
                particula.atualizar(self.ambiente, dt)

        # render
        self.background_renderer.desenhar()

        if self.background_renderer.cenario_feira:
            self.tamandua_renderer.atualizar(dt)
            self.tamandua_renderer.renderizar()
            self.barraca_renderer.renderizar()

        self.sistema_nuvens.renderizar(tela, self.background_renderer.eh_dia())
        self.sapo_renderer.renderizar(self.sapo.x, self.sapo.y, ESCALA, self.sapo.animacoes)
        self.pensamento_renderer.renderizar(tela, self.sapo)

        if not self.background_renderer.cenario_feira:
            self.frasco_climatico.renderizar(tela, centro_y)

            if not self.evento_livro.livro_visivel:
                for particula in self.particulas:
                    particula.desenhar(tela)
                    
                self.frasco_climatico.desenhar_nevoa(
                    tela,
                    self.evento_livro.nevoa
                )

            self.renderer_duende.renderizar(self.duende)
            self.renderer_semente.renderizar(self.semente)

            self.evento_livro.renderizar(tela, self.frasco_climatico)
            self.evento_livro.renderizar_livro_aberto(tela, self.clima_service)

        if not self.violao.acoplado:
            self.renderer_violao.renderizar(self.violao)

        # escalonar e apresentar
        img = tela._img

        if IS_ANDROID:
            self.controle_renderer.renderizar()

        self.texture.blit_buffer(
            img.tobytes(),
            colorfmt='rgba',
            bufferfmt='ubyte'
        )

        self.canvas.ask_update()

class GameApp(App):
    def build(self):
        return GameWidget()


if __name__ == '__main__':
    GameApp().run()