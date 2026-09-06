from types import SimpleNamespace

from application.cenario import CenarioPrincipal


def _cenario():
    c = CenarioPrincipal.__new__(CenarioPrincipal)
    c.sapudo = None
    c.personagens_hostis = []
    c.construcoes_hostis = []
    c._danos_flutuantes = []
    return c


def test_sapudo_recebe_popup_vermelho():
    c = _cenario()
    sapudo = SimpleNamespace(nome="sapudo", x=100, y=200, vida=39)
    c.sapudo = sapudo
    c.registrar_dano_visual(sapudo, 7)
    assert c._danos_flutuantes[0]["dano"] == 7
    assert sapudo is c._danos_flutuantes[0]["entidade"]


def test_inimigo_recebe_popup_azul_por_ser_hostil():
    c = _cenario()
    inimigo = SimpleNamespace(nome="bandido", x=100, y=200, vida=20)
    c.personagens_hostis.append(inimigo)
    c.registrar_dano_visual(inimigo, 4)
    assert c._danos_flutuantes[0]["dano"] == 4
    assert inimigo is c._danos_flutuantes[0]["entidade"]


def test_dano_zero_nao_cria_popup():
    c = _cenario()
    inimigo = SimpleNamespace(nome="bandido", x=100, y=200, vida=20)
    c.personagens_hostis.append(inimigo)
    c.registrar_dano_visual(inimigo, 0)
    assert c._danos_flutuantes == []
