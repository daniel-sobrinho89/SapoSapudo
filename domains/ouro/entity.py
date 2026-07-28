from core.animacoes import Animacoes
from domains.ouro.maquina_estado import EstadoOuro


class MinaOuro:
    def __init__(self, nome, x, y):
        self.nome = nome
        self.x = x
        self.y = y
        self.animacoes = Animacoes(nome)
        self.minerio = 24
        self.vida = 24

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)

    def obter_ouro(self):
        self.minerio -= 1
        if self.minerio == 20:
            self.animacoes.estado = EstadoOuro.NIVEL_OURO5
        elif self.minerio == 16:
            self.animacoes.estado = EstadoOuro.NIVEL_OURO4
        elif self.minerio == 12:
            self.animacoes.estado = EstadoOuro.NIVEL_OURO3
        elif self.minerio == 8:
            self.animacoes.estado = EstadoOuro.NIVEL_OURO2
        elif self.minerio == 4:
            self.animacoes.estado = EstadoOuro.NIVEL_OURO1
        elif self.minerio == 0:
            self.animacoes.estado = EstadoOuro.OBTIDO
