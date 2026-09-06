from types import SimpleNamespace

from application.usecases.personagem.mover import MoverPersonagemUseCase
from core.animacoes import Animacoes


class NavegacaoRetorno:
    _versao_obstaculos = 1

    def calcular_rota(self, *args):
        return []

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


def test_urso_orientacao_usa_deslocamento_real_no_retorno():
    personagem = SimpleNamespace(
        x=0.0,
        y=0.0,
        destino_x=0.0,
        destino_y=-20.0,
        altura=1,
        animacoes=Animacoes("urso"),
    )
    # Começa olhando para a direita (sem flip).
    personagem.animacoes.definir_por_direcao("ocioso", 100)
    mover = MoverPersonagemUseCase()

    # Primeiro trecho: vertical. A orientação horizontal anterior deve ser preservada.
    mover.executar(
        personagem,
        NavegacaoRetorno(),
        100,
        dt=0.2,
        destino_externo=(0.0, -20.0),
        animacao_correndo="correndo",
        animacao_parado="ocioso",
    )
    assert personagem.y < 0
    assert personagem.animacoes.flip is False

    mover.executar(
        personagem,
        NavegacaoRetorno(),
        100,
        dt=0.2,
        destino_externo=(40.0, -20.0),
        animacao_correndo="correndo",
        animacao_parado="ocioso",
    )
    assert personagem.x > 0
    assert personagem.animacoes.flip is False
