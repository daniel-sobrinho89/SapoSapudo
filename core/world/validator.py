from __future__ import annotations

from dataclasses import dataclass

from core.world.model import WorldModel


@dataclass(frozen=True)
class WorldIssue:
    severity: str
    code: str
    message: str
    location: str

    def __str__(self) -> str:
        return f"[{self.severity}] {self.code}: {self.message} ({self.location})"


class WorldValidator:
    """Valida contrato espacial e semântico do mundo antes de instanciá-lo."""

    def __init__(self, world: WorldModel, map_data: dict):
        self.world = world
        self.map_data = map_data
        self.colunas = int(map_data.get("colunas", 0))
        self.linhas = int(map_data.get("linhas", 0))
        self.offset_x = -60
        self.offset_y = self.linhas - 96
        self.issues: tuple[WorldIssue, ...] = ()

    def pixel_para_tile(self, x: float, y: float) -> tuple[int, int]:
        return int((x - self.offset_x) // 64), int((y - self.offset_y) // 64)

    def terreno(self, coluna: int, linha: int) -> str:
        if not (0 <= coluna < self.colunas and 0 <= linha < self.linhas):
            return "fora_do_mapa"
        overrides = self.map_data.get("terrain_overrides", ())
        for override in overrides:
            if (
                int(override.get("x", -1)) == coluna
                and int(override.get("y", -1)) == linha
            ):
                return override.get("tipo", "grama")
        if linha == self.linhas - 1:
            return "agua_fundo"
        for rio in self.map_data.get("rios", ()):
            if rio["x"] <= coluna < rio["x"] + rio.get("colunas", 1) and rio[
                "y"
            ] <= linha < rio["y"] + rio.get("linhas", 1):
                return "agua_fundo"
        return "grama"

    def validar(self) -> list[WorldIssue]:
        issues = []

        if self.world.start_region not in self.world.regions:
            issues.append(
                WorldIssue(
                    "ERROR",
                    "WORLD_START_REGION",
                    "Região inicial inexistente",
                    self.world.start_region,
                )
            )

        for region in self.world.regions.values():
            if (
                region.x < 0
                or region.y < 0
                or region.x + region.colunas > self.colunas
                or region.y + region.linhas > self.linhas
            ):
                issues.append(
                    WorldIssue(
                        "ERROR",
                        "REGION_OUT_OF_BOUNDS",
                        "Região ultrapassa os limites do mapa",
                        region.id,
                    )
                )

        for spawn in self.world.spawns.values():
            col, lin = self.pixel_para_tile(spawn.posicao.x, spawn.posicao.y)
            location = f"{spawn.id}@{col},{lin}"

            if not (0 <= col < self.colunas and 0 <= lin < self.linhas):
                issues.append(
                    WorldIssue(
                        "ERROR",
                        "SPAWN_OUT_OF_BOUNDS",
                        "Spawn fora do mapa",
                        location,
                    )
                )
                continue

            if spawn.regiao:
                region = self.world.regions.get(spawn.regiao)
                if region is None:
                    issues.append(
                        WorldIssue(
                            "ERROR",
                            "SPAWN_REGION_UNKNOWN",
                            "Região inexistente",
                            location,
                        )
                    )
                elif not region.contem_tile(col, lin):
                    issues.append(
                        WorldIssue(
                            "ERROR",
                            "SPAWN_OUTSIDE_REGION",
                            f"Spawn declarado em {region.id}, mas está fora dela",
                            location,
                        )
                    )

        return issues
