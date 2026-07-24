from domains.personagem.animacoes import AnimacoesPersonagem


class Personagem:
    def __init__(
        self,
        nome="Aldeao",
        madeira=0,
        ouro=0,
        carne=0,
    ):
        self.x = 400
        self.y = 450
        self.animacoes = AnimacoesPersonagem(nome)
        self.controlador = None
        self.corpo_rect = None
        self.selecionado = False
        self.destino_x = self.x
        self.menu_construcoes_aberto = False
        self.construcao_selecionada = None
        self.custo_carne = carne
        self.custo_ouro = ouro
        self.custo_madeira = madeira
        self.nome = nome

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)


def criar_personagem(nome):
    if nome == "Aldeao":
        return criar_aldeao()
    elif nome == "Soldado":
        return criar_soldado()


def criar_aldeao():
    return Personagem(
        "Aldeao",
        carne=5,
    )


def criar_soldado():
    return Personagem(
        "Soldado",
        carne=0,
    )
