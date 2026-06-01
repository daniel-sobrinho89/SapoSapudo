from utils.drag import iniciar_drag
from utils.drag import mover_com_offset

class Violao:

    def __init__(self):

        self.x = 805
        self.y = 500

        self.arrastando = False

        self.offset_x = 0
        self.offset_y = 0

        self.x_inicial = self.x
        self.y_inicial = self.y

        self.caindo = False

        self.velocidade_queda = 0

        self.chao_y = 520

        self.no_chao = False

        # Não manter pygame.Rect aqui — hitbox calculada pelo renderer
        self.acoplado = False

    def iniciar_arraste(self, mouse_x, mouse_y):

        self.arrastando = True

        self.offset_x, self.offset_y = iniciar_drag(
            self.x,
            self.y,
            mouse_x,
            mouse_y
        )

    def mover_arraste(self, mouse_x, mouse_y):

        if not self.arrastando:
            return

        self.x, self.y = mover_com_offset(
            mouse_x,
            mouse_y,
            self.offset_x,
            self.offset_y
        )

    def finalizar_arraste(self):
        self.arrastando = False

    def iniciar_queda(self):

        self.caindo = True

        self.no_chao = False

        self.velocidade_queda = 0

    def voltar_origem(self):

        self.x = self.x_inicial
        self.y = self.y_inicial

        self.caindo = False

        self.no_chao = False

        self.acoplado = False

    def atualizar(self, dt):

        if not self.caindo:
            return

        self.velocidade_queda += 900 * dt

        self.y += (
            self.velocidade_queda * dt
        )

        if self.y >= self.chao_y:

            self.y = self.chao_y

            self.velocidade_queda = 0

            self.caindo = False

            self.no_chao = True

        self.y = min(
            self.y,
            self.chao_y
        )