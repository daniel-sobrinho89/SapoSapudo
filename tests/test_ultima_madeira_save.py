from application.usecases.aldeao.construir_casa import ConstruirCasaUseCase


class _Anim:
    def __init__(self):
        self.flip = False
        self.estado = None

    def definir(self, estado, **kwargs):
        self.estado = estado
        self.flip = bool(kwargs.get("flip", self.flip))

    def flip_para_direcao(self, dx):
        return dx < 0


class _B:
    def __init__(self):
        self.x = 100
        self.y = 100
        self.animacoes = _Anim()
        self.destino_x = 100
        self.destino_y = 100


class _C:
    def __init__(self):
        self.nome = "casa_construindo"
        self.x = 120
        self.y = 100


class _Wood:
    def __init__(self, x, y):
        self.nome = "madeira"
        self.x = x
        self.y = y


class _Scene:
    def __init__(self):
        self.recursos = [_Wood(140, 100)]

    def remover_personagem(self, entidade, ignorar=None):
        if entidade in self.recursos:
            self.recursos.remove(entidade)


def test_retomada_da_ultima_madeira_termina_no_proximo_tick():
    s = _Scene()
    u = ConstruirCasaUseCase(s)
    b = _B()
    c = _C()
    done = []
    u.concluida_callback = lambda casa: done.append(casa)
    assert u.retomar(b, c, (140, 100), 1, tempo=1.65, flip=False)
    assert u._retomada_pendente is True
    assert u.executar(0.30) is False
    assert done
    assert u.ativo is False
