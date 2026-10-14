"""The Mirrored Magus redesign, session 5: texture painting.

Paints the session 4 layout (one 256 x 256 atlas, the same islands):
- the harlequin's diamonds: black and bone white on his legs; on his coat, sleeves and chest, his black half in black
  and crimson diamonds, his white half in bone white and ash; drawn from world position, so the lattice runs on
  across cube edges; folds shade the coat's hanging points, darker at their edges;
- crimson velvet: soft noise, darker folds; the corset laced across in black;
- tarnished gold bells, a bright top, a dark slit;
- the illager's grey skin, mottled;
- the mask (the user will judge it here): old porcelain, faintly mottled, gold filigree round the eyes; the grin
  painted, not modelled - a thin black line running beneath the nose and curling up into the cheeks, small teeth
  marked along it, a crimson stain under it; hairline cracks from the brow down past the left eye; dark drips running
  from the sockets;
- the crystal bow: facets in light and dark bands, bright edges; the string pale;
- the sockets near black, reddening at their lower edge; the claws darkening to their tips.
Form only, no painted light direction: ambient occlusion baked from the real geometry.

Run from the repository root: python tools/art/bosses/magus_s5.py
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
from bosses import magus_s2 as s2, magus_s3 as s3, magus_s4 as s4  # noqa: E402
from bosses import volley_crone_s5 as v5  # noqa: E402

OUT = ROOT / "docs/art/bosses/mirrored_magus/overhaul/s5_paint"
noise = v5.noise
mk = c5.make_ramp
YH, ZF = s2.YH, s2.ZF

RAMP = {
    "black": mk((6, 4, 8), (24, 20, 28), (78, 70, 86), 9),
    "white": mk((96, 90, 84), (206, 198, 180), (246, 242, 232), 9),
    "ash": mk((60, 56, 56), (132, 126, 120), (184, 178, 170), 7),               # the white half's darker diamonds
    "crimson": mk((40, 4, 10), (138, 18, 32), (204, 70, 78), 9),
    "crimson_deep": mk((24, 2, 8), (86, 10, 22), (140, 34, 46), 7),             # the black half's diamonds
    "gold": mk((64, 44, 16), (176, 140, 60), (246, 222, 150), 7),
    "skin": mk((48, 52, 56), (118, 124, 126), (176, 180, 178), 9),
    "nose": mk((44, 48, 50), (100, 106, 108), (156, 160, 160), 7),
    "porcelain": mk((150, 140, 128), (236, 230, 216), (254, 252, 246), 9),
    "socket": [(4, 3, 6), (10, 8, 14), (40, 10, 18), (70, 16, 26)],
    "leg": mk((40, 30, 40), (118, 92, 112), (176, 150, 168), 7),
    "claw": mk((10, 8, 12), (40, 34, 40), (96, 88, 96), 7),
    "crystal": mk((60, 120, 170), (150, 230, 250), (236, 252, 255), 7),
    "crystal_dark": mk((30, 70, 120), (90, 160, 210), (180, 230, 250), 7),
    "string": [(160, 190, 210), (230, 240, 255), (255, 255, 255)],
    "eye_glint": [(90, 200, 230), (150, 240, 255), (240, 255, 255)],
    "ink": [(8, 6, 10), (26, 16, 22)],
    "face": mk((120, 112, 104), (230, 226, 216), (252, 250, 244), 9),
    "greasepaint": mk((120, 112, 104), (230, 226, 216), (252, 250, 244), 9),
    "lips": mk((40, 4, 10), (150, 14, 28), (220, 80, 86), 7),
    "teeth": mk((110, 98, 70), (234, 226, 198), (252, 250, 236), 7),
    "rednose": mk((70, 6, 12), (196, 24, 36), (255, 140, 140), 7),
    "hair": mk((28, 4, 10), (96, 16, 28), (160, 50, 60), 7),
    "mouth": [(18, 2, 6), (40, 6, 12)],
    "card": mk((150, 140, 128), (238, 232, 220), (255, 252, 246), 7),
    "card_back": mk((40, 4, 10), (120, 16, 30), (180, 50, 60), 7),
    "rot": [(54, 40, 20), (92, 70, 34), (140, 112, 60)],                       # stained, rotting teeth
    "gum": [(60, 6, 14), (110, 20, 30)],
    "makeup": mk((90, 10, 20), (186, 30, 44), (226, 90, 96), 7),            # the clown's red mouth paint
    "sclera": [(180, 120, 110), (232, 226, 210)],                                          # the grin's line, the cracks
    "stain": [(96, 24, 30), (120, 40, 44)],
}
ZONE = {"black": ("black", 4), "white": ("white", 4), "crimson": ("crimson", 4), "gold": ("gold", 3),
        "skin": ("skin", 4), "nose": ("nose", 3), "porcelain": ("porcelain", 4), "socket": ("socket", 1),
        "leg": ("leg", 3), "claw": ("claw", 3), "crystal": ("crystal", 3), "crystal_dark": ("crystal_dark", 3),
        "string": ("string", 1), "eye_glint": ("eye_glint", 1), "face": ("face", 4), "lips": ("lips", 3),
        "teeth": ("teeth", 3), "rednose": ("rednose", 3), "hair": ("hair", 3), "card": ("card", 3), "throat": ("mouth", 0)}
GLOWING = s4.GLOWING
DIAMOND_PARTS = ("coat_", "chest_", "ribs_", "upper_", "fore_", "thigh_", "shin_")


def texel_points(cube, face, w, h):
    """Like volley_crone_s5.texel_points, at the cube's own texel density (session 4: 4 per unit on his head)."""
    d = s4.density(cube)
    if d == 1:
        return v5.texel_points(cube, face, w, h)
    pts, n, tu, tv = v5.texel_points(cube, face, w // d, h // d)
    au, su, av, sv = v5.FACE_UV[face]
    lo, hi = np.array(cube.frm), np.array(cube.to)
    us, vs = np.meshgrid((np.arange(w) + 0.5) / d, (np.arange(h) + 0.5) / d)
    full = np.zeros((h, w, 3))
    full[...] = pts[0, 0]
    full[..., au] = lo[au] + us if su > 0 else hi[au] - us
    full[..., av] = lo[av] + vs if sv > 0 else hi[av] - vs
    return full, n, tu, tv


def world_points(cube, face, w, h):
    pts, n, _, _ = texel_points(cube, face, w, h)
    m = v5.cube_matrix(cube)
    flat = np.c_[pts.reshape(-1, 3), np.ones(w * h)]
    world = (m @ flat.T).T[:, :3].reshape(h, w, 3)
    return world, m[:3, :3] @ n


def blank(cube, w, h):
    return np.full((h, w), ZONE[s4.zone_for(cube)][1], int), []


def clusters(seed, x, y, lo=170, hi=830, cell=2):
    r = noise(seed, x, y, cell)
    return -1 if r < lo else (1 if r > hi else 0)


def diamond_mask(w, h, offset=0):
    """The harlequin's diamonds on one face, in its own texels: a single chain of tall diamonds down a narrow face (a
    leg or a sleeve), a lattice of diamonds on a wide one. Returns -1 outside a diamond, else the diamond's index (its
    parity alternates the colours)."""
    out = np.full((h, w), -1, int)
    if w <= 6:
        period, cx = 7, (w - 1) / 2
        for y in range(h):
            k, r = divmod(y + offset, period)
            for x in range(w):
                if abs(x - cx) / (w / 2) + abs(r - (period - 1) / 2) / (period / 2) <= 1.0:
                    out[y, x] = k
        return out
    d = 5
    for y in range(h):
        for x in range(w):
            a, b = (x + y + offset) // d, (x - y + 100) // d
            out[y, x] = (a + b) % 2 if (a + b) % 2 else -1
    return out


# ---- painters ---------------------------------------------------------------------------------------------------------

def paint_cloth(cube, face, w, h, seed, ctx):
    """The harlequin's cloth, in what this size can hold (take 3: at 4 texels a limb, diamonds broke into crosses):
    one large diamond on each half of his chest in the opposite colour (crimson on black, black on white); crimson
    bands round his sleeves; split-colour legs, his left black and his right bone white, a crimson garter at the
    thigh; soft noise; the coat's hanging points darker at their edges."""
    lv, over = blank(cube, w, h)
    zone = s4.zone_for(cube)
    n = cube.name
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 120, 900, 2)
    if face in ("up", "down"):
        return lv, over
    lv[0, :] += 1
    if h > 3:
        lv[h - 1, :] -= 1
    if n.startswith("coat") and w >= 3:
        lv[:, 0] -= 1
        lv[:, w - 1] -= 1
    if n.startswith(("chest_", "ribs_")) and w >= 5:
        cx, cy = (w - 1) / 2, (h - 1) / 2
        for y in range(h):
            for x in range(w):
                if abs(x - cx) / (w / 2 - 0.3) + abs(y - cy) / (h / 2 - 0.3) <= 1.0:
                    over.append((y, x, "crimson_deep" if zone == "black" else "black", 3 if zone == "black" else 4))
    if n.startswith(("upper_", "fore_")):
        for y in range(h):
            if y % 6 in (2, 3):
                for x in range(w):
                    over.append((y, x, "crimson", 3))                  # bands round the sleeve
    if n.startswith(("thigh_", "shin_")):
        left = "left" in n
        for y in range(h):
            for x in range(w):
                over.append((y, x, "black" if left else "white", 4))
        if n.startswith("thigh_"):
            for y in range(h // 2, h // 2 + 2):
                for x in range(w):
                    over.append((y, x, "crimson", 4))                  # the garter
    return lv, over


def paint_crimson(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 200, 820, 1)              # velvet
    if face not in ("up", "down"):
        lv[0, :] += 1
    if cube.name == "corset" and face == "north":
        mid = (w - 1) / 2
        for y in range(h):
            for x in range(w):
                if abs(abs(x - mid) - (y % 3)) < 0.6:                 # laced across in black
                    over.append((y, x, "ink", 0))
    return lv, over


def paint_gold(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 250, 800, 1)
    if face == "up":
        lv += 2
    elif face == "down":
        lv -= 2
        if w >= 2:
            lv[h // 2, :] = 0                                          # the bell's slit
    return lv, over


def paint_skin(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    d = s4.density(cube)                                               # mottling at the base texel size, not finer
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x // d, y // d, 160 if d == 1 else 60, 860 if d == 1 else 960, 2)
    if cube.name == "head" and face == "north" and s2.MASK == "colombina":
        paint_face_skin(lv, over, ctx["world"], seed)
    if cube.name == "head" and face == "north" and s2.MASK == "clown":
        paint_clown_head(lv, over, ctx["world"], seed)
    if cube.name == "head" and face != "north" and s2.MASK == "clown":
        for y in range(h):                                             # his whole head is white: it's his face
            for x in range(w):
                over.append((y, x, "greasepaint", 3 if face in ("south", "down") else 4))
    return lv, over


def paint_porcelain(cube, face, w, h, seed, ctx):
    """Clean porcelain; the mask's features painted on its front (paint_mask)."""
    lv, over = blank(cube, w, h)
    world, normal = ctx["world"], ctx["normal"]
    if normal[2] < -0.5:
        paint_mask(lv, over, world, seed)
    return lv, over


def _eye(px, py, sx, wide=2.0, tall=0.8):
    """Inside an almond eye hole, slanting up and out."""
    ex, ey = sx * 3.1, YH + 2.2
    dx, dy = px - ex, py - ey - 0.35 * (px - ex) * sx
    return abs(dx) / wide + abs(dy) / tall < 1.0


def paint_mask(lv, over, world, seed):
    h, w = lv.shape
    for y in range(h):
        for x in range(w):
            px, py, pz = world[y, x]
            mark = None
            if s2.MASK == "volto":
                if _eye(px, py, -1) or _eye(px, py, 1):
                    mark = ("ink", 0)
                elif abs(px + 3.1) / 1.7 + abs(py - (YH + 2.2)) / 5.2 < 1.0:
                    mark = ("ink", 0)                                   # the harlequin's diamond through his left eye
                elif math.hypot((px - 3.4) / 0.7, (py - (YH - 1.6)) / 1.3) < 1.0:
                    mark = ("ink", 0)                                   # a black tear under the right
                elif abs(px) < 3.6:
                    gy = YH - 6 + 0.13 * px * px
                    if abs(py - gy) < 0.5:
                        mark = ("ink", 0)
                    elif 0.5 <= py - gy < 1.4 and abs(px) < 2.6 or -1.4 < py - gy <= -0.5 and abs(px) < 2.2:
                        mark = ("crimson", 4)                           # small blood-red lips
                if mark is None and 0 < px < 4.5 and YH + 3 < py < YH + 8.4:
                    cx = 1.2 + 0.45 * (YH + 8.4 - py) + 0.3 * math.sin(py * 2.1)
                    if abs(px - cx) < 0.4:
                        mark = ("ink", 1)                               # a hairline crack
            elif s2.MASK == "colombina":
                if _eye(px, py, -1, 2.2, 1.0) or _eye(px, py, 1, 2.2, 1.0):
                    mark = ("ink", 0)
                elif py > YH + 4.6 or py < YH - 0.2 or abs(px) > 6.0:
                    mark = ("gold", 4)                                  # the gold trim round its edge
                else:
                    mark = ("black", 3)
            elif s2.MASK == "comedy":
                for sx in (-1, 1):                                       # crescent eyes that smile (a ^ shape)
                    ex, ey = sx * 3.1, YH + 2.0
                    if math.hypot((px - ex) / 2.2, (py - ey) / 1.6) < 1 and math.hypot((px - ex) / 2.2, (py - ey + 1.2) / 1.6) > 1:
                        mark = ("ink", 0)
                top, bottom = YH - 5.2 + 0.1 * px * px, YH - 8.4 + 0.06 * px * px
                if abs(px) < 5.0 and bottom < py < top:
                    mark = ("ink", 0) if py < top - 0.6 else ("crimson", 3)    # the grinning void, a crimson rim
            if mark:
                over.append((y, x) + mark)


def paint_face_skin(lv, over, world, seed):
    """Under the colombina, the illager's own face: a grin stitched across it."""
    h, w = lv.shape
    for y in range(h):
        for x in range(w):
            px, py, pz = world[y, x]
            gy = YH - 6.6 + 0.12 * px * px
            if abs(px) < 5 and abs(py - gy) < 0.5:
                over.append((y, x, "ink", 0))
            elif abs(px) < 4.2 and abs(py - gy) < 1.5 and int(round(px)) % 2 == 0:
                over.append((y, x, "ink", 1))


def paint_socket(cube, face, w, h, seed, ctx):
    lv = np.zeros((h, w), int)
    for y in range(h):
        lv[y, :] = 1 if y < h - 1 else 2
    return lv, []


def paint_claw(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    world = ctx["world"]
    lo = cube.corners()[:, 1].min()
    for y in range(h):
        for x in range(w):
            if world[y, x][1] - lo < 2:
                lv[y, x] -= 2                                          # darker to the tips
    return lv, over


def paint_crystal(cube, face, w, h, seed, ctx):
    """Facets in light and dark bands, bright edges."""
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            band = ((x + y) // 2 + noise(seed, 0, (x - y) // 3, 1) % 2) % 3
            lv[y, x] += (1, 0, -1)[band]
    lv[0, :] += 2
    lv[:, 0] += 1
    return lv, over


def paint_plain(cube, face, w, h, seed, ctx):
    return blank(cube, w, h)


def in_mouth(px, py):
    c, half = s2.mouth_curve(px)
    return abs(px) < 6 and abs(py - c) < half


def _h(k, salt):
    """A steady pseudo-random 0..1 per tooth."""
    return noise(9001 + salt, int(k), 0, 1) / 999


def grin(px, py):
    """What the face is at a world point round his mouth (take 3): the clown's red mouth paint stretched wide up into
    his cheeks; inside it his real mouth, its lips dark crimson, packed with nasty teeth - crooked, uneven, stained,
    some broken off or missing, longer fangs among them - over bleeding gums, a darker second row behind, the black
    throat between. Returns a paint (ramp, shade) or None."""
    c, half = s2.mouth_curve(px)
    if abs(px) > 6.8:
        return None
    d = py - c
    if abs(px) < 6.4 and abs(d) < half + 1.35 and not abs(d) < half:
        return ("lips", 2) if abs(d) < half + 0.3 else ("makeup", 3 + (abs(d) > half + 1.0))
    if not abs(d) < half:
        return None
    up, low = c + half, c - half
    # the front teeth: one per 0.62 along the mouth, each its own width, length, lean and stain
    k = round(px / 0.62)
    cx = k * 0.62 + (_h(k, 1) - 0.5) * 0.18
    wide = 0.18 + 0.14 * _h(k, 2)
    for top, sign, salt in ((up, -1, 0), (low, 1, 5)):
        missing = _h(k, 3 + salt) > 0.86
        if missing:
            continue
        fang = _h(k, 4 + salt) > 0.78
        length = (1.35 if fang else 0.45 + 0.6 * _h(k, 6 + salt)) * (0.75 if sign > 0 else 1)
        along = (py - top) * sign                           # how far from the gum into the mouth
        lean = (_h(k, 7 + salt) - 0.5) * 0.5 * along        # crooked
        taper = 1 - along / max(0.01, length)               # pointed: narrower towards the tip
        if 0 <= along < length and abs(px - cx - lean) < wide * (0.35 + 0.65 * taper):
            if along < 0.14:
                return ("gum", 1)
            stain = _h(k, 8 + salt)
            if along > length * 0.7 and stain > 0.5 or stain > 0.85:
                return ("rot", 1 if stain > 0.7 else 2)      # brown at the tips, or rotten through
            return ("teeth", 3 + (abs(px - cx - lean) < wide * 0.3))
        if along < 0.14:
            return ("gum", 0)                               # bleeding gums between them
    # the second row, behind and between the first
    k2 = round((px - 0.31) / 0.62)
    cx2 = k2 * 0.62 + 0.31
    for top, sign in ((up, -1), (low, 1)):
        along = (py - top) * sign
        length2 = 0.3 + 0.35 * _h(k2, 11)
        if 0.1 < along < length2 + 0.1 and abs(px - cx2) < 0.12 * (1 - along / (length2 + 0.1)) + 0.05:
            return ("rot", 0)
    return ("mouth", 0)


def near_socket(px, py):
    """0 outside, else how deep into the dark round an eye (1 at its middle)."""
    best = 0.0
    for sx in (-1, 1):
        r = math.hypot((px - sx * 3.1) / 2.6, (py - (YH + 2.2)) / 2.0)
        best = max(best, 1 - r)
    return best


def paint_clown_head(lv, over, world, seed):
    """The head's own front, behind his sculpted face: white greasepaint, black round his eyes, and the dark of his
    mouth behind the teeth - the throat blackest in the middle, a deep red towards the lips."""
    h, w = lv.shape
    for y in range(h):
        for x in range(w):
            px, py, pz = world[y, x]
            c, half = s2.mouth_curve(px)
            if abs(px) < s2.MOUTH_W and abs(py - c) < half + 0.3:
                deep = abs(py - c) < half * 0.6 and abs(px) < 4.5
                over.append((y, x, "mouth", 0 if deep else 1))
            elif near_socket(px, py) > 0.12:
                over.append((y, x, "ink", 0))
            else:
                over.append((y, x, "greasepaint", 4))


def paint_face_paint(cube, face, w, h, seed, ctx):
    """White greasepaint, finely cracked; black round his eyes and a black diamond running down from each; the red of
    his clown's mouth spreading from his lips onto the cheeks and jaw beside them; a drip down from each corner."""
    lv, over = blank(cube, w, h)
    world, normal = ctx["world"], ctx["normal"]
    front = normal[2] < -0.5
    n = cube.name
    for y in range(h):
        for x in range(w):
            px, py, pz = world[y, x]
            if noise(seed + 3, x // 2, y // 2, 1) > 975:
                lv[y, x] -= 1                                          # the greasepaint's fine cracks
            if n.startswith("brow"):
                if face == "down":
                    over.append((y, x, "ink", 0))                      # the brow's shadow falls into the socket
                continue
            if not front:
                continue
            for sx in (-1, 1):
                ex, ey = sx * 3.1, YH + 2.2
                if not n.startswith("brow") and abs(px - ex) / 1.0 + abs(py - (ey - 1.6)) / 3.0 < 1.0 \
                        and py < ey - 0.9:
                    over.append((y, x, "ink", 0))                      # a black diamond down from each eye
            if near_socket(px, py) > 0.12 and not n.startswith(("chin", "jaw")):
                over.append((y, x, "ink", 0 if near_socket(px, py) > 0.3 else 1))
            if n.startswith("mouth_cheek"):
                c, half = s2.mouth_curve(px)
                if abs(py - c) < half + 1.6:
                    over.append((y, x, "makeup", 3))                   # the clown's red spreading past his lips
                if abs(abs(px) - (s2.MOUTH_W + 0.4)) < 0.25 and py < c:
                    over.append((y, x, "lips", 2))                     # a drip down from each corner
    return lv, over


def paint_lips(cube, face, w, h, seed, ctx):
    """Thick red lips: glossy on top, darker underneath and inside, a highlight along the front's upper edge."""
    lv, over = blank(cube, w, h)
    d = s4.density(cube)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x // d, y // d, 200, 850, 1)
    if face == "up":
        lv += 1
    elif face == "down":
        lv -= 2
    elif face == "north":
        lv[: max(1, h // 6), :] += 2
        lv[h - max(1, h // 6):, :] -= 1
    else:
        lv -= 1
    return lv, over


def paint_teeth(cube, face, w, h, seed, ctx):
    """Real teeth: yellowed, brown and darker towards the gum, a lighter tip, stained here and there; some teeth
    rotten through."""
    lv, over = blank(cube, w, h)
    world = ctx["world"]
    upper = "upper" in cube.name
    lo, hi = cube.corners()[:, 1].min(), cube.corners()[:, 1].max()
    rotten = noise(zlib.crc32(cube.name.split("_tip")[0].encode()), 0, 0, 1) > 780
    for y in range(h):
        for x in range(w):
            py = world[y, x][1]
            t = (hi - py) / max(0.1, hi - lo) if upper else (py - lo) / max(0.1, hi - lo)   # 0 at the gum end
            if cube.name.endswith("_tip"):
                t = 1.0
            if rotten:
                over.append((y, x, "rot", 0 if t < 0.4 else 1))
            elif t < 0.25:
                over.append((y, x, "rot", 1))                          # brown at the gum
            else:
                lv[y, x] += (1 if t > 0.8 else 0) - (1 if noise(seed, x // 2, y // 2, 1) > 860 else 0)
    if face in ("east", "west", "south"):
        lv -= 1
    return lv, over


def paint_rednose(cube, face, w, h, seed, ctx):
    """A glossy red ball: a highlight up and to the left, darker underneath, a crack across it."""
    lv, over = blank(cube, w, h)
    if face == "down":
        lv -= 2
    elif face in ("north", "up"):
        for y in range(h):
            for x in range(w):
                if x < w * 0.4 and y < h * 0.4:
                    lv[y, x] += 2
                if face == "north" and abs(x - y * 0.7 - w * 0.4) < 0.5:
                    lv[y, x] -= 3                                      # the crack
    return lv, over


def paint_hair(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += (1 if (x + noise(seed, 0, y, 1) % 3) % 3 == 0 else -1 if x % 4 == 2 else 0)
    return lv, over


def paint_eye(cube, face, w, h, seed, ctx):
    """His eyes (the clown's): an illager's - a pale, bloodshot white, a cyan iris, a dark pupil looking a little
    inward. Full-bright (the glow bone), so they stare out of the dark round them."""
    lv = np.full((h, w), 1, int)
    over = []
    if not cube.name.startswith("eye_") or face != "north":
        return lv, over
    world = ctx["world"]
    sx = 1 if world[0, 0][0] > 0 else -1
    cx, cy = sx * 3.1 - sx * 0.25, YH + 2.2
    for y in range(h):
        for x in range(w):
            px, py, pz = world[y, x]
            r = math.hypot(px - cx, (py - cy) * 1.1)
            if r < 0.24:
                over.append((y, x, "ink", 0))                          # the pupil
            elif r < 0.68:
                over.append((y, x, "eye_glint", 1 + (r < 0.5)))         # the cyan iris
            else:
                edge = abs(py - cy) > 0.62
                vein = noise(seed, x, y, 1) > 975
                over.append((y, x, "sclera", 0 if edge or vein else 1))  # the white, bloodshot
    return lv, over


SUITS = ("spade", "heart", "diamond", "club", "joker")


def _suit(name, u, v):
    """Whether a card's (u, v) in 0..1 falls in its suit's mark (drawn big in the middle) - and its colour."""
    du, dv = u - 0.5, v - 0.5
    if name == "diamond":
        return abs(du) / 0.24 + abs(dv) / 0.3 < 1, "makeup"
    if name == "heart":
        lobes = math.hypot(du + 0.11, dv + 0.08) < 0.13 or math.hypot(du - 0.11, dv + 0.08) < 0.13
        return lobes or (-0.1 < dv < 0.22 and abs(du) < 0.23 * (0.22 - dv) / 0.32), "makeup"
    if name == "spade":
        lobes = math.hypot(du + 0.11, dv - 0.06) < 0.13 or math.hypot(du - 0.11, dv - 0.06) < 0.13
        point = -0.24 < dv < 0.08 and abs(du) < 0.23 * (dv + 0.24) / 0.32
        return lobes or point or (0.08 < dv < 0.26 and abs(du) < 0.04), "ink"
    if name == "club":
        blobs = (math.hypot(du, dv + 0.1) < 0.1 or math.hypot(du - 0.11, dv + 0.02) < 0.1
                 or math.hypot(du + 0.11, dv + 0.02) < 0.1)
        return blobs or (0.0 < dv < 0.24 and abs(du) < 0.04), "ink"
    # the joker: a grinning jester's face
    face = math.hypot(du, (dv - 0.04) * 0.9) < 0.2
    grin = 0.06 < dv < 0.14 and abs(du) < 0.13 and dv > 0.06 + 0.4 * du * du
    return (face and not grin) or (-0.34 < dv < -0.16 and abs(du) < 0.2 - (dv + 0.34)), "makeup" if face else "ink"


def paint_card(cube, face, w, h, seed, ctx):
    """A playing card: on its face (towards his target) a white card, a thin border, its suit drawn big - spade, heart,
    diamond, club, and a grinning joker; on its back crimson with a black diamond lattice and a gold border."""
    k = int(cube.name.split("_")[1])
    lv = np.full((h, w), 3, int)
    over = []
    back = face == "south"
    for y in range(h):
        for x in range(w):
            u, v = (x + 0.5) / w, (y + 0.5) / h
            edge = min(x, y, w - 1 - x, h - 1 - y)
            if back:
                if edge < 1:
                    over.append((y, x, "gold", 3))
                else:
                    a, b = (x + y) // 4, (x - y + 64) // 4
                    over.append((y, x, "card_back", 3) if (a + b) % 2 else (y, x, "ink", 1))
                continue
            if edge < 1:
                lv[y, x] = 1                                           # the card's thin dark edge
                continue
            inside, ramp = _suit(SUITS[k], u, v)
            if inside:
                over.append((y, x, ramp, 3 if ramp == "makeup" else 0))
            elif (u < 0.22 and v < 0.18) or (u > 0.78 and v > 0.82):
                if (x + y) % 2 == 0:
                    over.append((y, x, "makeup" if SUITS[k] in ("heart", "diamond", "joker") else "ink", 2))  # an index
    return lv, over


def painter_for(cube):
    return {"black": paint_cloth, "white": paint_cloth, "leg": paint_cloth, "crimson": paint_crimson,
            "gold": paint_gold, "skin": paint_skin, "nose": paint_skin, "porcelain": paint_porcelain,
            "socket": paint_socket, "claw": paint_claw, "crystal": paint_crystal, "crystal_dark": paint_crystal,
            "string": paint_plain, "eye_glint": paint_eye, "face": paint_face_paint, "lips": paint_lips,
            "teeth": paint_teeth, "rednose": paint_rednose, "hair": paint_hair,
            "card": paint_card, "throat": paint_plain}[s4.zone_for(cube)]


def paint_face(model, i, face, w, h, solids):
    cube = model.cubes[i]
    seed = zlib.crc32(f"{cube.name}/{face}".encode())
    zone = s4.zone_for(cube)
    world, normal = world_points(cube, face, w, h)
    lv, over = painter_for(cube)(cube, face, w, h, seed, {"world": world, "normal": normal})
    if not zone.startswith(GLOWING) and zone != "porcelain":         # the mask stays clean (no shading blotches)
        d = s4.density(cube)
        ao = b5.occlusion(model, i, face, w // d, h // d, solids)
        ao = np.kron(ao, np.ones((d, d)))
        lv = lv - (ao >= 0.3) - (ao >= 0.55)
    out = c5.from_levels(lv, RAMP[ZONE[zone][0]], None)
    for y, x, rname, shade in over:
        if 0 <= y < h and 0 <= x < w:
            r = RAMP[rname]
            # the overlays keep the face's own light and shade (the diamonds fold with the cloth)
            s = shade + int(lv[y, x] - ZONE[zone][1]) if rname not in ("ink", "stain", "gold") else shade
            out[y, x, :3] = r[max(0, min(len(r) - 1, s))]
    return out


def painted():
    model = s2.build(s3.MODEL_ID)
    s2.finish(model)
    keys = s4.island_keys(model)
    sizes = {key: (key[2], key[3]) for key in keys.values()}
    positions, used, height = b4.pack(sizes)
    owner = {}
    for (i, f), key in sorted(keys.items(), key=lambda kv: (kv[0][0], FACES.index(kv[0][1]))):
        owner.setdefault(key, (i, f))
    solids = b5.solids_of(model)
    atlas = Image.new("RGBA", (s4.SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        i, f = owner[key]
        patch = Image.fromarray(paint_face(model, i, f, w, h, solids), "RGBA")
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return model, keys, positions, used, height, atlas


CLOSE = [
    {"name": "mask", "location": (0.8, 5, 5.15), "target": (0, -0.1, 5.1), "scale": 1.45, "player": False},
    {"name": "mask_34", "location": (3.5, 4, 5.3), "target": (0, -0.1, 5.1), "scale": 1.6, "player": False},
    {"name": "costume", "location": (2.5, 6, 3.4), "target": (0, 0, 3.4), "scale": 2.6, "player": False},
    {"name": "legs", "location": (2, 6, 1.4), "target": (0, 0, 1.3), "scale": 3.2, "player": False},
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
    atlas_path = OUT / "occultech_mirrored_magus.png"
    atlas.save(atlas_path)
    atlas.resize((atlas.width * 2, atlas.height * 2), Image.NEAREST).save(OUT / "atlas_preview.png")
    bb, _ = s4.rig_bbmodel(model, keys, positions, atlas_path, height, s3.pose_table())
    path = OUT / f"{model.name}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    out = OUT / "renders"
    s4.render_all(model, bb, atlas_path, out)
    s4.render(model, bb, atlas_path, out, CLOSE)
    names = ["hero", "front", "side", "back", "draw", "mask", "mask_34", "costume", "legs"]
    tw, th, pad, top, cols = 470, 352, 12, 56, 3
    rows = (len(names) + cols - 1) // cols
    img = Image.new("RGB", (pad + cols * (tw + pad), top + rows * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Mirrored Magus - painted (session 5)", font=sheet._font(28), fill=sheet.INK)
    for n_, name in enumerate(names):
        x, y = pad + (n_ % cols) * (tw + pad), top + (n_ // cols) * (th + 34 + pad)
        img.paste(sheet._tile(out / f"{name}.png", tw, th), (x, y))
        dr.text((x, y + th + 6), name.replace("_", " "), font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "sheet.png")
    print(json.dumps({"atlas": [s4.SIZE, height], "rows_used": used, "islands": len(positions)}))


if __name__ == "__main__":
    main()
