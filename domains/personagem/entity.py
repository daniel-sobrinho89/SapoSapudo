import random

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
        # Progressão exclusiva do protagonista. Nos demais personagens esses
        # campos permanecem inertes, mas manter o contrato uniforme simplifica
        # HUD e save/load futuros.
        self.experiencia = 0
        self.experiencia_total = 0
        self.nivel = 1
        self.pontos_evolucao = 0
        self.xp_recompensa = 0
        self.xp_missao_id = None
        self.xp_recompensada = False
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
        self.visivel = True
        self.destino_x = self.x
        self.destino_y = self.y
        self.construcao_selecionada = None
        self.tempo_barra_vida = 0.0
        self.ultimo_direcao_x = 1
        self.ultimo_direcao_y = 0
        self.defesa_ativa = False
        self.perfect_block = False
        self._tempo_defesa_esqueleto = 0.0
        self._cooldown_defesa_esqueleto = 0.0
        self._ultima_defesa_esqueleto = False
        self._agressor_pendente = None

    def definir_base_movimento(self, x, y):
        self.base_x = x
        self.base_y = y

    @property
    def raio_movimento_livre(self):
        return self.base_raio * TILE_SIZE

    @property
    def flip(self):
        return bool(getattr(self.animacoes, "flip", False))

    @flip.setter
    def flip(self, valor):
        definir_flip = getattr(self.animacoes, "definir_flip", None)
        if callable(definir_flip):
            definir_flip(bool(valor))

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)
        self.tempo_barra_vida = max(0.0, self.tempo_barra_vida - dt)

        if self.nome == "esqueleto":
            self._cooldown_defesa_esqueleto = max(
                0.0, self._cooldown_defesa_esqueleto - dt
            )
            if self.defesa_ativa:
                self._tempo_defesa_esqueleto = max(
                    0.0, self._tempo_defesa_esqueleto - dt
                )
                if self._tempo_defesa_esqueleto <= 0.0:
                    self.defesa_ativa = False
                    self.animacoes.definir("ocioso", flip=self.animacoes.flip)

    def receber_golpe(
        self,
        atacante,
        destino_x,
        destino_y,
    ):
        if self.vida <= 0:
            return

        if self.nome in {"esqueleto", "cobra"}:
            # Toda agressão gera uma intenção explícita de combate.
            # O coordenador consumirá esta intenção antes da IA autônoma.
            self._agressor_pendente = atacante

            # Somente a caveira possui animação/estado de defesa. A cobra usa
            # a mesma máquina de estados por compatibilidade, mas seu
            # sprites_config não possui "defendendo". Colocá-la nesse estado
            # fazia a animação parecer congelada depois de um ataque.
            if self.nome == "esqueleto":
                esta_atacando = (
                    self.animacoes.esta_em("atacando")
                    or self.animacoes.esta_em("atacando1")
                    or self.animacoes.esta_em("atacando2")
                )
                if (
                    esta_atacando
                    and not self.defesa_ativa
                    and self._cooldown_defesa_esqueleto <= 0.0
                    and random.random() < 0.28
                ):
                    self.defesa_ativa = True
                    self.perfect_block = False
                    self._ultima_defesa_esqueleto = True
                    self._tempo_defesa_esqueleto = 0.70
                    self._cooldown_defesa_esqueleto = 2.2
                    self.animacoes.definir("defendendo", flip=self.animacoes.flip)
                else:
                    self._ultima_defesa_esqueleto = False
            else:
                self._ultima_defesa_esqueleto = False

        dano_base = max(1, atacante.ataque - self.defesa)
        dano = dano_base
        if self.defesa_ativa:
            if self.perfect_block:
                dano = max(1, int(round(dano_base * 0.20)))
                self.ultimo_perfect_block = True
            else:
                dano = max(1, int(round(dano_base * 0.35)))
                self.ultimo_perfect_block = False
        else:
            self.ultimo_perfect_block = False

        self.vida = max(0, self.vida - dano)
        self.tempo_barra_vida = self.TEMPO_EXIBIR_BARRA_VIDA


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
