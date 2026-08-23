#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Os argumentos --visual, nomes de cenários etc. pertencem ao runner
# dos testes, não ao parser de argumentos do Kivy.
export KIVY_NO_ARGS=1

exec python -m tests.integration "$@"