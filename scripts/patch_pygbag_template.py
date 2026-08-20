#!/usr/bin/env python3
"""Patch the Pygbag template before it is used to serve the browser page."""

from __future__ import annotations

import re
import sys
from pathlib import Path

CSS = r"""
<style id="sapo-preloader-style">
html,body{
    margin:0!important;
    padding:0!important;
    width:100%!important;
    height:100%!important;
    overflow:hidden!important;
    background:#18364a!important;
}
#transfer{
    position:fixed!important;
    inset:0!important;
    z-index:2147483647!important;
    display:flex!important;
    flex-direction:column!important;
    align-items:center!important;
    justify-content:center!important;
    gap:14px!important;
    background:#18364a!important;
    margin:0!important;
    padding:0!important;
    text-align:center!important;
}
#transfer::before{
    content:"Sapo Sapudo";
    display:block;
    color:#f5f5f5;
    font-family:Arial,sans-serif;
    font-size:34px;
    font-weight:700;
    line-height:1.2;
}
#status{
    display:block!important;
    margin:0!important;
    color:#f5f5f5!important;
    font-family:Arial,sans-serif!important;
    font-size:20px!important;
    font-weight:700!important;
    line-height:1.3!important;
    min-height:28px!important;
}
#progress{
    appearance:none!important;
    -webkit-appearance:none!important;
    display:block!important;
    width:min(660px,78vw)!important;
    height:20px!important;
    margin:3px 0 0 0!important;
    border:0!important;
    border-radius:999px!important;
    background:#0e202c!important;
    overflow:hidden!important;
}
#progress::-webkit-progress-bar{
    background:#0e202c;
    border-radius:999px;
}
#progress::-webkit-progress-value{
    background:#8bd36b;
    border-radius:999px;
    transition:width .18s linear;
}
#progress::-moz-progress-bar{
    background:#8bd36b;
    border-radius:999px;
    transition:width .18s linear;
}
#sapo-indeterminate{
    position:absolute;
    left:0;
    top:0;
    width:100%;
    height:20px;
    border-radius:999px;
    overflow:hidden;
    pointer-events:none;
    background:linear-gradient(
        90deg,
        #0e202c 0%,
        #27495e 35%,
        #8bd36b 50%,
        #27495e 65%,
        #0e202c 100%
    );
    background-size:220% 100%;
    animation:sapo-loading 1.2s linear infinite;
}
@keyframes sapo-loading{
    0%{background-position:200% 0}
    100%{background-position:-20% 0}
}
canvas.emscripten{
    z-index:5!important;
}
html.sapo-python #sapo-indeterminate{
    display:none!important;
}
html.sapo-ready #transfer{
    display:none!important;
}
html.sapo-ready{
    background:transparent!important;
}
</style>
"""


def patch_template(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")

    original = text

    # The critical fix: the Pygbag bootstrap was explicitly hiding its
    # native transfer screen. Keep it visible until main.py finishes.
    text = text.replace(
        "    platform.window.transfer.hidden = true",
        "    platform.window.transfer.hidden = false",
    )
    text = text.replace(
        "        transfer.hidden = debug_hidden",
        "        transfer.hidden = false",
    )

    # The native template background is powderblue while the loader should be visible.
    text = text.replace(
        "background-color:powderblue;",
        "background-color:#18364a;",
    )
    text = text.replace(
        'platform.document.body.style.background = "#7f7f7f"',
        'platform.document.body.style.background = "#18364a"',
    )

    # Insert the loader CSS once.
    text = re.sub(
        r'<style id="sapo-preloader-style">.*?</style>',
        "",
        text,
        flags=re.S,
    )
    if "</head>" in text:
        text = text.replace("</head>", CSS + "\n</head>", 1)

    # Replace the initial label.
    text = re.sub(
        r'(<div class="emscripten" id="status">).*?(</div>)',
        r"\1Preparando o jogo...\2",
        text,
        count=1,
        flags=re.S,
    )

    # Add indeterminate animation over the native progress bar for the
    # period in which Pygbag has not published a numeric progress yet.
    marker = '<div class="emscripten">\n            <progress value="0" max="100" id="progress"></progress>\n        </div>'
    replacement = (
        '<div class="emscripten" style="position:relative">\n'
        '            <progress value="0" max="100" id="progress"></progress>\n'
        '            <div id="sapo-indeterminate" aria-hidden="true"></div>\n'
        "        </div>"
    )
    if marker in text:
        text = text.replace(marker, replacement, 1)
    elif 'id="sapo-indeterminate"' not in text and "</progress>" in text:
        text = text.replace(
            "</progress>",
            '</progress><div id="sapo-indeterminate" aria-hidden="true"></div>',
            1,
        )

    # Never allow the loader to be hidden by custom_onload.
    text = text.replace(
        "        transfer.hidden = debug_hidden\n",
        "        transfer.hidden = false\n",
    )

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def patch_tree(root: Path) -> int:
    changed = 0
    for path in root.rglob("*.tmpl"):
        if patch_template(path):
            changed += 1
    return changed


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch_pygbag_template.py <root>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    if not root.exists():
        print(f"template root does not exist: {root}", file=sys.stderr)
        return 2

    changed = patch_tree(root)
    print(f"Patched Pygbag templates: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
