from config import ALTURA, CENTRO_OFFSET_Y, ESCALA, LARGURA, QUANTIDADE_POEIRA
from core.fisica import sistema_fisica
from domains.aldeao.entity import Aldeao
from domains.arvore.entity import Arvore
from domains.casa_duende.entity import CasaDuende
from domains.clima.evento_livro import EventoLivro
from domains.clima.particulas.esfera import Esfera
from domains.duende.entity import DuendeNeblina
from domains.livro.entity import Livro
from domains.ouro.entity import Ouro
from domains.ovelha.entity import Ovelha
from domains.recursos.entity import Recurso
from render.aldeao_renderer import AldeaoRenderer
from render.arvore_render import ArvoreRenderer
from render.asset_manager import asset_manager
from render.barraca_renderer import BarracaRenderer
from render.casa_duende_renderer import CasaDuendeRenderer
from render.duende_renderer import DuendeRenderer
from render.ouro_rendery import OuroRenderer
from render.ovelha_render import OvelhaRenderer
from render.recurso_render import RecursoRenderer
from render.sapo_renderer import SapoRenderer
from render.tamandua_renderer import TamanduaRenderer


class CenarioBase:
    def __init__(
        self,
        tela,
        transform,
        clima_service,
        background_renderer,
        sistema_nuvens,
        sapo,
        violao,
        ambiente,
    ):
        self.tela = tela
        self.transform = transform
        self.clima_service = clima_service
        self.background_renderer = background_renderer
        self.sistema_nuvens = sistema_nuvens
        self.sapo = sapo
        self.violao = violao
        self.ambiente = ambiente

    def carregar(self):
        raise NotImplementedError

    def descarregar(self):
        raise NotImplementedError

    def atualizar(self, dt):
        raise NotImplementedError

    def renderizar(self, dt, sapo_renderer):
        raise NotImplementedError


class CenarioPrincipal(CenarioBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.duendes = []
        self.esferas = []
        self.arvores = []
        self.renderers_arvores = []
        self.ouro = []
        self.renderers_ouro = []
        self.recursos = []
        self.renderer_madeira = None
        self.renderer_ouro = None
        self.renderers_recursos = []
        self.ovelhas = []
        self.renderers_ovelhas = []

        self.sapo_renderer = None
        self.aldeao = None
        self.renderer_aldeao = None
        self.duende = None
        self.renderer_duende = None
        self.casa_duende = None
        self.casa_duende_renderer = None
        self.evento_livro = None
        self.livro = None
        self.carregado = False

    @property
    def tem_duende(self):
        return self.duende is not None

    def adicionar_recurso(self, x, y, nome_recurso):
        if nome_recurso == "madeira":
            total_frames_recurso = 1
        elif nome_recurso == "ouro":
            total_frames_recurso = 6

        recurso = Recurso(self.transform, x, y, total_frames_recurso)

        self.recursos.append(recurso)

        if nome_recurso == "madeira":
            self.renderers_recursos.append(self.renderer_madeira)
        elif nome_recurso == "ouro":
            self.renderers_recursos.append(self.renderer_ouro)

    def remover_recurso(self, renderer_ouro):
        if renderer_ouro in self.renderers_ouro:
            indice = self.renderers_ouro.index(renderer_ouro)

            self.renderers_ouro.pop(indice)
            self.ouro.pop(indice)

    def carregar(self):
        self.sapo_renderer = SapoRenderer(self.tela, asset_manager, self.transform)
        self.duende = DuendeNeblina()
        self.renderer_duende = DuendeRenderer(self.tela, asset_manager, self.transform)
        self.casa_duende = CasaDuende(self.transform)
        self.casa_duende_renderer = CasaDuendeRenderer(
            self.tela, asset_manager, self.transform
        )

        self.livro = Livro()
        self.evento_livro = EventoLivro(asset_manager, self.transform, self.livro, [])

        self.aldeao = Aldeao(self.transform)
        self.renderer_aldeao = AldeaoRenderer(self.tela, asset_manager, self.transform)

        self.renderer_madeira = RecursoRenderer(
            self.tela,
            asset_manager,
            self.transform,
            "madeira",
            1,
        )
        self.renderer_ouro = RecursoRenderer(
            self.tela,
            asset_manager,
            self.transform,
            "ouro",
            6,
        )

        posicoes = [
            (180, 240),
            (250, 215),
            (320, 255),
            (235, 305),
        ]

        for _indice, (x, y) in enumerate(posicoes, start=1):
            arvore = Arvore(self.transform, x, y)
            renderer = ArvoreRenderer(
                self.tela,
                asset_manager,
                self.transform,
                _indice,
            )

            self.arvores.append(arvore)
            self.renderers_arvores.append(renderer)

        posicoes = [
            (105, 400),
            (120, 440),
        ]

        for _indice, (x, y) in enumerate(posicoes, start=1):
            ouro = Ouro(self.transform, x, y)
            renderer = OuroRenderer(self.tela, asset_manager, self.transform)

            self.ouro.append(ouro)
            self.renderers_ouro.append(renderer)

        posicoes = [
            (180, 420),
            (350, 455),
            (620, 435),
        ]

        for _indice, (x, y) in enumerate(posicoes, start=1):
            ovelha = Ovelha(self.transform, x, y)
            renderer = OvelhaRenderer(
                self.tela,
                asset_manager,
                self.transform,
            )

            self.ovelhas.append(ovelha)
            self.renderers_ovelhas.append(renderer)

    def descarregar(self):
        self.duende = None
        self.renderer_duende = None
        self.casa_duende = None
        self.casa_duende_renderer = None
        self.aldeao = None
        self.renderer_aldeao = None
        self.renderer_madeira = None

    def atualizar(self, dt):
        if self.casa_duende:
            self.casa_duende.atualizar(dt)

        if self.duende:
            for duende in [self.duende] + self.duendes:
                duende.atualizar(dt)
                sistema_fisica.aplicar_forca_vento(
                    self.duende, self.clima_service, dt, sensibilidade=0.5
                )

        for esfera in self.esferas:
            esfera.atualizar(self.ambiente, dt)

        if self.aldeao:
            self.aldeao.atualizar(dt)

        for arvore in self.arvores:
            arvore.atualizar(dt)

        for ouro in self.ouro:
            ouro.atualizar(dt)

        for ovelha in self.ovelhas:
            ovelha.atualizar(dt)

        atualizou_ouro = False
        for recurso, renderer in zip(self.recursos, self.renderers_recursos):
            if renderer.nome_recurso == "ouro":
                if atualizou_ouro:
                    continue

                atualizou_ouro = True
                recurso.atualizar(dt)

    def renderizar(self, dt):
        self._atualizar_carregamento_assets()
        self._renderizar_cenario_principal()

    def _renderizar_cenario_principal(self):
        for arvore, renderer in zip(self.arvores, self.renderers_arvores):
            renderer.renderizar(arvore, arvore.animacoes)

        for ouro, renderer in zip(self.ouro, self.renderers_ouro):
            if ouro.mineiro > 0:
                renderer.renderizar(ouro, ouro.animacoes)

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

        for ovelha, renderer in zip(self.ovelhas, self.renderers_ovelhas):
            renderer.renderizar(ovelha, ovelha.animacoes)

        renderizou_madeira = False
        renderizou_ouro = False
        for recurso, renderer in zip(self.recursos, self.renderers_recursos):
            if renderer.nome_recurso == "madeira":
                if renderizou_madeira:
                    continue

                renderizou_madeira = True
            elif renderer.nome_recurso == "ouro":
                if renderizou_ouro:
                    continue

                renderizou_ouro = True

            renderer.renderizar(recurso, recurso.animacoes)

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

        self.renderer_aldeao.renderizar(self.aldeao, self.aldeao.animacoes)
        self.evento_livro.renderizar(self.tela, self.casa_duende)
        self.evento_livro.renderizar_livro_aberto(self.tela, self.clima_service)

        self.sapo_renderer.renderizar(self.sapo.x, self.sapo.y, self.sapo.animacoes)

    def _atualizar_carregamento_assets(self):
        if self.carregado:
            return

        self.sapo_renderer.atualizar_carregamento(10)

        if self.renderer_duende:
            self.renderer_duende.atualizar_carregamento(self.duende, 10)

        self.casa_duende_renderer.atualizar_carregamento(self.casa_duende, 10)

        for renderer in self.renderers_arvores:
            renderer.atualizar_carregamento(5)

        for renderer in self.renderers_ouro:
            renderer.atualizar_carregamento(5)

        for renderer in self.renderers_ovelhas:
            renderer.atualizar_carregamento(5)

        self.renderer_madeira.atualizar_carregamento(1)
        self.renderer_ouro.atualizar_carregamento(5)

        self.renderer_aldeao.atualizar_carregamento(5)

        self.carregado = (
            self.sapo_renderer.carregado
            and self.renderer_duende.carregado
            and self.casa_duende_renderer.carregado
        )
        if self.carregado:
            self.esferas = [
                Esfera(
                    self.casa_duende.area_particulas,
                    self.casa_duende.area_casa,
                    asset_manager,
                )
                for _ in range(QUANTIDADE_POEIRA)
            ]
            self.evento_livro.esferas = self.esferas
            for esfera in self.esferas:
                esfera.area_protegida = self.casa_duende.area_casa
                esfera.protegido = esfera.area_protegida.collidepoint(
                    int(esfera.x), int(esfera.y)
                )

    def adicionar_duende(self, duende):
        if len(self.duendes) < 1:
            self.duendes.append(duende)


class CenarioFeira(CenarioBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tamandua_renderer = None
        self.barraca_renderer = None

    @property
    def tem_feira(self):
        return self.tamandua_renderer is not None

    def carregar(self):
        self.tamandua_renderer = TamanduaRenderer(self.tela, self.transform)
        self.barraca_renderer = BarracaRenderer(
            self.tela, self.transform, LARGURA, ALTURA
        )

        x_barraca, y_barraca = self.barraca_renderer.obter_posicao()
        self.tamandua_renderer.definir_posicao(x_barraca + 33, y_barraca - 25)

    def descarregar(self):
        self.tamandua_renderer = None
        self.barraca_renderer = None

    def atualizar(self, dt):
        return None

    def renderizar(self, dt):
        if self.tamandua_renderer:
            self.tamandua_renderer.atualizar(dt)
            self.tamandua_renderer.renderizar()
        if self.barraca_renderer:
            self.barraca_renderer.renderizar()


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
        ambiente,
    ):
        self.tela = tela
        self.transform = transform
        self.clima_service = clima_service
        self.background_renderer = background_renderer
        self.sistema_nuvens = sistema_nuvens
        self.sapo = sapo
        self.violao = violao
        self.ambiente = ambiente
        self.centro_y = ALTURA // 2 + CENTRO_OFFSET_Y
        self.cenario_feira_anterior = False

        self.cenario_principal = CenarioPrincipal(
            tela,
            transform,
            clima_service,
            background_renderer,
            sistema_nuvens,
            sapo,
            violao,
            ambiente,
        )

        self.cenario_feira = CenarioFeira(
            tela,
            transform,
            clima_service,
            background_renderer,
            sistema_nuvens,
            sapo,
            violao,
            ambiente,
        )

        self.cenario_atual = self.cenario_principal

    @property
    def tem_duende(self):
        return self.cenario_principal.tem_duende

    @property
    def tem_feira(self):
        return self.cenario_feira.tem_feira

    @property
    def em_feira(self):
        return self.cenario_atual is self.cenario_feira

    def trocar_cenario(self, novo_cenario):
        if self.cenario_atual is novo_cenario:
            return

        self.sistema_nuvens.limpar()
        self.cenario_atual.descarregar()
        self.cenario_atual = novo_cenario
        self.cenario_atual.carregar()

    def atualizar(self, dt):
        if not self.cenario_feira_anterior and self.background_renderer.cenario_feira:
            self.trocar_cenario(self.cenario_feira)

        elif self.cenario_feira_anterior and not self.background_renderer.cenario_feira:
            self.trocar_cenario(self.cenario_principal)

        self.cenario_feira_anterior = self.background_renderer.cenario_feira

        self.cenario_atual.atualizar(dt)

    def renderizar(self, dt):
        self.tela.fill((0, 0, 0, 0))
        self.background_renderer.desenhar()

        self.cenario_atual.renderizar(dt)

        self.sistema_nuvens.renderizar(
            self.tela,
            self.background_renderer.eh_dia(),
        )

    def adicionar_duende(self, duende):
        self.cenario_principal.adicionar_duende(duende)
