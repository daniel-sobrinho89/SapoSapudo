class Violao:

    def __init__(self):

        self.x = 805
        self.y = 500

        self.arrastando = False

        self.offset_x = 0
        self.offset_y = 0

        # Não manter pygame.Rect aqui — hitbox calculada pelo renderer
        self.acoplado = False

    def iniciar_arraste(self, mouse_x, mouse_y):

        self.arrastando = True

        self.offset_x = (
            self.x - mouse_x
        )

        self.offset_y = (
            self.y - mouse_y
        )

    def mover_arraste(self, mouse_x, mouse_y):

        if not self.arrastando:
            return

        self.x = mouse_x + self.offset_x
        self.y = mouse_y + self.offset_y

    def finalizar_arraste(self):
        self.arrastando = False