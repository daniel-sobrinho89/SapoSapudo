"""Compatibilidade para imports antigos. A implementação agora é genérica."""

from application.usecases.personagem.comportamento import ControlarComportamentoUseCase
from domains.personagem.maquina_estado_soldado import EstadoSoldado


def ControlarComportamentoSoldadoUseCase(navegacao, mover=None):
    return ControlarComportamentoUseCase(navegacao, EstadoSoldado, mover=mover)


__all__ = ["ControlarComportamentoSoldadoUseCase"]
