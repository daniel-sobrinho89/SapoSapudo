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
from config import ALTURA, FPS, LARGURA, QUANTIDADE_POEIRA
from constants import CENTRO_OFFSET_Y, ESCALA
from core.ambiente import Ambiente
from core.audio_manager import AudioManager
from core.event_bus import (
    PensamentoExibidoEvent,
    event_bus,
)
from core.fisica import sistema_fisica
from domains.cenario import GerenciadorCenarios
from domains.clima.animacoes.folha import AnimacoesFolha
from domains.clima.clima_service import ClimaService
from domains.clima.evento_livro import EventoLivro
from domains.clima.frasco import FrascoClimatico
from domains.clima.nuvem import Nuvem
from domains.clima.particulas.poeira import ParticulaPoeira
from domains.clima.sistema_nuvens import SistemaNuvens
from domains.conversas.conversa_sapudo import ConversaSapudo
from domains.conversas.qwen_local_client import QwenLocalClient
from domains.sapudo.entity import Sapo
from domains.spotify.controller import ControladorVozMusical
from domains.spotify.spotify_manager import SpotifyManager
from domains.violao.entity import Violao
from domains.voz.tts_service import TTSService
from render.asset_manager import asset_manager
from render.background_renderer import BackgroundRenderer
from render.controle_renderer import ControleRenderer
from render.sapo_renderer import PensamentoSapoRenderer, SapoRenderer
from render.transform_utils import TransformUtils
from render.violao_renderer import ViolaoRenderer
from utils.input import init_scaling, real_to_virtual

logging.getLogger().setLevel(logging.INFO)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)


IS_ANDROID = "ANDROID_ARGUMENT" in os.environ

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
DISTANCIA_VIOLAO = 20

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

centro_y = ALTURA // 2 + CENTRO_OFFSET_Y

# =========================================
# Kivy App wrapper
# =========================================


class GameWidget(Widget):
    @property
    def duende(self):
        return self.gerenciador_cenarios.duende

    @duende.setter
    def duende(self, valor):
        self.gerenciador_cenarios.duende = valor

    @property
    def renderer_duende(self):
        return self.gerenciador_cenarios.renderer_duende

    @renderer_duende.setter
    def renderer_duende(self, valor):
        self.gerenciador_cenarios.renderer_duende = valor

    @property
    def semente(self):
        return self.gerenciador_cenarios.semente

    @semente.setter
    def semente(self, valor):
        self.gerenciador_cenarios.semente = valor

    @property
    def renderer_semente(self):
        return self.gerenciador_cenarios.renderer_semente

    @renderer_semente.setter
    def renderer_semente(self, valor):
        self.gerenciador_cenarios.renderer_semente = valor

    @property
    def tamandua_renderer(self):
        return self.gerenciador_cenarios.tamandua_renderer

    @property
    def barraca_renderer(self):
        return self.gerenciador_cenarios.barraca_renderer

    @property
    def tem_duende(self):
        return self.gerenciador_cenarios.tem_duende

    @property
    def tem_feira(self):
        return self.gerenciador_cenarios.tem_feira

    @property
    def reconhecedor_voz(self):
        return self.controlador_voz_musical.reconhecedor_voz

    @property
    def tempo_sem_audio(self):
        return self.controlador_voz_musical.tempo_sem_audio

    @tempo_sem_audio.setter
    def tempo_sem_audio(self, valor):
        self.controlador_voz_musical.tempo_sem_audio = valor

    @property
    def spotify_andando_para_violao(self):
        return self.controlador_voz_musical.spotify_andando_para_violao

    @spotify_andando_para_violao.setter
    def spotify_andando_para_violao(self, valor):
        self.controlador_voz_musical.spotify_andando_para_violao = valor

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        Clock.schedule_once(
            lambda dt: self.tts.falar("A lagoa continua a mesma, mas o dia nunca é..."),
            10,
        )

        self._inicializar_audio_spotify()
        self._inicializar_controles()
        self._inicializar_sistemas_base()
        self._inicializar_clima_e_ambiente()
        self._inicializar_cenario()
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
        self.sapo_renderer = SapoRenderer(tela, asset_manager, self.transform)
        self.pensamento_renderer = PensamentoSapoRenderer()
        self.animacoes_folha = AnimacoesFolha()
        self.violao = Violao()
        self.renderer_violao = ViolaoRenderer(tela, asset_manager, self.transform)
        self.tts = TTSService()

    def _inicializar_clima_e_ambiente(self):
        self.frasco_climatico = FrascoClimatico(self.transform)
        self.frasco_climatico.atualizar_posicao(centro_y)
        self.particulas = [
            ParticulaPoeira(
                self.frasco_climatico.area_particulas, self.frasco_climatico.area_pote
            )
            for _ in range(QUANTIDADE_POEIRA)
        ]
        self.evento_livro = EventoLivro(asset_manager, self.transform)
        self.evento_livro.particulas = self.particulas
        for p in self.particulas:
            p.area_protegida = self.frasco_climatico.area_pote
            p.protegido = p.area_protegida.collidepoint(int(p.x), int(p.y))

        self.clima_service = ClimaService()

        self.background_renderer = BackgroundRenderer(
            tela, LARGURA, ALTURA, self.transform, self.clima_service, self.ambiente
        )
        self.controle_renderer = ControleRenderer(tela, asset_manager, self.transform)
        self.sistema_nuvens = SistemaNuvens(self.transform)

    def _inicializar_cenario(self):
        self.gerenciador_cenarios = GerenciadorCenarios(
            tela,
            self.transform,
            self.clima_service,
            self.background_renderer,
            self.sistema_nuvens,
            None,  # sapo ainda não criado
            self.violao,
            self.frasco_climatico,
            self.ambiente,
            self.evento_livro,
            self.particulas,
        )

        if self.background_renderer.cenario_feira:
            self.gerenciador_cenarios.carregar_cenario_feira()
        else:
            self.gerenciador_cenarios.carregar_cenario_principal()

    def _inicializar_interacao(self):
        self.sapo = Sapo(centro_x, centro_y, self.clima_service)
        self.sapo.background_renderer = self.background_renderer
        self.sapo.animacoes.callback_verificar_spotify = (
            self.spotify.spotify_esta_tocando
        )
        self.gerenciador_cenarios.sapo = self.sapo

        self.client = QwenLocalClient()

        self.conversa_sapudo = ConversaSapudo(self.client)

        self.controlador_voz_musical = ControladorVozMusical(
            self.sapo,
            self.violao,
            self.spotify,
            self.audio,
            self.controle_renderer,
            DISTANCIA_VIOLAO,
            self.gerenciador_cenarios,
            self.conversa_sapudo,
            self.tts,
        )

    def _configurar_graficos(self):
        with self.canvas:
            self.texture = Texture.create(size=(LARGURA, ALTURA), colorfmt="rgba")

            self.texture.flip_vertical()

            self.rect = Rectangle(texture=self.texture, pos=(0, 0), size=Window.size)

    def desligar_microfone(self):
        self.controlador_voz_musical.desligar_microfone()

    def mostrar_pensamento_spotify_erro(self):
        self.controlador_voz_musical.mostrar_pensamento_spotify_erro()

    def iniciar_sequencia_spotify(self):
        self.controlador_voz_musical.iniciar_sequencia_spotify()

    def iniciar_sequencia_spotify_com_violao(self):
        self.controlador_voz_musical.iniciar_sequencia_spotify_com_violao()

    def carregar_cenario_feira(self):
        self.gerenciador_cenarios.carregar_cenario_feira()

    def descarregar_cenario_feira(self):
        self.gerenciador_cenarios.descarregar_cenario_feira()

    def carregar_cenario_principal(self):
        self.gerenciador_cenarios.carregar_cenario_principal()

    def descarregar_cenario_principal(self):
        self.gerenciador_cenarios.descarregar_cenario_principal()

    def on_size(self, *args):
        self.rect.size = (self.width, self.height)

        init_scaling(self.width, self.height, LARGURA, ALTURA)

    def on_pos(self, *args):
        self.rect.pos = self.pos

    def on_touch_down(self, touch):
        pos_virtual = real_to_virtual(touch.pos)

        # Microfone e Comandos Musicais
        if self.controlador_voz_musical.processar_toque_microfone(pos_virtual):
            return True

        # Controles de Movimento do Sapo
        if self.controle_renderer.rect_clique_esquerda.collidepoint(pos_virtual):
            self.controle_renderer.botao_esquerda_pressionado = True
            self.sapo.iniciar_controle_esquerda()
            return True

        if self.controle_renderer.rect_clique_direita.collidepoint(pos_virtual):
            self.controle_renderer.botao_direita_pressionado = True
            self.sapo.iniciar_controle_direita()
            return True

        # Livro e Poeira
        if self.evento_livro.processar_toque(pos_virtual):
            return True

        # Duende
        if self.tem_duende and self.duende.processar_toque_down(pos_virtual):
            return True

        # Violão (Acoplado ou Normal)
        if self.controlador_voz_musical.processar_toque_down_violao(
            pos_virtual, self.renderer_violao
        ):
            return True

        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        pos_virtual = real_to_virtual(touch.pos)

        # Atualizar Arrastes
        if self.violao.arrastando:
            self.violao.mover_arraste(*pos_virtual)

        if self.tem_duende and self.duende.arrastando:
            self.duende.mover_arraste(*pos_virtual)

        # Resetar estados visuais dos botões se sair da área
        if not self.controle_renderer.rect_clique_esquerda.collidepoint(pos_virtual):
            self.controle_renderer.botao_esquerda_pressionado = False

        if not self.controle_renderer.rect_clique_direita.collidepoint(pos_virtual):
            self.controle_renderer.botao_direita_pressionado = False

    def on_touch_up(self, touch):
        # Resetar Controles do Sapo
        self.controle_renderer.botao_esquerda_pressionado = False
        self.controle_renderer.botao_direita_pressionado = False
        self.sapo.parar_controle_esquerda()
        self.sapo.parar_controle_direita()

        # Finalizar Arraste Violão
        if self.controlador_voz_musical.processar_toque_up_violao():
            return True

        # Finalizar Arraste Duende
        if self.tem_duende and self.duende.processar_toque_up(
            self.frasco_climatico.area_interna
        ):
            return True

    def on_key_down(self, window, key, scancode, codepoint, modifiers):
        # seta esquerda
        if key == 276:
            self.tecla_esquerda_pressionada = True
            self.sapo.iniciar_controle_esquerda()

        # seta direita
        if key == 275:
            self.tecla_direita_pressionada = True
            self.sapo.iniciar_controle_direita()

        return True

    def on_key_up(self, window, key, scancode):
        if key == 276:
            self.tecla_esquerda_pressionada = False
            self.sapo.parar_controle_esquerda()

        if key == 275:
            self.tecla_direita_pressionada = False
            self.sapo.parar_controle_direita()

        return True

    def _atualizar_clima(self, dt):
        if self.clima_service.precisa_atualizar():

            def atualizar_clima():
                self.clima_service.atualizar()

            threading.Thread(target=atualizar_clima, daemon=True).start()

        self.clima_service.atualizar_visual(dt)

    def _atualizar_ambiente_fisica(self, dt):
        self.ambiente.atualizar(dt, self.clima_service)

        sistema_fisica.aplicar_forca_vento(
            self.sapo, self.clima_service, dt, sensibilidade=0.25
        )

        if getattr(self.clima_service, "rajada_ativa", False):
            self.animacoes_folha.intensidade_vento = 5.0
        else:
            self.animacoes_folha.intensidade_vento = 1.8

    def update(self, dt):
        dt = min(dt, 0.05)

        self._atualizar_clima(dt)

        events = self.sapo.atualizar(
            dt, self.ambiente, self.animacoes_folha, self.violao
        )
        if events.get("start_audio_passeio"):
            self.audio.tocar_passeio_sapudo()
            event_bus.publicar("musica_iniciada", musica_info="O Passeio do Sapudo")

        texto = events.get("novo_pensamento")
        if texto:
            self.tts.falar(texto)
            event_bus.publicar(PensamentoExibidoEvent(pensamento_texto=texto))

        if self.clima_service.precisa_atualizar():
            event_bus.publicar("clima_atualizado", clima_data=self.clima_service)

        self.spotify.atualizar_spotify(self, dt, self.sapo, self.violao)

        self.controlador_voz_musical.atualizar(dt)
        self._atualizar_ambiente_fisica(dt)
        self.gerenciador_cenarios.atualizar_transicao(dt)

        if self.violao.caindo:
            sistema_fisica.aplicar_forca_vento(
                self.violao, self.clima_service, dt, sensibilidade=0.6
            )

        self.violao.atualizar(dt)
        self.frasco_climatico.atualizar(dt)
        self.evento_livro.atualizar(dt)
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

        self.gerenciador_cenarios.renderizar(dt, ESCALA, self.sapo_renderer)
        self.pensamento_renderer.renderizar(tela, self.sapo, dt)

        if not self.violao.acoplado:
            self.renderer_violao.renderizar(self.violao)

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
