from core.animacoes import Animacoes


class Construcao:
    VIDA_MAXIMA = 500
    TEMPO_EXIBIR_BARRA_VIDA = 3.0

    def __init__(self, nome, x, y, altura, vida, madeira, ouro, carne):
        self.nome = nome
        self.x = x
        self.y = y
        self.altura = altura
        self.VIDA_MAXIMA = vida
        self.custo_madeira = madeira
        self.custo_ouro = ouro
        self.custo_carne = carne
        self.animacoes = Animacoes(nome)
        self.corpo_rect = None
        self.vida = self.VIDA_MAXIMA

        self.tempo_barra_vida = 0.0

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)
        self.tempo_barra_vida = max(0.0, self.tempo_barra_vida - dt)

    def receber_golpe(self):
        if self.vida <= 0:
            return

        self.vida -= 1
        self.tempo_barra_vida = self.TEMPO_EXIBIR_BARRA_VIDA


def criar_construcao(
    nome, x=0, y=0, altura=0, vida=0, ataque=0, defesa=0, madeira=0, ouro=0, carne=0
):
    return Construcao(nome, x, y, altura, vida, madeira, ouro, carne)
