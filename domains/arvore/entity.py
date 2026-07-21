from domains.arvore.animacoes import AnimacoesArvore
from domains.arvore.maquina_estado import EstadoArvore


class Arvore:
    def __init__(self, transform, x, y):
        self.transform = transform
        self.x = x
        self.y = y
        self.animacoes = AnimacoesArvore()
        self.madeira = 4

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)

    def obter_madeira(self):
        self.madeira -= 1
        if self.madeira == 0:
            self.animacoes.estado = EstadoArvore.CORTADA
