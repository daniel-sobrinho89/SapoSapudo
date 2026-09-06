from contextlib import suppress
from math import hypot

import utils.kivy_adapter as kivy_adapter
from application.fabrica_controladores import FabricaControladores
from application.usecases.conversa.controlar_conversa import ControlarConversaUseCase
from application.usecases.personagem.mover import MoverPersonagemUseCase
from core.audio_manager import AudioManager
from core.camera import Camera
from core.ciclo_dia_noite import CicloDiaNoite
from core.game_config import obter_config, obter_tipos
from core.indice_espacial import IndiceEspacial
from core.navegacao_mapa import NavegacaoMapa
from core.performance_metrics import PerformanceMetrics
from core.save_game import SaveGameManager
from core.world.editor import WorldEditor
from core.world.service import WorldService
from domains.construcao.entity import (  # noqa: F401
    criar_construcao,
)
from domains.efeitos.entity import criar_efeitos  # noqa: F401
from domains.personagem.entity import (  # noqa: F401
    criar_arvore,
    criar_entidade,
    criar_mina_ouro,
    criar_recurso,
)
from render.asset_manager import asset_manager
from render.conversa_renderer import ConversaRenderer
from render.menu_contextual_renderer import MenuContextualRenderer
from render.objeto_interativo_renderer import ObjetoInterativoRenderer
from render.sprite_animado_renderer import SpriteAnimadoRenderer
from render.tilemap_renderer import TileMapRenderer
from render.world_debug_renderer import WorldDebugRenderer
from render.world_editor_renderer import WorldEditorRenderer
from utils.config import ALTURA, CENTRO_OFFSET_Y, TILE_SIZE
from utils.kivy_adapter import Rect


class CenarioBase:
    def __init__(
        self,
        tela,
        transform,
        navegacao,
        mover_personagem,
        tilemap_renderer,
        camera,
        estado,
        world_context=None,
        ciclo_dia_noite=None,
    ):
        self.tela = tela
        self.transform = transform
        self.camera = camera
        self.navegacao = navegacao
        self.mover_personagem = mover_personagem
        self.tilemap_renderer = tilemap_renderer
        self.estado = estado
        self.world_context = world_context
        self.ciclo_dia_noite = ciclo_dia_noite or CicloDiaNoite()
        self.tilemap_renderer.ciclo_dia_noite = self.ciclo_dia_noite

    def carregar(self):
        raise NotImplementedError

    def atualizar(self, dt):
        raise NotImplementedError

    def renderizar(self, dt):
        raise NotImplementedError


class CenarioPrincipal(CenarioBase):
    # DEBUG TEMPORARIO
    DEBUG_NAVEGACAO_VISUAL = False

    # Espaço pessoal mínimo entre unidades móveis. É menor que a distância
    # de parada do ataque, então duas unidades podem combater sem se sobrepor.
    RAIO_PESSOAL_PERSONAGEM = 18.0
    DISTANCIA_MINIMA_ENTRE_PERSONAGENS = RAIO_PESSOAL_PERSONAGEM * 2.0
    SEPARACAO_MAXIMA_POR_FRAME = 5.0

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
        self.world_debug = WorldDebugRenderer(self.tela)
        self.world_editor_renderer = None
        if self.world_context is not None:
            self.world_debug_context = self.world_context
        self.menu_contextual = None
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
        self.menu_jogo_aberto = False
        self.menu_jogo_status = ""
        self.save_game = SaveGameManager(self)
        self.evolucao_espada_imagem = None
        self.evolucao_escudo_imagem = None
        self.itens_interativos = []
        self.renderer_itens_interativos = ObjetoInterativoRenderer(self.tela)
        self.renderer_itens_interativos.ciclo_dia_noite = self.ciclo_dia_noite
        self.conversa_controller = ControlarConversaUseCase(self)
        self.renderer_conversa = None
        self.sapudo = None
        self.bandidos_inicializados = False
        self._urso_ataque_noturno_ciclo = None
        self._urso_retornando_caverna = False
        self._urso_caverna_destino = None
        self._descanso_sapudo_ativo = False
        self._descanso_sapudo_posicao = None
        self._descanso_sapudo_fator_relogio = 180.0
        self._danos_flutuantes = []
        self._proximo_save_id = 1

    @property
    def total_madeira(self):
        return self.estoque["madeira"]

    @property
    def total_ouro(self):
        return self.estoque["ouro"]

    @property
    def total_carne(self):
        return self.estoque["carne"]

    def registrar_dano_visual(self, entidade, dano):
        """Cria um número flutuante indicando o dano recebido pela unidade."""
        dano = int(dano)
        if dano <= 0:
            return

        eh_sapudo = (
            entidade is self.sapudo or getattr(entidade, "nome", "").lower() == "sapudo"
        )
        eh_inimigo = (
            entidade in self.personagens_hostis or entidade in self.construcoes_hostis
        )
        if not eh_sapudo and not eh_inimigo:
            return

        self._danos_flutuantes.append(
            {
                "entidade": entidade,
                "dano": dano,
                "tempo": 0.0,
                "duracao": 0.85,
                "altura_inicial": 72.0,
            }
        )

    def _atualizar_danos_flutuantes(self, dt):
        vivos = []
        for efeito in self._danos_flutuantes:
            efeito["tempo"] += max(0.0, float(dt))
            if efeito["tempo"] < efeito["duracao"]:
                vivos.append(efeito)
        self._danos_flutuantes = vivos

    def _renderizar_danos_flutuantes(self):
        for efeito in self._danos_flutuantes:
            entidade = efeito["entidade"]
            progresso = min(1.0, efeito["tempo"] / efeito["duracao"])
            altura = efeito["altura_inicial"] + progresso * 34.0
            x, y = self.camera.tela(entidade.x, entidade.y + altura)
            cor = (
                (220, 45, 45)
                if (
                    entidade is self.sapudo
                    or getattr(entidade, "nome", "").lower() == "sapudo"
                )
                else (55, 125, 235)
            )
            texto = str(efeito["dano"])
            # Sombra para manter a leitura sobre cenários claros ou escuros.
            kivy_adapter.draw.text(
                self.tela, texto, (int(x) + 2, int(y) + 2), (20, 20, 20), 18
            )
            kivy_adapter.draw.text(self.tela, texto, (int(x), int(y)), cor, 18)

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
        if entidade not in lista:
            lista.append(entidade)

        # Construções dinâmicas da missão precisam entrar no mesmo registro
        # visual usado pelas construções carregadas normalmente. Isso evita que
        # uma entidade restaurada/runtime exista na coleção, mas fique sem
        # _render_registros e portanto nunca chegue ao renderer.
        if entidade not in self._registro_entidades:
            config = obter_config(entidade.nome)
            renderer = self._obter_renderer(entidade.nome, config)
            self.registrar_entidade(
                entidade,
                renderer,
                config.get("grupo", "personagens"),
                config.get("faccao"),
                config.get("renderer", {}).get("frames_carregamento", 1),
            )
        elif (
            not any(item.get("entidade") is entidade for item in self._render_registros)
            and nome_lista != "efeitos"
        ):
            registro = self._registro_entidades[entidade]
            renderer_cfg = obter_config(entidade.nome).get("renderer", {})
            self._render_registros.append(
                {
                    "entidade": entidade,
                    "renderer": registro["renderer"],
                    "escala": renderer_cfg.get("escala", 1.0) or 1.0,
                    "grupo": registro["grupo"],
                }
            )

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

    def reativar_recurso(self, resource_id, entidade):
        if entidade is None:
            return

        nome = getattr(entidade, "nome", "")

        if nome.startswith("arvore"):
            iniciar_crescimento = getattr(
                entidade,
                "iniciar_crescimento",
                None,
            )

            if callable(iniciar_crescimento):
                iniciar_crescimento()
            else:
                entidade.madeira = 8
                entidade.vida = 8

                estado = getattr(
                    entidade.animacoes,
                    "estado",
                    None,
                )

                if estado is not None:
                    with suppress(Exception):
                        entidade.animacoes.definir("ocioso")

            return

        if nome == "mina_ouro":
            entidade.minerio = getattr(entidade, "OURO_MAXIMO", 65)
            entidade.vida = entidade.minerio

            atualizar_estado = getattr(
                entidade,
                "_atualizar_estado",
                None,
            )

            if callable(atualizar_estado):
                atualizar_estado()

            if entidade not in self.minas_ouro:
                config = obter_config(nome)
                renderer = self._obter_renderer(nome, config)

                self.registrar_entidade(
                    entidade,
                    renderer,
                    config["grupo"],
                    config.get("faccao"),
                    config["renderer"]["frames_carregamento"],
                )

                self.minas_ouro.append(entidade)
                self._registrar_no_indice(entidade)

            return

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
                            usecase.personagem.animacoes.definir("ocioso_flip")
                        else:
                            usecase.personagem.animacoes.definir("ocioso")

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
                        usecase.personagem.animacoes.definir("ocioso_flip")
                    else:
                        usecase.personagem.animacoes.definir("ocioso")

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
            self.renderer_conversa = ConversaRenderer(
                self.tela,
                self.renderers,
                self._criar_avatar_dialogo,
            )
            self.conversa_controller.definir_renderer(self.renderer_conversa)
            self._renderers_auxiliares = {}
            for nome in ("barra_vida_base", "barra_vida"):
                self.carregar_entidade_temporaria(nome)
                self._renderers_auxiliares[nome] = self.renderers[nome]
            # O encontro inicial serve apenas para uma partida nova. Em uma
            # partida carregada o SaveGameManager restaura a fotografia do
            # mundo e do controlador, portanto não pode recriar/resetar
            # entidades da missão aqui.
            if not getattr(self, "_carregando_save", False):
                self._inicializar_encontro_bandidos()
            for nome in ("osso1", "osso2", "osso3", "avatar_bandido"):
                renderer = self.renderers.get(nome)
                if renderer is not None:
                    self._renderers_auxiliares[nome] = renderer
            self._menu_criado = True

        if not self._tipos_carregamento_restantes:
            self._atualizar_carregamento_assets()

    def carregar_entidade(self, tipo, x=None, y=None, altura=None):
        # Esqueletos não fazem mais parte do mundo atual. O filtro fica aqui
        # também para impedir que um spawn antigo ou arquivo de mapa legado
        # volte a renderizá-los.
        if tipo == "esqueleto":
            return [] if x is None and y is None else None

        config = obter_config(tipo)
        criador = globals()[config["classe"]]
        entidades = []

        if x is None and y is None:
            spawns_world = (
                self.world_context.spawn_system.obter_spawns_tipo(tipo)
                if self.world_context is not None
                else ()
            )
            if tipo == "bandido":
                # Os dois bandidos desta missão são narrativos: só entram no
                # mundo quando Bernardo inicia o encontro.
                spawns_world = tuple(
                    spawn for spawn in spawns_world if "narrativa" not in spawn.tags
                )
            spawns = [
                {
                    "x": spawn.posicao.x,
                    "y": spawn.posicao.y,
                    "altura": spawn.posicao.altura,
                    "id": spawn.id,
                    "regiao": spawn.regiao,
                }
                for spawn in spawns_world
            ]
            if not spawns:
                if tipo == "bandido":
                    return []
                entidade = criador(tipo)
                renderer = self._obter_renderer(tipo, config)
                if config.get("grupo") == "efeitos":
                    self._renderers_auxiliares[tipo] = renderer
                return entidade
        else:
            spawns = [{"x": x, "y": y, "altura": 0 if altura is None else altura}]

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
            if spawn.get("id"):
                entidade.world_spawn_id = spawn["id"]
                entidade.world_resource_id = spawn["id"]
                entidade.persistencia_dinamica = False
                entidade.save_id = f"world:{spawn['id']}"
            elif x is not None:
                # Entidades criadas em runtime pertencem à fotografia do save.
                # O SaveGameManager atribui um ID sequencial na primeira gravação.
                entidade.persistencia_dinamica = True
                entidade.save_id = None

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

            if grupo == "efeitos":
                self.efeitos.append(entidade)

            colecao = config["renderer"]["colecao"]
            if grupo != "efeitos":
                self.adicionar_personagem(entidade, colecao)
                if entidade.nome == "sapudo":
                    self.sapudo = entidade
                    self.camera.definir_limites_mundo(
                        self.tilemap_renderer.offset_x,
                        self.tilemap_renderer.offset_y,
                        self.tilemap_renderer.offset_x
                        + self.tilemap_renderer.largura * 64,
                        self.tilemap_renderer.offset_y
                        + self.tilemap_renderer.altura * 64,
                    )
                elif (
                    entidade.nome == "aldeao"
                    and self.conversa_controller.bernardo is None
                ):
                    self.conversa_controller.registrar_bernardo(entidade)

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

    def _criar_avatar_dialogo(self, tipo):
        config = obter_config(tipo)
        entidade = globals()[config["classe"]](tipo)
        renderer = self._obter_renderer(tipo, config)
        if not renderer.carregado:
            renderer.atualizar_carregamento(max(1, len(getattr(renderer, "_fila", ()))))
        return entidade

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
        renderer.ciclo_dia_noite = self.ciclo_dia_noite

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

    def _obter_urso_ativo(self):
        for urso in self.personagens_hostis:
            if getattr(urso, "nome", None) == "urso" and getattr(urso, "vida", 0) > 0:
                return urso
        return None

    def _obter_posicao_caverna_urso(self):
        """Obtém um ponto de saída caminhável e visualmente à frente da caverna."""
        cavernas = [
            caverna
            for caverna in self.construcoes_hostis
            if getattr(caverna, "nome", None) == "caverna"
        ]
        if not cavernas:
            cavernas = [
                construcao
                for construcao in self.construcoes
                if getattr(construcao, "nome", None) == "caverna"
            ]
        if not cavernas:
            return None

        caverna = cavernas[0]
        try:
            rect = self.obter_rect_colisao(caverna)
        except Exception:
            rect = Rect(caverna.x - 48, caverna.y - 48, 96, 96)

        altura_urso = 1
        margem = max(28.0, getattr(self.navegacao, "RAIO_COLISAO_CONSTRUCAO", 0) + 20.0)

        # Começamos pela borda inferior/externa e, se necessário, tentamos
        # pontos laterais. Todos os candidatos são validados com altura 1,
        # portanto o urso não nasce dentro do obstáculo nem em um tile onde
        # personagens da altura 1 não conseguem andar.
        candidatos = [
            (rect.centerx, rect.bottom - margem),
            (rect.centerx, rect.top + margem),
            (rect.left - margem, rect.centery),
            (rect.right + margem, rect.centery),
            (rect.left - margem, rect.bottom - margem),
            (rect.right + margem, rect.bottom - margem),
            (rect.left - margem, rect.top + margem),
            (rect.right + margem, rect.top + margem),
        ]

        validos = []
        for x, y in candidatos:
            try:
                valido = self.navegacao.pode_andar(x, y, altura_urso)
            except Exception:
                valido = False
            if valido:
                distancia = hypot(x - caverna.x, y - caverna.y)
                # Em empate, damos preferência ao maior y, que é desenhado
                # mais à frente no ordenamento de profundidade do cenário.
                validos.append((distancia, -y, x, y))

        if not validos:
            return None

        _, _, x, y = min(validos)
        return x, y, altura_urso

    def _processar_retorno_matinal_urso(self):
        """Ao amanhecer, recolhe o urso apenas se ele não estiver atacando Sapudo."""
        ciclo = self.ciclo_dia_noite
        hora_anterior = getattr(self, "_hora_dia_noite_anterior", ciclo.hora)
        hora_atual = ciclo.hora
        # Amanhecer ocorre somente na passagem 05:xx -> 06:xx.
        # A passagem 23:xx -> 00:xx é meia-noite e não deve recolher o urso.
        amanheceu = hora_anterior < 6.0 <= hora_atual
        if not amanheceu:
            return

        urso = self._obter_urso_ativo()
        if urso is None or not getattr(urso, "visivel", True):
            return

        controlador = self.controladores.get(urso)
        atacar = controlador.get("acoes", {}).get("atacar") if controlador else None
        usecase = atacar.get("usecase") if atacar else None
        alvo = getattr(usecase, "entidade_alvo", None)

        sapudo = getattr(self, "sapudo", None)
        # "Perseguir" e "atacar" são estados diferentes. Durante o dia,
        # somente um combate realmente iniciado contra o Sapudo pode
        # continuar. Se o urso apenas estiver correndo atrás dele, ou se
        # estiver perseguindo qualquer outro alvo, ele deve retornar à caverna.
        if alvo is sapudo:
            maquina = getattr(getattr(urso, "animacoes", None), "maquina", None)
            esta_atacando = bool(maquina and maquina.atacando())
            if esta_atacando:
                return

        if self._urso_retornando_caverna:
            return

        destino = self._obter_posicao_caverna_urso()
        if destino is None:
            return

        if usecase is not None and getattr(usecase, "entidade_alvo", None) is not None:
            finalizar = getattr(usecase, "_finalizar_ataque", None)
            if callable(finalizar):
                finalizar()

        self.mover_personagem.cancelar_rota(urso)
        self._urso_caverna_destino = (destino[0], destino[1])
        self._urso_retornando_caverna_entidade = urso
        self._urso_retornando_caverna = True
        urso.visivel = True
        urso.destino_x, urso.destino_y = self._urso_caverna_destino

    def _atualizar_retorno_matinal_urso(self, dt):
        if not self._urso_retornando_caverna:
            return

        urso = self._obter_urso_ativo()
        if urso is None:
            self._urso_retornando_caverna = False
            self._urso_retornando_caverna_entidade = None
            self._urso_caverna_destino = None
            return

        destino = self._urso_caverna_destino
        caverna = self._obter_caverna_urso()
        if destino is None or caverna is None:
            self._urso_retornando_caverna = False
            self._urso_retornando_caverna_entidade = None
            self._urso_caverna_destino = None
            return

        # O retorno usa exatamente o mesmo sistema de navegação dos demais
        # personagens. O destino é um ponto caminhável na entrada da caverna,
        # nunca o centro/parede do relevo. Assim o urso não atravessa obstáculos.
        dx = destino[0] - urso.x
        dy = destino[1] - urso.y
        distancia = hypot(dx, dy)

        if distancia <= 32.0:
            self.mover_personagem.cancelar_rota(urso)
            urso.x, urso.y = destino
            urso.base_pe_y = urso.y
            urso.destino_x, urso.destino_y = destino
            urso.animacoes.definir_por_direcao("ocioso", dx)
            urso.visivel = False
            self._urso_retornando_caverna = False
            self._urso_retornando_caverna_entidade = None
            self._urso_caverna_destino = None
            return

        from application.usecases.personagem.atacar import AtacarPersonagemUseCase

        velocidade = getattr(AtacarPersonagemUseCase, "VELOCIDADE", 110)
        self.mover_personagem.executar(
            personagem=urso,
            navegacao=self.navegacao,
            velocidade=velocidade,
            estado_correndo="correndo",
            estado_correndo_flip="correndo_flip",
            estado_parado="ocioso",
            estado_parado_flip="ocioso_flip",
            dt=dt,
            destino_externo=destino,
        )
        # A orientação já foi atualizada por MoverPersonagemUseCase a partir
        # do deslocamento horizontal real deste frame. Não a sobrescreva com
        # a posição final da caverna, pois isso faz o Urso caminhar de costas
        # até o trecho em que o deslocamento coincide com o destino final.

    def _obter_caverna_urso(self):
        for caverna in getattr(self, "construcoes_hostis", ()):
            if getattr(caverna, "nome", None) == "caverna":
                return caverna
        for caverna in getattr(self, "construcoes", ()):
            if getattr(caverna, "nome", None) == "caverna":
                return caverna
        return None

    def _processar_ataque_noturno_urso(self):
        ciclo = self.ciclo_dia_noite
        # O horário fica no sprites_config para ser ajustável sem alterar a IA.
        config_noturno = obter_config("urso").get("comportamento_noturno", {})
        texto_hora_saida = str(config_noturno.get("hora_saida", "18:10"))
        hora_str, minuto_str = texto_hora_saida.split(":", 1)
        hora_saida = int(hora_str) + (int(minuto_str) / 60.0)
        hora_anterior = getattr(self, "_hora_dia_noite_anterior", ciclo.hora)
        hora_atual = ciclo.hora
        self._hora_dia_noite_anterior = hora_atual

        cruzou_hora = hora_anterior < hora_saida <= hora_atual
        # Trata também a virada 24h -> 00h sem disparar novamente no mesmo ciclo.
        cruzou_hora |= (
            hora_atual >= hora_saida
            and hora_anterior > hora_atual
            and hora_anterior < 24.0
        )

        if not cruzou_hora:
            return

        numero_ciclo = (
            int(
                (getattr(ciclo, "_tempo_decorrido", 0.0)) / ciclo.DURACAO_CICLO_SEGUNDOS
            )
            if hasattr(ciclo, "_tempo_decorrido")
            else int(getattr(ciclo, "hora", 0.0) < hora_saida)
        )
        # A deduplicação principal usa a hora de saída observada; como o relógio
        # inicia às 08:00, cada retorno a 18:10 cria uma nova janela naturalmente.
        if self._urso_ataque_noturno_ciclo is not None and hora_atual < hora_saida:
            self._urso_ataque_noturno_ciclo = None
        urso_existente = self._obter_urso_ativo()
        posicao = self._obter_posicao_caverna_urso()
        if urso_existente is not None:
            # O urso recolhido durante o dia é reutilizado na noite seguinte.
            if not getattr(urso_existente, "visivel", True) and posicao is not None:
                self.mover_personagem.cancelar_rota(urso_existente)
                urso_existente.x, urso_existente.y = posicao[0], posicao[1]
                urso_existente.base_pe_y = urso_existente.y
                urso_existente.destino_x, urso_existente.destino_y = (
                    urso_existente.x,
                    urso_existente.y,
                )
                urso_existente.visivel = True
                self._urso_retornando_caverna = False
                self._urso_retornando_caverna_entidade = None
                self._urso_caverna_destino = None
                urso = urso_existente
            else:
                self._urso_ataque_noturno_ciclo = numero_ciclo
                return
        else:
            posicao = self._obter_posicao_caverna_urso()
            if posicao is None:
                return
            urso = self.carregar_entidade("urso", posicao[0], posicao[1], altura=1)
        if urso is None:
            return

        controlador = self.controladores.get(urso)
        ataque = controlador.get("acoes", {}).get("atacar") if controlador else None
        usecase = ataque.get("usecase") if ataque else None
        iniciar = getattr(usecase, "iniciar_ataque_noturno", None)
        if iniciar is not None and iniciar(urso):
            self._urso_ataque_noturno_ciclo = numero_ciclo
            return

        # Se o Sapudo não estiver disponível, não mantemos um urso órfão na caverna.
        self.remover_personagem(urso)

    def iniciar_descanso_sapudo(self):
        """Faz Sapudo entrar na casa de Bernardo e pula rapidamente até 06:30."""
        if self._descanso_sapudo_ativo:
            return False

        sapudo = self.sapudo
        casa = self.conversa_controller._casa_bernardo()
        if sapudo is None or casa is None:
            return False

        hora = float(self.ciclo_dia_noite.hora) % 24.0
        if not (hora >= 18.0 or hora < 5.0):
            return False

        self._descanso_sapudo_posicao = (
            sapudo.x,
            sapudo.y,
            getattr(sapudo, "altura", 0),
        )
        self._descanso_sapudo_ativo = True
        sapudo.visivel = False
        sapudo.destino_x = sapudo.x
        sapudo.destino_y = sapudo.y
        sapudo.defesa_ativa = False
        sapudo.perfect_block = False
        sapudo.animacoes.definir("ocioso", flip=sapudo.animacoes.flip)

        # Limpa qualquer combate do Urso antes de pausar o mundo.
        # O relógio continua acelerando dentro da casa, então o coordenador
        # não terá frames normais para desmontar o alvo sozinho.
        urso = self._obter_urso_ativo()
        if urso is not None:
            controlador_urso = self.controladores.get(urso)
            ataque = (
                controlador_urso.get("acoes", {}).get("atacar")
                if controlador_urso
                else None
            )
            usecase_urso = ataque.get("usecase") if ataque else None
            if (
                usecase_urso is not None
                and getattr(usecase_urso, "entidade_alvo", None) is sapudo
            ):
                finalizar = getattr(usecase_urso, "_finalizar_ataque", None)
                if callable(finalizar):
                    finalizar()
                else:
                    usecase_urso.entidade_alvo = None
                self.mover_personagem.cancelar_rota(urso)
                urso.destino_x = urso.x
                urso.destino_y = urso.y
                urso.animacoes.definir("ocioso", flip=urso.animacoes.flip)

        # Limpa qualquer comando manual que estivesse pressionado no instante
        # em que Sapudo entrou na casa.
        manual = getattr(
            getattr(self, "coordenador_estado_jogo", None), "sapudo_manual", None
        )
        if manual is not None:
            manual.teclas.clear()
            manual.ataque_em_andamento = False

        return True

    def _finalizar_descanso_sapudo(self):
        if not self._descanso_sapudo_ativo:
            return

        sapudo = self.sapudo
        posicao = self._descanso_sapudo_posicao
        self.ciclo_dia_noite.definir_hora(6.5)

        if sapudo is not None:
            if posicao is not None:
                sapudo.x, sapudo.y = posicao[0], posicao[1]
                sapudo.altura = posicao[2]
            sapudo.destino_x = sapudo.x
            sapudo.destino_y = sapudo.y
            sapudo.visivel = True
            sapudo.animacoes.definir("ocioso", flip=sapudo.animacoes.flip)
            self.indice_espacial.atualizar(sapudo)

        manual = getattr(
            getattr(self, "coordenador_estado_jogo", None), "sapudo_manual", None
        )
        if manual is not None:
            manual.teclas.clear()
            manual.ataque_em_andamento = False

        self._descanso_sapudo_ativo = False
        self._descanso_sapudo_posicao = None

        self._hora_dia_noite_anterior = 5.99
        self._processar_retorno_matinal_urso()

        cc = getattr(self, "conversa_controller", None)
        recolher = getattr(cc, "recolher_bernardo", None) if cc is not None else None
        bernardo = getattr(cc, "bernardo", None) if cc is not None else None
        if recolher is not None and bernardo is not None:
            with suppress(Exception):
                recolher.atualizar(0.0, 6.5, bernardo)

    def atualizar(self, dt):
        self.metricas_desempenho.iniciar_frame()

        if self._descanso_sapudo_ativo:
            hora_atual = self.ciclo_dia_noite.hora
            horas_ate_0630 = (6.5 - hora_atual) % 24.0
            delta_horas = (
                max(0.0, float(dt)) * self._descanso_sapudo_fator_relogio
            ) / self.ciclo_dia_noite.segundos_por_hora

            if delta_horas >= horas_ate_0630:
                self.ciclo_dia_noite.definir_hora(6.5)
                self._finalizar_descanso_sapudo()
                return

            self.ciclo_dia_noite.atualizar(
                dt, multiplicador=self._descanso_sapudo_fator_relogio
            )
            return

        self.ciclo_dia_noite.atualizar(dt)
        self._processar_retorno_matinal_urso()
        self._atualizar_retorno_matinal_urso(dt)
        self._processar_ataque_noturno_urso()
        if self.world_context is not None:
            self.world_context.atualizar(dt)
        self.conversa_controller.atualizar(dt)

        conversa_aberta = self.conversa_controller.aberta
        for item in self.entidades:
            entidade = item["entidade"]

            if conversa_aberta and item.get("grupo") in ("personagens", "hostis"):
                continue

            deve_atualizar = not entidade.vida <= 0
            if getattr(entidade, "crescendo", False):
                deve_atualizar = True

            if deve_atualizar:
                if self.world_context is not None:
                    self.world_context.vincular_entidade(entidade)
                entidade.atualizar(dt)
                grupo = item.get("grupo")

                if (
                    grupo in ("personagens", "hostis", "ovelhas")
                    and entidade is not self.construcao_arrastando
                ):
                    self.indice_espacial.atualizar(entidade)

        self._atualizar_danos_flutuantes(dt)
        self._resolver_separacao_personagens()
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

    def _resolver_separacao_personagens(self):
        unidades = [
            item["entidade"]
            for item in self.entidades
            if item.get("grupo") in ("personagens", "hostis")
            and item["entidade"] in self.controladores
            and item["entidade"].vida > 0
            and item["entidade"]
            is not getattr(self, "_urso_retornando_caverna_entidade", None)
            and item["entidade"] is not self.construcao_arrastando
        ]

        if len(unidades) < 2:
            return

        raio_consulta = self.DISTANCIA_MINIMA_ENTRE_PERSONAGENS + 6.0
        processados = set()

        for unidade in unidades:
            vizinhos = self.indice_espacial.consultar_raio(
                unidade.x,
                unidade.y,
                raio_consulta,
                grupos={"personagens", "hostis"},
            )

            for outro in vizinhos:
                if outro is unidade or outro.vida <= 0:
                    continue

                par = tuple(sorted((id(unidade), id(outro))))
                if par in processados:
                    continue
                processados.add(par)

                if getattr(unidade, "altura", 0) != getattr(outro, "altura", 0):
                    continue

                dx = outro.x - unidade.x
                dy = outro.y - unidade.y
                distancia = hypot(dx, dy)
                minima = self.DISTANCIA_MINIMA_ENTRE_PERSONAGENS

                if distancia >= minima:
                    continue

                if distancia < 0.001:
                    sentido = 1.0 if id(unidade) < id(outro) else -1.0
                    dx, dy = sentido, 0.0
                    distancia = 1.0

                excesso = minima - distancia
                correcao = min(excesso * 0.5, self.SEPARACAO_MAXIMA_POR_FRAME)

                nx = dx / distancia
                ny = dy / distancia

                nova_unidade = (
                    unidade.x - nx * correcao,
                    unidade.y - ny * correcao,
                )
                novo_outro = (
                    outro.x + nx * correcao,
                    outro.y + ny * correcao,
                )

                if self._posicao_personagem_valida(
                    unidade, nova_unidade[0], nova_unidade[1]
                ):
                    unidade.x, unidade.y = nova_unidade

                if self._posicao_personagem_valida(outro, novo_outro[0], novo_outro[1]):
                    outro.x, outro.y = novo_outro

                self.indice_espacial.atualizar(unidade)
                self.indice_espacial.atualizar(outro)

    def _posicao_personagem_valida(self, personagem, x, y):
        try:
            return self.navegacao._caminho_livre(
                personagem.x,
                personagem.y,
                x,
                y,
                personagem.altura,
            ) and self.navegacao.pode_andar(x, y, personagem.altura)
        except Exception:
            return True

    def renderizar(self, dt):
        if self._carregamento_pendente:
            self._atualizar_carregamento_assets()
        if not self.carregado:
            return
        self._renderizar_cenario_principal(dt)

    def _renderizar_cenario_principal(self, dt):
        self.tilemap_renderer.renderizar(dt, self.camera)
        if self.world_context is not None and not self.world_editor_ativo:
            self.world_debug.renderizar(self.world_context, self.camera, self.sapudo)

        itens_render = []
        for item in self._render_registros:
            entidade = item["entidade"]
            renderer = item["renderer"]
            if getattr(entidade, "visivel", True) is False:
                continue
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
                and renderer.carregado
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

        self._renderizar_danos_flutuantes()

        for item in self.itens_interativos:
            self.renderer_itens_interativos.renderizar(item, self.camera)

        if not self.world_editor_ativo:
            self._renderizar_debug_navegacao()
            self._renderizar_hud_rpg()

            if not self.conversa_controller.aberta and self.menu_contextual.aberto:
                self.menu_contextual.renderizar(self, self.camera)

            self._renderizar_audio_hud()
            self._renderizar_menu_jogo()

        if self.world_editor_ativo and self.world_editor_renderer is not None:
            self.world_editor_renderer.renderizar(self.world_context, self.camera)
            return

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

        if self.renderer_conversa and self.renderer_conversa.aberta:
            self.renderer_conversa.renderizar()

    def _carregar_icone_evolucao(self, nome, arquivo):
        """Carrega e normaliza um ícone de evolução a partir do AssetManager."""
        atributo = f"evolucao_{nome}_imagem"
        imagem = getattr(self, atributo, None)

        if imagem is False:
            return None

        if imagem is None:
            try:
                original = asset_manager.carregar(arquivo)
                tamanho = 42
                escala = min(
                    tamanho / max(1, original.get_width()),
                    tamanho / max(1, original.get_height()),
                )
                if escala != 1.0:
                    original = self.transform.escalar(
                        original,
                        (
                            max(1, int(original.get_width() * escala)),
                            max(1, int(original.get_height() * escala)),
                        ),
                    )
                imagem = original
                setattr(self, atributo, imagem)
            except Exception:
                setattr(self, atributo, False)
                return None

        return imagem

    def _renderizar_audio_hud(self):
        """Renderiza somente o ícone do menu, não o antigo ícone de áudio."""
        tamanho = 48
        margem = 14
        x = self.tela.get_width() - margem - tamanho
        y = margem + 50
        self.audio_hud_rect = Rect(x, y, tamanho, tamanho)

        kivy_adapter.draw.rect(self.tela, (38, 45, 54, 235), self.audio_hud_rect)
        for deslocamento in (13, 22, 31):
            kivy_adapter.draw.rect(
                self.tela,
                (240, 220, 170, 255),
                (x + 11, y + deslocamento, 26, 3),
            )

    def _renderizar_menu_jogo(self):
        if not self.audio_hud_rect:
            return
        if not self.menu_jogo_aberto:
            return

        x = max(8, self.tela.get_width() - 230)
        y = self.audio_hud_rect.bottom + 10
        w, h = 220, 172
        kivy_adapter.draw.rect(self.tela, (18, 23, 29, 245), Rect(x, y, w, h))
        kivy_adapter.draw.rect(self.tela, (170, 140, 70, 255), Rect(x, y, w, 3))
        kivy_adapter.draw.text(self.tela, "JOGO", (x + 16, y + 12), (240, 220, 170), 19)

        self.menu_jogo_botoes = {
            "salvar": Rect(x + 14, y + 45, 192, 32),
            "carregar": Rect(x + 14, y + 83, 192, 32),
            "musica": Rect(x + 14, y + 121, 192, 32),
        }
        rotulos = {
            "salvar": "SALVAR",
            "carregar": "CARREGAR",
            "musica": "MÚSICA  ON"
            if self.audio_manager.musica_vila_tocando
            else "MÚSICA  OFF",
        }
        for chave, rect in self.menu_jogo_botoes.items():
            kivy_adapter.draw.rect(self.tela, (48, 58, 67, 255), rect)
            kivy_adapter.draw.text(
                self.tela,
                rotulos[chave],
                (rect.x + 18, rect.y + 8),
                (245, 245, 245),
                15,
            )

        if self.menu_jogo_status:
            kivy_adapter.draw.text(
                self.tela,
                self.menu_jogo_status,
                (x + 14, y + h - 18),
                (180, 220, 190),
                12,
            )

    def _inicializar_encontro_bandidos(self):
        """Registra os bandidos e ossos definidos em mapa1.json.

        O mapa é a única fonte de verdade para os spawns da área do encontro.
        """
        if self.bandidos_inicializados:
            return

        self.bandidos_inicializados = True

        bandidos = [
            personagem
            for personagem in self.personagens_hostis
            if getattr(personagem, "nome", None) == "bandido"
        ]

        for bandido in bandidos:
            bandido.definir_base_movimento(bandido.x, bandido.y)
            bandido.destino_x = bandido.x
            bandido.destino_y = bandido.y
            bandido.animacoes.definir("ocioso")

        self.conversa_controller.definir_bandidos(bandidos)

        for efeito in self.efeitos:
            if getattr(efeito, "nome", "") in {"osso1", "osso2", "osso3"}:
                efeito.persistente = True

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

        if not self.carregado:
            self.carregado = (
                renderers_principais_prontos and menu_pronto and auxiliares_prontos
            )

        if self.carregado:
            self._carregamento_pendente = False

    def _renderizar_debug_navegacao(self):
        """Overlay temporario para visualizar bloqueios e degraus."""
        if not self.DEBUG_NAVEGACAO_VISUAL or self.tilemap_renderer is None:
            return
        sapudo = self.sapudo
        if sapudo is None:
            return
        tilemap = self.tilemap_renderer
        altura_atual = getattr(sapudo, "altura", 0)
        tile_size = TILE_SIZE
        offset_x = getattr(tilemap, "offset_x", 0)
        offset_y = getattr(tilemap, "offset_y", 0)

        for linha in range(tilemap.altura):
            for coluna in range(tilemap.largura):
                if tilemap.eh_degrau(coluna, linha):
                    continue
                try:
                    acessivel = tilemap.pode_andar(coluna, linha, altura_atual)
                except Exception:
                    acessivel = True
                if acessivel:
                    continue
                rect_mundo = Rect(
                    offset_x + coluna * tile_size,
                    offset_y + linha * tile_size,
                    tile_size,
                    tile_size,
                )
                rect = self.camera.tela_rect(rect_mundo)
                kivy_adapter.draw.rect(self.tela, (230, 45, 45, 75), rect, width=2)

        for (coluna, linha), _dados in getattr(
            tilemap, "degraus_superficie", {}
        ).items():
            rect_mundo = Rect(
                offset_x + coluna * tile_size,
                offset_y + linha * tile_size,
                tile_size,
                tile_size,
            )
            rect = self.camera.tela_rect(rect_mundo)
            kivy_adapter.draw.rect(self.tela, (245, 220, 35, 90), rect, width=3)

        obter_obstaculos = getattr(self.navegacao, "_obter_obstaculos", None)
        if callable(obter_obstaculos):
            for obstaculo in obter_obstaculos() or ():
                try:
                    rect = self.camera.tela_rect(obstaculo)
                    kivy_adapter.draw.rect(self.tela, (230, 45, 45, 120), rect, width=2)
                except Exception:
                    continue

    def _renderizar_hud_rpg(self):
        estado = self.conversa_controller.estado
        titulos = {
            "inicial": "Converse com Bernardo",
            "aguardando_bandidos": "Derrote os 2 bandidos no Vale dos Ossos",
            "dialogo_bandidos": "Converse com os bandidos",
            "combate_bandidos": "Derrote os 2 bandidos",
            "machado_com_sapudo": "Pegue o machado e volte até Bernardo",
            "bernardo_trabalhando": "Bernardo está reunindo madeira para a casa",
            "casa_construindo": "Bernardo está levando madeira para a casa",
            "aguardando_roubao": "Encontre Roubão e converse com ele",
            "dialogo_roubao": "Converse com Roubão",
            "missao_planalto_cobras": "Derrote as 5 cobras do Planalto dos Pinheiros",
            "missao_planalto_caverna": "Destrua a caverna e encontre o martelo",
            "martelo_com_sapudo": "Leve o martelo até Bernardo",
            "missao_planalto_concluida": "Missão concluída",
            "casa_pronta": "A casa de Bernardo está pronta",
            "casa_visitada": "A vila está começando a crescer",
        }
        kivy_adapter.draw.rect(self.tela, (20, 24, 28, 220), Rect(18, 18, 390, 88))
        kivy_adapter.draw.text(self.tela, "MISSÃO", (30, 25), (230, 200, 120), 15)
        kivy_adapter.draw.text(
            self.tela, titulos.get(estado, ""), (30, 47), (245, 245, 245), 17
        )

        sapudo = self.sapudo
        if sapudo is not None:
            xp = getattr(sapudo, "experiencia", 0)
            pontos = getattr(sapudo, "pontos_evolucao", 0)
            nivel = getattr(sapudo, "nivel", 1)
            kivy_adapter.draw.text(
                self.tela,
                f"Nv. {nivel}  XP {xp}/{100 * max(1, nivel)}  Pontos {pontos}",
                (30, 82),
                (170, 215, 190),
                14,
            )
            kivy_adapter.draw.text(
                self.tela,
                f"ATQ {getattr(sapudo, 'ataque', 0)}   DEF {getattr(sapudo, 'defesa', 0)}",
                (260, 82),
                (235, 205, 150),
                14,
            )

        if self.conversa_controller.inventario.get("machado"):
            kivy_adapter.draw.text(self.tela, "Machado", (795, 26), (245, 225, 170), 17)

        if (
            getattr(self.conversa_controller, "evolucao_pendente", False)
            and sapudo is not None
        ):
            x, y, w, h = 610, 108, 385, 190
            kivy_adapter.draw.rect(self.tela, (16, 20, 24, 245), Rect(x, y, w, h))
            kivy_adapter.draw.rect(self.tela, (170, 140, 70, 255), Rect(x, y, w, 3))
            kivy_adapter.draw.text(
                self.tela, "EVOLUÇÃO", (x + 22, y + 18), (235, 205, 125), 22
            )
            kivy_adapter.draw.text(
                self.tela,
                "Clique na espada ou no escudo para escolher",
                (x + 22, y + 48),
                (230, 230, 230),
                15,
            )

            espada = self._carregar_icone_evolucao(
                "espada",
                "ui/espada.png",
            )
            escudo = self._carregar_icone_evolucao(
                "escudo",
                "ui/escudo.png",
            )

            kivy_adapter.draw.rect(
                self.tela,
                (75, 75, 85, 255),
                Rect(x + 22, y + 76, 54, 54),
            )
            if espada is not None:
                rect_espada = espada.get_rect(center=(x + 49, y + 103))
                self.tela.blit(espada, rect_espada)

            kivy_adapter.draw.text(
                self.tela,
                "ATAQUE  +1",
                (x + 88, y + 92),
                (245, 245, 245),
                17,
            )

            kivy_adapter.draw.rect(
                self.tela,
                (75, 75, 85, 255),
                Rect(x + 210, y + 76, 54, 54),
            )
            if escudo is not None:
                rect_escudo = escudo.get_rect(center=(x + 237, y + 103))
                self.tela.blit(escudo, rect_escudo)

            kivy_adapter.draw.text(
                self.tela,
                "DEFESA  +1",
                (x + 276, y + 92),
                (245, 245, 245),
                17,
            )
            kivy_adapter.draw.text(
                self.tela,
                f"Ataque {sapudo.ataque}   Defesa {sapudo.defesa}",
                (x + 22, y + 154),
                (175, 205, 225),
                15,
            )
            return

        prompt = self.conversa_controller.prompt()
        if prompt:
            x, y = self.camera.tela(sapudo.x, sapudo.y - 58)
            kivy_adapter.draw.rect(
                self.tela, (18, 22, 26, 225), Rect(x - 88, y - 26, 176, 30)
            )
            kivy_adapter.draw.text(
                self.tela, prompt, (x - 76, y - 19), (255, 240, 180), 14
            )

        if (
            self.conversa_controller.mensagem_proximidade
            and not self.conversa_controller.aberta
        ):
            kivy_adapter.draw.text(
                self.tela,
                self.conversa_controller.mensagem_proximidade,
                (18, 114),
                (180, 230, 180),
                14,
            )

        if self.renderer_conversa and self.renderer_conversa.aberta:
            self.renderer_conversa.renderizar()

    @property
    def world_editor_ativo(self):
        """Indica se o editor visual do mundo está ativo nesta cena."""
        editor = getattr(self, "world_editor", None)
        return bool(editor is not None and getattr(editor, "ativo", False))


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
        self.centro_y = ALTURA // 2 + CENTRO_OFFSET_Y
        self.estado = EstadoJogo.JOGANDO
        self.world_service = WorldService()
        self.world_context = self.world_service.carregar()
        self.world_editor = WorldEditor(self.world_service)
        self.ciclo_dia_noite = CicloDiaNoite()
        self.tilemap_renderer = TileMapRenderer(
            tela,
            asset_manager,
            transform,
            world_context=self.world_context,
            ciclo_dia_noite=self.ciclo_dia_noite,
        )
        self.world_context.tilemap_renderer = self.tilemap_renderer
        self.world_context.validator.tilemap_renderer = self.tilemap_renderer
        self.navegacao = NavegacaoMapa(
            self.tilemap_renderer, world_context=self.world_context
        )
        self.mover_personagem = MoverPersonagemUseCase()

        self.cenario_principal = CenarioPrincipal(
            tela,
            transform,
            self.navegacao,
            self.mover_personagem,
            self.tilemap_renderer,
            self.camera,
            self.estado,
            world_context=self.world_context,
            ciclo_dia_noite=self.ciclo_dia_noite,
        )

        self.navegacao.definir_obter_obstaculos(
            self.cenario_principal.obter_obstaculos_construcoes
        )
        self.navegacao.definir_metricas(self.cenario_principal.metricas_desempenho)

        self.world_editor_renderer = WorldEditorRenderer(tela, self.world_editor)
        self.cenario_principal.world_editor_renderer = self.world_editor_renderer
        self.world_context.world_editor = self.world_editor
        self.world_editor.configurar_callbacks(
            focar=self._focar_no_objeto_editor,
            adicionar_spawn=self._adicionar_spawn_editor,
            remover_spawn=self._remover_spawn_editor,
            mover_spawn=self._mover_spawn_editor,
        )
        self.world_context.world_service = self.world_service
        self.world_context.definir_callback_respawn(
            self.cenario_principal.reativar_recurso
        )
        self.cenario_principal.world_editor = self.world_editor
        self.cenario_atual = self.cenario_principal

    def alternar_world_debug(self):
        return self.cenario_principal.world_debug.alternar()

    def alternar_world_editor(self):
        estava_ativo = self.world_editor.ativo
        if not estava_ativo:
            self._camera_editor_anterior = (
                self.camera.x,
                self.camera.y,
                self.camera.zoom,
                self.camera.zoom_min,
                self.camera.zoom_max,
            )
            self.camera.zoom_min = 0.25
            self.camera.zoom_max = 4.0
        ativo = self.world_editor.alternar()
        self.cenario_principal.world_editor_renderer.editor = self.world_editor
        if not ativo:
            if hasattr(self, "_camera_editor_anterior"):
                _, _, _, _, _ = self._camera_editor_anterior
            self.camera.zoom = 1.0
            self.camera.zoom_min = 0.9
            self.camera.zoom_max = 2.0
            self.camera._ajustar_limites()
        return ativo

    def _focar_no_objeto_editor(self, item):
        if hasattr(item, "posicao_tile"):
            coluna, linha = item.posicao_tile
        elif hasattr(item, "posicao"):
            coluna, linha = self.world_context._pixel_para_tile(
                item.posicao.x, item.posicao.y
            )
        else:
            coluna = getattr(item, "x", 0) + getattr(item, "colunas", 1) / 2
            linha = getattr(item, "y", 0) + getattr(item, "linhas", 1) / 2
        x, y = self.tilemap_renderer.tile_para_pixel(int(coluna), int(linha))
        self.camera.x = x - self.camera.largura_mundo_visivel / 2 + TILE_SIZE / 2
        self.camera.y = y - self.camera.altura_mundo_visivel / 2 + TILE_SIZE / 2
        self.camera._ajustar_limites()

    def _adicionar_spawn_editor(self, spawn):
        entidade = self.cenario_principal.carregar_entidade(
            spawn.tipo, spawn.posicao.x, spawn.posicao.y
        )
        if entidade is not None:
            entidade.world_spawn_id = spawn.id
            entidade.world_resource_id = spawn.id
            self.world_context.vincular_entidade(entidade)

    def _remover_spawn_editor(self, spawn):
        for item in list(self.cenario_principal._registro_entidades):
            if getattr(item, "world_spawn_id", None) == spawn.id:
                self.cenario_principal.remover_personagem(item)
                break

    def _mover_spawn_editor(self, spawn, tile):
        """Sincroniza a entidade de runtime com a posição editada no WorldModel."""
        if spawn is None:
            return
        for entidade in list(self.cenario_principal._registro_entidades):
            if getattr(entidade, "world_spawn_id", None) == spawn.id:
                entidade.x = float(spawn.posicao.x)
                entidade.y = float(spawn.posicao.y)

                # continuar tentando retornar à posição anterior.
                if hasattr(entidade, "destino_x"):
                    entidade.destino_x = entidade.x
                if hasattr(entidade, "destino_y"):
                    entidade.destino_y = entidade.y
                if hasattr(entidade, "alvo_x"):
                    entidade.alvo_x = entidade.x
                if hasattr(entidade, "alvo_y"):
                    entidade.alvo_y = entidade.y
                break

    @property
    def world_editor_ativo(self):
        return bool(self.world_editor.ativo)

    def world_editor_clicar(self, pos_virtual):
        if not self.world_editor.ativo:
            return False
        if self.world_editor_renderer.clicar(pos_virtual):
            return True
        mouse_mundo = self.camera.mundo(*pos_virtual)
        self.world_editor.selecionar(*mouse_mundo)
        return True

    def world_editor_set_mouse_button(self, button):
        self._world_editor_mouse_button = button

    def world_editor_touch_down(self, pos_virtual):
        if not self.world_editor.ativo:
            return False

        mouse_button = getattr(self, "_world_editor_mouse_button", None)
        if mouse_button in ("scrollup", "scrollleft"):
            self.camera.aproximar(foco_tela=pos_virtual)
            return True
        if mouse_button in ("scrolldown", "scrollright"):
            self.camera.afastar(foco_tela=pos_virtual)
            return True
        if self.world_editor_renderer.clicar(pos_virtual):
            return True
        mouse_mundo = self.camera.mundo(*pos_virtual)
        coluna, linha = self.world_context._pixel_para_tile(*mouse_mundo)
        if (
            self.world_editor.modo == "terreno"
            and self.world_editor.submodo_terreno == "relevo"
        ):
            if self.world_editor.selecionar_relevo_por_tile(coluna, linha) is not None:
                return True
            self.world_editor.iniciar_area(coluna, linha)
            return True
        if (
            self.world_editor.modo == "terreno"
            and self.world_editor.submodo_terreno == "espuma"
        ):
            self.world_editor.iniciar_area(coluna, linha)
            return True
        if self.world_editor.modo == "terreno":
            self.world_editor.pintar_terreno_no_tile(coluna, linha)
            return True
        if self.world_editor.modo == "objeto":
            if (
                self.world_editor.item_selecionado() is not None
                and self.world_editor.ponto_esta_no_selecionado(*mouse_mundo)
                and self.world_editor.iniciar_arrasto(*mouse_mundo)
            ):
                return True
            spawn = self.world_editor.spawn_no_tile(coluna, linha)
            if spawn is not None:
                self.world_editor.selecionar_spawn_id(spawn.id)
                self.world_editor.iniciar_arrasto(*mouse_mundo)
            else:
                self.world_editor.adicionar_objeto_no_tile(coluna, linha)
            return True
        if (
            self.world_editor.item_selecionado() is not None
            and self.world_editor.ponto_esta_no_selecionado(*mouse_mundo)
            and self.world_editor.iniciar_arrasto(*mouse_mundo)
        ):
            return True
        self.world_editor.selecionar(*mouse_mundo)
        return True

    def world_editor_touch_move(self, pos_virtual):
        if not self.world_editor.ativo:
            return False
        mouse_mundo = self.camera.mundo(*pos_virtual)
        if (
            self.world_editor.modo == "terreno"
            and self.world_editor.submodo_terreno in ("relevo", "espuma")
        ):
            coluna, linha = self.world_context._pixel_para_tile(*mouse_mundo)
            self.world_editor.atualizar_area(coluna, linha)
            return True
        if self.world_editor.modo == "terreno":
            coluna, linha = self.world_context._pixel_para_tile(*mouse_mundo)
            self.world_editor.pintar_terreno_no_tile(coluna, linha)
            return True
        return self.world_editor.mover_arrasto(*mouse_mundo)

    def world_editor_touch_up(self, pos_virtual):
        if not self.world_editor.ativo:
            return False
        if (
            self.world_editor.modo == "terreno"
            and self.world_editor.submodo_terreno in ("relevo", "espuma")
        ):
            self.world_editor.finalizar_area()
        else:
            self.world_editor.finalizar_arrasto()
        return True

    def __getattr__(self, nome):
        if nome.startswith("__"):
            raise AttributeError(nome)
        cenario = self.__dict__.get("cenario_atual")
        if cenario is None:
            raise AttributeError(nome)
        try:
            return getattr(cenario, nome)
        except AttributeError as exc:
            raise AttributeError(
                f"{type(self).__name__!s} não possui '{nome}' e o cenário atual "
                f"{type(cenario).__name__!s} também não possui esse atributo"
            ) from exc

    def atualizar(self, dt):
        self.cenario_atual.atualizar(dt)

    def renderizar(self, dt):
        self.tela.fill((0, 0, 0, 0))
        self.tilemap_renderer.atualizar_carregamento()
        self.cenario_atual.renderizar(dt)


class EstadoJogo:
    ABERTURA = 0
    JOGANDO = 1
