"""The Mirrored Magus redesign, session 1 step 3: take 3, one design from the user's picks.

The user (2026-10-13) on take 2 (magus_take2.py):
- A's hat is the best looking: keep it, and make it even more floppy, with little bells at the ends;
- C's Venetian mask (the cracked grinning mask): keep it;
- the illager's nose came through the mask: either the smile goes below / round the nose, or no smile at all;
- longer legs, a smaller midbody, big shoes.

So: the mask has its own long nose, a sheath over the illager's (as Venetian masks do), and covers his chin; the grin
runs beneath the nose and curls up his cheeks; the crack runs from the brow down beside the nose. Stilt legs a third
longer, the torso shorter, big curled clown shoes with a bell. The hat: three long, floppy points, drooping heavily
down past his shoulders and swinging out, thinning to little gold bells.

Model units: 16 = one block, y up, his face towards -z. The blue figure is a player (1.8 blocks).

Run from the repository root: python tools/art/bosses/magus_take3.py
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
from bosses import magus_silhouettes as t1, magus_take2 as t2, volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/mirrored_magus/overhaul/s1_take3"
beam = t2.beam
HIP = 42.0                       # stilt legs: a third longer than take 2's
STRIPE, STRIPES = 5.4, 7


def body(m, pose):
    root = m.group("root", (0, 0, 0))
    for sx in (-1, 1):
        side = "left" if sx < 0 else "right"
        leg = root.group(f"leg_{side}", (sx * 3.4, HIP, 0))
        for i in range(STRIPES):
            leg.box(f"leg_{side}_{i}", (sx * 3.4, 4.5 + i * STRIPE + STRIPE / 2, 0), (4.4, STRIPE, 4.4),
                    "black" if (i + (sx > 0)) % 2 else "white")
        # big curled clown shoes
        leg.box(f"shoe_{side}", (sx * 3.6, 2.3, -4), (8, 4.6, 16), "black")
        leg.box(f"shoe_toe_{side}", (sx * 3.6, 3.2, -12.5), (6.5, 4, 4), "crimson")
        leg.box(f"shoe_curl_{side}", (sx * 3.6, 7.2, -14.2), (3.4, 6, 3.4), "crimson", rotation=(-30, 0, 0))
        leg.box(f"shoe_bell_{side}", (sx * 3.6, 10.8, -15.4), (2.6, 2.6, 2.6), "gold")
    hunch = {"idle": -14, "draw": -7}[pose]
    torso = root.group("torso", (0, HIP, 0), (hunch, 0, 0))
    h = HIP
    # a smaller midbody: the coat split black / white, a short skirt, crimson lining
    for sx in (-1, 1):
        torso.box(f"chest_{sx}", (sx * 3.6, h + 11, 0), (7.2, 15, 8.6), "black" if sx < 0 else "white")
        torso.box(f"skirt_{sx}", (sx * 4, h - 0.5, 0.5), (8, 9, 10.5), "white" if sx < 0 else "black")
    torso.box("lining", (0, h - 0.5, 0.5), (15, 8, 9.5), "crimson_dark")
    for i in range(10):                                        # the hem cut into hanging points
        a = math.radians(i * 36 + 18)
        torso.box(f"dag_{i}", (math.sin(a) * 8, h - 5.5, math.cos(a) * 5.6 + 0.5), (4, 4, 1.2),
                  "crimson" if i % 2 else "black", rotation=(0, math.degrees(a), 45))
    for i, (x, l) in enumerate(((-5, 18), (0, 24), (5, 18))):  # coat tails
        torso.box(f"tail_{i}", (x, h - 4 - l / 2, 5.8), (4.4, l, 1.2), "black" if i % 2 else "crimson")
        torso.box(f"tail_point_{i}", (x, h - 4 - l - 1.5, 5.8), (3, 3, 1.2), "black" if i % 2 else "crimson",
                  rotation=(0, 0, 45))
    for layer, (r, y, mat) in enumerate(((12, h + 19.5, "white"), (9.5, h + 22, "black"))):     # the ruff
        for i in range(10):
            a = math.radians(i * 36)
            torso.box(f"ruff_{layer}_{i}", (math.sin(a) * r * 0.85, y, math.cos(a) * r * 0.6), (7, 3.2, 3.6),
                      mat if i % 2 else ("crimson" if layer else "white"), rotation=(0, math.degrees(a), 0))
    arms = {"idle": {"left": (18, 0, -8), "right": (24, 0, 12)},
            "draw": {"left": (96, 0, -4), "right": (84, -34, 20)}}[pose]
    hands = {}
    sh = h + 17
    for sx in (-1, 1):
        side = "left" if sx < 0 else "right"
        arm = torso.group(f"arm_{side}", (sx * 9.6, sh, 0), arms[side])
        arm.box(f"puff_{side}", (sx * 9.6, sh - 2, 0), (7.4, 5, 7.4), "crimson")
        arm.box(f"sleeve_{side}", (sx * 9.6, sh - 10, 0), (5.2, 12, 5.2), "white" if sx < 0 else "black")
        arm.box(f"fore_{side}", (sx * 9.6, sh - 23, 0), (4.4, 14, 4.4), "black" if sx < 0 else "white")
        arm.box(f"cuff_{side}", (sx * 9.6, sh - 30.5, 0), (6.4, 3, 6.4), "crimson")
        arm.box(f"hand_{side}", (sx * 9.6, sh - 34, 0), (4.4, 4, 4.4), "skin")
        for j, dx in enumerate((-1.3, 0, 1.3)):                # long clawed fingers
            beam(arm, f"claw_{side}_{j}", (sx * 9.6 + dx, sh - 36, 0), (sx * 9.6 + dx * 1.6, sh - 44, -2.5), 1.0, "claw")
        hands[side] = tuple((arm.world_matrix() @ np.array([sx * 9.6, sh - 36, 0, 1.0]))[:3])
    neck = h + 25                                               # the head clear of the ruff, so the grin shows
    head = torso.group("head", (0, neck, 0), ({"idle": 12, "draw": 5}[pose], 0, {"idle": 14, "draw": 4}[pose]))
    yh = neck + 7.5
    head.box("head", (0, yh, 0), (12, 15, 12), "skin")
    head.box("nose", (0, yh - 5, -7.5), (3, 6, 3), "nose")
    return root, head, hands, yh


def venetian_mask(g, yh):
    """The cracked grinning mask (C's, take 2), made Venetian: it covers the face down past the chin, with its own long
    nose sheathing the illager's; the grin runs beneath the nose and curls up the cheeks; a crack from the brow down
    beside the nose; eye holes slanting up and out."""
    z = -6.8
    g.box("mask", (0, yh - 1.5, z), (13, 18, 1.4), "mask")
    g.box("mask_brow", (0, yh + 5.6, z - 0.7), (13.6, 2.2, 1.2), "mask")
    g.box("mask_nose", (0, yh - 5, -8.4), (4.2, 7.4, 4.2), "mask")              # sheathes the illager's nose
    g.box("mask_nose_tip", (0, yh - 8.6, -9.2), (3, 1.6, 2.6), "mask")
    for sx in (-1, 1):
        g.box(f"mask_eye_{sx}", (sx * 3.4, yh + 2.4, z - 0.8), (4.2, 1.5, 0.6), "mask_dark", rotation=(0, 0, -sx * 22))
    for i in range(11):                                       # the grin: under the nose tip, curling up the cheeks
        dx = -6.5 + i * 1.3
        if abs(dx) < 1.6:
            y = yh - 9.6
        else:
            y = yh - 9.6 + 0.1 * (abs(dx) - 1.6) ** 2 * 1.4
        g.box(f"mask_grin_{i}", (dx, y, z - 0.8), (1.5, 1.3, 0.6), "mask_dark")
    for i, (dx, dy) in enumerate(((-2.2, 6.5), (-2.8, 4), (-2.4, 1.5), (-3.2, -1), (-2.8, -3.5))):   # the crack
        g.box(f"mask_crack_{i}", (dx, yh + dy, z - 0.85), (0.6, 2.6, 0.5), "mask_dark")


def floppy_hat(head, yh):
    top = yh + 7.5
    head.box("hat_band", (0, top + 1.5, 0), (13.6, 3, 13.6), "crimson")
    head.box("hat_cap", (0, top + 4.5, 0.5), (12.4, 4, 12.4), "black")
    for i, (d, bend, mats) in enumerate((((-0.85, 1.0, 0.15), (-0.05, -0.62, 0.06), ("black", "crimson")),
                                         ((0.85, 1.0, 0.15), (0.05, -0.62, 0.06), ("white", "black")),
                                         ((0, 1.0, 0.9), (0, -0.62, 0.14), ("crimson", "white")))):
        p = np.array([d[0] * 4.4, top + 5, d[2] * 3.4])
        dd = np.array(d, float)
        for k in range(8):                                   # floppy: long, drooping hard, thinning to a cord
            dd = dd / np.linalg.norm(dd)
            q = p + dd * 5.4
            w = 6.6 - k * 0.65
            beam(head, f"hat_point_{i}_{k}", tuple(p), tuple(q), w, mats[k % 2])
            p = q
            dd = dd + np.array(bend)
        head.box(f"hat_bell_{i}", tuple(p + np.array([0, -1.4, 0])), (2.4, 2.4, 2.4), "gold")      # a little bell
        head.box(f"hat_bell_lip_{i}", tuple(p + np.array([0, -2.7, 0])), (3, 0.8, 3), "gold")


def build(pose):
    m = Model(f"magus3_{pose}")
    root, head, hands, yh = body(m, pose)
    floppy_hat(head, yh)
    venetian_mask(head, yh)
    t1.crystal_bow(root, hands["left"], "y", drawn=pose == "draw")
    return m


FACE = [{"name": "face", "mode": "flat", "camera": "persp", "yaw": 20, "height": 4.8, "dist": 3.2, "target_z": 4.6,
         "player": False}]


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(t2.PALETTE)
    for pose in ("idle", "draw"):
        m = build(pose)
        v2.run_blender(m.render_json(v2.PALETTE), OUT / pose, t1.VIEWS + (FACE if pose == "draw" else []))
        if pose == "idle":
            lo, hi = m.bounds()
            print(round(float(hi[1]) / 16, 2), "blocks tall")
    tw, th, pad, top = 400, 320, 12, 60
    img = Image.new("RGB", (pad + 4 * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Mirrored Magus take 3: A's floppy hat, C's Venetian mask, stilt legs, big shoes",
            font=sheet._font(26), fill=sheet.INK)
    for r, pose in enumerate(("idle", "draw")):
        for c, v in enumerate(t1.VIEWS):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / pose / f"{v['name']}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{pose}: {t1.LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "take3.png")


if __name__ == "__main__":
    main()
