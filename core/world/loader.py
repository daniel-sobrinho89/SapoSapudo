from __future__ import annotations

import json
from pathlib import Path

from core.world.model import Position, Region, WorldModel, WorldSpawn
from utils.paths import BASE_DIR


class WorldLoader:
    """Carrega o mundo usando apenas regiões, entidades explícitas e estado."""

    def __init__(self, world_dir: str | Path | None = None):
        self.world_dir = Path(world_dir or BASE_DIR / "data/world")

    def _ler(self, nome: str):
        with (self.world_dir / nome).open(encoding="utf-8") as arquivo:
            return json.load(arquivo)

    def carregar(self) -> WorldModel:
        manifest = self._ler("world.json")
        regions = self._ler("regions.json")
        entities = self._ler("entities.json")
        state = self._ler("world_state.json")

        return WorldModel(
            world_id=manifest["world_id"],
            version=int(manifest.get("version", 1)),
            start_region=manifest["start_region"],
            map_id=manifest["map"],
            systems=dict(manifest.get("systems", {})),
            regions={item["id"]: self._region(item) for item in regions},
            spawns={item["id"]: self._spawn(item) for item in entities},
            state=state,
        )

    @staticmethod
    def _region(item: dict) -> Region:
        return Region(
            id=item["id"],
            nome=item.get("nome", item["id"]),
            tipo=item.get("tipo", "generica"),
            x=int(item["x"]),
            y=int(item["y"]),
            colunas=int(item["colunas"]),
            linhas=int(item["linhas"]),
            papel=item.get("papel", "generica"),
            tier=int(item.get("tier", 0)),
            risco=item.get("risco", "baixo"),
            recompensa=item.get("recompensa"),
            entrada=bool(item.get("entrada", False)),
            saida=bool(item.get("saida", False)),
            tags=tuple(item.get("tags", ())),
        )

    @staticmethod
    def _spawn(item: dict) -> WorldSpawn:
        posicao = item["posicao"]
        return WorldSpawn(
            id=item["id"],
            tipo=item["tipo"],
            regiao=item.get("regiao"),
            posicao=Position(
                float(posicao["x"]),
                float(posicao["y"]),
                int(posicao.get("altura", 0)),
            ),
            tags=tuple(item.get("tags", ())),
            origem=item.get("origem", "world"),
        )
