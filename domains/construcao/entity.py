from domains.construcao.animacoes import AnimacoesConstrucao


class Construcao:
    def __init__(
        self,
        nome,
        madeira,
        ouro,
        carne=0,
    ):
        self.nome = nome

        self.custo_madeira = madeira
        self.custo_ouro = ouro
        self.custo_carne = carne
        self.animacoes = AnimacoesConstrucao()
        self.corpo_rect = None
        self.x = 0
        self.y = 0
        self.menu_aberto = False

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)


def criar_construcao(nome):
    if nome == "Castelo":
        return criar_castelo()
    elif nome == "Casa":
        return criar_casa()
    elif nome == "Quartel":
        return criar_quartel()


def criar_castelo():
    return Construcao(
        "Castelo",
        madeira=30,
        ouro=50,
    )


def criar_casa():
    return Construcao(
        "Casa",
        madeira=10,
        ouro=0,
    )


def criar_quartel():
    return Construcao(
        "Quartel",
        madeira=0,
        ouro=0,
    )


# def criar_quartel():
#     return Construcao(
#         "Quartel",
#         madeira=20,
#         ouro=10,
#     )
