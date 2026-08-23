#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from time import perf_counter

from tests.integration.harness.headless_runtime import garantir_runtime_headless
from tests.integration.harness.scenario import IntegrationScenario
from tests.integration.scenarios.movement import ponto_tile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

garantir_runtime_headless()


def criar_cenario(quantidade):
    c = IntegrationScenario()
    pontos = []
    for linha in range(2, c.teste_altura - 2):
        for coluna in range(2, c.teste_largura - 2):
            pontos.append(ponto_tile(c, coluna, linha))
            if len(pontos) >= quantidade:
                return c, pontos
    raise RuntimeError("mapa não possui posições suficientes para o benchmark")


def executar(quantidade, ticks):
    c, pontos = criar_cenario(quantidade)
    for i in range(quantidade):
        c.criar_personagem(
            "soldado",
            *pontos[i],
            faccao="aliada",
        )

    inicio = perf_counter()
    for _ in range(ticks):
        c.tick(1 / 30)
    duracao = perf_counter() - inicio

    metricas = c.metricas_desempenho.snapshot()
    counters = metricas["counters"]
    return duracao, counters


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark headless de escalabilidade do SapoSapudo"
    )
    parser.add_argument("--ticks", type=int, default=300)
    parser.add_argument(
        "--quantidades", nargs="+", type=int, default=[10, 25, 50, 100, 150]
    )
    args = parser.parse_args()

    print(
        "quantidade | segundos | personagens_processados |"
        " buscas_alvo | candidatos_busca_alvo"
    )
    print("-" * 84)
    for quantidade in args.quantidades:
        duracao, counters = executar(quantidade, args.ticks)
        print(
            f"{quantidade:10d} | {duracao:8.3f} | "
            f"{counters.get('personagens_processados', 0):23d} | "
            f"{counters.get('buscas_alvo', 0):11d} | "
            f"{counters.get('candidatos_busca_alvo', 0):22d}"
        )


if __name__ == "__main__":
    main()
