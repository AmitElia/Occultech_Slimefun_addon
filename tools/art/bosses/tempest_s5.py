"""The Tempest redesign, session 5: texture painting (plan: docs/art/bosses/tempest/overhaul/plan.md).

Paints session 4's layout (the same islands). Ramps run from a cool, violet dark through the zone's colour to a warm
light; form only, with ambient occlusion baked from the real geometry. Detail sits in clusters, never single speckle.
- The seal: pale carved stone. On its two broad faces, two engraved rings frame the glyph circle, with a tick cut at every
  step of the circle between them, and a few hairline cracks that run out towards the rim. The broken edges are paler
  (fresh breaks). The rim is darker stone, worn lighter on its outer lip.
- The circlet: older weathered stone, rougher and darker, its lower edge in shadow.
- The heavy core: vanilla's look (heavy_core.png): every face of every block a raised frame round a recessed plate. Smooth
  dark steel with one soft highlight band, never noise (metal read as cork when it was noisy on the Choir).
- The wind: streaks running along each band, lightest down its middle, thinning to the edges.
- Glows (heart, glyphs, brows, eyes): hot centres fading to the zone's colour.
- The breeze skin (head, band, rods): vanilla's, untouched.
Every texel is fully opaque.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the last argument:
python tools/art/bosses/tempest_s5.py <folder>
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
from bosses import volley_crone_s5 as v5  # noqa: E402
from bosses import tempest_s2 as s2, tempest_s3 as s3, tempest_s4 as s4  # noqa: E402

OUT = ROOT / "docs/art/bosses/tempest/overhaul/s5_paint"
noise = v5.noise
mk = c5.make_ramp
RAMP = {
    "stone": mk((70, 62, 74), (196, 188, 168), (246, 240, 222), 9),
    "stone_dark": mk((34, 30, 38), (106, 100, 92), (170, 162, 146), 7),
    "stone_aged": mk((22, 20, 26), (72, 68, 66), (130, 124, 116), 7),
    "steel": mk((18, 18, 26), (78, 82, 89), (170, 178, 192), 9),
    "wind": mk((150, 160, 214), (222, 232, 250), (255, 255, 255), 7),
    "wind_dark": mk((70, 74, 140), (128, 140, 196), (196, 206, 240), 7),
    "core_glow": [(20, 120, 120), (40, 180, 170), (86, 232, 208), (170, 255, 240), (235, 255, 250)],
    "glyph": [(30, 150, 140), (70, 210, 190), (120, 250, 226), (190, 255, 244), (240, 255, 252)],
    "eye": [(200, 204, 224), (225, 228, 240), (243, 245, 255), (250, 250, 255), (255, 255, 255)],
    "eye_gold": [(200, 150, 50), (230, 185, 80), (249, 213, 100), (255, 235, 150), (255, 248, 210)],
}
MID = {k: (len(v) - 1) // 2 for k, v in RAMP.items()}
GLOWING = s4.GLOWING
SEAL_C = np.array([0.0, s2.CORE_Y, 12.0])
R_IN, R_MID, R_OUT = 20.0, 31.0, 44.0
GLYPH_R = R_MID + 4


class Face:
    def __init__(self, cube, face, w, h):
        self.cube, self.face, self.w, self.h = cube, face, w, h
        self.lv = np.full((h, w), MID.get(cube.mat, 4), int)
        self.zone = np.full((h, w), cube.mat, object)
        pts, n, _, _ = v5.texel_points(cube, face, w, h)
        m = v5.cube_matrix(cube)
        flat = pts.reshape(-1, 3)
        self.p = (m @ np.c_[flat, np.ones(len(flat))].T).T[:, :3].reshape(h, w, 3)
        self.n = m[:3, :3] @ n
        self.local_n = n
        self.seed = zlib.crc32(f"{cube.name}/{face}".encode())
        self.along_v = h > w


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


# ---- the seal ----------------------------------------------------------------------------------------------------------

def disc_coords(f, y, x):
    q = f.p[y, x] - SEAL_C
    return math.hypot(q[0], q[1]), math.degrees(math.atan2(q[0], q[1])) % 360


def paint_seal_face(f):
    """A broad face of a seal tile, in the bind pose: engraved rings, ticks between them, hairline cracks."""
    mottle(f, 120, 910, 3)
    for y in range(f.h):
        for x in range(f.w):
            r, a = disc_coords(f, y, x)
            if abs(r - (GLYPH_R - 4.5)) < 0.7 or abs(r - (GLYPH_R + 4.5)) < 0.7:
                f.lv[y, x] = MID["stone"] - 3                        # the engraved rings
            elif abs(r - (GLYPH_R + 3.5)) < 0.6 or abs(r - (GLYPH_R - 5.5)) < 0.6:
                f.lv[y, x] = MID["stone"] + 2                        # their lit lips
            elif GLYPH_R - 3.5 < r < GLYPH_R + 3.5 and (a % 9.0) < 1.1:
                f.lv[y, x] = MID["stone"] - 2                        # ticks round the circle
            elif r < R_IN + 2.0:
                f.lv[y, x] -= 1                                      # the inner lip, in the core's shadow
    # hairline cracks: a few jagged runs outwards from the glyph circle
    rng = np.random.default_rng(f.seed)
    if rng.random() < 0.45:
        y, x = int(rng.integers(0, f.h)), int(rng.integers(0, f.w))
        for _ in range(int(rng.integers(4, 9))):
            if 0 <= y < f.h and 0 <= x < f.w:
                f.lv[y, x] = MID["stone"] - 3
            x += int(rng.integers(-1, 2))
            y += 1 if rng.random() < 0.6 else 0


def paint_seal_edge(f):
    """A tile's narrow side: paler where it is a fresh break, otherwise plain worn stone."""
    mottle(f, 120, 910, 3)
    form(f)
    for y in range(f.h):
        for x in range(f.w):
            if noise(f.seed + 7, x, y, 3) > 760:
                f.lv[y, x] += 1


def paint_rim(f):
    mottle(f, 200, 820, 2)
    for y in range(f.h):
        for x in range(f.w):
            r, _ = disc_coords(f, y, x)
            if r > R_OUT - 0.8:
                f.lv[y, x] += 1                                       # the worn outer lip
    form(f)


def paint_aged(f):
    mottle(f, 140, 900, 3)
    if f.h >= 3 and abs(f.n[1]) < 0.7:
        f.lv[f.h - 1, :] -= 1
        f.lv[f.h - 2, :] -= (np.arange(f.w) % 3 == 0)
    form(f)


# ---- the heavy core ---------------------------------------------------------------------------------------------------------

def paint_steel(f):
    """Vanilla's heavy core face: a raised frame (lit bevel, dark groove inside it) round a recessed plate; one soft
    highlight band across the plate, never noise."""
    for y in range(f.h):
        for x in range(f.w):
            d = min(x, y, f.w - 1 - x, f.h - 1 - y)
            if d == 0:
                f.lv[y, x] += 2 if (x == 0 or y == 0) else 1
            elif d == 1:
                f.lv[y, x] += 1
            elif d == 2:
                f.lv[y, x] -= 2
            else:
                f.lv[y, x] -= 1
                band = (x + y) - (f.w + f.h) * 0.42
                if 0 <= band < 2.2:
                    f.lv[y, x] += 2
                elif -1.5 <= band < 0:
                    f.lv[y, x] += 1
    if f.n[1] < -0.6:
        f.lv -= 1


# ---- the wind ------------------------------------------------------------------------------------------------------------

def paint_wind(f):
    """Streaks along the band, lightest down the middle, thinning to its edges."""
    long_, short = (f.h, f.w) if f.along_v else (f.w, f.h)
    for y in range(f.h):
        for x in range(f.w):
            a, b = (y, x) if f.along_v else (x, y)
            c = abs(b - (short - 1) / 2) / max(1.0, short / 2)
            f.lv[y, x] += 1 if c < 0.3 else (-1 if c > 0.75 else 0)
            r = noise(f.seed, b, a // 6, 1)
            f.lv[y, x] += 1 if r > 860 else (-1 if r < 120 else 0)


# ---- glows ---------------------------------------------------------------------------------------------------------------

def paint_glow(f):
    for y in range(f.h):
        for x in range(f.w):
            dy = abs(y - (f.h - 1) / 2) / max(1, f.h / 2)
            dx = abs(x - (f.w - 1) / 2) / max(1, f.w / 2)
            d = max(dx, dy)
            f.lv[y, x] = 4 if d < 0.34 else (3 if d < 0.67 else 2)


def paint(model, i, face, w, h, solids):
    cube = model.cubes[i]
    n, m = cube.name, cube.mat
    f = Face(cube, face, w, h)
    if m in GLOWING:
        paint_glow(f)
    elif m == "stone":
        if abs(f.local_n[1]) > 0.7:          # tiles lie flat in their bone: local y is the disc's normal
            paint_seal_face(f)
        else:
            paint_seal_edge(f)
    elif m == "stone_dark":
        paint_rim(f)
    elif m == "stone_aged":
        paint_aged(f)
    elif m == "steel":
        paint_steel(f)
    elif m in ("wind", "wind_dark"):
        paint_wind(f)
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


VIEWS = [
    {"name": "hero", "location": (11, 15, 8), "target": (0, 0, 4.3), "scale": 12.0, "player": True},
    {"name": "far", "location": (11, 15, 5), "target": (0, 0, 4.3), "scale": 30.0, "player": True},
    {"name": "player_eye", "location": (-4.5, 10, 1.62), "target": (0, 0, 4.0), "scale": 11.0, "player": False},
    {"name": "face", "location": (2.2, 10, 7.2), "target": (0, 0, 6.4), "scale": 4.2, "player": False},
    {"name": "heart", "location": (3.0, 10, 4.9), "target": (0, 0, 4.4), "scale": 4.6, "player": False},
    {"name": "seal", "location": (-6, 10, 3.0), "target": (-3.2, 0, 2.6), "scale": 4.6, "player": False},
]


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
    solids = b5.solids_of(model)
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
    bb, _ = a4.textured_bbmodel(model, keys, positions, path, s4.SIZE, height, s2.HITBOX,
                                [(k, (rt, ps)) for k, (rt, ps, _) in poses.items()])
    s3.with_scale(bb, model, poses)
    p = OUT / f"{s4.NAME}.bbmodel"
    p.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    for folder in (s3.SERVER_MODELS, s3.TEST_MODELS):
        if folder.is_dir():
            shutil.copyfile(p, folder / p.name)
    posed = s3.build("idle")
    s4.zone_materials(posed)
    a4.render(posed, bb, path, OUT / "idle", VIEWS)
    paths = [OUT / "idle" / f"{v['name']}.png" for v in VIEWS]
    labels = [v["name"].replace("_", " ") + (" (about 10 blocks)" if v["name"] == "far" else "") for v in VIEWS]
    a5.grid(paths, labels, OUT / "sheet.png", "Tempest - painted (session 5)", cols=3, tw=470, th=352)
    print("painted", s4.SIZE, height)


if __name__ == "__main__":
    main()
