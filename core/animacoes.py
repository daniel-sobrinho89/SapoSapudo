import json
import sys

from core.animacao_movimento import AnimacaoMovimento
from utils.paths import BASE_DIR


class EstadoAnimacaoCompat:
    """Representação legada do estado visual, sem depender de um Enum de domínio."""

    def __init__(self, valor):
        self.value = getattr(valor, "value", valor)
        self.name = str(self.value).upper().replace("_", "_")

    def __eq__(self, other):
        return str(self.value).lower() == str(getattr(other, "value", other)).lower()

    def __hash__(self):
        return hash(str(self.value).lower())

    def __repr__(self):
        return f"EstadoAnimacaoCompat({self.value!r})"


class Animacoes:
    """Controlador declarativo de animações baseado em sprites_config.json.

    A configuração continua sendo a fonte de verdade dos sprites. Nenhuma
    máquina de estado concreta do domínio é importada aqui.
    """

    with open(BASE_DIR / "data/sprites_config.json", encoding="utf8") as f:
        CONFIG = json.load(f)

    def __init__(self, tipo):
        config = self.CONFIG[tipo.lower()]
        self._estado_anterior = None
        self._tipo = tipo.lower()

        self._estado = "ocioso"
        multiplicador_web = 0.65 if sys.platform == "emscripten" else 1.0

        self.animacoes = {
            nome: AnimacaoMovimento(
                dados["frames"],
                dados["tempo"] * multiplicador_web,
            )
            for nome, dados in config["animacoes"].items()
        }

        for nome, animacao in self.animacoes.items():
            setattr(self, nome, animacao)

    @property
    def estado(self):
        return EstadoAnimacaoCompat(self._estado)

    @estado.setter
    def estado(self, valor):
        valor = getattr(valor, "value", valor)
        self._estado = str(valor).lower()

    @property
    def flip(self):
        return str(self._estado).endswith("_flip")

    def definir(self, nome_animacao, flip=None):
        """Seleciona uma animação declarativamente.

        Mantém uma API sem dependência de Enums concretos. ``flip`` pode ser
        omitido para preservar a direção atual.
        """
        nome = str(nome_animacao).lower()
        if nome.endswith("_flip"):
            nome = nome[:-5]
            flip = True

        if nome not in self.animacoes:
            nome = "ocioso"

        if flip is None:
            flip = self.flip

        estado = nome + ("_flip" if flip else "")
        self._estado = estado
        return self.estado

    @property
    def nome_animacao_atual(self):
        nome = self._estado
        return nome[:-5] if nome.endswith("_flip") else nome

    def esta_em(self, nome_animacao):
        nome = str(nome_animacao).lower()
        if nome.endswith("_flip"):
            nome = nome[:-5]
        return self.nome_animacao_atual == nome

    def definir_flip(self, flip):
        return self.definir(self.nome_animacao_atual, flip=flip)

    def flip_para_direcao(self, dx):
        if dx == 0:
            return self.flip
        return dx < 0

    def definir_por_direcao(self, nome_animacao, dx):
        """Seleciona uma animação respeitando a convenção visual do personagem."""
        return self.definir(
            nome_animacao,
            flip=self.flip_para_direcao(dx),
        )

    def definir_por_movimento(self, nome_animacao, deslocamento_x):
        """Atualiza a orientação usando exclusivamente o deslocamento real."""
        return self.definir_por_direcao(nome_animacao, deslocamento_x)

    @property
    def animacao_atual(self):
        nome_animacao = self.nome_animacao_atual
        return self.animacoes.get(
            nome_animacao,
            self.animacoes.get("ocioso"),
        )

    def _nome_base_animacao_atual(self):
        """Retorna o nome da animação sem o sufixo visual de flip."""
        nome = str(self._estado).lower()
        return nome[:-5] if nome.endswith("_flip") else nome

    def _animacao_logica_atual(self):
        """Obtém o controlador temporal da animação sem depender do flip.

        O flip é uma característica de apresentação. Não existe uma segunda
        instância de ``AnimacaoMovimento`` para ``correndo_flip`` ou
        ``atacando_flip``: ambas devem avançar o mesmo controlador temporal da
        animação base.
        """
        nome_base = self._nome_base_animacao_atual()
        return self.animacoes.get(nome_base, self.animacoes.get("ocioso"))

    def atualizar(self, dt):
        animacao = self._animacao_logica_atual()

        if not animacao:
            return

        estado_animacao = self._estado
        if estado_animacao != self._estado_anterior:
            animacao.reset()
            self._estado_anterior = estado_animacao
            return False

        return animacao.atualizar(dt)

    def reset(self):
        animacao = self._animacao_logica_atual()
        if not animacao:
            return
        animacao.reset()

    def obter_selecao_frame(self):
        estado = self._estado
        animacao = self._animacao_logica_atual()
        return estado, animacao.frame
