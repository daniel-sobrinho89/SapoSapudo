from types import SimpleNamespace

from application.usecases.personagem.mover import MoverPersonagemUseCase
from core.animacoes import Animacoes


class NavegacaoReta:
    _versao_obstaculos = 1

    def calcular_rota(self, *args):
        # Primeiro desce verticalmente; depois avança para a direita.
        return [(0.0, -20.0), (40.0, -20.0)]

    def _limitar_distancia(self, x1, y1, x2, y2, passo):
        dx = x2 - x1
        dy = y2 - y1
        distancia = (dx * dx + dy * dy) ** 0.5
        if distancia <= passo:
            return x2, y2
        fator = passo / distancia
        return x1 + dx * fator, y1 + dy * fator

    def _caminho_livre(self, *args):
        return True

    def pode_andar(self, *args):
        return True

    def obter_altura_transicao(self, *args):
        return None


def test_movimento_vertical_nao_usa_alvo_final_para_flip():
    personagem = SimpleNamespace(
        x=0.0,
        y=0.0,
        destino_x=0.0,
        destino_y=-20.0,
        altura=1,
        animacoes=Animacoes("urso"),
    )
    # Urso inicia olhando para a direita.
    personagem.animacoes.definir("ocioso", flip=False)

    mover = MoverPersonagemUseCase()
    assert (
        mover.executar(
            personagem=personagem,
            navegacao=NavegacaoReta(),
            velocidade=100,
            dt=0.1,
            destino_externo=(40.0, -20.0),
            animacao_correndo="correndo",
            animacao_parado="ocioso",
        )
        is True
    )

    # Primeiro trecho é vertical. Não devemos olhar para o alvo final à direita
    # antes de existir deslocamento horizontal.
    assert personagem.animacoes.flip is False
