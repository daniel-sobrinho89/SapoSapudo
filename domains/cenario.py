import utils.kivy_adapter as kivy_adapter
from application.fabrica_controladores import FabricaControladores
from application.usecases.duende.controlar_comportamento_duende import (
    ControlarComportamentoDuendeUseCase,
)
from application.usecases.personagem.mover import MoverPersonagemUseCase
from core.camera import Camera
from core.game_config import obter_config, obter_tipos
from core.navegacao_mapa import NavegacaoMapa
from domains.construcao.entity import (  # noqa: F401
    criar_construcao,
)
from domains.duende.entity import DuendeNeblina
from domains.efeitos.entity import criar_efeitos  # noqa: F401
from domains.personagem.entity import (  # noqa: F401
    criar_arvore,
    criar_entidade,
    criar_mina_ouro,
    criar_recurso,
)
from domains.personagem.maquina_estado import EstadoAldeao
from render.asset_manager import asset_manager
from render.background_renderer import CeuRenderer
from render.duende_renderer import DuendeRenderer
from render.menu_contextual_renderer import MenuContextualRenderer
from render.sprite_animado_renderer import SpriteAnimadoRenderer
from render.tilemap_renderer import TileMapRenderer
from utils.config import ALTURA, CENTRO_OFFSET_Y, ESCALA, LARGURA
from utils.kivy_adapter import Rect


class CenarioBase:
    def __init__(
        self,
        tela,
        transform,
        ceu_renderer,
        navegacao,
        mover_personagem,
        tilemap_renderer,
        camera,
        estado,
    ):
        self.tela = tela
        self.transform = transform
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
        self.flora = []
        self.efeitos = []
        self.ovelhas = []
        self.construcoes = []
        self.construcoes_hostis = []
        self.personagens = []
        self.personagens_hostis = []
        self.controladores = {}
        self.menu_contextual = None
        self.duende = None
        self.renderer_duende = None
        self.carregado = False
        self.estoque = {
            "madeira": 0,
            "ouro": 0,
            "carne": 0,
        }
        self.renderers = {}
        self._frames_obstaculos = 0
        self._contagem_construcoes_cache = (-1, -1)

        self.construcao_arrastando = None

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
        return not contrucao_unica and self._possui_recursos(construcao)

    def obter_rect_colisao(self, entidade):
        renderer = self.renderers.get(entidade.nome)
        if renderer is None or not renderer.carregado:
            return Rect(entidade.x - 32, entidade.y - 32, 64, 64)

        config = obter_config(entidade.nome)
        renderer_cfg = config.get("renderer", {})
        escala = renderer_cfg.get("escala", 1.0)
        frame = renderer.obter_frame_animacao(entidade.animacoes)
        if frame is None:
            return Rect(entidade.x - 32, entidade.y - 32, 64, 64)

        escala_x = getattr(entidade, "escala_x", 0.9)
        escala_y = getattr(entidade, "escala_y", 0.9)
        fator_x = renderer.escala * escala * escala_x
        fator_y = renderer.escala * escala * escala_y

        bbox = frame.get_bounding_rect()
        largura = frame.get_width() * fator_x
        altura = frame.get_height() * fator_y

        return Rect(
            entidade.x - largura / 2 + bbox.x * fator_x,
            entidade.y - altura / 2 + bbox.y * fator_y,
            max(1, bbox.w * fator_x),
            max(1, bbox.h * fator_y),
        )

    def obter_obstaculos_construcoes(self):
        obstaculos = []
        for construcao in self.construcoes + self.construcoes_hostis:
            obstaculos.append(self.obter_rect_colisao(construcao))
        return obstaculos

    def posicao_construcao_valida(self, construcao):
        rect = self.obter_rect_colisao(construcao)

        # A validação cobre o contorno e o interior da construção. Assim uma
        # parte da edificação não pode atravessar água, parede ou borda mesmo
        # que o centro esteja sobre grama.
        pontos = {
            (rect.left, rect.top),
            (rect.right - 1, rect.top),
            (rect.left, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1),
            (rect.centerx, rect.centery),
        }

        # Acrescenta uma malha interna para impedir que uma parte da
        # construção atravesse uma área proibida mesmo quando os cantos estão
        # em grama.
        passo = 16
        for x in range(rect.left, rect.right, passo):
            pontos.add((x, rect.centery))
            pontos.add((x, rect.top))
            pontos.add((x, rect.bottom - 1))

        for y in range(rect.top, rect.bottom, passo):
            pontos.add((rect.centerx, y))
            pontos.add((rect.left, y))
            pontos.add((rect.right - 1, y))

        if any(
            not self.tilemap_renderer.pode_andar_pixel(
                x, y, construcao.altura, margem_borda=0
            )
            for x, y in pontos
        ):
            return False

        # Evita sobreposição com qualquer construção já existente.
        for outra in self.construcoes + self.construcoes_hostis:
            if outra is construcao:
                continue
            outra_rect = self.obter_rect_colisao(outra)
            if (
                rect.left < outra_rect.right
                and rect.right > outra_rect.left
                and rect.top < outra_rect.bottom
                and rect.bottom > outra_rect.top
            ):
                return False

        return True

    def obter_posicao_proxima_construcao(self, construcao):
        offsets = (
            (72, 16),
            (-72, 16),
            (72, -48),
            (-72, -48),
            (0, 80),
            (0, -80),
            (96, 0),
            (-96, 0),
        )

        for dx, dy in offsets:
            x = construcao.x + dx
            y = construcao.y + dy
            if self.navegacao.pode_andar(x, y, 0):
                return x, y

        return construcao.x, construcao.y

    def personagem_desbloqueado(self, personagem):
        if personagem.nome == "avatar_aldeao":
            return self._possui_recursos(personagem) and any(
                c.nome == "casa" for c in self.construcoes
            )

        if personagem.nome == "avatar_soldado":
            return self._possui_recursos(personagem) and any(
                c.nome == "quartel" for c in self.construcoes
            )

        return False

    def _possui_recursos(self, entidade):
        return (
            self.total_madeira >= entidade.custo_madeira
            and self.total_ouro >= entidade.custo_ouro
            and self.total_carne >= entidade.custo_carne
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

    def carregar(self):
        self.entidades = []

        for tipo in obter_tipos():
            self.carregar_entidade(tipo)

        self.menu_contextual = MenuContextualRenderer(
            self.tela, asset_manager, self.transform, self
        )

    def carregar_entidade(self, tipo, x=None, y=None):
        config = obter_config(tipo)
        criador = globals()[config["classe"]]
        entidades = []

        if x is None and y is None:
            ambiente = next(
                (
                    item
                    for item in self.tilemap_renderer.ambiente
                    if item.get("tipo") == tipo
                ),
                None,
            )

            spawns = ambiente.get("spawn", []) if ambiente else []
            if not spawns:
                entidade = criador(tipo)
                self._obter_renderer(tipo, config)
                return entidade
        else:
            spawns = [{"x": x, "y": y, "altura": 0}]

        for spawn in spawns:
            entidade = criador(
                tipo,
                x=spawn["x"],
                y=spawn["y"],
                altura=spawn["altura"],
                vida=config.get("vida", 0),
                ataque=config.get("ataque", 0),
                defesa=config.get("defesa", 0),
            )

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

        if not getattr(kivy_adapter, "IS_BROWSER", False):
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
        self._frames_obstaculos += 1
        contagem = (len(self.construcoes), len(self.construcoes_hostis))
        if contagem != self._contagem_construcoes_cache or self._frames_obstaculos >= (
            3 if getattr(kivy_adapter, "IS_BROWSER", False) else 1
        ):
            self.navegacao.atualizar_obstaculos()
            self._contagem_construcoes_cache = contagem
            self._frames_obstaculos = 0

        for item in self.entidades:
            entidade = item["entidade"]

            if not entidade.vida <= 0:
                entidade.atualizar(dt)

        for efeito in self.efeitos[:]:
            efeito.atualizar(dt)

            if (
                not getattr(efeito, "persistente", False)
                and efeito.animacoes.ocioso.progresso >= 1.0
            ):
                self.efeitos.remove(efeito)

    def renderizar(self, dt):
        self._atualizar_carregamento_assets()
        if not self.carregado:
            return
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

        if self.menu_contextual.aberto:
            self.menu_contextual.renderizar(self, self.camera)

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
                (255, 70, 70)
                if getattr(self.construcao_arrastando, "posicionamento_invalido", False)
                else None,
            )

    def progresso_carregamento(self):
        total = 0
        carregado = 0

        for item in self.entidades:
            renderer = item["renderer"]
            fila = getattr(renderer, "_fila", ())
            total += len(fila)
            carregado += min(getattr(renderer, "_indice", 0), len(fila))

        if total <= 0:
            return 1.0 if self.carregado else 0.0
        return max(0.0, min(1.0, carregado / total))

    def _atualizar_carregamento_assets(self):
        if self.carregado:
            return

        renderers = {}
        for item in self.entidades:
            renderer = item["renderer"]
            renderers[id(renderer)] = (renderer, item["frames_carregamento"])

        for renderer, quantidade in renderers.values():
            renderer.atualizar_carregamento(max(1, min(int(quantidade), 2)))

        self.menu_contextual.atualizar_carregamento()

        renderers_principais_prontos = bool(self.entidades) and all(
            renderer.carregado for renderer, _ in renderers.values()
        )

        menu_pronto = self.menu_contextual is not None and all(
            self.menu_contextual._renderers_temporarias[nome].carregado
            for nome in ("castelo", "casa", "quartel")
        )

        self.carregado = renderers_principais_prontos and menu_pronto


class GerenciadorCenarios:
    """
    Gerencia a troca de cenários e o ciclo de vida dos objetos de cada cenário.
    """

    def __init__(
        self,
        tela,
        transform,
    ):
        self.camera = Camera()
        self.tela = tela
        self.transform = transform
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
            self.ceu_renderer,
            self.navegacao,
            self.mover_personagem,
            self.tilemap_renderer,
            self.camera,
            self.estado,
        )

        self.navegacao.definir_obter_obstaculos(
            self.cenario_principal.obter_obstaculos_construcoes
        )

        self.cenario_atual = self.cenario_principal

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
        if not self.duende.movimento_bloqueado and not self.duende.teleporte.ativo:
            self.controlar_comportamento_duende.executar(dt)


class EstadoJogo:
    ABERTURA = 0
    JOGANDO = 1
