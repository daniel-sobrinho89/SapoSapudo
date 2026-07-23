from application.usecases.aldeao.controlar_comportamento_aldeao import (
    ControlarComportamentoAldeaoUseCase,
)
from application.usecases.aldeao.cortar_arvore import CortarArvoreUseCase
from application.usecases.aldeao.obter_carne import ObterCarneUseCase
from application.usecases.aldeao.obter_ouro import ObterOuroUseCase
from config import ALTURA, CENTRO_OFFSET_Y, ESCALA, LARGURA
from core.fisica import sistema_fisica
from domains.aldeao.entity import criar_personagem
from domains.arvore.entity import Arvore
from domains.clima.evento_livro import EventoLivro
from domains.duende.entity import DuendeNeblina
from domains.livro.entity import Livro
from domains.ouro.entity import Ouro
from domains.ovelha.entity import Ovelha
from domains.recursos.entity import Recurso
from render.arvore_render import ArvoreRenderer
from render.asset_manager import asset_manager
from render.barraca_renderer import BarracaRenderer
from render.duende_renderer import DuendeRenderer
from render.menu_casa_renderer import MenuCasaRenderer
from render.menu_construcoes_renderer import MenuConstrucoesRenderer
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

    def renderizar(self, dt):
        raise NotImplementedError


class CenarioPrincipal(CenarioBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.esferas = []
        self.arvores = []
        self.renderers_arvores = []
        self.ouro = []
        self.renderers_ouro = []
        self.recursos = []
        self.renderer_madeira = None
        self.renderer_ouro = None
        self.renderer_carne = None
        self.renderers_recursos = []
        self.ovelhas = []
        self.renderers_ovelhas = []
        self.construcoes = []
        self.personagens = []
        self.controladores = {}
        self.sapo_renderer = None
        self.menu_construcoes = None
        self.menu_casa_renderer = None
        self.duende = None
        self.renderer_duende = None
        self.evento_livro = None
        self.livro = None
        self.carregado = False

        self.construcao_arrastando = None
        self.personagem_arrastando = None

    @property
    def tem_duende(self):
        return self.duende is not None

    @property
    def total_madeira(self):
        return sum(
            1
            for renderer in self.renderers_recursos
            if renderer.nome_recurso == "madeira"
        )

    @property
    def total_ouro(self):
        return sum(
            1 for renderer in self.renderers_recursos if renderer.nome_recurso == "ouro"
        )

    @property
    def total_carne(self):
        return sum(
            1
            for renderer in self.renderers_recursos
            if renderer.nome_recurso == "carne"
        )

    def construcao_desbloqueada(self, construcao):
        return (
            self.total_madeira >= construcao.custo_madeira
            and self.total_ouro >= construcao.custo_ouro
            and self.total_carne >= construcao.custo_carne
        )

    @property
    def possui_castelo(self):
        return any(c.nome == "Castelo" for c in self.construcoes)

    @property
    def tilemap(self):
        return self.background_renderer.tilemap_renderer

    def adicionar_personagem(self, personagem):
        self.personagens.append(personagem)

        self.controladores[personagem] = {
            "ia": ControlarComportamentoAldeaoUseCase(),
            "corte": CortarArvoreUseCase(self),
            "ouro": ObterOuroUseCase(self),
            "carne": ObterCarneUseCase(self),
        }

    def adicionar_recurso(self, x, y, nome_recurso):
        if nome_recurso == "madeira":
            total_frames_recurso = 1
        elif nome_recurso == "ouro":
            total_frames_recurso = 6
        elif nome_recurso == "carne":
            total_frames_recurso = 1

        recurso = Recurso(self.transform, x, y, total_frames_recurso)

        self.recursos.append(recurso)

        if nome_recurso == "madeira":
            self.renderers_recursos.append(self.renderer_madeira)
        elif nome_recurso == "ouro":
            self.renderers_recursos.append(self.renderer_ouro)
        elif nome_recurso == "carne":
            self.renderers_recursos.append(self.renderer_carne)

    def remover_recurso(self, renderer_ouro):
        if renderer_ouro in self.renderers_ouro:
            indice = self.renderers_ouro.index(renderer_ouro)

            self.renderers_ouro.pop(indice)
            self.ouro.pop(indice)

    def carregar(self):
        self.sapo_renderer = SapoRenderer(self.tela, asset_manager, self.transform)
        self.duende = DuendeNeblina()
        self.renderer_duende = DuendeRenderer(self.tela, asset_manager, self.transform)

        self.livro = Livro()
        self.evento_livro = EventoLivro(asset_manager, self.transform, self.livro, [])

        self.adicionar_personagem(criar_personagem("Aldeao"))
        self.menu_construcoes = MenuConstrucoesRenderer(
            self.tela, asset_manager, self.transform
        )
        self.menu_casa_renderer = MenuCasaRenderer(
            self.tela, asset_manager, self.transform
        )

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
        self.renderer_carne = RecursoRenderer(
            self.tela,
            asset_manager,
            self.transform,
            "carne",
            1,
        )

        posicoes = [
            (230, 340),
            (300, 315),
            (370, 355),
            (285, 405),
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
            (145, 510),
            (160, 540),
        ]

        for _indice, (x, y) in enumerate(posicoes, start=1):
            ouro = Ouro(self.transform, x, y)
            renderer = OuroRenderer(self.tela, asset_manager, self.transform)

            self.ouro.append(ouro)
            self.renderers_ouro.append(renderer)

        posicoes = [
            (180, 420),
            (620, 435),
            (350, 455),
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
        self.renderer_madeira = None

    def atualizar(self, dt):
        if self.duende:
            for duende in [self.duende]:
                duende.atualizar(dt)
                sistema_fisica.aplicar_forca_vento(
                    self.duende, self.clima_service, dt, sensibilidade=0.5
                )

        for esfera in self.esferas:
            esfera.atualizar(self.ambiente, dt)

        for construcao in self.construcoes:
            construcao.atualizar(dt)

        for personagem in self.personagens:
            personagem.atualizar(dt)

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

        for construcao in self.construcoes:
            renderer = self.menu_construcoes.obter_renderer(construcao)

            renderer.renderizar(
                construcao,
                construcao.animacoes,
                escala=2.6,
            )

            if construcao.menu_aberto:
                self.menu_casa_renderer.renderizar(construcao, self)

        for personagem in self.personagens:
            renderer = self.menu_casa_renderer.obter_renderer(personagem)

            renderer.renderizar(
                personagem,
                personagem.animacoes,
                escala=1,
            )

            if personagem.menu_construcoes_aberto:
                self.menu_construcoes.renderizar(
                    personagem,
                    self,
                )

        renderizou_madeira = False
        renderizou_ouro = False
        renderizou_carne = False
        for recurso, renderer in zip(self.recursos, self.renderers_recursos):
            if renderer.nome_recurso == "madeira":
                if renderizou_madeira:
                    continue

                renderizou_madeira = True
            elif renderer.nome_recurso == "ouro":
                if renderizou_ouro:
                    continue

                renderizou_ouro = True
            elif renderer.nome_recurso == "carne":
                if renderizou_carne:
                    continue

                renderizou_carne = True

            renderer.renderizar(recurso, recurso.animacoes)

        for ovelha, renderer in zip(self.ovelhas, self.renderers_ovelhas):
            renderer.renderizar(ovelha, ovelha.animacoes)

        for esfera in self.esferas:
            if esfera.saiu_da_casa:
                esfera.desenhar(self.tela)

        if self.renderer_duende:
            self.renderer_duende.renderizar(self.duende, ESCALA)

        self.evento_livro.renderizar(self.tela)
        self.evento_livro.renderizar_livro_aberto(self.tela, self.clima_service)
        self.sapo_renderer.renderizar(self.sapo.x, self.sapo.y, self.sapo.animacoes)

        if self.construcao_arrastando:
            renderer = self.menu_construcoes.obter_renderer(
                self.construcao_arrastando,
            )

            renderer.renderizar(
                self.construcao_arrastando,
                self.construcao_arrastando.animacoes,
                180,
                escala=2.6,
            )

        if self.personagem_arrastando:
            renderer = self.menu_casa_renderer.obter_renderer(
                self.personagem_arrastando,
            )

            renderer.renderizar(
                self.personagem_arrastando,
                self.personagem_arrastando.animacoes,
                180,
                escala=1,
            )

    def _atualizar_carregamento_assets(self):
        if self.carregado:
            return

        self.sapo_renderer.atualizar_carregamento(10)

        if self.renderer_duende:
            self.renderer_duende.atualizar_carregamento(self.duende, 10)

        for renderer in self.renderers_arvores:
            renderer.atualizar_carregamento(5)

        for renderer in self.renderers_ouro:
            renderer.atualizar_carregamento(5)

        for renderer in self.renderers_ovelhas:
            renderer.atualizar_carregamento(5)

        self.renderer_madeira.atualizar_carregamento(1)
        self.renderer_ouro.atualizar_carregamento(5)
        self.renderer_carne.atualizar_carregamento(1)

        self.menu_construcoes.atualizar_carregamento()
        self.menu_casa_renderer.atualizar_carregamento()

        self.carregado = self.sapo_renderer.carregado and self.renderer_duende.carregado


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
        self.background_renderer.desenhar(dt)

        self.cenario_atual.renderizar(dt)

        self.sistema_nuvens.renderizar(
            self.tela,
            self.background_renderer.eh_dia(),
        )

    def adicionar_duende(self, duende):
        self.cenario_principal.adicionar_duende(duende)
