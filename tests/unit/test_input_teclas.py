from core.input_teclas import normalizar_tecla


def test_f3_keycode_normalizes_to_f3():
    assert normalizar_tecla(284, "") == "f3"


def test_f3_tuple_and_browser_name_normalize_to_f3():
    assert normalizar_tecla((284, "f3"), "") == "f3"
    assert normalizar_tecla(0, "F3") == "f3"


def test_wasd_tem_mesma_identidade_no_keydown_e_keyup():
    assert normalizar_tecla((119, "w"), "w") == "w"
    assert normalizar_tecla((119, "w"), "") == "w"
    assert normalizar_tecla((97, "a"), "a") == "a"
    assert normalizar_tecla((97, "a"), "") == "a"
    assert normalizar_tecla((115, "s"), "s") == "s"
    assert normalizar_tecla((115, "s"), "") == "s"
    assert normalizar_tecla((100, "d"), "d") == "d"
    assert normalizar_tecla((100, "d"), "") == "d"


def test_teclas_numericas_continuam_separadas_de_a_e_b():
    assert normalizar_tecla(49, "") == "1"
    assert normalizar_tecla(50, "") == "2"
    assert normalizar_tecla((97, "a"), "") == "a"
