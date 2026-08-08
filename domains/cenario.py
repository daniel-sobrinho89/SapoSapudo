from application.fabrica_controladores import FabricaControladores
from application.usecases.duende.controlar_comportamento_duende import (
    ControlarComportamentoDuendeUseCase,
)
from application.usecases.duende.controlar_sono_duende import ControlarSonoDuendeUseCase
from application.usecases.mover_personagem import MoverPersonagemUseCase
from core.camera import Camera
from core.game_config import obter_config, obter_tipos
from core.navegacao_mapa import NavegacaoMapa
from domains.construcao.entity import (  # noqa: F401
    criar_casa,
    criar_casa_goblin,
    criar_castelo,
    criar_quartel,
)
from domains.duende.entity import DuendeNeblina
from domains.efeitos.entity import criar_efeitos  # noqa: F401
from domains.personagem.entity import (  # noqa: F401
    criar_aldeao,
    criar_arvore,
    criar_goblin_tocha,
    criar_mina_ouro,
    criar_ovelha,
    criar_recurso,
    criar_soldado,
)
from domains.personagem.maquina_estado import EstadoAldeao
from render.asset_manager import asset_manager
from render.background_renderer import CeuRenderer
from render.duende_renderer import DuendeRenderer
from render.menu_casa_renderer import MenuCasaRenderer
from render.menu_construcoes_renderer import MenuConstrucoesRenderer
from render.sprite_animado_renderer import SpriteAnimadoRenderer
from render.tilemap_renderer import TileMapRenderer
from utils.config import ALTURA, CENTRO_OFFSET_Y, ESCALA, LARGURA


class CenarioBase:
    def __init__(
        self,
        tela,
        transform,
        clima_service,
        ceu_renderer,
        navegacao,
        mover_personagem,
        tilemap_renderer,
        camera,
        estado,
    ):
        self.tela = tela
        self.transform = transform
        self.clima_service = clima_service
        self.ceu_renderer = ceu_renderer
        self.camera = camera
        self.navegacao = navegacao
        self.mover_personagem = mover_personagem
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
        self.arvores = []
        self.minas_ouro = []
        self.recursos = []
        self.efeitos = []
        self.ovelhas = []
        self.construcoes = []
        self.construcoes_hostis = []
        self.personagens = []
        self.personagens_hostis = []
        self.controladores = {}
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
        self.renderers = {}

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

    def adicionar_personagem(self, entidade, nome_lista):
        lista = getattr(self, nome_lista)
        lista.append(entidade)

        controlador = FabricaControladores.criar(
            entidade,
            self,
        )

        if controlador:
            self.controladores[entidade] = controlador

    def adicionar_estoque(self, tipo, quantidade=1):
        self.estoque[tipo] += quantidade

    def remover_estoque(self, tipo, quantidade=1):
        self.estoque[tipo] = max(
            0,
            self.estoque[tipo] - quantidade,
        )

    def adicionar_efeito(self, efeito):
        self.efeitos.append(efeito)

    def reservar_recurso(self, tipo, coletor):
        for recurso in self.recursos:
            if recurso.nome == tipo and recurso.reservado_por is None:
                recurso.reservado_por = coletor
                return recurso

        return None

    def reservar_drop(self, recurso, coletor):
        if recurso not in self.recursos or recurso.reservado_por is not None:
            return False

        recurso.reservado_por = coletor
        return True

    def coletar_recurso(self, recurso, coletor):
        if recurso.reservado_por is not coletor or recurso not in self.recursos:
            return False

        self.remover_personagem(recurso, ignorar=coletor)
        return True

    def remover_personagem(self, entidade, ignorar=None):
        config = obter_config(entidade.nome)
        colecao = config["renderer"]["colecao"]
        lista = getattr(self, colecao)

        if entidade not in lista:
            return

        lista.remove(entidade)
        self.entidades = [
            item for item in self.entidades if item["entidade"] is not entidade
        ]

        self.controladores.pop(entidade, None)

        for ctrl in self.controladores.values():
            for acao in ctrl["acoes"].values():
                usecase = acao["usecase"]

                if getattr(usecase, "entidade_alvo", None) is entidade:
                    if getattr(usecase, "personagem", None) is ignorar:
                        continue

                    usecase.entidade_alvo = None

                    if usecase.flip:
                        usecase.personagem.animacoes.estado = EstadoAldeao.OCIOSO_FLIP
                    else:
                        usecase.personagem.animacoes.estado = EstadoAldeao.OCIOSO

    def parar_acao_global(self, entidade, ignorar=None):
        self.controladores.pop(entidade, None)

        for ctrl in self.controladores.values():
            for acao in ctrl["acoes"].values():
                usecase = acao["usecase"]

                if getattr(usecase, "entidade_alvo", None) is entidade:
                    if usecase.personagem is ignorar:
                        continue

                    usecase.entidade_alvo = None

                    if usecase.flip:
                        usecase.personagem.animacoes.estado = EstadoAldeao.OCIOSO_FLIP
                    else:
                        usecase.personagem.animacoes.estado = EstadoAldeao.OCIOSO

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
        self.entidades = []

        for tipo in obter_tipos():
            self.carregar_entidade(tipo)

        self.menu_construcoes = MenuConstrucoesRenderer(
            self.tela, asset_manager, self.transform, self
        )
        self.menu_casa_renderer = MenuCasaRenderer(
            self.tela, asset_manager, self.transform, self
        )

    def carregar_entidade(self, tipo, x=None, y=None):
        config = obter_config(tipo)
        criador = globals()[config["classe"]]
        entidades = []
        spawns = config["spawn"]

        if x is None and not spawns:
            entidade = criador(tipo)
            renderer = self._obter_renderer(tipo, config)

            return entidade

        spawns = spawns or [{"x": x, "y": y, "altura": 0}]

        for spawn in spawns:
            entidade = criador(tipo, x=spawn["x"], y=spawn["y"], altura=spawn["altura"])

            renderer = self._obter_renderer(tipo, config)

            grupo = config["grupo"]
            faccao = config.get("faccao", None)
            self.registrar_entidade(
                entidade,
                renderer,
                grupo,
                faccao,
                frames_carregamento=config["renderer"]["frames_carregamento"],
            )

            colecao = config["renderer"]["colecao"]
            if grupo != "efeitos":
                self.adicionar_personagem(entidade, colecao)

            entidades.append(entidade)

        if x is None:
            return entidades
        else:
            return entidades[0]

    def carregar_entidade_temporaria(self, tipo):
        config = obter_config(tipo)
        criador = globals()[config["classe"]]

        entidade = criador(tipo)
        self._obter_renderer(tipo, config)

        return entidade

    def _obter_renderer(self, tipo, config):
        renderer = self.renderers.get(tipo)

        if renderer:
            return renderer

        renderer = SpriteAnimadoRenderer(
            self.tela,
            asset_manager,
            self.transform,
            tipo,
            config["renderer"]["escala"],
        )

        while not renderer.carregado:
            renderer.atualizar_carregamento(
                config["renderer"]["frames_carregamento"],
            )

        self.renderers[tipo] = renderer

        return renderer

    def registrar_entidade(
        self,
        entidade,
        renderer,
        grupo,
        faccao,
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
                "grupo": grupo,
                "faccao": faccao,
                "frames_carregamento": frames_carregamento,
            }
        )

    def obter_entidade(self, entidade):
        return next(
            (item for item in self.entidades if item["entidade"] is entidade),
            None,
        )

    def atualizar(self, dt):
        for item in self.entidades:
            entidade = item["entidade"]

            if not entidade.vida <= 0:
                entidade.atualizar(dt)

        for efeito in self.efeitos:
            efeito.atualizar(dt)

            if (
                efeito.nome == "poeira_grande"
                and efeito.animacoes.ocioso.progresso >= 1.0
            ):
                self.remover_personagem(efeito)

    def renderizar(self, dt):
        self._atualizar_carregamento_assets()
        self._renderizar_cenario_principal(dt)

    def _renderizar_cenario_principal(self, dt):
        self.tilemap_renderer.renderizar(dt, self.camera)

        itens_render = []

        for tipo in obter_tipos():
            config = obter_config(tipo)

            renderer_cfg = config.get("renderer", {})
            colecao = renderer_cfg.get("colecao")

            if not colecao:
                continue

            renderer = self.renderers[tipo]

            for entidade in getattr(self, colecao):
                if entidade.nome != tipo:
                    continue

                itens_render.append(
                    {
                        "y": getattr(entidade, "base_pe_y", entidade.y),
                        "renderer": renderer,
                        "entidade": entidade,
                        "escala": renderer_cfg.get("escala"),
                    }
                )

        itens_render.sort(key=lambda item: item["y"])

        for item in itens_render:
            item["renderer"].renderizar(
                item["entidade"],
                item["entidade"].animacoes,
                self.camera,
                escala=item["escala"],
            )

            entidade = item["entidade"]
            if getattr(entidade, "tempo_barra_vida", 0.0) > 0:
                self.renderers["barra_vida_base"].renderizar_barra_vida(
                    entidade,
                    self.camera,
                    entidade.vida / entidade.VIDA_MAXIMA,
                    self.renderers["barra_vida"],
                )

        for efeito in self.efeitos:
            renderer = self.renderers[efeito.nome]

            renderer.renderizar(
                efeito,
                efeito.animacoes,
                self.camera,
            )

        if self.menu_casa_renderer.aberto:
            self.menu_casa_renderer.renderizar(self, self.camera)

        if self.menu_construcoes.aberto:
            self.menu_construcoes.renderizar(
                self,
                self.camera,
            )

        if self.construcao_arrastando:
            renderer = self.renderers[self.construcao_arrastando.nome]

            config = obter_config(self.construcao_arrastando.nome)
            renderer_cfg = config.get("renderer", {})
            escala = renderer_cfg.get("escala")

            renderer.renderizar(
                self.construcao_arrastando,
                self.construcao_arrastando.animacoes,
                self.camera,
                180,
                escala,
            )

        if self.personagem_arrastando:
            renderer = self.renderers[self.personagem_arrastando.nome]

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

        for entidade in self.entidades:
            entidade["renderer"].atualizar_carregamento(
                entidade["frames_carregamento"],
            )

        self.menu_construcoes.atualizar_carregamento()
        self.menu_casa_renderer.atualizar_carregamento()

        self.carregado = all(
            entidade["renderer"].carregado for entidade in self.entidades
        )


class GerenciadorCenarios:
    """
    Gerencia a troca de cenários e o ciclo de vida dos objetos de cada cenário.
    """

    def __init__(
        self,
        tela,
        transform,
        clima_service,
    ):
        self.camera = Camera()
        self.tela = tela
        self.transform = transform
        self.clima_service = clima_service
        self.ceu_renderer = CeuRenderer(tela, LARGURA, ALTURA)
        self.centro_y = ALTURA // 2 + CENTRO_OFFSET_Y
        self.estado = EstadoJogo.ABERTURA
        self.tilemap_renderer = TileMapRenderer(
            tela,
            asset_manager,
            transform,
        )
        self.navegacao = NavegacaoMapa(self.tilemap_renderer)
        self.mover_personagem = MoverPersonagemUseCase()

        self.cenario_principal = CenarioPrincipal(
            tela,
            transform,
            clima_service,
            self.ceu_renderer,
            self.navegacao,
            self.mover_personagem,
            self.tilemap_renderer,
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
            self.ceu_renderer.desenhar()

            if not hasattr(self, "duende"):
                self.duende = DuendeNeblina()
                self.renderer_duende = DuendeRenderer(
                    self.tela, asset_manager, self.transform
                )

                self.controlar_sono_duende = ControlarSonoDuendeUseCase(
                    self.duende,
                    self.clima_service,
                )
                self.controlar_comportamento_duende = (
                    ControlarComportamentoDuendeUseCase(self.duende)
                )

            self.duende.atualizar(dt)
            self.renderer_duende.atualizar_carregamento(self.duende, 10)
            self.renderer_duende.renderizar(self.duende, ESCALA)
            if self.renderer_duende.carregado:
                self._executar_fluxo_duende(dt)
        else:
            self.tilemap_renderer.atualizar_carregamento()

            self.cenario_atual.renderizar(dt)

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
