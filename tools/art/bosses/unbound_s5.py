"""The Unbound redesign, session 5: texture painting (plan: docs/art/bosses/the_unbound/overhaul/plan.md).

Paints the session 4 layout (one 256 x 256 atlas, the same islands) with fine ramps (close shades, cool shadows,
warm lights), so detail can be subtle:
- skin: vanilla's vindicator grey, mottled; the muscles read through light and shadow (lit tops of the shoulders and
  chest, shadowed undersides, the abs on the stomach); old welts where the restraints bit, each with a lit edge; the
  chest piece's fire spills warm light onto the skin round it, fading with distance;
- the face: a lit brow ridge and cheekbones, a jaw in shadow, a scar across one cheek; the heavy brow in bristles;
- the band: woven red cloth, darker at its edges, a scorched ring round the burning eye; the knot, tails and torn
  flap a darker red with folds and frayed ends;
- the horns: growth rings across their length, lighter towards the tips, the boss rough and ridged;
- leather: stitched edges, scuffs and creases; silver studs with a highlight;
- blackened iron: hammered and pitted, worn bright on its edges, rust in the pits; the chest piece's rim stained with
  heat (blue-violet to bronze) round the grate;
- chains: lit tops, dark ends;
- the trousers: a coarse weave, worn lighter at the knees, dirt rising from the boots;
- the cleaver: brushed steel streaked along its length, a bright honed bevel along the edge, dried blood on the edge
  and spattered onto the flat; a darker spine; a leather-wrapped handle;
- the glow: the fire hot in the middle and orange at its edges, flickering; the eye a white-cyan core in cyan, its
  halo fading out.
Form only, no painted light direction: ambient occlusion baked from the real geometry.

Run from the repository root: python tools/art/bosses/unbound_s5.py
"""
import json
import shutil
import subprocess
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import brood_s5 as b5, coven_s5 as c5, unbound_s2 as s2, unbound_s3 as s3, unbound_s4 as s4  # noqa: E402
from bosses import volley_crone_s4 as v4, volley_crone_s5 as v5  # noqa: E402

OUT = ROOT / "docs/art/bosses/the_unbound/overhaul/s5_paint"
noise = v5.noise
mk = c5.make_ramp

RAMP = {
    "skin": mk((58, 66, 72), (126, 132, 130), (196, 198, 188), 11),
    "ember": [(118, 96, 82), (150, 104, 76), (182, 120, 78), (214, 142, 86)],   # firelight on grey skin
    "brow": mk((14, 14, 18), (44, 44, 48), (96, 94, 96), 5),
    "cloth": mk((38, 8, 12), (134, 30, 32), (204, 98, 82), 9),
    "cloth_dark": mk((22, 4, 8), (70, 14, 18), (138, 48, 46), 7),
    "scorch": [(18, 10, 10), (38, 18, 16), (64, 30, 24)],
    "horn": mk((92, 80, 58), (196, 184, 152), (246, 240, 222), 9),
    "horn_root": mk((48, 40, 30), (124, 110, 86), (188, 172, 140), 7),
    "strap": mk((38, 24, 14), (112, 78, 48), (180, 140, 98), 7),
    "stud": mk((90, 94, 106), (198, 202, 210), (252, 253, 255), 5),
    "iron": mk((12, 12, 16), (56, 54, 60), (142, 138, 146), 9),
    "iron_lit": mk((46, 46, 52), (104, 102, 110), (200, 198, 206), 7),
    "heat": [(62, 56, 92), (90, 74, 98), (122, 90, 70), (150, 108, 60)],      # tempered iron: violet to bronze
    "rust": mk((54, 28, 18), (108, 60, 34), (158, 96, 58), 5),
    "chain": mk((36, 36, 42), (128, 128, 136), (222, 222, 230), 7),
    "pants": mk((12, 12, 18), (48, 48, 58), (106, 106, 120), 7),
    "dirt": [(44, 38, 32), (62, 54, 44), (82, 72, 58)],
    "boot": mk((5, 4, 4), (20, 17, 17), (72, 62, 58), 5),
    "steel": mk((56, 60, 68), (156, 162, 168), (242, 245, 247), 9),
    "spine": mk((30, 32, 38), (90, 94, 100), (172, 176, 182), 7),
    "wrap": mk((24, 14, 8), (66, 46, 30), (132, 100, 68), 5),
    "blood": mk((32, 4, 4), (94, 18, 18), (152, 42, 36), 5),
    "hole": [(8, 7, 10), (24, 22, 26), (40, 38, 44)],
    "fire": mk((150, 38, 8), (236, 92, 18), (255, 226, 140), 7),
    "eye": mk((16, 104, 146), (70, 210, 250), (226, 253, 255), 5),
    "eye_dim": mk((8, 34, 46), (26, 92, 116), (66, 158, 184), 5),
}
# zone -> (ramp, base shade)
ZONE = {"skin": ("skin", 5), "skin_crease": ("skin", 3), "nose": ("skin", 4), "brow": ("brow", 2),
        "cloth": ("cloth", 4), "cloth_dark": ("cloth_dark", 3), "horn": ("horn", 4), "horn_root": ("horn_root", 3),
        "horn_tip": ("horn", 3), "strap": ("strap", 3), "stud": ("stud", 2), "iron": ("iron", 4),
        "iron_lit": ("iron_lit", 3), "chain": ("chain", 3), "pants": ("pants", 3), "boot": ("boot", 2),
        "steel": ("steel", 4), "spine": ("spine", 3), "wrap": ("wrap", 2), "blood": ("blood", 2), "hole": ("hole", 1),
        "fire": ("fire", 3), "fire_hot": ("fire", 6), "eye": ("eye", 2), "eye_hot": ("eye", 4), "eye_dim": ("eye_dim", 2)}
GLOWING = ("fire", "eye")


def world_points(cube, face, w, h):
    pts, n, _, _ = v5.texel_points(cube, face, w, h)
    m = v5.cube_matrix(cube)
    flat = np.c_[pts.reshape(-1, 3), np.ones(w * h)]
    world = (m @ flat.T).T[:, :3].reshape(h, w, 3)
    normal = m[:3, :3] @ n
    return world, normal


def blank(cube, w, h):
    return np.full((h, w), ZONE[s4.zone_for(cube)][1], int), []


def clusters(seed, x, y, lo=170, hi=830, cell=2):
    r = noise(seed, x, y, cell)
    return -1 if r < lo else (1 if r > hi else 0)


# ---- painters (each returns a shade map on the zone's ramp and overlay pixels [(y, x, ramp, shade)]) ----------------

def paint_skin(cube, face, w, h, seed, ctx):
    """Grey skin, mottled; light on the tops of the masses, shadow under them; old welts where the restraints bit;
    the fire's warm light round the chest piece; the abs on the stomach."""
    lv, over = blank(cube, w, h)
    n = cube.name
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 35, 970, 2)
    if face == "up":
        lv += 1
    elif face == "down":
        lv -= 2
    else:
        lv[0, :] += 1                                                 # the top of every mass catches the light
        lv[h - 1, :] -= 1
        if h >= 6:
            lv[h - 2, :] -= 1
    if n == "abdomen" and face == "north":
        for y in range(1, h - 1, 3):
            for x in range(1, w - 1):
                if x == w // 2:
                    lv[y:y + 2, x] -= 1                               # the line down the middle
                elif (x - w // 2) % 4 == 0:
                    lv[y, x] -= 1
        lv[:, :] += 0
    if n in ("delt_-1", "delt_1", "traps", "trap_slope_-1", "trap_slope_1", "hump") and face not in ("down",):
        lv[:2, :] += 1
    # welts: a few short dark weals with a lit edge, on the back, shoulders and arms
    if face in ("south", "east", "west", "north") and w >= 6 and h >= 6 and n not in ("head", "abdomen"):
        for k in range(1 + noise(seed + 3, 0, 0, 1) % 2):
            y0 = 2 + noise(seed + 5 + k, 0, 0, 1) % max(1, h - 4)
            x0 = noise(seed + 7 + k, 0, 0, 1) % max(1, w - 4)
            for t in range(min(5, w - x0)):
                yy = y0 + (t // 2 if k % 2 else -(t // 2))
                if 0 <= yy < h and 0 <= x0 + t < w:
                    lv[yy, x0 + t] -= 1
                    if yy - 1 >= 0:
                        lv[yy - 1, x0 + t] += 1
    # the chest piece's fire, spilling onto the skin round it
    world, normal = ctx["world"], ctx["normal"]
    d = np.linalg.norm(world - ctx["fire"], axis=-1)
    facing = float(np.dot(normal, ctx["fire_normal"]))
    if facing > 0.3:
        for y in range(h):
            for x in range(w):
                if d[y, x] < 10:
                    over.append((y, x, "glow", 0.55 * (1 - d[y, x] / 10) ** 1.5))   # firelight, blended in
    return lv, over


def paint_head(cube, face, w, h, seed, ctx):
    """The face under the band: a lit brow ridge and cheekbones, the jaw in shadow, a scar across his left cheek."""
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 80, 940, 3)
    if face == "north":
        lv[:3, :] += 1                                                # the forehead
        for x in range(w):
            lv[3, x] -= 1 if noise(seed + 1, x, 0, 1) < 600 else 0  # a furrow above the scowl
        cheek = h - 5
        lv[cheek, 1:3] += 1
        lv[cheek, w - 3:w - 1] += 1                                   # cheekbones
        lv[h - 2:, :] -= 1
        lv[h - 1, :] -= 1                                             # the jaw in shadow
        for t in range(4):                                            # a scar, pale with a dark edge
            yy, xx = cheek - 1 + t, 1 + t
            if 0 <= yy < h and 0 <= xx < w:
                lv[yy, xx] += 2
                if yy + 1 < h:
                    lv[yy + 1, xx] -= 1
    elif face == "up":
        lv += 1
    elif face == "down":
        lv -= 2
    else:
        lv[h - 2:, :] -= 1
    return lv, over


def paint_nose(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    if face == "north":
        lv[:, w // 2] += 1                                            # the bridge
        lv[h - 1, :] -= 1
    elif face == "down":
        lv[:, :] -= 1
        lv[h // 2, 0] = 0
        lv[h // 2, w - 1] = 0                                         # nostrils
    else:
        lv[h - 1, :] -= 1
    return lv, over


def paint_brow(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += 1 if (x + y // 2) % 3 == 0 else (-1 if (x + y // 2) % 3 == 2 else 0)
    lv[0, :] += 1
    return lv, over


def paint_cloth(cube, face, w, h, seed, ctx):
    """Woven cloth: alternate threads, darker at its edges, frayed specks; a scorched ring round the burning eye."""
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += (1 if (x + y) % 2 == 0 else 0) + clusters(seed, x, y, 120, 900, 2) - (1 if (x * 3 + y) % 7 == 0 else 0)
    lv[0, :] -= 1
    lv[h - 1, :] -= 2
    for x in range(w):
        if noise(seed + 4, x, 0, 1) < 300:
            lv[h - 1, x] -= 1                                          # frayed lower edge
    if face == "north" and cube.name == "band":
        world = ctx["world"]
        d = np.linalg.norm(world[..., :2] - ctx["eye"][:2], axis=-1)
        for y in range(h):
            for x in range(w):
                if d[y, x] < 3.2:
                    over.append((y, x, "scorch", 0 if d[y, x] < 2.2 else (1 if d[y, x] < 2.7 else 2)))
    return lv, over


def paint_cloth_dark(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += (1 if (x + y) % 2 == 0 else 0) + (1 if x == 0 else 0) - (1 if (x + 2 * y) % 5 == 0 else 0)
    lv[h - 1, :] -= 1
    for x in range(w):
        if noise(seed + 2, x, 0, 1) < 450:
            lv[h - 1, x] -= 1
    return lv, over


def paint_horn(cube, face, w, h, seed, ctx):
    """Growth rings across the horn's length (its local x), lighter towards the tip, a crack or two."""
    lv, over = blank(cube, w, h)
    piece = int(cube.name.rsplit("_", 1)[-1]) if cube.name.rsplit("_", 1)[-1].isdigit() else 0
    lv += min(2, piece // 2)                                          # lighter towards the tip
    if face in ("north", "south", "up", "down"):
        for x in range(w):
            if x % 4 == 0:
                lv[:, x] -= 1                                         # growth rings
    if face == "up":
        lv += 1
    elif face == "down":
        lv -= 1
    for y in range(h):
        for x in range(w):
            if noise(seed + 9, x, y, 1) < 8:
                lv[y, x] -= 1                                         # a rare chip
    return lv, over


def paint_horn_root(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 120, 900, 2)
    if face == "up":
        lv += 1
    return lv, over


def paint_strap(cube, face, w, h, seed, ctx):
    """Leather: scuffs and creases, the edges darker with a row of stitches."""
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 150, 880, 2)
    if h >= 2:
        lv[0, :] += 1
        lv[h - 1, :] -= 1
    if h >= 3:
        for x in range(0, w, 2):
            lv[1 if h > 2 else 0, x] += 1                             # stitches
    for x in range(w):
        if noise(seed + 6, x, 0, 1) < 90:
            lv[:, x] -= 1                                             # a crease
    return lv, over


def paint_stud(cube, face, w, h, seed, ctx):
    lv = np.full((h, w), 2, int)
    lv[0, 0] = 4
    if h > 1 and w > 1:
        lv[h - 1, w - 1] = 0
    return lv, []


def paint_iron(cube, face, w, h, seed, ctx):
    """Blackened iron: hammered and pitted, the edges worn bright, rust in the pits; heat stains on the chest piece."""
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 200, 820)
            if noise(seed + 11, x, y, 1) < 30:
                over.append((y, x, "rust", 2))
    lv[0, :] += 2
    lv[:, 0] += 1
    lv[h - 1, :] -= 1
    if cube.name == "chest_piece" and face == "north":
        cx, cy = (w - 1) / 2, (h - 1) / 2
        for y in range(h):
            for x in range(w):
                r = max(abs(x - cx) / (w / 2), abs(y - cy) / (h / 2))
                if 0.45 < r < 0.9:
                    over.append((y, x, "heat", int((0.9 - r) / 0.45 * 3.9)))
    return lv, over


def paint_iron_lit(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 220, 760, 1)
    lv[0, :] += 2
    if h > 1:
        lv[h - 1, :] -= 1
    return lv, over


def paint_chain(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    lv[0, :] += 2
    lv[h - 1, :] -= 2
    if w >= 2:
        lv[:, w - 1] -= 1
    return lv, over


def paint_pants(cube, face, w, h, seed, ctx):
    """A coarse weave, worn lighter at the knees (the shin's top), dirt rising from the boots."""
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += (-1 if x % 5 == 2 and noise(seed + 3, x, y // 3, 1) < 700 else 0) + clusters(seed, x, y, 30, 975, 2)   # folds
    if cube.name.startswith("shin_") and face == "north":
        lv[:2, :] += 1                                                # worn knees
    if cube.name.startswith("shin_") and face not in ("up", "down"):
        for y in range(h // 2, h):
            for x in range(w):
                if noise(seed + 8, x, y, 2) < 300 * (y - h // 2 + 1) / (h // 2 + 1):
                    over.append((y, x, "dirt", 1 if y < h - 2 else 0))
    if face == "down":
        lv -= 2
    return lv, over


def paint_boot(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 180, 860)
    lv[0, :] += 1
    if face not in ("up", "down"):
        lv[h - 1, :] = 0                                              # the sole
    return lv, over


def paint_steel(cube, face, w, h, seed, ctx):
    """Brushed steel streaked along the blade, a bright honed bevel along the edge, blood dried onto the flat near it."""
    lv, over = blank(cube, w, h)
    world = ctx["world"]
    edge_a, edge_b = ctx["edge"]
    seg = edge_b - edge_a
    t = np.clip(((world - edge_a) @ seg) / (seg @ seg), 0, 1)
    d = np.linalg.norm(world - (edge_a + t[..., None] * seg), axis=-1)
    for y in range(h):
        for x in range(w):
            lv[y, x] += 1 if noise(seed + (x if w > h else y), 0, 0, 1) < 330 else 0       # streaks along the length
            if d[y, x] < 1.6:
                lv[y, x] += 3                                         # the honed bevel
            elif d[y, x] < 2.6:
                lv[y, x] += 1
            elif d[y, x] < 6 and noise(seed + 13, x, y, 1) < 180 * (6 - d[y, x]) / 3:
                over.append((y, x, "blood", 1 if noise(seed + 17, x, y, 1) < 500 else 2))   # spatter
    return lv, over


def paint_spine(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    if face == "up":
        lv += 2
    lv[0, :] += 1
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 200, 850)
    return lv, over


def paint_wrap(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += 1 if (x + y) % 3 == 0 else (-1 if (x + y) % 3 == 2 else 0)   # the wrap's turns
    return lv, over


def paint_blood(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 250, 900, 1)
    return lv, over


def paint_plain(cube, face, w, h, seed, ctx):
    return blank(cube, w, h)


def paint_fire(cube, face, w, h, seed, ctx):
    """Hot in the middle, orange at its edges, flickering tongues."""
    lv = np.zeros((h, w), int)
    base = ZONE[s4.zone_for(cube)][1]
    for y in range(h):
        for x in range(w):
            r = max(abs(x - (w - 1) / 2) / max(1, w / 2), abs(y - (h - 1) / 2) / max(1, h / 2))
            lv[y, x] = base + 2 - int(r * 3) + (1 if noise(seed, x, y, 1) > 700 else 0) - (1 if y == 0 else 0)
    return lv, []


def paint_eye(cube, face, w, h, seed, ctx):
    lv = np.zeros((h, w), int)
    base = ZONE[s4.zone_for(cube)][1]
    for y in range(h):
        for x in range(w):
            r = max(abs(x - (w - 1) / 2) / max(1, w / 2), abs(y - (h - 1) / 2) / max(1, h / 2))
            lv[y, x] = base + 1 - int(r * 2.5)
    return lv, []


def painter_for(cube):
    n, z = cube.name, s4.zone_for(cube)
    if n == "head":
        return paint_head
    return {"skin": paint_skin, "skin_crease": paint_plain, "nose": paint_nose, "brow": paint_brow,
            "cloth": paint_cloth, "cloth_dark": paint_cloth_dark, "horn": paint_horn, "horn_tip": paint_horn,
            "horn_root": paint_horn_root, "strap": paint_strap, "stud": paint_stud, "iron": paint_iron,
            "iron_lit": paint_iron_lit, "chain": paint_chain, "pants": paint_pants, "boot": paint_boot,
            "steel": paint_steel, "spine": paint_spine, "wrap": paint_wrap, "blood": paint_blood, "hole": paint_plain,
            "fire": paint_fire, "fire_hot": paint_fire, "eye": paint_eye, "eye_hot": paint_eye,
            "eye_dim": paint_eye}[z]


def paint_face(model, i, face, w, h, solids, ctx):
    cube = model.cubes[i]
    seed = zlib.crc32(f"{cube.name}/{face}".encode())
    zone = s4.zone_for(cube)
    world, normal = world_points(cube, face, w, h)
    lv, over = painter_for(cube)(cube, face, w, h, seed, dict(ctx, world=world, normal=normal))
    if not zone.startswith(GLOWING):
        ao = b5.occlusion(model, i, face, w, h, solids)
        lv = lv - (ao >= 0.3) - (ao >= 0.55)
    out = c5.from_levels(lv, RAMP[ZONE[zone][0]])
    for y, x, rname, shade in over:
        if 0 <= y < h and 0 <= x < w:
            if rname == "glow":
                warm = np.array((236, 124, 60))
                out[y, x, :3] = np.clip(out[y, x, :3] * (1 - shade) + warm * shade, 0, 255).astype(np.uint8)
                continue
            r = RAMP[rname]
            out[y, x, :3] = r[max(0, min(len(r) - 1, shade))]
    return out


def context(model):
    def centre(name):
        return next(c for c in model.cubes if c.name == name).corners().mean(0)
    fire = next(c for c in model.cubes if c.name == "chest_fire")
    fire_normal = v5.cube_matrix(fire)[:3, :3] @ np.array([0, 0, -1.0])
    edge = next(c for c in model.cubes if c.name == "edge_blood").corners()
    # the edge's two ends: the corners' extremes along its longest axis
    span = edge.max(0) - edge.min(0)
    order = np.argsort(edge @ (span / np.linalg.norm(span)))
    return {"fire": centre("chest_fire"), "fire_normal": fire_normal, "eye": centre("eye"),
            "edge": (edge[order[:4]].mean(0), edge[order[4:]].mean(0))}


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    k = s3.scale_factor()
    model = s2.build(s3.MODEL_ID)
    s2.finish(model, k)
    keys = s4.island_keys(model)
    sizes = {key: (key[2], key[3]) for key in keys.values()}
    positions, used, height = b4_pack(sizes)
    owner = {}
    for (i, f), key in sorted(keys.items(), key=lambda kv: (kv[0][0], FACES.index(kv[0][1]))):
        owner.setdefault(key, (i, f))
    solids = b5.solids_of(model)
    ctx = context(model)
    atlas = Image.new("RGBA", (s4.SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        i, f = owner[key]
        patch = Image.fromarray(paint_face(model, i, f, w, h, solids, ctx), "RGBA")
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    atlas_path = OUT / "occultech_unbound.png"
    atlas.save(atlas_path)
    atlas.resize((atlas.width * 2, atlas.height * 2), Image.NEAREST).save(OUT / "atlas_preview.png")
    bb, _ = s4.rig_bbmodel(model, keys, positions, atlas_path, height, s3.pose_table(k))
    path = OUT / f"{model.name}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    views = s4.VIEWS + [
        {"name": "ten_blocks", "location": (-3, 11, 1.62), "target": (0, 0, 1.9), "scale": 8, "player": False,
         "res": (640, 480)},
        {"name": "chest", "location": (1.2, 5.0, 2.4), "target": (0, 0.6, 2.2), "scale": 2.2, "player": False},
        {"name": "cleaver", "location": (4.0, -3.0, 2.0), "target": (1.0, -1.6, 0.2), "scale": 2.6, "player": False},
    ]
    out = OUT / "renders"
    out.mkdir()
    boxes = [{"corners": c.corners().tolist(), "from": c.frm, "to": c.to,
              "glow": s4.zone_for(c).startswith(GLOWING), "uv": bb["elements"][i]["faces"]}
             for i, c in enumerate(model.cubes)]
    job_file = out / "render_job.json"
    job_file.write_text(json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes,
                                    "views": views, "player_at": (2.6, 1.0)}), encoding="utf-8")
    result = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job_file)],
                            capture_output=True, text=True)
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job_file.unlink()
    names = [v["name"] for v in views]
    tw, th, pad, top, cols = 470, 352, 12, 56, 3
    rows = (len(names) + cols - 1) // cols
    img = Image.new("RGB", (pad + cols * (tw + pad), top + rows * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "The Unbound - painted (session 5)", font=sheet._font(28), fill=sheet.INK)
    for n_, name in enumerate(names):
        x, y = pad + (n_ % cols) * (tw + pad), top + (n_ // cols) * (th + 34 + pad)
        img.paste(sheet._tile(out / f"{name}.png", tw, th), (x, y))
        dr.text((x, y + th + 6), name.replace("_", " "), font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "sheet.png")
    print(json.dumps({"atlas": [s4.SIZE, height], "rows_used": used, "islands": len(positions)}))


def b4_pack(sizes):
    from bosses import brood_s4 as b4
    return b4.pack(sizes)


if __name__ == "__main__":
    main()
