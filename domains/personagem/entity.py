from core.animacoes import Animacoes


class Personagem:
    def __init__(self, nome="Aldeao", madeira=0, ouro=0, carne=0, x=400, y=450):
        self.x = x
        self.y = y
        self.animacoes = Animacoes(nome)
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
        self.vida = 1000

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)

    def receber_golpe(
        self,
        atacante_x,
        destino_x,
        destino_y,
    ):
        if self.vida <= 0:
            return

        self.vida -= 1

        if self.vida < 300:
            self.destino_x = destino_x
            self.destino_y = destino_y

            estado = self.animacoes.estado.__class__

            if atacante_x < self.x:
                self.animacoes.estado = estado.CORRENDO
            else:
                self.animacoes.estado = estado.CORRENDO_FLIP


def criar_personagem(nome, x=400, y=450):
    if nome == "Aldeao":
        return criar_aldeao()
    elif nome == "Soldado":
        return criar_soldado()
    elif nome == "Goblin_Tocha":
        return criar_goblin_tocha(x, y)


def criar_aldeao():
    return Personagem(
        "Aldeao",
        carne=0,
    )


def criar_soldado():
    return Personagem(
        "Soldado",
        carne=0,
    )


def criar_goblin_tocha(x=400, y=450):
    return Personagem("Goblin_Tocha", carne=0, x=x, y=y)
