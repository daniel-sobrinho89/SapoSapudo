import json
from pathlib import Path

from core.regiao_mapa import RegiaoMapa
from core.world.loader import WorldLoader
from core.world.validator import WorldValidator


def test_regiao_contem_tile():
    regiao = RegiaoMapa("bosque", "Bosque", "bosque", 2, 8, 13, 10)
    assert regiao.contem_tile(2, 8)
    assert regiao.contem_tile(14, 17)
    assert not regiao.contem_tile(15, 17)
    assert not regiao.contem_tile(2, 18)


def test_regiao_contem_pixel():
    regiao = RegiaoMapa("bosque", "Bosque", "bosque", 2, 8, 13, 10)
    assert regiao.contem_pixel(-60 + 2 * 64 + 32, -66 + 8 * 64 + 32, -60, -66)
    assert not regiao.contem_pixel(-60 + 15 * 64 + 32, -66 + 17 * 64 + 32, -60, -66)


def test_world_model_carrega_camadas_profissionais():
    world = WorldLoader().carregar()
    assert world.start_region == "vila_bernardo"
    assert len(world.regions) == 9
    assert len(world.spawn_rules) >= 10
    assert len(world.spawns) > 100


def test_spawns_de_recursos_respeitam_terreno_e_regra():
    mapa = json.loads(Path("data/mapas/mapa1.json").read_text(encoding="utf-8"))
    world = WorldLoader().carregar()
    issues = WorldValidator(world, mapa).validar()
    erros = [issue for issue in issues if issue.severity == "ERROR"]
    assert not erros, "\\n".join(map(str, erros))


def test_pedra_de_agua_vive_na_margem_agua():
    world = WorldLoader().carregar()
    pedras = [spawn for spawn in world.obter_spawns_tipo("pedra_agua1")]
    assert pedras
    assert all(spawn.regiao == "margem_sul" for spawn in pedras)
    assert all(spawn.regiao == "margem_sul" for spawn in pedras)


def test_tipos_duplicados_de_regioes_sao_preservados():
    world = WorldLoader().carregar()
    arvores = world.obter_spawns_tipo("arvore1")
    assert any(spawn.regiao == "bosque" for spawn in arvores)
    assert any(spawn.regiao == "vila_bernardo" for spawn in arvores)
