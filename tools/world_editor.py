from __future__ import annotations

import argparse
import json

from core.world.service import WorldService


def main():
    parser = argparse.ArgumentParser(
        description="Editor semântico do mundo Sapo Sapudo"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list-regions")
    sub.add_parser("validate")

    p = sub.add_parser("set-region")
    p.add_argument("id")
    p.add_argument("--papel")
    p.add_argument("--tier", type=int)
    p.add_argument("--risco")
    p.add_argument("--recompensa")

    args = parser.parse_args()
    service = WorldService()
    context = service.carregar()

    if args.cmd == "validate":
        for issue in context.validator.issues:
            print(issue)
        print(
            f"\nErros: {sum(i.severity == 'ERROR' for i in context.validator.issues)}"
        )
        print(f"Avisos: {sum(i.severity == 'WARN' for i in context.validator.issues)}")
        return

    if args.cmd == "list-regions":
        print(
            json.dumps(
                [r.__dict__ for r in context.world.regions.values()],
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
