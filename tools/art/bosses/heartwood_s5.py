"""Heartwood Horror, session 5: texture painting (plan: docs/art/bosses/heartwood_horror/overhaul/plan.md).

Paints session 4's layout (the same islands). Ramps run from a cool violet dark through each zone's colour to a warm
light; form from the real geometry (sky-facing lighter, undersides darker, ambient occlusion baked into creases);
detail in clusters and 1-texel bark furrows, never speckle. Every texel is fully clear or fully opaque.
- Bark (pale oak): furrows running along each limb, broken into lengths, ridges between them; knots ringed. Pale moss
  creeps over the faces that look up and hangs in short drips down the sides.
- Roots (fingers, toes, the lantern's tail): smoother, lighter, a few fine streaks.
- Broken branch ends: pale heartwood rings inside a ring of bark.
- The lantern's cage: near-black wood, lit along its top edges. The heart itself: vanilla's awake creaking heart,
  untouched, its cracks on the glow overlay.
- The resin: amber, lighter in the window where light comes through, darker at the edges, bubbles (bright clusters
  with a highlight) and drips running down; the same dither as session 4, so the sleeper still shows.
- The sleeper: vanilla's creaking skin, warmed towards amber, as if lit through the resin. Its shut eyes dark.
- Eyeblossoms: white petals shaded towards their base, grey buds darker at their foot, the eyes bright at the centre.
- The hanging moss strands: vanilla's pale hanging moss, untouched.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the argument:
python tools/art/bosses/heartwood_s5.py <folder> [--server]
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
from bosses import heartwood_s2 as s2, heartwood_s3 as s3, heartwood_s4 as s4  # noqa: E402

OUT = ROOT / "docs/art/bosses/heartwood_horror/overhaul/s5_paint"
noise = v5.noise
mk = c5.make_ramp
Z = s4.ZONES
RAMP = {
    "bark": mk((24, 20, 30), Z["bark"], (158, 146, 130), 9),
    "bark_dark": mk((14, 11, 18), Z["bark_dark"], (118, 106, 98), 9),
    "root": mk((36, 30, 38), (110, 98, 92), (168, 156, 142), 9),
    "wood": mk((80, 68, 72), Z["wood"], (238, 232, 218), 9),
    "moss": mk((48, 54, 56), (112, 120, 110), (168, 176, 160), 7),
    "heart_frame": mk((8, 6, 10), Z["heart_frame"], (104, 92, 84), 9),
    "resin": [(92, 28, 24), (146, 52, 22), (190, 78, 22), Z["resin"], (234, 124, 34), (250, 160, 60), (255, 200, 108)],
    "resin_dark": mk((48, 14, 14), Z["resin_dark"], (196, 96, 32), 7),
    "resin_core": mk((150, 62, 24), Z["resin_core"], (255, 196, 96), 7),
    "petal": mk((112, 104, 118), Z["petal"], (255, 252, 244), 7),
    "bud": mk((66, 60, 74), Z["bud"], (204, 198, 190), 7),
    "bloom": [(196, 78, 20), (236, 116, 28), Z["bloom"], (255, 190, 90), (255, 232, 168)],
    "eyelid": mk((18, 14, 18), Z["eyelid"], (92, 82, 78), 5),
}
MID = {k: (len(v) - 1) // 2 for k, v in RAMP.items()}
VANILLA = ("sleeper", "heart", "glow")
CLEAR = "clear"
AMBER = np.array([236, 140, 56])


class Face:
    def __init__(self, cube, face, w, h):
        self.cube, self.face, self.w, self.h = cube, face, w, h
        self.lv = np.full((h, w), MID.get(cube.mat, 4), int)
        self.zone = np.full((h, w), cube.mat, object)
        pts, n, _, _ = v5.texel_points(cube, face, w, h)
        m = v5.cube_matrix(cube)
        self.n = m[:3, :3] @ n
        self.seed = zlib.crc32(f"{cube.name}/{face}".encode())
        self.long_v = h >= w


def mottle(f, lo=180, hi=820, cell=2, seed=0):
    for y in range(f.h):
        for x in range(f.w):
            r = noise(f.seed + seed, x, y, cell)
            f.lv[y, x] += -1 if r < lo else (1 if r > hi else 0)


def form(f):
    """Sky-facing faces lighter, undersides darker, upright faces lit along their top row."""
    if f.n[1] > 0.6:
        f.lv += 1
    elif f.n[1] < -0.6:
        f.lv -= 2
    elif f.h >= 3:
        f.lv[0, :] += 1
        f.lv[f.h - 1, :] -= 1


def furrows(f, dark=-2, ridge=1):
    """Pale oak bark: furrows along the face's long axis, broken into lengths, a ridge beside some of them."""
    L, A = (f.h, f.w) if f.long_v else (f.w, f.h)
    for a in range(A):
        kind = noise(f.seed + 7, a, 0, 1)
        if kind < 300:
            d = dark
        elif kind > 760:
            d = ridge
        else:
            continue
        for l in range(L):
            if noise(f.seed + 11 + a, 0, l, 3) < 220:    # the furrow breaks off here and there
                continue
            y, x = (l, a) if f.long_v else (a, l)
            f.lv[y, x] += d


def knot(f):
    cy, cx = (f.h - 1) / 2, (f.w - 1) / 2
    for y in range(f.h):
        for x in range(f.w):
            d = max(abs(x - cx) / max(cx, 1), abs(y - cy) / max(cy, 1))
            f.lv[y, x] += 1 if d > 0.75 else (-2 if d < 0.35 else -1)


def moss_over(f):
    """Pale moss creeping over a face that looks up, and a fringe with short drips hanging down an upright face."""
    if f.cube.name.startswith(("hand_", "foot_", "lantern", "moss_", "stub_")) or f.cube.mat not in ("bark", "bark_dark"):
        return
    if f.n[1] > 0.35:
        for y in range(f.h):
            for x in range(f.w):
                if noise(f.seed + 23, x, y, 3) > 760:
                    f.zone[y, x] = "moss"
                    f.lv[y, x] = MID["moss"] + (1 if noise(f.seed + 29, x, y, 2) > 700 else 0)
    elif abs(f.n[1]) <= 0.35 and f.h >= 6:
        for x in range(f.w):
            r = noise(f.seed + 31, x, 0, 2)
            if r > 760:
                depth = 1 + (r > 880) + (noise(f.seed + 37, x, 0, 1) > 900) * 2
                for y in range(min(f.h, depth)):
                    f.zone[y, x] = "moss"
                    f.lv[y, x] = MID["moss"] - (y > 0)


def rings(f):
    """A broken branch's end: heartwood rings inside a ring of bark."""
    cy, cx = (f.h - 1) / 2, (f.w - 1) / 2
    for y in range(f.h):
        for x in range(f.w):
            d = max(abs(x - cx), abs(y - cy))
            if d >= min(cx, cy) - 0.1:
                f.zone[y, x] = "bark_dark"
                f.lv[y, x] = MID["bark_dark"]
            else:
                f.lv[y, x] = MID["wood"] + (-1 if int(round(d)) % 2 else 0)


def drips(f, rng, n, dark=-1):
    for _ in range(n):
        x = int(rng.integers(0, f.w))
        y0 = int(rng.integers(0, max(1, f.h // 3)))
        for y in range(y0, min(f.h, y0 + int(rng.integers(2, 6)))):
            f.lv[y, x] += dark


def paint_resin(f):
    """Amber: lighter in the window where light comes through, darker at the edges; bubbles and drips."""
    for y in range(f.h):
        for x in range(f.w):
            e = min(x, y, f.w - 1 - x, f.h - 1 - y) / max(1.0, min(f.w, f.h) / 2)
            f.lv[y, x] += -1 if e < 0.12 else (1 if e > 0.6 else 0)
    rng = np.random.default_rng(f.seed)
    for _ in range(max(1, f.w * f.h // 160)):              # bubbles: a bright 2x2 with one highlight texel
        x, y = int(rng.integers(0, max(1, f.w - 1))), int(rng.integers(0, max(1, f.h - 1)))
        f.lv[y:y + 2, x:x + 2] = len(RAMP["resin"]) - 2
        f.lv[y, x] = len(RAMP["resin"]) - 1


def paint(model, i, face, w, h, solids, flat):
    cube = model.cubes[i]
    m = cube.mat
    f = Face(cube, face, w, h)
    if m in ("bark", "bark_dark"):
        mottle(f, 110, 900, 3)
        furrows(f)
        if "knot" in cube.name and min(w, h) >= 5:
            knot(f)
        form(f)
        moss_over(f)
    elif m == "root":
        mottle(f, 200, 820, 2)
        furrows(f, -1, 0)
        form(f)
    elif m == "wood":
        rings(f)
    elif m == "heart_frame":
        furrows(f, -1, 1)
        form(f)
        f.lv[0, :] += 1
    elif m == "resin":
        paint_resin(f)
    elif m == "resin_core":                                # the chamber's walls: deep amber, lit from the window
        mottle(f, 200, 820, 2)
        form(f)
    elif m == "resin_dark":
        mottle(f, 200, 800, 2)
        form(f)
        drips(f, np.random.default_rng(f.seed), max(1, w // 3), -2)
    elif m == "petal":
        f.lv[:, :] += 1
        for y in range(h):                                  # darker towards the flower's centre (both ends of a blade)
            for x in range(w):
                along = (y / max(1, h - 1)) if h >= w else (x / max(1, w - 1))
                f.lv[y, x] -= 1 if abs(along - 0.5) < 0.18 else 0
        form(f)
    elif m == "bud":
        f.lv[h - max(1, h // 3):, :] -= 1
        f.lv[: max(1, h // 4), :] += 1
    elif m == "bloom":
        if w >= 3 and h >= 3:
            f.lv[1:-1, 1:-1] += 1
    elif m == "eyelid":
        pass
    if m not in ("bloom", "resin", "petal", "bud", "eyelid", "resin_core"):
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
    if m == "resin":                                       # session 4's translucency; bubbles and drips solid
        a = np.array(flat)[..., 3].astype(int)
        if cube.name == "resin":
            a = np.where(f.lv >= len(RAMP["resin"]) - 2, 255, a)
        out[..., 3] = a
    return out


VIEWS = [
    {"name": "hero", "location": (10, 15, 7.5), "target": (0, 0.5, 3.6), "scale": 13.5, "player": True},
    {"name": "far", "location": (10, 15, 4), "target": (0, 0.5, 3.6), "scale": 30.0, "player": True},
    {"name": "player_eye", "location": (-4.5, 10, 1.62), "target": (0, 1.5, 3.6), "scale": 12.5, "player": False},
    {"name": "chest", "location": (2.2, 10, 2.2), "target": (0, 1.6, 3.9), "scale": 4.6, "player": False},
    {"name": "arm", "location": (9, 7, 9), "target": (2.6, 0.2, 5.8), "scale": 5.2, "player": False},
    {"name": "back", "location": (-9, -16, 8), "target": (0, 0, 4.0), "scale": 13.0, "player": False},
]


def womb_view(model, bb, path):
    """The womb alone, as a player standing in front of it sees it (from below), to check the sleeper shows."""
    keep = [i for i, c in enumerate(model.cubes) if s2.in_subtree(c, ("womb",))]
    sub = type(model)(model.name)
    sub.cubes = [model.cubes[i] for i in keep]
    sbb = dict(bb, elements=[bb["elements"][i] for i in keep])
    c = np.vstack([cu.corners() for cu in sub.cubes]).mean(0) / 16
    target = (float(c[0]), float(-c[2]), float(c[1]))
    views = [{"name": "womb_below", "location": (target[0] + 1.0, target[1] + 3.2, target[2] - 2.4), "target": target,
              "scale": 2.6, "player": False},
             {"name": "womb_front", "location": (target[0] + 0.4, target[1] + 4.0, target[2]), "target": target,
              "scale": 2.6, "player": False}]
    s4.render(sub, sbb, path, OUT / "womb", views)
    a5.grid([OUT / "womb" / f"{v['name']}.png" for v in views], ["from below (a player in front)", "front"],
            OUT / "womb.png", "Heartwood Horror - the womb alone (session 5)", cols=2, tw=470, th=352)


def main(argv):
    assets = Path(argv[0]) / "assets/minecraft/textures"
    for key, rel in (("creaking", "entity/creaking/creaking.png"), ("heart_side", "block/creaking_heart_awake.png"),
                     ("heart_top", "block/creaking_heart_top_awake.png"), ("moss", "block/pale_hanging_moss.png"),
                     ("moss_tip", "block/pale_hanging_moss_tip.png"), ("heart_base", "block/creaking_heart.png"),
                     ("heart_base_top", "block/creaking_heart_top.png")):
        s4.TEX[key] = np.array(Image.open(assets / rel).convert("RGBA"))
    OUT.mkdir(parents=True, exist_ok=True)
    s2.PALETTE.update(s4.ZONES)
    s3.a2.PALETTE = dict(s2.PALETTE)
    model = s3.model()
    for c in model.cubes:
        if c.name.startswith("lantern_root"):
            c.mat = "bark_dark"
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
    atlas = Image.new("RGBA", (s4.SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        flat = s4.patch_for(key)
        name, face, _, _, mat = key
        if mat in VANILLA or (mat == "moss" and face not in ("up", "down")):
            arr = np.array(flat)
            if mat == "sleeper":                             # lit through the amber
                arr[..., :3] = np.clip(arr[..., :3] * 0.88 + AMBER * 0.1, 0, 255).astype(np.uint8)
            patch = Image.fromarray(arr, "RGBA")
        else:
            i, fc = owner[key]
            patch = Image.fromarray(paint(model, i, fc, w, h, solids, flat), "RGBA")
        if not (np.array(patch)[..., 3] == 0).any():
            atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    path = OUT / f"{s4.NAME}.png"
    atlas.save(path)
    half = 0
    for key, (x, y, w, h) in positions.items():               # only the resin shell may be half-clear
        a = np.array(atlas)[y:y + h, x:x + w, 3]
        n = int(((a > 0) & (a < 255)).sum())
        assert n == 0 or key[0] == "resin", f"half-clear texels on {key[0]}"
        half += n
    print("half-clear (resin shell only):", half)
    poses = s3.pose_table(s3.model())
    hitbox = s2.hitbox_bounds(s2.build().m)
    bb, _ = a4.textured_bbmodel(model, keys, positions, path, s4.SIZE, height, hitbox, list(poses.items()))
    p = OUT / f"{s4.NAME}.bbmodel"
    p.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if "--server" in argv and s3.SERVER_MODELS.is_dir():
        shutil.copyfile(p, s3.SERVER_MODELS / p.name)
    s4.render(model, bb, path, OUT / "idle", VIEWS)
    womb_view(model, bb, path)
    paths = [OUT / "idle" / f"{v['name']}.png" for v in VIEWS]
    labels = [v["name"].replace("_", " ") + (" (about 10 blocks)" if v["name"] == "far" else "") for v in VIEWS]
    a5.grid(paths, labels, OUT / "sheet.png", "Heartwood Horror - painted (session 5)", cols=3, tw=470, th=352)
    print("painted", s4.SIZE, height)


if __name__ == "__main__":
    main(sys.argv[1:])
