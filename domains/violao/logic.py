# =====================================
# systems/sapudo/logica_violao.py
# =====================================


class LogicaViolaoSapo:
    """
    Gerencia as regras de comportamento do Sapo com o violão.
    (Timers, ping-pong de frames e sequenciamento de estados).
    """

    def __init__(self):
        self.tempo_tocando = 0.0
        self.tempo_frame = 0.0
        self.frame_atual = 0
        self.direcao = 1

        self.frame_min = 0
        self.frame_max = 9
        self.intervalo_frame = 0.22
        self.tempo_limite_tocar = 900  # 15 minutos

    def resetar(self):
        self.tempo_tocando = 0
        self.tempo_frame = 0
        self.frame_atual = 0
        self.direcao = 1

    def atualizar_frames(self, dt):
        self.tempo_tocando += dt

        if self.tempo_tocando >= self.tempo_limite_tocar:
            return "levantar"

        self.tempo_frame += dt
        if self.tempo_frame < self.intervalo_frame:
            return None

        self.tempo_frame = 0
        self.frame_atual += self.direcao

        if self.frame_atual >= self.frame_max:
            self.frame_atual = self.frame_max
            self.direcao = -1
        elif self.frame_atual <= self.frame_min:
            self.frame_atual = self.frame_min
            self.direcao = 1

        return None
