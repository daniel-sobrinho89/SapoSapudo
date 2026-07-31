from core.animacoes import Animacoes


class Efeitos:
    def __init__(self, nome, madeira=0, ouro=0, carne=0):
        self.nome = nome

        self.animacoes = Animacoes(nome)
        self.corpo_rect = None
        self.x = 0
        self.y = 0
        self.escala_x = 1.0
        self.escala_y = 1.0
        self.inicio_x = 0
        self.deslocamento_x = 0
        self.vida = 0

        self.custo_carne = carne
        self.custo_ouro = ouro
        self.custo_madeira = madeira

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)


def criar_efeitos(nome):
    if nome == "poeira_grande":
        return criar_poeira_grande()
    elif nome == "barra_vida":
        return criar_barra_vida()
    elif nome == "barra_vida_base":
        return criar_barra_vida_base()
    elif nome == "avatar_aldeao":
        return criar_avatar_aldeao()
    elif nome == "avatar_soldado":
        return criar_avatar_soldado()
    elif nome == "fogo1":
        return criar_fogo1()
    elif nome == "fogo2":
        return criar_fogo2()


def criar_poeira_grande():
    return Efeitos("poeira_grande")


def criar_fogo1():
    return Efeitos("fogo1")


def criar_fogo2():
    return Efeitos("fogo2")


def criar_barra_vida():
    return Efeitos("barra_vida")


def criar_barra_vida_base():
    return Efeitos("barra_vida_base")


def criar_avatar_aldeao():
    return Efeitos(
        "avatar_aldeao",
        carne=0,
    )


def criar_avatar_soldado():
    return Efeitos(
        "avatar_soldado",
        carne=0,
    )
