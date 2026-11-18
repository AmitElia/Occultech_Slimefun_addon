"""The Drowned Elder redesign, session 5: texture painting (plan: docs/art/bosses/drowned_elder/overhaul/plan.md).

Paints session 4's layout (the same islands). The head keeps vanilla's Elder Guardian skin untouched, shown at 3 pixels
per texel; so that the body reads at the same pixel size, its detail is laid in 3x3 clusters (a body "texel" the size of
one of the head's). Ramps run from a cool violet dark through the zone's colour to a warm light; form only, with ambient
occlusion baked from the real geometry.
- plate (the shingles, the tail): the elder's cracked stone, after vanilla's plates: a darker frame round each shingle,
  lit along its front edge, a couple of jagged cracks running across it, calm clusters, never speckle;
- belly: the bottom shingles in bands across the body, like a serpent's belly scales;
- seam: the soft body between the shingles, in dark folds;
- spike: the elder's violet-navy, lighter towards the tip, one lit edge;
- membrane and fin: rays running the length of the fin, like vanilla's fin;
- glow (the beam eyes): a hot sea-glow centre with a dark slit pupil, so each reads as an eye.
Every texel is fully opaque.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the last argument:
python tools/art/bosses/drowned_s5.py <folder>
"""
import json
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
from bosses import volley_crone_s5 as v5  # noqa: E402
from bosses import drowned_s2 as s2, drowned_s3 as s3, drowned_s4 as s4  # noqa: E402

OUT = ROOT / "docs/art/bosses/drowned_elder/overhaul/s5_paint"
noise = v5.noise
mk = c5.make_ramp
Z = s4.ZONES
RAMP = {
    "plate": mk((62, 56, 70), Z["plate"], (232, 226, 206), 9),
    "belly": mk((120, 112, 116), Z["belly"], (252, 248, 232), 9),
    "seam": mk((24, 20, 30), Z["seam"], (150, 140, 142), 7),
    "spike": mk((20, 18, 44), Z["spike"], (160, 150, 210), 7),
    "membrane": mk((46, 36, 62), Z["membrane"], (196, 182, 212), 7),
    "fin": mk((50, 36, 54), Z["fin"], (206, 186, 200), 7),
    "glow": [(20, 96, 96), (40, 160, 150), (110, 232, 206), (180, 255, 238), (240, 255, 250)],
    "eye": mk((150, 140, 150), Z["eye"], (255, 252, 248), 5),
}
MID = {k: (len(v) - 1) // 2 for k, v in RAMP.items()}
C = 3                                   # body detail cluster: one head texel


class Face:
    def __init__(self, cube, face, w, h):
        self.cube, self.face, self.w, self.h = cube, face, w, h
        self.mat = cube.mat
        self.lv = np.full((h, w), MID.get(cube.mat, 4), int)
        pts, n, _, _ = v5.texel_points(cube, face, w, h)
        m = v5.cube_matrix(cube)
        self.n = m[:3, :3] @ n
        self.local_n = n
        self.seed = zlib.crc32(f"{cube.name}/{face}".encode())
        self.along_v = h > w


def mottle(f, lo=150, hi=860, cell=C, seed=0):
    for y in range(f.h):
        for x in range(f.w):
            r = noise(f.seed + seed, x, y, cell)
            f.lv[y, x] += -1 if r < lo else (1 if r > hi else 0)


def form(f):
    if f.n[1] > 0.7:
        f.lv += 1
    elif f.n[1] < -0.7:
        f.lv -= 1
    elif f.h >= 6:
        f.lv[:C, :] += 1
        f.lv[f.h - C:, :] -= 1


def crack(f, rng, depth=2):
    """A jagged crack across the face, stepping one cluster at a time (vanilla's plates crack in X-like runs)."""
    cw, ch = max(1, f.w // C), max(1, f.h // C)
    if rng.random() < 0.5:
        cx, cy, dx, dy = 0, int(rng.integers(0, ch)), 1, 0
    else:
        cx, cy, dx, dy = int(rng.integers(0, cw)), 0, 0, 1
    for _ in range(max(cw, ch)):
        x0, y0 = cx * C, cy * C
        if 0 <= cx < cw and 0 <= cy < ch:
            f.lv[y0 + 1:y0 + 2, x0:x0 + C] -= depth if dy == 0 else 0
            f.lv[y0:y0 + C, x0 + 1:x0 + 2] -= depth if dx == 0 else 0
        cx += dx
        cy += dy
        r = rng.random()
        if dx and r < 0.35:
            cy += 1 if rng.random() < 0.5 else -1
        if dy and r < 0.35:
            cx += 1 if rng.random() < 0.5 else -1


def frame(f, inner=-1):
    """A darker frame one cluster wide round the face, its outermost texel row a lit lip on the top/left."""
    for y in range(f.h):
        for x in range(f.w):
            d = min(x, y, f.w - 1 - x, f.h - 1 - y)
            if d == 0:
                f.lv[y, x] += 1 if (x == 0 or y == 0) else -1
            elif d < C:
                f.lv[y, x] += inner


def paint_plate(f):
    mottle(f)
    if f.w >= 2 * C and f.h >= 2 * C:
        frame(f)
        rng = np.random.default_rng(f.seed)
        for _ in range(1 + int(f.w * f.h > 500)):
            crack(f, rng)
    form(f)


def paint_belly(f):
    mottle(f, 120, 900)
    long_ = f.along_v
    for y in range(f.h):
        for x in range(f.w):
            a = y if long_ else x
            if a % (2 * C) == 0:
                f.lv[y, x] -= 2                        # the gap between two belly scales
            elif a % (2 * C) == 1:
                f.lv[y, x] += 1                        # the next scale's lit lip
    form(f)


def paint_seam(f):
    mottle(f, 200, 900)
    for y in range(f.h):
        for x in range(f.w):
            if (x // C) % 2 == 0:
                f.lv[y, x] -= 1                        # folds of soft hide


def paint_spike(f):
    tip = f.cube.name.endswith("_b")
    f.lv += 1 if tip else 0
    if f.w >= 2:
        f.lv[:, 0] += 1                                # one lit edge
    if f.n[1] < -0.6:
        f.lv -= 1


def paint_rays(f):
    """Fin rays: a thin darker ray every few texels down the fin's length over calm, soft membrane. Close, even stripes
    read as wooden planks (the first pass did), so the rays are sparse and the membrane between them is left calm."""
    for y in range(f.h):
        for x in range(f.w):
            a = x if f.along_v else y              # across the rays
            if a % 6 == 0:
                f.lv[y, x] -= 1
    mottle(f, 80, 940, cell=C)


def paint_eye(f):
    """A beam eye: a bright field, a one-texel rim, and a single dark vertical slit pupil (two texels wide, darker at its
    middle). Ringed levels around the slit read as a double bar, a "pause" sign, in the first renders."""
    cx = (f.w - 1) / 2
    for y in range(f.h):
        for x in range(f.w):
            rim = min(x, y, f.w - 1 - x, f.h - 1 - y) == 0
            f.lv[y, x] = 2 if rim else 3
            if abs(x - cx) < 1.0 and 1 <= y <= f.h - 2:
                f.lv[y, x] = 0 if 2 <= y <= f.h - 3 else 1
    f.lv = np.clip(f.lv, 0, 4)


def paint(model, i, face, w, h, solids):
    cube = model.cubes[i]
    f = Face(cube, face, w, h)
    m = cube.mat
    if m == "glow":
        paint_eye(f)
    elif m == "plate":
        paint_plate(f)
    elif m == "belly":
        paint_belly(f)
    elif m == "seam":
        paint_seam(f)
    elif m == "spike":
        paint_spike(f)
    elif m in ("membrane", "fin"):
        paint_rays(f)
    if m != "glow":
        ao = b5.occlusion(model, i, face, w, h, solids)
        f.lv = f.lv - (ao >= 0.3) - (ao >= 0.55)
    ramp = RAMP[m if m in RAMP else "plate"]
    out = np.zeros((h, w, 4), np.uint8)
    lv = np.clip(f.lv, 0, len(ramp) - 1)
    for y in range(h):
        for x in range(w):
            out[y, x, :3] = ramp[int(lv[y, x])]
            out[y, x, 3] = 255
    return out


VIEWS = [
    {"name": "hero", "location": (16, 9, 10), "target": (0, -6.5, 3.2), "scale": 19.0, "player": True},
    {"name": "far", "location": (16, 9, 6), "target": (0, -6.5, 3.2), "scale": 44.0, "player": True},
    {"name": "player_eye", "location": (-7, 9, 1.62), "target": (0, -4, 3.4), "scale": 15.0, "player": False},
    {"name": "head", "location": (4.5, 8, 5.5), "target": (0, 0.2, 3.6), "scale": 6.5, "player": False},
    {"name": "body", "location": (10, -4, 7), "target": (0, -6, 3.6), "scale": 8.0, "player": False},
    {"name": "below", "location": (9, 2, 0.4), "target": (0, -5.0, 3.0), "scale": 17.0, "player": False},
]
AIM_VIEWS = [{"name": "aim_eyes", "location": (14, -2, 4.5), "target": (0, -5.5, 3.6), "scale": 12.0, "player": False}]


def shown(posed, bb):
    keep = [i for i, c in enumerate(posed.cubes) if c.mat != "hitbox"]
    posed.cubes = [posed.cubes[i] for i in keep]
    return dict(bb, elements=[bb["elements"][i] for i in keep])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s2.PALETTE.update(s4.ZONES)
    model = s3.rest_model()
    s4.zone_materials(model)
    model.name = s4.NAME
    keys = s4.island_keys(model)
    b4.SIZE = s4.SIZE
    positions, used, _ = b4.pack({k: (k[2], k[3]) for k in keys.values()})
    height = 16
    while height < used:
        height *= 2
    owner = {}
    for (i, fc), key in sorted(keys.items(), key=lambda kv: (kv[0][0], FACES.index(kv[0][1]))):
        owner.setdefault(key, (i, fc))
    solids = [s for s in b5.solids_of(model) if model.cubes[s[0]].mat != "hitbox"]
    flat_atlas, flat_pos, _, _ = s4.build_atlas(keys)        # the skin patches, as session 4 lays them
    atlas = Image.new("RGBA", (s4.SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        if key[0].startswith("skin:"):
            fx, fy, _, _ = flat_pos[key]
            patch = flat_atlas.crop((fx, fy, fx + w, fy + h))
        else:
            i, fc = owner[key]
            patch = Image.fromarray(paint(model, i, fc, w, h, solids), "RGBA")
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    path = OUT / f"{s4.NAME}.png"
    atlas.save(path)
    a = np.array(atlas)[..., 3]
    assert not ((a > 0) & (a < 255)).any(), "half-clear texels"
    poses = s3.pose_table(s3.rest_model())
    bb, _ = a4.textured_bbmodel(model, keys, positions, path, s4.SIZE, height, (),
                                [(k, (rt, ps)) for k, (rt, ps, _) in poses.items()])
    s3.with_scale(bb, model, poses)
    hit = {c.name for c in model.cubes if c.mat == "hitbox"}
    for e in bb["elements"]:
        if e["name"] in hit:
            e["faces"] = {f: {"uv": [0, 0, 0, 0], "texture": None} for f in e["faces"]}
    p = OUT / f"{s4.NAME}.bbmodel"
    p.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    for folder in (s3.SERVER_MODELS, s3.TEST_MODELS):
        if folder.is_dir():
            shutil.copyfile(p, folder / p.name)
    for pose, views in (("idle", VIEWS), ("aim", AIM_VIEWS)):
        posed = s3.build(pose)
        s4.zone_materials(posed)
        a4.render(posed, shown(posed, bb), path, OUT / pose, views)
    names = [("idle", v["name"]) for v in VIEWS] + [("aim", v["name"]) for v in AIM_VIEWS]
    paths = [OUT / p_ / f"{n}.png" for p_, n in names]
    labels = [n.replace("_", " ") + (" (about 15 blocks)" if n == "far" else "") for _, n in names]
    a5.grid(paths, labels, OUT / "sheet.png", "Drowned Elder - painted (session 5)", cols=4, tw=440, th=330)
    print("painted", s4.SIZE, height)


if __name__ == "__main__":
    main()
