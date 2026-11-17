"""The Tidebreaker redesign, session 1 step 3: the full blockout.

The picks (2026-11-08): take 2's Viking Longship, S2 the Dragon on the stem, and F3 for the head: a normal Minecraft
zombie, the growth further along, onto the helm's band and the collar. Three poses: idle, the ram and the throw.

Colours away from the face are blockout zones. The head's texel tiles are preview only: the real model paints them on
one cube.

Run from the repository root, with a folder holding the 26.2 zombie textures as the last argument:
python tools/art/bosses/tide_blockout.py [idle ram throw] [quick] <folder>
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import tide_faces as tf, tide_faces2 as tf2, tide_take2 as t2, volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/tidebreaker/overhaul/s1_blockout"
K = t2.K
NECK = np.array([0.0, 7.0, -17.0])             # stem top to jaw hinge: low and far out, so he stands in view above it


def f3_head(r, hip):
    """F3 on his shoulders: the study's bust collar lands on the body's own collar."""
    tf.H[:] = hip + (0, 19.0 * K, -0.4 * K)
    tf.TOP = tf.H + np.array([0, 4.8 * K, 0])
    tf2.viking(r, "F3")


def dragon(g, top):
    """S2 on the stem. Its neck starts inside the stem post."""
    tf.S[:] = top + NECK
    tf.dragon_head(g, ((0, -9, 18), (0, -5, 13), (0, -1, 8), (0, 2, 4)), 6.5)


VIEWS = t2.VIEWS + [
    {"name": "bow", "mode": "flat", "camera": "persp", "yaw": -32, "height": 3.6, "dist": 8.0, "target_z": 3.6,
     "player": False},
]
LABELS = dict(t2.LABELS, bow="the bow, close")


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(tf.PALETTE)
    poses = [p for p in argv if p in t2.POSES] or list(t2.POSES)
    for pose in poses:
        m = Model(f"tidebreaker_blockout_{pose}")
        t2.longship(m, pose, stem=dragon, head_fn=f3_head)
        v2.PALETTE.update(tf2.PAL)
        v2.run_blender(m.render_json(v2.PALETTE), OUT / pose, VIEWS)
        if pose == "idle":
            lo, hi = m.bounds()
            print("size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
    if "quick" in argv:
        return
    tw, th, pad, top = 380, 300, 12, 60
    img = Image.new("RGB", (pad + len(VIEWS) * (tw + pad), top + len(t2.POSES) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Tidebreaker: the full blockout", font=sheet._font(26), fill=sheet.INK)
    names = {"idle": "idle", "ram": "the ram", "throw": "the throw"}
    for r, pose in enumerate(t2.POSES):
        for c, v in enumerate(VIEWS):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / pose / f"{v['name']}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{names[pose]}: {LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "blockout.png")


if __name__ == "__main__":
    main(sys.argv[1:])
