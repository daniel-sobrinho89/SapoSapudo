from domains.recursos.animacoes import AnimacoesRecurso


class Recurso:
    def __init__(self, transform, x, y, total_frames_recurso):
        self.transform = transform
        self.x = x
        self.y = y
        self.animacoes = AnimacoesRecurso(total_frames_recurso)

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)
