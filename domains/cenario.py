from application.usecases.aldeao.controlar_comportamento_aldeao import (
    ControlarComportamentoAldeaoUseCase,
)
from application.usecases.aldeao.cortar_arvore import CortarArvoreUseCase
from application.usecases.aldeao.obter_carne import ObterCarneUseCase
from application.usecases.aldeao.obter_ouro import ObterOuroUseCase
from application.usecases.controlar_comportamento_goblin_tocha import (
    ControlarComportamentoGoblinTochaUseCase,
)
from application.usecases.controlar_comportamento_ovelha import (
    ControlarComportamentoOvelhaUseCase,
)
from application.usecases.duende.controlar_comportamento_duende import (
    ControlarComportamentoDuendeUseCase,
)
from application.usecases.duende.controlar_sono_duende import ControlarSonoDuendeUseCase
from application.usecases.goblin.atacar import AtacarUseCase as AtacarGoblinUseCase
from application.usecases.morte_personagem import MortePersonagemUseCase
from application.usecases.soldado.atacar import AtacarUseCase
from application.usecases.soldado.controlar_comportamento_soldado import (
    ControlarComportamentoSoldadoUseCase,
)
from config import ALTURA, CENTRO_OFFSET_Y, ESCALA
from core.camera import Camera
from core.game_config import obter_config
from core.navegacao_mapa import NavegacaoMapa
from domains.arvore.entity import Arvore
from domains.construcao.entity import (
    criar_casa,
    criar_casa_goblin,
    criar_castelo,
    criar_quartel,
)
from domains.duende.entity import DuendeNeblina
from domains.efeitos.entity import criar_efeitos
from domains.ouro.entity import MinaOuro
from domains.ovelha.entity import Ovelha
from domains.personagem.entity import (
    criar_aldeao,
    criar_goblin_tocha,
    criar_personagem,
    criar_soldado,
)
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


CRIADORES = {
    "criar_aldeao": criar_aldeao,
    "criar_soldado": criar_soldado,
}


class CenarioPrincipal(CenarioBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.arvores = []
        self.renderers_arvores = []
        self.minas_ouro = []
        self.renderers_minas_ouro = []
        self.recursos = []
        self.efeitos = []
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
        self.estoque = {
            "madeira": 0,
            "ouro": 0,
            "carne": 0,
        }

        self.construcao_arrastando = None
        self.personagem_arrastando = None

    @property
    def tem_duende(self):
        return self.duende is not None

    @property
    def total_madeira(self):
        return self.estoque["madeira"]

    @property
    def total_ouro(self):
        return self.estoque["ouro"]

    @property
    def total_carne(self):
        return self.estoque["carne"]

    def construcao_desbloqueada(self, construcao):
        contrucao_unica = self._contrucao_unica(construcao.nome)
        return (
            not contrucao_unica
            and self.total_madeira >= construcao.custo_madeira
            and self.total_ouro >= construcao.custo_ouro
            and self.total_carne >= construcao.custo_carne
        )

    def _contrucao_unica(self, nome):
        if nome == "castelo":
            return any(c.nome == "castelo" for c in self.construcoes)

    @property
    def tilemap(self):
        return self.tilemap_renderer

    def adicionar_personagem(self, personagem):
        self.personagens.append(personagem)

        if personagem.nome == "aldeao":
            self.controladores[personagem] = {
                "padrao": ControlarComportamentoAldeaoUseCase(self.navegacao),
                "morte": MortePersonagemUseCase(self),
                "acoes": {
                    "arvore": {
                        "itens": self.arvores,
                        "usecase": CortarArvoreUseCase(self),
                    },
                    "ouro": {
                        "itens": self.minas_ouro,
                        "usecase": ObterOuroUseCase(self),
                    },
                    "carne": {
                        "itens": self.ovelhas,
                        "usecase": ObterCarneUseCase(self),
                    },
                },
            }
        elif personagem.nome == "soldado":
            self.controladores[personagem] = {
                "padrao": ControlarComportamentoSoldadoUseCase(self.navegacao),
                "morte": MortePersonagemUseCase(self),
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
            "morte": MortePersonagemUseCase(self),
            "acoes": {
                "atacar": {
                    "itens": self.personagens,
                    "usecase": AtacarGoblinUseCase(self),
                },
            },
        }

    def adicionar_animal(self, personagem):
        self.controladores[personagem] = {
            "padrao": ControlarComportamentoOvelhaUseCase(self.navegacao),
            "morte": MortePersonagemUseCase(self),
            "acoes": {},
        }

    def adicionar_construcao(self, entidade):
        self.construcoes.append(entidade)

    def adicionar_recurso(self, x, y, nome_recurso):
        recurso = Recurso(self.transform, x, y, nome_recurso)

        self.recursos.append(recurso)

        if nome_recurso == "madeira":
            self.renderers_recursos.append(self.renderer_madeira)
        elif nome_recurso == "ouro":
            self.renderers_recursos.append(self.renderer_ouro)
        elif nome_recurso == "carne":
            self.renderers_recursos.append(self.renderer_carne)

    def remover_recurso(self, minas_ouro):
        if minas_ouro in self.minas_ouro:
            indice = self.minas_ouro.index(minas_ouro)

            self.renderers_minas_ouro.pop(indice)
            self.minas_ouro.pop(indice)

    def adicionar_estoque(self, tipo, quantidade=1):
        self.estoque[tipo] += quantidade

    def remover_estoque(self, tipo, quantidade=1):
        self.estoque[tipo] = max(
            0,
            self.estoque[tipo] - quantidade,
        )

    def adicionar_efeito(self, efeito):
        self.efeitos.append(efeito)

    def remover_personagem(self, personagem):
        if personagem in self.personagens:
            self.personagens.remove(personagem)
        elif personagem in self.personagens_hostis:
            self.personagens_hostis.remove(personagem)
        elif personagem in self.ovelhas:
            self.ovelhas.remove(personagem)
        elif personagem in self.efeitos:
            self.efeitos.remove(personagem)
        else:
            return

        self.controladores.pop(personagem, None)

        for ctrl in self.controladores.values():
            for acao in ctrl["acoes"].values():
                usecase = acao["usecase"]

                if usecase.entidade_alvo is personagem:
                    usecase.entidade_alvo = None

    def personagem_desbloqueado(self, personagem):
        if personagem.nome == "avatar_aldeao":
            return self.construcao_desbloqueada(personagem) and any(
                c.nome == "casa" for c in self.construcoes
            )

        if personagem.nome == "avatar_soldado":
            return self.construcao_desbloqueada(personagem) and any(
                c.nome == "quartel" for c in self.construcoes
            )

        return False

    def carregar(self):
        self.sapo_renderer = SapoRenderer(self.tela, asset_manager, self.transform)

        # self.adicionar_personagem(criar_personagem("aldeao"))
        self.adicionar_personagem_hostil(
            criar_personagem("goblin_Tocha", x=1200, y=220)
        )

        recurso_madeira = Recurso(self.transform, 0, 0, "madeira")
        self.renderer_madeira = SpriteAnimadoRenderer(
            self.tela,
            asset_manager,
            self.transform,
            "madeira",
            1,
        )
        recurso_ouro = Recurso(self.transform, 0, 0, "ouro")
        self.renderer_ouro = SpriteAnimadoRenderer(
            self.tela,
            asset_manager,
            self.transform,
            "ouro",
            1,
        )
        recurso_carne = Recurso(self.transform, 0, 0, "carne")
        self.renderer_carne = SpriteAnimadoRenderer(
            self.tela,
            asset_manager,
            self.transform,
            "carne",
            1,
        )

        self.castelo = criar_castelo()
        self.renderer_castelo = SpriteAnimadoRenderer(
            self.tela, asset_manager, self.transform, self.castelo.nome, 0.25
        )
        self.casa = criar_casa()
        self.renderer_casa = SpriteAnimadoRenderer(
            self.tela, asset_manager, self.transform, self.casa.nome, 0.25
        )
        self.casa_goblin = criar_casa_goblin(x=1250, y=150)
        self.renderer_casa_goblin = SpriteAnimadoRenderer(
            self.tela, asset_manager, self.transform, self.casa_goblin.nome, 0.25
        )
        self.adicionar_construcao(self.casa_goblin)

        self.quartel = criar_quartel()
        self.renderer_quartel = SpriteAnimadoRenderer(
            self.tela, asset_manager, self.transform, self.quartel.nome, 0.25
        )

        self.goblin_tocha = criar_goblin_tocha()
        self.renderer_goblin_tocha = SpriteAnimadoRenderer(
            self.tela, asset_manager, self.transform, self.goblin_tocha.nome, 1.0
        )

        self.poeira_grande = criar_efeitos("poeira_grande")
        self.renderer_poeira_grande = SpriteAnimadoRenderer(
            self.tela, asset_manager, self.transform, self.poeira_grande.nome, 1.0
        )
        self.barra_vida = criar_efeitos("barra_vida")
        self.renderer_barra_vida = SpriteAnimadoRenderer(
            self.tela, asset_manager, self.transform, self.barra_vida.nome, 1.0
        )
        self.barra_vida_base = criar_efeitos("barra_vida_base")
        self.renderer_barra_vida_base = SpriteAnimadoRenderer(
            self.tela, asset_manager, self.transform, self.barra_vida_base.nome, 1.0
        )
        self.avatar_aldeao = criar_efeitos("avatar_aldeao")
        self.renderer_avatar_aldeao = SpriteAnimadoRenderer(
            self.tela, asset_manager, self.transform, self.avatar_aldeao.nome, 0.3
        )
        self.avatar_soldado = criar_efeitos("avatar_soldado")
        self.renderer_avatar_soldado = SpriteAnimadoRenderer(
            self.tela, asset_manager, self.transform, self.avatar_soldado.nome, 0.3
        )

        self.entidades = [
            {
                "entidade": self.castelo,
                "renderer": self.renderer_castelo,
                "frames_carregamento": 1,
            },
            {
                "entidade": self.casa,
                "renderer": self.renderer_casa,
                "frames_carregamento": 1,
            },
            {
                "entidade": self.casa_goblin,
                "renderer": self.renderer_casa_goblin,
                "frames_carregamento": 16,
            },
            {
                "entidade": self.quartel,
                "renderer": self.renderer_quartel,
                "frames_carregamento": 1,
            },
            {
                "entidade": self.goblin_tocha,
                "renderer": self.renderer_goblin_tocha,
                "frames_carregamento": 5,
            },
            {
                "entidade": self.barra_vida_base,
                "renderer": self.renderer_barra_vida_base,
                "frames_carregamento": 1,
            },
            {
                "entidade": self.barra_vida_base,
                "renderer": self.renderer_barra_vida_base,
                "frames_carregamento": 1,
            },
            {
                "entidade": self.poeira_grande,
                "renderer": self.renderer_poeira_grande,
                "frames_carregamento": 5,
            },
            {
                "entidade": recurso_madeira,
                "renderer": self.renderer_madeira,
                "frames_carregamento": 1,
            },
            {
                "entidade": recurso_ouro,
                "renderer": self.renderer_ouro,
                "frames_carregamento": 5,
            },
            {
                "entidade": recurso_carne,
                "renderer": self.renderer_carne,
                "frames_carregamento": 1,
            },
            {
                "entidade": self.avatar_aldeao,
                "renderer": self.renderer_avatar_aldeao,
                "frames_carregamento": 1,
            },
            {
                "entidade": self.avatar_soldado,
                "renderer": self.renderer_avatar_soldado,
                "frames_carregamento": 1,
            },
        ]

        self.carregar_entidade("aldeao")
        self.carregar_entidade("soldado")

        for nome, x, y in [
            ("arvore1", 230, 340),
            ("arvore2", 300, 315),
            ("arvore3", 370, 355),
            ("arvore4", 285, 405),
        ]:
            arvore = Arvore(self.transform, x, y, nome)

            renderer = self.obter_renderer_por_tipo(nome)
            if renderer is None:
                renderer = SpriteAnimadoRenderer(
                    self.tela,
                    asset_manager,
                    self.transform,
                    nome,
                    1,
                )

            self.registrar_entidade(
                arvore,
                renderer,
                frames_carregamento=5,
                lista=self.arvores,
                lista_renderers=self.renderers_arvores,
            )

        for x, y in [
            (180, 420),
            (620, 435),
            (350, 455),
        ]:
            ovelha = Ovelha(
                self.transform,
                x,
                y,
                "ovelha",
            )

            self.adicionar_animal(ovelha)

            renderer = self.obter_renderer_por_tipo("ovelha")
            if renderer is None:
                renderer = SpriteAnimadoRenderer(
                    self.tela,
                    asset_manager,
                    self.transform,
                    "ovelha",
                    1,
                )

            self.registrar_entidade(
                ovelha,
                renderer,
                frames_carregamento=5,
                lista=self.ovelhas,
                lista_renderers=self.renderers_ovelhas,
            )

        for x, y in [
            (145, 510),
            (160, 540),
        ]:
            mina = MinaOuro(
                self.transform,
                x,
                y,
                "mina_ouro",
            )

            renderer = self.obter_renderer_por_tipo("mina_ouro")
            if renderer is None:
                renderer = SpriteAnimadoRenderer(
                    self.tela,
                    asset_manager,
                    self.transform,
                    "mina_ouro",
                    1,
                )

            self.registrar_entidade(
                mina,
                renderer,
                frames_carregamento=5,
                lista=self.minas_ouro,
                lista_renderers=self.renderers_minas_ouro,
            )

        self.menu_construcoes = MenuConstrucoesRenderer(
            self.tela, asset_manager, self.transform, self
        )
        self.menu_casa_renderer = MenuCasaRenderer(
            self.tela, asset_manager, self.transform, self
        )

    def carregar_entidade(self, tipo, x=None, y=None):
        config = obter_config(tipo)
        criador = CRIADORES[config["classe"]]

        if x is None:
            spawns = config["spawn"]
        else:
            spawns = [{"x": x, "y": y}]

        for spawn in spawns:
            entidade = criador(
                x=spawn["x"],
                y=spawn["y"],
            )

            renderer = self.obter_renderer_por_tipo(tipo)
            if renderer is None:
                renderer = SpriteAnimadoRenderer(
                    self.tela,
                    asset_manager,
                    self.transform,
                    tipo,
                    config["renderer"]["escala"],
                )

                while not renderer.carregado:
                    renderer.atualizar_carregamento(
                        config["renderer"]["frames_carregamento"]
                    )

            self.registrar_entidade(
                entidade,
                renderer,
                frames_carregamento=config["renderer"]["frames_carregamento"],
            )

            if x is None:
                grupo = config["grupo"]
                if grupo == "personagens":
                    self.adicionar_personagem(entidade)
                elif grupo == "hostis":
                    self.adicionar_personagem_hostil(entidade)
                elif grupo == "ovelhas":
                    self.adicionar_animal(entidade)
            else:
                self.personagem_arrastando = entidade

    def registrar_entidade(
        self,
        entidade,
        renderer,
        frames_carregamento,
        lista=None,
        lista_renderers=None,
    ):
        if lista is not None:
            lista.append(entidade)

        if lista_renderers is not None:
            lista_renderers.append(renderer)

        self.entidades.append(
            {
                "entidade": entidade,
                "renderer": renderer,
                "frames_carregamento": frames_carregamento,
            }
        )

    def atualizar(self, dt):
        for item in self.entidades:
            entidade = item["entidade"]
            if not entidade.vida <= 0:
                entidade.atualizar(dt)

        for personagem in self.personagens_hostis:
            if not personagem.vida <= 0:
                personagem.atualizar(dt)

        for efeito in self.efeitos:
            efeito.atualizar(dt)

            if (
                efeito.nome == "poeira_grande"
                and efeito.animacoes.ocioso.progresso >= 1.0
            ):
                self.remover_personagem(efeito)

        atualizou_ouro = False
        for recurso, renderer in zip(self.recursos, self.renderers_recursos):
            if renderer.tipo == "ouro":
                if atualizou_ouro:
                    continue

                atualizou_ouro = True
                recurso.atualizar(dt)

    def renderizar(self, dt):
        self._atualizar_carregamento_assets()
        self._renderizar_cenario_principal(dt)

    def _renderizar_cenario_principal(self, dt):
        self.tilemap_renderer.renderizar(dt, self.camera)

        for arvore, renderer in zip(self.arvores, self.renderers_arvores):
            renderer.renderizar(arvore, arvore.animacoes, self.camera)

        for minas_ouro, renderer in zip(self.minas_ouro, self.renderers_minas_ouro):
            if minas_ouro.minerio > 0:
                renderer.renderizar(minas_ouro, minas_ouro.animacoes, self.camera)

        for construcao in self.construcoes:
            renderer = self.obter_renderer(construcao)

            renderer.renderizar(
                construcao,
                construcao.animacoes,
                self.camera,
                escala=2.6,
            )

        for personagem in self.personagens:
            renderer = self.obter_renderer(personagem)

            renderer.renderizar(
                personagem,
                personagem.animacoes,
                self.camera,
                escala=1,
            )

        for personagem in self.personagens_hostis:
            renderer = self.obter_renderer(personagem)

            renderer.renderizar(
                personagem,
                personagem.animacoes,
                self.camera,
                escala=1,
            )

        for efeito in self.efeitos:
            renderer = self.obter_renderer(efeito)

            renderer.renderizar(
                efeito,
                efeito.animacoes,
                self.camera,
                escala=1,
            )

        for recurso, renderer in zip(self.recursos, self.renderers_recursos):
            renderer.renderizar(recurso, recurso.animacoes, self.camera)

        for ovelha, renderer in zip(self.ovelhas, self.renderers_ovelhas):
            renderer.renderizar(ovelha, ovelha.animacoes, self.camera)

        self.sapo_renderer.renderizar(self.sapo.x, self.sapo.y, self.sapo.animacoes)

        if self.menu_casa_renderer.aberto:
            self.menu_casa_renderer.renderizar(self, self.camera)

        if self.menu_construcoes.aberto:
            self.menu_construcoes.renderizar(
                self,
                self.camera,
            )

        if self.construcao_arrastando:
            renderer = self.obter_renderer(
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
            renderer = self.obter_renderer(
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

        for entidade in self.entidades:
            entidade["renderer"].atualizar_carregamento(
                entidade["frames_carregamento"],
            )

        self.menu_construcoes.atualizar_carregamento()
        self.menu_casa_renderer.atualizar_carregamento()

        self.carregado = self.sapo_renderer.carregado and all(
            entidade["renderer"].carregado for entidade in self.entidades
        )

    def obter_renderer(self, entidade):
        for opcao in self.entidades:
            if opcao["entidade"].nome == entidade.nome:
                return opcao["renderer"]

    def obter_renderer_por_tipo(self, tipo):
        for item in self.entidades:
            if item["entidade"].nome == tipo:
                return item["renderer"]

        return None


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

            if not hasattr(self, "duende"):
                self.duende = DuendeNeblina()
                self.renderer_duende = DuendeRenderer(
                    self.tela, asset_manager, self.transform
                )

                self.controlar_sono_duende = ControlarSonoDuendeUseCase(
                    self.sapo,
                    self.duende,
                    self.clima_service,
                )
                self.controlar_comportamento_duende = (
                    ControlarComportamentoDuendeUseCase(self.duende, self.sapo)
                )

            self.duende.atualizar(dt)
            self.renderer_duende.atualizar_carregamento(self.duende, 10)
            self.renderer_duende.renderizar(self.duende, ESCALA)
            if self.renderer_duende.carregado:
                self._executar_fluxo_duende(dt)
        else:
            self.tilemap_renderer.atualizar_carregamento()

            self.cenario_atual.renderizar(dt)

            self.sistema_nuvens.renderizar(
                self.tela,
                self.background_renderer.eh_dia(),
            )

    def _executar_fluxo_duende(self, dt):
        # TODO! Ajustar para verificar se duende existe

        if (
            not self.clima_service.clima_disponivel
            or not self.duende
            or self.duende.animacoes.dormindo
            or self.duende.animacoes.acordando
        ):
            self.controlar_sono_duende.executar(dt)
        elif not self.duende.movimento_bloqueado and not self.duende.teleporte.ativo:
            self.controlar_comportamento_duende.executar(dt)


class EstadoJogo:
    ABERTURA = 0
    JOGANDO = 1
