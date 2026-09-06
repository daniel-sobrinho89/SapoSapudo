class DummyRect:
    def collidepoint(self, pos):
        x, y = pos
        return 0 <= x <= 100 and 0 <= y <= 100


def test_menu_jogo_defaults_exist():
    # Guardrail test for source contract.
    from pathlib import Path

    text = Path("application/cenario.py").read_text()
    assert "menu_jogo_aberto" in text
    assert "_renderizar_menu_jogo" in text
    assert "SaveGameManager" in text


def test_coordenador_has_menu_click_path():
    from pathlib import Path

    text = Path("application/coordenador_estado_jogo.py").read_text()
    assert "menu_jogo_aberto" in text
    assert 'nome == "salvar"' in text
    assert 'nome == "carregar"' in text
    assert 'nome == "musica"' in text
