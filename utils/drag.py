"""Pequenos helpers para cálculo de arraste (sem depender de pygame).

Fornece funções mínimas para reduzir duplicação nas entidades.
"""

def iniciar_drag(entity_x, entity_y, mouse_x, mouse_y):
    """Retorna offsets (offset_x, offset_y) para iniciar arraste."""
    return (entity_x - mouse_x, entity_y - mouse_y)


def mover_com_offset(mouse_x, mouse_y, offset_x, offset_y):
    """Retorna nova posição (x, y) baseada em mouse e offsets."""
    return (mouse_x + offset_x, mouse_y + offset_y)
