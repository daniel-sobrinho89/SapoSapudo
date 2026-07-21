from domains.aldeao.animacoes import AnimacoesAldeao


class Aldeao:
    def __init__(self, transform):
        self.transform = transform
        self.x = 300
        self.y = 350
        self.animacoes = AnimacoesAldeao()
        self.selecionado = False
        self.destino_x = self.x

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)
