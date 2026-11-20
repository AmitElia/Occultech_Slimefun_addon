"""Dread Riders, session 5: texture painting (plan: docs/art/bosses/dread_riders/overhaul/plan.md).

Paints session 4's layout (the same islands, one atlas per model). Ramps run from a cool violet/blue dark through the
zone's colour to a warm light; form only (the game shades by face direction), with ambient occlusion baked from the
real geometry. Detail sits in 2x2-3x3 clusters, never speckle; metal stays smooth with one highlight band (noise made
metal read as cork on the Choir). Every texel fully clear or fully opaque. Vanilla skins (the heads, the riders'
bodies, the skeleton's limbs) are untouched.

- The Vanguard's horse: vanilla's rotting zombie-horse green, mottled, with darker rot and paler mould in clusters; on
  the flanks under the barding the ribs show through as pale bars. Dark mane and tail in strands.
- Netherite-dark plate: a lit bevel, a groove inside it, one soft highlight band, grime pooling low, scuffed edges in
  broken runs, a few scratches with a shadow under them, rivets along the big plates' edges. Spikes are smooth: a lit
  ridge and a highlight band. The chest boss and sigil glow crimson.
- The saddle cloth and banner: near-black violet cloth in folds, the hanging ends tattered; crimson trim with a
  stitched line. The lance: wood grain along its length, a leather grip in bands. The horns: dark horn ringed with
  growth ridges, pale at the tips.
- The skeleton horse: old bone, lit along the top, darker towards the joints, hairline cracks. Red rope lashings
  twisted in diagonal bands; the blanket a coarse weave, frayed along its lower edge. A dark horsehair tail.
- The steppe helm: smooth iron with a highlight band and a few hammer dents; gold rim and ribs polished; the aventail
  in rows of rings; the plume in horsehair strands.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the argument:
python tools/art/bosses/dread_s5.py <client folder> [--server]
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
from bosses import archevoker_s2 as a2, archevoker_s4 as a4, archevoker_s5 as a5, brood_s4 as b4, brood_s5 as b5  # noqa: E402
from bosses import coven_s5 as c5, volley_crone_s5 as v5  # noqa: E402
from bosses import dread_s2 as s2, dread_s3 as s3, dread_s4 as s4  # noqa: E402

OUT = ROOT / "docs/art/bosses/dread_riders/overhaul/s5_paint"
noise = v5.noise
mk = c5.make_ramp
Z = s4.ZONES
RAMP = {
    "zhorse": mk((16, 26, 26), Z["zhorse"], (150, 166, 108), 11),
    "zhorse_dark": mk((12, 18, 20), Z["zhorse_dark"], (110, 124, 84), 9),
    "hair": mk((6, 6, 10), Z["hair"], (78, 76, 68), 9),
    "hoof": mk((12, 10, 16), Z["hoof"], (118, 104, 90), 9),
    "plate": mk((12, 8, 18), (54, 48, 58), (116, 106, 114), 11),
    "plate_edge": mk((24, 18, 30), (96, 88, 96), (176, 166, 166), 11),
    "plate_dark": mk((6, 4, 10), Z["plate_dark"], (92, 86, 92), 9),
    "cloth": mk((6, 4, 12), Z["cloth"], (86, 72, 98), 9),
    "trim": mk((40, 8, 22), Z["trim"], (228, 100, 80), 9),
    "leather": mk((28, 16, 20), Z["leather"], (176, 136, 96), 9),
    "wood": mk((36, 22, 24), Z["wood"], (198, 162, 114), 9),
    "horn": mk((6, 4, 10), Z["horn"], (112, 100, 88), 9),
    "horn_tip": mk((70, 60, 64), Z["horn_tip"], (238, 230, 208), 9),
    "chain": mk((22, 22, 32), Z["chain"], (178, 178, 182), 9),
    "iron_dark": mk((14, 14, 22), Z["iron_dark"], (140, 140, 148), 9),
    "zskin": mk((22, 40, 24), Z["zskin"], (170, 200, 120), 9),
    "zface": mk((8, 14, 8), Z["zface"], (60, 80, 50), 5),
    "bone": mk((58, 54, 66), Z["bone"], (240, 240, 234), 11),       # vanilla skeleton-horse greys
    "bone_dark": mk((34, 32, 42), Z["bone_dark"], (206, 204, 198), 9),
    "lamellar": mk((14, 14, 24), Z["lamellar"], (170, 172, 180), 9),
    "socket": mk((6, 6, 8), Z["socket"], (70, 70, 76), 5),
    "rope": mk((34, 8, 16), Z["rope"], (204, 96, 76), 9),
    "blanket": mk((38, 30, 38), Z["blanket"], (208, 194, 172), 9),
    "iron": mk((40, 40, 58), Z["iron"], (240, 240, 236), 11),
    "gold": mk((58, 34, 20), Z["gold"], (248, 218, 134), 11),
    "mail": mk((26, 26, 38), Z["mail"], (188, 188, 188), 9),
    "plume": mk((40, 6, 18), Z["plume"], (238, 112, 92), 9),
    "skel": mk((58, 58, 66), Z["skel"], (246, 246, 238), 9),
    "skel_dark": mk((18, 18, 22), Z["skel_dark"], (130, 130, 130), 5),
    "coat": mk((12, 14, 26), Z["coat"], (126, 142, 152), 9),
    "coat_dark": mk((6, 8, 18), Z["coat_dark"], (98, 108, 122), 9),
    "cyan": [(20, 110, 122), (50, 180, 192), (96, 236, 226), (180, 252, 248), (240, 255, 255)],
    "crimson": [(90, 10, 20), (170, 24, 36), (232, 48, 56), (255, 130, 110), (255, 222, 204)],
}
MID = {k: (len(v) - 1) // 2 for k, v in RAMP.items()}
GLOWING = s4.GLOWING
CLEAR = "clear"
TATTERED = ("banner", "cloth_side", "cape", "blanket-1_", "blanket1_", "coat_tail")


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
        self.seed = zlib.crc32(f"{cube.name}/{face}".encode())
        self.long_v = h >= w
        self.rng = np.random.default_rng(self.seed)


def mottle(f, lo=170, hi=830, cell=2, seed=0, amount=1):
    for y in range(f.h):
        for x in range(f.w):
            r = noise(f.seed + seed, x, y, cell)
            f.lv[y, x] += -amount if r < lo else (amount if r > hi else 0)


def form(f):
    """Sky-facing faces lighter, undersides darker, upright faces lit along their top row."""
    if f.n[1] > 0.7:
        f.lv += 1
    elif f.n[1] < -0.7:
        f.lv -= 2
    elif f.h >= 3:
        f.lv[0, :] += 1
        f.lv[f.h - 1, :] -= 1


def grime(f):
    """On upright faces: light on the top, grime pooling at the bottom (by world height)."""
    ys = f.p[..., 1]
    lo, hi = ys.min(), ys.max()
    if abs(f.n[1]) < 0.6 and hi - lo > 3:
        t = (ys - lo) / (hi - lo)
        f.lv += (t > 0.78).astype(int) - (t < 0.25).astype(int)


def bevel(f, lit=2, groove=-1):
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
    for y in range(f.h):
        for x in range(f.w):
            b = (x + y) - (f.w + f.h) * at
            if 0 <= b < width:
                f.lv[y, x] += 1


def tatter(f, depth=5):
    """A hanging cloth's lower edge cut into ragged tatters (cut-outs), the frayed edge darker."""
    if not (f.long_v and f.h >= 8 and abs(f.n[1]) < 0.5):
        return
    for x in range(f.w):
        cut = int(f.rng.integers(0, depth + 1)) if x % 2 == 0 else int(f.rng.integers(0, max(1, depth - 2)))
        for k in range(cut):
            f.zone[f.h - 1 - k, x] = CLEAR
        if cut < f.h:
            f.lv[f.h - 1 - cut, x] -= 1


# ---- materials ---------------------------------------------------------------------------------------------------------

def paint_hide(f):
    """The zombie horse: rotting green, darker rot and paler mould in clusters, the ribs showing on the flanks."""
    mottle(f, 110, 910, 3)
    for y in range(f.h):
        for x in range(f.w):
            r = noise(f.seed + 3, x, y, 4)
            if r > 950:
                f.lv[y, x] -= 1                    # rot
            elif r < 25:
                f.lv[y, x] += 1                    # mould
    form(f)
    name = f.cube.name
    if name.startswith("body_") and abs(f.n[0]) > 0.7:
        for y in range(f.h):
            for x in range(f.w):
                px, py, pz = f.p[y, x]
                if -24 < pz < 14 and 38 < py < 58:
                    ph = int(pz) % 7
                    if ph in (0, 1):
                        f.lv[y, x] += 3            # a rib through the hide
                    elif ph == 2:
                        f.lv[y, x] -= 2            # the hollow behind it


def paint_hair(f):
    for y in range(f.h):
        for x in range(f.w):
            a = x if f.long_v else y
            f.lv[y, x] += (1, 0, -1)[(a + (noise(f.seed, a, 0, 1) > 600)) % 3]
            if noise(f.seed + 4, a, (y if f.long_v else x) // 3, 1) > 870:
                f.lv[y, x] -= 1


def paint_plate(f, rivets=True):
    """Netherite-dark plate: bevel, groove, one highlight band, grime low, scuffed edges, a few scratches, rivets."""
    grime(f)
    bevel(f)
    band(f, 0.38, 2.6)
    for y in range(f.h):
        for x in range(f.w):
            if min(x, y, f.w - 1 - x, f.h - 1 - y) == 0 and noise(f.seed + 5, x, y, 3) > 700:
                f.lv[y, x] += 1
    area = f.w * f.h
    for _ in range(int(f.rng.integers(0, 3)) if area >= 70 else 0):
        x, y = int(f.rng.integers(0, f.w)), int(f.rng.integers(0, f.h))
        dx, dy = (1, 1) if f.rng.random() < 0.5 else (1, -1)
        for _ in range(int(f.rng.integers(3, 7))):
            if 0 <= x < f.w and 0 <= y < f.h:
                f.lv[y, x] += 1
                if y + 1 < f.h:
                    f.lv[y + 1, x] -= 1
            x += dx
            y += dy if f.rng.random() < 0.7 else 0
    if rivets and f.w >= 10 and f.h >= 8:
        for x in range(3, f.w - 2, 5):
            for y in (2, f.h - 3):
                f.lv[y, x] += 2
                if y + 1 < f.h and x + 1 < f.w:
                    f.lv[y + 1, x + 1] -= 1
    if f.n[1] < -0.6:
        f.lv -= 1


def paint_spike(f):
    """Smooth steel: lit along one edge, a highlight band, darker at the root."""
    for y in range(f.h):
        for x in range(f.w):
            a = x if not f.long_v else y
            if (x == 0 or y == 0):
                f.lv[y, x] += 2
    band(f, 0.45, 2.0)
    form(f)


def paint_bone(f):
    mottle(f, 70, 950, 3)
    form(f)
    if f.long_v and f.h >= 8:
        f.lv[:2, :] -= 1
        f.lv[f.h - 2:, :] -= 1
    if f.w * f.h >= 40 and f.rng.random() < 0.45:
        y, x = int(f.rng.integers(1, f.h - 1)), int(f.rng.integers(0, f.w))
        for _ in range(int(f.rng.integers(3, 6))):
            if 0 <= y < f.h and 0 <= x < f.w:
                f.lv[y, x] -= 2
            y += 1
            x += int(f.rng.integers(-1, 2))


def paint_cloth(f):
    for y in range(f.h):
        for x in range(f.w):
            fold = (x // 2) % 3 if f.long_v else (y // 2) % 3
            f.lv[y, x] += (1, 0, -1)[fold]
            if noise(f.seed, x, y // 3, 1) > 880:
                f.lv[y, x] -= 1
    form(f)
    if f.cube.name.startswith(TATTERED):
        tatter(f)


def paint_trim(f):
    form(f)
    if f.h >= 3 and f.w >= 6:
        mid = f.h // 2
        f.lv[mid, ::2] += 1
    elif f.w >= 3 and f.h >= 6:
        mid = f.w // 2
        f.lv[::2, mid] += 1


def paint_leather(f):
    mottle(f, 200, 820, 2)
    form(f)
    if f.cube.name.startswith("lance_grip"):
        for y in range(f.h):
            for x in range(f.w):
                if ((x if not f.long_v else y) // 2) % 2 == 0:
                    f.lv[y, x] -= 1
    elif f.h >= 4 and f.w >= 8:
        f.lv[1, 1:-1:2] += 1                       # a stitched line along the top


def paint_wood(f):
    for y in range(f.h):
        for x in range(f.w):
            across = x if f.long_v else y
            along = y if f.long_v else x
            r = noise(f.seed, across, along // 4, 1)
            f.lv[y, x] += 1 if r > 760 else (-1 if r < 240 else 0)
    form(f)


def paint_horn(f):
    for y in range(f.h):
        for x in range(f.w):
            along = y if f.long_v else x
            if along % 3 == 0:
                f.lv[y, x] -= 1                    # growth ridges
            elif along % 3 == 1:
                f.lv[y, x] += 1
    form(f)


def paint_lamellar(f):
    """Rows of small laced plates: a dark slit between plates every 3 texels, each row lit along its top, a lace row
    darker under it; one soft band."""
    for y in range(f.h):
        for x in range(f.w):
            across = x if not f.long_v or f.w >= f.h else y
            along_row = y if not f.long_v or f.w >= f.h else x
            if across % 3 == 2:
                f.lv[y, x] -= 1
            if along_row % 4 == 0:
                f.lv[y, x] += 1
            elif along_row % 4 == 3:
                f.lv[y, x] -= 1
    band(f, 0.4, 2.0)
    grime(f)


def paint_rope(f):
    for y in range(f.h):
        for x in range(f.w):
            f.lv[y, x] += 1 if (x + y) % 4 < 2 else -1


def paint_blanket(f):
    for y in range(f.h):
        for x in range(f.w):
            if (x // 2 + y // 2) % 2 == 0 and noise(f.seed, x, y, 2) > 400:
                f.lv[y, x] += 1
    mottle(f, 120, 940, 3, 7)
    form(f)
    if f.cube.name.startswith(TATTERED):
        tatter(f, 4)


def paint_iron(f, dents=True):
    bevel(f, 2, -1)
    band(f, 0.4, 2.2)
    form(f)
    if dents and f.w * f.h >= 30:
        for _ in range(int(f.rng.integers(0, 3))):
            x, y = int(f.rng.integers(0, max(1, f.w - 2))), int(f.rng.integers(0, max(1, f.h - 2)))
            f.lv[y, x:x + 2] += 1
            f.lv[y + 1:y + 2, x:x + 2] -= 1


def paint_mail(f):
    for y in range(f.h):
        for x in range(f.w):
            if y % 2 == 0:
                f.lv[y, x] += 1 if (x + (y // 2) % 2) % 2 == 0 else -1
            else:
                f.lv[y, x] -= 1
    grime(f)


def paint_plume(f):
    paint_hair(f)
    form(f)


def paint_hoof(f):
    form(f)
    ys = f.p[..., 1]
    if abs(f.n[1]) < 0.6 and ys.max() - ys.min() > 2:
        f.lv[ys < ys.min() + 1.5] -= 1


def paint_glow(f):
    for y in range(f.h):
        for x in range(f.w):
            dy = abs(y - (f.h - 1) / 2) / max(1, f.h / 2)
            dx = abs(x - (f.w - 1) / 2) / max(1, f.w / 2)
            d = max(dx, dy)
            f.lv[y, x] = 4 if d < 0.34 else (3 if d < 0.67 else 2)


def paint(model, i, face, w, h, solids):
    cube = model.cubes[i]
    m = cube.mat
    f = Face(cube, face, w, h)
    if m in GLOWING:
        paint_glow(f)
    elif m in ("zhorse", "zhorse_dark", "zskin"):
        paint_hide(f)
    elif m in ("hair",):
        paint_hair(f)
    elif m in ("plate", "plate_dark", "plate_edge"):
        if "spike" in cube.name or "finial" in cube.name or "lance_head" in cube.name:
            paint_spike(f)
        else:
            paint_plate(f, rivets=m == "plate")
    elif m in ("bone", "bone_dark", "skel"):
        paint_bone(f)
    elif m in ("cloth", "coat", "coat_dark"):
        paint_cloth(f)
    elif m in ("trim",):
        paint_trim(f)
    elif m in ("leather",):
        paint_leather(f)
    elif m in ("wood",):
        paint_wood(f)
    elif m in ("horn", "horn_tip"):
        paint_horn(f)
    elif m == "rope":
        paint_rope(f)
    elif m == "lamellar":
        paint_lamellar(f)
    elif m == "blanket":
        paint_blanket(f)
    elif m in ("iron", "gold", "iron_dark", "chain"):
        paint_iron(f, dents=m == "iron")
    elif m == "mail":
        paint_mail(f)
    elif m == "plume":
        paint_plume(f)
    elif m == "hoof":
        paint_hoof(f)
    else:
        form(f)
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


def painted_atlas(kind, part, model, keys):
    b4.SIZE = s4.SIZE
    positions, used, _ = b4.pack({k: (k[2], k[3]) for k in keys.values()})
    height = 16
    while height < used:
        height *= 2
    solids = b5.solids_of(model)
    atlas = Image.new("RGBA", (s4.SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        _, face, _, _, _, i = key
        arr = s4.vanilla_patch(kind, part, model.cubes[i], face, w, h)
        if arr is None or arr.shape[:2] != (h, w):
            arr = paint(model, i, face, w, h, solids)
        else:
            arr = arr.astype(np.uint8).copy()
            arr[..., 3] = 255
        patch = Image.fromarray(arr.astype(np.uint8), "RGBA")
        if not (np.array(patch)[..., 3] == 0).any():
            atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    a = np.array(atlas)[..., 3]
    assert not ((a > 0) & (a < 255)).any(), "half-clear texels"
    return atlas, positions, height


def main(argv):
    assets = Path(argv[0]) / "assets/minecraft/textures/entity"
    for key, rel in (("zombie", "zombie/zombie.png"), ("skeleton", "skeleton/skeleton.png"),
                     ("horse_zombie", "horse/horse_zombie.png"), ("horse_skeleton", "horse/horse_skeleton.png")):
        s4.TEX[key] = np.array(Image.open(assets / rel).convert("RGBA"))
    OUT.mkdir(parents=True, exist_ok=True)
    s2.PALETTE.update(Z)
    a2.PALETTE = dict(s2.PALETTE)
    a4.ZONES, a4.GLOWING = Z, GLOWING
    only = [k for k in ("vanguard", "outrider") if k in argv] or ["vanguard", "outrider"]
    for kind in only:
        P = s3.build_pair(kind)
        bbs, atlases = [], []
        for part, model, name, hb, poses in (("mount", P["mount"], f"occultech_dread_{kind}_mount_rig", None, P["mount_poses"]),
                                             ("rider", P["rider"], f"occultech_dread_{kind}_rig", P["hitbox"], P["rider_poses"])):
            keys = s4.island_keys(model)
            atlas, positions, height = painted_atlas(kind, part, model, keys)
            path = OUT / f"{name}.png"
            atlas.save(path)
            s3.scale_model(model)
            bb, _ = s4.textured(model, name, keys, positions, path, height, s3.scaled_hitbox(hb), s3.scaled_poses(poses))
            p = OUT / f"{name}.bbmodel"
            p.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
            if "--server" in argv and s3.SERVER_MODELS.is_dir():
                shutil.copyfile(p, s3.SERVER_MODELS / p.name)
            bbs.append(bb)
            atlases.append(atlas)
        P["seat"] = np.array(P["seat"]) * s3.SCALE
        views = s4.views_for(P)
        views.insert(1, {"name": "far", "location": (11, 15, 5), "target": (0, 0, 3.6), "scale": 30.0, "player": True})
        views = [v for v in views if v["name"] not in ("front",)]
        s4.pair_render(kind, P, bbs, atlases, OUT / kind, views)
        paths = [OUT / kind / f"{v['name']}.png" for v in views]
        labels = [v["name"].replace("_", " ") + (" (about 10 blocks)" if v["name"] == "far" else "") for v in views]
        a5.grid(paths, labels, OUT / f"sheet_{kind}.png", f"Dread Riders: the {kind.title()}, painted (session 5)",
                cols=4, tw=470, th=352)
        print("painted", kind)


if __name__ == "__main__":
    main(sys.argv[1:])
