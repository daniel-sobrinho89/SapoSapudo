# =====================================
# systems/duende/arraste_duende.py
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
        self.soltou_frente_pote = False

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

    def finalizar(self, entity_x, entity_y, frasco_rect):
        self.ativo = False
        self.soltou_frente_pote = frasco_rect.collidepoint(int(entity_x), int(entity_y))

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

    def processar_toque_up(
        self, frasco_rect, entity_x, entity_y, animacoes, escolher_destino_callback
    ):
        if self.ativo:
            self.finalizar(entity_x, entity_y, frasco_rect)
            if self.soltou_frente_pote:
                animacoes.iniciar_sono()
                animacoes.iniciar_sono_programado()
            elif animacoes.dormindo:
                animacoes.iniciar_acordar()
                animacoes.cancelar_sono_programado()
                escolher_destino_callback()
            return True
        return False
