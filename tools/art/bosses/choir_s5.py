"""The Blaze Choir redesign, session 5: texture painting (plan: docs/art/bosses/blaze_choir/overhaul/plan.md).

Paints session 4's layouts (the same islands). Ramps run from a cool, violet dark through the zone's colour to a warm
light; form only, with ambient occlusion baked from the real geometry. Detail sits in clusters, never single speckle.
- Brass: lathe rings round every round part (plate, cymbals, tiers), hammered dimples on the cymbals, tarnish streaks
  running down the pipes, a dark sounding mouth on the outer face of each organ pipe, rivets round the plate.
- Heat tint: the metal nearest each singer's fire takes the temper colours of heated brass, straw to bronze to purple
  to blue, in bands by distance. It is what tells these instruments are burning from the inside.
- Bell bronze: a cast, patinated skin, darker in the recesses, a raised inscription band of small marks, the lip worn
  bright where the clapper strikes.
- The wheel: dark oak with grain along every part, the bell rope's twist, iron-dark straps with rivets on the yoke.
- The cord: soft pleats on the Alto's cap, the tassels' strands.
- The fire: hot cores fading out to the zone's colour; the singing mouths the same.
- The heads: vanilla's blaze skin, untouched.
Every texel is fully opaque.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the last argument:
python tools/art/bosses/choir_s5.py <folder>
"""
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES  # noqa: E402
from bosses import archevoker_s4 as a4, archevoker_s5 as a5, brood_s4 as b4, brood_s5 as b5, coven_s5 as c5  # noqa: E402
import zlib
from bosses import choir_s2 as s2, choir_s3 as s3, choir_s4 as s4, volley_crone_s5 as v5  # noqa: E402

OUT = ROOT / "docs/art/bosses/blaze_choir/overhaul/s5_paint"
noise = v5.noise
mk = c5.make_ramp
Z = s4.ZONES

RAMP = {
    "brass": mk((60, 34, 34), (198, 150, 70), (255, 238, 160), 9),
    "brass_dark": mk((26, 18, 26), Z["brass_dark"], (170, 132, 84), 7),
    "bronze": mk((38, 20, 24), (150, 96, 52), (236, 178, 108), 9),
    "bronze_dark": mk((20, 12, 18), Z["bronze_dark"], (146, 104, 70), 7),
    "wood": mk((14, 9, 12), Z["wood"], (124, 92, 66), 7),
    "cord": mk((70, 14, 28), Z["cord"], (246, 128, 104), 7),
    "inside": [(10, 6, 10), (24, 16, 18), Z["inside"], (70, 50, 44)],
    "temper": [(70, 86, 140), (104, 74, 128), (150, 92, 76), (196, 140, 80), (226, 184, 112)],
    "white_fire": [(255, 196, 120), (255, 222, 160), (255, 240, 200), (255, 250, 232), (255, 255, 250)],
    "fire": [(214, 86, 24), (240, 124, 36), (255, 164, 64), (255, 204, 110), (255, 238, 180)],
    "red_fire": [(150, 26, 20), (196, 44, 28), (236, 84, 44), (255, 132, 72), (255, 196, 130)],
    "mouth": [(220, 120, 40), (244, 160, 56), (255, 196, 70), (255, 228, 140), (255, 248, 210)],
    "blaze": [Z["blaze"]],
}
MID = {k: (len(v) - 1) // 2 for k, v in RAMP.items()}
MID.update({"temper": 2, "inside": 1})
GLOWING = s4.GLOWING


# ---- shared painting helpers (as in tide_s5.py) ----

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
FIRES = {"soprano": [((0, s2.TOP + 3.5, 0), 9), ((0, 16, 0), 13)], "alto": [((0, 13, 0), 12)],
         "bass": [((0, 7, 0), 15), ((0, 45, 0), 8)]}


def heat(f, singer, strength=1.0):
    """Temper colours near the fire: bands by distance, straw at the edge, blue at the hottest."""
    for y in range(f.h):
        for x in range(f.w):
            p = f.p[y, x]
            best = 0.0
            for c, reach in FIRES[singer]:
                d = float(np.linalg.norm(p - np.array(c)))
                best = max(best, 1 - d / (reach * strength))
            best += (smooth(f.seed & 255, x, y, 2.5) - 0.5) * 0.25
            if best > 0.12:
                f.set(y, x, "temper", int(np.clip(4 - best * 6, 0, 4)))


def radial(f, centre, step=2):
    """Lathe rings: alternate bands by distance from the round part's axis."""
    for y in range(f.h):
        for x in range(f.w):
            d = f.p[y, x] - centre
            r = math.hypot(d[0], d[2]) if abs(f.n[1]) > 0.5 else float(np.linalg.norm(d))
            k = int(r / step) % 3
            f.lv[y, x] += 1 if k == 0 else (-1 if k == 2 and noise(f.seed, x, y, 2) > 300 else 0)


def dish_centre(cube):
    g = cube.group
    while g is not None and not (g.name.startswith(("cymbal_", "tier", "finger_", "nimbus"))):
        g = g.parent
    return np.array(g.world_matrix()[:3, 3] if g is None else (g.world_matrix() @ np.array((*g.origin, 1.0)))[:3])


def paint_cymbal(f):
    """Polished by playing: smooth, with fine tone grooves, one bright band two thirds out, a dark ring by the dome."""
    c = dish_centre(f.cube)
    big = 25.0 if "cymbal" in f.cube.name else (10.0 if "finger" in f.cube.name else 13.0)
    for y in range(f.h):
        for x in range(f.w):
            r = float(np.linalg.norm(f.p[y, x] - c)) / big
            lv = MID["brass"]
            if 0.55 < r < 0.68:
                lv += 2
            elif 0.48 < r <= 0.55 or 0.68 <= r < 0.76:
                lv += 1
            elif r < 0.33:
                lv -= 1
            if int(r * big) % 4 == 0 and 0.33 < r < 0.95:
                lv -= 1
            if smooth(f.seed & 127, x, y, 4) > 0.82:
                lv -= 1                                                     # a soft tarnish patch
            f.lv[y, x] = lv


def paint_pipe(f, cube):
    """A drawn brass tube: a lit column near one edge, a dark one near the other, a few tarnish runs downwards."""
    form(f)
    if not f.side:
        return
    w = f.w if f.along_v else f.h
    for y in range(f.h):
        for x in range(f.w):
            a, b = (x, y) if f.along_v else (y, x)
            if w >= 3 and a == 1:
                f.lv[y, x] += 2
            elif w >= 3 and a == w - 1:
                f.lv[y, x] -= 1
            if noise(f.seed, a, 0, 1) > 760 and smooth(f.seed & 127, a * 3, b, 5) > 0.55:
                f.lv[y, x] -= 1                                             # a tarnish run
    out = np.array((cube.frm[0] + cube.to[0], 0, cube.frm[2] + cube.to[2])) / 2
    out = out / (np.linalg.norm(out) or 1)
    if cube.name.startswith("pipe") and f.n @ out > 0.5 and abs(f.n[0]) > 0.5 and not cube.name.endswith("_low"):
        for y in range(3, 6):                                              # the sounding mouth, under the band
            for x in range(1, f.w - 1):
                f.set(y, x, "inside", 0 if y < 5 else 1)
            f.set(2, f.w // 2, "brass", MID["brass"] + 3)                     # the lip
            f.set(2, f.w // 2 - 1, "brass", MID["brass"] + 3)


def paint_plate(f):
    radial(f, np.array((0.0, f.p[0, 0, 1], 0.0)), 2)
    if f.side and f.w >= 6:
        for x in range(1, f.w - 1, 4):
            f.set(f.h // 2, x, "brass_dark", MID["brass_dark"] + 2)          # rivets round the rim
    form(f)


def paint_bronze(f):
    """Cast bell bronze: smooth, a lit band round the waist, patina gathered in soft patches."""
    for y in range(f.h):
        for x in range(f.w):
            py = f.p[y, x, 1]
            if 24 < py < 30:
                f.lv[y, x] += 1
            if smooth(f.seed & 255, x, y, 4) > 0.8:
                f.lv[y, x] -= 1                                             # patina gathering
    n = f.cube.name
    if n.startswith("bell_band") and f.side and f.h >= 2:                   # the inscription: raised marks in a row
        for x in range(1, f.w - 1):
            if noise(f.seed, x, 0, 1) % 3:
                f.set(f.h // 2, x, "bronze_dark", MID["bronze_dark"] + 2)
    if n.startswith("bell_lip"):
        f.lv[:, :] += 2                                                     # struck bright
    if any(abs(v) > 0.01 for v in f.cube.rotation):                     # a panel of the round casting: shade by height,
        for y in range(f.h):                                            # never per panel (that stripes it like a barrel)
            for x in range(f.w):
                py = f.p[y, x, 1]
                f.lv[y, x] += 1 if py > 36 else (-1 if py < 14 else 0)
    else:
        form(f)


def paint_wood(f):
    grain(f, 140, 900)
    form(f)


def paint_rope(f):
    for y in range(f.h):
        for x in range(f.w):
            f.lv[y, x] += 1 if (x + y) % 3 == 0 else (-1 if (x + y) % 3 == 2 else 0)


def paint_cap(f):
    for y in range(f.h):
        for x in range(f.w):
            f.lv[y, x] += -1 if x % 4 == 0 else (1 if x % 4 == 2 else 0)    # soft pleats
    mottle(f, 200, 820, 2)
    form(f)


def paint_glow(f):
    for y in range(f.h):
        for x in range(f.w):
            dy = abs(y - (f.h - 1) / 2) / max(1, f.h / 2)
            dx = abs(x - (f.w - 1) / 2) / max(1, f.w / 2)
            d = max(dx, dy)
            f.lv[y, x] = 4 if d < 0.34 else (3 if d < 0.67 else 2)


def paint_head(face, w, h):
    u, v = s4.UV_SKIN[face]
    return np.array(Image.fromarray(s4.SKIN[v:v + 8, u:u + 8].astype("uint8"), "RGBA").resize((w, h), Image.NEAREST))


def singer_of(model):
    return next(s for s in s2.RIGS if s in model.name)


def paint(model, i, face, w, h, solids):
    cube = model.cubes[i]
    n, m = cube.name, cube.mat
    if n == "head":
        return paint_head(face, w, h)
    f = Face(cube, face, w, h)
    singer = singer_of(model)
    if m in GLOWING:
        paint_glow(f)
    elif m == "brass" and ("_bow" in n or "_dome" in n or "_cap" in n):
        paint_cymbal(f)
    elif m in ("brass", "brass_dark") and n.startswith(("pipe", "fringe", "spire", "wire", "band", "foot", "fan", "striker_rod", "spindle")):
        paint_pipe(f, cube)
    elif m in ("brass", "brass_dark") and n.startswith(("plate", "striker_disc", "cap_band")):
        paint_plate(f)
    elif m in ("brass", "brass_dark"):
        mottle(f, 180, 840, 2)
        form(f)
    elif m in ("bronze", "bronze_dark"):
        paint_bronze(f)
    elif m == "wood":
        paint_wood(f)
    elif m == "cord":
        paint_rope(f) if n.startswith(("rope", "tassel")) else paint_cap(f)
    elif m == "inside":
        mottle(f, 300, 900, 2)
    if m in ("brass", "brass_dark", "bronze", "bronze_dark"):
        heat(f, singer)
    if m not in GLOWING:
        ao = b5.occlusion(model, i, face, w, h, solids)
        f.lv = f.lv - (ao >= 0.3) - (ao >= 0.55)
    out = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            r = RAMP[f.zone[y, x]]
            out[y, x, :3] = r[int(np.clip(f.lv[y, x], 0, len(r) - 1))]
            out[y, x, 3] = 255
    return out


def model_pass(singer):
    model = s3.build(singer, "idle")
    s4.bell_bronze(model)
    name = s3.rig_id(singer)
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
    a = np.array(atlas)[..., 3]
    assert not ((a > 0) & (a < 255)).any(), "half-clear texels"
    bb, _ = a4.textured_bbmodel(model, keys, positions, path, s4.SIZE, height, s2.HITBOX[singer], s3.pose_table(singer).items())
    p = OUT / f"{name}.bbmodel"
    p.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(p, s3.SERVER_MODELS / p.name)
    a4.render(model, bb, path, OUT / singer, views(singer))


DETAIL = {"soprano": ((1.8, 7, 3.6), (0, 0, 3.2), 3.6), "alto": ((3, 7, 2.4), (1.8, 0, 1.9), 3.6),
          "bass": ((2.5, 7, 1.6), (0, 0, 1.6), 4.0)}


def views(singer):
    hz, w = s4.HEAD_Z[singer], s4.WIDE[singer]
    loc, tgt, sc = DETAIL[singer]
    return [
        {"name": "hero", "location": (7, 11, 6), "target": (0, 0, 3.4), "scale": w, "player": True},
        {"name": "far", "location": (7, 11, 4), "target": (0, 0, 3.4), "scale": 26.0, "player": True},
        {"name": "head", "location": (1.8, 8, hz + 0.8), "target": (0, 0, hz), "scale": 3.4, "player": False},
        {"name": "detail", "location": loc, "target": tgt, "scale": sc, "player": False},
    ]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for singer in s2.RIGS:
        model_pass(singer)
    paths, labels = [], []
    for singer in s2.RIGS:
        for v in views(singer):
            paths.append(OUT / singer / f"{v['name']}.png")
            labels.append(f"{singer}: {v['name']}" + (" (10 blocks)" if v["name"] == "far" else ""))
    a5.grid(paths, labels, OUT / "sheet.png", "The Blaze Choir - painted (session 5)", cols=4, tw=400, th=300)
    print("painted")


if __name__ == "__main__":
    main()
