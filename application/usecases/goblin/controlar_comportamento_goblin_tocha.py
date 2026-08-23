"""Compatibilidade para imports antigos. A implementação agora é genérica."""

from application.usecases.personagem.comportamento import ControlarComportamentoUseCase
from domains.personagem.maquina_estado_goblin_tocha import EstadoGoblinTocha


def ControlarComportamentoGoblinTochaUseCase(navegacao, mover=None):
    return ControlarComportamentoUseCase(navegacao, EstadoGoblinTocha, mover=mover)


__all__ = ["ControlarComportamentoGoblinTochaUseCase"]
