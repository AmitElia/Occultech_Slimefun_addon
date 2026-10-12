"""Mire Monarch redesign, step 2: the face study on the Brute (posture B, picked 2026-10-11).

Three faces on the same front half of the Brute (the shoulder yoke, the huge forearms, the glands), so each face is
judged in the frame it will live in. Shared by all three: a jaw as wide as the head under an overbite, the mouth
corners turned down, glow kept to the eyes, the gland splits and the mouth, a tiny crown between the eyes, few parts.

  F1  The Hooded Glare   a heavy V-shaped brow shelf; the eyes are thin glowing slits deep in its shadow; the mouth
                         shut in a hard frown under a thick upper lip.
  F2  The Toad's Scowl   the toad's own bulging eyes kept on top of the head (the vanilla frog's placement), but
                         half-shut under thick angry lids; the lower half glows round a dark horizontal pupil.
  F3  The Open Maw       the jaw hangs open on a dark mouth with the tongue coiled inside, glowing; bony crests
                         (a cane toad's) run back from the crown over small, deep-set glowing eyes.

Run from the repository root: python tools/art/bosses/monarch_face.py
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import monarch_s1 as m1, volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/mire_monarch/overhaul/s1_face"
PALETTE = {
    "skin": (58, 68, 38), "skin_dark": (42, 50, 28), "jaw": (66, 74, 42), "bone": (128, 122, 92),
    "maw": (22, 12, 10), "shade": (18, 20, 14), "lid": (66, 76, 42),
    "glow": (176, 255, 40), "hot": (214, 255, 110), "glow_hot": (214, 255, 110), "pupil": (16, 12, 10), "tongue": (150, 220, 40),
    "wart": (74, 80, 46), "gold": (226, 172, 44), "gold_dark": (156, 108, 26), "gem": (120, 255, 60),
}
FACES = {"F1": "The Hooded Glare", "F2": "The Toad's Scowl", "F3": "The Open Maw"}


def tiny_crown(g, x, y, z, w=8):
    """The tiny crown between the eyes: a band, three diamond points along the front, a lime stone."""
    c = g.group("crown", (x, y, z))
    c.box("crown_band", (x, y + 1.5, z), (w, 3, w * 0.8), "gold")
    for i in (-1, 0, 1):
        s = 3.2 if i == 0 else 2.6
        c.box(f"crown_pt{i}", (x + i * w * 0.36, y + 3, z - w * 0.2), (s, s, 1.4), "gold", rotation=(0, 0, 45))
        c.box(f"crown_back{i}", (x + i * w * 0.36, y + 3, z + w * 0.25), (s * 0.8, s * 0.8, 1.2), "gold_dark",
              rotation=(0, 0, 45))
    c.box("crown_gem", (x, y + 1.6, z - w * 0.4 - 0.6), (2.2, 2.2, 1), "gem", rotation=(0, 0, 45))


def body(root):
    """The front half of the Brute, the same for every face: the shoulder yoke, the forearms, the glands."""
    b = root.group("body", (0, 40, 0))
    m1.octo(b, "yoke", (0, 48, -4), (70, 26, 34), "skin", 0.4)
    m1.octo(b, "chest", (0, 30, -14), (50, 26, 22), "skin_dark", 0.35)
    for sd in (-1, 1):
        m1.wart(b, f"wart_{sd}", (sd * 14, 62, -2), 8, (0, sd * 10, -sd * 10))
        m1.gland(b, f"gland_{sd}", (sd * 22, 54, -18), (13, 9, 20), sd * -12)
        arm = root.group(f"arm_{sd}", (sd * 34, 48, -8))
        m1.tapered(arm, f"arm_{sd}_upper", (sd * 34, 48, -8), (sd * 46, 24, -6), 20, 17, "skin")
        m1.tapered(arm, f"arm_{sd}_fore", (sd * 46, 24, -6), (sd * 42, 4, -26), 17, 15, "skin")
        arm.box(f"arm_{sd}_hand", (sd * 42, 2.5, -32), (22, 5, 20), "skin_dark", rotation=(0, sd * -12, 0))
    return b


def head_base(h, jaw_open=0.0):
    """The head: a broad skull with an overbite over a jaw as wide as it, the mouth line between them, the upper
    lip's corners hanging down (the frown). jaw_open: degrees the jaw swings down on its hinge."""
    m1.octo(h, "skull", (0, 28, -34), (52, 18, 30), "skin", 0.3)
    m1.octo(h, "snout", (0, 24, -47), (48, 10, 4), "skin", 0.3)          # the overbite: the lip overhangs the jaw
    jaw = h.group("jaw", (0, 16, -20), (jaw_open, 0, 0))
    m1.octo(jaw, "jaw_mass", (0, 13, -33), (46, 10, 28), "jaw", 0.32)
    h.box("mouth", (0, 18.5, -33), (47, 3, 27), "maw")                     # the mouth line, recessed
    # the frown, drawn on the front of the face: the mouth line runs straight across, then turns down at each corner
    h.box("mouth_front", (0, 19, -49.2), (30, 3, 1), "maw")
    for sd in (-1, 1):
        h.box(f"mouth_corner_{sd}", (sd * 19.5, 16.6, -49.2), (11, 3, 1), "maw", rotation=(0, 0, sd * 28))

    return jaw


def hooded_glare(model):
    root = model.group("root", (0, 0, 0))
    body(root)
    h = root.group("hi_head", (0, 28, -24))
    head_base(h)
    for sd in (-1, 1):
        # a heavy brow shelf in a V: the inner ends dip, the shelf juts out over the eyes
        h.box(f"brow_{sd}", (sd * 13, 37.5, -44), (26, 6, 14), "skin_dark", rotation=(0, 0, sd * 14))
        h.box(f"socket_{sd}", (sd * 13, 32, -48.6), (14, 6, 2), "shade", rotation=(0, 0, sd * 14))
        h.box(f"eye_{sd}", (sd * 13, 32, -49.4), (10, 1.8, 1), "glow", rotation=(0, 0, sd * 14))
        h.box(f"eye_hot_{sd}", (sd * 12.5, 32.1, -49.9), (4, 1, 0.6), "hot", rotation=(0, 0, sd * 14))
    tiny_crown(h, 0, 37, -40)


def toads_scowl(model):
    root = model.group("root", (0, 0, 0))
    body(root)
    h = root.group("hi_head", (0, 28, -24))
    head_base(h)
    for sd in (-1, 1):
        # the toad's bulging eye on the front corner of the head, half shut under a thick angry lid
        m1.octo(h, f"eye_{sd}", (sd * 15, 41, -40), (14, 11, 13), "glow", 0.3)
        h.box(f"pupil_{sd}", (sd * 15, 39.6, -46.8), (9, 2, 1), "pupil")
        h.box(f"lid_{sd}", (sd * 15, 46.5, -40.5), (17, 7, 15), "lid", rotation=(-8, 0, sd * 20))
        h.box(f"lid_rim_{sd}", (sd * 14.5, 43.2, -47.4), (16, 2.4, 2), "skin_dark", rotation=(0, 0, sd * 20))
    tiny_crown(h, 0, 37, -44, 7)


def open_maw(model):
    root = model.group("root", (0, 0, 0))
    body(root)
    h = root.group("hi_head", (0, 28, -24))
    jaw = head_base(h, jaw_open=14)
    h.box("throat", (0, 15, -30), (40, 8, 22), "maw")                         # the dark inside of the open mouth
    jaw.box("tongue", (0, 15.5, -34), (18, 3, 20), "tongue")                  # the tongue coiled on the jaw floor
    jaw.box("tongue_tip", (0, 16.5, -44), (12, 5, 6), "glow")
    for sd in (-1, 1):                                                        # toxic drips off the lip corners
        h.box(f"drool_{sd}", (sd * 22, 12, -47.5), (1.6, 7 + (sd > 0) * 3, 1.6), "glow")
    for sd in (-1, 1):
        # cane-toad crests: bony ridges from the crown back over the eyes to the glands
        h.box(f"crest_{sd}", (sd * 9, 38.5, -36), (5, 4, 22), "skin_dark", rotation=(0, sd * -18, 0))
        h.box(f"crest_knob_{sd}", (sd * 14, 38.5, -45), (9, 5, 6), "skin_dark", rotation=(0, 0, sd * 14))
        h.box(f"socket_{sd}", (sd * 16, 33.5, -45.5), (11, 6, 6), "shade", rotation=(0, 0, sd * 12))
        h.box(f"eye_{sd}", (sd * 16, 33.5, -48.8), (7, 3.4, 1), "glow", rotation=(0, 0, sd * 12))
        h.box(f"eye_hot_{sd}", (sd * 16, 33.5, -49.3), (3, 1.6, 0.6), "hot", rotation=(0, 0, sd * 12))
    tiny_crown(h, 0, 37, -42, 7)


BUILD = {"F1": hooded_glare, "F2": toads_scowl, "F3": open_maw}
VIEWS = [
    {"name": "front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 2.0, "dist": 7, "target_z": 1.7, "player": False},
    {"name": "three_quarter", "mode": "flat", "camera": "persp", "yaw": 38, "height": 2.6, "dist": 7, "target_z": 1.8,
     "player": False},
    {"name": "player_eye", "mode": "flat", "camera": "persp", "yaw": -14, "height": 1.62, "dist": 4.5, "target_z": 2.0,
     "lens": 24, "player": False},
    {"name": "side", "mode": "flat", "camera": "persp", "yaw": 90, "height": 2.0, "dist": 7, "target_z": 1.8, "player": False},
    {"name": "clay", "mode": "clay", "camera": "persp", "yaw": 25, "height": 2.2, "dist": 6.5, "target_z": 1.8, "player": False},
]


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    items = []
    for key, title in FACES.items():
        out = OUT / key
        out.mkdir(parents=True, exist_ok=True)
        model = Model(f"occultech_mire_monarch_face_{key.lower()}")
        BUILD[key](model)
        model.write_bbmodel(out / f"{model.name}.bbmodel")
        v2.run_blender(model.render_json(PALETTE), out, VIEWS)
        stats = model.stats()
        (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        items.append((key, title))
        print(key, stats["cubes"], stats["size_blocks"])
    sheet.compare_sheet(OUT, items, OUT / "faces.png", heading="Mire Monarch - the Brute's face, three options (step 2)",
                        views=("front", "three_quarter", "player_eye", "clay"))


if __name__ == "__main__":
    main()
