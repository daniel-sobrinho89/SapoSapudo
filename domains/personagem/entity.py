from core.animacoes import Animacoes
from domains.arvore.entity import Arvore
from domains.ouro.entity import MinaOuro
from domains.recursos.entity import Recurso
from utils.config import TILE_SIZE


class Personagem:
    VIDA_MAXIMA = 40
    VIDA_MINIMA = 30
    TEMPO_EXIBIR_BARRA_VIDA = 3.0

    def __init__(
        self, nome, x, y, altura, vida, ataque, defesa, madeira=0, ouro=0, carne=0
    ):
        self.nome = nome
        self.x = x
        self.y = y
        self.altura = altura
        self.VIDA_MAXIMA = vida
        self.ataque = ataque
        self.defesa = defesa
        self.custo_carne = carne
        self.custo_ouro = ouro
        self.custo_madeira = madeira
        self.animacoes = Animacoes(nome)

        self.base_x = x
        self.base_y = y
        # Raio da área de movimentação livre, em tiles.
        # O centro muda somente quando o personagem recebe uma nova ordem
        # (movimento, ataque ou coleta). Animais não usam este comportamento.
        self.base_raio = 4

        self.vida = self.VIDA_MAXIMA
        self.corpo_rect = None
        self.selecionado = False
        self.destino_x = self.x
        self.destino_y = self.y
        self.construcao_selecionada = None
        self.tempo_barra_vida = 0.0

    def definir_base_movimento(self, x, y):
        """Define o centro da área de movimentação autônoma do personagem."""
        self.base_x = x
        self.base_y = y

    @property
    def raio_movimento_livre(self):
        return self.base_raio * TILE_SIZE

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)
        self.tempo_barra_vida = max(0.0, self.tempo_barra_vida - dt)

    def receber_golpe(
        self,
        atacante,
        destino_x,
        destino_y,
    ):
        if self.vida <= 0:
            return

        dano = max(1, atacante.ataque - self.defesa)
        self.vida = max(0, self.vida - dano)
        self.tempo_barra_vida = self.TEMPO_EXIBIR_BARRA_VIDA

        if self.vida < self.VIDA_MINIMA or self.ataque == 0:
            self.destino_x = destino_x
            self.destino_y = destino_y

            estado = self.animacoes.estado.__class__

            if atacante.x < self.x:
                self.animacoes.estado = estado.CORRENDO
            else:
                self.animacoes.estado = estado.CORRENDO_FLIP


def criar_entidade(
    nome,
    x=0,
    y=0,
    altura=0,
    vida=0,
    ataque=0,
    defesa=0,
    madeira=0,
    ouro=0,
    carne=0,
):
    return Personagem(
        nome,
        x,
        y,
        altura,
        vida,
        ataque,
        defesa,
        madeira=madeira,
        ouro=ouro,
        carne=carne,
    )


def criar_arvore(nome, x=400, y=450, altura=0, vida=0, ataque=0, defesa=0):
    return Arvore(nome, x=x, y=y, altura=altura)


def criar_mina_ouro(nome, x=400, y=450, altura=0, vida=0, ataque=0, defesa=0):
    return MinaOuro(nome, x=x, y=y, altura=altura)


def criar_recurso(nome, x=400, y=450, altura=0, vida=0, ataque=0, defesa=0):
    return Recurso(nome, x=x, y=y, altura=altura)
