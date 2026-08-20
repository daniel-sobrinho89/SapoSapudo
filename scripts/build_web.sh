#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$ROOT/build/web_source"
PYGBAG_BUILD="$WORK/build/web"
FINAL_WEB="$ROOT/build/web"
FINAL_ZIP="$ROOT/build/web.zip"

# Fail early when the source package is missing the runtime assets.
# Pygbag cannot produce a playable build without them.
if [ ! -d "$ROOT/assets" ]; then
  echo "ERROR: assets/ directory not found at $ROOT/assets"
  echo "The web build requires the game's assets/ directory."
  exit 1
fi
ASSET_COUNT="$(find "$ROOT/assets" -type f | wc -l | tr -d " ")"
if [ "$ASSET_COUNT" -eq 0 ]; then
  echo "ERROR: assets/ exists but contains no files."
  exit 1
fi
echo "Web assets found: $ASSET_COUNT files"

rm -rf "$WORK" "$FINAL_WEB" "$FINAL_ZIP" "$ROOT/build/web-cache"
mkdir -p "$WORK" "$ROOT/build"

copy_tree() {
  local src="$1"
  local dst="$2"

  if command -v rsync >/dev/null 2>&1; then
    rsync -a \
      --exclude='.venv/' \
      --exclude='venv/' \
      --exclude='__pycache__/' \
      --exclude='*.pyc' \
      --exclude='*.pyo' \
      "$src/" "$dst/"
  else
    tar -C "$ROOT" \
      --exclude='*/.venv' \
      --exclude='*/venv' \
      --exclude='*/__pycache__' \
      --exclude='*.pyc' \
      --exclude='*.pyo' \
      -cf - "$(basename "$src")" \
      | tar -C "$WORK" -xf -
  fi
}

for d in application core data domains render utils assets; do
  if [ -d "$ROOT/$d" ]; then
    mkdir -p "$WORK/$d"
    copy_tree "$ROOT/$d" "$WORK/$d"
  fi
done

cp "$ROOT/main_web.py" "$WORK/main.py"

find "$WORK" -type d \
  \( -name .venv -o -name venv -o -name __pycache__ \) \
  -prune -exec rm -rf {} +
find "$WORK" -type f \
  \( -name '*.pyc' -o -name '*.pyo' \) \
  -delete

echo "Web source prepared: $WORK"

PYGBAG_REQUIRED_VERSION="0.9.3"
PYGBAG_INSTALLED_VERSION="$(python - <<'PY'
import importlib.metadata
try:
    print(importlib.metadata.version("pygbag"))
except importlib.metadata.PackageNotFoundError:
    print("")
PY
)"

if [ "$PYGBAG_INSTALLED_VERSION" != "$PYGBAG_REQUIRED_VERSION" ]; then
  echo "Installing pygbag==$PYGBAG_REQUIRED_VERSION (current: ${PYGBAG_INSTALLED_VERSION:-not installed})"
  python -m pip install --disable-pip-version-check --no-input --upgrade "pygbag==$PYGBAG_REQUIRED_VERSION"
fi

PYGBAG_FINAL_VERSION="$(python - <<'PY'
import importlib.metadata
print(importlib.metadata.version("pygbag"))
PY
)"

if [ "$PYGBAG_FINAL_VERSION" != "$PYGBAG_REQUIRED_VERSION" ]; then
  echo "ERROR: pygbag version is $PYGBAG_FINAL_VERSION; expected $PYGBAG_REQUIRED_VERSION"
  exit 1
fi

echo "Using pygbag $PYGBAG_FINAL_VERSION"

cd "$ROOT"
python -m pygbag \
    --build \
    --archive \
    --ume_block 0 \
    --app_name "Sapo Sapudo" \
    --title "Sapo Sapudo" \
    --package "br.com.saposapudo.web" \
    --version "0.9.3" \
    --PYBUILD "3.12" \
    --cdn "https://pygame-web.github.io/archives/0.9/" \
    "$WORK"

if [ ! -d "$PYGBAG_BUILD" ]; then
  echo "Pygbag build directory not found: $PYGBAG_BUILD"
  exit 1
fi

python "$ROOT/scripts/patch_pygbag_template.py" "$WORK/build/web-cache"

mkdir -p "$FINAL_WEB"
cp -a "$PYGBAG_BUILD"/. "$FINAL_WEB"/

WEB_INDEX="$FINAL_WEB/index.html"
if [ ! -f "$WEB_INDEX" ]; then
  echo "ERROR: generated web index not found: $WEB_INDEX"
  exit 1
fi

python - "$WEB_INDEX" <<'PY'
from pathlib import Path
import re
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")

# Pygbag 0.9.3 generates data-python=python3.12 (normally unquoted).
# Do not rewrite it to cpython3.12: python3.12 is the selector emitted by
# the official 0.9 runtime template. Normalize only malformed relative URLs.
s = s.replace(
    "https://pygame-web.github.io/archives/0.9//",
    "https://pygame-web.github.io/archives/0.9/",
)
s = s.replace(
    "http://localhost:8000/archives/0.9//",
    "http://localhost:8000/archives/0.9/",
)
s = s.replace(
    "//archives/0.9/",
    "https://pygame-web.github.io/archives/0.9/",
)
s = re.sub(
    r'([=\'"])\/archives/0\.9/',
    r'\1https://pygame-web.github.io/archives/0.9/',
    s,
)

p.write_text(s, encoding="utf-8")
PY

if grep -Rqi 'archives/0\.8' "$WEB_INDEX"; then
  echo "ERROR: generated web artifact still references the obsolete 0.8 archive/runtime."
  exit 1
fi

if grep -Eq 'archives/0\.9//|cdn/0\.9\.3' "$WEB_INDEX"; then
  echo "ERROR: generated web artifact contains a malformed/obsolete runtime URL."
  grep -nE 'archives/0\.9//|cdn/0\.9\.3' "$WEB_INDEX" || true
  exit 1
fi

python - "$WEB_INDEX" <<'PY3'
from pathlib import Path
import re
import sys

s = Path(sys.argv[1]).read_text(encoding="utf-8")
match = re.search(
    r'data-python\s*=\s*["\']?(?:python|cpython)3\.12["\']?(?=[\s>])',
    s,
)
if not match:
    print("ERROR: generated web artifact does not select Python 3.12.")
    sys.exit(1)
print(f"Python web runtime selector: {match.group(0)}")
PY3

python - "$WEB_INDEX" <<'PY2'
from pathlib import Path
import re
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")

s = s.replace(
    '    platform.document.body.style.background = "#7f7f7f"',
    '    platform.document.body.style.background = "#18364a"',
)
s = s.replace(
    '    platform.window.transfer.hidden = true',
    '    platform.window.transfer.hidden = false',
)
s = s.replace(
    '        transfer.hidden = debug_hidden',
    '        transfer.hidden = false',
)

css = r"""<style id="sapo-preloader-style">
:root{--sapo-percent:"0%";}
html,body{margin:0!important;padding:0!important;width:100%!important;height:100%!important;overflow:hidden!important;background:#18364a!important;}
#transfer{position:fixed!important;inset:0!important;z-index:2147483647!important;display:flex!important;flex-direction:column!important;align-items:center!important;justify-content:center!important;gap:14px!important;background:#18364a!important;margin:0!important;padding:0!important;text-align:center!important;}
#transfer::before{content:"Sapo Sapudo";display:block;color:#f5f5f5;font-family:Arial,sans-serif;font-size:34px;font-weight:700;line-height:1.2;}
#status{display:block!important;margin:0!important;color:#f5f5f5!important;font-family:Arial,sans-serif!important;font-size:20px!important;font-weight:700!important;line-height:1.3!important;min-height:28px!important;}
#progress{appearance:none!important;-webkit-appearance:none!important;display:block!important;width:min(660px,78vw)!important;height:20px!important;margin:3px 0 0 0!important;border:0!important;border-radius:999px!important;background:#0e202c!important;overflow:hidden!important;}
#progress::-webkit-progress-bar{background:#0e202c;border-radius:999px;}
#progress::-webkit-progress-value{background:#8bd36b;border-radius:999px;transition:width .18s linear;}
#progress::-moz-progress-bar{background:#8bd36b;border-radius:999px;transition:width .18s linear;}
#transfer::after{content:var(--sapo-percent);display:block;color:#f5f5f5;font-family:Arial,sans-serif;font-size:18px;font-weight:700;min-height:24px;}
#sapo-indeterminate{position:absolute;left:0;top:0;width:min(660px,78vw);height:20px;border-radius:999px;overflow:hidden;pointer-events:none;background:linear-gradient(90deg,#0e202c 0%,#27495e 35%,#8bd36b 50%,#27495e 65%,#0e202c 100%);background-size:220% 100%;animation:sapo-loading 1.2s linear infinite;}
html.sapo-python #sapo-indeterminate{display:none!important;}
@keyframes sapo-loading{0%{background-position:200% 0}100%{background-position:-20% 0}}
canvas.emscripten{z-index:5!important;}
html.sapo-ready #transfer{display:none!important;}
html.sapo-ready{background:transparent!important;}
</style>"""

s = re.sub(r'<style id="sapo-preloader-style">.*?</style>', '', s, flags=re.S)
s = s.replace('</head>', css + '</head>', 1)
s = re.sub(r'(<div class="emscripten" id="status">).*?(</div>)', r'\1Preparando o jogo...\2', s, count=1, flags=re.S)
s = s.replace(
    '<div class="emscripten">\n            <progress value="0" max="100" id="progress"></progress>\n        </div>',
    '<div class="emscripten" style="position:relative">\n            <progress value="0" max="100" id="progress"></progress>\n            <div id="sapo-indeterminate" aria-hidden="true"></div>\n        </div>',
    1,
)
if 'id="sapo-indeterminate"' not in s:
    s = s.replace('</progress>', '</progress><div id="sapo-indeterminate" aria-hidden="true"></div>', 1)
s = s.replace('        transfer.hidden = debug_hidden\n', '        transfer.hidden = false\n')
s = s.replace(
    '        show_infobox()\n',
    '        status.innerText = "Preparando o jogo..."\n        progress.value = 0\n        document.documentElement.style.setProperty("--sapo-percent", "0%")\n        show_infobox()\n',
    1,
)
s = s.replace('status.innerText = "Downloading..."', 'status.innerText = "Preparando o jogo..."')
p.write_text(s, encoding="utf-8")
PY2

# The official itch artifact is always build/web.zip at the project root.
python - "$FINAL_WEB" "$FINAL_ZIP" <<'PY'
from pathlib import Path
import sys, zipfile

src = Path(sys.argv[1])
out = Path(sys.argv[2])
with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for path in sorted(src.rglob("*")):
        if path.is_file():
            z.write(path, path.relative_to(src).as_posix())
PY

echo "Browser build directory: $FINAL_WEB"
echo "Browser archive: $FINAL_ZIP"
