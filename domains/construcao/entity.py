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


def criar_castelo():
    return Construcao(
        "Castelo",
        madeira=20,
        ouro=40,
    )


def criar_casa():
    return Construcao(
        "Casa",
        madeira=10,
        ouro=0,
    )
