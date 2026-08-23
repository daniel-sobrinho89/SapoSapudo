from contextlib import suppress
from dataclasses import dataclass

from application.coordenador_estado_jogo import CoordenadorEstadoJogo
from application.fabrica_controladores import FabricaControladores
from application.usecases.construcao.destruir_construcao import (
    DestruirConstrucaoUseCase,
)
from application.usecases.personagem.mover import MoverPersonagemUseCase
from core.game_config import obter_config
from core.indice_espacial import IndiceEspacial
from core.navegacao_mapa import NavegacaoMapa
from core.performance_metrics import PerformanceMetrics
from domains.arvore.entity import Arvore
from domains.construcao.entity import criar_construcao
from domains.personagem.entity import criar_entidade
from render.tilemap_renderer import TileMapRenderer
from tests.integration.harness.geometry import TestRect
from utils.kivy_adapter import Surface

ENTITY_CONFIG = {
    "soldado": dict(vida=300, ataque=7, defesa=2),
    "goblin_tocha": dict(vida=200, ataque=4, defesa=0),
    "aldeao": dict(vida=100, ataque=3, defesa=0),
}


@dataclass
class RealTraceClock:
    tempo: float = 0.0


class _TraceRenderer:
    """Renderer mínimo para os UseCases que ajustam efeitos visualmente."""

    escala = 1.0
    _TAMANHOS = {
        "soldado": (64, 96),
        "goblin_tocha": (64, 96),
        "aldeao": (64, 96),
        "casa": (128, 128),
        "casa_goblin": (128, 128),
        "poeira_grande": (128, 96),
        "fogo1": (64, 64),
        "fogo2": (72, 72),
        "explosao2": (160, 160),
    }

    def __init__(self, nome):
        self.nome = nome.lower()

    def obter_frame_animacao(self, animacoes):
        frame = Surface(self._TAMANHOS.get(self.nome, (64, 64)))
        frame.fill((255, 255, 255, 255))
        return frame


class IntegrationScenario:
    """Runtime integrado mínimo: usa as mesmas fábricas, UseCases,
    NavegacaoMapa e ciclo do CoordenadorEstadoJogo do jogo real.
    """

    def __init__(self):
        self.tilemap_renderer = TileMapRenderer(None, None, None)
        self.mover_personagem = MoverPersonagemUseCase()
        self._rects = {}
        self.entidades = []
        self.arvores = []
        self.minas_ouro = []
        self.recursos = []
        self.ovelhas = []
        self.construcoes = []
        self.construcoes_hostis = []
        self.personagens = []
        self.personagens_hostis = []
        self.controladores = {}
        self._registro_entidades = {}
        self.indice_espacial = IndiceEspacial(128)
        self.metricas_desempenho = PerformanceMetrics(habilitado=True)
        self.renderers = {
            nome: _TraceRenderer(nome)
            for nome in (
                "soldado",
                "goblin_tocha",
                "aldeao",
                "casa",
                "casa_goblin",
                "poeira_grande",
                "fogo1",
                "fogo2",
                "explosao2",
            )
        }
        self.efeitos = []
        self.estoque = {"madeira": 0, "ouro": 0, "carne": 0}
        self.construcao_arrastando = None
        self.navegacao = NavegacaoMapa(
            self.tilemap_renderer, self.obter_obstaculos_construcoes
        )
        self.navegacao.definir_metricas(self.metricas_desempenho)
        self.coordenador = CoordenadorEstadoJogo(self)
        self.clock = RealTraceClock()

    @property
    def tilemap(self):
        return self.tilemap_renderer

    @property
    def teste_largura(self):
        return self.tilemap_renderer.largura

    @property
    def teste_altura(self):
        return self.tilemap_renderer.altura

    def tick(self, dt=1 / 30):
        self.coordenador.executar(dt)
        self.clock.tempo += dt
        for entidade in list(self.entidades):
            obj = entidade["entidade"]
            if getattr(obj, "vida", 1) > 0:
                atualizar = getattr(obj, "atualizar", None)
                if atualizar:
                    atualizar(dt)
                self.indice_espacial.atualizar(obj)

        # O runtime real também atualiza os efeitos fora do fluxo das
        # entidades. Isso é importante nos testes visuais: poeira de morte,
        # fogo da construção e explosão precisam existir por seus ciclos reais
        # de animação, não apenas no frame em que foram criados.
        for efeito in list(self.efeitos):
            efeito.atualizar(dt)
            if (
                not getattr(efeito, "persistente", False)
                and getattr(efeito.animacoes.ocioso, "progresso", 0.0) >= 1.0
            ):
                self.efeitos.remove(efeito)

    def adicionar(self, entidade, grupo, faccao=None, rect=None):
        entidade._faccao_teste = faccao
        registro = {
            "entidade": entidade,
            "grupo": grupo,
            "faccao": faccao,
        }
        self.entidades.append(registro)
        getattr(self, grupo).append(entidade)
        self._registro_entidades[entidade] = registro
        grupo_indice = {
            "construcoes_hostis": "construcoes",
            "personagens_hostis": "hostis",
        }.get(grupo, grupo)
        if grupo_indice in (
            "personagens",
            "hostis",
            "construcoes",
            "recursos",
            "arvores",
            "minas_ouro",
        ):
            self.indice_espacial.registrar(entidade, grupo_indice)
        if rect is not None:
            self._rects[entidade] = rect
        return entidade

    def obter_entidade(self, objeto):
        return self._registro_entidades.get(objeto)

    def obter_rect_colisao(self, entidade):
        rect = self._rects.get(entidade)
        if rect is not None:
            return rect
        return TestRect(entidade.x - 32, entidade.y - 32, 64, 64)

    def obter_obstaculos_construcoes(self):
        return tuple(
            self._rects[c]
            for c in self.construcoes + self.construcoes_hostis
            if c is not self.construcao_arrastando and c in self._rects
        )

    def atualizar_obstaculos(self):
        self.navegacao.atualizar_obstaculos()

    def criar_personagem(self, nome, x, y, altura=0, faccao=None):
        cfg = ENTITY_CONFIG[nome]
        entidade = criar_entidade(nome, x, y, altura, **cfg)
        self.adicionar(
            entidade,
            "personagens_hostis" if nome == "goblin_tocha" else "personagens",
            faccao=faccao,
        )
        grupo = "hostis" if nome == "goblin_tocha" else "personagens"
        controlador = FabricaControladores.criar(entidade, self)
        if controlador:
            self.controladores[entidade] = controlador
        self.renderers.setdefault(nome.lower(), _TraceRenderer(nome))
        self.entidades[-1]["grupo"] = grupo
        return entidade

    def criar_construcao_teste(
        self, nome, x, y, altura=0, faccao=None, tamanho=128, vida=None
    ):
        # A vida da construção deve vir da mesma fonte de configuração usada
        # pelo jogo. Para casas hostis, o sprite/config correspondente é
        # ``casa_goblin``; para casas aliadas/neutras, ``casa``.
        tipo_config = "casa_goblin" if faccao == "goblin" and nome == "casa" else nome
        config = obter_config(tipo_config)
        vida_config = config.get("vida")
        vida = vida_config if vida is None else vida
        if vida is None:
            raise ValueError(
                f"Construção {tipo_config!r} não possui vida configurada em sprites"
            )
        entidade = criar_construcao(nome, x, y, altura, vida, 0, 0, 0)
        grupo_lista = "construcoes_hostis" if faccao == "goblin" else "construcoes"
        self.adicionar(
            entidade,
            grupo_lista,
            faccao=faccao,
            rect=TestRect(x - tamanho / 2, y - tamanho / 2, tamanho, tamanho),
        )
        self.renderers.setdefault(nome.lower(), _TraceRenderer(nome))
        self.entidades[-1]["grupo"] = "construcoes"
        from application.usecases.construcao.defender_construcao import (
            DefenderConstrucaoUseCase,
        )

        self.registrar_controlador_construcao(
            entidade,
            DefenderConstrucaoUseCase(self),
            morte=DestruirConstrucaoUseCase(self),
        )
        self.notificar_obstaculos_alterados()
        return entidade

    def registrar_controlador_construcao(self, construcao, padrao, morte=None):
        self.controladores[construcao] = {
            "padrao": padrao,
            "morte": morte,
            "acoes": {},
        }

    def criar_arvore_teste(self, x, y, altura=0):
        arvore = Arvore("arvore1", x, y, altura)
        arvore.corpo_rect = TestRect(x - 32, y - 48, 64, 96)
        self.adicionar(arvore, "arvores")
        return arvore

    def adicionar_efeito(self, efeito):
        self.efeitos.append(efeito)
        self.renderers.setdefault(efeito.nome.lower(), _TraceRenderer(efeito.nome))
        return efeito

    def remover_personagem(self, entidade, ignorar=None):
        for grupo in (
            "arvores",
            "personagens",
            "personagens_hostis",
            "construcoes",
            "construcoes_hostis",
        ):
            lista = getattr(self, grupo, [])
            if entidade in lista:
                lista.remove(entidade)
        self.entidades = [x for x in self.entidades if x["entidade"] is not entidade]
        self._registro_entidades.pop(entidade, None)
        self.indice_espacial.remover(entidade)
        for alvo in list(self._registro_entidades):
            self.remover_atacante(alvo, entidade)
        self.controladores.pop(entidade, None)

    def parar_acao_global(self, entidade, ignorar=None):
        for ctrl in self.controladores.values():
            for acao in ctrl.get("acoes", {}).values():
                usecase = acao.get("usecase")
                if (
                    getattr(usecase, "entidade_alvo", None) is entidade
                    and getattr(usecase, "personagem", None) is not ignorar
                ):
                    # O usecase de corte administra sozinho a troca para a
                    # próxima árvore. Não interrompa os outros cortadores.
                    if usecase.__class__.__name__ == "CortarArvoreUseCase":
                        continue

                    cancelar = getattr(usecase, "cancelar", None)
                    if cancelar:
                        cancelar()
                    else:
                        usecase.entidade_alvo = None

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
        self.navegacao.notificar_obstaculos_alterados()

    def carregar_entidade(self, tipo, x=None, y=None):
        if tipo != "madeira":
            raise ValueError(f"tipo não suportado pelo runtime de integração: {tipo}")
        from domains.personagem.entity import criar_recurso

        recurso = criar_recurso(tipo, x or 0, y or 0, 0)
        self.adicionar(recurso, "recursos")
        return recurso

    def adicionar_estoque(self, tipo, quantidade=1):
        self.estoque[tipo] += quantidade

    def obter_posicao_proxima_construcao(self, construcao):
        return construcao.x + 72, construcao.y


def snapshot_visual_entity(entidade, faccao=None):
    """Estado visual mínimo do personagem/objeto exatamente no instante do trace."""
    estado = "ocioso"
    frame = 0
    flip = False
    animacoes = getattr(entidade, "animacoes", None)
    if animacoes is not None:
        try:
            estado, frame = animacoes.obter_selecao_frame()
        except Exception:
            estado = getattr(getattr(animacoes, "estado", None), "name", "ocioso")
            frame = 0
        maquina = getattr(animacoes, "maquina", None)
        flip = bool(getattr(maquina, "flip", False))
    dados = {
        "nome": getattr(entidade, "nome", "desconhecido"),
        "x": float(getattr(entidade, "x", 0)),
        "y": float(getattr(entidade, "y", 0)),
        "altura": int(getattr(entidade, "altura", 0)),
        "vida": float(getattr(entidade, "vida", 0)),
        "vida_maxima": float(
            getattr(entidade, "VIDA_MAXIMA", getattr(entidade, "vida", 0))
        ),
        "estado": str(estado),
        "frame": int(frame),
        "flip": flip,
    }
    if faccao is not None:
        dados["faccao"] = faccao
    return dados


def snapshot_efeito(efeito):
    estado, frame = efeito.animacoes.obter_selecao_frame()
    return {
        "nome": getattr(efeito, "nome", "efeito"),
        "x": float(getattr(efeito, "x", 0)),
        "y": float(getattr(efeito, "y", 0)),
        "estado": str(estado),
        "frame": int(frame),
        "escala_x": float(getattr(efeito, "escala_x", 1.0)),
        "escala_y": float(getattr(efeito, "escala_y", 1.0)),
        "persistente": bool(getattr(efeito, "persistente", False)),
    }


def snapshot_construcao(entidade, faccao=None, tamanho=None):
    dados = snapshot_visual_entity(entidade, faccao=faccao)
    if tamanho is not None:
        dados["size"] = tamanho
    dados["vida_inicial"] = float(
        getattr(entidade, "VIDA_MAXIMA", getattr(entidade, "vida", 0))
    )
    return dados


def ponto_tile(cenario, coluna, linha):
    x, y = cenario.tilemap_renderer.tile_para_pixel(coluna, linha)
    return x + 32, y + 32


def ponto_degrau(cenario):
    coluna, linha = next(iter(cenario.tilemap_renderer.degraus))
    return coluna, linha, ponto_tile(cenario, coluna, linha)
