"""The Night Matriarch redesign, session 5: texture painting.

Paints the session 4 layout (one 256 x 256 atlas, the same islands) with fine ramps (close shades, cool shadows,
lighter highlights), so detail stays subtle:
- the hide: vanilla's phantom blue-grey, mottled and leathery, creased; paler on her underside; where the hide gives
  way to bare bone down the middle of her head it is torn, a ragged dark edge with raw flesh along it;
- the sculk (the user: the infestation is mostly texture): dark teal blotches spreading over her hide, her bone and the
  roots of her wings, heavier on her rotten left side and her back, flecked with points of cyan light;
- bone: old and yellowed, cracked, darker in the sutures; the skull side of her head, the ribs, spine, crown, the
  wings' spars and finger bones;
- the rotten flesh inside the open flank: dark, wet, sinewed;
- the wings: dark membrane with paler veins fanning from the shoulder, and the tears (the user: in the texture, not
  missing blocks) - ragged holes and a torn trailing edge, cut out so the sky shows through, the bones left bare
  where whole stretches are gone; the same holes on both faces of each strip;
- the owl's tail: grey-brown feathers barred across like an owl's, darker at the tips; one feather broken off;
- the gills: each plane cut out into a frond like an axolotl's gill - a glowing cyan stalk, dark sculk filaments
  fringing both edges, shorter towards the tip;
- the glow: the phantom's green eye with a pale core; the sculk light deep in the empty socket.
Form only, no painted light direction: ambient occlusion baked from the real geometry.

Run from the repository root: python tools/art/bosses/matriarch_s5.py
"""
import json
import math
import shutil
import subprocess
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
from bosses import matriarch_s2 as s2, matriarch_s3 as s3, matriarch_s4 as s4  # noqa: E402
from bosses import volley_crone_s3 as v3, volley_crone_s4 as v4, volley_crone_s5 as v5  # noqa: E402

OUT = ROOT / "docs/art/bosses/night_matriarch/overhaul/s5_paint"
noise = v5.noise
mk = c5.make_ramp
W, L, FRONT, LIFT, HW = s2.W, s2.L, s2.FRONT, s2.LIFT, s2.HW

RAMP = {
    "hide": mk((20, 24, 46), (68, 82, 130), (150, 166, 204), 11),
    "hide_dark": mk((8, 10, 22), (38, 44, 80), (96, 104, 140), 7),
    "belly": mk((48, 54, 80), (128, 140, 176), (206, 214, 232), 9),
    "flesh": mk((20, 6, 10), (74, 30, 38), (142, 72, 74), 7),
    "bone": mk((66, 58, 44), (206, 198, 172), (250, 246, 230), 9),
    "membrane": mk((8, 8, 20), (38, 42, 74), (104, 112, 152), 9),
    "feather": mk((36, 34, 46), (122, 120, 146), (214, 210, 222), 9),
    "sculk": mk((4, 16, 22), (16, 46, 58), (44, 104, 118), 7),
    "spark": [(36, 150, 170), (60, 200, 220), (150, 246, 255)],        # sculk's points of light
    "hole": [(4, 4, 8), (14, 12, 18), (28, 26, 34)],
    "eye": mk((40, 110, 20), (150, 255, 110), (240, 255, 220), 5),
    "sculk_glow": mk((10, 90, 110), (40, 214, 232), (220, 255, 255), 5),
    "gill": mk((4, 22, 30), (22, 96, 116), (170, 250, 255), 9),
}
ZONE = {"hide": ("hide", 5), "hide_dark": ("hide_dark", 3), "belly": ("belly", 4), "flesh": ("flesh", 3),
        "bone": ("bone", 4), "membrane": ("membrane", 4), "feather": ("feather", 4), "sculk": ("sculk", 3),
        "hole": ("hole", 1), "eye": ("eye", 2), "sculk_glow": ("sculk_glow", 2), "gill": ("gill", 4)}
GLOWING = s4.GLOWING


# ---- helpers ---------------------------------------------------------------------------------------------------------

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


def smooth(seed, u, v, cell):
    """Smooth value noise 0..1 (bilinear between cell corners), for blotches that run across cube edges."""
    i, j = math.floor(u / cell), math.floor(v / cell)
    fu, fv = u / cell - i, v / cell - j
    fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
    a, b = noise(seed, i, j, 1), noise(seed, i + 1, j, 1)
    c, d = noise(seed, i, j + 1, 1), noise(seed, i + 1, j + 1, 1)
    return ((a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv) / 999


def sculk_amount(p):
    """How thick the sculk grows at a world point: blotches over her, heavier on her left (her rotten side) and on
    her back."""
    x, y, z = p
    v = 0.6 * smooth(7, x, z, 9) + 0.25 * smooth(11, x + y, z - y, 4) + 0.15 * smooth(13, y, x + z, 3)
    v += 0.12 if x < 0 else 0
    v += 0.06 if y > LIFT + 4 else 0
    return v


def infest(lv, over, world, seed, threshold=0.66):
    """Sculk over a face: its own ramp where it's thick, a dark rim where it thins, points of light here and there."""
    h, w = lv.shape
    for y in range(h):
        for x in range(w):
            a = sculk_amount(world[y, x])
            if a > threshold:
                spark = noise(seed + 17, x, y, 1)
                if a > threshold + 0.08 and spark > 965:
                    over.append((y, x, "spark", 1 + (spark > 990)))
                else:
                    over.append((y, x, "sculk", 3 + (1 if noise(seed + 19, x, y, 2) > 700 else 0)
                                 - (1 if a < threshold + 0.03 else 0)))
            elif a > threshold - 0.04:
                lv[y, x] -= 1                                          # the hide darkens where it's creeping in


# ---- painters (each returns a shade map on the zone's ramp, overlay pixels [(y, x, ramp, shade)], and an alpha map
# for cut-outs) ---------------------------------------------------------------------------------------------------------

def paint_hide(cube, face, w, h, seed, ctx):
    """The phantom's hide: mottled, leathery creases, the tops of masses catching light; torn and raw along the split
    down the middle of her head; sculk creeping over it."""
    lv, over = blank(cube, w, h)
    world = ctx["world"]
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 160, 860, 2)
            if noise(seed + 3, x, y, 3) > 900:
                lv[y, x] -= 1                                          # a darker blotch
    if face not in ("up", "down"):
        lv[0, :] += 1
        lv[h - 1, :] -= 1
    elif face == "up":
        lv += 1
    # leathery creases: short dark strokes with a lit edge
    for k in range(max(1, w * h // 90)):
        y0, x0 = noise(seed + 30 + k, 0, 0, 1) % h, noise(seed + 50 + k, 0, 0, 1) % w
        for t in range(min(4, w - x0)):
            yy = y0 + (t // 2)
            if yy < h:
                lv[yy, x0 + t] -= 1
                if yy + 1 < h:
                    lv[yy + 1, x0 + t] += 1
    # torn along the split between hide and skull (her head's middle, x near 0)
    if cube.group.name == "hi_head" or cube.name.startswith("hide_tatter"):
        for y in range(h):
            for x in range(w):
                d = world[y, x][0]
                rag = noise(seed + 61, x, y, 1) % 3
                if d < 1.0 + rag:
                    over.append((y, x, "flesh", 2 + (noise(seed + 62, x, y, 1) > 600)))
                elif d < 2.5 + rag:
                    lv[y, x] -= 2
    infest(lv, over, world, seed)
    return lv, over


def paint_hide_dark(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 200, 860, 2)
    lv[0, :] += 1
    infest(lv, over, ctx["world"], seed)
    return lv, over


def paint_belly(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 150, 870, 2)
            if y % 4 == 0:
                lv[y, x] -= 1                                          # the phantom's banded underside
    infest(lv, over, ctx["world"], seed, 0.7)
    return lv, over


def paint_bone(cube, face, w, h, seed, ctx):
    """Old bone: yellowed, pitted, cracked; darker towards its ends; sculk creeping over some of it."""
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 140, 880, 2)
            if noise(seed + 5, x, y, 1) > 970:
                lv[y, x] -= 2                                          # a pit
    lv[0, :] += 1
    # cracks: thin wandering dark lines
    for k in range(max(1, (w * h) // 120)):
        y, x = noise(seed + 40 + k, 0, 0, 1) % h, noise(seed + 70 + k, 0, 0, 1) % w
        for t in range(6):
            if 0 <= y < h and 0 <= x < w:
                lv[y, x] -= 2
            x += 1
            y += (noise(seed + 90 + k, t, 0, 1) % 3) - 1
    if cube.name == "skull" and face == "north":
        mid = w // 2
        for y in range(h):
            lv[y, mid + (noise(seed + 7, 0, y, 2) % 3) - 1] -= 2       # the suture down her bare forehead
    if cube.group.name in ("body", "hi_head") and not cube.name.startswith("crown"):
        infest(lv, over, ctx["world"], seed, 0.8)      # sculk only creeps onto her skull and ribs, sparingly
    return lv, over


def paint_flesh(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 220, 760, 2)
            if (x + y // 3) % 5 == 0:
                lv[y, x] += 1                                          # sinew
            if noise(seed + 9, x, y, 2) > 930:
                lv[y, x] += 2                                          # a wet glint
    return lv, over


# the tears: (along the span, along the chord, radius) in wing units, per side
HOLES = {1: [(13.5, 19, 4.5), (39, 13, 3.5), (46.5, 9, 6), (54, 22, 4), (75, 4, 5), (66, 12, 3)],
         -1: [(22.5, 25, 5), (31, 17, 3.5), (39, 11, 6), (61.5, 6, 4.5), (68.5, 10, 3.5), (49, 20, 3)]}


def torn(world, side, seed, trailing):
    """1 where the membrane is torn away (a hole, or a bite out of its trailing edge), so the sky shows through."""
    x, y, z = world
    s, c = abs(x) - W / 2, z - (FRONT + 2)
    if c < 3:
        return False                                                   # the leading edge along the spar holds
    for hs, hc, r in HOLES[side]:
        rag = 0.75 + 0.5 * smooth(seed, s * 2, c * 2, 2)
        if (s - hs) ** 2 + (c - hc) ** 2 < (r * rag) ** 2:
            return True
    return trailing - z < 2.2 * smooth(seed + 3, s, 0, 3) + 0.3


def paint_membrane(cube, face, w, h, seed, ctx):
    """Dark membrane, paler veins fanning from the shoulder, mottled; sculk at the wing's root; torn through."""
    lv, over = blank(cube, w, h)
    world = ctx["world"]
    side = 1 if world[0, 0][0] > 0 else -1
    trailing = cube.corners()[:, 2].max()
    alpha = np.full((h, w), 255, int)
    for y in range(h):
        for x in range(w):
            px, py, pz = world[y, x]
            s, c = abs(px) - W / 2, pz - (FRONT + 2)
            lv[y, x] += clusters(seed, x, y, 180, 880, 3)
            ang = math.degrees(math.atan2(c, s + 6))
            if abs((ang % 11) - 5.5) > 4.7:
                lv[y, x] += 1                                          # a vein
            if torn(world[y, x], side, 101 if side > 0 else 202, trailing):
                alpha[y, x] = 0
            elif torn((px + 0.8 * side, py, pz), side, 101 if side > 0 else 202, trailing) or \
                    torn((px, py, pz + 0.8), side, 101 if side > 0 else 202, trailing):
                lv[y, x] -= 2                                          # the ragged edge of a tear, dark and frayed
    if abs(world[0, 0][0]) < W / 2 + 20:
        infest(lv, over, world, seed, 0.72)                            # only at the wing's root
    return lv, over, alpha


def paint_feather(cube, face, w, h, seed, ctx):
    """An owl's feather: barred across, darker towards the tip, a paler quill line; one feather broken off."""
    lv, over = blank(cube, w, h)
    world = ctx["world"]
    base = np.array([0, LIFT, L / 2 + 9])
    alpha = np.full((h, w), 255, int)
    broken = cube.name.startswith("feather_1_")
    for y in range(h):
        for x in range(w):
            d = float(np.linalg.norm((world[y, x] - base)[[0, 2]]))
            lv[y, x] += clusters(seed, x, y, 200, 860, 2)
            if int(d) % 9 in (0, 1, 2):
                lv[y, x] -= 1                                          # the bars, soft and wide
            if face in ("up", "down") and (x == 0 or x == w - 1):
                lv[y, x] -= 1                                          # each feather's edge, so the fan reads
            if d > 30:
                lv[y, x] -= 1                                          # the darker tip
            if broken and d > 22 + 3 * smooth(seed, x, y, 2):
                alpha[y, x] = 0
    return lv, over, alpha


def paint_gill(cube, face, w, h, seed, ctx):
    """An axolotl's gill cut out of the plane: a glowing stalk down the middle, filaments fringing both edges, each
    raked back towards the tip, shorter as they go."""
    lv = np.zeros((h, w), int)
    alpha = np.zeros((h, w), int)
    if face not in ("north", "south"):
        return lv, [], alpha
    world = ctx["world"]
    pivot = v3.world_pivot(cube.group)
    length = float(cube.to[0] - cube.frm[0])
    mid = (h - 1) / 2
    for y in range(h):
        for x in range(w):
            t = float(np.linalg.norm(world[y, x] - pivot)) / length       # 0 at her head, 1 at the tip
            off = abs(y - mid)
            if off <= 0.6 + 0.4 * (1 - t):
                alpha[y, x], lv[y, x] = 255, 7 - int(2 * t)               # the stalk, brightest near the head
                continue
            reach = (mid + 0.5) * (1.05 - 0.6 * t)
            k = int(round(t * length * 2 - off))                          # filaments rake back along the stalk
            if off <= reach and k % 2 == 0 and t > 0.08:
                alpha[y, x] = 255
                lv[y, x] = 3 + (1 if off < reach * 0.5 else 0) + (1 if noise(seed, x, y, 1) > 800 else 0)
    return lv, [], alpha


def paint_sculk(cube, face, w, h, seed, ctx):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 200, 820, 1)
    return lv, over


def paint_glow(cube, face, w, h, seed, ctx):
    lv = np.zeros((h, w), int)
    base = ZONE[s4.zone_for(cube)][1]
    for y in range(h):
        for x in range(w):
            r = max(abs(x - (w - 1) / 2) / max(1, w / 2), abs(y - (h - 1) / 2) / max(1, h / 2))
            lv[y, x] = base + 2 - int(r * 2.5)
    return lv, []


def paint_plain(cube, face, w, h, seed, ctx):
    return blank(cube, w, h)


def painter_for(cube):
    return {"hide": paint_hide, "hide_dark": paint_hide_dark, "belly": paint_belly, "flesh": paint_flesh,
            "bone": paint_bone, "membrane": paint_membrane, "feather": paint_feather, "sculk": paint_sculk,
            "hole": paint_plain, "eye": paint_glow, "sculk_glow": paint_glow, "gill": paint_gill}[s4.zone_for(cube)]


def paint_face(model, i, face, w, h, solids):
    cube = model.cubes[i]
    seed = zlib.crc32(f"{cube.name}/{face}".encode())
    zone = s4.zone_for(cube)
    world, normal = world_points(cube, face, w, h)
    result = painter_for(cube)(cube, face, w, h, seed, {"world": world, "normal": normal})
    lv, over, alpha = result if len(result) == 3 else (*result, None)
    if not zone.startswith(GLOWING) and zone != "membrane":
        ao = b5.occlusion(model, i, face, w, h, solids)
        lv = lv - (ao >= 0.3) - (ao >= 0.55)
    out = c5.from_levels(lv, RAMP[ZONE[zone][0]], alpha)
    for y, x, rname, shade in over:
        if 0 <= y < h and 0 <= x < w and out[y, x, 3]:
            r = RAMP[rname]
            out[y, x, :3] = r[max(0, min(len(r) - 1, shade))]
    return out


def painted():
    """The rig, its islands and the painted atlas."""
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
    {"name": "wing", "location": (-7.5, 4.5, 6.5), "target": (-4.2, 0.6, 0.4), "scale": 6.5, "player": False},
    {"name": "tail", "location": (2.5, -9, 5.5), "target": (0, -3.6, 0.4), "scale": 5, "player": False},
    {"name": "flank", "location": (-6, 2.5, 2.2), "target": (0, 0.5, 0.8), "scale": 4.5, "player": False},
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
    atlas_path = OUT / "occultech_night_matriarch.png"
    atlas.save(atlas_path)
    atlas.resize((atlas.width * 2, atlas.height * 2), Image.NEAREST).save(OUT / "atlas_preview.png")
    bb, _ = s4.rig_bbmodel(model, keys, positions, atlas_path, height, s3.pose_table())
    path = OUT / f"{model.name}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    out = OUT / "renders"
    s4.render(model, bb, atlas_path, out, s4.VIEWS + CLOSE)
    glide = s2.build("glide_view")
    s2.finish(glide)
    s2.pose(glide, dict(s2.POSES["glide"][1], alt=128))
    s4.render(glide, bb, atlas_path, out, s4.BELOW)
    names = [v["name"] for v in s4.VIEWS + CLOSE + s4.BELOW]
    tw, th, pad, top, cols = 470, 352, 12, 56, 3
    rows = (len(names) + cols - 1) // cols
    img = Image.new("RGB", (pad + cols * (tw + pad), top + rows * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Night Matriarch - painted (session 5)", font=sheet._font(28), fill=sheet.INK)
    for n_, name in enumerate(names):
        x, y = pad + (n_ % cols) * (tw + pad), top + (n_ // cols) * (th + 34 + pad)
        img.paste(sheet._tile(out / f"{name}.png", tw, th), (x, y))
        dr.text((x, y + th + 6), name.replace("_", " "), font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "sheet.png")
    print(json.dumps({"atlas": [s4.SIZE, height], "rows_used": used, "islands": len(positions)}))


if __name__ == "__main__":
    main()
