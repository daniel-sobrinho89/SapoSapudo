from core.animacoes import Animacoes
from domains.arvore.entity import Arvore
from domains.ouro.entity import MinaOuro
from domains.ovelha.entity import Ovelha
from domains.recursos.entity import Recurso


class Personagem:
    VIDA_MAXIMA = 40
    TEMPO_EXIBIR_BARRA_VIDA = 3.0

    def __init__(self, nome="Aldeao", madeira=0, ouro=0, carne=0, x=400, y=450):
        self.x = x
        self.y = y
        self.animacoes = Animacoes(nome)
        self.controlador = None
        self.corpo_rect = None
        self.selecionado = False
        self.destino_x = self.x
        self.construcao_selecionada = None
        self.custo_carne = carne
        self.custo_ouro = ouro
        self.custo_madeira = madeira
        self.nome = nome
        self.vida = self.VIDA_MAXIMA
        self.fugindo = False
        self.tempo_barra_vida = 0.0

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)
        self.tempo_barra_vida = max(0.0, self.tempo_barra_vida - dt)

    def receber_golpe(
        self,
        atacante_x,
        destino_x,
        destino_y,
    ):
        if self.vida <= 0:
            return

        self.vida -= 1
        self.tempo_barra_vida = self.TEMPO_EXIBIR_BARRA_VIDA

        if self.vida < 20:
            self.fugindo = True
            self.destino_x = destino_x
            self.destino_y = destino_y

            estado = self.animacoes.estado.__class__

            if atacante_x < self.x:
                self.animacoes.estado = estado.CORRENDO
            else:
                self.animacoes.estado = estado.CORRENDO_FLIP


def criar_personagem(nome, x=400, y=450):
    if nome == "aldeao":
        return criar_aldeao(x, y)
    elif nome == "soldado":
        return criar_soldado(x, y)
    elif nome == "goblin_Tocha":
        return criar_goblin_tocha(x, y)


def criar_aldeao(nome, x=400, y=450):
    return Personagem(nome, carne=0, x=x, y=y)


def criar_soldado(nome, x=400, y=450):
    return Personagem(nome, carne=0, x=x, y=y)


def criar_goblin_tocha(nome, x=400, y=450):
    return Personagem(nome, carne=0, x=x, y=y)


def criar_ovelha(nome, x=400, y=450):
    return Ovelha(nome, x=x, y=y)


def criar_arvore(nome, x=400, y=450):
    return Arvore(nome, x=x, y=y)


def criar_mina_ouro(nome, x=400, y=450):
    return MinaOuro(nome, x=x, y=y)


def criar_recurso(nome, x=400, y=450):
    return Recurso(nome, x=x, y=y)
