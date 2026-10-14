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
    "ink": [(8, 6, 10), (26, 16, 22)],                                          # the grin's line, the cracks
    "stain": [(96, 24, 30), (120, 40, 44)],
}
ZONE = {"black": ("black", 4), "white": ("white", 4), "crimson": ("crimson", 4), "gold": ("gold", 3),
        "skin": ("skin", 4), "nose": ("nose", 3), "porcelain": ("porcelain", 4), "socket": ("socket", 1),
        "leg": ("leg", 3), "claw": ("claw", 3), "crystal": ("crystal", 3), "crystal_dark": ("crystal_dark", 3),
        "string": ("string", 1), "eye_glint": ("eye_glint", 1)}
GLOWING = s4.GLOWING
DIAMOND_PARTS = ("coat_", "chest_", "ribs_", "upper_", "fore_", "thigh_", "shin_")


def world_points(cube, face, w, h):
    pts, n, _, _ = v5.texel_points(cube, face, w, h)
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
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 160, 860, 2)
    return lv, over


def grin_y(x):
    """The stitched grin (take 3): below the mask's short nose, wide across his face and curling up into the cheeks."""
    return YH - 8.4 + 0.16 * x * x


def paint_porcelain(cube, face, w, h, seed, ctx):
    """Clean old porcelain, barely mottled; a fine gold arc over each eye; on the front, a stitched grin - a thin black
    line from cheek to cheek with stitches across it - two thin cracks past the left eye, a thin dark drip from each
    socket."""
    lv, over = blank(cube, w, h)
    world, normal = ctx["world"], ctx["normal"]
    front = normal[2] < -0.5
    for y in range(h):
        for x in range(w):
            if noise(seed + 5, x, y, 3) > 930:
                lv[y, x] -= 1
            if not front:
                continue
            px, py, pz = world[y, x]
            for sx in (-1, 1):
                ex, ey = sx * 3.1, YH + 2.2
                rel = (px - ex) * sx                                   # outward from the nose
                arc = ey + 1.8 + 0.25 * rel - 0.06 * rel * rel
                if abs(py - arc) < 0.5 and -2.2 < rel < 3.0:
                    over.append((y, x, "gold", 4))                     # a fine gold arc, sweeping up and out
                if abs(px - (ex + sx * 0.6)) < 0.5 and ey - 4.2 - (sx > 0) < py < ey - 1.1:
                    over.append((y, x, "stain", 0))                    # a thin dark drip
            gy = grin_y(px)
            if abs(px) < 6.2:
                if abs(py - gy) < 0.5:
                    over.append((y, x, "ink", 0))
                elif abs(py - gy) < 1.5 and int(round(px)) % 2 == 0 and abs(px) < 4.6:
                    over.append((y, x, "ink", 1))                      # the stitches across it
            for k, (cx0, slope, top, bottom) in enumerate(((-1.7, -0.3, YH + 8, YH + 0.5), (-4.6, 0.2, YH + 6, YH + 1))):
                cx = cx0 + slope * (top - py) + 0.4 * math.sin(py * 1.9 + k)
                if bottom < py < top and abs(px - cx) < 0.4:
                    over.append((y, x, "ink", 1))
    return lv, over


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


def painter_for(cube):
    return {"black": paint_cloth, "white": paint_cloth, "leg": paint_cloth, "crimson": paint_crimson,
            "gold": paint_gold, "skin": paint_skin, "nose": paint_skin, "porcelain": paint_porcelain,
            "socket": paint_socket, "claw": paint_claw, "crystal": paint_crystal, "crystal_dark": paint_crystal,
            "string": paint_plain, "eye_glint": paint_plain}[s4.zone_for(cube)]


def paint_face(model, i, face, w, h, solids):
    cube = model.cubes[i]
    seed = zlib.crc32(f"{cube.name}/{face}".encode())
    zone = s4.zone_for(cube)
    world, normal = world_points(cube, face, w, h)
    lv, over = painter_for(cube)(cube, face, w, h, seed, {"world": world, "normal": normal})
    if not zone.startswith(GLOWING):
        ao = b5.occlusion(model, i, face, w, h, solids)
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
