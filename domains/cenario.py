import gc

from config import ALTURA, LARGURA
from constants import CENTRO_OFFSET_Y
from core.fisica import sistema_fisica
from domains.clima.semente import Semente
from domains.duende.entity import DuendeNeblina
from render.asset_manager import asset_manager
from render.barraca_renderer import BarracaRenderer
from render.duende_renderer import DuendeRenderer
from render.semente_renderer import SementeRenderer
from render.tamandua_renderer import TamanduaRenderer


class GerenciadorCenarios:
    """
    Gerencia a troca de cenários e o ciclo de vida dos objetos de cada cenário.
    """

    def __init__(
        self,
        tela,
        transform,
        clima_service,
        background_renderer,
        sistema_nuvens,
        sapo,
        violao,
        frasco_climatico,
        ambiente,
        evento_livro,
        particulas,
    ):
        self.tela = tela
        self.transform = transform
        self.clima_service = clima_service
        self.background_renderer = background_renderer
        self.sistema_nuvens = sistema_nuvens
        self.sapo = sapo
        self.violao = violao
        self.frasco_climatico = frasco_climatico
        self.ambiente = ambiente
        self.evento_livro = evento_livro
        self.particulas = particulas

        self.centro_x = LARGURA // 2
        self.centro_y = ALTURA // 2 + CENTRO_OFFSET_Y

        self.cenario_feira_anterior = False

        # Objetos do cenário principal
        self.duende = None
        self.renderer_duende = None
        self.semente = None
        self.renderer_semente = None

        # Objetos do cenário feira
        self.tamandua_renderer = None
        self.barraca_renderer = None

    @property
    def tem_duende(self):
        return self.duende is not None

    @property
    def tem_feira(self):
        return self.tamandua_renderer is not None

    def carregar_cenario_feira(self):
        self.tamandua_renderer = TamanduaRenderer(self.tela, self.transform)
        self.barraca_renderer = BarracaRenderer(
            self.tela, self.transform, LARGURA, ALTURA
        )

        x_barraca, y_barraca = self.barraca_renderer.obter_posicao()
        self.tamandua_renderer.definir_posicao(x_barraca + 33, y_barraca - 25)

    def descarregar_cenario_feira(self):
        self.tamandua_renderer = None
        self.barraca_renderer = None

    def carregar_cenario_principal(self):
        self.duende = DuendeNeblina()
        self.renderer_duende = DuendeRenderer(self.tela, asset_manager, self.transform)
        self.duende.resgate.violao_monitorado = self.violao
        self.semente = Semente()
        self.renderer_semente = SementeRenderer(
            self.tela, asset_manager, self.transform
        )

    def descarregar_cenario_principal(self):
        self.duende = None
        self.renderer_duende = None
        self.semente = None
        self.renderer_semente = None

    def atualizar_transicao(self, dt):
        """Gerencia a transição entre cenários e atualiza os objetos ativos."""
        if not self.cenario_feira_anterior and self.background_renderer.cenario_feira:
            self.sistema_nuvens.limpar()
            self.descarregar_cenario_principal()
            gc.collect()
            self.carregar_cenario_feira()

        if self.cenario_feira_anterior and not self.background_renderer.cenario_feira:
            self.sistema_nuvens.limpar()
            self.descarregar_cenario_feira()
            gc.collect()
            self.carregar_cenario_principal()

        self.cenario_feira_anterior = self.background_renderer.cenario_feira

        if not self.background_renderer.cenario_feira:
            pote_x = self.centro_x - 260
            pote_y = self.centro_y + 40

            if self.duende:
                self.duende.atualizar(
                    dt,
                    self.sapo,
                    pote_x,
                    pote_y,
                    self.clima_service,
                    self.frasco_climatico.area_interna,
                    self.ambiente,
                )
                sistema_fisica.aplicar_forca_vento(
                    self.duende, self.clima_service, dt, sensibilidade=0.5
                )

            if self.semente:
                self.semente.atualizar(dt, self.clima_service)

            for particula in self.particulas:
                particula.atualizar(self.ambiente, dt)

    def renderizar(self, dt, ESCALA, sapo_renderer):
        """Renderiza os elementos do cenário atual."""
        self.background_renderer.desenhar()

        if self.background_renderer.cenario_feira:
            if self.tamandua_renderer:
                self.tamandua_renderer.atualizar(dt)
                self.tamandua_renderer.renderizar()
            if self.barraca_renderer:
                self.barraca_renderer.renderizar()

        self.sistema_nuvens.renderizar(self.tela, self.background_renderer.eh_dia())
        sapo_renderer.renderizar(self.sapo.x, self.sapo.y, ESCALA, self.sapo.animacoes)

        if not self.background_renderer.cenario_feira:
            self.frasco_climatico.renderizar(self.tela, self.centro_y)

            if not self.evento_livro.livro_visivel:
                for particula in self.particulas:
                    particula.desenhar(self.tela)

                self.frasco_climatico.desenhar_nevoa(self.tela, self.evento_livro.nevoa)

            if self.renderer_duende:
                self.renderer_duende.renderizar(self.duende)
            if self.renderer_semente:
                self.renderer_semente.renderizar(self.semente)

            self.evento_livro.renderizar(self.tela, self.frasco_climatico)
            self.evento_livro.renderizar_livro_aberto(self.tela, self.clima_service)
