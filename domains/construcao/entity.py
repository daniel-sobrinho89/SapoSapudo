from core.animacoes import Animacoes


class Construcao:
    def __init__(self, nome, madeira=0, ouro=0, carne=0, x=0, y=0):
        self.nome = nome

        self.custo_madeira = madeira
        self.custo_ouro = ouro
        self.custo_carne = carne
        self.animacoes = Animacoes(nome)
        self.corpo_rect = None
        self.x = x
        self.y = y
        self.vida = 1000

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)


def criar_construcao(nome, x=0, y=0):
    if nome == "castelo":
        return criar_castelo(nome, x, y)
    elif nome == "casa":
        return criar_casa(nome, x, y)
    elif nome == "quartel":
        return criar_quartel(nome, x, y)
    elif nome == "casa_goblin":
        return criar_casa_goblin(nome, x, y)


def criar_castelo(nome, x=0, y=0):
    return Construcao(nome, madeira=0, ouro=0, x=x, y=y)


def criar_casa(nome, x=0, y=0):
    return Construcao(nome, madeira=0, ouro=0, x=x, y=y)


def criar_casa_goblin(nome, x=0, y=0):
    return Construcao(nome, x=x, y=y)


def criar_quartel(nome, x=0, y=0):
    return Construcao(
        nome,
        madeira=0,
        ouro=0,
        x=x,
    )
