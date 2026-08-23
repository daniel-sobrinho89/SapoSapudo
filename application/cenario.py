from contextlib import suppress

import utils.kivy_adapter as kivy_adapter
from application.fabrica_controladores import FabricaControladores
from application.usecases.duende.controlar_comportamento_duende import (
    ControlarComportamentoDuendeUseCase,
)
from application.usecases.personagem.mover import MoverPersonagemUseCase
from core.audio_manager import AudioManager
from core.camera import Camera
from core.game_config import obter_config, obter_tipos
from core.indice_espacial import IndiceEspacial
from core.navegacao_mapa import NavegacaoMapa
from core.performance_metrics import PerformanceMetrics
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
        self._registro_entidades = {}
        self.indice_espacial = IndiceEspacial(128)
        self.metricas_desempenho = PerformanceMetrics(habilitado=False)
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
        self._renderers_auxiliares = {}
        # Registros de renderização pré-calculados. Evitam reconstruir uma
        # lista por tipo e fazer milhares de chamadas a obter_config() a cada
        # frame, algo particularmente caro no WebAssembly.
        self._render_registros = []
        self._carregamento_pendente = True

        self._tipos_render = tuple(
            tipo
            for tipo in obter_tipos()
            if obter_config(tipo).get("renderer", {}).get("colecao")
            and obter_config(tipo).get("grupo") != "efeitos"
        )

        self.construcao_arrastando = None
        self.primeiro_frame_renderizado = False
        self.audio_manager = AudioManager()
        self.audio_hud_rect = None
        self.audio_hud_imagem = None

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
        nome = construcao.nome.removeprefix("avatar_")
        if self._contrucao_unica(nome):
            return False

        if nome == "casa":
            if sum(c.nome == "casa" for c in self.construcoes) >= 3:
                return False
        elif (
            nome == "quartel"
            and sum(c.nome == "quartel" for c in self.construcoes) >= 1
        ):
            return False

        return self._possui_recursos(construcao)

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
        arrastando = self.construcao_arrastando

        for construcao in self.construcoes + self.construcoes_hostis:
            # A construção arrastada é apenas um preview e ainda não bloqueia
            # a navegação do cenário.
            if construcao is arrastando:
                continue

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
            casas = sum(c.nome == "casa" for c in self.construcoes)
            limite_aldeoes = min(3, casas) * 2
            if limite_aldeoes <= 0:
                return False
            if sum(1 for p in self.personagens if p.nome == "aldeao") >= limite_aldeoes:
                return False
            return self._possui_recursos(personagem)

        if personagem.nome == "avatar_soldado":
            quartels = sum(c.nome == "quartel" for c in self.construcoes)
            limite_soldados = min(1, quartels) * 3
            if limite_soldados <= 0:
                return False
            if (
                sum(1 for p in self.personagens if p.nome == "soldado")
                >= limite_soldados
            ):
                return False
            return self._possui_recursos(personagem)

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
        self._registrar_no_indice(entidade)

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

    def liberar_reserva_recurso(self, recurso, coletor):
        if recurso is None:
            return False

        if getattr(recurso, "reservado_por", None) is not coletor:
            return False

        recurso.reservado_por = None
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

        registro = self._registro_entidades.get(entidade)
        grupo_entidade = registro.get("grupo") if registro is not None else None

        lista.remove(entidade)
        self._registro_entidades.pop(entidade, None)
        self.entidades = [
            item for item in self.entidades if item["entidade"] is not entidade
        ]
        self._render_registros = [
            item for item in self._render_registros if item["entidade"] is not entidade
        ]

        self._remover_do_indice(entidade)
        for atacante in list(getattr(entidade, "atacantes_ativos", ())):
            ctrl_atacante = self.controladores.get(atacante)
            if ctrl_atacante is not None:
                atacar = ctrl_atacante.get("acoes", {}).get("atacar")
                if atacar is not None:
                    usecase = atacar.get("usecase")
                    if (
                        usecase is not None
                        and getattr(usecase, "entidade_alvo", None) is entidade
                    ):
                        usecase.entidade_alvo = None
            self.remover_atacante(entidade, atacante)

        for possivel_alvo in list(self._registro_entidades):
            self.remover_atacante(possivel_alvo, entidade)

        self.controladores.pop(entidade, None)

        if grupo_entidade == "construcoes":
            self.notificar_obstaculos_alterados()

        for ctrl in self.controladores.values():
            for acao in ctrl["acoes"].values():
                usecase = acao["usecase"]

                if getattr(usecase, "entidade_alvo", None) is entidade:
                    if getattr(usecase, "personagem", None) is ignorar:
                        continue

                    cancelar = getattr(usecase, "cancelar", None)
                    if cancelar is not None:
                        cancelar()
                    else:
                        usecase.entidade_alvo = None

                    if getattr(usecase, "personagem", None) is not None:
                        if usecase.flip:
                            usecase.personagem.animacoes.estado = (
                                EstadoAldeao.OCIOSO_FLIP
                            )
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

                    # Cortadores de árvore fazem a própria transição para outra
                    # árvore disponível. Não cancele outro aldeão que ainda
                    # esteja levando madeira para o depósito ou chegando ao
                    # ponto da árvore, pois ele precisa concluir sua ação e
                    # procurar a próxima árvore a partir do último ponto de corte.
                    if usecase.__class__.__name__ == "CortarArvoreUseCase":
                        continue

                    usecase.entidade_alvo = None

                    if usecase.flip:
                        usecase.personagem.animacoes.estado = EstadoAldeao.OCIOSO_FLIP
                    else:
                        usecase.personagem.animacoes.estado = EstadoAldeao.OCIOSO

    def carregar(self):
        self.iniciar_carregamento()
        while self._tipos_carregamento_restantes:
            self.processar_carregamento(max_tipos=1)

        while not self.carregado:
            self._atualizar_carregamento_assets()

    def iniciar_carregamento(self):
        if getattr(self, "_carregamento_iniciado", False):
            return

        self.entidades = []
        self.renderers = {}
        self._tipos_carregamento_restantes = list(obter_tipos())
        self._carregamento_iniciado = True
        self._menu_criado = False
        self._renderers_auxiliares = {}
        self.carregado = False

        # Recursos iniciais são definidos pelo mapa. O estoque é reiniciado
        # aqui para que cada novo cenário comece exatamente com os valores
        # configurados em mapa1.json.
        recursos_iniciais = getattr(self.tilemap_renderer, "recursos_iniciais", {})
        self.estoque = {
            "madeira": int(recursos_iniciais.get("madeira", 0)),
            "ouro": int(recursos_iniciais.get("ouro", 0)),
            "carne": int(recursos_iniciais.get("carne", 0)),
        }

    def processar_carregamento(self, max_tipos=1):
        if not getattr(self, "_carregamento_iniciado", False):
            self.iniciar_carregamento()

        for _ in range(max(1, int(max_tipos))):
            if not self._tipos_carregamento_restantes:
                break

            tipo = self._tipos_carregamento_restantes.pop(0)
            self.carregar_entidade(tipo)

        if not self._menu_criado and not self._tipos_carregamento_restantes:
            self.menu_contextual = MenuContextualRenderer(
                self.tela, asset_manager, self.transform, self
            )
            self._renderers_auxiliares = {}
            for nome in ("barra_vida_base", "barra_vida"):
                self.carregar_entidade_temporaria(nome)
                self._renderers_auxiliares[nome] = self.renderers[nome]
            self._menu_criado = True

        if not self._tipos_carregamento_restantes:
            self._atualizar_carregamento_assets()

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
                renderer = self._obter_renderer(tipo, config)
                if config.get("grupo") == "efeitos":
                    self._renderers_auxiliares[tipo] = renderer
                return entidade
        else:
            spawns = [{"x": x, "y": y, "altura": 0}]

        for spawn in spawns:
            argumentos = {
                "x": spawn["x"],
                "y": spawn["y"],
                "altura": spawn["altura"],
                "vida": config.get("vida", 0),
                "ataque": config.get("ataque", 0),
                "defesa": config.get("defesa", 0),
            }

            # Custos econômicos são dados de configuração do tipo de entidade.
            # Apenas personagens e construções os recebem, pois recursos, árvores
            # e efeitos possuem factories com contratos diferentes.
            custo = config.get("custo", {})
            if config.get("classe") in ("criar_entidade", "criar_construcao"):
                argumentos.update(
                    madeira=custo.get("madeira", 0),
                    ouro=custo.get("ouro", 0),
                    carne=custo.get("carne", 0),
                )

            entidade = criador(tipo, **argumentos)

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
            if entidades:
                renderer = self.renderers.get(tipo)
                if renderer is not None and not renderer.carregado:
                    # Spawn interativo: o personagem/recurso precisa estar
                    # completamente disponível já no próximo frame.
                    quantidade = max(1, len(getattr(renderer, "_fila", ())))
                    renderer.atualizar_carregamento(quantidade)
            return entidades[0]

    def carregar_entidade_temporaria(self, tipo):
        config = obter_config(tipo)
        criador = globals()[config["classe"]]

        argumentos = {}
        custo = config.get("custo", {})
        if config.get("classe") in ("criar_entidade", "criar_construcao"):
            argumentos.update(
                madeira=custo.get("madeira", 0),
                ouro=custo.get("ouro", 0),
                carne=custo.get("carne", 0),
            )

        entidade = criador(tipo, **argumentos)
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

        if config.get("grupo") == "efeitos" and getattr(
            kivy_adapter, "IS_BROWSER", False
        ):
            self._renderers_auxiliares[tipo] = renderer

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

        registro = {
            "entidade": entidade,
            "renderer": renderer,
            "grupo": grupo,
            "faccao": faccao,
            "frames_carregamento": frames_carregamento,
        }
        self.entidades.append(registro)
        self._registro_entidades[entidade] = registro

        if grupo in (
            "personagens",
            "hostis",
            "construcoes",
            "recursos",
            "arvores",
            "minas_ouro",
        ):
            self.indice_espacial.registrar(entidade, grupo)

        if grupo != "efeitos":
            config = obter_config(entidade.nome)
            renderer_cfg = config.get("renderer", {})
            self._render_registros.append(
                {
                    "entidade": entidade,
                    "renderer": renderer,
                    "escala": renderer_cfg.get("escala", 1.0) or 1.0,
                    "grupo": grupo,
                }
            )

        if not renderer.carregado:
            self._carregamento_pendente = True

    def obter_entidade(self, entidade):
        # Consulta O(1). Mantemos a busca antiga eliminada para que IA e
        # combate não reconstruam listas apenas para descobrir metadados.
        return self._registro_entidades.get(entidade)

    def _registrar_no_indice(self, entidade, grupo=None):
        if grupo is None:
            registro = self._registro_entidades.get(entidade)
            grupo = registro.get("grupo") if registro else None
        if grupo in (
            "personagens",
            "hostis",
            "construcoes",
            "recursos",
            "arvores",
            "minas_ouro",
        ):
            self.indice_espacial.registrar(entidade, grupo)

    def _remover_do_indice(self, entidade):
        self.indice_espacial.remover(entidade)

    def registrar_atacante(self, alvo, atacante):
        if alvo is None or atacante is None:
            return
        atacantes = getattr(alvo, "atacantes_ativos", None)
        if atacantes is None:
            atacantes = set()
            alvo.atacantes_ativos = atacantes
        atacantes.add(atacante)

    def remover_atacante(self, alvo, atacante):
        atacantes = getattr(alvo, "atacantes_ativos", None)
        if atacantes is None:
            return
        atacantes.discard(atacante)
        if not atacantes:
            with suppress(Exception):
                delattr(alvo, "atacantes_ativos")

    def notificar_obstaculos_alterados(self):
        """Atualiza os obstáculos imediatamente e invalida a versão de rotas."""
        self._frames_obstaculos = 0
        self._contagem_construcoes_cache = (
            len(self.construcoes),
            len(self.construcoes_hostis),
        )
        self.navegacao.notificar_obstaculos_alterados()
        self.mover_personagem.notificar_obstaculos_alterados(self.navegacao)

    def atualizar(self, dt):
        self.metricas_desempenho.iniciar_frame()

        for item in self.entidades:
            entidade = item["entidade"]

            if not entidade.vida <= 0:
                entidade.atualizar(dt)
                grupo = item.get("grupo")
                # Árvores, minas, recursos e construções colocadas não mudam
                # de célula. Só entidades móveis precisam atualizar o bucket
                # espacial a cada frame. O preview de construção é excluído.
                if (
                    grupo in ("personagens", "hostis", "ovelhas")
                    and entidade is not self.construcao_arrastando
                ):
                    self.indice_espacial.atualizar(entidade)

        # Obstáculos dinâmicos mudam por eventos de construção/destruição.
        # A sincronização periódica fica apenas como rede de segurança para
        # cenários legados ou alterações externas.
        self._frames_obstaculos += 1
        if self._frames_obstaculos >= (
            60 if getattr(kivy_adapter, "IS_BROWSER", False) else 30
        ):
            alteracoes = self.navegacao.atualizar_obstaculos()
            if alteracoes:
                self.mover_personagem.notificar_obstaculos_alterados(self.navegacao)
            self._frames_obstaculos = 0

        for efeito in self.efeitos[:]:
            efeito.atualizar(dt)

            if (
                not getattr(efeito, "persistente", False)
                and efeito.animacoes.ocioso.progresso >= 1.0
            ):
                self.efeitos.remove(efeito)

    def renderizar(self, dt):
        if self._carregamento_pendente:
            self._atualizar_carregamento_assets()
        if not self.carregado:
            return
        self._renderizar_cenario_principal(dt)

    def _renderizar_cenario_principal(self, dt):
        self.tilemap_renderer.renderizar(dt, self.camera)

        # Primeiro faz culling por câmera e só depois ordena. Em mapas com
        # muitas unidades, a lista de renderização passa a conter apenas o
        # que pode realmente aparecer na tela.
        itens_render = []
        for item in self._render_registros:
            entidade = item["entidade"]
            renderer = item["renderer"]
            if not renderer.carregado:
                continue

            escala = item["escala"]
            largura = max(1.0, float(getattr(renderer, "largura", 64)) * float(escala))
            altura = max(1.0, float(getattr(renderer, "altura", 64)) * float(escala))
            if not self.camera.visivel(entidade.x, entidade.y, largura, altura):
                continue

            itens_render.append(
                (
                    getattr(entidade, "base_pe_y", entidade.y),
                    renderer,
                    entidade,
                    escala,
                    item["grupo"],
                )
            )

        itens_render.sort(key=lambda item: item[0])

        personagens_renderizados_neste_frame = 0

        for _, renderer, entidade, escala, grupo_entidade in itens_render:
            renderer.renderizar(
                entidade,
                entidade.animacoes,
                self.camera,
                escala=escala,
            )

            eh_personagem = grupo_entidade in ("personagens", "hostis")

            if (
                eh_personagem
                and getattr(entidade, "render_rect", None) is not None
                and getattr(item["renderer"], "carregado", False)
            ):
                personagens_renderizados_neste_frame += 1

            if getattr(entidade, "tempo_barra_vida", 0.0) > 0:
                self.renderers["barra_vida_base"].renderizar_barra_vida(
                    entidade,
                    self.camera,
                    entidade.vida / entidade.VIDA_MAXIMA,
                    self.renderers["barra_vida"],
                )

        if personagens_renderizados_neste_frame > 0:
            self.primeiro_frame_renderizado = True

        for efeito in self.efeitos:
            renderer = self.renderers[efeito.nome]

            renderer.renderizar(
                efeito,
                efeito.animacoes,
                self.camera,
            )

        if self.menu_contextual.aberto:
            self.menu_contextual.renderizar(self, self.camera)

        self._renderizar_audio_hud()

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

    def _renderizar_audio_hud(self):
        if self.audio_hud_imagem is None:
            try:
                self.audio_hud_imagem = asset_manager.carregar("ui/audio.png")
            except Exception:
                self.audio_hud_imagem = False
                self.audio_hud_rect = None
                return

        if not self.audio_hud_imagem:
            return

        imagem = self.audio_hud_imagem
        tamanho = 48
        escala = min(
            tamanho / max(1, imagem.get_width()), tamanho / max(1, imagem.get_height())
        )
        if escala != 1.0:
            imagem = self.transform.escalar(
                imagem,
                (
                    max(1, int(imagem.get_width() * escala)),
                    max(1, int(imagem.get_height() * escala)),
                ),
            )

        margem = 14
        self.audio_hud_rect = imagem.get_rect(
            top=margem,
            right=self.tela.get_width() - margem,
        )
        self.tela.blit(imagem, self.audio_hud_rect)

        if self.audio_manager.habilitado and self.audio_manager.musica_vila_tocando:
            kivy_adapter.draw.rect(
                self.tela,
                (90, 220, 110),
                (
                    self.audio_hud_rect.left - 4,
                    self.audio_hud_rect.bottom + 4,
                    self.audio_hud_rect.width + 8,
                    3,
                ),
            )

    def progresso_carregamento(self):
        total = 0
        carregado = 0
        renderers = {}

        for item in self.entidades:
            renderers[id(item["renderer"])] = item["renderer"]

        for renderer in self._renderers_auxiliares.values():
            renderers[id(renderer)] = renderer

        for renderer in renderers.values():
            fila = getattr(renderer, "_fila", ())
            total += len(fila)
            carregado += min(getattr(renderer, "_indice", 0), len(fila))

        if total <= 0:
            return 1.0 if self.carregado else 0.0
        return max(0.0, min(1.0, carregado / total))

    def _atualizar_carregamento_assets(self):
        renderers = {}
        for item in self.entidades:
            renderer = item["renderer"]
            renderers[id(renderer)] = (renderer, item["frames_carregamento"])

        for renderer, quantidade in renderers.values():
            if not renderer.carregado:
                renderer.atualizar_carregamento(max(1, min(int(quantidade), 2)))

        if self.menu_contextual is not None:
            self.menu_contextual.atualizar_carregamento()

        for renderer in self._renderers_auxiliares.values():
            if not renderer.carregado:
                renderer.atualizar_carregamento(2)

        renderers_principais_prontos = bool(self.entidades) and all(
            renderer.carregado for renderer, _ in renderers.values()
        )

        tipos_menu = (
            "castelo",
            "casa",
            "quartel",
            "avatar_aldeao",
            "avatar_soldado",
            "escudo",
        )
        menu_pronto = self.menu_contextual is not None and all(
            nome in self.renderers and self.renderers[nome].carregado
            for nome in tipos_menu
        )

        auxiliares_prontos = all(
            renderer.carregado for renderer in self._renderers_auxiliares.values()
        )

        # Depois que a cena inicial ficou pronta, novos spawns não podem
        # colocar o jogo inteiro novamente no estado de carregamento.
        if not self.carregado:
            self.carregado = (
                renderers_principais_prontos and menu_pronto and auxiliares_prontos
            )

        if self.carregado:
            self._carregamento_pendente = False


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
        self.navegacao.definir_metricas(self.cenario_principal.metricas_desempenho)

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
