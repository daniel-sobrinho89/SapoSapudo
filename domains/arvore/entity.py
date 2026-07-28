from core.animacoes import Animacoes
from domains.arvore.maquina_estado import EstadoArvore


class Arvore:
    def __init__(self, nome, x, y):
        self.nome = nome
        self.x = x
        self.y = y
        self.animacoes = Animacoes(nome)
        self.madeira = 8
        self.vida = 8

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)

    def obter_madeira(self):
        self.madeira -= 1
        if self.madeira == 0:
            self.animacoes.estado = EstadoArvore.CORTADA
