from __future__ import annotations

import json
from pathlib import Path

from core.world.loader import WorldLoader
from core.world.services import WorldContext
from core.world.validator import WorldValidator
from utils.paths import BASE_DIR


class WorldService:
    """Ponto único de entrada do mundo para a aplicação."""

    def __init__(
        self, world_dir: str | Path | None = None, map_path: str | Path | None = None
    ):
        self.world_dir = Path(world_dir or BASE_DIR / "data/world")
        self.map_path = Path(map_path or BASE_DIR / "data/mapas/mapa1.json")
        self.context: WorldContext | None = None

    def carregar(self) -> WorldContext:
        if self.context is not None:
            return self.context
        world = WorldLoader(self.world_dir).carregar()
        with self.map_path.open(encoding="utf-8") as arquivo:
            map_data = json.load(arquivo)
        validator = WorldValidator(world, map_data)
        issues = validator.validar()
        validator.issues = tuple(issues)
        errors = [issue for issue in issues if issue.severity == "ERROR"]
        if errors:
            detalhes = "\n".join(str(issue) for issue in errors[:20])
            raise ValueError(f"World inválido durante o carregamento:\n{detalhes}")
        self.context = WorldContext(world, validator)
        return self.context

    def recarregar(self) -> WorldContext:
        self.context = None
        return self.carregar()
