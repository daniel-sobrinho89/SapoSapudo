#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$ROOT/build/web_source"
CACHE="$ROOT/build/web-cache"

if [ ! -f "$WORK/main.py" ]; then
  echo "Web source not found: $WORK"
  echo "Running build_web.sh first..."
  "$ROOT/scripts/build_web.sh"
fi

if [ ! -f "$WORK/main.py" ]; then
  echo "ERROR: build/web_source/main.py was not generated."
  exit 1
fi

PYGBAG_REQUIRED_VERSION="0.9.3"
PYGBAG_VERSION="$(python - <<'PY'
import importlib.metadata
try:
    print(importlib.metadata.version("pygbag"))
except importlib.metadata.PackageNotFoundError:
    print("")
PY
)"

if [ "$PYGBAG_VERSION" != "$PYGBAG_REQUIRED_VERSION" ]; then
  echo "ERROR: pygbag version is ${PYGBAG_VERSION:-not installed}; expected $PYGBAG_REQUIRED_VERSION"
  echo "Run: python -m pip install --upgrade --force-reinstall pygbag==$PYGBAG_REQUIRED_VERSION"
  exit 1
fi

echo "Using pygbag $PYGBAG_VERSION with the current 0.9.3 runtime."
echo "Serving source through pygbag so the official archives/repo prebuilts are available."

# Remove incomplete cache entries from interrupted runtime downloads, then patch the fresh cache.
rm -rf "$CACHE"
python "$ROOT/scripts/patch_pygbag_template.py" "$WORK/build/web-cache"
echo "Open: http://localhost:8000"
echo

cd "$ROOT"
exec python -m pygbag     --port 8000     --ume_block 0     --app_name "Sapo Sapudo"     --title "Sapo Sapudo"     --package "br.com.saposapudo.web"     --version "0.9.3"     --PYBUILD "3.12"     --cdn "https://pygame-web.github.io/archives/0.9/"     "$WORK"
