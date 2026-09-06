import sys
from pathlib import Path

from core.save_game import SaveGameManager

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class FakeAnim:
    flip = False


class FakeUC:
    def __init__(self, target, cenario):
        self.entidade_alvo = target
        self.cenario_principal = cenario
        self.tempo = 0.21
        self.tempo_apos_golpe = 0.0
        self.busca_automatica_bloqueada = False


class E:
    def __init__(self, nome, x, y):
        self.nome = nome
        self.x = x
        self.y = y
        self.vida = 100
        self.altura = 1
        self.visivel = True
        self.save_id = None
        self.persistencia_dinamica = True
        self.animacoes = FakeAnim()


class C:
    pass


def test_save_registra_urso_perseguindo_sapudo():
    c = C()
    c._proximo_save_id = 1
    c.sapudo = E("sapudo", 300, 300)
    urso = E("urso", 200, 300)
    c.personagens_hostis = [urso]
    c.personagens = [c.sapudo]
    c.ovelhas = []
    c.construcoes = []
    c.construcoes_hostis = []
    c.arvores = []
    c.minas_ouro = []
    c.recursos = []
    c.efeitos = []
    c.flora = []
    c.controladores = {urso: {"acoes": {"atacar": {"usecase": FakeUC(c.sapudo, c)}}}}
    c.world_context = None
    c.estoque = {}
    c.ciclo_dia_noite = type("H", (), {"hora": 20.0})()
    c.camera = type("Cam", (), {"x": 0, "y": 0})()
    c.conversa_controller = None
    d = SaveGameManager(c)._coletar()
    assert d["perseguicao_urso"]["alvo"] == c.sapudo.save_id
    assert d["perseguicao_urso"]["urso"] == urso.save_id
