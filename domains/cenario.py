from application.usecases.aldeao.controlar_comportamento_aldeao import (
    ControlarComportamentoAldeaoUseCase,
)
from application.usecases.aldeao.controlar_comportamento_goblin_tocha import (
    ControlarComportamentoGoblinTochaUseCase,
)
from application.usecases.aldeao.cortar_arvore import CortarArvoreUseCase
from application.usecases.aldeao.obter_carne import ObterCarneUseCase
from application.usecases.aldeao.obter_ouro import ObterOuroUseCase
from application.usecases.controlar_comportamento_ovelha import (
    ControlarComportamentoOvelhaUseCase,
)
from application.usecases.goblin.atacar import AtacarUseCase as AtacarGoblinUseCase
from application.usecases.soldado.atacar import AtacarUseCase
from application.usecases.soldado.controlar_comportamento_soldado import (
    ControlarComportamentoSoldadoUseCase,
)
from config import ALTURA, CENTRO_OFFSET_Y, ESCALA
from core.camera import Camera
from core.navegacao_mapa import NavegacaoMapa
from domains.arvore.entity import Arvore
from domains.duende.entity import DuendeNeblina
from domains.ouro.entity import Ouro
from domains.ovelha.entity import Ovelha
from domains.personagem.entity import criar_personagem
from domains.recursos.entity import Recurso
from render.asset_manager import asset_manager
from render.duende_renderer import DuendeRenderer
from render.menu_casa_renderer import MenuCasaRenderer
from render.menu_construcoes_renderer import MenuConstrucoesRenderer
from render.sapo_renderer import SapoRenderer
from render.sprite_animado_renderer import SpriteAnimadoRenderer
from render.tilemap_renderer import TileMapRenderer


class CenarioBase:
    def __init__(
        self,
        tela,
        transform,
        clima_service,
        background_renderer,
        navegacao,
        tilemap_renderer,
        sistema_nuvens,
        sapo,
        ambiente,
        camera,
        estado,
    ):
        self.tela = tela
        self.transform = transform
        self.clima_service = clima_service
        self.background_renderer = background_renderer
        self.sistema_nuvens = sistema_nuvens
        self.sapo = sapo
        self.ambiente = ambiente
        self.camera = camera
        self.navegacao = navegacao
        self.tilemap_renderer = tilemap_renderer
        self.estado = estado

    def carregar(self):
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
        self.personagens_hostis = []
        self.controladores = {}
        self.sapo_renderer = None
        self.menu_construcoes = None
        self.menu_casa_renderer = None
        self.duende = None
        self.renderer_duende = None
        self.carregado = False

        self.construcao_arrastando = None
        self.personagem_arrastando = None

    @property
    def tem_duende(self):
        return self.duende is not None

    @property
    def total_madeira(self):
        return sum(
            1 for renderer in self.renderers_recursos if renderer.tipo == "madeira"
        )

    @property
    def total_ouro(self):
        return sum(1 for renderer in self.renderers_recursos if renderer.tipo == "ouro")

    @property
    def total_carne(self):
        return sum(
            1 for renderer in self.renderers_recursos if renderer.tipo == "carne"
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
        return self.tilemap_renderer

    def adicionar_personagem(self, personagem):
        self.personagens.append(personagem)

        if personagem.nome == "Aldeao":
            self.controladores[personagem] = {
                "padrao": ControlarComportamentoAldeaoUseCase(self.navegacao),
                "acoes": {
                    "arvore": {
                        "itens": self.arvores,
                        "usecase": CortarArvoreUseCase(self),
                    },
                    "ouro": {
                        "itens": self.ouro,
                        "usecase": ObterOuroUseCase(self),
                    },
                    "carne": {
                        "itens": self.ovelhas,
                        "usecase": ObterCarneUseCase(self),
                    },
                },
            }
        elif personagem.nome == "Soldado":
            self.controladores[personagem] = {
                "padrao": ControlarComportamentoSoldadoUseCase(self.navegacao),
                "acoes": {
                    "atacar": {
                        "itens": self.personagens_hostis,
                        "usecase": AtacarUseCase(self),
                    },
                },
            }

    def adicionar_personagem_hostil(self, personagem):
        self.personagens_hostis.append(personagem)

        self.controladores[personagem] = {
            "padrao": ControlarComportamentoGoblinTochaUseCase(self.navegacao),
            "acoes": {
                "atacar": {
                    "itens": self.personagens,
                    "usecase": AtacarGoblinUseCase(self),
                },
            },
        }

    def adicionar_animal(self, personagem):
        self.ovelhas.append(personagem)

        self.controladores[personagem] = {
            "padrao": ControlarComportamentoOvelhaUseCase(self.navegacao),
            "acoes": {},
        }

    def adicionar_recurso(self, x, y, nome_recurso):
        recurso = Recurso(self.transform, x, y, nome_recurso)

        self.recursos.append(recurso)

        if nome_recurso == "madeira":
            self.renderers_recursos.append(self.renderer_madeira)
        elif nome_recurso == "ouro":
            self.renderers_recursos.append(self.renderer_ouro)
        elif nome_recurso == "carne":
            self.renderers_recursos.append(self.renderer_carne)

    def remover_recurso(self, ouro):
        if ouro in self.ouro:
            indice = self.ouro.index(ouro)

            self.renderers_ouro.pop(indice)
            self.ouro.pop(indice)

    def personagem_desbloqueado(self, personagem):
        if personagem.nome == "Aldeao":
            return self.construcao_desbloqueada(personagem) and any(
                c.nome == "Casa" for c in self.construcoes
            )

        if personagem.nome == "Soldado":
            return self.construcao_desbloqueada(personagem) and any(
                c.nome == "Quartel" for c in self.construcoes
            )

        return False

    def carregar(self):
        self.sapo_renderer = SapoRenderer(self.tela, asset_manager, self.transform)
        self.duende = DuendeNeblina()
        self.renderer_duende = DuendeRenderer(self.tela, asset_manager, self.transform)

        self.adicionar_personagem(criar_personagem("Aldeao"))
        self.adicionar_personagem_hostil(
            criar_personagem("Goblin_Tocha", x=1200, y=500)
        )
        self.menu_construcoes = MenuConstrucoesRenderer(
            self.tela, asset_manager, self.transform
        )
        self.menu_casa_renderer = MenuCasaRenderer(
            self.tela, asset_manager, self.transform
        )

        self.renderer_madeira = SpriteAnimadoRenderer(
            self.tela,
            asset_manager,
            self.transform,
            "madeira",
            1,
        )
        self.renderer_ouro = SpriteAnimadoRenderer(
            self.tela,
            asset_manager,
            self.transform,
            "ouro",
            1,
        )
        self.renderer_carne = SpriteAnimadoRenderer(
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
            arvore = Arvore(self.transform, x, y, f"arvore{_indice}")
            renderer = SpriteAnimadoRenderer(
                self.tela, asset_manager, self.transform, arvore.nome, 1
            )

            self.arvores.append(arvore)
            self.renderers_arvores.append(renderer)

        posicoes = [
            (145, 510),
            (160, 540),
        ]

        for _indice, (x, y) in enumerate(posicoes, start=1):
            ouro = Ouro(self.transform, x, y, "mina_ouro")
            renderer = SpriteAnimadoRenderer(
                self.tela, asset_manager, self.transform, ouro.nome, 1
            )

            self.ouro.append(ouro)
            self.renderers_ouro.append(renderer)

        posicoes = [
            (180, 420),
            (620, 435),
            (350, 455),
        ]

        for _indice, (x, y) in enumerate(posicoes, start=1):
            ovelha = Ovelha(self.transform, x, y, "ovelha")
            self.adicionar_animal(ovelha)
            renderer = SpriteAnimadoRenderer(
                self.tela, asset_manager, self.transform, ovelha.nome, 1
            )
            self.renderers_ovelhas.append(renderer)

    def atualizar(self, dt):
        if self.duende:
            for duende in [self.duende]:
                duende.atualizar(dt)

        for esfera in self.esferas:
            esfera.atualizar(self.ambiente, dt)

        for construcao in self.construcoes:
            construcao.atualizar(dt)

        for personagem in self.personagens:
            personagem.atualizar(dt)

        for personagem in self.personagens_hostis:
            personagem.atualizar(dt)

        for arvore in self.arvores:
            arvore.atualizar(dt)

        for ouro in self.ouro:
            ouro.atualizar(dt)

        for ovelha in self.ovelhas:
            ovelha.atualizar(dt)

        atualizou_ouro = False
        for recurso, renderer in zip(self.recursos, self.renderers_recursos):
            if renderer.tipo == "ouro":
                if atualizou_ouro:
                    continue

                atualizou_ouro = True
                recurso.atualizar(dt)

    def renderizar(self, dt):
        self._atualizar_carregamento_assets()
        self._renderizar_cenario_principal()

    def _renderizar_cenario_principal(self):
        for arvore, renderer in zip(self.arvores, self.renderers_arvores):
            renderer.renderizar(arvore, arvore.animacoes, self.camera)

        for ouro, renderer in zip(self.ouro, self.renderers_ouro):
            if ouro.mineiro > 0:
                renderer.renderizar(ouro, ouro.animacoes, self.camera)

        for esfera in self.esferas:
            if not esfera.saiu_da_casa:
                esfera.desenhar(self.tela)

        for construcao in self.construcoes:
            renderer = self.menu_construcoes.obter_renderer(construcao)

            renderer.renderizar(
                construcao,
                construcao.animacoes,
                self.camera,
                escala=2.6,
            )

            if construcao.menu_aberto:
                self.menu_casa_renderer.renderizar(construcao, self, self.camera)

        for personagem in self.personagens:
            renderer = self.menu_casa_renderer.obter_renderer(personagem)

            renderer.renderizar(
                personagem,
                personagem.animacoes,
                self.camera,
                escala=1,
            )

            if personagem.menu_construcoes_aberto:
                self.menu_construcoes.renderizar(
                    personagem,
                    self,
                    self.camera,
                )

        for personagem in self.personagens_hostis:
            renderer = self.menu_casa_renderer.obter_renderer(personagem)

            renderer.renderizar(
                personagem,
                personagem.animacoes,
                self.camera,
                escala=1,
            )

        renderizou_madeira = False
        renderizou_ouro = False
        renderizou_carne = False
        for recurso, renderer in zip(self.recursos, self.renderers_recursos):
            if renderer.tipo == "madeira":
                if renderizou_madeira:
                    continue

                renderizou_madeira = True
            elif renderer.tipo == "ouro":
                if renderizou_ouro:
                    continue

                renderizou_ouro = True
            elif renderer.tipo == "carne":
                if renderizou_carne:
                    continue

                renderizou_carne = True

            renderer.renderizar(recurso, recurso.animacoes, self.camera)

        for ovelha, renderer in zip(self.ovelhas, self.renderers_ovelhas):
            renderer.renderizar(ovelha, ovelha.animacoes, self.camera)

        for esfera in self.esferas:
            if esfera.saiu_da_casa:
                esfera.desenhar(self.tela)

        if self.renderer_duende:
            self.renderer_duende.renderizar(self.duende, ESCALA)

        self.sapo_renderer.renderizar(self.sapo.x, self.sapo.y, self.sapo.animacoes)

        if self.construcao_arrastando:
            renderer = self.menu_construcoes.obter_renderer(
                self.construcao_arrastando,
            )

            renderer.renderizar(
                self.construcao_arrastando,
                self.construcao_arrastando.animacoes,
                self.camera,
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
                self.camera,
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
        ambiente,
    ):
        self.camera = Camera()
        self.tela = tela
        self.transform = transform
        self.clima_service = clima_service
        self.background_renderer = background_renderer
        self.sistema_nuvens = sistema_nuvens
        self.sapo = sapo
        self.ambiente = ambiente
        self.centro_y = ALTURA // 2 + CENTRO_OFFSET_Y
        self.estado = EstadoJogo.ABERTURA
        self.tilemap_renderer = TileMapRenderer(
            tela,
            asset_manager,
            transform,
        )
        self.navegacao = NavegacaoMapa(self.tilemap_renderer)

        self.cenario_principal = CenarioPrincipal(
            tela,
            transform,
            clima_service,
            background_renderer,
            self.navegacao,
            self.tilemap_renderer,
            sistema_nuvens,
            sapo,
            ambiente,
            self.camera,
            self.estado,
        )

        self.cenario_atual = self.cenario_principal

    @property
    def tem_duende(self):
        return self.cenario_principal.tem_duende

    def atualizar(self, dt):
        self.cenario_atual.atualizar(dt)

    def renderizar(self, dt):
        self.tela.fill((0, 0, 0, 0))

        if self.estado == EstadoJogo.ABERTURA:
            self.background_renderer.desenhar(dt, self.camera)
        else:
            self.tilemap_renderer.atualizar_carregamento()
            self.tilemap_renderer.renderizar(dt, self.camera)

            self.cenario_atual.renderizar(dt)

            self.sistema_nuvens.renderizar(
                self.tela,
                self.background_renderer.eh_dia(),
            )

    def adicionar_duende(self, duende):
        self.cenario_principal.adicionar_duende(duende)


class EstadoJogo:
    ABERTURA = 0
    JOGANDO = 1
