from core.animacao import Animacao
from domains.personagem.maquina_estado import MaquinaEstadoAldeao
from domains.personagem.maquina_estado_soldado import MaquinaEstadoSoldado

CONFIG = {
    "Aldeao": {
        "maquina": MaquinaEstadoAldeao,
        "animacoes": {
            "ocioso": (8, 0.20),
            "ocioso_flip": (8, 0.20),
            "ocioso_madeira": (8, 0.15),
            "ocioso_madeira_flip": (8, 0.15),
            "correndo": (6, 0.15),
            "correndo_flip": (6, 0.15),
            "correndo_machado": (6, 0.15),
            "correndo_machado_flip": (6, 0.15),
            "correndo_madeira": (6, 0.15),
            "correndo_madeira_flip": (6, 0.15),
            "usando_machado": (6, 0.15),
            "usando_machado_flip": (6, 0.15),
            "correndo_picareta": (6, 0.15),
            "correndo_picareta_flip": (6, 0.15),
            "usando_picareta": (6, 0.15),
            "usando_picareta_flip": (6, 0.15),
            "correndo_ouro": (6, 0.15),
            "correndo_ouro_flip": (6, 0.15),
            "correndo_faca": (6, 0.15),
            "correndo_faca_flip": (6, 0.15),
            "usando_faca": (4, 0.15),
            "usando_faca_flip": (4, 0.15),
            "correndo_carne": (6, 0.15),
            "correndo_carne_flip": (6, 0.15),
        },
    },
    "Soldado": {
        "maquina": MaquinaEstadoSoldado,
        "animacoes": {
            "ocioso": (8, 0.20),
            "ocioso_flip": (8, 0.20),
            "correndo": (6, 0.15),
            "correndo_flip": (6, 0.15),
        },
    },
}


class AnimacoesPersonagem:
    def __init__(self, tipo):
        cfg = CONFIG[tipo]

        self.maquina = cfg["maquina"]()

        self.animacoes = {
            nome: Animacao(frames, tempo)
            for nome, (frames, tempo) in cfg["animacoes"].items()
        }

        for nome, animacao in self.animacoes.items():
            setattr(self, nome, animacao)

    @property
    def estado(self):
        return self.maquina.estado

    @estado.setter
    def estado(self, valor):
        self.maquina.trocar(valor)

    # ====================================
    # UPDATE
    # ====================================

    def atualizar(self, dt):
        self.maquina.atualizar(dt)
        self._atualizar_animacoes(dt)

    def _atualizar_animacoes(self, dt):
        estado = self.maquina.estado.name.lower()
        animacao = self.animacoes.get(estado)

        if animacao:
            animacao.atualizar(dt)

    def obter_selecao_frame(self):
        estado = self.maquina.estado.name.lower()

        animacao = self.animacoes.get(
            estado,
            self.animacoes["ocioso"],
        )

        return estado, animacao.frame
