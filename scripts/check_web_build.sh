#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_DIR="$ROOT/build/web"
echo "WEB_DIR=$WEB_DIR"
PYGBAG_VERSION="$(python - <<'PY'
import importlib.metadata
try:
    print(importlib.metadata.version("pygbag"))
except importlib.metadata.PackageNotFoundError:
    print("")
PY
)"
echo "pygbag=$PYGBAG_VERSION"
test "$PYGBAG_VERSION" = "0.9.3" || {
  echo "ERRO: esta build web exige pygbag 0.9.3"
  exit 1
}
test -f "$WEB_DIR/index.html" || { echo "ERRO: build/web/index.html não existe"; exit 1; }
echo "index.html OK"
grep -q 'ume_block.*0' "$WEB_DIR/index.html" && echo "ume_block=0 OK" || echo "ATENÇÃO: não foi possível confirmar ume_block=0"
echo "web_source.tar.gz:"
ls -lh "$WEB_DIR/web_source.tar.gz" 2>/dev/null || true
echo
echo "run_web.sh usa pygbag 0.9.3 / CPython 3.12 com o archive 0.9."

echo

grep -q 'archives/0\.9//' "$WEB_DIR/index.html" && { echo "ERRO: URL duplicada archives/0.9//"; exit 1; } || echo "URLs do archive OK"
if grep -Eq '(^|[^:])//archives/0\.9/' "$WEB_DIR/index.html"; then echo "ERRO: URL protocol-relative archives/0.9/"; exit 1; fi

grep -q 'cdn/0\.9\.3' "$WEB_DIR/index.html" && { echo "ERRO: referência antiga cdn/0.9.3"; exit 1; } || echo "Sem referência antiga cdn/0.9.3"

grep -q 'sapo-preloader' "$WEB_DIR/index.html" && echo "HTML preloader OK" || {
  echo "ERRO: preloader HTML não encontrado"
  exit 1
}
