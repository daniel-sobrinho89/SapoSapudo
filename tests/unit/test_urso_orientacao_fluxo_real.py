from types import SimpleNamespace

from application.usecases.personagem.mover import MoverPersonagemUseCase
from core.animacoes import Animacoes


class Nav:
    _versao_obstaculos = 1

    def calcular_rota(self, *args):
        return [(20.0, 0.0)]

    def _limitar_distancia(self, x1, y1, x2, y2, passo):
        dx, dy = x2 - x1, y2 - y1
        d = (dx * dx + dy * dy) ** 0.5
        if d <= passo:
            return x2, y2
        f = passo / d
        return x1 + dx * f, y1 + dy * f

    def _caminho_livre(self, *args):
        return True

    def pode_andar(self, *args):
        return True

    def obter_altura_transicao(self, *args):
        return None


def test_urso_movimento_para_direita_define_orientacao_pelo_deslocamento_real():
    urso = SimpleNamespace(
        x=0.0,
        y=0.0,
        destino_x=20.0,
        destino_y=0.0,
        altura=1,
        animacoes=Animacoes("urso"),
    )
    # Começa olhando para a esquerda, para garantir que o movimento é quem manda.
    urso.animacoes.definir_por_direcao("ocioso", -10)
    mover = MoverPersonagemUseCase()
    assert (
        mover.executar(
            urso,
            Nav(),
            100,
            dt=0.1,
            destino_externo=(20.0, 0.0),
            animacao_correndo="correndo",
            animacao_parado="ocioso",
        )
        is True
    )
    assert urso.x > 0
    # Para o Urso, o sinal positivo é a direção horizontal oposta à convenção de flip.
    assert urso.animacoes.flip is False
