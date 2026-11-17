"""The Abyssal Warden redesign, session 5: texture painting (plan: docs/art/bosses/abyssal_warden/overhaul/plan.md).

Paints session 4's layout (one 512 x 512 atlas, the same islands). Every ramp runs from a cool dark through the zone's
colour to a warm light. The painting carries form only, with no painted light direction: crease shading (ambient
occlusion) is baked from the real geometry.
- **The hull** is painted from where each texel sits on the sphere, not panel by panel, so the weathering runs on
  across the panels: bright copper on the crown, then exposed, then dark weathered copper, then the pale verdigris
  crust round the open neck. The edges between the stages are ragged; tongues of verdigris climb up from the neck as
  if the sea crept up him. Every panel has a dark seam round it and a row of rivets along its top and bottom; some
  rivets weep a verdigris streak down the panel. The crown has a soft shine.
- **The brass:** polished, a lit upper edge and a shaded lower one, tarnish in clusters and a few green spots.
- **The glass:** almost clear sea glass, thicker and greener at its rim, with a few scratches.
- **The eye:** the yellowed sclera with red veins branching in from its edge (painted, as the user asked), darker
  towards the rim; the wet flesh round it; the iris as a glowing gradient with fibres round the slit, never flat.
- **The creature:** mottled sea-green skin, darker blotches and pale flecks, veins along the arm, ringed tendrils with
  suckers, knuckle creases on the fingers, creases across the palm; barnacles with their plates and dark openings;
  glossy claws.
- **The kelp:** blades with a lit midrib, ragged ends going yellow-brown; the hose ribbed rubber; the valves' stems
  threaded.

Run from the repository root: python tools/art/bosses/warden_s5.py
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
from bosses import archevoker_s4 as a4, brood_s4 as b4, brood_s5 as b5, coven_s5 as c5  # noqa: E402
from bosses import volley_crone_s5 as v5  # noqa: E402
from bosses import warden_s2 as s2, warden_s3 as s3, warden_s4 as s4  # noqa: E402

OUT = ROOT / "docs/art/bosses/abyssal_warden/overhaul/s5_paint"
noise = v5.noise
mk = c5.make_ramp
C = s2.C
R = s2.R

RAMP = {
    "copper": mk((62, 26, 42), (205, 115, 83), (255, 200, 156), 9),
    "copper_exposed": mk((44, 32, 42), (135, 101, 83), (200, 162, 130), 9),
    "copper_weathered": mk((14, 26, 32), (57, 82, 59), (112, 142, 104), 9),
    "verdigris": mk((22, 58, 66), (68, 136, 116), (156, 218, 190), 9),
    "copper_dark": mk((32, 14, 20), (112, 58, 38), (172, 108, 76), 7),
    "rivet": mk((88, 56, 40), (222, 170, 112), (255, 230, 184), 7),
    "brass": mk((52, 38, 30), (190, 154, 88), (246, 226, 168), 9),
    "glass": mk((40, 92, 112), (156, 222, 232), (234, 252, 255), 7),
    "sclera": mk((92, 76, 70), (179, 171, 150), (238, 232, 212), 9),
    "vein": [(66, 12, 22), (112, 26, 34), (150, 46, 48), (186, 76, 72), (204, 110, 100)],
    "flesh_wet": mk((58, 30, 44), (150, 100, 104), (216, 174, 170), 7),
    "iris": [(12, 74, 92), (22, 128, 140), (44, 180, 186), (80, 232, 214), (150, 250, 232), (210, 255, 246)],
    "iris_dark": [(6, 36, 50), (12, 70, 88), (24, 128, 132), (44, 170, 168), (70, 206, 196)],
    "pupil": [(3, 5, 9), (10, 14, 20), (16, 34, 42), (24, 70, 80)],
    "glint": [(214, 246, 250), (250, 252, 255), (255, 255, 255)],
    "flesh": mk((20, 34, 42), (104, 130, 112), (172, 192, 160), 9),
    "flesh_dark": mk((10, 18, 26), (58, 78, 70), (112, 132, 112), 9),
    "barnacle": mk((86, 82, 86), (204, 198, 178), (246, 242, 228), 7),
    "barnacle_old": mk((66, 66, 68), (148, 144, 128), (202, 198, 180), 7),
    "nail": mk((8, 10, 14), (34, 38, 36), (96, 104, 96), 7),
    "kelp": mk((18, 42, 24), (112, 176, 63), (198, 224, 124), 9),
    "kelp_tip": mk((54, 44, 22), (150, 128, 52), (214, 194, 104), 7),
    "hose": mk((16, 12, 16), (70, 56, 44), (126, 106, 84), 7),
    "shard": mk((60, 120, 136), (170, 226, 232), (240, 254, 255), 7),
    "spray": [(170, 214, 228), (206, 236, 244), (226, 246, 250), (244, 252, 255), (255, 255, 255)],
}
RAMP["hose_band"] = RAMP["brass"]
RAMP["sclera_blood"] = mk((96, 52, 58), (188, 150, 134), (238, 210, 194), 9)     # session 6: bloodshot, below half
MID = {k: (len(v) - 1) // 2 for k, v in RAMP.items()}
MID.update({"iris": 3, "iris_dark": 2, "pupil": 1, "glint": 1, "spray": 2, "vein": 2})
GLOWING = s4.GLOWING
HULL = ("copper", "copper_exposed", "copper_weathered", "verdigris")


class Face:
    """One face being painted: levels, the ramp per texel, the alpha, and where its texels are on the helmet."""

    def __init__(self, model, cube, face, w, h):
        self.cube, self.face, self.w, self.h = cube, face, w, h
        self.lv = np.full((h, w), MID.get(cube.mat, 4), int)
        self.zone = np.full((h, w), cube.mat, object)
        self.alpha = None
        pts, n, tu, tv = v5.texel_points(cube, face, w, h)
        m = np.linalg.inv(BODY) @ v5.cube_matrix(cube)       # the body's own space: the bow taken out
        flat = pts.reshape(-1, 3)
        self.p = (m @ np.c_[flat, np.ones(len(flat))].T).T[:, :3].reshape(h, w, 3)
        self.n = m[:3, :3] @ n
        self.seed = zlib.crc32(f"{cube.name}/{face}".encode())

    def set(self, y, x, zone, level):
        if 0 <= y < self.h and 0 <= x < self.w:
            self.zone[y, x], self.lv[y, x] = zone, level


BODY = np.eye(4)


def mottle(f, lo=170, hi=830, cell=2, seed=0):
    for y in range(f.h):
        for x in range(f.w):
            r = noise(f.seed + seed, x, y, cell)
            f.lv[y, x] += -1 if r < lo else (1 if r > hi else 0)


def form(f):
    """Form, not light: tops a step lighter, undersides darker, a face's upper edge lit and its lower edge shaded."""
    if f.n[1] > 0.7:
        f.lv += 1
    elif f.n[1] < -0.7:
        f.lv -= 2
    elif f.h >= 3:
        f.lv[0, :] += 1
        f.lv[f.h - 1, :] -= 1


def smooth_noise(seed, u, v, scale):
    """Value noise in 0..1, smooth between cells (for the weathering's ragged edges)."""
    x, y = u / scale, v / scale
    x0, y0 = math.floor(x), math.floor(y)
    fx, fy = x - x0, y - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)

    def at(i, j):
        return noise(seed, i, j, 1) / 999

    a = at(x0, y0) * (1 - fx) + at(x0 + 1, y0) * fx
    b = at(x0, y0 + 1) * (1 - fx) + at(x0 + 1, y0 + 1) * fx
    return a * (1 - fy) + b * fy


# ---- the hull ---------------------------------------------------------------------------------------------------------

RNG = np.random.default_rng(29)
TONGUES = [(float(RNG.uniform(-math.pi, math.pi)), float(RNG.uniform(0.15, 0.55)), float(RNG.uniform(2.0, 4.5)))
           for _ in range(16)]                               # verdigris climbing from the neck: (azimuth, top, width)


def weathering(p):
    """How weathered the copper is at a point on the helmet: 0 new on the crown .. 3.x a verdigris crust at the neck."""
    d = p - C
    lat = float(np.clip(d[1] / R, -1, 1))
    az = math.atan2(d[0], -d[2])
    arc = az * R                                             # texels round the sphere at the equator
    rag = smooth_noise(11, arc, d[1], 7) * 0.9 + smooth_noise(12, arc, d[1], 2.5) * 0.35
    w = 0.95 - lat * 2.2 + rag * 0.8
    ring = R * max(0.2, math.cos(math.asin(lat)))
    for a0, top, width in TONGUES:
        da = (az - a0 + math.pi) % (2 * math.pi) - math.pi
        off = abs(da) * ring
        if lat < top:
            k = (top - lat) / (top + 0.9)
            if off < width * (0.35 + k):
                w += 0.9 * (1 - off / (width * (0.35 + k) + 1e-6))
    return w


def stage(w):
    return HULL[int(np.clip(math.floor(w), 0, 3))]


def paint_hull(f):
    """The copper hull, from each texel's place on the sphere."""
    outward = float(np.dot(f.n, (f.p[f.h // 2, f.w // 2] - C) / np.linalg.norm(f.p[f.h // 2, f.w // 2] - C))) > 0.6
    for y in range(f.h):
        for x in range(f.w):
            p = f.p[y, x]
            wv = weathering(p)
            z = stage(wv)
            lv = MID[z]
            frac = wv - math.floor(wv)
            if z != "verdigris" and frac > 0.82:
                lv -= 1                                      # the stage's edge darkens before it turns
            lat = (p[1] - C[1]) / R
            lv += 1 if lat > 0.55 else (-1 if lat < -0.35 else 0)     # the sphere's form: the crown, the underside
            if z == "copper" and lat > 0.62 and smooth_noise(5, p[0], p[2], 6) > 0.55:
                lv += 1                                      # the crown's shine
            r = noise(f.seed, x, y, 2)
            lv += -1 if r < 120 else (1 if r > 900 else 0)
            if z == "verdigris" and noise(f.seed + 3, x, y, 1) > 860:
                lv += 1                                      # the crust's pale grains
            f.zone[y, x], f.lv[y, x] = z, lv
    if not outward:
        f.lv -= 1                                            # a panel's edges, inside the seams
        return
    name = f.cube.name
    edges = {"l": True, "r": True, "t": True, "b": True}
    if "_tile" in name:                                      # a tile by an opening: only its real panel edges
        u, v = int(name[-2]), int(name[-1])
        edges = {"l": u == 0, "r": u == s3.TILES - 1, "t": v == s3.TILES - 1, "b": v == 0}
    if name.startswith("hull_cap"):
        edges = {"l": False, "r": False, "t": False, "b": False}
    w, h = f.w, f.h
    for y in range(h):                                       # the seams
        for x in range(w):
            if (edges["l"] and x == 0) or (edges["r"] and x == w - 1) or (edges["t"] and y == 0) or \
                    (edges["b"] and y == h - 1):
                f.lv[y, x] -= 2
    for row, side in ((1, "t"),):                            # a row of rivets along the top, some weeping a streak
        if not edges[side] or h < 6:
            continue
        for x in range(2 + noise(f.seed, 3, 3, 1) % 2, w - 2, 5):
            if edges["l"] is False and x < 2:
                continue
            z = f.zone[row, x]
            f.set(row, x, "rivet", MID["rivet"] + 1)
            f.set(row + 1, x, z, f.lv[min(h - 1, row + 1), x] - 1)          # the rivet's head sits proud
            if side == "t" and noise(f.seed, x, 31, 1) > 720:
                length = 3 + noise(f.seed, x, 37, 1) % 7
                for k in range(2, 2 + length):
                    yy = row + k
                    if yy >= h - 1:
                        break
                    taper = k > length * 0.6
                    zz = "verdigris" if f.zone[yy, x] in ("copper", "copper_exposed") else "verdigris"
                    f.set(yy, x, zz, MID["verdigris"] - (1 if taper else 0))
                    if not taper and noise(f.seed, x, yy, 1) > 500 and x + 1 < w - 1:
                        f.set(yy, x + 1, f.zone[yy, x + 1], f.lv[yy, x + 1] - 1)


# ---- fittings ---------------------------------------------------------------------------------------------------------

def paint_brass(f):
    mottle(f, 60, 970, 3)
    form(f)
    for y in range(f.h):
        for x in range(f.w):
            r = noise(f.seed + 7, x, y, 2)
            if r < 45:
                f.lv[y, x] -= 1                              # tarnish
            elif r > 975 and f.w >= 3 and f.h >= 3:
                f.set(y, x, "verdigris", MID["verdigris"])   # a spot of green
    if f.cube.name.startswith(("hose_band",)) and f.w >= 3:
        for x in range(0, f.w, 2):
            f.lv[:, x] -= 1                                  # the band's ribs


def paint_rivet(f):
    f.lv[:, :] = MID["rivet"]
    if f.w >= 2 and f.h >= 2:
        f.lv[0, :] += 1
        f.lv[:, 0] += 1
        f.lv[f.h - 1, :] -= 2
        f.lv[:, f.w - 1] -= 1
    form(f)


def paint_stem(f):
    """A valve's stem: threaded, rings across its length."""
    lo, hi = np.array(f.cube.frm), np.array(f.cube.to)
    axis = int(np.argmax(hi - lo))
    pts, _, _, _ = v5.texel_points(f.cube, f.face, f.w, f.h)
    for y in range(f.h):
        for x in range(f.w):
            t = pts[y, x, axis] - lo[axis]
            f.lv[y, x] += 1 if int(t) % 2 == 0 else -1
    mottle(f, 150, 990, 2)


# ---- the window and the eye -------------------------------------------------------------------------------------------

CENTRES = {}


def disc_centre(model, prefix):
    if prefix not in CENTRES:
        pts = []
        for c in model.cubes:
            if c.name.startswith(prefix):
                m = np.linalg.inv(BODY) @ v5.cube_matrix(c)
                ctr = (np.array(c.frm) + np.array(c.to)) / 2
                pts.append((m @ np.array([*ctr, 1.0]))[:3])
        CENTRES[prefix] = np.mean(pts, 0)
    return CENTRES[prefix]


def paint_glass(f, model):
    """Clear glass with an opaque rim, scratches and a glint. Every texel is fully clear or fully opaque: in game a
    half-clear texel hides whatever is drawn behind it after it (the eye vanished in some frames)."""
    prefix = f.cube.name.split("_glass")[0] + "_glass"
    ctr = disc_centre(model, prefix)
    rw = 16 if prefix == "window_glass" else 8
    f.alpha = np.zeros((f.h, f.w), int)
    for y in range(f.h):
        for x in range(f.w):
            d = f.p[y, x] - ctr
            r = float(np.linalg.norm(d)) / rw
            lv, a = MID["glass"], 0
            if r > 0.9:
                lv, a = lv - 1, 255                          # the thick rim of the glass, greener
            elif r > 0.82 and (x + y) % 2 == 0:
                lv, a = lv - 1, 255                          # the rim thinning into clear glass
            u, v = d[0] + d[2], d[1]
            if abs((u * 0.7 - v) % 9 - 4.5) < 0.5 and 0.2 < r < 0.8 and noise(f.seed, int(u), 3, 3) > 450 \
                    and noise(f.seed + 7, x, y, 1) > 520:
                lv, a = lv + 1, 255                          # scratches, broken and faint
            if abs(u + v * 0.35 - 6) < 0.6 and r < 0.5 and v > 0 and (x + y) % 2 == 0:
                lv, a = lv + 2, 255                          # the glint, broken so the eye shows between
            f.lv[y, x], f.alpha[y, x] = lv, a
    if f.face not in ("north", "south") and f.n[2] > -0.5:
        f.alpha[:, :] = 255                                  # the glass's edge, seen side on


VEINS = {}
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def vein_cells(rw=16, seed=41, count=8, lengths=(8, 13), forks=(0.11, 0.06), inner=0.44):
    """Red veins branching in from the sclera's edge, as cells in the eye's plane (x, y relative to its centre).
    Session 6's bloodshot eye asks for more, longer vessels that fork more often and reach nearer the iris."""
    args = (rw, seed, count, lengths, forks, inner)
    if args not in VEINS:
        rng = np.random.default_rng(seed)
        cells = {}

        def walk(x, y, a, length, width, depth):
            """A vessel winding inwards: it keeps turning a little the same way, then the other (never straight),
            forks once or twice, and thins and pales towards its tip."""
            bend = float(rng.choice([-1, 1]) * rng.uniform(0.12, 0.22))      # every vessel starts curving
            for step in range(length * 2):                     # half-texel steps: no gaps on the bends
                bend = float(np.clip(bend + rng.uniform(-0.09, 0.09), -0.26, 0.26))
                a += bend * 0.5
                x += math.cos(a) * 0.5
                y += math.sin(a) * 0.5
                if math.hypot(x, y) < rw * inner:              # under the iris: hidden anyway
                    return
                t = step / (length * 2)
                tone = 0 if t < 0.25 and depth == 0 else (1 if t < 0.5 else (2 if t < 0.8 else 3))
                key = (round(x), round(y))
                cells[key] = min(cells.get(key, 9), tone)
                if width > 1 and t < 0.3:
                    side = (round(x - math.sin(a)), round(y + math.cos(a)))
                    cells[side] = min(cells.get(side, 9), tone + 1)
                if depth < 2 and step > 4 and step % 2 == 0 and rng.random() < forks[min(depth, 1)]:
                    walk(x, y, a + float(rng.choice([-1, 1]) * rng.uniform(0.55, 1.05)),
                         max(3, int(length * (1 - t) * 0.7)), 1, depth + 1)

        for i in range(count):
            a = math.radians(i * 360 / count + float(rng.uniform(-16, 16)))
            r0 = rw * 0.99
            walk(math.cos(a) * r0, math.sin(a) * r0, a + math.pi + float(rng.uniform(-0.5, 0.5)),
                 int(rng.integers(*lengths)), 2 if i % 2 == 0 else 1, 0)
        VEINS[args] = cells
    return VEINS[args]


BLOODSHOT = dict(seed=43, count=13, lengths=(11, 17), forks=(0.16, 0.09), inner=0.4)


def paint_sclera(f, model):
    """The yellowed white. The bloodshot copy (session 6's `sclera_blood`, shown below half) is pinker, with more
    vessels, longer and thicker, and a flushed rim."""
    blood = f.cube.name.startswith("sclera_blood")
    ctr = disc_centre(model, "sclera")
    cells = vein_cells(**BLOODSHOT) if blood else vein_cells()
    zone = "sclera_blood" if blood else "sclera"
    f.zone[:, :] = zone
    for y in range(f.h):
        for x in range(f.w):
            d = f.p[y, x] - ctr
            r = math.hypot(d[0], d[1]) / 16
            lv = MID[zone] + (1 if r < 0.55 else 0) - (1 if r > 0.78 else 0) - (1 if r > 0.92 else 0)
            if noise(f.seed, x, y, 2) < 140:
                lv -= 1                                      # yellowed blotches
            f.lv[y, x] = lv
            key = (round(d[0]), round(d[1]))
            if f.face == "north" and key in cells:
                f.set(y, x, "vein", cells[key])
            elif blood and f.face == "north" and r > 0.84 and noise(f.seed + 3, x // 2, y // 2, 1) > 420:
                f.set(y, x, "vein", 4 if r < 0.92 else 3)   # the flushed rim, in 2x2 clusters
    if f.face == "north":                                    # wet glints
        for y in range(f.h):
            for x in range(f.w):
                if noise(f.seed + 5, x, y, 1) > 992 and f.zone[y, x] == zone:
                    f.lv[y, x] = len(RAMP[zone]) - 1


def paint_iris(f, model):
    """The glowing iris: brightest in a ring round the slit, fibres running out from it, darker at its rim."""
    ctr = disc_centre(model, "iris_h")
    for y in range(f.h):
        for x in range(f.w):
            d = f.p[y, x] - ctr
            r = math.hypot(d[0], d[1]) / 8
            a = math.atan2(d[1], d[0])
            if f.cube.mat == "iris_dark":
                lv = 2 + (1 if noise(f.seed, int((a + 4) * 4), 0, 1) > 600 else 0) - (1 if r > 0.6 else 0)
            else:
                lv = 4 if r < 0.62 else (3 if r < 0.86 else 2)
                if noise(17, int((a + 4) * 5), 0, 1) > 640:  # fibres
                    lv += 1
                if r > 0.95:
                    lv -= 1
            f.lv[y, x] = lv


def paint_pupil(f):
    f.lv[:, :] = 1
    if f.w >= 2:
        f.lv[:, 0] = 2
        f.lv[:, f.w - 1] = 2
    f.lv[f.h // 2 - 2:f.h // 2 + 2, :] = 0


def paint_wet(f):
    mottle(f, 160, 860, 2)
    form(f)
    for y in range(f.h):
        for x in range(f.w):
            if noise(f.seed + 9, x, y, 1) > 985:
                f.lv[y, x] = len(RAMP["flesh_wet"]) - 1      # a wet glint


# ---- the creature ------------------------------------------------------------------------------------------------------

def paint_flesh(f):
    """Mottled sea-green skin: darker blotches, pale flecks; the arm's veins; ringed tendrils with suckers; the hand's
    creases."""
    n = f.cube.name
    for y in range(f.h):
        for x in range(f.w):
            p = f.p[y, x]
            b = smooth_noise(21, p[0] + p[2] * 0.7, p[1] + p[2] * 0.3, 4)
            f.lv[y, x] += -1 if b < 0.32 else (1 if b > 0.78 else 0)
            if noise(f.seed, x, y, 1) > 965:
                f.lv[y, x] += 1                              # pale flecks
    form(f)
    lo, hi = np.array(f.cube.frm), np.array(f.cube.to)
    axis = int(np.argmax(hi - lo))
    pts, _, _, _ = v5.texel_points(f.cube, f.face, f.w, f.h)
    t = pts[..., axis] - lo[axis]
    across = [i for i in range(3) if i != axis]
    if n.startswith(("hand_upper", "hand_fore")) and hi[axis] - lo[axis] > 10:
        for y in range(f.h):                                 # swollen veins along the arm, wavering
            for x in range(f.w):
                s = pts[y, x, across[0]] + pts[y, x, across[1]]
                if abs((s + 2.2 * math.sin(t[y, x] / 4.5)) % 9 - 4.5) < 0.55:
                    f.lv[y, x] -= 2
    if n.startswith("tendril"):
        for y in range(f.h):
            for x in range(f.w):
                if int(t[y, x]) % 3 == 0:
                    f.lv[y, x] -= 1                          # rings
                if f.n[2] > 0.5 or f.n[0] > 0.5:             # suckers on the inner side
                    if int(t[y, x]) % 3 == 1 and f.w >= 3 and x == f.w // 2:
                        f.set(y, x, "barnacle_old", 2)
    if "_finger" in n or "_thumb" in n:
        for y in range(f.h):
            for x in range(f.w):
                if int(t[y, x]) % 6 in (0,):
                    f.lv[y, x] -= 1                          # knuckle creases
        if f.w >= 3:
            f.lv[:, 0] -= 1
            f.lv[:, f.w - 1] -= 1
    if n.endswith("_palm") and min(f.w, f.h) >= 10:
        for x in range(2, f.w - 2):                          # creases across the palm, curving
            for y0 in (int(f.h * 0.3 + abs(x - f.w / 2) * 0.25), int(f.h * 0.68 - abs(x - f.w / 2) * 0.2)):
                if 0 <= y0 < f.h:
                    f.lv[y0, x] -= 2
    if n.endswith("_knuckles"):
        for x in range(1, f.w - 1, 5):
            f.lv[:, x:x + 2] += 1


def paint_barnacle(f):
    """A barnacle: plates up its sides, its top a ring of plates round a dark opening."""
    if f.n[1] > 0.7:
        cy, cx = (f.h - 1) / 2, (f.w - 1) / 2
        for y in range(f.h):
            for x in range(f.w):
                d = max(abs(y - cy), abs(x - cx))
                f.lv[y, x] = MID[f.cube.mat] + (1 if d >= max(1, min(f.w, f.h) / 2 - 1) else 0)
                if d < 0.75 or (min(f.w, f.h) >= 4 and d < 1.25):
                    f.set(y, x, "pupil", 1)                  # the opening
    else:
        for y in range(f.h):
            for x in range(f.w):
                f.lv[y, x] += 1 if x % 2 == 0 else -1         # the plates
        f.lv[f.h - 1, :] -= 1
        if f.n[1] < -0.7:
            f.lv -= 2


def paint_nail(f):
    lo, hi = np.array(f.cube.frm), np.array(f.cube.to)
    axis = int(np.argmax(hi - lo))
    pts, _, _, _ = v5.texel_points(f.cube, f.face, f.w, f.h)
    t = (pts[..., axis] - lo[axis]) / max(1e-6, hi[axis] - lo[axis])
    f.lv += (t > 0.6).astype(int) + (t > 0.85).astype(int)
    if f.w >= 2:
        f.lv[:, 0] += 1


def paint_kelp(f):
    """A kelp blade: a lit midrib, darker edges, its lower end ragged and going yellow-brown; the bulbs round."""
    n = f.cube.name
    if n.endswith("_bulb"):
        mottle(f, 200, 800, 1)
        form(f)
        if f.w >= 2:
            f.lv[0, 0] += 2
        return
    f.alpha = np.full((f.h, f.w), 255, int)
    seg = int(n.split("_")[1]) if n.split("_")[1].isdigit() else 0
    for y in range(f.h):
        for x in range(f.w):
            if f.w >= 3 and x in (0, f.w - 1):
                f.lv[y, x] -= 1
            if f.w >= 4 and x == f.w // 2:
                f.lv[y, x] += 1                              # the midrib
            if noise(f.seed, x, y, 2) > 880:
                f.lv[y, x] -= 1
            down = y / max(1, f.h - 1)                        # row 0 is the top of the face
            if seg == 1 and down > 0.7:
                f.zone[y, x] = "kelp_tip"
                f.lv[y, x] = MID["kelp_tip"] + (1 if x == f.w // 2 else 0)
                if f.w >= 3 and x in (0, f.w - 1) and noise(f.seed, x, y, 1) > 420:
                    f.alpha[y, x] = 0                        # ragged
            if seg == 1 and y == f.h - 1 and noise(f.seed, x, 5, 1) > 380:
                f.alpha[y, x] = 0


def paint_hose(f):
    """Ribbed rubber: a rib every three texels across its length, a faint canvas weave."""
    lo, hi = np.array(f.cube.frm), np.array(f.cube.to)
    axis = int(np.argmax(hi - lo))
    pts, _, _, _ = v5.texel_points(f.cube, f.face, f.w, f.h)
    for y in range(f.h):
        for x in range(f.w):
            t = pts[y, x, axis] - lo[axis]
            if int(t) % 3 == 0:
                f.lv[y, x] += 1
            elif (x + y) % 4 == 0:
                f.lv[y, x] -= 1
    form(f)


def paint_see_through(f, alpha):
    f.alpha = np.full((f.h, f.w), alpha, int)
    lo, hi = np.array(f.cube.frm), np.array(f.cube.to)
    axis = int(np.argmax(hi - lo))
    pts, _, _, _ = v5.texel_points(f.cube, f.face, f.w, f.h)
    t = (pts[..., axis] - lo[axis]) / max(1e-6, hi[axis] - lo[axis])
    if f.cube.mat == "spray":                                # thick at the valve, thinning out, streaked
        for y in range(f.h):
            for x in range(f.w):
                k = int(f.cube.name.rsplit("_", 1)[-1]) if f.cube.name[-1].isdigit() else 0
                f.alpha[y, x] = int(alpha * (1.0 - 0.28 * k) * (0.6 + 0.4 * (noise(f.seed, x, y, 1) > 400)))
                f.lv[y, x] = 2 + (1 if noise(f.seed + 1, x, y // 2, 1) > 600 else 0) - (1 if t[y, x] > 0.7 else 0)
    else:                                                    # a shard: lit edges
        if f.w >= 2:
            f.lv[:, 0] += 2
            f.alpha[:, 0] = 220


def paint(model, cube, face, w, h, solids):
    f = Face(model, cube, face, w, h)
    m, n = cube.mat, cube.name
    if n.startswith("hull"):
        paint_hull(f)
    elif m in ("brass", "hose_band"):
        paint_brass(f)
    elif m == "rivet":
        paint_rivet(f)
    elif m == "copper_dark":
        paint_stem(f)
    elif m == "glass":
        paint_glass(f, model)
    elif m == "sclera":
        paint_sclera(f, model)
    elif m in ("iris", "iris_dark"):
        paint_iris(f, model)
    elif m == "pupil":
        paint_pupil(f)
    elif m == "glint":
        f.lv[:, :] = 1
    elif m == "flesh_wet":
        paint_wet(f)
    elif m in ("flesh", "flesh_dark"):
        paint_flesh(f)
    elif m in ("barnacle", "barnacle_old"):
        paint_barnacle(f)
    elif m == "nail":
        paint_nail(f)
    elif m == "kelp":
        paint_kelp(f)
    elif m == "hose":
        paint_hose(f)
    elif m in ("shard", "spray"):
        paint_see_through(f, s4.ALPHA[m])
    else:
        mottle(f)
    if m not in GLOWING and m not in s4.ALPHA:
        ao = b5.occlusion(model, model.cubes.index(cube), face, w, h, solids)
        f.lv = f.lv - (ao >= 0.3) - (ao >= 0.55)
    out = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            r = RAMP[f.zone[y, x]]
            out[y, x, :3] = r[int(np.clip(f.lv[y, x], 0, len(r) - 1))]
            # no half-clear texels: in game they hide what is drawn behind them after them, so a see-through
            # part (the spray, the shards) is dithered into clear and opaque texels instead
            a = 255 if f.alpha is None else int(np.clip(f.alpha[y, x], 0, 255))
            out[y, x, 3] = 255 if a * 16 > 255 * BAYER[y % 4][x % 4] + 127 else 0
    return out


def painted(model):
    global BODY
    BODY = s2.group(model, "body").world_matrix()
    a4.ZONES, a4.GLOWING, a4.twin = s4.ZONES, GLOWING, s4.twin
    a4.b4.hidden = s4.hidden
    keys = a4.island_keys(model)
    sizes = {key: (key[2], key[3]) for key in keys.values()}
    b4.SIZE = s4.SIZE
    positions, used, _ = b4.pack(sizes)
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
        patch = Image.fromarray(paint(model, model.cubes[i], fc, w, h, solids), "RGBA")
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return keys, positions, height, atlas


CLOSE = [
    {"name": "eye_close", "location": (0.6, 10, 4.3), "target": (0, 0, 4.1), "scale": 2.9, "player": False},
    {"name": "crown", "location": (6, 9, 9), "target": (0, 0, 4.6), "scale": 5.2, "player": False},
    {"name": "neck", "location": (-6, 9, 1.0), "target": (0, 0, 2.4), "scale": 5.4, "player": False},
]
HAND_VIEWS = [
    {"name": "hero", "location": (12, 12, 7), "target": (1.5, 0, 4.2), "scale": 13.0, "player": True},
    {"name": "front", "location": (0, 18, 4.6), "target": (1.5, 0, 4.6), "scale": 12.0, "player": False},
    {"name": "arm", "location": (13, 3, 6.5), "target": (3.4, 0.4, 4.8), "scale": 7.5, "player": False},
    {"name": "hand_close", "location": (9, 9, 9), "target": (4.4, 1.4, 5.4), "scale": 4.2, "player": False},
]


def grid(paths, labels, out, heading, cols=3, tw=470, th=352):
    pad, top = 12, 56
    rows = (len(paths) + cols - 1) // cols
    img = Image.new("RGB", (pad + cols * (tw + pad), top + rows * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), heading, font=sheet._font(28), fill=sheet.INK)
    for k, (p, label) in enumerate(zip(paths, labels)):
        x, y = pad + (k % cols) * (tw + pad), top + (k // cols) * (th + 34 + pad)
        img.paste(sheet._tile(p, tw, th), (x, y))
        dr.text((x, y + th + 6), label, font=sheet._font(17), fill=sheet.DIM)
    img.save(out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.rglob("*"):                               # files only: an open folder can't be removed
        if old.is_file() and old.name != "README.md":
            old.unlink()
    model = s4.zoned("idle")
    keys, positions, height, atlas = painted(model)
    name = s3.MODEL_ID
    atlas_path = OUT / f"{name}.png"
    atlas.save(atlas_path)
    atlas.resize((atlas.width * 2, atlas.height * 2), Image.NEAREST).save(OUT / f"{name}_preview.png")
    poses = s3.pose_table()
    for variant in s3.VARIANTS:
        m = s4.zoned("idle")
        bb, _ = s4.textured(m, name + variant, keys, positions, atlas_path, height, poses, variant)
        path = OUT / f"{name + variant}.bbmodel"
        path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
        if s3.SERVER_MODELS.is_dir():
            shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    bb, _ = s4.textured(model, name, keys, positions, atlas_path, height, {}, "")
    s4.render(model, bb, atlas_path, OUT / "renders", s4.VIEWS + CLOSE, s4.shown_model(model, {}))
    names = ["hero", "front", "side", "back", "player_eye", "eye", "eye_close", "crown", "neck"]
    grid([OUT / "renders" / f"{n}.png" for n in names], [n.replace("_", " ") for n in names], OUT / "sheet.png",
         "The Abyssal Warden - painted (session 5)")
    raised = s4.zoned("raised")
    spec = s2.POSES["raised"][1]
    bb_r, _ = s4.textured(raised, name + "_33", keys, positions, atlas_path, height, {}, "_33")
    s4.render(raised, bb_r, atlas_path, OUT / "hand", HAND_VIEWS, s4.shown_model(raised, spec))
    hn = [v["name"] for v in HAND_VIEWS]
    grid([OUT / "hand" / f"{n}.png" for n in hn], hn, OUT / "hand.png", "From 33%: the hand - painted", cols=2)
    print("painted", atlas.size)


if __name__ == "__main__":
    main()
