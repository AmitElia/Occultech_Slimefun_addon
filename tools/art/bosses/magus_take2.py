"""The Mirrored Magus redesign, session 1 step 2: take 2 of the silhouettes.

The user rejected take 1 (magus_silhouettes.py, 2026-10-13): "a much better clown/jester hat", "a little scarier",
"the colours are wrong - think harlequin jester / magician / clown, but scary". Kept: tall and looming, vanilla's
Illusioner underneath, a theatre mask, the crystal-shard bow.

So, scarier through shape and colour:
- the harlequin's colours: black and bone white split down him, blood crimson, tarnished gold bells (the crystal bow
  keeps its icy cyan, the tier's light);
- a gaunt hunched lean, the head tilted to one side; very long arms ending in clawed fingers; stilt legs in black and
  white stripes; long curled shoes;
- a coat split black / white, its hem cut into hanging points (dagged), coat tails behind; a big two-layer ruff;
- a much bigger jester hat: heavy points thick at the base and tapering, arcing up and drooping, bells at the tips;
- the theatre mask: an exaggerated grin (or a weeping half), eye holes slanting.

Three takes on the hat and mask:
  A  the Grinning Jester   three long floppy points drooping past his shoulders like tentacles; a full mask, a grin
                           from ear to ear
  B  the Two-Faced         two huge points curling up and outward like horns; a split mask, grinning on one side,
                           weeping on the other
  C  the Crowned Fool      five points standing up round his head like a crown of flames, bells hanging; the grinning
                           mask cracked down the middle
Shown idle (the bow lowered, hunched) and drawing. Model units: 16 = one block, y up, his face towards -z. The blue
figure is a player (1.8 blocks). Colours are the proposed palette, flat.

Run from the repository root: python tools/art/bosses/magus_take2.py
"""
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import magus_silhouettes as t1, volley_crone_s2 as v2, volley_s1 as v1  # noqa: E402

OUT = ROOT / "docs/art/bosses/mirrored_magus/overhaul/s1_take2"
PALETTE = {
    "black": (24, 20, 28), "white": (222, 214, 196), "crimson": (138, 18, 32), "crimson_dark": (82, 10, 22),
    "skin": (118, 124, 126), "nose": (100, 106, 108), "mask": (232, 226, 210), "mask_dark": (16, 12, 18),
    "gold": (176, 140, 60), "crystal": (150, 230, 250), "crystal_dark": (90, 160, 210), "string": (230, 240, 255),
    "claw": (40, 34, 40), "tear": (40, 30, 60),
}


def beam(g, name, a, b, w, mat):
    return v1.beam(g, name, a, b, w, mat)


def point(g, name, base, direction, bend, segs, seg_len, w0, w1, mats, bell=True):
    """A jester hat's point: tapering segments from a thick base, the direction turning by `bend` each segment."""
    p = np.array(base, float)
    d = np.array(direction, float)
    for k in range(segs):
        d = d / np.linalg.norm(d)
        q = p + d * seg_len
        w = w0 + (w1 - w0) * k / max(1, segs - 1)
        beam(g, f"{name}_{k}", tuple(p), tuple(q), w, mats[k % len(mats)])
        p = q
        d = d + np.array(bend, float)
    if bell:
        g.box(f"{name}_bell", tuple(p + np.array([0, -2, 0])), (3.6, 3.6, 3.6), "gold")
        g.box(f"{name}_bell_lip", tuple(p + np.array([0, -3.9, 0])), (4.4, 1, 4.4), "gold")


# ---- the body ---------------------------------------------------------------------------------------------------------

def body(m, pose):
    root = m.group("root", (0, 0, 0))
    for sx in (-1, 1):
        side = "left" if sx < 0 else "right"
        leg = root.group(f"leg_{side}", (sx * 3.4, 30, 0))
        for i in range(5):                                       # stilt legs in black and white stripes
            leg.box(f"leg_{side}_{i}", (sx * 3.4, 4 + i * 5.4 + 2.7, 0), (4.4, 5.4, 4.4),
                    "black" if (i + (sx > 0)) % 2 else "white")
        leg.box(f"shoe_{side}", (sx * 3.4, 1.5, -3), (5, 3, 11), "black")
        leg.box(f"shoe_curl_{side}", (sx * 3.4, 4.5, -9.5), (2.4, 5, 2.4), "crimson", rotation=(-35, 0, 0))
        leg.box(f"shoe_bell_{side}", (sx * 3.4, 7.5, -10.5), (2.2, 2.2, 2.2), "gold")
    hunch = {"idle": -16, "draw": -8}[pose]
    torso = root.group("torso", (0, 30, 0), (hunch, 0, 0))
    # the coat, split black / white down the middle, crimson lining
    for sx in (-1, 1):
        torso.box(f"chest_{sx}", (sx * 3.75, 42, 0), (7.5, 22, 9), "black" if sx < 0 else "white")
        torso.box(f"skirt_{sx}", (sx * 4.25, 25, 0.5), (8.5, 12, 11), "white" if sx < 0 else "black")
    torso.box("lining", (0, 25, 0.5), (16, 11, 10), "crimson_dark")
    # the hem cut into hanging points all round (dagged), alternating colours
    for i in range(10):
        a = math.radians(i * 36 + 18)
        x, z = math.sin(a) * 8.6, math.cos(a) * 5.8
        torso.box(f"dag_{i}", (x, 17.5, z + 0.5), (4.2, 4.2, 1.2), "crimson" if i % 2 else "black",
                  rotation=(0, math.degrees(a), 45))
    for i, (x, l) in enumerate(((-5, 22), (0, 28), (5, 22))):    # coat tails at the back
        torso.box(f"tail_{i}", (x, 19 - l / 2, 6), (4.5, l, 1.2), "black" if i % 2 else "crimson")
        torso.box(f"tail_point_{i}", (x, 19 - l - 1.5, 6), (3, 3, 1.2), "black" if i % 2 else "crimson",
                  rotation=(0, 0, 45))
    # a big two-layer ruff
    for layer, (r, y, mat) in enumerate(((12, 53, "white"), (9.5, 55.5, "black"))):
        for i in range(10):
            a = math.radians(i * 36)
            torso.box(f"ruff_{layer}_{i}", (math.sin(a) * r * 0.85, y, math.cos(a) * r * 0.6), (7, 3.2, 3.6),
                      mat if i % 2 else ("crimson" if layer else "white"), rotation=(0, math.degrees(a), 0))
    # very long arms, clawed hands
    arms = {"idle": {"left": (18, 0, -8), "right": (24, 0, 12)},
            "draw": {"left": (96, 0, -4), "right": (84, -34, 20)}}[pose]
    hands = {}
    for sx in (-1, 1):
        side = "left" if sx < 0 else "right"
        arm = torso.group(f"arm_{side}", (sx * 10, 50, 0), arms[side])
        arm.box(f"sleeve_{side}", (sx * 10, 43, 0), (5.4, 14, 5.4), "white" if sx < 0 else "black")
        arm.box(f"puff_{side}", (sx * 10, 48, 0), (7.4, 5, 7.4), "crimson")
        arm.box(f"fore_{side}", (sx * 10, 28, 0), (4.4, 16, 4.4), "black" if sx < 0 else "white")
        arm.box(f"cuff_{side}", (sx * 10, 21, 0), (6.4, 3, 6.4), "crimson")
        arm.box(f"hand_{side}", (sx * 10, 17.5, 0), (4.4, 4, 4.4), "skin")
        for j, dx in enumerate((-1.3, 0, 1.3)):                  # long clawed fingers
            beam(arm, f"claw_{side}_{j}", (sx * 10 + dx, 15.5, 0), (sx * 10 + dx * 1.6, 7, -2.5), 1.0, "claw")
        hands[side] = tuple((arm.world_matrix() @ np.array([sx * 10, 15, 0, 1.0]))[:3])
    head = torso.group("head", (0, 54, 0), ({"idle": 14, "draw": 6}[pose], 0, {"idle": 14, "draw": 4}[pose]))
    head.box("head", (0, 61.5, 0), (12, 15, 12), "skin")
    head.box("nose", (0, 56.5, -7.5), (3, 6, 3), "nose")
    return root, torso, head, hands


# ---- the masks ---------------------------------------------------------------------------------------------------------

def mask_grin(g, x, y, z, w=13, cracked=False):
    g.box("mask", (x, y, z), (w, 14, 1.4), "mask")
    g.box("mask_cheeks", (x, y - 1.5, z - 0.6), (w - 2, 3, 1.0), "mask")
    for sx in (-1, 1):                                            # eye holes slanting up and out
        g.box(f"mask_eye_{sx}", (x + sx * 3.2, y + 2.6, z - 0.8), (4, 1.5, 0.6), "mask_dark", rotation=(0, 0, -sx * 22))
    for i in range(9):                                            # a grin from ear to ear, curving up
        dx = -6 + i * 1.5
        g.box(f"mask_grin_{i}", (x + dx, y - 3.8 + (dx * dx) * 0.06, z - 0.8), (1.7, 1.3, 0.6), "mask_dark")
    if cracked:
        for i, (dx, dy) in enumerate(((0.5, 5.5), (-0.4, 3), (0.6, 0.5), (-0.3, -2), (0.4, -4.5))):
            g.box(f"mask_crack_{i}", (x + dx, y + dy, z - 0.85), (0.6, 2.6, 0.5), "mask_dark")


def mask_split(g, x, y, z):
    """Grinning on her right, weeping on the left: one mask, two faces."""
    g.box("mask", (x, y, z), (13, 14, 1.4), "mask")
    g.box("mask_eye_r", (x + 3.2, y + 2.6, z - 0.8), (4, 1.5, 0.6), "mask_dark", rotation=(0, 0, -22))
    g.box("mask_eye_l", (x - 3.2, y + 2.2, z - 0.8), (4, 1.5, 0.6), "mask_dark", rotation=(0, 0, -22))
    for i in range(4):                                            # the grin, right half
        dx = 1 + i * 1.5
        g.box(f"mask_grin_{i}", (x + dx, y - 3.8 + dx * dx * 0.07, z - 0.8), (1.7, 1.3, 0.6), "mask_dark")
    for i in range(4):                                            # the frown, left half
        dx = -1 - i * 1.5
        g.box(f"mask_frown_{i}", (x + dx, y - 3.4 - dx * dx * 0.07, z - 0.8), (1.7, 1.3, 0.6), "mask_dark")
    g.box("mask_tear", (x - 3.6, y - 1, z - 0.8), (1, 4, 0.5), "tear")
    g.box("mask_split", (x, y, z - 0.85), (0.5, 14, 0.4), "mask_dark")


# ---- the hats ----------------------------------------------------------------------------------------------------------

def hat_band(head, y=69.5):
    head.box("hat_band", (0, y, 0), (13.6, 3, 13.6), "crimson")
    head.box("hat_cap", (0, y + 3, 0.5), (12.4, 4, 12.4), "black")


def hat_tentacles(head):
    hat_band(head)
    for i, (d, bend, mats) in enumerate((((-0.8, 1.0, 0.2), (-0.1, -0.45, 0.05), ("black", "crimson")),
                                         ((0.8, 1.0, 0.2), (0.1, -0.45, 0.05), ("white", "black")),
                                         ((0, 1.0, 0.8), (0, -0.45, 0.15), ("crimson", "white")))):
        point(head, f"hat_point_{i}", (d[0] * 4, 73, d[2] * 3), d, bend, 6, 6.2, 6.5, 2.4, mats)


def hat_horns(head):
    hat_band(head)
    for i, sx in enumerate((-1, 1)):
        point(head, f"hat_horn_{i}", (sx * 4, 73, 0), (sx * 0.45, 1, 0.1), (sx * 0.32, -0.12, 0), 7, 6.0, 7.5, 2.2,
              ("black", "white") if sx < 0 else ("white", "black"))


def hat_crown(head):
    hat_band(head)
    for i in range(5):
        a = math.radians(-60 + i * 30)
        d = (math.sin(a) * 0.55, 1.0, -0.15 + abs(math.sin(a)) * 0.1)
        point(head, f"hat_crown_{i}", (math.sin(a) * 5, 73, 0), d, (math.sin(a) * 0.12, -0.08, 0.05), 4, 5.2, 4.5, 1.8,
              ("crimson", "black") if i % 2 else ("black", "white"))


TAKES = {
    "A": ("The Grinning Jester", hat_tentacles, "grin"),
    "B": ("The Two-Faced", hat_horns, "split"),
    "C": ("The Crowned Fool", hat_crown, "cracked"),
}


def build(key, pose):
    title, hat, mask = TAKES[key]
    m = Model(f"magus2_{key}_{pose}")
    root, torso, head, hands = body(m, pose)
    hat(head)
    if mask == "split":
        mask_split(head, 0, 62, -6.8)
    else:
        mask_grin(head, 0, 62, -6.8, cracked=mask == "cracked")
    t1.crystal_bow(root, hands["left"], "y", drawn=pose == "draw")
    return m, title


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    views = t1.VIEWS
    for key in TAKES:
        for pose in ("idle", "draw"):
            m, title = build(key, pose)
            v2.run_blender(m.render_json(v2.PALETTE), OUT / key / pose, views)
            if pose == "idle":
                lo, hi = m.bounds()
                print(key, title, round(float(hi[1]) / 16, 2), "blocks tall")
        tw, th, pad, top = 400, 320, 12, 60
        img = Image.new("RGB", (pad + 4 * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Mirrored Magus take 2 - {key}: {TAKES[key][0]}", font=sheet._font(26), fill=sheet.INK)
        for r, pose in enumerate(("idle", "draw")):
            for c, v in enumerate(views):
                x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
                img.paste(sheet._tile(OUT / key / pose / f"{v['name']}.png", tw, th), (x, y))
                dr.text((x, y + th + 6), f"{pose}: {t1.LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / f"{key}_{TAKES[key][0].lower().replace(' ', '_').replace('-', '_')}.png")


if __name__ == "__main__":
    main()
