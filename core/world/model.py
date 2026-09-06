from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Position:
    x: float
    y: float
    altura: int = 0


@dataclass(frozen=True)
class Region:
    id: str
    nome: str
    tipo: str
    x: int
    y: int
    colunas: int
    linhas: int
    papel: str = "generica"
    tier: int = 0
    risco: str = "baixo"
    recompensa: str | None = None
    entrada: bool = False
    saida: bool = False
    tags: tuple[str, ...] = ()

    def contem_tile(self, coluna: int, linha: int) -> bool:
        return (
            self.x <= coluna < self.x + self.colunas
            and self.y <= linha < self.y + self.linhas
        )


@dataclass(frozen=True)
class WorldSpawn:
    id: str
    tipo: str
    regiao: str | None
    posicao: Position
    tags: tuple[str, ...]
    origem: str = "world"


@dataclass
class WorldModel:
    world_id: str
    version: int
    start_region: str
    map_id: str
    systems: dict[str, bool]
    regions: dict[str, Region]
    spawns: dict[str, WorldSpawn]
    state: dict[str, Any] = field(default_factory=dict)

    def obter_spawns_tipo(self, tipo: str) -> list[WorldSpawn]:
        return [spawn for spawn in self.spawns.values() if spawn.tipo == tipo]

    def obter_regiao(self, regiao_id: str) -> Region | None:
        return self.regions.get(regiao_id)

    def obter_regiao_no_tile(self, coluna: int, linha: int) -> Region | None:
        candidatas = [
            region
            for region in self.regions.values()
            if region.contem_tile(coluna, linha)
        ]
        if not candidatas:
            return None
        return min(candidatas, key=lambda region: region.colunas * region.linhas)
