from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from core.camera import Camera
from render.tilemap_renderer import TileMapRenderer
from render.transform_utils import TransformUtils
from utils.kivy_adapter import Surface
from utils.paths import BASE_DIR

TILE = 64


class VisualAssets:
    """Carrega os mesmos PNG/WebP do jogo, sem depender do CoreImage/Kivy."""

    def __init__(self):
        self._cache = {}
        self._frames = {}
        self._config = json.loads(
            (BASE_DIR / "data" / "sprites_config.json").read_text(encoding="utf-8")
        )

    def carregar(self, nome):
        if nome in self._cache:
            return self._cache[nome]
        caminho = BASE_DIR / "assets" / nome
        if not caminho.exists():
            raise FileNotFoundError(
                f"Asset visual não encontrado: {caminho}. "
                "Os GIFs reais precisam ser executados dentro do projeto que contém a pasta assets/."
            )
        with Image.open(caminho) as imagem:
            rgba = imagem.convert("RGBA")
        surface = Surface(rgba.size)
        surface._img = rgba
        self._cache[nome] = surface
        return surface

    def frames(self, tipo):
        tipo = tipo.lower()
        if tipo in self._frames:
            return self._frames[tipo]
        config = self._config[tipo]
        flip = config.get("flip", False)
        resultado = {}
        for estado, dados in config.get("animacoes", {}).items():
            sheet = self.carregar(dados["arquivo"]).pil_image()
            total = dados["frames"]
            fw = sheet.width // total
            fh = sheet.height
            frames = []
            for i in range(total):
                frame = sheet.crop((i * fw, 0, (i + 1) * fw, fh))
                frames.append(frame)
            resultado[estado] = frames
            if flip:
                resultado[f"{estado}_flip"] = [
                    ImageOps.mirror(frame) for frame in frames
                ]
        self._frames[tipo] = resultado
        return resultado

    def config(self, tipo):
        return self._config[tipo.lower()]


def _font(size, bold=False):
    nome = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    caminho = Path("/usr/share/fonts/truetype/dejavu") / nome
    try:
        return ImageFont.truetype(str(caminho), size)
    except OSError:
        return ImageFont.load_default()


FONT_TITLE = _font(18, True)
FONT_HUD = _font(12, True)
FONT_SMALL = _font(11)
FONT_SMALL_B = _font(11, True)


def _clamp(v, a, b):
    return max(a, min(v, b))


def _snapshot_state(item):
    estado = item.get("estado", "ocioso") or "ocioso"
    frame = int(item.get("frame", 0) or 0)
    return estado, max(0, frame)


def _sprite_from_trace(assets, item, out_scale=1.0):
    tipo = item["nome"].lower()
    frames = assets.frames(tipo)
    estado, indice = _snapshot_state(item)
    candidatos = [estado, estado.replace("_flip", ""), "ocioso"]
    frames_ativos = next((frames.get(k) for k in candidatos if frames.get(k)), None)
    if not frames_ativos:
        return None
    indice = min(indice, len(frames_ativos) - 1)
    imagem = frames_ativos[indice]

    cfg = assets.config(tipo)
    escala = float(cfg.get("renderer", {}).get("escala", 1.0))
    escala_x = float(item.get("escala_x", 0.9))
    escala_y = float(item.get("escala_y", 0.9))
    largura = max(1, round(imagem.width * escala * escala_x * out_scale))
    altura = max(1, round(imagem.height * escala * escala_y * out_scale))
    return imagem.resize((largura, altura), Image.Resampling.NEAREST)


def _effect_sprite_from_trace(assets, item, out_scale=1.0):
    tipo = item["nome"].lower()
    frames = assets.frames(tipo)
    estado, indice = _snapshot_state(item)
    frames_ativos = (
        frames.get(estado)
        or frames.get(estado.replace("_flip", ""))
        or frames.get("ocioso")
    )
    if not frames_ativos:
        return None
    indice = min(indice, len(frames_ativos) - 1)
    imagem = frames_ativos[indice]
    cfg = assets.config(tipo)
    escala = float(cfg.get("renderer", {}).get("escala", 1.0))
    escala_x = float(item.get("escala_x", 1.0))
    escala_y = float(item.get("escala_y", 1.0))
    largura = max(1, round(imagem.width * escala * escala_x * out_scale))
    altura = max(1, round(imagem.height * escala * escala_y * out_scale))
    return imagem.resize((largura, altura), Image.Resampling.NEAREST)


def _sprite_position(camera, item, image):
    x, y = camera.tela(item["x"], item["y"])
    return int(x - image.width / 2), int(y - image.height / 2)


def _health(draw, x, y, label, current, maximum, width=150):
    maximum = max(1, float(maximum))
    pct = max(0.0, min(1.0, float(current) / maximum))
    draw.text(
        (x, y),
        f"{label} {int(current)}/{int(maximum)}",
        font=FONT_SMALL_B,
        fill=(244, 247, 247),
    )
    draw.rounded_rectangle(
        (x, y + 15, x + width, y + 22), 3, fill=(54, 31, 31), outline=(227, 211, 173)
    )
    if pct > 0:
        draw.rounded_rectangle(
            (x, y + 15, x + width * pct, y + 22), 3, fill=(211, 79, 68)
        )


def _camera_for_scene(tilemap, trace, dados, width, height, zoom=1.15):
    pontos = []
    for item in trace:
        for pessoa in item.get("personagens", []):
            pontos.append((pessoa["x"], pessoa["y"]))
        for aldeao in item.get("aldeoes", []):
            pontos.append((aldeao["x"], aldeao["y"]))
        if "x" in item and "y" in item:
            pontos.append((item["x"], item["y"]))
        if item.get("goblin_x") is not None:
            pontos.append((item["goblin_x"], item["goblin_y"]))
        if item.get("s1x") is not None:
            pontos.append((item["s1x"], item["s1y"]))
        if item.get("s2x") is not None:
            pontos.append((item["s2x"], item["s2y"]))
        for construcao in item.get("construcoes", []):
            pontos.append((construcao["x"], construcao["y"]))

    construction = dados.get("construction")
    if construction:
        pontos.append((construction["x"], construction["y"]))
    obstacle = dados.get("obstacle")
    if obstacle:
        pontos.append((obstacle["x"], obstacle["y"]))
    tree = dados.get("tree") or dados.get("arvore")
    if tree:
        pontos.append((tree["x"], tree["y"]))
    if dados.get("goal"):
        pontos.append(tuple(dados["goal"]))

    if not pontos:
        pontos = [(tilemap.largura * TILE / 2, tilemap.altura * TILE / 2)]

    min_x = min(p[0] for p in pontos)
    max_x = max(p[0] for p in pontos)
    min_y = min(p[1] for p in pontos)
    max_y = max(p[1] for p in pontos)

    pad = 150
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    desired_world_w = max(width / zoom, max_x - min_x + pad * 2)
    desired_world_h = max(height / zoom, max_y - min_y + pad * 2)
    zoom_x = width / desired_world_w
    zoom_y = height / desired_world_h
    zoom = min(zoom, zoom_x, zoom_y)

    camera = Camera()
    camera.largura = width
    camera.altura = height
    camera.zoom = max(0.65, zoom)

    world_w = tilemap.largura * TILE
    world_h = tilemap.altura * TILE
    min_cam_x = tilemap.offset_x
    min_cam_y = tilemap.offset_y
    max_cam_x = tilemap.offset_x + world_w - width / camera.zoom
    max_cam_y = tilemap.offset_y + world_h - height / camera.zoom
    camera.x = _clamp(
        center_x - width / (2 * camera.zoom), min_cam_x, max(min_cam_x, max_cam_x)
    )
    camera.y = _clamp(
        center_y - height / (2 * camera.zoom), min_cam_y, max(min_cam_y, max_cam_y)
    )
    return camera


class RealSceneContext:
    def __init__(self, tilemap, trace, dados, width, height):
        self.width = width
        self.height = height
        self.assets = VisualAssets()
        self.transform = TransformUtils()
        self.camera = _camera_for_scene(tilemap, trace, dados, width, height)
        self.surface = Surface((width, height))
        self.visual_tilemap = TileMapRenderer(self.surface, self.assets, self.transform)
        self.visual_tilemap.atualizar_carregamento()

    def terrain(self):
        self.surface.fill((12, 26, 34, 255))
        self.visual_tilemap.tela = self.surface
        self.visual_tilemap.renderizar(1 / 14, self.camera)
        return self.surface.pil_image().convert("RGBA")


def _render_terrain(
    tilemap, camera, assets, transform, dt=1 / 12, width=760, height=460
):
    surface = Surface((width, height))
    surface.fill((12, 26, 34, 255))
    visual_tilemap = TileMapRenderer(surface, assets, transform)
    visual_tilemap.atualizar_carregamento()
    visual_tilemap.renderizar(dt, camera)
    return surface.pil_image().convert("RGBA")


def _path_points(trace, extractor):
    points = []
    for estado in trace:
        valor = extractor(estado)
        if valor is not None:
            points.append(valor)
    return points


def _draw_path(draw, camera, world_points):
    if len(world_points) < 2:
        return
    pontos = [camera.tela(x, y) for x, y in world_points]
    draw.line(
        pontos,
        fill=(248, 221, 77, 125),
        width=max(2, int(4 * camera.zoom)),
        joint="curve",
    )


def _draw_overlay(draw, nome, idx, total, t, kind, width):
    bar_h = 56
    draw.rectangle((0, 0, width, bar_h), fill=(8, 18, 25, 214))
    draw.text((12, 8), f"Sapo Sapudo · {nome}", font=FONT_TITLE, fill=(245, 248, 247))
    draw.text(
        (12, 32),
        f"execução real · etapa {idx}/{total}",
        font=FONT_SMALL,
        fill=(194, 217, 224),
    )

    status = ""
    if kind == "gathering":
        n = sum(1 for a in t.get("aldeoes", []) if a.get("cortando"))
        status = f"{n}/{len(t.get('aldeoes', []))} aldeões no corte"
    elif kind in ("movement", "movement_step"):
        status = f"movendo · altura {t.get('altura', 0)}"
    elif kind == "construction_attack":
        status = f"dois soldados · construção {t.get('vida_construcao', 0)} PV"
    else:
        alvo = t.get("alvo_goblin")
        status = f"combate{f' · goblin → {alvo}' if alvo else ''}"
    bbox = draw.textbbox((0, 0), status, font=FONT_HUD)
    draw.rounded_rectangle(
        (width - (bbox[2] - bbox[0]) - 26, 16, width - 12, 40),
        6,
        fill=(32, 57, 73, 225),
    )
    draw.text((width - 18, 20), status, font=FONT_HUD, fill=(247, 220, 93), anchor="ra")


def _draw_actor(frame, camera, assets, actor, color, label):
    draw = ImageDraw.Draw(frame, "RGBA")
    try:
        sprite = _sprite_from_trace(assets, actor, out_scale=camera.zoom)
    except (FileNotFoundError, KeyError):
        sprite = None
    if sprite is not None:
        px, py = _sprite_position(camera, actor, sprite)
        frame.alpha_composite(sprite, (px, py))
        anchor = camera.tela(actor["x"], actor["y"])
        draw.ellipse(
            (anchor[0] - 4, anchor[1] - 4, anchor[0] + 4, anchor[1] + 4), fill=color
        )
    else:
        px, py = camera.tela(actor["x"], actor["y"])
        draw.ellipse(
            (px - 11, py - 11, px + 11, py + 11),
            fill=color,
            outline=(255, 255, 255, 220),
            width=2,
        )
        draw.text((px, py), label, font=FONT_SMALL_B, fill=(255, 255, 255), anchor="mm")


def _draw_actor_health(draw, camera, actor):
    vida = actor.get("vida")
    if vida is None:
        return
    maximum = actor.get("vida_maxima", vida)
    cx, cy = camera.tela(actor["x"], actor["y"])
    _health(
        draw,
        int(cx - 55),
        int(cy - max(52, 48 * camera.zoom)),
        actor.get("nome", "Personagem"),
        vida,
        maximum,
        110,
    )


def _draw_effects(frame, camera, assets, effects):
    for effect in effects or []:
        try:
            sprite = _effect_sprite_from_trace(assets, effect, out_scale=camera.zoom)
        except (FileNotFoundError, KeyError):
            sprite = None
        if sprite is not None:
            px, py = _sprite_position(camera, effect, sprite)
            frame.alpha_composite(sprite, (px, py))


def _draw_world_path(draw, camera, trace, key_x="x", key_y="y"):
    pontos = _path_points(
        trace,
        lambda t: (t.get(key_x), t.get(key_y)) if t.get(key_x) is not None else None,
    )
    _draw_path(draw, camera, pontos)


def _draw_construction(
    frame, camera, assets, construction, draw_health=True, vida=None, vida_max=None
):
    if not construction:
        return
    tipo = construction.get("nome", "casa")
    if construction.get("faccao") == "goblin" and "casa_goblin" in assets._config:
        tipo = "casa_goblin"
    actor = {
        "nome": tipo,
        "x": construction["x"],
        "y": construction["y"],
        "estado": construction.get("estado", "ocioso"),
        "frame": construction.get("frame", 0),
    }
    try:
        sprite = _sprite_from_trace(assets, actor, out_scale=camera.zoom)
    except (FileNotFoundError, KeyError):
        sprite = None
    if sprite is not None:
        px, py = _sprite_position(camera, actor, sprite)
        frame.alpha_composite(sprite, (px, py))
    else:
        draw = ImageDraw.Draw(frame, "RGBA")
        cx, cy = camera.tela(construction["x"], construction["y"])
        size_world = construction.get("size", 128)
        size_px = size_world * camera.zoom
        draw.rectangle(
            (cx - size_px / 2, cy - size_px / 2, cx + size_px / 2, cy + size_px / 2),
            fill=(102, 66, 43, 190),
            outline=(231, 193, 121, 255),
            width=2,
        )
    if draw_health and vida is not None:
        draw = ImageDraw.Draw(frame, "RGBA")
        cx, cy = camera.tela(construction["x"], construction["y"])
        _health(
            draw,
            int(cx - 70),
            int(cy - max(58, 56 * camera.zoom)),
            "Construção",
            vida,
            vida_max
            if vida_max is not None
            else construction.get("vida_inicial", vida),
            140,
        )


def render_frame(nome, trace, dados, idx, total, size=(760, 460), context=None):
    if not trace:
        raise ValueError(f"{nome}: trace vazio")
    width, height = size
    tilemap = dados["tilemap"]
    context = context or RealSceneContext(tilemap, trace, dados, width, height)
    assets = context.assets
    camera = context.camera
    base = context.terrain()
    frame = base.copy()
    draw = ImageDraw.Draw(frame, "RGBA")
    t = trace[idx]
    kind = dados.get("kind")

    if kind in ("movement", "movement_step"):
        _draw_world_path(draw, camera, trace[: idx + 1])
        # Obstáculo do cenário real. O runtime fornece a construção como
        # ``obstacle``; renderizamos o sprite real, atrás do personagem.
        obstacle = dados.get("obstacle")
        if obstacle:
            _draw_construction(
                frame,
                camera,
                assets,
                {
                    "nome": obstacle.get("nome", "casa"),
                    "x": obstacle["x"],
                    "y": obstacle["y"],
                    "size": obstacle.get("size", 128),
                    "faccao": obstacle.get("faccao"),
                    "vida_inicial": obstacle.get("vida_inicial"),
                },
                draw_health=False,
            )
        actor = _actor_from_motion(t, dados)
        if actor:
            _draw_actor(frame, camera, assets, actor, (74, 139, 238, 255), "S")
        if dados.get("goal"):
            gx, gy = dados["goal"]
            px, py = camera.tela(gx, gy)
            draw.ellipse(
                (px - 8, py - 8, px + 8, py + 8), outline=(232, 87, 72, 255), width=3
            )

    elif kind == "gathering":
        tree = dados.get("tree") or dados.get("arvore")
        if tree:
            tree_actor = {"nome": "arvore1", **tree, "estado": "ocioso", "frame": 0}
            sprite = _sprite_from_trace(assets, tree_actor, out_scale=camera.zoom)
            if sprite:
                px, py = _sprite_position(camera, tree_actor, sprite)
                frame.alpha_composite(sprite, (px, py))
        for k, actor in enumerate(t.get("aldeoes", [])):
            actor = {"nome": "aldeao", **actor}
            path = [
                (q["aldeoes"][k]["x"], q["aldeoes"][k]["y"])
                for q in trace[: idx + 1]
                if k < len(q.get("aldeoes", []))
            ]
            _draw_path(draw, camera, path)
            _draw_actor(frame, camera, assets, actor, (78, 137, 225, 255), f"A{k + 1}")

    else:
        # Construções ficam atrás dos personagens, como no jogo real. Isso
        # evita que a casa cubra o soldado e pareça que ele está golpeando
        # a própria construção.
        construction = _construction_for_frame(t, dados)
        if construction:
            _draw_construction(
                frame,
                camera,
                assets,
                construction,
                draw_health=True,
                vida=t.get("vida_construcao", construction.get("vida", 1)),
                vida_max=construction.get(
                    "vida_inicial", max(t.get("vida_construcao", 1), 1)
                ),
            )

        pessoas = t.get("personagens", [])
        for k, actor in enumerate(pessoas):
            path = [
                (q["personagens"][k]["x"], q["personagens"][k]["y"])
                for q in trace[: idx + 1]
                if k < len(q.get("personagens", []))
            ]
            _draw_path(draw, camera, path)
            color = (
                (75, 137, 232, 255)
                if actor.get("faccao") != "goblin"
                else (216, 88, 66, 255)
            )
            _draw_actor(frame, camera, assets, actor, color, actor.get("nome", "P"))
            _draw_actor_health(draw, camera, actor)

        # Os efeitos são capturados pelo runtime real: poeira de morte, fogo
        # persistente da construção e explosão de destruição.
        _draw_effects(frame, camera, assets, t.get("efeitos", []))

        # compatibilidade com traces antigos, enquanto o snapshot novo é adotado.
        if not pessoas:
            if t.get("x") is not None:
                actor = {
                    "nome": "soldado",
                    "x": t["x"],
                    "y": t["y"],
                    "estado": t.get("estado_soldado", "ocioso"),
                    "frame": t.get("frame_soldado", 0),
                    "faccao": "aliada",
                }
                _draw_actor(frame, camera, assets, actor, (75, 137, 232, 255), "S")
            if t.get("goblin_x") is not None:
                actor = {
                    "nome": "goblin_tocha",
                    "x": t["goblin_x"],
                    "y": t["goblin_y"],
                    "estado": t.get("estado_goblin", "ocioso"),
                    "frame": t.get("frame_goblin", 0),
                    "faccao": "goblin",
                }
                _draw_actor(frame, camera, assets, actor, (216, 88, 66, 255), "G")

        # linha de ataque só como pista discreta, sobre os sprites reais.
        alvo = t.get("alvo_goblin")
        if alvo == "soldado" and t.get("goblin_x") is not None:
            a = camera.tela(t["goblin_x"], t["goblin_y"])
            b = camera.tela(t.get("x", 0), t.get("y", 0))
            draw.line((a, b), fill=(255, 154, 67, 150), width=3)

    _draw_overlay(draw, nome, idx + 1, total, t, kind, width)
    return frame.convert("RGB")


def _actor_from_motion(t, dados):
    return {
        "nome": "soldado",
        "x": t.get("x", dados.get("start", (0, 0))[0]),
        "y": t.get("y", dados.get("start", (0, 0))[1]),
        "estado": t.get("estado", t.get("estado_soldado", "ocioso")),
        "frame": t.get("frame", t.get("frame_soldado", 0)),
        "faccao": "aliada",
    }


def _construction_for_frame(t, dados):
    if t.get("construcoes"):
        return dict(t["construcoes"][0])
    construction = dados.get("construction")
    return dict(construction) if construction else None


def gerar_gif_real(nome, resultado, caminho, fps=14, max_frames=36, size=(760, 460)):
    if not resultado or not resultado.trace or not isinstance(resultado.trace, dict):
        raise ValueError(f"{nome}: não há trace real suficiente para GIF")
    dados = dict(resultado.trace)
    trace = dados.get("trace", [])
    if not trace:
        raise ValueError(f"{nome}: trace vazio")

    indices = _selecionar_frames(trace, max_frames)
    context = RealSceneContext(dados["tilemap"], trace, dados, size[0], size[1])
    frames = [
        render_frame(nome, trace, dados, idx, len(indices), size=size, context=context)
        for idx in indices
    ]
    caminho.parent.mkdir(parents=True, exist_ok=True)
    duration = max(35, round(1000 / max(1, fps)))
    frames[0].save(
        caminho,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        optimize=False,
        disposal=2,
    )
    return caminho, {
        "gif_frames": len(frames),
        "gif_fps": fps,
        "gif_render": "assets_reais",
    }


def _selecionar_frames(trace, max_frames):
    n = len(trace)
    if n <= max_frames:
        return list(range(n))
    importantes = {0, n - 1}
    for i in range(1, n):
        anterior = trace[i - 1]
        atual = trace[i]
        if atual.get("vida_goblin") != anterior.get("vida_goblin"):
            importantes.update((i - 1, i))
        if atual.get("vida_construcao") != anterior.get("vida_construcao"):
            importantes.update((i - 1, i))
        if atual.get("alvo_goblin") != anterior.get("alvo_goblin"):
            importantes.update((i - 1, i))
        if atual.get("altura") != anterior.get("altura"):
            importantes.update((i - 1, i))
        for key in ("p0estado", "p1estado", "p2estado"):
            if atual.get(key) != anterior.get(key):
                importantes.update((i - 1, i))
    restantes = max(0, max_frames - len(importantes))
    amostras = []
    if restantes:
        for k in range(restantes):
            amostras.append(round((k + 1) * (n - 1) / (restantes + 1)))
    indices = sorted(set(list(importantes) + amostras))
    if len(indices) > max_frames:
        indices = sorted(set([0, n - 1] + indices[1:-1]))
        step = max(1, len(indices) // max_frames)
        indices = indices[::step][:max_frames]
        if indices[-1] != n - 1:
            indices[-1] = n - 1
    return indices
