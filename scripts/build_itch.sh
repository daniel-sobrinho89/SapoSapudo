#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_DIR="$ROOT/build/web"
UPLOAD_DIR="$ROOT/build/itch_upload"
UPLOAD_ZIP="$UPLOAD_DIR/SapoSapudo-Web-Prototype.zip"

cd "$ROOT"

if [ ! -d "$ROOT/assets" ]; then
  echo "ERROR: assets/ directory not found. The project cannot be packaged for itch.io without it."
  exit 1
fi

ASSET_COUNT="$(find "$ROOT/assets" -type f | wc -l | tr -d ' ')"
if [ "$ASSET_COUNT" -eq 0 ]; then
  echo "ERROR: assets/ directory is empty."
  exit 1
fi

echo "== Building web version =="
./scripts/build_web.sh

echo
echo "== Validating itch.io package =="
./scripts/check_web_build.sh

python - "$WEB_DIR" "$UPLOAD_DIR" "$UPLOAD_ZIP" <<'PY2'
from pathlib import Path
import sys, zipfile

web_dir = Path(sys.argv[1])
upload_dir = Path(sys.argv[2])
upload_zip = Path(sys.argv[3])

index = web_dir / "index.html"
if not index.is_file():
    raise SystemExit("ERROR: build/web/index.html was not generated")

files = [p for p in web_dir.rglob("*") if p.is_file()]
count = len(files)
size = sum(p.stat().st_size for p in files)
max_file = max((p.stat().st_size for p in files), default=0)
max_name = max((len(p.relative_to(web_dir).as_posix()) for p in files), default=0)

print(f"Files: {count}")
print(f"Uncompressed bytes: {size}")
print(f"Largest file: {max_file} bytes")
print(f"Longest path: {max_name} chars")

if count > 1000:
    raise SystemExit("ERROR: itch.io HTML5 ZIP limit exceeded: more than 1000 files")
if size > 500 * 1024 * 1024:
    raise SystemExit("ERROR: itch.io HTML5 ZIP limit exceeded: extracted content is over 500 MB")
if max_file > 200 * 1024 * 1024:
    raise SystemExit("ERROR: itch.io HTML5 ZIP limit exceeded: a file is over 200 MB")
if max_name > 240:
    raise SystemExit("ERROR: itch.io HTML5 ZIP limit exceeded: a path is over 240 characters")

with zipfile.ZipFile(upload_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for path in sorted(files):
        z.write(path, path.relative_to(web_dir).as_posix())

with zipfile.ZipFile(upload_zip) as z:
    names = z.namelist()
    if "index.html" not in names:
        raise SystemExit("ERROR: index.html is not at the root of the upload ZIP")

print()
print(f"ITCH_UPLOAD={upload_zip}")
print(f"Upload ZIP size: {upload_zip.stat().st_size} bytes")
PY2

echo
echo "Pronto para upload no itch.io:"
echo "  $UPLOAD_ZIP"
