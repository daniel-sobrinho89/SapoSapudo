from render.transform_utils import TransformUtils
from utils.kivy_adapter import SRCALPHA, Surface


def _surface(size, value):
    s = Surface(size, SRCALPHA)
    s.fill((value, value, value, 255))
    return s


def test_escalar_nao_reutiliza_resultado_de_outro_objeto_com_id_reaproveitado():
    t = TransformUtils()
    primeira = _surface((8, 8), 40)
    resultado_primeiro = t.escalar(primeira, (16, 16))

    chave = (id(primeira), 16, 16)
    segunda = _surface((8, 8), 200)
    # Simula exatamente o cenário perigoso: mesma chave, fonte diferente.
    t.cache_escalas[chave] = (primeira, resultado_primeiro)

    resultado_segundo = t.escalar(segunda, (16, 16))

    assert resultado_segundo is not resultado_primeiro
    assert resultado_segundo.pil_image().getpixel((0, 0))[:3] == (200, 200, 200)


def test_recorte_spritesheet_valida_a_fonte():
    t = TransformUtils()
    primeira = _surface((16, 8), 30)
    frames1 = t.recortar_spritesheet(primeira, 1, 2)
    chave = (id(primeira), 1, 2)

    segunda = _surface((16, 8), 220)
    t.cache_spritesheets[chave] = (primeira, frames1)
    frames2 = t.recortar_spritesheet(segunda, 1, 2)

    assert frames2 is not frames1
    assert frames2[0].pil_image().getpixel((0, 0))[:3] == (220, 220, 220)
