"""Compatibilidade para imports antigos. A implementação agora é genérica."""

from application.usecases.personagem.comportamento import ControlarComportamentoUseCase
from domains.personagem.maquina_estado import EstadoAldeao


def ControlarComportamentoAldeaoUseCase(navegacao, mover=None):
    return ControlarComportamentoUseCase(navegacao, EstadoAldeao, mover=mover)


__all__ = ["ControlarComportamentoAldeaoUseCase"]
