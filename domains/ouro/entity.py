from core.animacoes import Animacoes
from domains.ouro.maquina_estado import EstadoOuro


class Ouro:
    def __init__(self, transform, x, y, nome):
        self.nome = nome
        self.transform = transform
        self.x = x
        self.y = y
        self.animacoes = Animacoes(nome)
        self.mineiro = 24

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)

    def obter_ouro(self):
        self.mineiro -= 1
        if self.mineiro == 20:
            self.animacoes.estado = EstadoOuro.NIVEL_OURO5
        elif self.mineiro == 16:
            self.animacoes.estado = EstadoOuro.NIVEL_OURO4
        elif self.mineiro == 12:
            self.animacoes.estado = EstadoOuro.NIVEL_OURO3
        elif self.mineiro == 8:
            self.animacoes.estado = EstadoOuro.NIVEL_OURO2
        elif self.mineiro == 4:
            self.animacoes.estado = EstadoOuro.NIVEL_OURO1
        elif self.mineiro == 0:
            self.animacoes.estado = EstadoOuro.OBTIDO
