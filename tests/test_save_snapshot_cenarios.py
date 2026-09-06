from types import SimpleNamespace

from core.save_game import SaveGameManager


class FakeCenario:
    def __init__(self):
        self.personagens = []
        self.personagens_hostis = []
        self.ovelhas = []
        self.construcoes = []
        self.construcoes_hostis = []
        self.arvores = []
        self.minas_ouro = []
        self.recursos = []
        self.efeitos = []
        self.sapudo = None
        self._proximo_save_id = 1
        self.conversa_controller = SimpleNamespace(
            cobras_missao=[],
            casa_madeira_entregue=3,
            casa_madeira_para_transportar=11,
            estado="missao_planalto_cobras",
        )

    def carregar_entidade(self, nome, x, y, altura=0):
        e = SimpleNamespace(
            nome=nome,
            x=x,
            y=y,
            altura=altura,
            persistencia_dinamica=True,
            save_id=None,
            vida=47,
            ataque=6,
            defesa=2,
            VIDA_MAXIMA=47,
            visivel=True,
            destino_x=x,
            destino_y=y,
            base_x=x,
            base_y=y,
            base_raio=4,
            xp_recompensa=40,
            xp_missao_id="missao_cobras_planalto",
            xp_recompensada=False,
            madeira=0,
            minerio=0,
            coletado=False,
        )
        if nome == "cobra":
            self.personagens_hostis.append(e)
        elif nome == "madeira":
            self.recursos.append(e)
        else:
            self.personagens.append(e)
        return e

    def remover_personagem(self, e):
        for colecao in (
            self.personagens,
            self.personagens_hostis,
            self.ovelhas,
            self.construcoes,
            self.construcoes_hostis,
            self.arvores,
            self.minas_ouro,
            self.recursos,
            self.efeitos,
        ):
            if e in colecao:
                colecao.remove(e)
                return


def test_snapshot_v2_reconstroi_entidades_runtime_genericas(tmp_path, monkeypatch):
    c = FakeCenario()
    c.personagens_hostis = [
        SimpleNamespace(
            nome="cobra", save_id="runtime:c1", persistencia_dinamica=True, x=1, y=2
        ),
        SimpleNamespace(
            nome="cobra", save_id="runtime:c2", persistencia_dinamica=True, x=3, y=4
        ),
    ]
    c.recursos = [
        SimpleNamespace(
            nome="madeira",
            save_id=f"runtime:m{i}",
            persistencia_dinamica=True,
            x=10 + i,
            y=20,
        )
        for i in range(14)
    ]
    c.estoque = {"madeira": 11, "ouro": 0, "carne": 0}
    manager = SaveGameManager(c)
    registro_cobra = {
        "save_id": "runtime:c1",
        "nome": "cobra",
        "persistencia_dinamica": True,
        "x": 1,
        "y": 2,
        "altura": 1,
    }
    assert manager._registro_dinamico(registro_cobra, 2)
    assert manager._id_registro(
        {"nome": "cobra", "world_spawn_id": None}, 7, 1
    ).startswith("legacy:1:7:")


def test_save_version_1_sem_ids_ainda_considera_runtime_dinamico():
    assert SaveGameManager._registro_dinamico(
        {"nome": "cobra", "world_spawn_id": None}, 1
    )
    assert SaveGameManager._registro_dinamico(
        {"nome": "madeira", "world_spawn_id": None}, 1
    )
    assert not SaveGameManager._registro_dinamico(
        {"nome": "ovelha", "world_spawn_id": "ovelha_01"}, 1
    )


def test_resolver_valor_preserva_estado_de_objeto_runtime():
    c = FakeCenario()
    manager = SaveGameManager(c)
    classe = type("FakeUseCase", (), {})
    objeto = classe()
    objeto.ativo = False
    registro = manager._resolver_valor(
        {"__object_state__": {"ativo": True, "madeira_restante": 7}},
        {},
    )
    assert registro["__object_state__"]["ativo"] is True
    assert registro["__object_state__"]["madeira_restante"] == 7


def test_world_state_snapshot_persiste_timer_de_recurso():
    from core.world.state import EstadoRecurso, WorldState

    state = WorldState()
    state.registrar_recurso("arvore-01")
    state.marcar_recurso_coletado("arvore-01")
    snap = state.snapshot()
    assert snap["recursos"]["arvore-01"] == EstadoRecurso.COLETADO.value
    assert snap["temporizadores_recursos"]["arvore-01"] > 0


def test_arvore_reconstroi_animacao_cortada():
    from domains.arvore.entity import Arvore

    arvore = Arvore("arvore1", 10, 20, 0)
    arvore.madeira = 0
    arvore.vida = 0
    arvore.restaurar_estado_save({"madeira": 0})
    assert arvore.animacoes.esta_em("cortada")
