from types import SimpleNamespace

from core.animacoes import Animacoes


def test_bernardo_usa_flip_por_direcao():
    anim = Animacoes("aldeao")
    assert anim.flip_para_direcao(-100) is True
    assert anim.flip_para_direcao(100) is False


def test_mover_personagem_nao_vira_para_o_alvo_durante_trecho_vertical():
    # O caminho pode ter dx=0. A orientação deve continuar com a última
    # direção horizontal conhecida, sem olhar para o alvo final.
    from application.usecases.personagem.mover import MoverPersonagemUseCase

    class Navegacao:
        _versao_obstaculos = 1

        def calcular_rota(self, *args):
            return [(0, 10)]

        def _limitar_distancia(self, x1, y1, x2, y2, passo):
            return (x2, y2)

        def _caminho_livre(self, *args):
            return True

        def pode_andar(self, *args):
            return True

        def obter_altura_transicao(self, *args):
            return None

    personagem = SimpleNamespace(
        x=0.0,
        y=0.0,
        destino_x=0.0,
        destino_y=10.0,
        altura=0,
        animacoes=Animacoes("urso"),
    )
    mover = MoverPersonagemUseCase()
    assert (
        mover.executar(
            personagem=personagem,
            navegacao=Navegacao(),
            velocidade=100,
            estado_correndo="correndo",
            estado_correndo_flip="correndo_flip",
            estado_parado="ocioso",
            estado_parado_flip="ocioso_flip",
            dt=0.1,
            destino_externo=(10, 10),
        )
        is True
    )
    # O primeiro trecho é vertical; portanto a direção horizontal anterior
    # deve ser preservada, em vez de apontar para o destino final.
    assert personagem.animacoes.flip is False
