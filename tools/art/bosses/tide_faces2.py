"""The Tidebreaker redesign, session 1 step 2, round 2: a normal Minecraft zombie under the helmet.

The review (2026-11-08): S2, the Dragon, is the serpent. None of the Viking faces: he should be a normal Minecraft
zombie with little barnacles growing on him, like the Flying Dutchman's crew. There the face stays readable and the
growth gathers in patches at its edges (cheek, jaw, temple), big shells in the middle of a patch and small ones
scattered round it, the skin stained where it spreads.

The head is vanilla's: 8 x 8 x 8 at 1.45 times, every texel a tile coloured from the real 26.2 skin (preview only; the
real model paints these on one cube). The barnacles are low stepped cones a texel or so across, packed by a seeded
scatter that keeps clear of the eyes and mouth, and the crust under them is painted into the skin.
  F1  zombie skin, a light growth: one cheek and the opposite temple
  F2  drowned skin, the same light growth (the vanilla mob the boss really is)
  F3  zombie skin, further along: the jaw and side of the head, onto the helm and the collar

Run from the repository root after extracting zombie.png and drowned.png from the 26.2 client into SKINS:
python tools/art/bosses/tide_faces2.py [F1 F2 F3]
"""
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import tide_faces as tf, volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/tidebreaker/overhaul/s1_faces2"
SKINS = Path(sys.argv[-1]) if len(sys.argv) > 1 and Path(sys.argv[-1]).is_dir() else OUT
K = tf.K
H = tf.H
tf.TOP = H + np.array([0, 4.8 * K, 0])          # the 8-tall vanilla head: the band sits over its top row only
UV = {"front": (8, 8), "right": (0, 8), "left": (16, 8), "back": (24, 8)}
PAL = dict(tf.PALETTE, b_big=(156, 154, 132), b_mid=(128, 130, 110), b_dark=(98, 104, 88), b_hole=(58, 62, 54))
CRUST = (86, 94, 76)
CHALK = (146, 144, 122)
# (face, column, row, reach in texels, how many shells); column 0 is the image's left of that face
GROWTH = {
    "F1": [("front", 0.9, 6.0, 1.5, 12), ("front", 7.0, 1.9, 1.0, 6), ("right", 6.4, 5.8, 1.4, 9)],
    "F3": [("front", 0.9, 6.0, 1.8, 16), ("front", 3.0, 7.2, 1.3, 8), ("front", 7.0, 1.9, 1.2, 8),
           ("right", 5.2, 5.2, 2.6, 26), ("left", 1.6, 6.2, 1.4, 10)],
}
GROWTH["F2"] = GROWTH["F1"]
SKIN = {"F1": "zombie.png", "F2": "drowned.png", "F3": "zombie.png"}
CLEAR = {"front": [(1.5, 4.0, 1.5), (5.5, 4.0, 1.5), (3.5, 5.8, 1.5)]}        # the eyes and the mouth stay bare


def point(face, c, r, out=0.0):
    """Where a spot on the head is: columns and rows in texels from the face's top left, seen from outside."""
    u, v = (3.5 - c + 0.5 - 0.5) * K, (3.5 - r) * K
    f = 4 * K + out
    return {"front": H + (u, v, -f), "back": H + (-u, v, f), "right": H + (f, v, u), "left": H + (-f, v, -u)}[face]


def flat(face, a, t):
    return (a, a, t) if face in ("front", "back") else (t, a, a)


def shell(g, name, face, c, r, a, rng):
    """One barnacle: a low plate and a smaller cap set off its centre, so a patch reads rough, not as squares inside
    squares. Only the biggest show a small opening; on the rest it is texture."""
    dc, dr = rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12)
    g.box(name, tuple(point(face, c, r, 0.25)), flat(face, a, 0.5), "b_big" if a > 1.2 else "b_mid")
    g.box(name + "_b", tuple(point(face, c + dc, r + dr, 0.65)), flat(face, a * 0.62, 0.4), "b_mid" if a > 1.2 else "b_dark")
    if a > 1.6:
        g.box(name + "_h", tuple(point(face, c + dc, r + dr, 0.88)), flat(face, a * 0.26, 0.08), "b_hole")


def scatter(rng, c, r, reach, n, face):
    """Shells round a patch's centre, biggest in the middle, none touching, none over the eyes or mouth."""
    placed = []
    tries = 0
    while len(placed) < n and tries < n * 80:
        tries += 1
        d = abs(rng.gauss(0, reach * 0.55))
        ang = rng.uniform(0, 6.283)
        x, y = c + d * np.cos(ang), r + d * np.sin(ang)
        if not (0.1 < x < 7.9 and 0.9 < y < 7.9):
            continue
        if any(np.hypot(x - a, y - b) < q for a, b, q in CLEAR.get(face, ())):
            continue
        a = (1.9 if d < reach * 0.32 else 1.3 if d < reach * 0.7 else 0.85) * rng.uniform(0.88, 1.08)
        if all(np.hypot(x - px, y - py) * K > (a + pa) * 0.52 for px, py, pa in placed):
            placed.append((x, y, a))
    return placed


def tiles(g, key, skin, patches):
    rng = random.Random(7)
    for face, (u0, v0) in UV.items():
        for r in range(8):
            for c in range(8):
                col = np.array(skin[v0 + r, u0 + c][:3], float)
                hit = 0.0
                for f, pc, pr, reach, _ in patches:
                    if f == face:
                        d = np.hypot(c - pc + 0.5 - 0.5, r - pr)
                        hit = max(hit, 1 - d / (reach + 0.9) + rng.uniform(-0.18, 0.18))
                if any(np.hypot(c - a, r - b) < q for a, b, q in CLEAR.get(face, ())):
                    hit = 0
                if hit > 0:
                    col = col + (np.array(CHALK if hit > 0.55 else CRUST, float) - col) * min(0.8, 0.45 + hit * 0.5)
                name = "tx_%02x%02x%02x" % tuple(int(v) for v in col)
                PAL[name] = tuple(int(v) for v in col)
                g.box(f"{face}_{r}_{c}", tuple(point(face, c, r, 0.03)), flat(face, K, 0.06)
                      if face in ("front", "back") else flat(face, K, 0.06), name)


def viking(g, key):
    skin = np.array(Image.open(SKINS / SKIN[key]).convert("RGBA"))
    if key == "F2":                                           # the drowned's face is on its outer layer: lay it over
        over = np.array(Image.open(SKINS / "drowned_outer_layer.png").convert("RGBA"))
        hat = over[8:16, 32:64]
        region = skin[8:16, 0:32]
        region[hat[..., 3] > 0] = hat[hat[..., 3] > 0]
    g.box("head", tuple(H), (8 * K - 0.1, 8 * K - 0.1, 8 * K - 0.1), "skin_dark")
    tiles(g, key, skin, GROWTH[key])
    tf.bust(g)
    tf.dome(g)
    for s in (-1, 1):
        tf.horn(g, f"horn_{s}", [(s * x, y, z) for x, y, z in tf.OX], 2.9)
    rng = random.Random(hash(key) % 1000 if False else {"F1": 3, "F2": 3, "F3": 11}[key])
    for i, (face, c, r, reach, n) in enumerate(GROWTH[key]):
        for j, (x, y, a) in enumerate(scatter(rng, c, r, reach, n, face)):
            shell(g, f"b{i}_{j}", face, x, y, a, rng)
    if key == "F3":                                           # the growth carrying on over the helm and the collar
        x0, y0, z0 = tf.TOP
        for i, (dx, dy, a) in enumerate(((5.0, -1.1, 1.8), (6.1, -0.8, 1.2), (4.0, -1.5, 1.1), (6.6, -1.4, 0.9))):
            g.box(f"helm_b{i}", (x0 + dx - 1.0 + 0.0, y0 + dy, z0 - 4.85 * K - 0.25), (a, a, 0.5), "b_big")
            g.box(f"helm_b{i}_h", (x0 + dx - 1.0, y0 + dy, z0 - 4.85 * K - 0.6), (a * 0.6, a * 0.6, 0.3), "b_mid")
        for i, (x, y, a) in enumerate(((4.1, -6.6, 2.0), (3.0, -6.0, 1.3), (5.0, -7.2, 1.2), (2.4, -7.2, 0.9))):
            g.box(f"collar_b{i}", tuple(H + np.array((x, y, -3.3)) * K + (0, 0, -0.3)), (a, a, 0.7), "b_big")
            g.box(f"collar_b{i}_h", tuple(H + np.array((x, y, -3.3)) * K + (0, 0, -0.75)), (a * 0.6, a * 0.6, 0.3), "b_mid")


TITLES = {"F1": "Zombie, light growth", "F2": "Drowned skin, light growth", "F3": "Zombie, further along"}


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    keys = [a for a in argv if a in TITLES] or list(TITLES)
    for key in keys:
        m = Model("tide_" + key)
        viking(m.group("root", (0, 0, 0)), key)
        v2.PALETTE.update(PAL)
        v2.run_blender(m.render_json(v2.PALETTE), OUT / key, tf.views(3.0))
        print(key, TITLES[key], "cubes", len(m.cubes))
    tw, th, pad, top = 400, 320, 12, 60
    vs = tf.views(1)
    img = Image.new("RGB", (pad + len(vs) * (tw + pad), top + 3 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Tidebreaker: a normal zombie, with a little growth", font=sheet._font(26), fill=sheet.INK)
    for r, k in enumerate(TITLES):
        for c, v in enumerate(vs):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / k / f"{v['name']}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{k} {TITLES[k]}: {tf.LAB[v['name']]}", font=sheet._font(16), fill=sheet.DIM)
    img.save(OUT / "zombie_faces.png")


if __name__ == "__main__":
    main(sys.argv[1:])
