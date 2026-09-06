from pathlib import Path


def test_savegame_version_e_identidade_generica():
    texto = (
        Path(__file__)
        .parents[1]
        .joinpath("core", "save_game.py")
        .read_text(encoding="utf-8")
    )
    assert "VERSION = 3" in texto
    assert "__entity_ref__" in texto
    assert "persistencia_dinamica" in texto
    assert "controlador_estado" in texto


def test_save_nao_tem_blocos_especificos_de_cobra_ou_bandidos():
    texto = (
        Path(__file__)
        .parents[1]
        .joinpath("core", "save_game.py")
        .read_text(encoding="utf-8")
    )
    # O novo formato não deve depender de nomes de missão para reconstruir
    # entidades ou o estado do controlador.
    assert 'nome") == "cobra"' not in texto
    assert 'nome") == "bandido"' not in texto
    assert "papel_missao" not in texto


def test_save_persiste_estado_de_objeto_runtime_sem_conhecer_a_missao():
    texto = (
        Path(__file__)
        .parents[1]
        .joinpath("core", "save_game.py")
        .read_text(encoding="utf-8")
    )
    assert "__object_state__" in texto
    assert "_aplicar_estado_objeto" in texto


def test_save_nao_descarta_construir_casa_do_controlador():
    texto = (
        Path(__file__)
        .parents[1]
        .joinpath("core", "save_game.py")
        .read_text(encoding="utf-8")
    )
    trecho = texto[
        texto.index("def _serializar_controlador") : texto.index("def _dados_entidade")
    ]
    assert '"construir_casa"' not in trecho.split("if nome in", 1)[-1]
