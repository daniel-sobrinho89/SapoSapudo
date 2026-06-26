from core.event_bus import event_bus
from utils.drag import iniciar_drag, mover_com_offset


class Violao:
    def __init__(self, gerenciador_cenarios):
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

        self.chao_y = 520

        self.no_chao = False
        self.acoplado = False

        self.gerenciador_cenarios = gerenciador_cenarios

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

        self.acoplado = False

    def tentar_desacoplar(self, mouse_pos, sapo):
        distancia = ((mouse_pos[0] - sapo.x) ** 2 + (mouse_pos[1] - sapo.y) ** 2) ** 0.5

        if distancia < 120:
            self.acoplado = False
            event_bus.publicar("violao_desacoplado")
            self.iniciar_arraste(*mouse_pos)
            return True
        return False

    def finalizar_interacao(self, sapo):
        """Finaliza o arraste e decide se acopla ao sapo ou cai."""
        if not self.arrastando:
            return False

        self.finalizar_arraste()

        dentro_area = abs(self.x - sapo.x) < 80 and abs(self.y - sapo.y) < 80

        if dentro_area and sapo.pode_receber_violao():
            self.acoplado = True
            self.x = sapo.x + 5
            self.y = sapo.y + 20

            event_bus.publicar("violao_acoplado")
            event_bus.publicar("spotify_iniciado")
        else:
            self.iniciar_queda()
            if self.gerenciador_cenarios and self.gerenciador_cenarios.tem_duende:
                duende = self.gerenciador_cenarios.duende
                if duende.pode_resgatar_violao():
                    distancia_violao = abs(self.x - duende.x)
                    MIN_TELEPORT_DIST = 120
                    if (
                        not duende.consegue_alcancar_antes_da_queda(self)
                        and distancia_violao > MIN_TELEPORT_DIST
                    ):
                        duende.teleportar_para_violao(self)
                    duende.iniciar_resgate_violao(self)

        return True

    def atualizar(self, dt):
        if not self.caindo:
            return

        # gravidade
        self.velocidade_queda += 900 * dt

        # atualizar posições horizontais e verticais
        self.x += self.vel_x * dt
        self.y += self.velocidade_queda * dt

        if self.y >= self.chao_y:
            self.y = self.chao_y

            self.velocidade_queda = 0

            self.caindo = False

            self.no_chao = True
        self.y = min(self.y, self.chao_y)

        # amortecimento horizontal ao pousar
        if self.no_chao:
            self.vel_x *= 0.3
            if abs(self.vel_x) < 2:
                self.vel_x = 0
