from application.usecases.sapudo.controlar_sapudo_manual import (
    ControlarSapudoManualUseCase,
)
from core.navegacao_mapa import NavegacaoMapa
from domains.personagem.entity import Personagem


class _Nav:
    def pode_andar(self, x, y, altura):
        return True

    def fugir(self, *args):
        return args[0], args[1]


class _Conversa:
    aberta = False


class _Cenario:
    navegacao = _Nav()
    conversa_controller = _Conversa()
    personagens_hostis = []
    construcoes_hostis = []

    def obter_entidade(self, entidade):
        return {"faccao": "player"}


def _sapudo(cenario):
    sapudo = Personagem("sapudo", 100, 100, 0, 150, 5, 0)
    cenario.personagens = [sapudo]
    controle = ControlarSapudoManualUseCase(cenario)
    controle.definir_sapudo(sapudo)
    return sapudo, controle


def test_ataques_alternam_entre_1_e_2():
    cenario = _Cenario()
    sapudo, controle = _sapudo(cenario)

    controle.tecla_down("space")
    assert sapudo.animacoes.esta_em("atacando1")
    controle.atualizar(0.5)
    controle.tecla_down("space")
    assert sapudo.animacoes.esta_em("atacando2")


def test_perfect_block_reduz_mas_nao_zera_dano():
    cenario = _Cenario()
    sapudo, controle = _sapudo(cenario)
    inimigo = Personagem("soldado", 160, 100, 0, 100, 10, 0)

    sapudo.defesa_ativa = True
    sapudo.perfect_block = True
    sapudo.receber_golpe(inimigo, 0, 0)

    assert sapudo.vida == 148
    assert sapudo.vida > 0


def test_movimento_usa_wasd():
    cenario = _Cenario()
    sapudo, controle = _sapudo(cenario)
    controle.tecla_down("d")
    controle.atualizar(0.1)
    assert sapudo.x > 100
    assert sapudo.animacoes.esta_em("correndo")


def test_setas_sapudo_tem_a_direcao_visual_correta():
    cenario = _Cenario()
    sapudo, controle = _sapudo(cenario)

    controle.tecla_down("right")
    controle.atualizar(0.1)
    assert sapudo.animacoes.flip is False

    controle.tecla_up("right")
    controle.tecla_down("left")
    controle.atualizar(0.1)
    assert sapudo.animacoes.flip is True


def test_flip_sapudo_direita_e_esquerda():
    cenario = _Cenario()
    sapudo, controle = _sapudo(cenario)

    controle.tecla_down("d")
    controle.atualizar(0.1)
    assert sapudo.animacoes.flip is False
    assert sapudo.animacoes.esta_em("correndo")

    controle.tecla_up("d")
    controle.tecla_down("a")
    controle.atualizar(0.1)
    assert sapudo.animacoes.flip is True
    assert sapudo.animacoes.esta_em("correndo") and sapudo.animacoes.flip


class _NavBloqueada(_Nav):
    def pode_andar(self, x, y, altura):
        return False


def test_nao_fica_correndo_quando_bloqueado():
    cenario = _Cenario()
    cenario.navegacao = _NavBloqueada()
    sapudo, controle = _sapudo(cenario)
    controle.tecla_down("d")
    controle.atualizar(0.1)
    assert sapudo.x == 100
    assert sapudo.animacoes.esta_em("ocioso")


class _NavDegrau:
    def pode_andar(self, x, y, altura):
        # corredor baixo até x < 132, degrau em 132..140, terreno alto depois
        if x < 132:
            return altura == 0
        return altura == 1

    def obter_altura_transicao(self, x0, y0, x1, y1, altura):
        if x0 < 132 <= x1:
            return 1
        return None

    def fugir(self, *args):
        return args[0], args[1]


def test_sapudo_sobe_degrau_e_continua_no_relevo():
    cenario = _Cenario()
    cenario.navegacao = _NavDegrau()
    sapudo, controle = _sapudo(cenario)
    sapudo.x = 124
    controle.tecla_down("d")
    for _ in range(10):
        controle.atualizar(0.02)
    assert sapudo.altura == 1
    assert sapudo.x > 132


def test_defesa_q_funciona_como_alternancia():
    cenario = _Cenario()
    sapudo, controle = _sapudo(cenario)
    controle.tecla_down("q")
    controle.atualizar(0.05)
    assert sapudo.defesa_ativa
    controle.tecla_up("q")
    controle.atualizar(0.20)
    controle.tecla_down("q")
    assert not sapudo.defesa_ativa
    assert sapudo.animacoes.esta_em("ocioso")


def test_defesa_q_pode_ser_reativada_mesmo_sem_keyup():
    cenario = _Cenario()
    sapudo, controle = _sapudo(cenario)
    controle.tecla_down("q")
    assert sapudo.defesa_ativa
    controle.atualizar(0.20)
    controle.tecla_down("q")
    assert not sapudo.defesa_ativa
    controle.atualizar(0.20)
    controle.tecla_down("q")
    assert sapudo.defesa_ativa


class _TileMapDegrauReal:
    def pixel_para_tile(self, x, y):
        return (int(x // 64), int(y // 64))

    def obter_degrau(self, coluna, linha):
        if (coluna, linha) in {(1, 2), (2, 2)}:
            return {
                "direcao": "direita",
                "altura_baixa": 0,
                "altura_alta": 1,
            }
        return None

    def obter_altura(self, coluna, linha):
        return 1 if coluna >= 2 else 0


class _NavDegrauReal:
    def __init__(self):
        from core.navegacao_mapa import NavegacaoMapa

        self.tilemap = _TileMapDegrauReal()
        self.impl = NavegacaoMapa.__new__(NavegacaoMapa)
        self.impl.tilemap = self.tilemap

    def obter_altura_transicao(self, x0, y0, x1, y1, altura):
        return self.impl.obter_altura_transicao(x0, y0, x1, y1, altura)


def test_transicao_degrau_usa_a_fronteira_real_de_altura():
    nav = _NavDegrauReal()
    # 1->2 cruza de altura 0 para 1 na própria superfície do degrau.
    assert nav.obter_altura_transicao(127, 129, 129, 129, 0) == 1
    # O retorno cruza a mesma fronteira no sentido inverso.
    assert nav.obter_altura_transicao(129, 129, 127, 129, 1) == 0


def test_superficie_inteira_do_degrau_nao_alterna_altura_dentro_dela():
    class _Tilemap:
        offset_y = 0
        altura = 4
        largura = 4

        def obter_degrau(self, coluna, linha):
            if (coluna, linha) in {(1, 1), (2, 1)}:
                return {
                    "direcao": "direita",
                    "altura_baixa": 0,
                    "altura_alta": 1,
                }
            return None

        def pixel_para_tile(self, x, y):
            return int(x // 64), int(y // 64)

        def obter_altura(self, coluna, linha):
            return 1 if coluna >= 2 else 0

    tilemap = _Tilemap()
    nav = NavegacaoMapa.__new__(NavegacaoMapa)
    nav.tilemap = tilemap

    # Dentro da mesma célula da superfície não existe transição.
    assert nav.obter_altura_transicao(70, 70, 80, 80, 0) is None
    # Caminhar dentro da parte baixa da escada também não troca altura.
    assert nav.obter_altura_transicao(80, 90, 120, 90, 0) is None
    # A troca ocorre apenas na fronteira entre as células de alturas diferentes.
    assert nav.obter_altura_transicao(127, 90, 129, 90, 0) == 1
    assert nav.obter_altura_transicao(129, 90, 127, 90, 1) == 0


def test_space_mantido_encadeia_ataques_sem_novo_keydown():
    cenario = _Cenario()
    sapudo, controle = _sapudo(cenario)

    controle.tecla_down("space")
    assert sapudo.animacoes.esta_em("atacando1")

    # A tecla continua pressionada. O fim do primeiro ataque deve iniciar
    # automaticamente o segundo, sem depender de outro KEYDOWN.
    controle.atualizar(0.48)
    assert sapudo.animacoes.esta_em("atacando2")

    # E o terceiro golpe deve voltar ao ataque 1.
    controle.atualizar(0.48)
    assert sapudo.animacoes.esta_em("atacando1")

    controle.tecla_up("space")
    controle.atualizar(0.48)
    assert not controle.ataque_em_andamento


def test_mapa1_define_tres_esqueletos_e_ossos_na_area_inferior():
    from core.world.loader import WorldLoader

    world = WorldLoader().carregar()
    esqueletos = world.obter_spawns_tipo("esqueleto")
    ossos = [
        spawn
        for spawn in world.spawns.values()
        if spawn.tipo in {"osso1", "osso2", "osso3"}
    ]

    assert len(esqueletos) == 3
    assert all(spawn.posicao.y >= 900 for spawn in esqueletos)
    assert len(ossos) >= 6
