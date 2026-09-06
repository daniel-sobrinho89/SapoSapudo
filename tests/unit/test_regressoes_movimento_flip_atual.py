from types import SimpleNamespace

from application.usecases.personagem.comportamento import ControlarComportamentoUseCase
from core.animacoes import Animacoes


class _MoverTravado:
    def __init__(self):
        self.canceladas = 0

    def executar(self, **kwargs):
        # Simula exatamente a regressão: a ação diz que está correndo,
        # mas nenhuma coordenada muda.
        return True

    def cancelar_rota(self, personagem):
        self.canceladas += 1
        personagem.destino_x = personagem.x
        personagem.destino_y = personagem.y


def test_bandido_mantem_convencao_visual_padrao():
    animacoes = Animacoes("bandido")
    assert animacoes.flip_para_direcao(-1) is True
    assert animacoes.flip_para_direcao(1) is False


def test_comportamento_autonomo_recupera_de_corrida_sem_deslocamento():
    personagem = SimpleNamespace(
        x=10.0,
        y=20.0,
        destino_x=100.0,
        destino_y=20.0,
        animacoes=Animacoes("ovelha"),
        raio_movimento_livre=256,
        base_x=10.0,
        base_y=20.0,
        altura=0,
        world_context=None,
    )
    mover = _MoverTravado()
    usecase = ControlarComportamentoUseCase(
        navegacao=None,
        mover=mover,
        world_context=None,
    )
    personagem.animacoes.definir("correndo")

    for _ in range(3):
        usecase.executar(0.1, personagem)

    assert mover.canceladas == 1
    assert personagem.destino_x == personagem.x
    assert personagem.destino_y == personagem.y
    assert personagem.animacoes.nome_animacao_atual == "ocioso"
