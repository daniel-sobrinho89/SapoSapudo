import argparse
import importlib
import traceback
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from tests.integration.harness.headless_runtime import garantir_runtime_headless
from tests.integration.scenarios import SCENARIOS

garantir_runtime_headless()


@dataclass
class Result:
    nome: str
    ok: bool
    duracao: float
    erro: str = ""
    trace: object = None


def executar(nome):
    config = SCENARIOS[nome]
    alvo = config[0]
    modulo, funcao = alvo.rsplit(".", 1)
    callback = getattr(
        importlib.import_module(f"tests.integration.scenarios.{modulo}"), funcao
    )
    args = config[1:]
    inicio = perf_counter()
    try:
        trace = callback(*args)
        return Result(nome, True, perf_counter() - inicio, trace=trace)
    except Exception as exc:
        return Result(
            nome,
            False,
            perf_counter() - inicio,
            traceback.format_exc(),
            getattr(exc, "trace", None),
        )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Testes integrados do Sapo Sapudo")
    parser.add_argument("cenarios", nargs="*", choices=sorted(SCENARIOS))
    parser.add_argument(
        "--visual", action="store_true", help="gera GIFs reais e relatório HTML"
    )
    args = parser.parse_args(argv)

    nomes = args.cenarios or list(SCENARIOS)
    resultados = [executar(nome) for nome in nomes]

    print("=" * 62)
    print("SAPO SAPUDO - TESTES INTEGRADOS")
    print("=" * 62)
    for item in resultados:
        marca = "OK" if item.ok else "FAIL"
        print(f"[{marca}] {item.nome:<42} {item.duracao:>7.2f}s")
        if not item.ok:
            print(item.erro)

    aprovados = sum(item.ok for item in resultados)
    print("-" * 62)
    print(
        f"{aprovados} OK | {len(resultados) - aprovados} FALHARAM | {len(resultados)} TOTAL"
    )

    if args.visual:
        from tests.integration.visual.report import gerar_relatorio

        output = gerar_relatorio(resultados, Path("tests/test-results"))
        print(f"Relatório visual: {output}")

    return 0 if aprovados == len(resultados) else 1


if __name__ == "__main__":
    raise SystemExit(main())
