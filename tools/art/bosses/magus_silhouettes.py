"""The Mirrored Magus redesign, session 1 step 1: three takes on the user's direction as cuboid blockouts.

The brief (user, 2026-10-13): a slender, tall jester / harlequin magician, tall and looming, based on vanilla's
Illusioner; a theatre mask; a bow made of glass and crystal shards. His fight (MirroredMagus.java) is unchanged:
three-arrow fans, a warned prism burst, and every 15 s three decoys that look exactly like him (so the model has no
detail only the real one carries - his faint sparkle is the plugin's).

Built on vanilla's IllagerModel at 1.8x, stretched slender: long legs, a long illusioner coat with harlequin tails, a
ruff collar, long arms, the illager's long head and nose. The three takes differ in hat and mask:
  A  the Grand Jester     a tall two-pointed jester hat curling outward, a full theatre mask worn over his face
  B  the Masquerade       a floppy three-pointed jester hat with bells, the theatre mask held up on a stick
  C  the Showman          a tall magician's hat ringed with jester points, a half mask over one side of his face
Each is shown idle (the bow lowered) and drawing the bow. Model units: 16 = one block, y up, his face towards -z.
The blue figure is a player (1.8 blocks). Colours are blockout zones, not the palette.

Run from the repository root: python tools/art/bosses/magus_silhouettes.py
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
from bosses import volley_crone_s2 as v2, volley_s1 as v1  # noqa: E402

OUT = ROOT / "docs/art/bosses/mirrored_magus/overhaul/s1_silhouettes"
PALETTE = {
    "robe": (52, 74, 150), "robe_dark": (32, 40, 96), "trim": (200, 196, 214), "skin": (128, 134, 136),
    "nose": (112, 118, 120), "mask": (236, 232, 222), "mask_dark": (24, 22, 30), "hat": (70, 46, 130),
    "hat_dark": (48, 30, 96), "bell": (220, 190, 90), "crystal": (150, 230, 250), "crystal_dark": (90, 160, 210),
    "string": (230, 240, 255), "stick": (60, 44, 34), "shoe": (36, 30, 52),
}


def beam(g, name, a, b, w, mat):
    return v1.beam(g, name, a, b, w, mat)


# ---- the body: vanilla's illager, tall and slender ------------------------------------------------------------------

def body(m, pose):
    root = m.group("root", (0, 0, 0))
    for sx in (-1, 1):
        side = "left" if sx < 0 else "right"
        leg = root.group(f"leg_{side}", (sx * 3.2, 30, 0))
        leg.box(f"leg_{side}_box", (sx * 3.2, 16, 0), (5, 28, 5), "robe_dark")
        leg.box(f"shoe_{side}", (sx * 3.2, 1.5, -2.5), (5.6, 3, 10), "shoe")
        leg.box(f"shoe_tip_{side}", (sx * 3.2, 3.5, -8), (3, 3, 3), "shoe", rotation=(-30, 0, 0))   # curled toes
    torso = root.group("torso", (0, 30, 0))
    torso.box("chest", (0, 41, 0), (15, 22, 9), "robe")
    torso.box("coat_skirt", (0, 24, 0.5), (17, 14, 11), "robe")
    for i, (x, l) in enumerate(((-6, 20), (0, 25), (6, 20))):              # harlequin coat tails, pointed, at the back
        torso.box(f"tail_{i}", (x, 24 - l / 2, 5.5), (5, l, 1.4), "robe_dark" if i % 2 else "robe")
        torso.box(f"tail_tip_{i}", (x, 24 - l - 1.5, 5.5), (2.5, 3, 1.4), "trim")
    for i in range(6):                                                     # the ruff collar, zigzag
        a = i * 60
        torso.box(f"ruff_{i}", (math.sin(math.radians(a)) * 8, 52.5, math.cos(math.radians(a)) * 5.5),
                  (8, 3, 4), "trim", rotation=(0, a, 0))
    # the arms: long, thin, a cuff at the wrist
    arms = {"idle": {"left": (6, 0, -6), "right": (4, 0, 8)},
            "draw": {"left": (88, 0, -4), "right": (80, -30, 18)},
            "stick": {"left": (6, 0, -6), "right": (96, 0, 28)}}[pose]
    hands = {}
    for sx in (-1, 1):
        side = "left" if sx < 0 else "right"
        arm = torso.group(f"arm_{side}", (sx * 10, 50, 0), arms[side])
        arm.box(f"upper_{side}", (sx * 10, 42, 0), (5, 16, 5), "robe")
        arm.box(f"cuff_{side}", (sx * 10, 25.5, 0), (6.5, 4, 6.5), "trim")
        arm.box(f"fore_{side}", (sx * 10, 30, 0), (4.5, 8, 4.5), "robe_dark")
        arm.box(f"hand_{side}", (sx * 10, 21, 0), (4.5, 5, 4.5), "skin")
        hands[side] = tuple((arm.world_matrix() @ np.array([sx * 10, 20, 0, 1.0]))[:3])   # where the hand is
    head = torso.group("head", (0, 52, 0))
    head.box("head", (0, 59.5, 0), (12, 15, 12), "skin")
    head.box("nose", (0, 54.5, -7.5), (3, 6, 3), "nose")
    return root, torso, head, hands


# ---- the masks ---------------------------------------------------------------------------------------------------------

def mask_face(g, centre, half=False):
    """A theatre mask: a pale plate shaped round the face, dark almond eye holes, a crescent smile."""
    x, y, z = centre
    w = 7 if half else 13
    g.box("mask", (x + (3 if half else 0), y, z), (w, 14, 1.4), "mask")
    g.box("mask_brow", (x + (3 if half else 0), y + 5.5, z - 0.6), (w + 1, 2, 1.2), "mask")
    for sx in ((1,) if half else (-1, 1)):
        g.box(f"mask_eye_{sx}", (x + sx * 3, y + 2, z - 0.8), (3.4, 1.6, 0.6), "mask_dark", rotation=(0, 0, sx * 15))
    if not half:
        for i, dx in enumerate((-3, -1.5, 0, 1.5, 3)):
            g.box(f"mask_smile_{i}", (x + dx, y - 3.5 + abs(dx) * 0.45, z - 0.8), (1.6, 1.2, 0.6), "mask_dark")


def hat_two_point(head):
    head.box("hat_band", (0, 67.5, 0), (13.5, 3, 13.5), "trim")
    head.box("hat_crown", (0, 71, 0), (12, 5, 12), "hat")
    for sx in (-1, 1):
        g = head
        base = np.array([sx * 4.5, 72, 0])
        d = np.array([sx * 0.45, 1.0, 0.15])
        w = 6.5
        for k in range(5):
            nxt = base + d * 6
            beam(g, f"hat_point_{sx}_{k}", tuple(base), tuple(nxt), w, "hat" if k % 2 == 0 else "hat_dark")
            base = nxt
            d = d + np.array([sx * 0.35, -0.28, 0])                        # curling outward and over
            w *= 0.8
        g.box(f"bell_{sx}", tuple(base + np.array([0, -1.5, 0])), (3, 3, 3), "bell")


def hat_three_point(head):
    head.box("hat_band", (0, 67.5, 0), (13.5, 3, 13.5), "trim")
    for i, (dx, dz) in enumerate(((-1, 0), (1, 0), (0, 1))):
        base = np.array([dx * 4, 69, dz * 4])
        d = np.array([dx * 0.7, 0.9, dz * 0.7])
        w = 6
        for k in range(4):
            nxt = base + d * 5.5
            beam(head, f"hat_point_{i}_{k}", tuple(base), tuple(nxt), w, "hat" if (i + k) % 2 else "hat_dark")
            base = nxt
            d = d + np.array([dx * 0.25, -0.55, dz * 0.25])               # floppy: the points droop
            w *= 0.78
        head.box(f"bell_{i}", tuple(base + np.array([0, -1.5, 0])), (3, 3, 3), "bell")


def hat_showman(head):
    head.box("hat_brim", (0, 67.5, 0), (18, 1.5, 18), "hat_dark")
    head.box("hat_tall", (0, 76, 0), (11, 16, 11), "hat")
    head.box("hat_band", (0, 70, 0), (11.8, 3, 11.8), "trim")
    for i in range(6):                                                     # jester points round the brim
        a = math.radians(i * 60 + 30)
        p = np.array([math.sin(a) * 9, 68, math.cos(a) * 9])
        beam(head, f"brim_point_{i}", tuple(p), tuple(p + np.array([math.sin(a) * 4, -3, math.cos(a) * 4])), 2.4,
             "hat" if i % 2 else "hat_dark")
        head.box(f"bell_{i}", tuple(p + np.array([math.sin(a) * 4.5, -4.5, math.cos(a) * 4.5])), (2, 2, 2), "bell")


# ---- the crystal bow ---------------------------------------------------------------------------------------------------

def crystal_bow(g, grip, plane, span=40, drawn=False):
    """A bow of glass and crystal shards: an arc of jagged shards of uneven size, splinters jutting out, a bright string.
    plane: the bow's limbs run along 'y' (held upright) and it bends towards -z (drawn: the string pulled back)."""
    gx, gy, gz = grip
    r = span * 0.75
    a0 = math.asin((span / 2) / r)
    pts = []
    for k in range(9):
        a = -a0 + 2 * a0 * k / 8
        y = gy + r * math.sin(a)
        z = gz - (r * math.cos(a) - r * math.cos(a0)) - 3
        pts.append((gx, y, z))
    sizes = (2.0, 3.2, 2.4, 3.8, 4.2, 3.8, 2.4, 3.2, 2.0)
    for k in range(8):
        mat = "crystal" if k % 2 else "crystal_dark"
        beam(g, f"bow_shard_{k}", pts[k], pts[k + 1], sizes[k], mat)
        if k in (1, 3, 5, 6):                                              # splinters
            mid = np.array(pts[k]) + (np.array(pts[k + 1]) - np.array(pts[k])) * 0.5
            beam(g, f"bow_splinter_{k}", tuple(mid), tuple(mid + np.array([0, (k - 3.5) * 0.6, -4])), 1.3, "crystal")
    pull = 9 if drawn else 0
    top, bottom = pts[0], pts[-1]
    nock = (gx, gy, gz + pull)
    beam(g, "string_a", top, nock, 0.6, "string")
    beam(g, "string_b", nock, bottom, 0.6, "string")
    if drawn:
        beam(g, "arrow", (gx, gy, gz + pull), (gx, gy, gz - 18), 1.0, "crystal")


# ---- the takes -------------------------------------------------------------------------------------------------------

TAKES = {
    "A": ("The Grand Jester", hat_two_point, "worn"),
    "B": ("The Masquerade", hat_three_point, "stick"),
    "C": ("The Showman", hat_showman, "half"),
}


def build(key, pose):
    title, hat, mask = TAKES[key]
    m = Model(f"magus_{key}_{pose}")
    root, torso, head, hands = body(m, "stick" if mask == "stick" and pose == "idle" else pose)
    hat(head)
    if mask == "worn":
        mask_face(head, (0, 60, -6.8))
    elif mask == "half":
        mask_face(head, (0, 60, -6.8), half=True)
    # the bow, in his left hand (built where the posed hand is, upright)
    crystal_bow(root, hands["left"], "y", drawn=pose == "draw")
    # the mask on a stick, held up before his face in his right hand
    if mask == "stick":
        rx, ry, rz = hands["right"]
        if pose == "idle":
            top = (0, 52, rz - 3)
            beam(root, "mask_stick", (rx, ry, rz), top, 1.4, "stick")
            mask_face(root, (0, 59, -9.5))                                  # held just before his face
        else:
            mask_face(head, (0, 60, -6.8))                                  # pressed to his face to aim
    return m, title


VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 35, "height": 3.0, "dist": 9, "target_z": 2.3},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 2.6, "dist": 8.5, "target_z": 2.5,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -30, "height": 1.62, "dist": 9, "target_z": 2.8,
     "player": False},
]
LABELS = {"flat_34": "three-quarter", "flat_front": "front", "sil_side": "side, silhouette", "clay_eye": "a player's eye"}


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    for key in TAKES:
        for pose in ("idle", "draw"):
            m, title = build(key, pose)
            v2.run_blender(m.render_json(v2.PALETTE), OUT / key / pose, VIEWS)
            if pose == "idle":
                lo, hi = m.bounds()
                print(key, title, round(float(hi[1]) / 16, 2), "blocks tall")
        tw, th, pad, top = 400, 320, 12, 60
        img = Image.new("RGB", (pad + 4 * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Mirrored Magus {key}: {TAKES[key][0]}", font=sheet._font(26), fill=sheet.INK)
        for r, pose in enumerate(("idle", "draw")):
            for c, v in enumerate(VIEWS):
                x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
                img.paste(sheet._tile(OUT / key / pose / f"{v['name']}.png", tw, th), (x, y))
                dr.text((x, y + th + 6), f"{pose}: {LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / f"{key}_{TAKES[key][0].lower().replace(' ', '_')}.png")


if __name__ == "__main__":
    main()
