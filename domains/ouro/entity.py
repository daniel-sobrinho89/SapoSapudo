from core.animacoes import Animacoes
from domains.ouro.maquina_estado import EstadoOuro


class MinaOuro:
    OURO_MAXIMO = 65

    def __init__(self, nome, x, y, altura):
        self.nome = nome
        self.x = x
        self.y = y
        self.altura = altura
        self.corpo_rect = None

        self.animacoes = Animacoes(nome)

        self.minerio = self.OURO_MAXIMO
        self.vida = self.OURO_MAXIMO

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)

    def obter_ouro(self):
        if self.minerio <= 0:
            return 0

        self.minerio -= 1
        self._atualizar_estado()

        return 1

    def _atualizar_estado(self):
        if self.minerio <= 0:
            self.animacoes.estado = EstadoOuro.OBTIDO
        elif self.minerio <= 13:
            self.animacoes.estado = EstadoOuro.NIVEL_OURO1
        elif self.minerio <= 26:
            self.animacoes.estado = EstadoOuro.NIVEL_OURO2
        elif self.minerio <= 39:
            self.animacoes.estado = EstadoOuro.NIVEL_OURO3
        elif self.minerio <= 52:
            self.animacoes.estado = EstadoOuro.NIVEL_OURO4
        else:
            self.animacoes.estado = EstadoOuro.NIVEL_OURO5
