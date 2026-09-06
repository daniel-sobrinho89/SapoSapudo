from types import SimpleNamespace

from core.save_game import SaveGameManager


class CenarioFake:
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
        self.flora = []
        self.sapudo = None
        self._proximo_save_id = 1
        self.conversa_controller = SimpleNamespace(
            cobras_missao=[], casa_construindo=None, construir_casa=SimpleNamespace()
        )
        self.estoque = {"madeira": 0, "ouro": 0, "carne": 0}
        self.ciclo_dia_noite = SimpleNamespace(hora=10.0)
        self.camera = SimpleNamespace(x=0, y=0)
        self.world_context = None

    def carregar_entidade(self, nome, x, y, altura=0):
        e = SimpleNamespace(
            nome=nome,
            x=x,
            y=y,
            altura=altura,
            vida=47,
            VIDA_MAXIMA=47,
            persistencia_dinamica=True,
            save_id=None,
            visivel=True,
            destino_x=x,
            destino_y=y,
            base_x=x,
            base_y=y,
            base_raio=4,
        )
        if nome == "cobra":
            self.personagens_hostis.append(e)
        elif nome == "casa_construindo":
            self.construcoes.append(e)
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
            self.flora,
        ):
            if e in colecao:
                colecao.remove(e)


def test_entidade_morta_referenciada_eh_salva_como_ref():
    c = CenarioFake()
    manager = SaveGameManager(c)
    cobra = SimpleNamespace(
        nome="cobra", x=123.0, y=456.0, vida=0, persistencia_dinamica=True, save_id=None
    )
    c.conversa_controller.cobras_missao = [cobra]
    coleta = manager._coletar()
    assert any(
        e["nome"] == "cobra" and e["vida"] == 0 and e["no_cenario"] is False
        for e in coleta["entidades"]
    )
    ref = coleta["controlador_estado"]["cobras_missao"][0]
    assert "__entity_ref__" in ref


def test_entidades_referenciadas_pelo_controller_incluem_usecase():
    c = CenarioFake()
    manager = SaveGameManager(c)
    casa = SimpleNamespace(
        nome="casa_construindo",
        x=50.0,
        y=70.0,
        vida=1,
        persistencia_dinamica=True,
        save_id=None,
    )
    c.construcoes = [casa]
    c.conversa_controller.casa_construindo = casa
    c.conversa_controller.construir_casa.casa = casa
    coleta = manager._coletar()
    registros = [e for e in coleta["entidades"] if e["nome"] == "casa_construindo"]
    assert len(registros) == 1
    assert registros[0]["no_cenario"] is True
    assert (
        coleta["controlador_estado"]["casa_construindo"]["__entity_ref__"]
        == registros[0]["save_id"]
    )
    estado = coleta["controlador_estado"]["construir_casa"]["__object_state__"]
    assert estado["casa"]["__entity_ref__"] == registros[0]["save_id"]


def test_ids_duplicados_sao_normalizados_no_snapshot():
    c = CenarioFake()
    manager = SaveGameManager(c)
    a = SimpleNamespace(
        nome="cobra", x=1, y=1, vida=47, persistencia_dinamica=True, save_id="runtime:1"
    )
    b = SimpleNamespace(
        nome="casa_construindo",
        x=2,
        y=2,
        vida=1,
        persistencia_dinamica=True,
        save_id="runtime:1",
    )
    c.personagens_hostis = [a]
    c.construcoes = [b]
    snap = manager._coletar()
    ids = [e["save_id"] for e in snap["entidades"]]
    assert len(ids) == len(set(ids))


def test_save_antigo_com_cobra_morta_inline_e_migrado_para_referencia():
    c = CenarioFake()
    manager = SaveGameManager(c)
    c.conversa_controller.cobras_missao = []
    legado = {
        "__object_state__": {
            "nome": "cobra",
            "x": 123,
            "y": 456,
            "altura": 1,
            "vida": 0,
            "persistencia_dinamica": True,
            "VIDA_MAXIMA": 47,
        },
        "__object_type__": "Cobra",
    }
    migrado = manager._migrar_referencias_legadas({"cobras_missao": [legado]})
    ref = migrado["cobras_missao"][0]
    assert "__entity_ref__" in ref
    ident = ref["__entity_ref__"]
    entidade = manager._indice_entidades()[ident]
    assert entidade.vida == 0
    assert entidade not in c.personagens_hostis
    assert entidade in c._entidades_save_detached.values()
