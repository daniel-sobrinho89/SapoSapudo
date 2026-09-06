from types import SimpleNamespace

from application.usecases.personagem.comportamento import ControlarComportamentoUseCase


class _Navegacao:
    def ponto_aleatorio_no_raio(self, *args):
        return (100.0, 0.0)

    def calcular_rota(self, *args):
        return [(100.0, 0.0)]

    def _limitar_distancia(self, x1, y1, x2, y2, passo):
        return (x2, y2)

    def _caminho_livre(self, *args):
        return True

    def pode_andar(self, *args):
        return True

    def obter_altura_transicao(self, *args):
        return None


class _Animacoes:
    def __init__(self):
        self.nome_animacao_atual = "correndo"
        self.flip = False
        self.calls = []

    def definir_por_direcao(self, nome, dx):
        self.calls.append((nome, dx))

    def definir(self, nome, flip=None):
        self.calls.append((nome, flip))


class _Mover:
    def executar(self, **kwargs):
        personagem = kwargs["personagem"]
        personagem.x = personagem.destino_x
        personagem.y = personagem.destino_y
        return True


def test_comportamento_move_quando_destino_existe_sem_maquina_de_estado():
    personagem = SimpleNamespace(
        x=0.0,
        y=0.0,
        destino_x=100.0,
        destino_y=0.0,
        animacoes=_Animacoes(),
        raio_movimento_livre=256,
        base_x=0.0,
        base_y=0.0,
        altura=0,
        world_context=None,
    )
    usecase = ControlarComportamentoUseCase(_Navegacao(), mover=_Mover())

    usecase.executar(0.1, personagem)

    assert personagem.x == 100.0
    assert personagem.y == 0.0
