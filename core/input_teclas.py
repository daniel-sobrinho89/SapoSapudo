def normalizar_tecla(keycode, text=""):
    """Normaliza teclas Kivy/SDL de forma idêntica no KEYDOWN e KEYUP."""
    codigo = keycode[0] if isinstance(keycode, tuple) else keycode
    nome = keycode[1] if isinstance(keycode, tuple) and len(keycode) > 1 else ""

    # KEYUP nem sempre fornece `text`, enquanto KEYDOWN frequentemente fornece.
    # Primeiro usamos o nome textual da própria chave para que W/A/S/D tenham
    # exatamente a mesma identidade nos dois eventos.
    texto = (text or nome or "").lower()
    especiais = {
        273: "up",
        274: "down",
        275: "right",
        276: "left",
        32: "space",
        13: "enter",
        27: "escape",
        284: "f3",
        285: "f4",
        49: "1",
        50: "2",
    }

    if texto in {"f3", "f4"}:
        return texto
    if texto in {
        "up",
        "down",
        "left",
        "right",
        "space",
        "enter",
        "escape",
        "w",
        "a",
        "s",
        "d",
        "q",
        "e",
    }:
        return texto

    if codigo in especiais:
        return especiais[codigo]

    # SDL/Kivy pode entregar o código ASCII da letra sem um nome textual no
    # KEYUP. Convertemos explicitamente para a mesma letra usada no KEYDOWN.
    if isinstance(codigo, int) and 97 <= codigo <= 122:
        return chr(codigo)
    if isinstance(codigo, int) and 65 <= codigo <= 90:
        return chr(codigo + 32)

    return texto or str(codigo).lower()
