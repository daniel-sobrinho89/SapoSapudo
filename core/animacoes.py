import json

from core.animacao_movimento import AnimacaoMovimento
from domains.arvore.maquina_estado import MaquinaEstadoArvore
from domains.construcao.maquina_estado import MaquinaEstadoConstrucao
from domains.ouro.maquina_estado import MaquinaEstadoOuro
from domains.personagem.maquina_estado import MaquinaEstadoAldeao
from domains.personagem.maquina_estado_goblin_tocha import MaquinaEstadoGoblinTocha
from domains.personagem.maquina_estado_ovelha import MaquinaEstadoOvelha
from domains.personagem.maquina_estado_sapudo import MaquinaEstadoSapudo
from domains.personagem.maquina_estado_soldado import MaquinaEstadoSoldado
from domains.recursos.maquina_estado import MaquinaEstadoRecurso
from utils.paths import BASE_DIR

MAQUINAS = {
    "MaquinaEstadoAldeao": MaquinaEstadoAldeao,
    "MaquinaEstadoSoldado": MaquinaEstadoSoldado,
    "MaquinaEstadoGoblinTocha": MaquinaEstadoGoblinTocha,
    "MaquinaEstadoArvore": MaquinaEstadoArvore,
    "MaquinaEstadoConstrucao": MaquinaEstadoConstrucao,
    "MaquinaEstadoOuro": MaquinaEstadoOuro,
    "MaquinaEstadoOvelha": MaquinaEstadoOvelha,
    "MaquinaEstadoRecurso": MaquinaEstadoRecurso,
    "MaquinaEstadoSapudo": MaquinaEstadoSapudo,
}


class Animacoes:
    with open(BASE_DIR / "data/sprites_config.json", encoding="utf8") as f:
        CONFIG = json.load(f)

    def __init__(self, tipo):
        config = self.CONFIG[tipo.lower()]
        self._estado_anterior = None

        self.maquina = MAQUINAS[config["maquina"]]()

        self.animacoes = {
            nome: AnimacaoMovimento(
                dados["frames"],
                dados["tempo"],
            )
            for nome, dados in config["animacoes"].items()
        }

        for nome, animacao in self.animacoes.items():
            setattr(self, nome, animacao)

    @property
    def estado(self):
        return self.maquina.estado

    @estado.setter
    def estado(self, valor):
        self.maquina.trocar(valor)

    @property
    def animacao_atual(self):
        estado = self.maquina.estado.name.lower()

        nome_animacao = estado.replace("_flip", "")

        return self.animacoes.get(
            nome_animacao,
            self.animacoes["ocioso"],
        )

    def atualizar(self, dt):
        self.maquina.atualizar(dt)

        estado = self.maquina.estado.name.lower()
        estado_animacao = estado.replace("_flip", "")

        animacao = self.animacoes.get(estado_animacao)

        if not animacao:
            return

        if estado_animacao != self._estado_anterior:
            animacao.reset()
            self._estado_anterior = estado_animacao
            return False

        return animacao.atualizar(dt)

    def reset(self):
        estado = self.maquina.estado.name.lower()
        estado_animacao = estado.replace("_flip", "")

        animacao = self.animacoes.get(estado_animacao)

        if not animacao:
            return

        animacao.reset()

    def obter_selecao_frame(self):
        estado = self.maquina.estado.name.lower()

        nome_animacao = estado.replace("_flip", "")

        animacao = self.animacoes.get(
            nome_animacao,
            self.animacoes["ocioso"],
        )

        return estado, animacao.frame
