from html import escape

from tests.integration.harness.geometry import TestRect

TILE = 64


def _esc(v):
    return escape(str(v), quote=True)


def rect(x, y, w, h, fill, stroke=None, sw=1, opacity=1.0):
    ex = f" stroke='{stroke}' stroke-width='{sw}'" if stroke else ""
    return f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' fill='{fill}' opacity='{opacity}'{ex}/>"


def circle(x, y, r, fill, stroke="#fff", sw=2):
    return f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{r:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>"


def line(x1, y1, x2, y2, stroke="#f5e663", sw=3, dash=None):
    ex = f" stroke-dasharray='{dash}'" if dash else ""
    return f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' stroke='{stroke}' stroke-width='{sw}'{ex}/>`".replace(
        "`", ""
    )


def text(x, y, v, size=12, fill="#fff", weight="normal", anchor="start"):
    return f"<text x='{x:.1f}' y='{y:.1f}' font-family='sans-serif' font-size='{size}px' font-weight='{weight}' fill='{fill}' text-anchor='{anchor}'>{_esc(v)}</text>"


def base(tilemap):
    w, h = tilemap.largura * TILE, tilemap.altura * TILE
    out = [rect(0, 0, w, h, "#4e7f4a")]
    for y in range(tilemap.altura):
        for x in range(tilemap.largura):
            fill = "#79a963" if tilemap.obter_altura(x, y) > 0 else "#4e7f4a"
            if (x, y) in getattr(tilemap, "tiles_bloqueados", set()):
                fill = "#41454b"
            out.append(rect(x * TILE, y * TILE, TILE, TILE, fill, "#315d3c", 1))
    return out


def relief_overlay(tilemap):
    """Representação próxima do jogo: topo elevado, parede do penhasco e degrau conectado."""
    out = []
    groups = {}
    for y in range(tilemap.altura):
        for x in range(tilemap.largura):
            h = tilemap.obter_altura(x, y)
            if h > 0:
                groups.setdefault(h, []).append((x, y))

    for h, cells in sorted(groups.items()):
        x0 = min(x for x, _ in cells) * TILE
        x1 = (max(x for x, _ in cells) + 1) * TILE
        y0 = min(y for _, y in cells) * TILE
        y1 = (max(y for _, y in cells) + 1) * TILE

        # Área superior do relevo, com cor própria.
        out.append(rect(x0, y0, x1 - x0, y1 - y0, "#6f9f59", "#d8e58a", 2, 0.95))
        out.append(rect(x0, y0, x1 - x0, TILE * 0.28, "#8fb56e", None, 0, 1.0))

        # Parede vertical frontal, para deixar claro que existe desnível físico.
        wall_y = y1 - TILE * 0.34
        out.append(
            rect(x0, wall_y, x1 - x0, TILE * 0.34, "#5c493c", "#3a2d28", 1, 0.95)
        )
        out.append(text(x0 + 8, y0 + 18, f"RELEVO · nível {h}", 10, "#f7ffd0", "bold"))

    # Degraus ficam encostados na borda do relevo, como uma passagem de nível,
    # e não soltos ao lado da área elevada.
    for (x, y), d in tilemap.degraus.items():
        px, py = x * TILE, y * TILE
        low = d["altura_baixa"]
        high = d["altura_alta"]
        out.append(rect(px, py, TILE, TILE, "#c58b4a", "#fff0b0", 2, 1.0))
        out.append(
            rect(px + 4, py + 5, TILE - 8, TILE - 10, "#e2ab5f", "#8f5c30", 1, 1.0)
        )
        out.append(line(px + 7, py + TILE - 8, px + TILE - 7, py + 8, "#fff1b3", 2))
        out.append(
            text(
                px + TILE / 2,
                py + TILE - 7,
                f"{low}→{high}",
                8,
                "#3a2618",
                "bold",
                "middle",
            )
        )
        out.append(text(px + TILE + 6, py + 15, "DEGRAU", 8, "#fff0b0", "bold"))
    return out


def pathline(points, color="#f5e663", width=5, dash=None):
    if len(points) < 2:
        return []
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    ex = f" stroke-dasharray='{dash}'" if dash else ""
    return [
        f"<polyline points='{pts}' fill='none' stroke='{color}' stroke-width='{width}' stroke-linecap='round' stroke-linejoin='round'{ex}/>"
    ]


def health(out, x, y, label, current, maximum, width=190):
    maximum = max(1, maximum)
    pct = max(0, min(current / maximum, 1))
    out.append(text(x, y - 5, f"{label}: {current}/{maximum}", 10, "#fff", "bold"))
    out.append(rect(x, y, width, 10, "#3a2525", "#ead6ad", 1))
    out.append(rect(x, y, width * pct, 10, "#d65b48"))


def footer(out, y, w, lines):
    out.append(rect(0, y, w, 118, "#18364a"))
    yy = y + 20
    for v, c, b in lines:
        out.append(text(12, yy, v, 10, c, "bold" if b else "normal"))
        yy += 18


def stage_svg(title, subtitle, tilemap, stages, legend_height=118):
    w = tilemap.largura * TILE
    map_h = tilemap.altura * TILE
    ph = map_h + legend_height
    gap = 28
    H = 68 + len(stages) * (ph + gap)
    out = [
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {H}' width='{w}' height='{H}'>",
        rect(0, 0, w, H, "#102735"),
        text(18, 27, title, 18, "#fff", "bold"),
        text(18, 48, subtitle, 11, "#cfe6ef"),
    ]
    for i, stage in enumerate(stages):
        yoff = 68 + i * (ph + gap)
        out.append(f"<g transform='translate(0,{yoff})'>")
        out += base(tilemap)
        out += stage.get("overlay", [])
        out += stage.get("art", [])
        footer(out, map_h, w, stage.get("footer", []))
        out.append("</g>")
    out.append("</svg>")
    return "\n".join(out)


def combat_trace_scene(nome, tilemap, trace, dados):
    trace = trace or []
    stages = []
    if "start" not in dados and "soldado" in dados:
        dados = dict(dados)
        dados["start"] = dados["soldado"]
        dados["goal"] = dados["goblin"]
    if "construction" not in dados and dados.get("construcao"):
        cx, cy, size = dados["construcao"]
        dados = dict(dados)
        dados["construction"] = {"x": cx, "y": cy, "size": size}
    if "construction" not in dados and dados.get("obstacles"):
        ox, oy, ow, oh = dados["obstacles"][0]
        dados = dict(dados)
        dados["construction"] = {"x": ox + ow / 2, "y": oy + oh / 2, "size": ow}
    if not trace:
        raise ValueError(f"{nome}: fluxo real não forneceu trace")
    if "start" not in dados and trace:
        dados = dict(dados)
        first = trace[0]
        last = trace[-1]
        dados["start"] = (first.get("x", 0), first.get("y", 0))
        dados["goal"] = (
            last.get("goblin_x", last.get("x", 0)),
            last.get("goblin_y", last.get("y", 0)),
        )
        # sample 6 actual states
    idxs = (
        sorted(
            set(
                round(i * (len(trace) - 1) / min(5, len(trace) - 1))
                for i in range(min(6, len(trace)))
            )
        )
        if len(trace) > 1
        else [0]
    )
    for j, idx in enumerate(idxs):
        t = trace[idx]
        art = []
        overlay = []
        if nome in ("inimigos_em_niveis_diferentes", "goblin_no_degrau"):
            art += relief_overlay(tilemap)
        sx = t.get("x", dados["start"][0])
        sy = t.get("y", dados["start"][1])
        gx = t.get("goblin_x", dados["goal"][0])
        gy = t.get("goblin_y", dados["goal"][1])
        if dados.get("construction"):
            c = dados["construction"]
            o = TestRect(
                c["x"] - c["size"] / 2, c["y"] - c["size"] / 2, c["size"], c["size"]
            )
            art.append(rect(o.left, o.top, o.w, o.h, "#6c472d", "#e1c17a", 3))
        art += pathline(
            [
                (trace[k].get("x"), trace[k].get("y"))
                for k in idxs[: j + 1]
                if trace[k].get("x") is not None
            ]
        )
        art += [circle(sx, sy, 10, "#4b82dc"), circle(gx, gy, 10, "#d85742")]
        if nome == "soldado_defende_construcao":
            cc = dados["construction"]
            art.append(
                rect(
                    cc["x"] - cc["size"] / 2,
                    cc["y"] - cc["size"] / 2,
                    cc["size"],
                    cc["size"],
                    "#6c472d",
                    "#e1c17a",
                    3,
                )
            )
            health(
                art,
                12,
                cc["y"] - cc["size"] / 2 - 28,
                "Construção",
                t.get("vida_construcao", 0),
                200,
                220,
            )
            health(
                art,
                250,
                cc["y"] - cc["size"] / 2 - 28,
                "Goblin",
                t.get("vida_goblin", 200),
                200,
                190,
            )
            alvo = t.get("alvo_goblin", "construção")
            status = f"Goblin está atacando: {alvo}"
            if alvo == "soldado":
                art.append(line(gx, gy, sx, sy, "#f0a45d", 3, "6 5"))
            footer_lines = (
                [
                    f"Etapa {j + 1}/{len(idxs)} · vida da construção e troca de alvo",
                    "#d7efcc",
                    False,
                ]
                if False
                else [
                    (
                        f"Etapa {j + 1}/{len(idxs)} · goblin → construção → soldado",
                        "#fff",
                        True,
                    ),
                    (
                        f"Construção: {t.get('vida_construcao', 0)}/200 · Goblin: {t.get('vida_goblin', 0)}/200",
                        "#ffd39e",
                        True,
                    ),
                    (status, "#f5e663", True),
                    (
                        "amarelo = movimento real · linha laranja = ataque do goblin",
                        "#cfe6ef",
                        False,
                    ),
                ]
            )
        elif nome in ("inimigos_em_niveis_diferentes", "goblin_no_degrau"):
            hs = t.get("altura_soldado", 0)
            hg = t.get("altura_goblin", 1)
            footer_lines = [
                (
                    f"Etapa {j + 1}/{len(idxs)} · combate real entre níveis",
                    "#fff",
                    True,
                ),
                (
                    f"Soldado: altura {hs} · {'ABAIXO' if hs == 0 else 'ACIMA'} do relevo",
                    "#d7efcc",
                    True,
                ),
                (
                    f"Goblin: altura {hg} · {'ABAIXO' if hg == 0 else 'ACIMA'} do relevo",
                    "#d7efcc",
                    True,
                ),
                (f"Vida do goblin: {t.get('vida_goblin', 200)}/200", "#ffd39e", True),
                (
                    "azul = relevo · laranja = degrau · amarelo = movimento real",
                    "#f5e663",
                    False,
                ),
            ]
        else:
            health(art, 12, 18, "Soldado", t.get("vida_soldado", 300), 300, 180)
            health(art, 215, 18, "Goblin", t.get("vida_goblin", 200), 200, 180)
            footer_lines = [
                (f"Etapa {j + 1}/{len(idxs)} · combate real", "#fff", True),
                (
                    f"Soldado: {t.get('vida_soldado', 300)}/300 · Goblin: {t.get('vida_goblin', 200)}/200",
                    "#ffd39e",
                    True,
                ),
                ("amarelo = caminho real do teste", "#f5e663", False),
            ]
        stages.append({"art": art, "overlay": overlay, "footer": footer_lines})
    sub = "ESTADOS CAPTURADOS DURANTE A EXECUÇÃO REAL DO TESTE"
    if nome == "soldado_contorna_construcao":
        sub += " · rota registrada pelo UseCase"
    return stage_svg(nome + " · fluxo real", sub, tilemap, stages)


def movement_scene(nome, tilemap, trace, dados):
    if not trace:
        raise ValueError(f"{nome}: fluxo real não forneceu trace")
    idxs = (
        sorted(
            set(
                round(i * (len(trace) - 1) / min(6, len(trace) - 1))
                for i in range(min(7, len(trace)))
            )
        )
        if len(trace) > 1
        else [0]
    )
    stages = []
    prev = None
    for j, idx in enumerate(idxs):
        t = trace[idx]
        pos = (t["x"], t["y"])
        h = t.get("altura", 0)
        art = []
        art += relief_overlay(tilemap) if "degrau" in nome or tilemap.degraus else []

        # Obstáculos reais definidos no cenário são desenhados sobre o mapa.
        for obstacle in dados.get("obstacles", []):
            ox, oy, ow, oh = obstacle
            art.append(rect(ox, oy, ow, oh, "#6c472d", "#e1c17a", 3))
            art.append(
                text(
                    ox + ow / 2,
                    oy + oh / 2,
                    "OBSTÁCULO",
                    12,
                    "#fff2c4",
                    "bold",
                    "middle",
                )
            )

        actual = [(q["x"], q["y"]) for q in trace[: idx + 1]]
        art += pathline(actual)
        art += [circle(*pos, 11, "#4b82dc"), circle(*dados["goal"], 9, "#d85742")]
        if prev is not None and h != prev:
            art.append(
                line(pos[0], pos[1], pos[0] + 28, pos[1] - 20, "#ffcf70", 3, "5 4")
            )
            art.append(
                text(
                    pos[0] + 32, pos[1] - 22, f"altura {prev}→{h}", 9, "#ffe1a3", "bold"
                )
            )
        region = "acima do relevo" if h > 0 else "abaixo do relevo"
        footer_lines = [
            (f"Etapa {j + 1}/{len(idxs)} · altura atual: {h}", "#fff", True),
            (f"Área de relevo: nível {h} · personagem {region}", "#d7efcc", True),
        ]
        if prev is not None and h != prev:
            footer_lines.append(
                (f"altura antes/depois do degrau: {prev} → {h}", "#ffd39e", True)
            )
        else:
            footer_lines.append(
                ("sem transição de degrau nesta etapa", "#cfe6ef", False)
            )
        if dados.get("obstacles"):
            footer_lines.append(
                (
                    "marrom = obstáculo/construção · amarelo = caminho real percorrido",
                    "#f5e663",
                    False,
                )
            )
        else:
            footer_lines.append(
                (
                    "verde = relevo elevado · laranja = degrau · amarelo = caminho real",
                    "#f5e663",
                    False,
                )
            )
        stages.append({"art": art, "footer": footer_lines})
        prev = h
    return stage_svg(
        nome + " · fluxo real",
        "POSIÇÕES, RELEVO E OBSTÁCULOS CAPTURADOS DURANTE A EXECUÇÃO",
        tilemap,
        stages,
    )


def gathering_scene(nome, tilemap, trace, dados):
    if not trace:
        raise ValueError(f"{nome}: fluxo real não forneceu trace")
    idxs = (
        sorted(
            set(
                round(i * (len(trace) - 1) / min(5, len(trace) - 1))
                for i in range(min(6, len(trace)))
            )
        )
        if len(trace) > 1
        else [0]
    )
    tree_data = dados.get("tree") or dados.get("arvore")
    tree = (
        {"x": tree_data[0], "y": tree_data[1]}
        if isinstance(tree_data, tuple)
        else tree_data
    )
    stages = []
    for j, idx in enumerate(idxs):
        t = trace[idx]
        art = [circle(tree["x"], tree["y"], 16, "#3d8b4b", "#b8e59f", 3)]
        aldeoes = t["aldeoes"]
        for k, a in enumerate(aldeoes):
            art += pathline(
                [
                    (x["x"], x["y"])
                    for x in trace[: idx + 1]
                    for x in ([x["aldeoes"][k]] if k < len(x["aldeoes"]) else [])
                ]
            )
            art.append(circle(a["x"], a["y"], 10, "#4b82dc"))
            if a.get("cortando"):
                art.append(
                    line(a["x"], a["y"], tree["x"], tree["y"], "#c5d85d", 3, "4 4")
                )
        footer = [
            (f"Etapa {j + 1}/{len(idxs)} · {len(aldeoes)} aldeão(ões)", "#fff", True),
            (f"Árvore alvo: ({tree['x']},{tree['y']})", "#d7efcc", False),
            (
                f"Cortando agora: {sum(1 for a in aldeoes if a.get('cortando'))}/{len(aldeoes)}",
                "#ffd39e",
                True,
            ),
            (
                "azul = aldeão · amarelo = percurso real · linha verde = ação de corte",
                "#f5e663",
                False,
            ),
        ]
        stages.append({"art": art, "footer": footer})
    return stage_svg(
        nome + " · fluxo real",
        "ESTADOS CAPTURADOS ENQUANTO O USE CASE DE CORTE É EXECUTADO",
        tilemap,
        stages,
    )


def construction_attack_scene(nome, tilemap, trace, dados):
    if "construction" not in dados:
        cx, cy, size = dados["construcao"]
        dados = dict(dados)
        dados["construction"] = {"x": cx, "y": cy, "size": size}
    if not trace:
        raise ValueError(f"{nome}: fluxo real não forneceu trace")
    idxs = (
        sorted(
            set(
                round(i * (len(trace) - 1) / min(4, len(trace) - 1))
                for i in range(min(5, len(trace)))
            )
        )
        if len(trace) > 1
        else [0]
    )
    c = dados["construction"]
    o = TestRect(c["x"] - c["size"] / 2, c["y"] - c["size"] / 2, c["size"], c["size"])
    stages = []
    initial = max([t.get("vida_construcao", 0) for t in trace] + [0])
    for j, idx in enumerate(idxs):
        t = trace[idx]
        art = [
            rect(o.left, o.top, o.w, o.h, "#6c472d", "#e1c17a", 3),
            text(c["x"], c["y"], "CONSTRUÇÃO", 12, "#fff2c4", "bold", "middle"),
            circle(t["s1x"], t["s1y"], 10, "#4b82dc"),
            circle(t["s2x"], t["s2y"], 10, "#6096db"),
        ]
        for key in ("s1", "s2"):
            art += pathline(
                [(q[key + "x"], q[key + "y"]) for q in trace[: idx + 1]], "#f5e663"
            )
        current = t.get("vida_construcao", initial)
        health(art, 12, 18, "Construção", current, initial, 220)
        if current < initial:
            art.append(line(t["s1x"], t["s1y"], c["x"], c["y"], "#ff9f43", 3, "5 4"))
            art.append(line(t["s2x"], t["s2y"], c["x"], c["y"], "#ff9f43", 3, "5 4"))
            art.append(
                text(
                    c["x"],
                    c["y"] - c["size"] / 2 - 38,
                    "ATAQUE",
                    9,
                    "#ffbf70",
                    "bold",
                    "middle",
                )
            )
        footer = [
            (f"Etapa {j + 1}/{len(idxs)} · ataque real à construção", "#fff", True),
            (f"Vida da construção: {current}/{initial}", "#ffd39e", True),
            (
                "amarelo = movimento real · laranja = golpes efetivamente executados",
                "#f5e663",
                False,
            ),
        ]
        stages.append({"art": art, "footer": footer})
    return stage_svg(
        nome + " · fluxo real",
        "ESTADOS CAPTURADOS DURANTE O ATAQUE REAL DOS SOLDADOS",
        tilemap,
        stages,
    )


def simple_scene(nome, tilemap, trace, dados):
    if not trace:
        raise ValueError(f"{nome}: fluxo real não forneceu trace")
    t = trace[-1]
    stages = []
    art = []
    if "x" in t:
        art.append(circle(t["x"], t["y"], 11, "#4b82dc"))
    if "goblin_x" in t:
        art.append(circle(t["goblin_x"], t["goblin_y"], 10, "#d85742"))
    stages.append(
        {
            "art": art,
            "footer": [
                (nome, "#fff", True),
                (
                    "visualização baseada no estado final real da execução",
                    "#d7efcc",
                    False,
                ),
            ],
        }
    )
    return stage_svg(
        nome + " · estado real", "CAPTURA FINAL DO FLUXO EXECUTADO", tilemap, stages
    )


def gerar_cena(nome, fixture, dados, caminho, trace=None):
    tilemap = (trace or {}).get("tilemap") if isinstance(trace, dict) else None
    if tilemap is None:
        raise ValueError(
            f"{nome}: visualização recusada porque o runtime real não forneceu o tilemap"
        )
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if not trace:
        raise ValueError(
            f"{nome}: visualização recusada porque não há trace da execução real"
        )
    kind = trace.get("kind") if isinstance(trace, dict) else None
    tr = trace.get("trace", []) if isinstance(trace, dict) else trace
    if kind in ("movement", "combat_step"):
        svg = (
            movement_scene(nome, tilemap, tr, dados)
            if kind == "movement"
            else combat_trace_scene(nome, tilemap, tr, dados)
        )
    elif kind == "gathering":
        svg = gathering_scene(nome, tilemap, tr, dados)
    elif kind in ("combat_construction", "defend_construction"):
        svg = combat_trace_scene(nome, tilemap, tr, dados)
    elif kind == "construction_attack":
        svg = construction_attack_scene(nome, tilemap, tr, dados)
    elif kind == "combat":
        svg = combat_trace_scene(nome, tilemap, tr, dados)
    else:
        svg = simple_scene(nome, tilemap, tr, dados)
    caminho.write_text(svg, encoding="utf-8")
    return caminho, {"trace_points": len(tr)}
