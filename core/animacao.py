class Animacao:
    def __init__(self, total_frames, intervalo, loop=True):
        self.frame = 0
        self.tempo = 0.0
        self.total_frames = total_frames
        self.intervalo = intervalo
        self.loop = loop

    def atualizar(self, dt):
        self.tempo += dt
        if self.tempo < self.intervalo:
            return False
        self.tempo -= self.intervalo
        self.frame += 1
        terminou = False
        if self.frame >= self.total_frames:
            terminou = True
            if self.loop:
                self.frame = 0
            else:
                self.frame = self.total_frames - 1
        return terminou

    def reset(self):
        self.frame = 0
        self.tempo = 0
