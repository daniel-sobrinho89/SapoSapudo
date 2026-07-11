from dataclasses import dataclass

from config import CHAO_Y
from utils.drag import iniciar_drag, mover_com_offset


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
        self.vel_x = 0.0

        self.no_chao = False
        self.acoplado = False
        self.fora_do_lugar = False

    def iniciar_arraste(self, mouse_x, mouse_y):
        self.arrastando = True

        self.offset_x, self.offset_y = iniciar_drag(self.x, self.y, mouse_x, mouse_y)

    def mover_arraste(self, mouse_x, mouse_y):
        if not self.arrastando:
            return

        self.x, self.y = mover_com_offset(
            mouse_x, mouse_y, self.offset_x, self.offset_y
        )

    def finalizar_arraste(self):
        self.arrastando = False

    def iniciar_queda(self):
        self.caindo = True
        self.no_chao = False
        self.velocidade_queda = 0
        self.vel_x = 0.0

    def voltar_origem(self):
        self.x = self.x_inicial
        self.y = self.y_inicial

        self.caindo = False
        self.no_chao = False

        self.velocidade_queda = 0
        self.vel_x = 0.0

        self.arrastando = False
        self.acoplado = False

    def finalizar_interacao(self, area):
        if not self.arrastando:
            return False

        self.finalizar_arraste()
        return True

    def atualizar(self, dt):
        if not self.caindo:
            return

        # gravidade
        self.velocidade_queda += 900 * dt

        # atualizar posições horizontais e verticais
        self.x += self.vel_x * dt
        self.y += self.velocidade_queda * dt

        if self.y >= CHAO_Y:
            self.y = CHAO_Y

            self.velocidade_queda = 0

            self.caindo = False

            self.no_chao = True
        self.y = min(self.y, CHAO_Y)

        # amortecimento horizontal ao pousar
        if self.no_chao:
            self.vel_x *= 0.3
            if abs(self.vel_x) < 2:
                self.vel_x = 0

            if self.x != self.x_inicial or self.y != self.y_inicial:
                self.fora_do_lugar = True
            else:
                self.fora_do_lugar = False


@dataclass
@dataclass
class EstadoViolao:
    x: float
    y: float
    x_inicial: float
    y_inicial: float
    caindo: bool
    acoplado: bool
    no_chao: bool
    velocidade_queda: float
    vel_x: float
