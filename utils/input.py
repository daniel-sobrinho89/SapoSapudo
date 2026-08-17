from contextlib import suppress

import utils.kivy_adapter as kivy_adapter

LARGURA = 1024
ALTURA = 600
LARGURA_REAL = None
ALTURA_REAL = None


def init_scaling(real_w, real_h, virtual_w=1024, virtual_h=600):
    global LARGURA_REAL, ALTURA_REAL, LARGURA, ALTURA
    LARGURA_REAL = real_w
    ALTURA_REAL = real_h
    LARGURA = virtual_w
    ALTURA = virtual_h


def real_to_virtual(pos):
    with suppress(Exception):
        rx, ry = pos
        if LARGURA_REAL and ALTURA_REAL:
            vx = int(rx * LARGURA / LARGURA_REAL)
            vy = ALTURA - int(ry * ALTURA / ALTURA_REAL)
            return (vx, vy)
    return pos


def virtual_to_real(pos):
    with suppress(Exception):
        vx, vy = pos
        if LARGURA_REAL and ALTURA_REAL:
            return (int(vx * LARGURA_REAL / LARGURA), int(vy * ALTURA_REAL / ALTURA))
    return pos


def event_pos_virtual(event):
    if hasattr(event, "pos"):
        return real_to_virtual(event.pos)

    if hasattr(event, "x") and hasattr(event, "y"):
        try:
            rx = int(event.x * LARGURA_REAL)
            ry = int(event.y * ALTURA_REAL)
            return real_to_virtual((rx, ry))
        except Exception:
            return None

    return None


def obter_posicao_ponteiro():
    return real_to_virtual(kivy_adapter.mouse.get_pos())


def obter_clique_ponteiro(event):
    if event.type in (kivy_adapter.MOUSEBUTTONDOWN, kivy_adapter.MOUSEBUTTONUP):
        return (getattr(event, "button", None), event_pos_virtual(event))

    if event.type in (
        getattr(kivy_adapter, "FINGERDOWN", None),
        getattr(kivy_adapter, "FINGERUP", None),
    ):
        return (None, event_pos_virtual(event))
    return None
