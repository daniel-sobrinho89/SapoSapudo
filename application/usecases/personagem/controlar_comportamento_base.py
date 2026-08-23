"""Compatibilidade para imports antigos."""

from .comportamento import (
    ControlarComportamentoUseCase as ControlarComportamentoBaseUseCase,
)

__all__ = ["ControlarComportamentoBaseUseCase"]
