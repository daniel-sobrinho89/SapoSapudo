from config import ALTURA, CENTRO_OFFSET_Y, ESCALA, LARGURA, QUANTIDADE_POEIRA
from core.fisica import sistema_fisica
from domains.clima.evento_livro import EventoLivro
from domains.clima.particulas.esfera import Esfera
from domains.duende.entity import DuendeNeblina
from domains.livro.entity import Livro
from domains.semente.entity import Semente
from render.asset_manager import asset_manager
from render.barraca_renderer import BarracaRenderer
from render.casa_duende_renderer import CasaDuendeRenderer
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
        casa_duende,
        ambiente,
    ):
        self.tela = tela
        self.transform = transform
        self.clima_service = clima_service
        self.background_renderer = background_renderer
        self.sistema_nuvens = sistema_nuvens
        self.sapo = sapo
        self.violao = violao
        self.casa_duende = casa_duende
        self.ambiente = ambiente
        self.duendes = []
        self.esferas = []

        self.centro_y = ALTURA // 2 + CENTRO_OFFSET_Y
        self.cenario_feira_anterior = False

        # Objetos do cenário principal
        self.duende = None
        self.renderer_duende = None
        self.casa_duende_renderer = None
        self.semente = None
        self.renderer_semente = None
        self.evento_livro = None
        self.livro = None
        self.cenario_principal_carregado = False

        # Objetos do cenário feira
        self.tamandua_renderer = None
        self.barraca_renderer = None

    @property
    def tem_duende(self):
        return self.duende is not None

    @property
    def tem_feira(self):
        return self.tamandua_renderer is not None

    @property
    def em_feira(self):
        return self.background_renderer.cenario_feira

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
        self.semente = Semente()
        self.renderer_semente = SementeRenderer(
            self.tela, asset_manager, self.transform
        )
        self.casa_duende_renderer = CasaDuendeRenderer(
            self.tela, asset_manager, self.transform
        )
        self.livro = Livro()

        self.evento_livro = EventoLivro(asset_manager, self.transform, self.livro, [])

    def descarregar_cenario_principal(self):
        self.duende = None
        self.renderer_duende = None
        self.casa_duende_renderer = None
        self.semente = None
        self.renderer_semente = None

    def atualizar(self, dt):
        if not self.cenario_feira_anterior and self.background_renderer.cenario_feira:
            self.sistema_nuvens.limpar()
            self.descarregar_cenario_principal()
            self.carregar_cenario_feira()

        if self.cenario_feira_anterior and not self.background_renderer.cenario_feira:
            self.sistema_nuvens.limpar()
            self.descarregar_cenario_feira()
            self.carregar_cenario_principal()

        self.cenario_feira_anterior = self.background_renderer.cenario_feira

        if not self.background_renderer.cenario_feira:
            if self.duende:
                for duende in [self.duende] + self.duendes:
                    duende.atualizar(dt)
                    sistema_fisica.aplicar_forca_vento(
                        self.duende, self.clima_service, dt, sensibilidade=0.5
                    )

            if self.semente:
                self.semente.atualizar(dt, self.clima_service)

            for esfera in self.esferas:
                esfera.atualizar(self.ambiente, dt)

    def renderizar(self, dt, sapo_renderer):
        """Renderiza os elementos do cenário atual."""
        self.tela.fill((0, 0, 0, 0))
        self.background_renderer.desenhar()
        self._atualizar_carregamento_assets(sapo_renderer)

        if self.em_feira:
            if self.tamandua_renderer:
                self.tamandua_renderer.atualizar(dt)
                self.tamandua_renderer.renderizar()
            if self.barraca_renderer:
                self.barraca_renderer.renderizar()
        else:
            self._atualizar_cenario_principal()

        self.sistema_nuvens.renderizar(self.tela, self.background_renderer.eh_dia())
        sapo_renderer.renderizar(self.sapo.x, self.sapo.y, ESCALA, self.sapo.animacoes)

    def _atualizar_cenario_principal(self):
        for esfera in self.esferas:
            if not esfera.saiu_da_casa:
                esfera.desenhar(self.tela)

        if (
            self.renderer_duende
            and self.duende.animacoes.atras_da_casa
            and self.duende.percentual_visivel <= 0.15
        ):
            self.renderer_duende.renderizar(self.duende, ESCALA)

        if self.duende.animacoes.saindo_da_casa:
            for duende in self.duendes:
                self.renderer_duende.renderizar(duende, ESCALA)

        hora_atual = self.ambiente.obter_hora_decimal()
        if (
            hora_atual >= 18.5 or hora_atual < 6
        ) and not self.casa_duende.animacoes.luz_esta_acesa:
            self.casa_duende.animacoes.iniciar_luz_acesa()

        self.casa_duende_renderer.renderizar(
            self.casa_duende,
            self.casa_duende.animacoes,
        )

        for esfera in self.esferas:
            if esfera.saiu_da_casa:
                esfera.desenhar(self.tela)

        self.casa_duende.desenhar_nevoa(self.tela, self.evento_livro.nevoa)

        if self.renderer_duende:
            if (
                self.duende.percentual_visivel > 0.15
                or not self.duende.animacoes.atras_da_casa
            ):
                self.renderer_duende.renderizar(self.duende, ESCALA)

            if not self.duende.animacoes.saindo_da_casa:
                for duende in self.duendes:
                    self.renderer_duende.renderizar(duende, ESCALA)

        if self.renderer_semente:
            self.renderer_semente.renderizar(self.semente)

        self.evento_livro.renderizar(self.tela, self.casa_duende)
        self.evento_livro.renderizar_livro_aberto(self.tela, self.clima_service)

    def _atualizar_carregamento_assets(self, sapo_renderer):
        if self.cenario_principal_carregado:
            return

        sapo_renderer.atualizar_carregamento(10)

        if self.renderer_duende:
            self.renderer_duende.atualizar_carregamento(self.duende, 10)

        self.casa_duende_renderer.atualizar_carregamento(self.casa_duende, 10)
        self.cenario_principal_carregado = (
            sapo_renderer.carregado
            and self.renderer_duende.carregado
            and self.casa_duende_renderer.carregado
        )
        if self.cenario_principal_carregado:
            self.esferas = [
                Esfera(
                    self.casa_duende.area_particulas,
                    self.casa_duende.area_casa,
                    asset_manager,
                )
                for _ in range(QUANTIDADE_POEIRA)
            ]
            self.evento_livro.esferas = self.esferas
            for e in self.esferas:
                e.area_protegida = self.casa_duende.area_casa
                e.protegido = e.area_protegida.collidepoint(int(e.x), int(e.y))

    def adicionar_duende(self, duende):
        self.duendes.append(duende)
