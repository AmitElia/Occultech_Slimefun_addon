"""Brood Mother redesign, session 5: texture painting.

Paints the session 4 layout (same rules, 256 x 512):
- the head is vanilla's spider head texture on every side, each vanilla pixel 3 x 3 texels on the 24 x 24 face, with
  vanilla's pale fang pixels; the eyes are vanilla's eye pixels in vanilla's colours, glowing;
- the chitin ramp is vanilla's own spider browns (plus one violet-leaning shadow and one warm light), so she reads as
  the vanilla spider grown huge. Detail in clusters: fine bristle strokes along the legs, darker joint ends,
  tarantula bands near each knee, split plate edges, a chevron on the rear of the abdomen;
- hair cards are hair strips with alpha: strands from a dark root to a gold tip, with gaps between them, so a card reads
  as a fringe and not a plane;
- wax runs in streaks from the top of each face, with sheen spots on the fresh wax and soot on the old; candles have
  drip lines and a melt pool on top; flames have a hot core;
- form only, no painted light direction: ambient occlusion baked from the real geometry (texels darken where another
  part is close in front of them).

Run from the repository root: python tools/art/bosses/brood_s5.py
It reads the vanilla spider textures from the installed 26.2 client jar; the jar is never copied into the repository.
"""
import base64
import json
import shutil
import sys
import zipfile
import zlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, _uuid, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import brood_s2 as s2, brood_s3 as s3, brood_s4 as s4  # noqa: E402
from bosses import volley_crone_s3 as v3, volley_crone_s5 as v5  # noqa: E402

OUT = ROOT / "docs/art/bosses/brood_mother/overhaul/s5_paint"
VANILLA = v5.VANILLA

# Ramps, dark to light. The chitin is vanilla's spider palette with a violet-leaning shadow below it and a warm light
# above; the others are hue-shifted the same way (shadows cool, lights warm).
RAMP = {
    "chitin": [(18, 14, 20), (26, 20, 15), (38, 32, 27), (50, 43, 38), (61, 52, 45), (71, 62, 53), (79, 69, 60),
               (96, 84, 72), (122, 108, 92)],
    "hair": [(46, 34, 30), (82, 62, 48), (120, 94, 72), (163, 132, 106), (198, 166, 118), (228, 200, 140)],
    "mandible": [(8, 5, 10), (18, 10, 14), (30, 16, 20), (48, 28, 32), (80, 52, 58)],
    "fang": [(94, 79, 72), (146, 137, 127), (186, 172, 148), (214, 198, 166), (238, 228, 200)],
    "wax": [(60, 36, 28), (96, 64, 46), (118, 81, 54), (160, 118, 78), (212, 167, 115), (236, 200, 144),
            (250, 228, 182)],
    "candle": [(150, 126, 100), (196, 178, 146), (222, 206, 172), (236, 222, 190), (248, 242, 220)],
    "wick": [(12, 10, 14), (30, 24, 28), (64, 52, 50)],
    "flame": [(196, 66, 22), (236, 116, 32), (255, 168, 58), (255, 214, 122), (255, 248, 214)],
}
# zone -> (ramp, base level)
ZONE = {"chitin": ("chitin", 4), "chitin_lit": ("chitin", 6), "plate": ("chitin", 7), "hair": ("hair", 3),
        "mandible": ("mandible", 1), "fang": ("fang", 3), "wax": ("wax", 4), "wax_old": ("wax", 2),
        "candle": ("candle", 3), "wick": ("wick", 1), "flame": ("flame", 2)}
# the spider head box in spider.png (origin 32, 4; 8 x 8 x 8): where each face starts
VANILLA_HEAD = {"up": (40, 4), "down": (48, 4), "east": (32, 12), "north": (40, 12), "west": (48, 12),
                "south": (56, 12)}
LEG_SEGMENT = {"1": "femur", "2": "patella", "3": "tibia", "4": "metatarsus"}


def vanilla_textures():
    with zipfile.ZipFile(VANILLA) as jar:
        body = Image.open(jar.open("assets/minecraft/textures/entity/spider/spider.png")).convert("RGBA")
        eyes = Image.open(jar.open("assets/minecraft/textures/entity/spider/spider_eyes.png")).convert("RGBA")
        candle = Image.open(jar.open("assets/minecraft/textures/block/white_candle_lit.png")).convert("RGBA")
        flame = Image.open(jar.open("assets/minecraft/textures/particle/flame.png")).convert("RGBA")
    return body, eyes, candle, flame


# vanilla's white candle greys, warmed to ivory so the candles belong with the honey wax; its lit top stays as is
CANDLE_WARM = {(199, 211, 211): (206, 196, 176), (224, 229, 229): (228, 220, 200), (248, 248, 248): (244, 238, 222),
               (255, 255, 255): (252, 248, 236)}


noise = v5.noise


# ---- geometry: ambient occlusion -----------------------------------------------------------------------------------

def solids_of(model):
    """Every cube that can shade another (hair cards have no volume), with its inverse matrix and world bounds."""
    out = []
    for j, c in enumerate(model.cubes):
        if c.mat == "hair" or min(np.array(c.to) - np.array(c.frm)) < 0.5:
            continue
        m = v5.cube_matrix(c)
        corners = np.array([[x, y, z, 1] for x in (c.frm[0], c.to[0]) for y in (c.frm[1], c.to[1])
                            for z in (c.frm[2], c.to[2])])
        world = (m @ corners.T).T[:, :3]
        out.append((j, np.linalg.inv(m), np.array(c.frm), np.array(c.to), world.min(0), world.max(0)))
    return out


def occlusion(model, index, face, w, h, solids):
    """0..1 per texel: how much of the space just in front of it is filled by other parts (crease shading)."""
    cube = model.cubes[index]
    pts, n, tu, tv = v5.texel_points(cube, face, w, h)
    m = v5.cube_matrix(cube)
    offsets = [n * 0.7, n * 1.6, n * 0.8 + tu * 1.6, n * 0.8 - tu * 1.6, n * 0.8 + tv * 1.6, n * 0.8 - tv * 1.6]
    flat = pts.reshape(-1, 3)
    worlds = [(m @ np.c_[flat + off, np.ones(len(flat))].T).T for off in offsets]
    lo_all = np.min([wd[:, :3].min(0) for wd in worlds], 0)
    hi_all = np.max([wd[:, :3].max(0) for wd in worlds], 0)
    near = [s for s in solids if s[0] != index and np.all(s[4] <= hi_all) and np.all(s[5] >= lo_all)]
    hits = np.zeros(len(flat))
    for world in worlds:
        inside = np.zeros(len(flat), bool)
        for _, inv, lo, hi, _, _ in near:
            local = (inv @ world.T).T[:, :3]
            inside |= np.all((local > lo + 0.05) & (local < hi - 0.05), axis=1)
        hits += inside
    return (hits / len(offsets)).reshape(h, w)


def along(cube, face, w, h):
    """0..1 per texel along the cube's longest axis (0 at its low end), and that axis."""
    pts, _, _, _ = v5.texel_points(cube, face, w, h)
    lo, hi = np.array(cube.frm), np.array(cube.to)
    axis = int(np.argmax(hi - lo))
    return (pts[..., axis] - lo[axis]) / max(1e-6, hi[axis] - lo[axis]), axis


# ---- painters: each returns an RGBA array (h, w, 4) ----------------------------------------------------------------

def from_levels(lv, ramp, alpha=None):
    lv = np.clip(lv, 0, len(ramp) - 1)
    rgb = np.array(ramp, np.uint8)[lv]
    a = np.full(lv.shape + (1,), 255, np.uint8) if alpha is None else alpha[..., None].astype(np.uint8)
    return np.concatenate([rgb, a], -1)


def paint_head(face, w, h, body, ao):
    """Vanilla's spider head, pixel for pixel (3 x 3 texels each on the face). Eye pixels lie under the eye cubes and
    are painted as the darkest chitin, a socket; vanilla's pale fang pixels keep their colour."""
    ox, oy = VANILLA_HEAD[face]
    ramp = np.array(RAMP["chitin"])
    out = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            r, g, b, _ = body.getpixel((ox + min(7, x * 8 // w), oy + min(7, y * 8 // h)))
            if r > 2 * g + 20:                      # an eye pixel: the socket behind the eye cube
                rgb = RAMP["chitin"][0]
            elif r > 120:                           # vanilla's fang pixels
                rgb = RAMP["fang"][1] if (r + g + b) > 400 else RAMP["fang"][0]
            else:
                lv = int(np.argmin(((ramp - (r, g, b)) ** 2).sum(1)))
                lv -= int(ao[y, x] >= 0.34) + int(ao[y, x] >= 0.6)
                rgb = RAMP["chitin"][max(0, lv)]
            out[y, x] = (*rgb, 255)
    return out


def paint_eye(cube, face, w, h, eyes):
    """Vanilla's eye pixels in vanilla's colours on the front; the sides take the middle red."""
    if cube.name.startswith("eye_mutant"):
        lv = np.full((h, w), 1)
        if face == "east":
            lv[1:-1, 1:-1] = 2
        reds = [(98, 0, 0), (166, 2, 2), (255, 14, 14)]
        return np.concatenate([np.array(reds, np.uint8)[lv], np.full((h, w, 1), 255, np.uint8)], -1)
    _, _, c, r, _, _ = cube.name.split("_")
    out = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            if face == "north":
                px = eyes.getpixel((40 + int(c) + x // 3, 12 + int(r) + y // 3))
                rgb = px[:3] if px[3] else (98, 0, 0)
            else:
                rgb = (166, 2, 2)
            out[y, x] = (*rgb, 255)
    return out


def paint_hair(cube, face, w, h, seed):
    """A hair strip with alpha. Leg cards: strands grow out from the leg (the card's middle band, inside the chitin)
    to both edges. Fringe cards: strands hang from the top edge. Root dark, tip gold, gaps between strands."""
    lv = np.zeros((h, w), int)
    alpha = np.zeros((h, w), int)
    if "_fur_" in cube.name:
        hl = s2.LEG_HAIR[int(cube.name.split("_")[2])]
        mid = (h - 1) / 2
        core = max(1.0, h / 2 - hl)              # the leg's half-thickness: hidden inside the chitin
        for x in range(w):
            for side in (-1, 1):
                if noise(seed + side, x, 0, 1) < 140:   # a gap in the fringe
                    continue
                reach = (h / 2 - core) * (0.7 + noise(seed + 5 + side, x, 1, 1) / 3400)
                steps = int(round(core + reach))
                for k in range(int(core) - 1, steps):
                    y = int(round(mid + side * (k + 0.5)))
                    if 0 <= y < h:
                        f = (k - core) / max(1.0, reach)
                        alpha[y, x] = 255
                        lv[y, x] = 1 if f < 0.25 else (2 if f < 0.55 else (3 if f < 0.85 else 4))
    else:
        alpha[0, :] = 255
        lv[0, :] = 1                                    # the root line along the top
        for x in range(w):
            if noise(seed, x, 0, 1) < 250:
                continue
            length = int(round(h * (0.45 + noise(seed + 3, x, 1, 1) / 1800)))
            for y in range(1, max(2, length)):
                f = y / max(1, length)
                alpha[y, x] = 255
                lv[y, x] = 1 if f < 0.3 else (2 if f < 0.6 else (3 if f < 0.85 else 5))
    return from_levels(lv, RAMP["hair"], alpha)


def paint_candle(face, w, h, candle):
    """Vanilla's lit white candle at our size: its two columns of shading, its warm-lit band under the wick, the body
    below and its shaded foot; the top face is vanilla's lit top. Each vanilla pixel is w/2 texels across."""
    out = np.zeros((h, w, 4), np.uint8)
    k = max(1, w // 2)
    for y in range(h):
        for x in range(w):
            col = min(1, x * 2 // w)
            if face in ("up", "down"):
                vy = 6 + min(1, y * 2 // h)
            else:
                row, from_foot = y // k, (h - 1 - y) // k
                if row < 4:
                    vy = 6 + row                                  # the warm band under the flame
                elif from_foot < 3:
                    vy = 15 - from_foot                           # vanilla's shaded foot
                else:
                    vy = 10 + (row % 2)                           # the body, repeated
            px = candle.getpixel((col, vy))
            out[y, x] = (*CANDLE_WARM.get(px[:3], px[:3]), 255)
    return out


def paint_card(cube, w, h, flame):
    """A wick card in vanilla's wick colour, or a flame card from vanilla's flame particle (its 4 x 8 core, scaled),
    with its alpha: a clear teardrop flame."""
    if cube.mat == "wick":
        return np.tile(np.array([33, 32, 52, 255], np.uint8), (h, w, 1))
    out = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            out[y, x] = flame.getpixel((2 + min(3, x * 4 // w), min(7, y * 8 // h)))
    return out


def paint_levels(cube, face, w, h, seed):
    """Level map for every other zone (before ambient occlusion)."""
    zone = cube.mat
    ramp, base = ZONE[zone]
    lv = np.full((h, w), base, int)
    fa, axis = along(cube, face, w, h)
    parts = cube.name.split("_")
    is_leg_segment = cube.name.startswith("leg_") and len(parts) == 3 and parts[2] in LEG_SEGMENT
    upright = face not in ("up", "down")
    for y in range(h):
        for x in range(w):
            r = noise(seed, x, y)
            edge = min(x, y, w - 1 - x, h - 1 - y)
            if zone in ("chitin", "chitin_lit", "plate"):
                # fine bristles: short strokes along the long axis, light and dark, in clusters
                stroke = noise(seed + 9, x // (1 if axis else 2), y // (2 if axis else 1), 1)
                if stroke < 90:
                    lv[y, x] += 1
                elif stroke > 940:
                    lv[y, x] -= 1
                if zone == "plate" and edge == 0:
                    lv[y, x] += 1 if (y == 0 or not upright) else -1   # lit plate edges, a dark lower lip
                if is_leg_segment:
                    a = fa[y, x]
                    if a < 0.06 or a > 0.94:
                        lv[y, x] -= 1                                   # joint ends tuck into the knuckles
                    elif parts[2] in ("1", "3") and 0.8 < a < 0.9:
                        lv[y, x] += 2                                   # the tarantula band near the knee
                if cube.name.startswith("abdomen") and face == "south":
                    cx = abs(x - (w - 1) / 2)
                    if (y + cx // 1) % 9 in (0, 1) and y < h * 0.8:
                        lv[y, x] += 2                                   # the chevron down her rear
                if upright and h >= 12 and y > h * 0.75 and noise(seed + 7, x, y, 3) < 300:
                    lv[y, x] -= 1                                       # dust settles low on big faces
            elif zone == "mandible":
                lv[y, x] += 3 if y == max(1, h // 3) else 0             # one glossy highlight along each jaw
                if edge == 0:
                    lv[y, x] -= 1
            elif zone == "fang":
                lv[y, x] -= 1 if fa[y, x] > 0.75 else 0                   # the tip darkens
                lv[y, x] += 1 if r < 120 else 0
            elif zone in ("wax", "wax_old") and ("_drip" in cube.name or "_bead_" in cube.name):
                if "_bead_" in cube.name:
                    lv[y, x] = 5 if (y == 0 or not upright) else 4         # a bead of wax catches the light
                elif upright and y >= h - 1:
                    lv[y, x] += 2                                       # the glossy tip of a run
            elif zone in ("wax", "wax_old"):
                run = noise(seed + 2, x, 0, 1)
                runs_to = h * (0.3 + run / 1500)
                if upright and run < 450 and y < runs_to:
                    lv[y, x] += 1                                       # a fresh run of wax down from the top
                if zone == "wax" and noise(seed + 4, x, y) > 965:
                    lv[y, x] += 2                                       # sheen
                if zone == "wax_old" and noise(seed + 6, x, y) < 90:
                    lv[y, x] -= 1                                       # soot
                if upright and y == h - 1 and h > 2:
                    lv[y, x] -= 1                                       # the lip where a run ends
            elif zone == "candle":
                if face == "up":
                    lv[y, x] = 1 if edge > 0 else 4                     # a melt pool inside a bright rim
                elif noise(seed + 2, x, 0, 1) < 300 and y < h * 0.6:
                    lv[y, x] += 1                                       # drip lines
                elif r < 70:
                    lv[y, x] -= 1
            elif zone == "wick":
                lv[y, x] = 2 if y == 0 and upright else 1
            elif zone == "flame":
                if w * h <= 4:
                    lv[y, x] = 3
                elif upright:
                    hot = 1 - y / max(1, h - 1)                             # hottest at the base
                    centre = abs(x - (w - 1) / 2) <= 0.5
                    lv[y, x] = 4 if (centre and y >= h - 2) else (3 if centre else (2 if hot < 0.7 else 1))
                else:
                    lv[y, x] = 4 if edge > 0 or w <= 2 else 3
    return np.clip(lv, 0, len(RAMP[ramp]) - 1)


def paint_face(model, i, face, w, h, solids, vanilla):
    cube = model.cubes[i]
    seed = zlib.crc32(f"{cube.name}/{face}".encode())
    if cube.mat == "hair":
        return paint_hair(cube, face, w, h, seed)
    if cube.mat in ("eye", "eye_small"):
        return paint_eye(cube, face, w, h, vanilla[1])
    if cube.mat in ("flame", "wick") and zero_thick(cube):
        return paint_card(cube, w, h, vanilla[3])
    if cube.mat == "candle":
        return paint_candle(face, w, h, vanilla[2])
    glow = cube.mat == "flame"
    ao = np.zeros((h, w)) if glow else occlusion(model, i, face, w, h, solids)
    if cube.name == "head":
        return paint_head(face, w, h, vanilla[0], ao)
    lv = paint_levels(cube, face, w, h, seed)
    lv = lv - (ao >= 0.34) - (ao >= 0.6)
    return from_levels(lv, RAMP[ZONE[cube.mat][0]])


def zero_thick(cube):
    return min(np.array(cube.to) - np.array(cube.frm)) < 0.01


# ---- atlas, model, renders -----------------------------------------------------------------------------------------

def island_keys(model):
    """Session 4's islands, with leg hair and body fringe kept apart (they are painted differently)."""
    keys = s4.island_keys(model)
    for k, key in keys.items():
        if key[0] == "hair":
            keys[k] = ("hair", "leg" if "_fur_" in model.cubes[k[0]].name else "fringe", key[1], key[2])
    return keys


def build_atlas(model, keys):
    sizes = {key: s4.v4.face_size(model.cubes[i], f) for (i, f), key in keys.items()}
    positions, used, height = s4.pack(sizes)
    owner = {}
    for (i, f), key in sorted(keys.items(), key=lambda kv: (kv[0][0], FACES.index(kv[0][1]))):
        owner.setdefault(key, (i, f))
    solids = solids_of(model)
    vanilla = vanilla_textures()
    atlas = Image.new("RGBA", (s4.SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        i, f = owner[key]
        patch = Image.fromarray(paint_face(model, i, f, w, h, solids, vanilla), "RGBA")
        if not zero_thick(model.cubes[i]):   # cards keep a clear border: no stray opaque texels at their edges
            atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return atlas, positions, used, height


def views():
    return s4.views() + [
        # about how big she is on a 1080p screen at 10 blocks (70 degree field of view)
        {"name": "ten_blocks", "location": (-3, 11, 1.62), "target": (0, 0, 1.5), "scale": 11, "player": False,
         "res": (640, 480)},
        {"name": "wax_pile", "location": (3.5, 1.5, 5.8), "target": (0, -1.7, 3.3), "scale": 3.8, "player": False},
        {"name": "leg", "location": (5.5, 3.5, 2.2), "target": (2.6, 0.6, 1.6), "scale": 3.2, "player": False},
        {"name": "flank", "location": (-6, -1.2, 2.4), "target": (-1.2, -1.9, 1.9), "scale": 4.2, "player": False},
    ]


def painted():
    model = s4.rig()
    keys = island_keys(model)
    atlas, positions, used, height = build_atlas(model, keys)
    return model, keys, atlas, positions, used, height


def to_bbmodel(model, keys, positions, height, atlas_path):
    texture = {"name": atlas_path.name, "path": "", "folder": "", "namespace": "", "id": "0", "group": "",
               "width": s4.SIZE, "height": height, "uv_width": s4.SIZE, "uv_height": height, "particle": False,
               "use_as_default": True, "layers_enabled": False, "render_mode": "default", "render_sides": "auto",
               "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False,
               "visible": True, "internal": True, "saved": False, "uuid": _uuid(s3.MODEL_ID + "/atlas"),
               "source": "data:image/png;base64," + base64.b64encode(atlas_path.read_bytes()).decode()}
    bb = model.to_bbmodel(texture_size=(s4.SIZE, height), textures=(texture,))
    for i, element in enumerate(bb["elements"]):
        for f in FACES:
            key = keys.get((i, f))
            if key is None:
                element["faces"][f] = {"uv": [0, 0, 0, 0], "texture": None}
                continue
            x, y, w, h = positions[key]
            element["faces"][f] = {"uv": [x, y, x + w, y + h], "texture": 0}
        if model.cubes[i].mat in s4.GLOW_ZONES:
            element["light_emission"] = 15
    frm, to = s2.hitbox_bounds(model)
    add_hitbox(bb, frm, to)
    poses = s3.pose_table()
    bb["animations"] = [{"uuid": _uuid(f"{s3.MODEL_ID}/anim/{key}"), "name": key, "loop": "hold", "override": False,
                         "length": 0.5, "snapping": 20, "selected": False, "anim_time_update": "", "blend_weight": "",
                         "start_delay": "", "loop_delay": "", "animators": v3.keyframes(model, pose)}
                        for key, pose in poses.items()]
    return bb


def main():
    model, keys, atlas, positions, used, height = painted()
    OUT.mkdir(parents=True, exist_ok=True)
    atlas_path = OUT / "occultech_brood_mother.png"
    atlas.save(atlas_path)
    atlas.resize((s4.SIZE * 2, height * 2), Image.NEAREST).save(OUT / "atlas_preview.png")
    bb = to_bbmodel(model, keys, positions, height, atlas_path)
    path = OUT / f"{s3.MODEL_ID}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)

    s4.render(model, bb, atlas_path, OUT / "renders", views())
    names = [v["name"] for v in views()]
    tw, th, pad, top, cols = 520, 390, 12, 56, 5
    rows = (len(names) + cols - 1) // cols
    img = Image.new("RGB", (pad + cols * (tw + pad), top + rows * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Brood Mother - painted (session 5)", font=sheet._font(28), fill=sheet.INK)
    for k, name in enumerate(names):
        x, y = pad + (k % cols) * (tw + pad), top + (k // cols) * (th + 34 + pad)
        img.paste(sheet._tile(OUT / "renders" / f"{name}.png", tw, th), (x, y))
        dr.text((x, y + th + 6), name.replace("_", " "), font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "sheet.png")
    print(json.dumps({"atlas": [s4.SIZE, height], "rows_used": used, "islands": len(positions)}))


if __name__ == "__main__":
    main()
