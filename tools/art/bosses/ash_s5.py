"""The Elder of Ash, session 5: texture painting (plan: docs/art/bosses/elder_of_ash/overhaul/plan.md).

Paints the session 4 layout (one 512 x 512 atlas, the same islands) with fine ramps (close shades, cool shadows, warm
lights), so detail can be subtle. Form only, no painted light direction: ambient occlusion is baked from the real
geometry.
- the toad, countershaded: dark green where the skin faces the sky, mottled darker, with small raised warts (a lit
  top, a shadow under); brown down the sides, darker towards the ground, blotched, a few green flecks where it turns
  to the top; the pale belly with fine folds; the glands pitted with pores; warts dark with a lit crown;
- fingers and toes: knuckle creases, pale pads with a darker rim;
- the face: the mouth's line and its downturned corners, the nostrils and the inside of the mouth; the ember eyes with
  a bright core and a dark slit pupil; the brow ridges rough, the ash-white brows in strands with paler tips;
- the amber markings painted on: the three stripes down each cheek, the flank stripes, the haunch crescents and the
  wrist bands, each brighter along its middle;
- the volcano: skin hardening to ash (patches of each, cracks), ash speckled light and dark, basalt in long columnar
  cracks with a few hairline cracks glowing amber, the lit facets paler;
- the lava: a hot core along each run, cooler orange towards the edges, dark crust floating on it; the crater hotter;
- the pipe: wood grain, brass fittings with a highlight, the ember speckled with ash;
- the tongue: a groove down its middle, the tip hot.

Run from the repository root: python tools/art/bosses/ash_s5.py
"""
import json
import math
import shutil
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import brood_s4 as b4, brood_s5 as b5, coven_s5 as c5  # noqa: E402
from bosses import ash_s2 as s2, ash_s3 as s3, ash_s4 as s4, volley_crone_s5 as v5  # noqa: E402

OUT = ROOT / "docs/art/bosses/elder_of_ash/overhaul/s5_paint"
noise = v5.noise
mk = c5.make_ramp

LAVA = mk((120, 22, 10), (255, 120, 30), (255, 240, 180), 9)
RAMP = {
    "skin": mk((20, 28, 18), (58, 72, 38), (124, 140, 76), 9),
    "flank": mk((42, 26, 22), (136, 106, 66), (208, 178, 122), 9),
    "belly": mk((112, 88, 70), (204, 178, 126), (246, 230, 188), 7),
    "wart": mk((16, 16, 12), (38, 36, 22), (92, 90, 54), 5),
    "gland": mk((50, 48, 30), (118, 112, 70), (180, 172, 112), 7),
    "toe": mk((38, 26, 20), (92, 70, 42), (148, 118, 78), 5),
    "pad": mk((108, 82, 60), (178, 146, 98), (230, 206, 154), 5),
    "mouth": mk((10, 5, 8), (34, 18, 18), (84, 40, 38), 5),
    "tongue": mk((88, 28, 40), (178, 78, 76), (238, 150, 130), 7),
    "tongue_tip": mk((200, 90, 30), (255, 150, 60), (255, 228, 160), 5),
    "brow": mk((12, 10, 10), (34, 30, 20), (74, 66, 46), 5),
    "brow_ash": mk((146, 142, 148), (214, 210, 200), (250, 248, 240), 7),
    "brow_ash_dark": mk((98, 96, 104), (164, 160, 152), (214, 210, 200), 5),
    "eye": mk((206, 112, 30), (255, 186, 60), (255, 248, 206), 7),
    "skin_ash": mk((58, 56, 46), (124, 120, 102), (184, 180, 162), 7),
    "ash": mk((84, 82, 86), (158, 154, 148), (216, 214, 208), 7),
    "ash_dark": mk((48, 46, 52), (104, 100, 98), (158, 154, 150), 7),
    "basalt": mk((16, 14, 20), (52, 48, 54), (112, 106, 114), 9),
    "basalt_lit": mk((34, 32, 40), (80, 76, 84), (142, 136, 146), 7),
    "lava": LAVA, "lava_hot": LAVA, "ember": LAVA, "crack": LAVA,
    "pipe": mk((42, 22, 12), (124, 80, 44), (186, 136, 86), 7),
    "pipe_metal": mk((68, 60, 50), (168, 158, 134), (238, 230, 208), 7),
    # overlays
    "mark": mk((150, 72, 20), (236, 150, 52), (255, 216, 132), 5),
    "pupil": [(18, 8, 8), (40, 18, 12)],
    "crust": [(36, 14, 12), (66, 24, 14), (104, 38, 16)],
}
BASE = {"skin": 4, "flank": 4, "belly": 3, "wart": 2, "gland": 3, "toe": 2, "pad": 2, "mouth": 2, "tongue": 3,
        "tongue_tip": 2, "brow": 2, "brow_ash": 3, "brow_ash_dark": 2, "eye": 3, "skin_ash": 3, "ash": 3, "ash_dark": 3,
        "basalt": 4, "basalt_lit": 3, "lava": 4, "lava_hot": 6, "ember": 6, "pipe": 3, "pipe_metal": 3}
GLOWING = s4.GLOWING


def smooth(seed, u, v, cell):
    """Smooth value noise 0..1, for blotches that run across cube edges."""
    i, j = math.floor(u / cell), math.floor(v / cell)
    fu, fv = u / cell - i, v / cell - j
    fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
    a, b = noise(seed, i, j, 1), noise(seed, i + 1, j, 1)
    c, d = noise(seed, i, j + 1, 1), noise(seed, i + 1, j + 1, 1)
    return ((a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv) / 999


def blotch(p, seed, scale=7.0):
    """0..1 at a world point: soft patches, the same on neighbouring faces."""
    x, y, z = p
    return 0.6 * smooth(seed, x + 0.37 * y, z - 0.21 * y, scale) + 0.4 * smooth(seed + 5, z + y, x - y, scale * 0.45)


def world_points(cube, face, w, h):
    pts, n, _, _ = v5.texel_points(cube, face, w, h)
    m = v5.cube_matrix(cube)
    flat = np.c_[pts.reshape(-1, 3), np.ones(w * h)]
    world = (m @ flat.T).T[:, :3].reshape(h, w, 3)
    return world, m[:3, :3] @ n


# ---- painters: each returns a shade map on its zone's ramp and overlay pixels [(y, x, ramp, shade)] -------------------

def plain(zone, w, h):
    return np.full((h, w), BASE[zone], int), []


def paint_skin(zone, w, h, seed, ctx):
    """Dark green, mottled; small raised warts with a lit top and a shadow under."""
    lv, over = plain(zone, w, h)
    world = ctx["world"]
    for y in range(h):
        for x in range(w):
            b = blotch(world[y, x], 3)
            lv[y, x] += -2 if b < 0.3 else (-1 if b < 0.42 else (1 if b > 0.74 else 0))
            r = noise(seed, x, y, 2)
            if r > 955 and y % 2 == 0 and y + 2 < h:          # a small wart (2x2): lit, its shadow below
                lv[y, x] += 1
                lv[y + 2, x] -= 1
    return lv, over


def paint_flank(zone, w, h, seed, ctx):
    """Brown down the sides, darker towards the ground, blotched; a few green flecks where it turns to the top."""
    lv, over = plain(zone, w, h)
    world, normal = ctx["world"], ctx["normal"]
    side = abs(normal[1]) < 0.5
    for y in range(h):
        for x in range(w):
            p = world[y, x]
            b = blotch(p, 17, 6.0)
            lv[y, x] += -2 if b < 0.28 else (-1 if b < 0.4 else (1 if b > 0.76 else 0))
            if p[1] < 12:
                lv[y, x] -= 1                                  # darker near the ground
            if normal[1] < -0.5:
                lv[y, x] -= 1                                  # undersides
            r = noise(seed, x, y, 2)
            if r > 965 and y % 2 == 0 and y + 2 < h:
                lv[y, x] += 1
                lv[y + 2, x] -= 1
            if side and y < 2 and noise(seed + 4, x, y, 2) > 620:
                over.append((y, x, "skin", 3 + (noise(seed + 6, x, y, 1) > 700)))
    return lv, over


def paint_belly(zone, w, h, seed, ctx):
    lv, over = plain(zone, w, h)
    for y in range(h):
        for x in range(w):
            if y % 3 == 2 and noise(seed, x, y // 3, 3) > 250:
                lv[y, x] -= 1                                  # fine folds across
            elif noise(seed + 3, x, y, 2) > 930:
                lv[y, x] += 1

    return lv, over


def paint_wart(zone, w, h, seed, ctx):
    lv, over = plain(zone, w, h)
    cy, cx = (h - 1) / 2, (w - 1) / 2
    for y in range(h):
        for x in range(w):
            d = max(abs(y - cy) / max(1, cy + 0.5), abs(x - cx) / max(1, cx + 0.5))
            lv[y, x] += 1 if d < 0.4 else (-1 if d > 0.85 else 0)
    return lv, over


def paint_gland(zone, w, h, seed, ctx):
    lv, over = plain(zone, w, h)
    for y in range(h):
        for x in range(w):
            if noise(seed, x, y, 1) > 900:
                lv[y, x] -= 2                                  # pores
                if x + 1 < w:
                    lv[y, x + 1] += 1
            elif blotch(ctx["world"][y, x], 23, 4) > 0.7:
                lv[y, x] += 1
    return lv, over


def paint_toe(zone, w, h, seed, ctx):
    lv, over = plain(zone, w, h)
    long_x = w >= h
    n = w if long_x else h
    for k in range(3, n - 1, 4):                               # knuckle creases
        if long_x:
            lv[:, k] -= 1
        else:
            lv[k, :] -= 1
    lv[0, :] += 1
    return lv, over


def paint_pad(zone, w, h, seed, ctx):
    lv, over = plain(zone, w, h)
    lv[0, :] -= 1
    lv[-1, :] -= 1
    lv[:, 0] -= 1
    lv[:, -1] -= 1
    if h > 2 and w > 2:
        lv[1:-1, 1:-1] += 1
    return lv, over


def paint_mouth(zone, w, h, seed, ctx):
    lv, over = plain(zone, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += 1 if noise(seed, x, y, 2) > 820 else 0
    return lv, over


def paint_tongue(zone, w, h, seed, ctx):
    lv, over = plain(zone, w, h)
    if w <= h:
        lv[:, w // 2] -= 1
    else:
        lv[h // 2, :] -= 1
    for y in range(h):
        for x in range(w):
            if noise(seed, x, y, 2) > 950:
                lv[y, x] += 1
    return lv, over


def paint_brow(zone, w, h, seed, ctx):
    lv, over = plain(zone, w, h)
    for y in range(h):
        for x in range(w):
            if (x + y) % 3 == 0 and noise(seed, x, y, 1) > 350:
                lv[y, x] += 1                                  # bristles
            elif noise(seed + 2, x, y, 1) < 120:
                lv[y, x] -= 1
    return lv, over


def paint_hair(zone, w, h, seed, ctx):
    """The ash-white brows: strands along their length, paler towards the tips."""
    lv, over = plain(zone, w, h)
    long_x = w >= h
    for y in range(h):
        for x in range(w):
            strand = (y if long_x else x)
            along = (x / max(1, w - 1)) if long_x else (y / max(1, h - 1))
            lv[y, x] += (1 if noise(seed, strand, 0, 1) > 500 else -1) * (noise(seed + 7, x // 3, y // 3, 1) > 300)
            lv[y, x] += 1 if along > 0.75 else 0
    return lv, over


def paint_eye(zone, w, h, seed, ctx):
    lv, over = plain(zone, w, h)
    cy, cx = (h - 1) / 2, (w - 1) / 2
    for y in range(h):
        for x in range(w):
            d = math.hypot((x - cx) / max(1, w / 2), (y - cy) / max(1, h / 2))
            lv[y, x] += 3 if d < 0.35 else (1 if d < 0.7 else -1)
    return lv, over


def paint_skin_ash(zone, w, h, seed, ctx):
    """Skin hardening to ash: where the volcano's foot comes out of the back it is still the toad's green skin, and it
    turns to ash as it rises (patches of skin left among the ash, cracks between), so the join has no edge."""
    lv, over = plain(zone, w, h)
    world = ctx["world"]
    for y in range(h):
        for x in range(w):
            p = world[y, x]
            b = blotch(p, 31, 5.0)
            skin = max(0.0, min(1.0, (56 - p[1]) / 10))          # 1 at y 46 and below, 0 from y 56 up
            if b < 0.35 + 0.65 * skin:
                over.append((y, x, "skin", 4 - (noise(seed + 2, x, y, 2) < 300) + (b > 0.8)))
                continue
            ridge = abs(smooth(37, p[0] * 1.4 + p[1], p[2] * 1.4 - p[1], 3) - 0.5)
            if ridge < 0.03:
                lv[y, x] -= 2                                  # a crack
            elif b > 0.7:
                lv[y, x] += 1
    return lv, over


def paint_ash(zone, w, h, seed, ctx):
    """Ash: speckled light and dark, soft cracks."""
    lv, over = plain(zone, w, h)
    world = ctx["world"]
    for y in range(h):
        for x in range(w):
            p = world[y, x]
            r = noise(seed, x, y, 2)
            lv[y, x] += 1 if r > 920 else (-1 if r < 80 else 0)
            if abs(smooth(41, p[0] + p[1] * 0.6, p[2] - p[1] * 0.6, 4) - 0.5) < 0.025:
                lv[y, x] -= 2
            elif blotch(p, 43, 6) > 0.72:
                lv[y, x] += 1
    return lv, over


def paint_basalt(zone, w, h, seed, ctx):
    """Basalt in long columnar cracks; facets lighter at their top; a few hairline cracks glowing amber."""
    lv, over = plain(zone, w, h)
    world = ctx["world"]
    for y in range(h):
        for x in range(w):
            p = world[y, x]
            col = abs(smooth(51, math.atan2(p[0], p[2] - 8) * 20, p[1] * 0.12, 1.6) - 0.5)
            if col < 0.04:
                lv[y, x] -= 2                                  # a column's crack
                if noise(seed + 5, x // 2, y // 6, 1) > 965:
                    over.append((y, x, "crack", 3 + (noise(seed + 6, x, y, 1) > 600)))   # glowing through
            elif noise(seed, x, y, 2) > 930:
                lv[y, x] += 1
    lv[0, :] += 1
    return lv, over


def paint_lava(zone, w, h, seed, ctx):
    """A hot core along the run, cooler towards the edges, dark crust floating on it."""
    lv, over = plain(zone, w, h)
    long_x = w >= h
    across = h if long_x else w
    mid = (across - 1) / 2
    for y in range(h):
        for x in range(w):
            a = (y if long_x else x)
            along = (x if long_x else y)
            wob = (noise(seed, along // 2, 0, 1) % 3) - 1
            d = abs(a - mid - wob * 0.5) / max(1, across / 2)
            lv[y, x] = 7 if d < 0.3 else (5 if d < 0.65 else 3)
            if d > 0.45 and noise(seed + 9, x, y, 2) > 860:
                over.append((y, x, "crust", 1 + (noise(seed + 11, x, y, 1) > 500)))
    if zone == "lava_hot":
        lv += 1
    return lv, over


def paint_ember(zone, w, h, seed, ctx):
    lv, over = plain(zone, w, h)
    for y in range(h):
        for x in range(w):
            r = noise(seed, x, y, 1)
            if r > 760:
                over.append((y, x, "crust", 0 + (r > 900)))
            elif r < 200:
                lv[y, x] += 2
    return lv, over


def paint_pipe(zone, w, h, seed, ctx):
    lv, over = plain(zone, w, h)
    long_x = w >= h
    for y in range(h):
        for x in range(w):
            grain = (y if long_x else x)
            lv[y, x] += -1 if noise(seed, grain, (x if long_x else y) // 4, 1) > 650 else 0
    return lv, over


def paint_metal(zone, w, h, seed, ctx):
    lv, over = plain(zone, w, h)
    lv[0, :] += 2
    lv[-1, :] -= 1
    for y in range(h):
        for x in range(w):
            if noise(seed, x, y, 1) < 80:
                lv[y, x] -= 1
    return lv, over


PAINTERS = {"skin": paint_skin, "flank": paint_flank, "belly": paint_belly, "wart": paint_wart, "gland": paint_gland,
            "toe": paint_toe, "pad": paint_pad, "mouth": paint_mouth, "tongue": paint_tongue,
            "tongue_tip": paint_eye, "brow": paint_brow, "brow_ash": paint_hair, "brow_ash_dark": paint_hair,
            "eye": paint_eye, "skin_ash": paint_skin_ash, "ash": paint_ash, "ash_dark": paint_ash,
            "basalt": paint_basalt, "basalt_lit": paint_basalt, "lava": paint_lava, "lava_hot": paint_lava,
            "ember": paint_ember, "pipe": paint_pipe, "pipe_metal": paint_metal}


# ---- the painted details: the decals from the design, laid onto the faces under them --------------------------------

def decals():
    """The painted details as boxes in the rest pose: markings, the mouth's line and inside, nostrils, pupils."""
    shown = s2.build("decals")
    out = []
    for c in shown.cubes:
        if s2.is_decal(c) or c.name.startswith("maw_"):
            m = v5.cube_matrix(c)
            lo, hi = np.array(c.frm), np.array(c.to)
            thin = int(np.argmin(hi - lo))
            pad = np.zeros(3)
            pad[thin] = 1.4
            corners = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
            world = (m @ corners.T).T[:, :3]
            out.append((c.mat, np.linalg.inv(m), lo - pad, hi + pad, world.min(0) - 2, world.max(0) + 2,
                        (lo + hi) / 2, hi - lo, thin))
    return out


def lay_decals(world, over, zone, found):
    if zone in GLOWING and zone != "eye":
        return
    h, w = world.shape[:2]
    lo_w, hi_w = world.reshape(-1, 3).min(0), world.reshape(-1, 3).max(0)
    near = [d for d in found if np.all(d[4] <= hi_w) and np.all(d[5] >= lo_w)]
    if not near:
        return
    flat = np.c_[world.reshape(-1, 3), np.ones(w * h)]
    for mat, inv, lo, hi, _, _, centre, size, thin in near:
        if zone == "eye" and mat != "pupil":
            continue
        local = (inv @ flat.T).T[:, :3]
        inside = np.all((local >= lo) & (local <= hi), axis=1).reshape(h, w)
        for y, x in zip(*np.nonzero(inside)):
            if mat == "mark":
                q = local[y * w + x]
                axes = [k for k in range(3) if k != thin]
                across = min(abs(q[k] - centre[k]) / max(0.5, size[k] / 2) for k in axes)
                over.append((y, x, "mark", 3 if across < 0.45 else 2))
            elif mat == "pupil":
                over.append((y, x, "pupil", 0))
            else:
                over.append((y, x, "mouth", 0 if mat == "mouth" else 1))


# ---- the atlas -----------------------------------------------------------------------------------------------------

def paint_face(model, i, face, w, h, solids, normals, found):
    cube = model.cubes[i]
    seed = zlib.crc32(f"{cube.name}/{face}".encode())
    zone = s4.face_zone(model, i, face, normals)
    world, normal = world_points(cube, face, w, h)
    lv, over = PAINTERS[zone](zone, w, h, seed, {"world": world, "normal": normal})
    if zone not in GLOWING and zone != "skin_ash":
        ao = b5.occlusion(model, i, face, w, h, solids)
        lv = lv - (ao >= 0.3) - (ao >= 0.55)
    lay_decals(world, over, zone, found)
    ramp = RAMP[zone]
    out = c5.from_levels(lv, ramp)
    for y, x, rname, shade in over:
        if 0 <= y < h and 0 <= x < w:
            r = RAMP[rname]
            out[y, x, :3] = r[max(0, min(len(r) - 1, shade))]
    return out


def painted():
    model = s4.build_model()
    keys = s4.island_keys(model)
    sizes = {key: (key[2], key[3]) for key in keys.values()}
    b4.SIZE = s4.SIZE
    positions, used, height = b4.pack(sizes)
    owner = {}
    for (i, f), key in sorted(keys.items(), key=lambda kv: (kv[0][0], FACES.index(kv[0][1]))):
        owner.setdefault(key, (i, f))
    solids = b5.solids_of(model)
    normals = s4.face_normals(model)
    found = decals()
    atlas = Image.new("RGBA", (s4.SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        i, f = owner[key]
        patch = Image.fromarray(paint_face(model, i, f, w, h, solids, normals, found), "RGBA")
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return model, keys, positions, used, height, atlas


CLOSE = [
    {"name": "face_close", "location": (1.6, 9, 2.4), "target": (0, 3.4, 1.9), "scale": 3.6, "player": False},
    {"name": "volcano", "location": (6, 8, 9), "target": (0, -0.4, 5.0), "scale": 5.5, "player": False},
    {"name": "flank", "location": (12, 1.5, 2.2), "target": (0, -0.4, 1.6), "scale": 5.5, "player": False},
]


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    model, keys, positions, used, height, atlas = painted()
    atlas_path = OUT / s4.ATLAS
    atlas.save(atlas_path)
    atlas.save(OUT / "atlas_preview.png")
    bb, _ = s4.rig_bbmodel(model, keys, positions, atlas_path, height, s3.pose_table())
    path = OUT / f"{model.name}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    out = OUT / "renders"
    s4.render(model, bb, atlas_path, out, s4.VIEWS + CLOSE)
    names = [v["name"] for v in s4.VIEWS + CLOSE]
    tw, th, pad, top, cols = 470, 352, 12, 56, 3
    rows = (len(names) + cols - 1) // cols
    img = Image.new("RGB", (pad + cols * (tw + pad), top + rows * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "The Elder of Ash - painted (session 5)", font=sheet._font(28), fill=sheet.INK)
    for n_, name in enumerate(names):
        x, y = pad + (n_ % cols) * (tw + pad), top + (n_ // cols) * (th + 34 + pad)
        img.paste(sheet._tile(out / f"{name}.png", tw, th), (x, y))
        dr.text((x, y + th + 6), name.replace("_", " "), font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "sheet.png")
    print(json.dumps({"atlas": [s4.SIZE, height], "rows_used": used, "islands": len(positions)}))


if __name__ == "__main__":
    main()
