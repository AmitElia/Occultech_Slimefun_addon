"""The Hollow Warlord (the Headsman), session 5: texture painting (plan: docs/art/bosses/hollow_warlord/overhaul/plan.md).

Paints session 4's layout (the same islands). Ramps run from a cool violet dark through the zone's colour to a warm
light; form only, with ambient occlusion baked from the real geometry. Detail sits in 2x2 clusters, never speckle, and
metal stays smooth with one highlight band (noise made metal read as cork on the Choir).
- Bone: old wither bone, lit along its top edge, darker towards the joints, a few hairline cracks.
- Blackstone plate: polished stone. A lit bevel round each face, a dark groove inside it, one soft highlight band
  across the plate, a few faint blackstone grain clusters. plate_lit carries the same bevel, lighter.
- Leather: the grip wrapped in black leather bands. The belt is an iron girdle (plate).
- The tabard: soot-black cloth in vertical folds, its lower ends cut into ragged tatters and moth holes (clear texels).
- The blade: dark steel, a bright honed edge along both long sides, one highlight band; the guard polished blackstone.
- The brand: a soul-cyan rune broken into glyphs along the fuller.
- Under each taken skull: a severed vertebra in plain bone (no glow; review 1).
Review 1 (user): no glowing spine pieces, no red or brown, battered armour, one grey family with the wither skin.
- The four skulls: vanilla's wither skull, untouched.
Every texel is fully clear or fully opaque.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the argument:
python tools/art/bosses/headsman_s5.py <folder> [--server]
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
from bosses import headsman_s2 as s2, headsman_s3 as s3, headsman_s4 as s4, headsman_study as st  # noqa: E402

OUT = ROOT / "docs/art/bosses/hollow_warlord/overhaul/s5_paint"
noise = v5.noise
mk = c5.make_ramp
Z = s4.ZONES
RAMP = {   # one grey family: the wither skin's neutral greys, its faint teal in the lights
    "bone": mk((14, 14, 15), Z["bone"], (98, 102, 102), 9),
    "bone_dark": mk((10, 10, 11), Z["bone_dark"], (75, 77, 77), 9),
    "plate": mk((26, 27, 28), Z["plate"], (126, 130, 130), 11),
    "plate_lit": mk((44, 46, 47), Z["plate_lit"], (156, 160, 160), 11),
    "leather_dark": mk((26, 27, 28), Z["leather_dark"], (126, 130, 130), 11),
    "grip": mk((8, 8, 9), Z["grip"], (84, 86, 88), 9),
    "cloth": mk((6, 6, 7), Z["cloth"], (70, 72, 74), 9),
    "cloth_dark": mk((4, 4, 5), Z["cloth_dark"], (58, 60, 62), 9),
    "blade": mk((34, 36, 38), Z["blade"], (220, 224, 224), 9),
    "guard": mk((26, 27, 28), Z["guard"], (126, 130, 130), 11),
    "socket": mk((4, 4, 5), Z["socket"], (34, 35, 36), 5),
    "soul": [(30, 130, 150), (60, 190, 210), (92, 232, 240), (180, 252, 252), (240, 255, 255)],
    "flame": [(30, 120, 150), (60, 186, 212), (120, 240, 246), (196, 255, 252), (245, 255, 255)],
    "brand": [(24, 90, 104), (50, 160, 180), (92, 232, 240), (180, 252, 252), (240, 255, 255)],
}
MID = {k: (len(v) - 1) // 2 for k, v in RAMP.items()}
GLOWING = s4.GLOWING
CLEAR = "clear"


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
        self.long_v = h >= w


def mottle(f, lo=170, hi=830, cell=2, seed=0):
    for y in range(f.h):
        for x in range(f.w):
            r = noise(f.seed + seed, x, y, cell)
            f.lv[y, x] += -1 if r < lo else (1 if r > hi else 0)


def form(f):
    """Sky-facing faces lighter, undersides darker, upright faces lit along their top row."""
    if f.n[1] > 0.7:
        f.lv += 1
    elif f.n[1] < -0.7:
        f.lv -= 2
    elif f.h >= 3:
        f.lv[0, :] += 1
        f.lv[f.h - 1, :] -= 1


def bevel(f, lit=2, groove=-1):
    """A polished plate: a lit rim round the face, a darker groove just inside it."""
    if f.w < 4 or f.h < 4:
        f.lv[0, :] += 1
        return
    for y in range(f.h):
        for x in range(f.w):
            d = min(x, y, f.w - 1 - x, f.h - 1 - y)
            if d == 0:
                f.lv[y, x] += lit if (x == 0 or y == 0) else lit - 1
            elif d == 1 and f.w >= 7 and f.h >= 7:
                f.lv[y, x] += groove


def band(f, at=0.4, width=2.4):
    """One soft highlight band diagonally across the face."""
    for y in range(f.h):
        for x in range(f.w):
            b = (x + y) - (f.w + f.h) * at
            if 0 <= b < width:
                f.lv[y, x] += 1


# ---- materials ---------------------------------------------------------------------------------------------------------

def paint_bone(f):
    mottle(f, 150, 860, 2)
    form(f)
    if f.long_v and f.h >= 8:                         # a limb: darker towards both joints
        f.lv[:2, :] -= 1
        f.lv[f.h - 2:, :] -= 1
    rng = np.random.default_rng(f.seed)
    if f.w * f.h >= 40 and rng.random() < 0.4:        # a hairline crack, a few texels long
        y, x = int(rng.integers(1, f.h - 1)), int(rng.integers(0, f.w))
        for _ in range(int(rng.integers(3, 6))):
            if 0 <= y < f.h and 0 <= x < f.w:
                f.lv[y, x] -= 2
            y += 1
            x += int(rng.integers(-1, 2))


def paint_plate(f):
    """Battered blackstone-iron: grime pooling low on each piece, scuffed bright edges, scratches with a shadow under
    them, dents, chipped corners and the odd crack. Every mark is a cluster, never speckle."""
    rng = np.random.default_rng(f.seed)
    ys = f.p[..., 1]
    lo, hi = ys.min(), ys.max()
    if abs(f.n[1]) < 0.6 and hi - lo > 3:                      # grime pools low, the top catches light
        t = (ys - lo) / (hi - lo)
        f.lv += (t > 0.75).astype(int) - (t < 0.3).astype(int) - (t < 0.12).astype(int)
    mottle(f, 60, 960, 3, 11)
    for y in range(f.h):                                       # scuffed edges: worn bright in broken runs
        for x in range(f.w):
            d = min(x, y, f.w - 1 - x, f.h - 1 - y)
            if d == 0 and noise(f.seed + 5, x, y, 3) > 640:
                f.lv[y, x] += 2
    area = f.w * f.h
    for _ in range(int(rng.integers(0, 3)) if area >= 60 else 0):      # scratches
        x, y = int(rng.integers(0, f.w)), int(rng.integers(0, f.h))
        dx, dy = (1, 1) if rng.random() < 0.5 else (1, -1)
        for _ in range(int(rng.integers(4, 9))):
            if 0 <= x < f.w and 0 <= y < f.h:
                f.lv[y, x] += 1
                if y + 1 < f.h:
                    f.lv[y + 1, x] -= 1
            x += dx
            y += dy if rng.random() < 0.7 else 0
    for _ in range(int(rng.integers(0, 2)) if area >= 100 and f.w >= 6 and f.h >= 6 else 0):     # dents: lit rim top-left, dark bowl
        x, y = int(rng.integers(1, f.w - 3)), int(rng.integers(1, f.h - 3))
        f.lv[y, x:x + 3] += 1
        f.lv[y + 1:y + 3, x + 1:x + 3] -= 2
    if area >= 36 and rng.random() < 0.55:                              # a chipped corner
        cx = 0 if rng.random() < 0.5 else f.w - 2
        cy = 0 if rng.random() < 0.5 else f.h - 2
        f.lv[cy:cy + 2, cx:cx + 2] -= 2
    if area >= 80 and f.w >= 5 and rng.random() < 0.35:                  # a crack
        x, y = int(rng.integers(2, f.w - 2)), 0
        for _ in range(int(rng.integers(5, 10))):
            if 0 <= x < f.w and 0 <= y < f.h:
                f.lv[y, x] -= 2
            y += 1
            x += int(rng.integers(-1, 2))
    if f.n[1] < -0.6:
        f.lv -= 1


def paint_leather(f):
    mottle(f, 200, 820, 2)
    form(f)
    if f.cube.mat == "grip":                           # the wrap: diagonal bands with dark seams
        for y in range(f.h):
            for x in range(f.w):
                if (x + y) % 3 == 0:
                    f.lv[y, x] -= 2
    elif f.h >= 3 and f.w >= 6:                        # the belt's stitched line
        mid = f.h // 2
        f.lv[mid, ::2] += 1


def paint_cloth(f):
    """Vertical folds; the long faces' lower ends cut into ragged tatters."""
    for y in range(f.h):
        for x in range(f.w):
            fold = (x // 2) % 3
            f.lv[y, x] += (1, 0, -1)[fold]
            if noise(f.seed, x, y // 3, 1) > 880:
                f.lv[y, x] -= 1
    f.lv[0, :] -= 1                                    # under the belt
    if f.long_v and f.h >= 10 and abs(f.n[1]) < 0.5:
        rng = np.random.default_rng(f.seed)
        for x in range(f.w):
            cut = int(rng.integers(0, 6)) if x % 2 == 0 else int(rng.integers(0, 4))
            for k in range(cut):
                f.zone[f.h - 1 - k, x] = CLEAR
            if cut < f.h:
                f.lv[f.h - 1 - cut, x] -= 1            # frayed, darker edge
        if f.w >= 4 and f.h >= 14 and rng.random() < 0.6:   # a moth-eaten hole
            hx, hy = int(rng.integers(1, f.w - 2)), int(rng.integers(3, f.h - 8))
            f.zone[hy:hy + 2, hx:hx + 2] = CLEAR


def paint_blade(f):
    """Smooth steel: a bright honed edge along both long sides, one highlight band down the flat."""
    long_axis_v = f.long_v
    for y in range(f.h):
        for x in range(f.w):
            a = x if long_axis_v else y
            n = f.w if long_axis_v else f.h
            if n >= 6 and (a == 0 or a == n - 1):
                along = y if long_axis_v else x
                f.lv[y, x] += -2 if noise(f.seed + 9, along, 0, 2) > 820 else 3   # the honed edge, nicked
            elif n >= 6 and (a == 1 or a == n - 2):
                f.lv[y, x] += 1
            elif n >= 8 and abs(a - (n - 1) / 2) < 1.6:
                f.lv[y, x] -= 1                         # the fuller under the brand
    band(f, 0.35, 3.0)


def paint_glow(f, strokes=False):
    for y in range(f.h):
        for x in range(f.w):
            dy = abs(y - (f.h - 1) / 2) / max(1, f.h / 2)
            dx = abs(x - (f.w - 1) / 2) / max(1, f.w / 2)
            d = max(dx, dy)
            f.lv[y, x] = 4 if d < 0.34 else (3 if d < 0.67 else 2)
    if strokes:                                        # the brand: glyphs along the fuller, broken by dark gaps
        long_ = f.h if f.long_v else f.w
        for i in range(long_):
            if i % 7 in (5, 6):
                if f.long_v:
                    f.lv[i, :] = 0
                else:
                    f.lv[:, i] = 0
            elif i % 7 == 2:
                if f.long_v:
                    f.lv[i, :] = 4
                else:
                    f.lv[:, i] = 4


def paint_flame(f):
    """Soul fire: white-cyan at the root, tongues cut out of the top edge on the sides."""
    for y in range(f.h):
        for x in range(f.w):
            t = y / max(1, f.h - 1)                    # 0 at the top, 1 at the root: teal tips, cyan root
            f.lv[y, x] = 1 + int(round(t * 1.4))
    if abs(f.n[1]) < 0.5 and f.h >= 3:            # irregular tongues: each pair of columns burns to its own height
        rng = np.random.default_rng(f.seed)
        for x0 in range(0, f.w, 2):
            cut = int(rng.integers(0, f.h - 1))
            for x in range(x0, min(f.w, x0 + 2)):
                for k in range(cut):
                    f.zone[k, x] = CLEAR
    elif f.n[1] > 0.5:
        f.zone[:, :] = CLEAR                         # no flat lid on the fire


def paint(model, i, face, w, h, solids):
    cube = model.cubes[i]
    m = cube.mat
    f = Face(cube, face, w, h)
    if m == "brand":
        paint_glow(f, strokes=True)
    elif m == "flame":
        paint_flame(f)
    elif m in GLOWING:
        paint_glow(f)
    elif m in ("bone", "bone_dark"):
        paint_bone(f)
    elif m in ("plate", "plate_lit", "guard", "leather_dark"):    # the belt is an iron girdle now
        paint_plate(f)
    elif m == "grip":
        paint_leather(f)
    elif m in ("cloth", "cloth_dark"):
        paint_cloth(f)
    elif m == "blade":
        paint_blade(f)
    if m not in GLOWING:
        ao = b5.occlusion(model, i, face, w, h, solids)
        f.lv = f.lv - (ao >= 0.3) - (ao >= 0.55)
    out = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            if f.zone[y, x] == CLEAR:
                continue
            r = RAMP[f.zone[y, x]]
            out[y, x, :3] = r[int(np.clip(f.lv[y, x], 0, len(r) - 1))]
            out[y, x, 3] = 255
    return out


VIEWS = [
    {"name": "hero", "location": (-9, 13, 6), "target": (0, 0, 3.9), "scale": 11.0, "player": True},
    {"name": "far", "location": (-9, 13, 4), "target": (0, 0, 3.9), "scale": 28.0, "player": True},
    {"name": "player_eye", "location": (4.0, 11, 1.62), "target": (0, 0, 3.4), "scale": 12.0, "player": False},
    {"name": "face", "location": (-1.6, 9, 5.0), "target": (0, 0.6, 4.7), "scale": 4.2, "player": False},
    {"name": "sword", "location": (-2, 8, 1.0), "target": (1.0, 1.6, 1.3), "scale": 4.6, "player": False},
    {"name": "back", "location": (-8, -15, 6), "target": (0, 0, 4.0), "scale": 10.5, "player": False},
]


def main(argv):
    st.SKIN = Image.open(Path(argv[0]) / "assets/minecraft/textures/entity/skeleton/wither_skeleton.png").convert("RGBA")
    s4.SKIN = np.array(st.SKIN)
    OUT.mkdir(parents=True, exist_ok=True)
    s2.PALETTE.update(s4.ZONES)
    s3.a2.PALETTE = dict(s2.PALETTE)
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
    flat_atlas, flat_pos, _, _ = s4.build_atlas(keys)
    atlas = Image.new("RGBA", (s4.SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        if key[0].startswith("skin:"):
            fx, fy, _, _ = flat_pos[key]
            patch = flat_atlas.crop((fx, fy, fx + w, fy + h))
            atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        else:
            i, fc = owner[key]
            patch = Image.fromarray(paint(model, i, fc, w, h, solids), "RGBA")
            if not (np.array(patch)[..., 3] == 0).any():      # no bleed border round islands with cut-outs
                atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    path = OUT / f"{s4.NAME}.png"
    atlas.save(path)
    a = np.array(atlas)[..., 3]
    assert not ((a > 0) & (a < 255)).any(), "half-clear texels"
    poses = s3.pose_table(s3.rest_model())
    hitbox = s2.hitbox_bounds(s2.pose(s2.rig(), "idle"))
    bb, _ = a4.textured_bbmodel(model, keys, positions, path, s4.SIZE, height, hitbox, list(poses.items()))
    p = OUT / f"{s4.NAME}.bbmodel"
    p.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if "--server" in argv and s3.SERVER_MODELS.is_dir():
        shutil.copyfile(p, s3.SERVER_MODELS / p.name)
    posed = s3.posed("idle")
    s4.zone_materials(posed)
    a4.render(posed, bb, path, OUT / "idle", VIEWS)
    paths = [OUT / "idle" / f"{v['name']}.png" for v in VIEWS]
    labels = [v["name"].replace("_", " ") + (" (about 10 blocks)" if v["name"] == "far" else "") for v in VIEWS]
    a5.grid(paths, labels, OUT / "sheet.png", "Hollow Warlord - painted (session 5)", cols=3, tw=470, th=352)
    print("painted", s4.SIZE, height)


if __name__ == "__main__":
    main(sys.argv[1:])
