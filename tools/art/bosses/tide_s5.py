"""The Tidebreaker redesign, session 5: texture painting (plan: docs/art/bosses/tidebreaker/overhaul/plan.md).

Paints session 4's layouts (the same islands). Ramps run from a cool dark through the zone's colour to a warm light; form
only, with ambient occlusion baked from the real geometry.
- The shell, from each texel's place on the coil: a spiral of growth lines, tiger stripes tapering in from the rim, salt
  and age in soft patches.
- The longship: clinker strakes with grain, a row of iron rivets weeping rust, tar along the laps, weed creeping up from
  the waterline; a planked deck; shields with flaking paint on bare wood and an iron rim.
- The dragon: carved wood, scales cut into the neck and skull, worn paint, ivory teeth.
- The animal: wet, mottled flesh; ringed tentacles with pale suckers; a gold eye.
- The Viking: the real zombie face with the crust and stain grown in under the barnacles, the eyes and mouth bare; green
  arms; torn leather with ragged hems and stitching; bound shins; a fur collar; a rusted, riveted helmet; ringed ox
  horns.
Every texel is fully opaque or fully clear.

Run from the repository root, with a folder holding the 26.2 zombie textures as the last argument:
python tools/art/bosses/tide_s5.py <folder>
"""
import json
import math
import shutil
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES  # noqa: E402
from bosses import archevoker_s4 as a4, archevoker_s5 as a5, brood_s4 as b4, brood_s5 as b5, coven_s5 as c5  # noqa: E402
from bosses import tide_s2 as s2, tide_s3 as s3, tide_s4 as s4, volley_crone_s5 as v5  # noqa: E402
from bosses.tide_silhouettes import CY, CZ, R  # noqa: E402

OUT = ROOT / "docs/art/bosses/tidebreaker/overhaul/s5_paint"
noise = v5.noise
mk = c5.make_ramp
Z = s4.ZONES
tf2 = s2.tf2


def ramp(zone, dark, light, n=9):
    return mk(dark, Z[zone], light, n)


RAMP = {
    "shell": ramp("shell", (108, 92, 92), (252, 244, 218)), "stripe": ramp("stripe", (66, 24, 32), (214, 122, 84), 7),
    "shell_in": ramp("shell_in", (58, 46, 54), (206, 186, 156), 7), "nacre": ramp("nacre", (96, 108, 132), (244, 248, 250), 7),
    "body": ramp("body", (58, 18, 30), (214, 116, 92)), "hood": ramp("hood", (26, 12, 20), (146, 80, 66), 7),
    "tentacle": ramp("tentacle", (78, 26, 36), (240, 164, 128)), "sucker": mk((150, 96, 92), (226, 178, 152), (250, 226, 200), 5),
    "naut_eye": ramp("naut_eye", (106, 66, 40), (255, 240, 176), 7), "pupil": [(4, 4, 8), (18, 18, 24), (44, 46, 58)],
    "wood": ramp("wood", (32, 28, 34), (178, 166, 142)), "wood_dark": ramp("wood_dark", (14, 12, 18), (120, 106, 92), 7),
    "tar": mk((8, 8, 12), (28, 26, 30), (64, 60, 62), 5), "weed": mk((12, 34, 32), (44, 78, 58), (104, 130, 82), 5),
    "iron": ramp("iron", (16, 18, 26), (140, 144, 150)), "iron_light": ramp("iron_light", (40, 42, 54), (196, 198, 200), 7),
    "rust": mk((40, 22, 24), (92, 54, 40), (138, 86, 54), 5), "rope": ramp("rope", (72, 54, 44), (222, 198, 142), 7),
    "net": ramp("net", (60, 46, 40), (210, 186, 136), 5), "paint_white": ramp("paint_white", (104, 96, 96), (242, 236, 214), 7),
    "paint_red": ramp("paint_red", (44, 12, 20), (190, 84, 62), 7), "tooth": ramp("tooth", (112, 96, 84), (246, 238, 212), 7),
    "dark": [(4, 4, 8), (16, 16, 20), (34, 34, 40)], "gum": ramp("gum", (40, 16, 24), (150, 82, 80), 5),
    "glow": [(214, 128, 44), (244, 172, 62), (255, 214, 110), (255, 238, 170), (255, 252, 226)],
    "skin": ramp("skin", (26, 54, 34), (146, 186, 104)), "skin_dark": ramp("skin_dark", (14, 34, 26), (88, 124, 72), 7),
    "leather": ramp("leather", (28, 16, 20), (160, 118, 82)), "leather_dark": ramp("leather_dark", (10, 6, 12), (112, 82, 62), 7),
    "stitch": mk((96, 80, 60), (168, 148, 110), (214, 198, 158), 3), "fur": ramp("fur", (46, 38, 40), (206, 192, 164)),
    "horn": ramp("horn", (98, 76, 62), (250, 240, 214)),
    "b_big": mk((92, 90, 80), Z["b_big"], (214, 210, 186), 7), "b_mid": mk((92, 90, 80), Z["b_mid"], (198, 196, 172), 7),
    "b_dark": mk((76, 78, 70), Z["b_dark"], (172, 172, 150), 5), "b_hole": [(20, 22, 22), Z["b_hole"], (90, 94, 82)],
}
MID = {k: (len(v) - 1) // 2 for k, v in RAMP.items()}
MID.update({"glow": 2, "pupil": 1, "dark": 1, "b_hole": 1})
GLOWING = ("glow",)


def smooth(seed, u, v, scale):
    x, y = u / scale, v / scale
    x0, y0 = math.floor(x), math.floor(y)
    fx, fy = x - x0, y - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    at = lambda i, j: noise(seed, i, j, 1) / 999
    return (at(x0, y0) * (1 - fx) + at(x0 + 1, y0) * fx) * (1 - fy) + (at(x0, y0 + 1) * (1 - fx) + at(x0 + 1, y0 + 1) * fx) * fy


class Face:
    def __init__(self, cube, face, w, h):
        self.cube, self.face, self.w, self.h = cube, face, w, h
        self.lv = np.full((h, w), MID.get(cube.mat, 4), int)
        self.zone = np.full((h, w), cube.mat, object)
        self.alpha = np.full((h, w), 255, int)
        pts, n, _, _ = v5.texel_points(cube, face, w, h)
        m = v5.cube_matrix(cube)
        flat = pts.reshape(-1, 3)
        self.p = (m @ np.c_[flat, np.ones(len(flat))].T).T[:, :3].reshape(h, w, 3)
        self.n = m[:3, :3] @ n
        self.local_n = n
        lo, hi = np.array(cube.frm), np.array(cube.to)
        self.axis = int(np.argmax(hi - lo))
        self.t = pts[..., self.axis] - lo[self.axis]
        self.length = float(hi[self.axis] - lo[self.axis])
        self.seed = zlib.crc32(f"{cube.name}/{face}".encode())
        self.along_v = h > w
        self.side = abs(n[self.axis]) < 0.5                   # a face that runs along the cube's length

    def set(self, y, x, zone, level=None):
        if 0 <= y < self.h and 0 <= x < self.w:
            self.zone[y, x], self.lv[y, x] = zone, MID[zone] if level is None else level

    def across(self, y, x):
        return x if self.along_v else y


def mottle(f, lo=170, hi=830, cell=2, seed=0):
    for y in range(f.h):
        for x in range(f.w):
            r = noise(f.seed + seed, x, y, cell)
            f.lv[y, x] += -1 if r < lo else (1 if r > hi else 0)


def form(f):
    if f.n[1] > 0.7:
        f.lv += 1
    elif f.n[1] < -0.7:
        f.lv -= 2
    elif f.h >= 3:
        f.lv[0, :] += 1
        f.lv[f.h - 1, :] -= 1


def grain(f, lo=170, hi=880):
    """Grain along the longer side: streaks a few texels long, never speckle."""
    for y in range(f.h):
        for x in range(f.w):
            a, b = (y, x) if f.along_v else (x, y)
            r = noise(f.seed, b, a // 7, 1) if noise(f.seed + 1, b, a // 5, 1) > 450 else noise(f.seed + 2, b, a // 11, 1)
            f.lv[y, x] += -1 if r < lo else (1 if r > hi else 0)


# ---- the nautilus ------------------------------------------------------------------------------------------------------

def coil(p):
    dy, dz = p[1] - CY, p[2] - CZ
    return math.hypot(dy, dz), math.atan2(dz, dy)


def paint_shell(f):
    outer = f.side or f.n[0] ** 2 > 0.4
    for y in range(f.h):
        for x in range(f.w):
            p = f.p[y, x]
            r, th = coil(p)
            lv = MID["shell"]
            flank = abs(f.n[0]) > 0.7
            if flank:                                         # growth rings: one wavering line every few texels
                if int(r + 1.2 * math.sin(th * 5)) % 6 == 0:
                    lv -= 1
            elif int(th * 14 + 40) % 5 == 0:
                lv -= 1
            s = smooth(31, r * 1.5, th * 9, 7)
            lv += -1 if s < 0.2 else (1 if s > 0.8 else 0)
            deg = math.degrees(th) + 5 * math.sin(r / 5)
            if outer and flank and r > R * 0.5 and (deg % 40) < 7 * (r / R) ** 3:
                f.set(y, x, "stripe", MID["stripe"] + (1 if noise(f.seed, x, y, 2) > 780 else 0))
                continue
            f.lv[y, x] = lv
    if not (f.cube.name.startswith(("flank_", "dome_", "whorl_")) and abs(f.n[0]) > 0.7):
        form(f)


def paint_stripe(f):
    mottle(f, 150, 850, 2)
    if min(f.w, f.h) >= 4:                                     # a ragged edge, so it isn't a painted bar
        for y in range(f.h):
            for x in range(f.w):
                if f.across(y, x) in (0, (f.w if f.along_v else f.h) - 1) and noise(f.seed, x, y, 2) > 520:
                    f.set(y, x, "shell", MID["shell"] - 1)


def paint_rings(f):
    for y in range(f.h):
        for x in range(f.w):
            r, _ = coil(f.p[y, x])
            f.lv[y, x] += 1 if int(r) % 3 == 0 else 0


def paint_flesh(f):
    for y in range(f.h):
        for x in range(f.w):
            p = f.p[y, x]
            b = smooth(21, p[0] + p[2] * 0.7, p[1] + p[2] * 0.3, 4)
            f.lv[y, x] += -1 if b < 0.34 else (1 if b > 0.76 else 0)
            if noise(f.seed + 4, x, y, 1) > 985:
                f.lv[y, x] = len(RAMP[f.cube.mat]) - 1       # a wet glint
    form(f)


def paint_hood(f):
    for y in range(f.h):
        for x in range(f.w):
            f.lv[y, x] += -1 if (x + noise(f.seed, 0, y // 6, 1) % 3) % 7 == 0 else 0     # leathery folds
    mottle(f, 120, 900, 2)
    form(f)


def paint_tentacle(f):
    for y in range(f.h):
        for x in range(f.w):
            t = f.t[y, x]
            f.lv[y, x] += -1 if int(t) % 4 == 0 else 0
            if t < f.length * 0.25:
                f.lv[y, x] += 0
    mottle(f, 130, 880, 2)
    if f.face == "north" and f.w >= 3:                         # pale suckers down the inner side
        for y in range(1, f.h - 1, 3):
            f.set(y, f.w // 2, "sucker", 2)
            if f.w >= 4:
                f.set(y, f.w // 2 - 1, "sucker", 1)


def paint_eye(f):
    if abs(f.n[0]) < 0.7:
        return
    c = np.array(((f.cube.group.origin[0]), f.cube.group.origin[1], f.cube.group.origin[2]))
    for y in range(f.h):
        for x in range(f.w):
            d = f.p[y, x] - c
            r, a = math.hypot(d[1], d[2]) / 4.4, math.atan2(d[1], d[2])
            f.lv[y, x] = (MID["naut_eye"] + (1 if r < 0.6 else 0) - (1 if r > 0.85 else 0)
                          + (1 if noise(17, int((a + 4) * 5), 0, 1) > 620 else 0))


# ---- the ship ----------------------------------------------------------------------------------------------------------

def paint_plank(f):
    """A clinker strake: grain, tar along its lower lap, rivets along the top weeping rust, weed near the waterline."""
    grain(f)
    big = f.side and max(f.w, f.h) >= 10 and min(f.w, f.h) >= 4
    if not big:
        form(f)
        return
    for x in range(f.w):
        f.set(f.h - 1, x, "tar", MID["tar"])
        if noise(f.seed, x // 3, 5, 1) > 400:
            f.set(f.h - 2, x, "tar", MID["tar"] + 1)
    f.lv[0, :] += 1
    for x in range(2 + noise(f.seed, 2, 2, 1) % 3, f.w - 1, 6):
        f.set(1, x, "iron", MID["iron"] + 2)
        if noise(f.seed, x, 9, 1) > 480:
            for k in range(2, min(f.h - 2, 2 + noise(f.seed, x, 11, 1) % 4)):
                f.set(k, x, "rust", MID["rust"] - (k > 3))
    for y in range(f.h):
        for x in range(f.w):
            py = f.p[y, x, 1]
            if py < 26 and smooth(41, f.p[y, x, 2] + abs(f.p[y, x, 0]), py, 4) > 0.2 + 0.75 * py / 26:
                f.set(y, x, "weed", MID["weed"] + (noise(f.seed, x, y, 2) > 700))


def paint_deck(f):
    grain(f)
    if f.face == "up":
        for y in range(f.h):
            for x in range(f.w):
                if x % 5 == 0:
                    f.set(y, x, "tar", MID["tar"])
                elif abs(x - f.w / 2) < 6:
                    f.lv[y, x] += 1                          # worn pale where he stands


def carved(f):
    """Carved scales on the dragon's neck and skull: overlapping rows cut into the wood; bare wood where it's worn."""
    grain(f, 120, 930)
    if min(f.w, f.h) >= 5 and f.n[1] > -0.5:
        for y in range(f.h):
            row = y // 4
            for x in range(f.w):
                u = (x + row * 3) % 6
                if y % 4 == 3 and u not in (0, 5):
                    f.lv[y, x] -= 2
                elif u == 0 and y % 4 >= 1:
                    f.lv[y, x] -= 2
                elif y % 4 == 0 and u in (2, 3):
                    f.lv[y, x] += 1
    form(f)


def paint_flaking(f):
    """Old paint, worn through to the wood in patches, a darker line at its edges."""
    zone = f.cube.mat
    mottle(f, 150, 860, 2)
    for y in range(f.h):
        for x in range(f.w):
            s = smooth(f.seed & 255, x, y, 3)
            if s < 0.32:
                f.set(y, x, "wood", MID["wood"] + (noise(f.seed, x, y, 1) > 700))
            elif s < 0.4:
                f.lv[y, x] = MID[zone] - 2
    if f.h >= 4:
        form(f) if zone == "paint_white" else None


SHIELDS = {}


def paint_shield(f, model):
    key = f.cube.name.split("_h")[0].split("_v")[0].split("_c")[0]
    if key not in SHIELDS:
        pts = [(np.array(c.frm) + np.array(c.to)) / 2 for c in model.cubes if c.name.startswith(key + "_")]
        SHIELDS[key] = np.mean(pts, 0)
    c = SHIELDS[key]
    if abs(f.n[0]) < 0.7:
        grain(f)
        f.zone[:, :] = "wood_dark"
        f.lv[:, :] = MID["wood_dark"]
        return
    other = "paint_white" if f.cube.mat == "paint_red" else "paint_red"
    for y in range(f.h):
        for x in range(f.w):
            d = f.p[y, x] - c
            r = math.hypot(d[1], d[2])
            zone = f.cube.mat if d[2] * (1 if abs(d[1]) < 0.1 else 1) > 0 else other
            s = smooth(f.seed & 255, f.p[y, x, 1], f.p[y, x, 2], 2.2)
            if r > 3.6:
                f.set(y, x, "wood_dark", MID["wood_dark"] + (noise(f.seed, x, y, 2) > 600))
            elif s < 0.3:
                f.set(y, x, "wood", MID["wood"] - 1 + (noise(f.seed, x, y, 2) > 500))
            else:
                f.set(y, x, zone, MID[zone] - (s < 0.38))


def paint_iron(f):
    mottle(f, 200, 800, 2)
    form(f)
    for y in range(f.h):
        for x in range(f.w):
            s = smooth(f.seed & 511, x, y, 3)
            if s > 0.87:
                f.set(y, x, "rust", MID["rust"] + (noise(f.seed, x, y, 2) > 650))
    n = f.cube.name
    if n.startswith("helm_band") and f.side and f.w >= 8:
        for x in range(2, f.w - 1, 4):                        # rivets round the band
            f.set(f.h // 2, x, "iron_light", MID["iron_light"])
    if n.startswith("spear_blade") and f.w >= 3 and f.h >= 3:
        f.lv[:, :] = MID["iron"] + 1
        f.lv[(f.h // 2 if not f.along_v else 0):, :] += 0
        mid = f.h // 2 if f.w > f.h else None
        if mid is not None:
            f.lv[mid, :] += 2


def paint_rope(f):
    for y in range(f.h):
        for x in range(f.w):
            f.lv[y, x] += 1 if (x + y) % 3 == 0 else (-1 if (x + y) % 3 == 2 else 0)


def paint_net(f):
    for y in range(f.h):
        for x in range(f.w):
            if x % 4 and y % 4:
                f.alpha[y, x] = 0
            elif x % 4 == 0 and y % 4 == 0:
                f.lv[y, x] += 1                               # the knots


def paint_tooth(f):
    for y in range(f.h):
        for x in range(f.w):
            f.lv[y, x] += -1 if y < f.h * 0.3 else 0
    mottle(f, 80, 940, 2)


def paint_glow(f):
    for y in range(f.h):
        for x in range(f.w):
            dy = abs(y - (f.h - 1) / 2) / max(1, f.h / 2)
            dx = abs(x - (f.w - 1) / 2) / max(1, f.w / 2)
            d = max(dx, dy)
            f.lv[y, x] = 4 if d < 0.34 else (3 if d < 0.67 else 2)


# ---- the Viking --------------------------------------------------------------------------------------------------------

UV_SKIN = {"north": ("front", 8, 8), "east": ("right", 0, 8), "west": ("left", 16, 8), "south": ("back", 24, 8),
           "up": (None, 8, 0), "down": (None, 16, 0)}


def paint_head(face):
    """The real zombie skin, with the crust and stain grown in under the barnacles (F3's patches), at 3 pixels per
    texel. The eyes and the mouth stay bare."""
    name, u, v = UV_SKIN[face]
    px = np.array(Image.fromarray(s4.SKIN[v:v + 8, u:u + 8].astype("uint8"), "RGBA").resize((24, 24), Image.NEAREST)).astype(float)
    patches = [(c, r, reach) for fc, c, r, reach, _ in tf2.GROWTH["F3"] if fc == name]
    clear = tf2.CLEAR.get(name, ())
    seed = zlib.crc32(face.encode())
    for sy in range(24):
        for sx in range(24):
            c, r = (sx - 1) / 3, (sy - 1) / 3
            if not patches or any(math.hypot(c - a, r - b) < q for a, b, q in clear):
                continue
            hit = max(1 - math.hypot(c - pc, r - pr) / (reach + 0.9) for pc, pr, reach in patches)
            hit += (smooth(seed & 255, sx, sy, 2.6) - 0.5) * 0.55
            if hit > 0.42:
                tone = np.array((154, 152, 128) if noise(seed, sx, sy, 2) > 620 else (132, 132, 110), float)
            elif hit > 0.14:
                tone = np.array((86, 94, 76) if noise(seed + 1, sx, sy, 2) > 400 else (70, 82, 64), float)
            else:
                continue
            px[sy, sx, :3] += (tone - px[sy, sx, :3]) * 0.82
    return px.astype("uint8")


def paint_skin(f):
    mottle(f, 150, 850, 2)
    if f.h >= 5 and f.w >= 4:                                 # zombie blotches, in blocks as on vanilla's skin
        for y in range(f.h):
            for x in range(f.w):
                f.lv[y, x] += 1 if noise(f.seed + 3, x // 3, y // 3, 1) > 700 else (-1 if noise(f.seed + 4, x // 3, y // 3, 1) < 260 else 0)
    form(f)


def paint_leather(f):
    n = f.cube.name
    mottle(f, 140, 870, 2)
    if n.startswith("wrap_"):                                 # leg wraps: bands winding down the shin
        for y in range(f.h):
            for x in range(f.w):
                f.lv[y, x] += 1 if (y + x // 2) % 4 == 0 else (-1 if (y + x // 2) % 4 == 3 else 0)
    elif n.startswith("bracer_"):                             # a bracer: a strap every few texels with a stud
        for y in range(1, f.h - 1, 4):
            f.lv[y, :] -= 2
            if f.w >= 3:
                f.set(y, f.w // 2, "iron_light", MID["iron_light"] + 1)
    elif n in ("chest", "tunic_hips") and f.face in ("north", "south"):
        for y in range(f.h):                                  # creases, then a stitched seam down one side
            for x in range(f.w):
                if (x + noise(f.seed, 1, y // 5, 1) % 4) % 9 == 0:
                    f.lv[y, x] -= 2
        for y in range(1, f.h - 1, 3):
            f.set(y, 2, "stitch", 1)
        for y in range(f.h):                                  # worn, scuffed patches
            for x in range(f.w):
                if smooth(f.seed & 255, x, y, 4) > 0.74:
                    f.lv[y, x] += 1
                elif smooth((f.seed & 255) + 9, x, y, 3) > 0.84 and 2 < y < f.h - 2 and 3 < x < f.w - 2:
                    f.set(y, x, "leather_dark", 0)            # small tears, dark inside
    elif n == "buckle":
        pass
    form(f)
    if n.startswith(("hem", "cloak")) and f.side:             # torn: a ragged lower edge
        for x in range(f.w):
            cut = 1 + noise(f.seed, x // 2, 3, 1) % (3 if f.h > 6 else 2)
            f.alpha[f.h - cut:, x] = 0
        if n == "cloak" and f.h > 8:                          # and a few holes through it
            for y in range(2, f.h - 3):
                for x in range(1, f.w - 1):
                    if smooth(f.seed & 255, x, y, 3) > 0.84:
                        f.alpha[y, x] = 0


def paint_fur(f):
    for y in range(f.h):
        for x in range(f.w):
            r = noise(f.seed, x, y // 3, 1)
            f.lv[y, x] += -2 if r < 200 else (2 if r > 780 else 0)
    if f.side:
        for x in range(f.w):                                  # tufts at the lower edge
            if noise(f.seed, x, 4, 1) > 500:
                f.lv[f.h - 1, x] -= 2


def paint_horn(f):
    n = f.cube.name.split("_")
    i = int(n[-1]) if n[-1].isdigit() else 0
    f.lv[:, :] += 1 if i > 5 else (-1 if i < 2 else 0)
    for y in range(f.h):
        for x in range(f.w):
            if i < 8 and int(f.t[y, x] + i * 3) % 4 == 0:
                f.lv[y, x] -= 1                               # the rings of the horn
    if i >= 10:
        f.lv[:, :] -= 3                                       # dark, polished tips


def paint_barnacle(f):
    """Barely shaded: at this size a drawn outline turns them into squares inside squares."""
    mottle(f, 240, 800, 1)
    if f.n[1] < -0.5:
        f.lv -= 1


def paint(model, i, face, w, h, solids):
    cube = model.cubes[i]
    n, m = cube.name, cube.mat
    if n == "head":
        return paint_head(face)
    f = Face(cube, face, w, h)
    names = []
    g = cube.group
    while g is not None:
        names.append(g.name)
        g = g.parent
    if m == "shell":
        paint_shell(f)
    elif m == "stripe":
        paint_stripe(f)
    elif m == "shell_in":
        paint_rings(f)
    elif m == "body":
        paint_flesh(f)
    elif m == "hood":
        paint_lid = n.startswith("lidplate")
        paint_hood(f) if not paint_lid else form(f)
    elif m == "tentacle":
        paint_tentacle(f)
    elif m == "naut_eye":
        paint_eye(f)
    elif m in ("wood", "wood_dark", "paint_red", "paint_white") and n.startswith("shield_"):
        paint_shield(f, model) if not n.startswith("shield_boss") else paint_iron(f)
    elif m in ("wood", "wood_dark"):
        if n == "deck":
            paint_deck(f)
        elif n.startswith("strake"):
            paint_plank(f)
        elif any(x.startswith(("figure",)) for x in names):
            carved(f)
        else:
            grain(f)
            form(f)
    elif m in ("paint_red", "paint_white"):
        paint_flaking(f)
    elif m in ("iron", "iron_light"):
        paint_iron(f)
    elif m == "rope":
        paint_rope(f)
    elif m == "net":
        paint_net(f)
    elif m == "tooth":
        paint_tooth(f)
    elif m == "glow":
        paint_glow(f)
    elif m in ("skin", "skin_dark"):
        paint_skin(f)
    elif m in ("leather", "leather_dark"):
        paint_leather(f)
    elif m == "fur":
        paint_fur(f)
    elif m == "horn":
        paint_horn(f)
    elif m.startswith("b_"):
        paint_barnacle(f)
    if m not in GLOWING and m != "net" and not m.startswith("b_") and not (n.startswith(("flank_", "dome_", "whorl_", "callus_")) and abs(f.n[0]) > 0.7):
        ao = b5.occlusion(model, i, face, w, h, solids)
        f.lv = f.lv - (ao >= 0.3) - (ao >= 0.55)
    out = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            r = RAMP[f.zone[y, x]]
            out[y, x, :3] = r[int(np.clip(f.lv[y, x], 0, len(r) - 1))]
            out[y, x, 3] = 255 if f.alpha[y, x] > 127 else 0
    return out


def model_pass(kind, name, hitbox):
    model = s3.build(kind, "idle")
    model.name = name
    keys = s4.island_keys(model)
    b4.SIZE = s4.SIZE
    positions, used, _ = b4.pack({k: (k[2], k[3]) for k in keys.values()})
    height = 16
    while height < used:
        height *= 2
    owner = {}
    for (i, fc), key in sorted(keys.items(), key=lambda kv: (kv[0][0], FACES.index(kv[0][1]))):
        owner.setdefault(key, (i, fc))
    solids = b5.solids_of(model)
    atlas = Image.new("RGBA", (s4.SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        i, fc = owner[key]
        patch = Image.fromarray(paint(model, i, fc, w, h, solids), "RGBA")
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    path = OUT / f"{name}.png"
    atlas.save(path)
    atlas.resize((atlas.width * 2, atlas.height * 2), Image.NEAREST).save(OUT / f"{name}_preview.png")
    bb, _ = a4.textured_bbmodel(model, keys, positions, path, s4.SIZE, height, hitbox, s3.pose_table(kind).items())
    p = OUT / f"{name}.bbmodel"
    p.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(p, s3.SERVER_MODELS / p.name)
    return {c.name: bb["elements"][i]["faces"] for i, c in enumerate(model.cubes)}, height


VIEWS = [
    {"name": "hero", "location": (9, 13, 7), "target": (0, 0, 2.9), "scale": 10.5, "player": True},
    {"name": "side", "location": (18, 0, 3), "target": (0, 0, 3), "scale": 9.5, "player": False},
    {"name": "back", "location": (8, -14, 6), "target": (0, -1, 2.4), "scale": 9.5, "player": False},
    {"name": "far", "location": (9, 13, 5), "target": (0, 0, 2.9), "scale": 27.0, "player": True},
    {"name": "viking", "location": (3, 12, 5.6), "target": (0, 1.4, 4.2), "scale": 3.6, "player": False},
    {"name": "head", "location": (1.2, 12, 5.3), "target": (0, 1.5, 4.95), "scale": 1.5, "player": False},
    {"name": "bow", "location": (5, 11, 3.2), "target": (0, 2.0, 2.2), "scale": 4.4, "player": False},
    {"name": "dragon", "location": (-4, 12, 4.6), "target": (0, 3.2, 3.9), "scale": 3.2, "player": False},
    {"name": "shell", "location": (12, -2, 3), "target": (0, -0.4, 1.9), "scale": 4.2, "player": False},
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s4.OUT, s4.VIEWS = OUT, VIEWS
    mf, mh = model_pass("mount", s3.MOUNT_ID, s3.MOUNT_HITBOX)
    rf, rh = model_pass("rider", s3.RIDER_ID, s3.RIDER_HITBOX)
    s4.together(mf, rf, mh, rh, False)
    a5.grid([OUT / "colour" / f"{v['name']}.png" for v in VIEWS], [v["name"] for v in VIEWS], OUT / "sheet.png",
            "The Tidebreaker - painted (session 5)")
    print("painted", mh, rh)


if __name__ == "__main__":
    main()
