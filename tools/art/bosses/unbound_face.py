"""The Unbound redesign, session 1 step 2: the face study (plan: docs/art/bosses/the_unbound/overhaul/plan.md).

A bust of the take-2 silhouette (the bare, buff, hunched brute): his chest, traps and shoulders, the straps and the
burning chest piece, and the head, which is what this step decides. The head is vanilla's illager head (8x10x8, the
2x4x2 nose hanging one pixel below the chin; IllagerModel in the 26.2 client) at 1.5x, sunk low between the traps.

Three heads on the same bust:
  F1  The blindfolded vindicator  vanilla's face exactly; a neat red band over the eyes, knotted behind, its ends
                                  trailing; his left eye burns cyan through a tear in it; bull horns out from the
                                  temples, then up
  F2  The scowl                   a heavy brow pushed down into a scowl over the band, a broader nose, a square jaw
                                  with an underbite; the band ragged and slipping askew, the eye burning through a
                                  scorched hole with cyan wisps rising off it; the horns sweep forward like a charging
                                  bull's
  F3  The bull                    a heavy horn boss across the top of the skull, the horns out, down and up like a
                                  buffalo's; an iron ring through the big nose; the band bound tight, its long ends
                                  hanging over his shoulder; the eye's cyan bleeding through the weave around it

Units are model pixels (16 = one block). The front is -z; his left is -x.
Run from the repository root: python tools/art/bosses/unbound_face.py
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
from bosses import monarch_s1 as m1, volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/the_unbound/overhaul/s1_face"
OUT2 = ROOT / "docs/art/bosses/the_unbound/overhaul/s1_face2"
K = 1.5
PALETTE = {
    "skin": (122, 128, 126), "skin_dark": (98, 104, 104), "nose": (112, 118, 116), "brow": (58, 60, 62),
    "pants": (50, 50, 58), "cloth": (150, 34, 34), "cloth_dark": (108, 24, 26), "scorch": (40, 22, 22),
    "horn": (208, 196, 164), "horn_dark": (164, 150, 116), "horn_root": (128, 116, 92),
    "strap": (88, 60, 40), "stud": (206, 210, 218), "iron": (70, 66, 72), "iron_lit": (120, 116, 124),
    "fire": (236, 92, 18), "fire_hot": (255, 186, 70),
    "eye": (70, 210, 250), "eye_hot": (200, 248, 255), "eye_dim": (26, 92, 116),
}
FACES = {"F1": "The blindfolded vindicator", "F2": "The scowl", "F3": "The bull"}
# take 2 (user, 2026-10-12): one head - F2's scowling brow and slipping ragged band (not its jaw or tusks), F3's eye,
# horns and nose ring - and the chest reworked: he burns from the inside, no furnace plate. Three ways to show it.
TAKES = {"C1": ("Head: F2 + F3. Chest: the fissure", "C1"), "C2": ("Head: F2 + F3. Chest: ember veins", "C2"),
         "C3": ("Head: F2 + F3. Chest: the burning heart", "C3")}
# take 3 (user, 2026-10-12): none of the burning chests; back to the chest piece. The locked head and chest.
FINAL = ("The head (F2 + F3) and the burning chest piece", "PIECE")
OUT3 = ROOT / "docs/art/bosses/the_unbound/overhaul/s1_face3"
HUNCH = -12                                       # the upper body leans forward over the hips


def horn(g, name, points, widths, tilt=0.0, mats=("horn_root", "horn", "horn", "horn_dark")):
    """A bull's horn: tapering beams along a curve drawn flat in the x-y plane (the root's depth), so no piece
    twists; tilt swings the whole horn forward (negative) or back about its root."""
    z = points[0][2]
    hg = g.group(name, points[0], (tilt, 0, 0))
    for i in range(len(points) - 1):
        a, b = (points[i][0], points[i][1], z), (points[i + 1][0], points[i + 1][1], z)
        d = [b[j] - a[j] for j in range(3)]
        n = sum(v * v for v in d) ** 0.5 or 1
        ext = widths[i] * 0.45 / n                              # run each piece into the next so the joints close
        a2 = tuple(a[j] - d[j] * ext for j in range(3))
        b2 = tuple(b[j] + d[j] * ext for j in range(3))
        roll = math.degrees(math.atan2(b2[1] - a2[1], b2[0] - a2[0]))
        roll = roll - 180 if roll > 90 else roll + 180 if roll <= -90 else roll      # a box is the same turned 180
        length = math.hypot(b2[0] - a2[0], b2[1] - a2[1])
        hg.box(f"{name}_{i}", tuple((a2[j] + b2[j]) / 2 for j in range(3)), (length, widths[i], widths[i]),
               mats[min(i, len(mats) - 1)], rotation=(0, 0, round(roll, 3)))


def horn_steps(g, name, root, sx, steps, widths, tilt=0.0):
    """A horn from its root as (angle, length) steps, mirrored by side sx. Angles from BetterModel's free set
    (0, 22.5, 45) keep the whole horn in one display."""
    pts = [root]
    for ang, ln in steps:
        a = math.radians(ang)
        x, y, z = pts[-1]
        pts.append((x + sx * ln * math.cos(a), y + ln * math.sin(a), z))
    horn(g, name, pts, widths, tilt)


def bust(model, face, chest="C1"):
    root = model.group("root", (0, 0, 0))
    root.box("waist", (0, 25, 0), (19, 8, 12), "pants")
    root.box("belt", (0, 28.4, 0), (20, 2.4, 13), "strap")
    torso = root.group("torso", (0, 26, 0), (HUNCH, 0, 0))
    # the bare torso: a deep, wide chest; lats tapering to the waist; deltoids; traps rising round the low head
    m1.octo(torso, "chest", (0, 40, 0), (30, 20, 17), "skin", 0.12)
    torso.box("abdomen", (0, 31, 0), (21, 9, 13), "skin")
    torso.box("traps", (0, 49, 2.5), (20, 5, 11), "skin")
    # the heavy back: lats and a hump of traps behind the low head, so the hunch reads from the side and balances
    # over the legs (C's side posture)
    m1.octo(torso, "back", (0, 39, 7.5), (27, 18, 10), "skin", 0.2)
    m1.octo(torso, "hump", (0, 47.5, 6.5), (22, 8, 11), "skin", 0.3)
    for sx in (-1, 1):
        torso.box(f"delt_{sx}", (sx * 16.5, 45, 0.5), (10, 10, 12), "skin", rotation=(0, 0, 0))
        torso.box(f"trap_slope_{sx}", (sx * 11.5, 47.5, 2), (8, 4, 10), "skin", rotation=(0, 0, sx * -22.5))
        torso.box(f"upper_arm_{sx}", (sx * 18.5, 35, 0), (10, 15, 10.5), "skin_dark", rotation=(0, 0, sx * 6))
        torso.box(f"pec_line_{sx}", (sx * 5.5, 35.6, -8.6), (9, 1.0, 0.6), "skin_dark")
    # the straps crossing the chest, studded, and the burning chest piece where they cross
    for sx in (-1, 1):
        # a flat strap lying on the chest (front at z -8.5), at 45 degrees (one display), from the shoulder to the
        # chest's lower edge, passing behind the chest piece where the two cross
        a, b = (sx * 13.5, 47, -9.05), (-sx * 3.5, 30, -9.05)
        length = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
        torso.box(f"strap_{sx}", ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, a[2]), (length, 2.6, 1.0), "strap",
                  rotation=(0, 0, 45 * sx))
        for i in range(6):
            t = (i + 0.5) / 6
            p = tuple(a[j] + (b[j] - a[j]) * t for j in range(3))
            if abs(p[0]) < 6.5 and 32 < p[1] < 44:
                continue                                   # behind the chest piece
            torso.box(f"stud_{sx}_{i}", (p[0], p[1], -9.85), (1.0, 1.0, 0.6), "stud")
    CHESTS[chest](torso)
    # the head, low and forward between the traps, lifted so he looks ahead
    head = torso.group("hi_head", (0, 47.5, -7), (-HUNCH - 4, 0, 0))
    hw, hh = 8 * K, 10 * K
    hc = (0, 47.5 + hh / 2, -8)
    head.box("head", hc, (hw, hh, hw), "skin")
    HEADS[face](head, hc, hw, hh, hc[2] - hw / 2)
    return root


def vanilla_face(h, hc, hw, hh, f, brow=True):
    """Vanilla's illager face: the unibrow, the long nose hanging a pixel below the chin."""
    x, y, z = hc
    bottom = y - hh / 2
    h.box("nose", (x, bottom + 1 * K, f - 1 * K), (2 * K, 4 * K, 2 * K), "nose")
    if brow:
        h.box("brow", (x, bottom + 8 * K, f - 0.3), (8 * K, 1.2 * K, 0.6), "brow")
    return bottom


def band(h, hc, hw, y, height=4.2, tilt=0.0, mat="cloth"):
    """The red cloth wrapped round the head over the eyes."""
    x, _, z = hc
    h.box("band", (x, y, z), (hw + 0.9, height, hw + 0.9), mat, rotation=(0, 0, tilt))


def tails(h, hc, hw, y, long=False):
    """The knot behind and its two trailing ends."""
    x, _, z = hc
    back = z + hw / 2 + 0.6
    h.box("knot", (x, y, back + 0.6), (2.6, 2.6, 1.6), "cloth_dark")
    n = 9 if long else 5.5
    h.box("tail_a", (x - 1.2, y - n / 2 - 0.6, back + 1.6), (2.2, n, 0.6), "cloth_dark", rotation=(-22.5, 0, 0))
    h.box("tail_b", (x + 1.0, y - n / 2 - 1.4, back + 1.2), (1.8, n * 0.8, 0.6), "cloth_dark", rotation=(-22.5, 0, 0))
    if long:
        h.box("tail_c", (x - 4.5, y - 7, back - 1), (2.0, 10, 0.6), "cloth_dark", rotation=(0, 0, 22.5))


def face_blindfold(h, hc, hw, hh, f):
    x, y, z = hc
    bottom = vanilla_face(h, hc, hw, hh, f)
    eye_y = bottom + 6 * K
    band(h, hc, hw, eye_y)
    tails(h, hc, hw, eye_y)
    # the tear and the left eye burning through it
    h.box("tear", (-2.4 * K, eye_y + 0.2, f - 0.55), (3.6, 1.6, 0.3), "scorch", rotation=(0, 0, -8))
    h.box("tear_b", (-2.4 * K + 1.2, eye_y - 0.5, f - 0.55), (1.6, 1.0, 0.3), "scorch")
    h.box("eye", (-2.4 * K, eye_y + 0.2, f - 0.7), (2.6, 0.8, 0.3), "eye", rotation=(0, 0, -8))
    h.box("eye_core", (-2.4 * K, eye_y + 0.2, f - 0.85), (1.0, 0.5, 0.2), "eye_hot")
    # bull horns from the temples, above the band: out, then up, the tips turned a little in
    for sx in (-1, 1):
        horn(h, f"horn_{sx}", [(sx * (hw / 2 - 1), eye_y + 4.6, z), (sx * (hw / 2 + 3.5), eye_y + 5.6, z),
                               (sx * (hw / 2 + 7), eye_y + 8.2, z - 0.6), (sx * (hw / 2 + 8), eye_y + 12, z - 1.4),
                               (sx * (hw / 2 + 6.8), eye_y + 14.6, z - 2)], [4.8, 4.0, 3.0, 2.0], tilt=-12)


def face_scowl(h, hc, hw, hh, f):
    x, y, z = hc
    bottom = vanilla_face(h, hc, hw, hh, f, brow=False)
    eye_y = bottom + 6 * K
    # a heavy brow pushed down in the middle, a broader nose over it, a square jaw with an underbite
    for sx in (-1, 1):
        h.box(f"brow_{sx}", (sx * 2.6, eye_y + 3.4, f - 0.9), (5.6, 2.2, 1.8), "brow", rotation=(0, 0, sx * 14))
    h.box("nose_wide", (x, bottom + 2.2, f - 1.2), (3.6, 4.4, 2.4), "nose")
    h.box("jaw", (x, bottom + 1.2, f - 0.4), (hw - 0.6, 2.4, 1.6), "skin_dark")
    for sx in (-1, 1):
        h.box(f"tusk_{sx}", (sx * 3.4, bottom + 2.8, f - 1.0), (1.0, 1.6, 0.8), "horn")
    band(h, hc, hw, eye_y, 4.4, tilt=7)
    tails(h, hc, hw, eye_y)
    h.box("rag", (2.6, eye_y - 2.6, f - 0.5), (3.0, 1.8, 0.4), "cloth", rotation=(0, 0, 12))   # a torn flap hanging
    h.box("hole", (-2.4 * K, eye_y + 0.1, f - 0.55), (3.6, 2.4, 0.3), "scorch", rotation=(0, 0, 10))
    h.box("eye", (-2.4 * K, eye_y + 0.1, f - 0.7), (2.6, 0.8, 0.3), "eye", rotation=(0, 0, -10))
    h.box("eye_core", (-2.4 * K, eye_y + 0.1, f - 0.85), (0.8, 0.6, 0.2), "eye_hot")
    for i, (dx, dy, s) in enumerate(((-0.6, 2.6, 1.0), (0.4, 4.2, 0.8), (-0.2, 5.8, 0.6))):     # wisps rising off it
        h.box(f"wisp_{i}", (-2.4 * K + dx, eye_y + dy, f - 1.2 - i * 0.3), (s, s * 1.4, s), "eye_dim")
    # the horns sweep forward like a charging bull's
    for sx in (-1, 1):
        horn(h, f"horn_{sx}", [(sx * (hw / 2 - 1), eye_y + 4.6, z + 1), (sx * (hw / 2 + 4), eye_y + 5.4, z),
                               (sx * (hw / 2 + 6.5), eye_y + 7, z - 3.5), (sx * (hw / 2 + 7), eye_y + 9.2, z - 7),
                               (sx * (hw / 2 + 5.4), eye_y + 11, z - 9)], [4.8, 4.0, 3.0, 2.0], tilt=-50)


def face_bull(h, hc, hw, hh, f):
    x, y, z = hc
    bottom = vanilla_face(h, hc, hw, hh, f)
    eye_y = bottom + 6 * K
    band(h, hc, hw, eye_y, 4.0)
    tails(h, hc, hw, eye_y, long=True)
    h.box("halo", (-2.4 * K, eye_y + 0.1, f - 0.55), (4.2, 2.2, 0.3), "eye_dim")                # cyan through the weave
    h.box("eye", (-2.4 * K, eye_y + 0.1, f - 0.7), (2.6, 0.8, 0.3), "eye")
    h.box("eye_core", (-2.4 * K, eye_y + 0.1, f - 0.85), (0.8, 0.6, 0.2), "eye_hot")
    # an iron ring through the big nose
    nz = f - 2 * K - 0.4
    h.box("ring_l", (-1.7, bottom - 1.6, nz), (0.8, 2.6, 0.8), "iron_lit")
    h.box("ring_r", (1.7, bottom - 1.6, nz), (0.8, 2.6, 0.8), "iron_lit")
    h.box("ring_b", (0, bottom - 2.9, nz), (4.2, 0.8, 0.8), "iron_lit")
    # a heavy horn boss across the top of the skull; the horns out, down a little, then up, like a buffalo's
    h.box("boss", (x, y + hh / 2 + 0.6, z + 0.4), (hw + 1.4, 2.4, 6.4), "horn_root")
    for sx in (-1, 1):
        horn(h, f"horn_{sx}", [(sx * (hw / 2 - 0.5), y + hh / 2 + 0.2, z + 0.4), (sx * (hw / 2 + 5), y + hh / 2 - 1.2, z),
                               (sx * (hw / 2 + 8.5), y + hh / 2, z - 0.4), (sx * (hw / 2 + 10.5), y + hh / 2 + 4, z - 1.2),
                               (sx * (hw / 2 + 9.6), y + hh / 2 + 7.4, z - 2)], [5.4, 4.4, 3.2, 2.2], tilt=-8)


def face_mix(h, hc, hw, hh, f):
    """The user's mix: F2's scowling brow, broad nose and slipping ragged band (no jaw, no tusks); F3's eye (a slit
    with a soft halo through the weave), its iron nose ring, its horn boss and buffalo horns."""
    x, y, z = hc
    bottom = vanilla_face(h, hc, hw, hh, f, brow=False)
    eye_y = bottom + 6 * K
    # the scowl: the brow pressed down onto the band's top edge
    for sx in (-1, 1):
        h.box(f"brow_{sx}", (sx * 2.6, eye_y + 2.7, f - 0.6), (5.0, 1.8, 1.2), "brow", rotation=(0, 0, sx * 22.5))
    h.box("nose_wide", (x, bottom + 2.2, f - 1.2), (3.6, 4.4, 2.4), "nose")
    # the band: a snug straight wrap (take 2; the tilted slab read oddly; tatters along its edge read as blood),
    # a torn flap hanging at his right temple, the knot and its tails behind
    h.box("band", (x, eye_y, z), (hw + 1.0, 4.0, hw + 1.0), "cloth")
    tails(h, hc, hw, eye_y, long=True)
    h.box("rag", (hw / 2 + 0.6, eye_y - 2.8, f + 2.2), (0.4, 3.2, 2.4), "cloth_dark")     # the torn flap
    h.box("halo", (-2.4 * K, eye_y + 0.1, f - 0.55), (4.2, 2.2, 0.3), "eye_dim")
    h.box("eye", (-2.4 * K, eye_y + 0.1, f - 0.7), (2.6, 0.8, 0.3), "eye")
    h.box("eye_core", (-2.4 * K, eye_y + 0.1, f - 0.85), (0.8, 0.6, 0.2), "eye_hot")
    nz = f - 2 * K - 0.4
    h.box("ring_l", (-1.7, bottom - 1.6, nz), (0.8, 2.6, 0.8), "iron_lit")
    h.box("ring_r", (1.7, bottom - 1.6, nz), (0.8, 2.6, 0.8), "iron_lit")
    h.box("ring_b", (0, bottom - 2.9, nz), (4.2, 0.8, 0.8), "iron_lit")
    h.box("boss", (x, y + hh / 2 + 0.6, z + 0.4), (hw + 1.4, 2.4, 6.4), "horn_root")
    for sx in (-1, 1):
        horn_steps(h, f"horn_{sx}", (sx * (hw / 2 - 0.5), y + hh / 2 + 0.2, z + 0.4), sx,
                   [(-22.5, 5.6), (0, 3.6), (45, 4.6), (45, 3.0)], [5.4, 4.4, 3.2, 2.2], tilt=-8)


# ---- the chest: burning from the inside (take 2) --------------------------------------------------------------------
# The skin is split and the fire inside shows through: glowing cracks (a hot core line in a wider ember line) on the
# chest's front face (z = -8.5). The skin round them gets a warm glow spill when it's painted (session 5).

CHEST_Z = -8.75


def crack(t, name, points, w=1.3, core=True):
    """A glowing split in the skin along a polyline, drawn flat on the chest's front."""
    for i in range(len(points) - 1):
        z = CHEST_Z if (points[i][1] + points[i + 1][1]) / 2 >= 31 else -6.75     # the chest, or the narrower stomach
        a, b = (*points[i], z), (*points[i + 1], z)
        m1.beam(t, f"{name}_{i}", a, b, w, "fire")
        if core and w >= 1.0:
            m1.beam(t, f"{name}_{i}_hot", (a[0], a[1], z - 0.35), (b[0], b[1], z - 0.35), w * 0.4, "fire_hot")


def chest_fissure(t):
    """C1: one jagged fissure splits the sternum from the collarbones to the stomach, branching out across the pecs;
    the light is brightest in its middle."""
    crack(t, "fissure", [(0.6, 47.5), (-0.8, 44.5), (0.9, 41.5), (-0.6, 38.5), (1.1, 35.5), (-0.2, 32.5), (0.4, 29.5)], 1.8)
    crack(t, "branch_a", [(-0.8, 44.5), (-4.5, 45.8), (-8.5, 44.6), (-11, 45.6)], 1.1)
    crack(t, "branch_b", [(0.9, 41.5), (4.8, 42.6), (8.6, 40.6)], 1.1)
    crack(t, "branch_c", [(-0.6, 38.5), (-4.2, 36.8), (-7.8, 37.6), (-10.4, 35)], 1.0)
    crack(t, "branch_d", [(1.1, 35.5), (4.6, 33.4), (7, 34.4)], 0.9)
    crack(t, "branch_e", [(-0.2, 32.5), (-3.6, 30.6)], 0.8, core=False)
    t.box("fissure_glow", (0.2, 39, CHEST_Z - 0.5), (2.2, 5, 0.3), "fire_hot")


def chest_veins(t):
    """C2: no single wound - glowing veins spread from his heart over the whole chest and onto the shoulders, like
    lava under cracked rock; thin, many, branching."""
    heart = (-4.5, 40.5)
    t.box("heart_glow", (heart[0], heart[1], CHEST_Z - 0.4), (2.6, 2.6, 0.3), "fire_hot", rotation=(0, 0, 45))
    for i, path in enumerate([
            [heart, (-8, 43), (-11.5, 44), (-14.5, 46.5)],
            [heart, (-6.5, 46), (-4, 48)],
            [heart, (-1, 43.5), (3.5, 45.5), (8, 44.5), (12.5, 46)],
            [heart, (0.5, 39), (5, 37.5), (9.5, 39.5), (12, 37)],
            [heart, (-8.5, 37.5), (-11.5, 34)],
            [heart, (-3, 35.5), (-5, 31.5), (-3, 28.5)],
            [(0.5, 39), (2.5, 34), (5.5, 31)],
            [(3.5, 45.5), (5.5, 48)],
            [(-8, 43), (-9, 39.5)]]):
        crack(t, f"vein_{i}", path, 0.9 if i < 6 else 0.7, core=i < 4)


def chest_heart(t):
    """C3: the burning heart - a short, wide split over his heart (his left chest) blazing, short cracks radiating
    from it, and embers drifting out of it."""
    c = (-4.8, 40.5)
    t.box("heart_split", (c[0], c[1], CHEST_Z - 0.2), (5.6, 2.8, 0.6), "fire", rotation=(0, 0, -18))
    t.box("heart_core", (c[0], c[1], CHEST_Z - 0.55), (3.4, 1.2, 0.3), "fire_hot", rotation=(0, 0, -18))
    for i, (dx, dy) in enumerate(((-5, 3.2), (-4.4, -3.4), (4.6, 2.6), (3.8, -3.8), (0.4, 5), (-1, -5.2))):
        crack(t, f"ray_{i}", [(c[0] + dx * 0.45, c[1] + dy * 0.45), (c[0] + dx, c[1] + dy),
                              (c[0] + dx * 1.45 + (0.8 if i % 2 else -0.8), c[1] + dy * 1.4)], 0.9, core=i < 2)
    for i, (dx, dy, dz) in enumerate(((-1, 5, -2.2), (1.5, 7.5, -3.4), (-2.5, 9.5, -2.6), (0.5, 11.5, -4))):
        t.box(f"ember_{i}", (c[0] + dx, c[1] + dy, CHEST_Z + dz), (0.8, 0.8, 0.8), "fire_hot" if i % 2 else "fire")


def chest_piece(t):
    """The burning chest piece (the original brief, take 1's chest; the user went back to it after the three burning
    chests): a blackened iron plate strapped where the straps cross, fire burning behind its grate."""
    t.box("chest_piece", (0, 38, -9.0), (11, 10, 1.4), "iron")
    t.box("chest_fire", (0, 38, -9.8), (6, 5.4, 0.4), "fire")
    t.box("chest_fire_hot", (0, 37.4, -10.0), (1.4, 1.6, 0.3), "fire_hot")
    for dx in (-1.6, 0, 1.6):
        t.box(f"grate_{dx}", (dx, 38, -10.1), (0.8, 6.4, 0.4), "iron")
    t.box("chest_rim", (0, 43.4, -9.2), (11.6, 1.2, 1.6), "iron_lit")


CHESTS = {"C1": chest_fissure, "C2": chest_veins, "C3": chest_heart, "PIECE": chest_piece}
HEADS = {"F1": face_blindfold, "F2": face_scowl, "F3": face_bull, "MIX": face_mix}
VIEWS = [
    {"name": "face", "mode": "flat", "camera": "persp", "yaw": -24, "height": 3.25, "dist": 2.9, "target_z": 3.35, "player": False},
    {"name": "front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.1, "dist": 4.2, "target_z": 2.8, "player": False},
    {"name": "three_quarter", "mode": "flat", "camera": "persp", "yaw": -40, "height": 3.3, "dist": 4.4, "target_z": 2.8,
     "player": False},
    {"name": "player_eye", "mode": "flat", "camera": "persp", "yaw": -14, "height": 1.62, "dist": 3.4, "target_z": 3.0,
     "lens": 24, "player": False},
    ]


GLOW = {"fire", "fire_hot", "eye", "eye_hot", "eye_dim"}


def _blender(boxes, out, views, extra=None):
    import json as _json
    import subprocess
    out.mkdir(parents=True, exist_ok=True)
    job_file = out / "render_job.json"
    job_file.write_text(_json.dumps(dict({"boxes": boxes, "out": out.as_posix(), "views": views, "res": [900, 700]},
                                         **(extra or {}))), encoding="utf-8")
    r = subprocess.run([str(v2.BLENDER), "-b", "--factory-startup", "--python",
                        str(ROOT / "tools/art/bosskit/blender_render.py"), "--", str(job_file)],
                       capture_output=True, text=True)
    if r.returncode or "RENDER_DONE" not in r.stdout:
        raise SystemExit(r.stdout[-2000:] + r.stderr[-2000:])
    job_file.unlink()


def render_glowing(model, out, views=None, extra=None):
    """The study views, with the fire and the eye glowing: a normal render, then an unlit pass where everything but
    the glowing parts is black (the same geometry, so it's hidden where it should be), laid over it with a bloom.
    extra: more job settings for both passes (player_at: where the scale player stands, in blocks)."""
    from PIL import Image, ImageChops, ImageFilter
    views = views or VIEWS
    _blender(model.render_json(PALETTE), out, views, extra)
    dark = {k: (v if k in GLOW else (0, 0, 0)) for k, v in PALETTE.items()}
    glow_dir = out / "glow"
    _blender(model.render_json(dark), glow_dir, [dict(v, light="FLAT") for v in views],
             dict(extra or {}, ground=[0, 0, 0], sky=[0, 0, 0], player_color=[0, 0, 0]))
    for v in views:
        if v["mode"] != "flat":                     # silhouettes and clay show shape only
            continue
        base = Image.open(out / f"{v['name']}.png").convert("RGB")
        mask = Image.open(glow_dir / f"{v['name']}.png").convert("RGB")
        lit = mask.convert("L").point(lambda x: 255 if x > 24 else 0)
        base.paste(mask, (0, 0), lit)                                       # the glow, unlit
        bloom = mask.filter(ImageFilter.GaussianBlur(8)).point(lambda x: min(255, int(x * 1.15)))
        base = ImageChops.screen(base, bloom)
        base.save(out / f"{v['name']}.png")
    shutil.rmtree(glow_dir)


def main():
    """Take 3: the chosen head on the chest piece. (Take 1, three heads, is in s1_face; take 2, the burning chests,
    in s1_face2.)"""
    if OUT3.exists():
        for old in OUT3.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    title, chest = FINAL
    out = OUT3 / "final"
    out.mkdir(parents=True, exist_ok=True)
    model = Model("occultech_unbound_face3")
    bust(model, "MIX", chest)
    model.write_bbmodel(out / f"{model.name}.bbmodel")
    render_glowing(model, out)
    print(model.stats()["cubes"], "cubes")
    sheet.compare_sheet(OUT3, [("final", title)], OUT3 / "faces.png", heading="The Unbound - the head and chest",
                        views=("face", "front", "three_quarter", "player_eye"))


if __name__ == "__main__":
    main()
