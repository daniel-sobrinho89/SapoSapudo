"""Compatibilidade para imports antigos. A implementação agora é genérica."""

from application.usecases.personagem.comportamento import ControlarComportamentoUseCase
from domains.personagem.maquina_estado_sapudo import EstadoSapudo


def ControlarComportamentoSapudoUseCase(navegacao, mover=None):
    return ControlarComportamentoUseCase(navegacao, EstadoSapudo, mover=mover)


__all__ = ["ControlarComportamentoSapudoUseCase"]
