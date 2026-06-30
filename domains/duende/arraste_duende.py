# =====================================
# domains.duende/arraste_duende.py
# =====================================

from utils.drag import iniciar_drag, mover_com_offset


class ArrasteDuende:
    """
    Gerencia o sistema de drag and drop do Duende.
    """

    def __init__(self):
        self.ativo = False
        self.offset_x = 0
        self.offset_y = 0

    def iniciar(self, entity_x, entity_y, mouse_x, mouse_y):
        self.ativo = True
        self.offset_x, self.offset_y = iniciar_drag(
            entity_x, entity_y, mouse_x, mouse_y
        )

    def mover(self, mouse_x, mouse_y, entity):
        if not self.ativo:
            return
        entity.x, entity.y = mover_com_offset(
            mouse_x, mouse_y, self.offset_x, self.offset_y
        )

    def processar_toque_down(self, pos_virtual, corpo_rect, entity_x, entity_y):
        if corpo_rect and corpo_rect.collidepoint(pos_virtual):
            self.iniciar(entity_x, entity_y, *pos_virtual)
            return True
        return False

    def processar_toque_move(self, pos_virtual, entity):
        if self.ativo:
            self.mover(*pos_virtual, entity)
            return True
        return False
