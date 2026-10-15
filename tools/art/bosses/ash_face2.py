"""The Elder of Ash, session 1 step 2, take 2: the mixed face.

The user (2026-10-14): keep F3's angles (the wide eyes under one heavy brow ridge, low over its inner end) and its ember
markings, and add the Hermit's ash-white brows, but without hiding the eyes; the markings go on other areas too.
So the ash-white brows grow from the ridge's outer half and sweep out past the eye's outer corner, framing the eye
instead of covering it. Two amounts of markings:

  M1  the face and the front legs: under and beside the eyes, down the cheeks, a chevron on the chin, the mouth's
      corners, a mark between the eyes; bands round the forearms and upper arms, a stripe across each hand
  M2  M1 plus the body: stripes down the shoulders and flanks, along the glands, and up the back towards the volcano,
      as if the lava's heat had marked him

The frame (B2's front half) and the head come from ash_face.py.

Run from the repository root: python tools/art/bosses/ash_face2.py
"""
import json
import math
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import ash_face as f1  # noqa: E402

OUT = ROOT / "docs/art/bosses/elder_of_ash/overhaul/s1_face2"
beam = f1.beam
VARIANTS = {"M1": "the face and the front legs", "M2": "the face, the legs and the body"}


def ash_brows(h, sd, x, y, front):
    """Three ash-white tufts from the brow ridge's outer half, sweeping out past the eye's outer corner and drooping:
    they frame the eye from above and outside and never cross it (the eye spans x +-6 round its centre)."""
    for i, (ox, oy, ln, th, tilt) in enumerate(((1, 9.0, 19, 3.4, 8), (4, 7.4, 18, 3.0, -12), (7.5, 5.6, 15, 2.6, -30))):
        a = math.radians(tilt)
        cx = sd * (x + ox + ln / 2 * math.cos(a))
        cy = y + oy + ln / 2 * math.sin(a)
        h.box(f"brow_ash_{sd}_{i}", (cx, cy, front + 1.5 - i * 0.9), (ln, th, 6 - i),
              "brow_ash" if i < 2 else "brow_ash_dark", rotation=(0, 0, sd * tilt))


def band(g, name, a, b, t, w, d):
    """An ember band round a limb segment from a to b, at t along it (a short beam a little thicker than the limb)."""
    p = [a[i] + (b[i] - a[i]) * t for i in range(3)]
    q = [a[i] + (b[i] - a[i]) * (t + 0.07) for i in range(3)]
    beam(g, name, tuple(p), tuple(q), w + 0.8, "mark", d + 0.8)


def face_marks(h, x, y, front):
    for sd in (-1, 1):
        h.box(f"mark_under_{sd}", (sd * x, y - 5.0, front - 0.3), (12, 1.6, 0.4), "mark")
        h.box(f"mark_outer_{sd}", (sd * (x + 9.7), y - 0.5, front + 2.5), (0.4, 8, 5), "mark")
        h.box(f"mark_cheek_{sd}", (sd * (x + 4), 28.5, -59.2), (1.8, 10, 0.4), "mark", rotation=(0, 0, sd * -16))
        h.box(f"mark_corner_{sd}", (sd * 31.5, 15.8, -54.6), (1.6, 4.6, 0.4), "mark", rotation=(0, 0, sd * 8))
        h.box(f"mark_chin_{sd}", (sd * 3.6, 16.2, -56.2), (8.6, 1.6, 0.4), "mark", rotation=(0, 0, sd * 32))
    h.box("mark_brow", (0, 39.3, -50), (3.4, 0.4, 3.4), "mark", rotation=(0, 45, 0))


def arm_marks(root):
    for sd in (-1, 1):
        sh, el, wr = (sd * 36, 18, -16), (sd * 57, 15, -30), (sd * 52, 5, -44)
        g = root.group(f"arm_marks_{sd}", el)
        for i, t in enumerate((0.3, 0.55)):
            band(g, f"mark_fore_{sd}_{i}", el, wr, t, 14, 13)
        band(g, f"mark_upper_{sd}", sh, el, 0.62, 16, 15)
        g.box(f"mark_hand_{sd}", (sd * 52, 6.2, -48), (14, 0.4, 1.8), "mark")


def body_marks(root):
    b = root.group("body_marks", (0, 30, 0))
    for sd in (-1, 1):
        for i, (z, y, h, tilt) in enumerate(((-16, 30, 14, 14), (-2, 32, 16, 10), (12, 33, 14, 6))):
            b.box(f"mark_flank_{sd}_{i}", (sd * 44.2, y, z), (0.4, h, 1.8), "mark", rotation=(tilt, 0, 0))
        b.box(f"mark_shoulder_{sd}", (sd * 39, 38, -27.2), (1.8, 12, 0.4), "mark", rotation=(0, 0, sd * 12))
        b.box(f"mark_gland_{sd}", (sd * 29, 42.7, -26), (1.6, 0.4, 12), "mark")
        for i, x in enumerate((20, 30)):
            b.box(f"mark_back_{sd}_{i}", (sd * x, 54.2, -6 + i * 4), (1.8, 0.4, 12), "mark", rotation=(0, sd * -20, 0))


def build(model, key):
    root = model.group("root", (0, 0, 0))
    f1.bust(root)
    h = root.group("hi_head", (0, 26, -26))
    f1.head_base(h)
    x, y, z = f1.EYE_AT
    for sd in (-1, 1):
        front = f1.eye(h, sd, (sd * x, y, z), open_=0.85)
        h.box(f"brow_{sd}", (sd * (x + 0.5), y + 6.8, front + 2.6), (21, 3.6, 8), "brow", rotation=(-8, 0, sd * 11))
        ash_brows(h, sd, x, y, front)
    face_marks(h, x, y, z - 7.5)
    arm_marks(root)
    if key == "M2":
        body_marks(root)
    f1.pipe(h, "clenched")


VIEWS = [
    {"name": "front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 2.2, "dist": 7.5, "target_z": 2.0, "player": False},
    {"name": "three_quarter", "mode": "flat", "camera": "persp", "yaw": 38, "height": 3.0, "dist": 11, "target_z": 1.8,
     "player": False},
    {"name": "player_eye", "mode": "flat", "camera": "persp", "yaw": -18, "height": 1.62, "dist": 7.0, "target_z": 2.2,
     "lens": 28, "player": False},
    {"name": "side", "mode": "flat", "camera": "persp", "yaw": 70, "height": 2.6, "dist": 11, "target_z": 1.8, "player": False},
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for key in VARIANTS:
        out = OUT / key
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        model = Model(f"occultech_elder_of_ash_face2_{key.lower()}")
        build(model, key)
        model.write_bbmodel(out / f"{model.name}.bbmodel")
        f1.render(model, out, VIEWS)
        stats = model.stats()
        (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        print(key, stats["cubes"], stats["size_blocks"])
    sheet.compare_sheet(OUT, list(VARIANTS.items()), OUT / "faces.png",
                        heading="The Elder of Ash - the mixed face (step 2, take 2)",
                        views=("front", "three_quarter", "player_eye", "side"))


if __name__ == "__main__":
    main()
