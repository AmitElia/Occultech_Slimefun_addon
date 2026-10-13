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
    "pants": mk((12, 12, 18), (50, 50, 62), (118, 118, 134), 9),
    "dirt": [(44, 38, 32), (62, 54, 44), (82, 72, 58)],
    "boot": mk((5, 4, 4), (20, 17, 17), (72, 62, 58), 5),
    "steel": mk((56, 60, 68), (156, 162, 168), (242, 245, 247), 9),
    "spine": mk((30, 32, 38), (90, 94, 100), (172, 176, 182), 7),
    "wrap": mk((24, 14, 8), (66, 46, 30), (132, 100, 68), 5),
    "blood": [(26, 6, 6), (48, 10, 10), (72, 14, 14), (96, 20, 18), (124, 26, 22), (156, 38, 30), (196, 74, 60)],
    "hole": [(8, 7, 10), (24, 22, 26), (40, 38, 44)],
    "fire": mk((150, 120, 100), (232, 214, 190), (255, 252, 244), 7),   # neutral warm white: the stage tint colours it
    "eye": mk((16, 104, 146), (70, 210, 250), (226, 253, 255), 5),
    "eye_dim": mk((8, 34, 46), (26, 92, 116), (66, 158, 184), 5),
}
# zone -> (ramp, base shade)
ZONE = {"skin": ("skin", 5), "skin_crease": ("skin", 3), "nose": ("skin", 4), "brow": ("brow", 2),
        "cloth": ("cloth", 4), "cloth_dark": ("cloth_dark", 3), "horn": ("horn", 4), "horn_root": ("horn_root", 3),
        "horn_tip": ("horn", 3), "strap": ("strap", 3), "stud": ("stud", 2), "iron": ("iron", 4),
        "iron_lit": ("iron_lit", 3), "chain": ("chain", 3), "pants": ("pants", 4), "boot": ("boot", 2),
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
    the abs on the stomach."""
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
    # (no painted firelight round the furnace: it stayed orange whatever colour the stage tinted the fire)
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
    if cube.name == "furnace_door" and face in ("north", "south") and w >= 6 and h >= 6:
        for y in range(2, h - 2, 2):                                 # the door's draught vent: dark slits
            lv[y, 2:w - 2] -= 3
        for y, x in ((1, 1), (1, w - 2), (h - 2, 1), (h - 2, w - 2)):
            lv[y, x] += 3                                            # rivets at its corners
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
    """A plane of chain, cut out, 4 texels wide: a face-on ring (rounded, its middle open) then a side-on link (2 wide),
    every 7 texels; the crossed plane is offset half a link, so each ring sits on the other plane's side link."""
    long_h = h >= w
    n, across = (h, w) if long_h else (w, h)
    lv = np.zeros((h, w), int)
    alpha = np.zeros((h, w), int)
    shift = 4 if cube.name.endswith("_b") else 0
    c0, c1 = across // 2 - 1, across // 2                    # the two middle columns
    for i in range(n):
        p = (i + shift) % 7
        for j in range(across):
            if p in (0, 4):
                on = j in (c0, c1)                           # the ring's rounded top and bottom
            elif p in (1, 2, 3):
                on = j in (c0 - 1, c1 + 1)                   # its sides, the middle open
            else:
                on = j in (c0, c1)                           # a side-on link
            if on:
                y, x = (i, j) if long_h else (j, i)
                alpha[y, x] = 255
                lit = j <= c0                                # lit on its left, as the iron rounds away
                lv[y, x] = (5 if p in (0, 1) else (4 if p < 5 else 3)) + (1 if lit else -1)
    return lv, [], alpha


def paint_pants(cube, face, w, h, seed, ctx):
    """Coarse dark trousers: seams with stitching down the sides; long soft folds, each a shadow with a lit edge;
    creases bunched at the knees; the thighs worn lighter; frayed hems over the boots, with dirt."""
    lv, over = blank(cube, w, h)
    n = cube.name
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 12, 990, 2)            # barely any noise: the folds carry the cloth
    if face in ("east", "west") and w >= 3:
        mid = w // 2
        lv[:, mid] -= 1                                               # the side seam...
        for y in range(0, h, 2):
            lv[y, mid + 1 if mid + 1 < w else mid] += 1              # ...and its stitches
    if face in ("north", "south") and w >= 5:
        for x in range(w):
            if x % 4 == 1 and noise(seed + 3, x, 0, 1) < 650:
                top = noise(seed + 4, x, 0, 1) % max(1, h // 3)
                for y in range(top, h):
                    lv[y, x] -= 1                                     # a long fold's shadow...
                    if x + 1 < w:
                        lv[y, x + 1] += 1                             # ...and its lit edge
    if n.startswith("thigh_") and face == "north":
        cx, cy = (w - 1) / 2, h * 0.55
        for y in range(h):
            for x in range(w):
                if ((x - cx) / (w * 0.4)) ** 2 + ((y - cy) / (h * 0.4)) ** 2 < 1:
                    lv[y, x] += 1                                     # worn lighter over the thigh
    if n.startswith("shin_") and face == "north":
        for y in (1, 3):
            for x in range(w):
                if y < h and (x + y) % 5 != 0:
                    lv[y, x] -= 1                                     # two creases bunched at the knee
    if n.startswith("shin_") and face not in ("up", "down"):
        for x in range(w):
            if noise(seed + 9, x, 0, 1) < 450:
                lv[h - 1, x] -= 2                                     # the frayed hem
        for y in range(h // 2, h):
            for x in range(w):
                if noise(seed + 8, x, y, 2) < 260 * (y - h // 2 + 1) / (h // 2 + 1):
                    over.append((y, x, "dirt", 1 if y < h - 2 else 0))
    if n in ("waist", "pelvis") and face in ("north", "south"):
        lv[0, :] -= 1
        for x in range(1, w, 3):
            lv[1, x] -= 1                                             # gathered under the belt
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
    """Brushed steel streaked along the blade and a bright honed bevel along the edge. The blood: dried thick on the
    edge and heaviest towards the tip, runs dripping from the edge down the flat with a drop at each end, a smear
    wiped along it, spatter in clusters; dark and dried, redder where it's fresh."""
    lv, over = blank(cube, w, h)
    world = ctx["world"]
    edge_a, edge_b = ctx["edge"]
    seg = edge_b - edge_a
    t = np.clip(((world - edge_a) @ seg) / (seg @ seg), 0, 1)
    d = np.linalg.norm(world - (edge_a + t[..., None] * seg), axis=-1)
    along = t * np.linalg.norm(seg)                               # texels along the edge, from the handle end
    span = np.linalg.norm(seg)
    runs = [s for s in range(1, int(span)) if noise(seed + 41, s, 0, 1) < 330]
    for y in range(h):
        for x in range(w):
            lv[y, x] += 1 if noise(seed + (x if w > h else y), 0, 0, 1) < 330 else 0       # streaks along the length
            if d[y, x] < 1.6:
                lv[y, x] += 3                                     # the honed bevel
            elif d[y, x] < 2.6:
                lv[y, x] += 1
            tip = along[y, x] / max(1.0, span)                    # 0 at the handle, 1 at the tip
            thick = 1.2 + 1.6 * tip                               # dried blood along the edge, heavier to the tip
            if d[y, x] < thick and noise(seed + 43, int(along[y, x]), 0, 1) < 600 + 380 * tip:
                over.append((y, x, "blood", 1 if d[y, x] < thick - 0.8 else 2))
                continue
            for s in runs:                                        # runs from the edge down the flat
                length = 2 + noise(seed + 47, s, 0, 1) % 6
                if abs(along[y, x] - s) < 0.55 and d[y, x] < thick + length:
                    end = d[y, x] > thick + length - 1.2
                    over.append((y, x, "blood", 4 if end else (2 if d[y, x] < thick + 1.5 else 3)))
                elif end_drop(along[y, x], d[y, x], s, thick + length):
                    over.append((y, x, "blood", 4))
            if 5 < d[y, x] < 7 and 0.25 < tip < 0.7 and noise(seed + 51, x // 2, y // 2, 1) < 420:
                over.append((y, x, "blood", 5 if noise(seed + 53, x, y, 1) < 300 else 3))   # a wiped smear
            if d[y, x] < 9 and noise(seed + 13, x, y, 2) < 70 * (9 - d[y, x]) / 4 and noise(seed + 57, x, y, 1) < 500:
                over.append((y, x, "blood", 3 if noise(seed + 17, x, y, 1) < 600 else 6))   # spatter, a few fresh
    return lv, over


def end_drop(along, d, s, reach):
    """The drop at the end of a run: a texel either side, just above its tip."""
    return abs(along - s) < 1.3 and reach - 0.6 < d < reach + 0.4


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
    """The thick blood caked on the edge and in the runs: dried dark, with a few wet glints."""
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 300, 920, 1)
            if noise(seed + 61, x, y, 1) < 60:
                lv[y, x] = 6
    return lv, over


def paint_plain(cube, face, w, h, seed, ctx):
    return blank(cube, w, h)


def paint_fire(cube, face, w, h, seed, ctx):
    """Hot in the middle, dimmer at its edges, flickering; a flame tongue brightest at its root. Painted near white:
    the fight tints the fire bones its stage colour (session 6)."""
    lv = np.zeros((h, w), int)
    base = ZONE[s4.zone_for(cube)][1]
    if cube.name.startswith("furnace_coal"):
        for y in range(h):
            for x in range(w):                                       # glowing coals, dark where they've crusted
                lv[y, x] = base + (1 if noise(seed, x, y, 1) > 600 else -3 if noise(seed + 1, x, y, 1) > 650 else 0)
        return lv, []
    if cube.name.startswith("flame_"):
        for y in range(h):
            for x in range(w):
                lv[y, x] = base - 1 + (y * 4) // max(1, h) - (1 if noise(seed, x, y, 1) > 750 else 0)   # dim tip, bright root
        return lv, []
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
    result = painter_for(cube)(cube, face, w, h, seed, dict(ctx, world=world, normal=normal))
    lv, over, alpha = result if len(result) == 3 else (*result, None)
    if not zone.startswith(GLOWING) and alpha is None:
        ao = b5.occlusion(model, i, face, w, h, solids)
        if zone == "pants":
            lv = lv - (ao >= 0.6)        # cloth: only a real press darkens it (the thigh over the knee made blots)
        else:
            lv = lv - (ao >= 0.3) - (ao >= 0.55)
    out = c5.from_levels(lv, RAMP[ZONE[zone][0]], alpha)
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


def hidden(cube):
    """In a bone that starts hidden (the flames)."""
    g = cube.group
    while g is not None:
        if not g.visible:
            return True
        g = g.parent
    return False


def painted():
    """The rig, its islands and the painted atlas."""
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
    return k, model, keys, positions, used, height, atlas


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    k, model, keys, positions, used, height, atlas = painted()
    atlas_path = OUT / "occultech_unbound.png"
    atlas.save(atlas_path)
    atlas.resize((atlas.width * 2, atlas.height * 2), Image.NEAREST).save(OUT / "atlas_preview.png")
    bb, _ = s4.rig_bbmodel(model, keys, positions, atlas_path, height, s3.pose_table(k))
    path = OUT / f"{model.name}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    views = s4.VIEWS + s4.grown([
        {"name": "ten_blocks", "location": (-3, 11, 1.62), "target": (0, 0, 1.9), "scale": 8, "player": False,
         "res": (640, 480)},
        {"name": "chest", "location": (1.2, 5.0, 2.4), "target": (0, 0.6, 2.2), "scale": 2.2, "player": False},
        {"name": "cleaver", "location": (4.0, -3.0, 2.0), "target": (1.0, -1.6, 0.2), "scale": 2.6, "player": False},
        {"name": "legs", "location": (1.5, 5.0, 0.9), "target": (0, 0.2, 0.7), "scale": 2.2, "player": False},
        {"name": "chain", "location": (-3.6, 3.6, 0.9), "target": (-1.1, 0.2, 0.5), "scale": 1.4, "player": False},
    ])
    out = OUT / "renders"
    out.mkdir()
    boxes = [{"corners": c.corners().tolist(), "from": c.frm, "to": c.to,
              "glow": s4.zone_for(c).startswith(GLOWING), "uv": bb["elements"][i]["faces"]}
             for i, c in enumerate(model.cubes) if not hidden(c)]
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
