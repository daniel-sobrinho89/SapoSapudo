from types import SimpleNamespace

from core.save_game import SaveGameManager


class FakeCiclo:
    hora = 2.5


class FakeCenario:
    def __init__(self):
        self.ciclo_dia_noite = FakeCiclo()
        self._descanso_sapudo_ativo = True
        self._descanso_sapudo_posicao = (100.0, 200.0, 1)
        self._descanso_sapudo_fator_relogio = 180.0
        self.sapudo = SimpleNamespace(
            x=100.0, y=200.0, altura=1, visivel=False, destino_x=100.0, destino_y=200.0
        )
        self.estoque = {"madeira": 0, "ouro": 0, "carne": 0}
        self.camera = SimpleNamespace(x=0, y=0)
        self.world_context = None
        self.personagens = []
        self.personagens_hostis = []
        self.ovelhas = []
        self.construcoes = []
        self.construcoes_hostis = []
        self.arvores = []
        self.minas_ouro = []
        self.recursos = []
        self.efeitos = []
        self.flora = []
        self.controladores = {}
        self.conversa_controller = SimpleNamespace(
            bernardo=SimpleNamespace(
                x=10.0, y=20.0, visivel=False, destino_x=10.0, destino_y=20.0
            ),
            recolher_bernardo=SimpleNamespace(
                ativo=True,
                dormindo=True,
                voltando_para_inicio=False,
                destino=(10.0, 20.0),
                destino_inicial=(10.0, 20.0),
                tipo_destino="casa",
            ),
        )


def test_snapshot_persiste_descanso_e_recolhimento():
    c = FakeCenario()
    d = SaveGameManager(c)._coletar()
    assert d["descanso_sapudo"]["ativo"] is True
    assert d["descanso_sapudo"]["posicao"] == [100.0, 200.0, 1]
    assert d["recolher_bernardo"]["dormindo"] is True
    assert d["recolher_bernardo"]["destino"] == [10.0, 20.0]
