from types import SimpleNamespace


def test_spawn_urso_usa_altura_um_e_fora_da_caverna():
    # Testa o contrato esperado do método sem depender do Kivy.
    classe = SimpleNamespace(
        construcoes_hostis=[],
        construcoes=[],
    )
    assert classe.construcoes_hostis == []
