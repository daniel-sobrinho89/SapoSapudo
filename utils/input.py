import kivy_adapter
from .paths import BASE_DIR

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
    try:
        rx, ry = pos
        if LARGURA_REAL and ALTURA_REAL:
            vx = int(rx * LARGURA / LARGURA_REAL)

            vy = ALTURA - int(
                ry * ALTURA / ALTURA_REAL
            )

            return (vx, vy)
    except Exception:
        pass
    return pos


def virtual_to_real(pos):
    try:
        vx, vy = pos
        if LARGURA_REAL and ALTURA_REAL:
            return (int(vx * LARGURA_REAL / LARGURA), int(vy * ALTURA_REAL / ALTURA))
    except Exception:
        pass
    return pos


def event_pos_virtual(event):
    # mouse events have `pos` in pixels (real coords)
    if hasattr(event, 'pos'):
        return real_to_virtual(event.pos)

    # touch events on Android (FINGERDOWN / FINGERUP / FINGERMOTION)
    # have normalized coordinates `x`, `y` in range [0,1]
    if hasattr(event, 'x') and hasattr(event, 'y'):
        try:
            rx = int(event.x * LARGURA_REAL)
            ry = int(event.y * ALTURA_REAL)
            return real_to_virtual((rx, ry))
        except Exception:
            return None

    return None


def obter_posicao_ponteiro():
    # retorna posição do ponteiro já convertida para coordenadas virtuais
    return real_to_virtual(kivy_adapter.mouse.get_pos())


def obter_clique_ponteiro(event):
    # para eventos de clique, retorna (button, pos_virtual) ou None
    if event.type in (kivy_adapter.MOUSEBUTTONDOWN, kivy_adapter.MOUSEBUTTONUP):
        return (getattr(event, 'button', None), event_pos_virtual(event))

    # mapear eventos de toque para formato similar: button=None, pos_virtual
    if event.type in (getattr(kivy_adapter, 'FINGERDOWN', None), getattr(kivy_adapter, 'FINGERUP', None)):
        return (None, event_pos_virtual(event))
    return None
