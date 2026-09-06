from __future__ import annotations

from core.world.service import WorldService


def main() -> int:
    context = WorldService().carregar()
    issues = context.validator.issues
    erros = [issue for issue in issues if issue.severity == "ERROR"]
    avisos = [issue for issue in issues if issue.severity == "WARN"]
    world = context.world
    print("SAPO SAPUDO - WORLD VALIDATOR")
    print(f"World: {world.world_id} v{world.version}")
    print(f"Regiões: {len(world.regions)} | Spawns: {len(world.spawns)}")
    for issue in issues:
        print(issue)
    print(f"RESULTADO: {len(erros)} erros | {len(avisos)} avisos")
    return 1 if erros else 0


if __name__ == "__main__":
    raise SystemExit(main())
