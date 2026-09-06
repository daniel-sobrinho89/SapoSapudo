from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from core.world.model import Region, WorldModel, WorldSpawn
from core.world.state import WorldState
from utils.config import TILE_SIZE


@dataclass(frozen=True)
class WorldLocation:
    regiao: Region | None


class RegionService:
    def __init__(self, world: WorldModel):
        self.world = world

    def obter(self, regiao_id: str | None) -> Region | None:
        return self.world.obter_regiao(regiao_id) if regiao_id else None

    def no_tile(self, coluna: int, linha: int) -> Region | None:
        return self.world.obter_regiao_no_tile(coluna, linha)

    def no_pixel(self, x: float, y: float) -> Region | None:
        coluna = int(x // TILE_SIZE)
        linha = int(y // TILE_SIZE)
        return self.no_tile(coluna, linha)

    def pertence(self, regiao_id: str, x: float, y: float) -> bool:
        regiao = self.obter(regiao_id)
        if regiao is None:
            return False
        return regiao.contem_tile(int(x // TILE_SIZE), int(y // TILE_SIZE))


class SpawnSystem:
    """Catálogo simples de entidades explícitas do mapa.

    A posição e a quantidade de cada entidade vêm diretamente de
    ``entities.json``. Não existe uma segunda camada de zonas ou regras
    procedurais para recriar o conteúdo.
    """

    def __init__(self, world: WorldModel, validator):
        self.world = world
        self.validator = validator
        self._por_tipo: dict[str, tuple[WorldSpawn, ...]] = {}
        for spawn in world.spawns.values():
            self._por_tipo.setdefault(spawn.tipo, []).append(spawn)
        self._por_tipo = {key: tuple(value) for key, value in self._por_tipo.items()}

    def obter_spawns_tipo(self, tipo: str) -> tuple[WorldSpawn, ...]:
        return self._por_tipo.get(tipo, ())

    def pode_spawnar(self, spawn: WorldSpawn) -> bool:
        # As entidades são declaradas diretamente pelo mapa, então a única
        # validação necessária aqui é a validade espacial.
        return not any(
            issue.severity == "ERROR" and issue.location.startswith(spawn.id + "@")
            for issue in self.validator.issues
        )


class WorldContext:
    """Contexto único do mundo usado por domínio, IA, navegação e debug."""

    def __init__(self, world: WorldModel, validator):
        self.world = world
        self.validator = validator
        self.region_service = RegionService(world)
        self.spawn_system = SpawnSystem(world, validator)
        self.validator.tilemap_renderer = None
        self.state = WorldState(
            duracao_dia=float(
                world.state.get("clock", {}).get("duracao_dia_simulado", 180.0)
            ),
            clima=self._clima_inicial(),
            eventos_habilitados=bool(
                world.state.get("eventos", {}).get("habilitados", False)
            ),
            intervalo_clima=float(
                world.state.get("clima", {}).get("intervalo_mudanca", 75.0)
            ),
            duracao_respawn=float(
                world.state.get("recursos", {}).get("duracao_respawn", 45.0)
            ),
        )
        self._entidades_vinculadas = set()
        self._entidades_runtime: dict[str, object] = {}
        self.world_editor = None
        self.world_service = None
        self._recursos_runtime: dict[str, object] = {}
        self._respawn_callback = None

    def _clima_inicial(self):
        from core.world.state import Clima

        return Clima(
            str(self.world.state.get("clima", {}).get("estado_inicial", "normal"))
        )

    def definir_callback_respawn(self, callback) -> None:
        self._respawn_callback = callback

    def reindexar(self) -> None:
        """Reconstrói índices após edição visual do WorldModel em memória."""
        tilemap = getattr(self, "tilemap_renderer", None)
        if tilemap is not None:
            self.validator.map_data["terrain_overrides"] = [
                {"x": x, "y": y, "tipo": tipo}
                for (x, y), tipo in getattr(tilemap, "terrain_overrides", {}).items()
            ]
        self.region_service = RegionService(self.world)
        self.spawn_system = SpawnSystem(self.world, self.validator)
        issues = self.validator.validar()
        self.validator.issues = tuple(issues)

    def atualizar(self, dt: float) -> None:
        self.state.atualizar(dt)
        regenerados = self.state.consumir_recursos_regenerados()
        if self._respawn_callback is not None:
            for resource_id in regenerados:
                entidade = self._recursos_runtime.get(resource_id)
                self._respawn_callback(resource_id, entidade)

    def _pixel_para_tile(self, x: float, y: float) -> tuple[int, int]:
        tilemap = getattr(self, "tilemap_renderer", None)
        offset_x = getattr(tilemap, "offset_x", self.validator.offset_x)
        offset_y = getattr(tilemap, "offset_y", self.validator.offset_y)
        return int((x - offset_x) // TILE_SIZE), int((y - offset_y) // TILE_SIZE)

    def localizar(self, x: float, y: float) -> WorldLocation:
        coluna, linha = self._pixel_para_tile(x, y)
        return WorldLocation(
            regiao=self.region_service.no_tile(coluna, linha),
        )

    def politica_local(self, x: float, y: float) -> dict[str, object]:
        loc = self.localizar(x, y)
        regiao = loc.regiao
        risco = regiao.risco if regiao else "baixo"
        politica = {
            "risco": risco,
            "papel": regiao.papel if regiao else "generica",
            "tier": regiao.tier if regiao else 0,
            "atividade": self.state.atividade,
        }
        if regiao and regiao.papel == "hub_inicial":
            politica["raio"] = 140
        elif regiao and regiao.papel == "coleta_recorrente":
            politica["raio"] = 180
        elif regiao and regiao.papel == "recurso_avancado":
            politica["raio"] = 140
        elif regiao and regiao.papel == "narrativa_ambiental":
            politica["raio"] = 220
        if risco == "medio_alto":
            politica["raio"] = min(politica.get("raio", 160), 140)
        return politica

    def vincular_entidade(self, entidade) -> WorldLocation:
        contexto = self.contexto_entidade(entidade)
        entidade.world_context = self
        entidade.world_location = contexto
        entidade.regiao_id = contexto.regiao.id if contexto.regiao else None

        entity_id = (
            getattr(entidade, "world_resource_id", None)
            or getattr(entidade, "id", None)
            or (f"{getattr(entidade, 'nome', type(entidade).__name__)}:{id(entidade)}")
        )
        self._entidades_runtime[entity_id] = entidade
        if entity_id not in self._entidades_vinculadas:
            self._entidades_vinculadas.add(entity_id)
            nome = str(getattr(entidade, "nome", ""))
            if nome == "ovelha":
                self.state.registrar_fauna(entity_id)
            if (
                nome
                in {"mina_ouro", "arvore", "arvore1", "arvore2", "arvore3", "arvore4"}
                or "pedra" in nome
            ):
                self.state.registrar_recurso(entity_id)
                self._recursos_runtime[entity_id] = entidade
            if contexto.regiao and "hostil" in contexto.regiao.tags:
                self.state.registrar_ameaca(contexto.regiao.id)
        return contexto

    def contexto_entidade(self, entidade) -> WorldLocation:
        return self.localizar(entidade.x, entidade.y)

    def prioridade_movimento(self, coluna: int, linha: int) -> float:
        return 2.0

    def custo_movimento(self, coluna: int, linha: int) -> float:
        return 1.40

    def ponto_autonomo(self, personagem, raio_min=40, raio_max=None):
        """Seleciona um destino dentro da mesma região, respeitando o risco."""
        contexto = self.contexto_entidade(personagem)
        politica = self.politica_local(personagem.x, personagem.y)
        raio_max = raio_max or getattr(
            personagem, "raio_movimento_livre", politica.get("raio", 160)
        )
        raio_max = min(raio_max, float(politica.get("raio", raio_max)))
        origem_x, origem_y = personagem.x, personagem.y
        candidatos = []
        import random

        for _ in range(48):
            x = random.uniform(origem_x - raio_max, origem_x + raio_max)
            y = random.uniform(origem_y - raio_max, origem_y + raio_max)
            distancia = hypot(x - origem_x, y - origem_y)
            if distancia < raio_min or distancia > raio_max:
                continue
            local = self.localizar(x, y)
            if contexto.regiao and (
                local.regiao is None or local.regiao.id != contexto.regiao.id
            ):
                continue
            col, lin = self._pixel_para_tile(x, y)
            score = distancia * 0.04
            if local.regiao and local.regiao.risco == "alto":
                score += 20
            score += distancia * 0.04
            candidatos.append((score, x, y))
        if not candidatos:
            return None
        _, x, y = min(candidatos, key=lambda item: item[0])
        return x, y
