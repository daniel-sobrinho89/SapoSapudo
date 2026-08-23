"""Compatibilidade com imports antigos.

A implementação do cenário pertence à camada de aplicação porque coordena
casos de uso, renderização, navegação e ciclo de vida do jogo.
"""

from application.cenario import (
    CenarioBase,
    CenarioPrincipal,
    EstadoJogo,
    GerenciadorCenarios,
)

__all__ = ["CenarioBase", "CenarioPrincipal", "EstadoJogo", "GerenciadorCenarios"]
