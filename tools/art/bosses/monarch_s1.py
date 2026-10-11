"""Mire Monarch, session 1 take 5: three directions for a mutated, radioactive toad king.

The brief (2026-10-11): a mutated version of vanilla's frog; radioactive and toxic; a large crown; large warts on its
back; and a new attack, a tongue that pulls a player in. The fight is otherwise set (MireMonarch.java): the marked
leap and its jumpable shockwave, the 66% spawn crawling back to feed it, the 33% dried phase sweating acid.

What changed from the rejected toads (take 4, monarch_s1.py in git history): those were built from stepped "rounded
boxes" and blobs, so every part read as a crate. Here every direction keeps **vanilla's frog head exactly** (FrogModel:
a 7x3x9 head slab over a 7x3x9 jaw slab split by the mouth line, 3x2x3 eyes on the front corners, flat 8x8 webbed
hands and feet) scaled by a whole factor k, the way Brood Mother kept the vanilla spider's head at 3x. Only the body
around it mutates, and the large forms are tilted slabs (any angle works in game), not stacked terraces.

  A  The Glowback      k=6. Low and enormously swollen: the back balloons into a hump of radioactive warts, each
                       a bulb cracked open on a glowing core; two great poison glands behind the eyes (a real toad's
                       parotoids); a wide gold crown sunk into the back of the skull, warts pushing through it.
  B  The Stilt Tyrant  k=5. The legs mutated: over-long hind legs folded so the knees rise above its back like a
                       grasshopper's, long straight arms lifting the chest, the head held high and proud; a ridge of
                       glowing pustule spines down its back; a tall spired crown.
  C  The Lantern Throat k=6. The throat mutated: the croaking sac swollen into a huge glowing bladder of toxin
                       hanging to the floor under its chin, veined with skin; a back crowded with warts; the
                       heaviest crown, many-pointed, slipping to one side.

Each direction is also shown with the tongue out (the new pull attack). Phase 2 (dried) waits for the direction lock.

Run from the repository root: python tools/art/bosses/monarch_s1.py
"""
import json
import math
import random
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, rotation_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s1 as v1, volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/mire_monarch/overhaul/s1_concepts"
PALETTE = {
    # vanilla's cold frog greens, darkened (dark vessel); the cream underside; the dark brown mouth
    "skin": (62, 92, 30), "skin_dark": (44, 68, 24), "skin_light": (96, 138, 44), "belly": (176, 160, 100),
    "mouth": (46, 29, 16), "tongue": (150, 210, 40), "tongue_tip": (220, 255, 110),
    "iris": (214, 170, 64), "pupil": (16, 12, 10),
    "wart": (88, 96, 40), "wart_dark": (60, 66, 30),
    "glow": (170, 255, 0), "glow_hot": (236, 255, 140), "sac": (150, 230, 40), "vein": (52, 80, 26),
    "gold": (226, 172, 44), "gold_dark": (156, 108, 26), "gem": (120, 255, 60),
}
DIRECTIONS = {"A": "The Glowback", "B": "The Stilt Tyrant", "C": "The Lantern Throat"}


# ---- parts --------------------------------------------------------------------------------------------------------

def beam(g, name, a, b, w, mat, d=None):
    return v1.beam(g, name, a, b, w, mat, d)


def octo(g, name, c, size, mat, cham=0.3, rot=(0, 0, 0), axis="z"):
    """A mass with its four long edges chamfered at 45 degrees: an octagonal prism along axis (a cross plus four
    diagonal plates filling the notches), in its own little group so it can be tilted as one. cham: the chamfer as a
    fraction of the smaller cross-section side."""
    w, h, d = size
    o = g.group(name, c, rot)
    x, y, z = c
    if axis == "z":
        a, b, L = w, h, d
    else:                                                    # along x: the cross-section is d (as "a") by h
        a, b, L = d, h, w
    ch = cham * min(a, b)
    t = ch / math.sqrt(2)

    def put(nm, da, db, sa, sb, sl, angle=0.0):
        if axis == "z":
            o.box(nm, (x + da, y + db, z), (sa, sb, sl), mat, rotation=(0, 0, angle))
        else:
            o.box(nm, (x, y + db, z + da), (sl, sb, sa), mat, rotation=(angle, 0, 0))

    put(name + "_h", 0, 0, a, b - 2 * ch, L)
    put(name + "_v", 0, 0, a - 2 * ch, b, L - 1)
    for sa in (-1, 1):
        for sb in (-1, 1):
            put(f"{name}_c{sa}{sb}", sa * (a / 2 - 0.75 * ch), sb * (b / 2 - 0.75 * ch), ch * math.sqrt(2), t,
                L - 0.5, 45 * sa * sb * (-1 if axis == "z" else 1))
    return o


def ball(g, name, c, size, mat, cham=0.3, rot=(0, 0, 0)):
    """Rounded from every side: an octagonal prism along z joined with one along x."""
    w, h, d = size
    o = g.group(name, c, rot)
    octo(o, name + "_z", c, (w, h, d * 0.72), mat, cham)
    octo(o, name + "_x", c, (w * 0.72 - 0.5, h - 0.5, d), mat, cham, axis="x")
    return o


def tapered(g, name, a, b, w0, w1, mat):
    """A limb segment thick at a, thinner at b: two overlapping beams."""
    m = tuple((a[i] + b[i]) / 2 for i in range(3))
    beam(g, name + "_a", a, tuple(a[i] + (b[i] - a[i]) * 0.62 for i in range(3)), w0, mat)
    beam(g, name + "_b", m, b, w1, mat)


def frog_head(g, k, y0, cz, eye_k=1.0, tongue=0.0):
    """Vanilla's frog head at k times: the jaw slab, the dark mouth line, the head slab with its paler stripe, two eyes
    standing on the front corners (gold iris, dark horizontal pupil). tongue: how far the tongue reaches, in blocks."""
    w, h, d = 7 * k, 3 * k, 9 * k
    g.box("jaw", (0, y0 + h / 2, cz), (w, h, d), "skin_dark")
    g.box("chin", (0, y0 + 0.5, cz - 1), (w - 2, 1.2, d - 4), "belly")
    g.box("mouth", (0, y0 + h, cz - 0.5), (w + 0.8, 2, d), "mouth")
    g.box("skull", (0, y0 + h * 1.5 + 0.5, cz), (w, h - 1, d), "skin")
    g.box("stripe", (0, y0 + 2 * h + 0.4, cz + 1), (3 * k, 1, d - 2 * k), "skin_light")
    es = 3 * k * eye_k
    for sd in (-1, 1):
        ex, ez = sd * 2 * k, cz - d / 2 + k + es / 2
        ey = y0 + 2 * h + k * eye_k
        g.box(f"eye_{sd}", (ex, ey, ez), (es, 2 * k * eye_k, es), "skin")
        # the iris looks out sideways and forward: on the outer and the front face
        g.box(f"iris_{sd}_side", (ex + sd * (es / 2 + 0.3), ey, ez), (0.6, k * 1.2 * eye_k, es * 0.8), "iris")
        g.box(f"pupil_{sd}_side", (ex + sd * (es / 2 + 0.7), ey, ez), (0.6, k * 0.4 * eye_k, es * 0.6), "pupil")
        g.box(f"iris_{sd}", (ex, ey, ez - es / 2 - 0.3), (es * 0.8, k * 1.2 * eye_k, 0.6), "iris")
        g.box(f"pupil_{sd}", (ex, ey, ez - es / 2 - 0.7), (es * 0.6, k * 0.4 * eye_k, 0.6), "pupil")
    if tongue:
        # vanilla's tongue is a flat 4x7 plane; this one is thick, toxic and reaches blocks out, a sticky club at its tip
        reach = tongue * 16
        g.box("tongue", (0, y0 + h - 1, cz - d / 2 - reach / 2 + 4), (2.2 * k, 2, reach), "tongue")
        g.box("tongue_tip", (0, y0 + h - 1, cz - d / 2 - reach + 2), (3.2 * k, 5, 2.4 * k), "tongue_tip")
    return w, h, d


def wart(g, name, c, r, tilt=(0, 0, 0), core=True, mat="wart"):
    """A big wart: a squat lump (a square and its 45-degree twin make an octagon from above), split open on top over
    a glowing core."""
    x, y, z = c
    g.box(name, c, (2 * r, r * 1.1, 2 * r), mat, rotation=(tilt[0], 45 + tilt[1], tilt[2]))
    g.box(name + "_b", (x, y + r * 0.15, z), (1.7 * r, r * 1.2, 1.7 * r), mat, rotation=tilt)
    if core:
        g.box(name + "_core", (x, y + r * 0.62, z), (r * 1.3, r * 0.5, r * 1.3), "glow", rotation=(tilt[0], 45 + tilt[1], tilt[2]))
        g.box(name + "_hot", (x, y + r * 0.82, z), (r * 0.7, r * 0.45, r * 0.7), "glow_hot", rotation=tilt)


def gland(g, name, c, size, yaw, mat="wart"):
    """A toad's parotoid: a long swollen poison gland behind the eye, a glowing seam along its top."""
    x, y, z = c
    w, h, d = size
    g.box(name, c, (w, h, d), mat, rotation=(0, yaw, 0))
    g.box(name + "_b", (x, y + 0.6, z), (w * 0.75, h + 1.4, d * 0.8), mat, rotation=(0, yaw, 0))
    g.box(name + "_seam", (x, y + h / 2 + 1.0, z), (1.6, 1.6, d * 0.7), "glow", rotation=(0, yaw, 0))
    for i in (-1, 1):                                     # pores along the seam
        g.box(f"{name}_pore{i}", (x + i * w * 0.22, y + h / 2 + 0.9, z + i * d * 0.18), (2, 1.4, 2), "glow_hot",
              rotation=(0, yaw, 0))


def crown(g, name, c, r, h, points, tilt=(0, 0, 0), flare=0, gem=True):
    """A large gold crown, kept bold and clean: a square band (four panels on a darker rim), tall tapering points
    standing on it, a gold ball on each tip, a glowing stone set in every side. points: the heights of the points
    along one side, as fractions of h (the corner points are the first and last)."""
    cx, cy, cz = c
    cr = g.group(name, c, tilt)
    t = 3.0
    n = len(points)
    for i, (nx, nz) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
        px, pz = cx + nx * (r - t / 2), cz + nz * (r - t / 2)
        width = 2 * r - (2 * t if nx else 0)      # the x-facing panels sit between the z-facing ones
        cr.box(f"{name}_band{i}", (px, cy, pz), (width, h, t) if nz else (t, h, width), "gold")
        cr.box(f"{name}_rim{i}", (px + nx * 0.6, cy - h / 2 + 1.5, pz + nz * 0.6),
               (width + 1.2, 3, t + 1.2) if nz else (t + 1.2, 3, width + 1.2), "gold_dark")
        cr.box(f"{name}_lip{i}", (px + nx * 0.4, cy + h / 2 - 0.8, pz + nz * 0.4),
               (width + 0.8, 1.6, t + 0.8) if nz else (t + 0.8, 1.6, width + 0.8), "gold_dark")
        if gem:
            cr.box(f"{name}_gem{i}", (px + nx * 1.8, cy, pz + nz * 1.8), (5, 5, 1.6) if nz else (1.6, 5, 5), "gem",
                   rotation=(0, 0, 45) if nz else (45, 0, 0))
        span = 2 * r - t
        for j, f in enumerate(points):
            if nx and j in (0, n - 1):            # the corner points belong to the z-facing panels
                continue
            s = (j / (n - 1) - 0.5) * span if n > 1 else 0
            bx, bz = (px + s, pz) if nz else (px, pz + s)
            ph = h * f
            # one clean triangle per point: a square turned 45 degrees in the band's plane, its lower half sunk into
            # the band; a tall point stands that triangle on a post. A gold ball on the apex.
            base = 2 * r / (n - 1) * 0.95
            ph = h * f
            top = cy + h / 2
            turn = (0, 0, 45) if nz else (45, 0, 0)
            if ph <= base / 2 * 1.15:
                dsz = ph * math.sqrt(2)
                cr.box(f"{name}_pt{i}_{j}", (bx, top, bz), (dsz, dsz, t) if nz else (t, dsz, dsz), "gold", rotation=turn)
                apex = top + ph
            else:
                pw = base * 0.55
                post = ph - pw / 2
                cr.box(f"{name}_post{i}_{j}", (bx, top + post / 2 - 0.5, bz), (pw, post + 1, t) if nz else (t, post + 1, pw),
                       "gold")
                dsz = pw / math.sqrt(2) * 1.0001
                cr.box(f"{name}_pt{i}_{j}", (bx, top + post, bz), (dsz, dsz, t - 0.4) if nz else (t - 0.4, dsz, dsz),
                       "gold", rotation=turn)
                apex = top + post + pw / 2
            cr.box(f"{name}_ball{i}_{j}", (bx, apex + 0.8, bz), (3.2, 3.2, 3.2), "gold_dark", rotation=(0, 45, 0))
    return cr

def webbed(g, name, c, k, yaw=0, spread=1.0):
    """Vanilla's webbed hand or foot: a flat plane with three long toes and round pads, turned by yaw."""
    x, y, z = c
    rot = (0, yaw, 0)
    m = rotation_matrix(rot)

    def at(dx, dz):
        p = m @ np.array([dx, 0, dz])
        return (x + p[0], y, z + p[2])

    s = 2.6 * k
    g.box(f"{name}_web", at(0, 0), (s, 0, s), "skin_dark", rotation=rot)
    for i in (-1, 0, 1):
        a = i * 0.42 * spread
        tl = s * (0.9 if i else 1.05)
        p = at(math.sin(a) * tl * 0.5, -math.cos(a) * tl * 0.5)
        g.box(f"{name}_toe{i}", (p[0], y + 0.7, p[2]), (k * 0.55, 1.4, tl), "skin",
              rotation=(0, yaw + math.degrees(-a), 0))
        q = at(math.sin(a) * tl, -math.cos(a) * tl)
        g.box(f"{name}_pad{i}", (q[0], y + 0.9, q[2]), (k * 0.9, 1.8, k * 0.9), "skin_light", rotation=rot)


def hind_leg(g, name, sd, hip, knee, ankle, foot, k, thigh, shin, foot_yaw):
    """A folded frog leg: a heavy thigh to the knee, the shin folded back down to the ankle, the foot splayed."""
    tapered(g, name + "_thigh", hip, knee, thigh, thigh * 0.7, "skin")
    g.box(name + "_knee", knee, (thigh * 0.62, thigh * 0.62, thigh * 0.62), "skin", rotation=(0, 45, 0))
    tapered(g, name + "_shin", knee, ankle, shin, shin * 0.7, "skin")
    beam(g, name + "_ankle", ankle, (foot[0], foot[1] + 1.5, foot[2]), shin * 0.55, "skin_dark")
    webbed(g, name + "_foot", foot, k, foot_yaw, 1.2)


def front_leg(g, name, sd, shoulder, elbow, hand, k, w, hand_yaw):
    tapered(g, name + "_upper", shoulder, elbow, w, w * 0.85, "skin")
    g.box(name + "_elbow", elbow, (w * 0.85, w * 0.85, w * 0.85), "skin")
    tapered(g, name + "_fore", elbow, (hand[0], hand[1] + 1.2, hand[2]), w * 0.85, w * 0.65, "skin")
    webbed(g, name + "_hand", hand, k * 0.8, hand_yaw)


# ---- A: The Glowback ----------------------------------------------------------------------------------------------

def glowback(model, tongue):
    rnd = random.Random(5)
    k = 4
    root = model.group("root_body", (0, 0, 0))
    body = root.group("body", (0, 20, 14))
    # a wide, low dome far bigger than the head: the trunk, the hump rising over the hips, the rump falling away
    octo(body, "trunk", (0, 21, 12), (80, 38, 62), "skin", 0.38)
    octo(body, "hump", (0, 40, 20), (62, 20, 44), "skin", 0.4, rot=(-8, 0, 0))
    octo(body, "rump", (0, 28, 42), (58, 26, 20), "skin", 0.4, rot=(32, 0, 0))
    body.box("belly", (0, 3.5, 10), (66, 5, 56), "belly")
    # the large warts: radioactive bulbs crowding the hump, cracked open on glowing cores; smaller down the flanks
    spots = [(0, 54, 22, 9), (-17, 51, 14, 8), (17, 51, 18, 8), (-9, 52, 34, 7), (12, 51, 34, 7),
             (-28, 44, 28, 6.5), (28, 44, 26, 6.5), (0, 50, 6, 6), (-30, 38, 6, 5), (31, 37, 8, 5),
             (-36, 30, 20, 4.5), (36, 30, 22, 4.5), (0, 44, 44, 5.5)]
    for i, (x, y, z, r) in enumerate(spots):
        wart(body, f"wart_{i}", (x, y, z), r, (rnd.uniform(-8, 8), rnd.uniform(-20, 20), -x * 0.8), core=r >= 6)
    hd = root.group("hi_head", (0, 20, -14))
    frog_head(hd, k, 7, -28, tongue=tongue)
    for sd in (-1, 1):
        gland(hd, f"gland_{sd}", (sd * 15, 34, -8), (12, 10, 22), sd * -14)
    crown(hd, "crown", (0, 36.5, -11), 15, 11, (0.75, 0.6, 0.75), tilt=(-8, 0, 0))
    legs = root.group("legs", (0, 0, 0))
    for sd in (-1, 1):
        hind_leg(legs, f"leg_{sd}", sd, (sd * 38, 22, 32), (sd * 48, 18, 8), (sd * 44, 5, 38), (sd * 50, 0.5, 52),
                 5, 20, 11, sd * -40)
        front_leg(legs, f"arm_{sd}", sd, (sd * 18, 14, -24), (sd * 28, 10, -32), (sd * 26, 0.5, -42), 5, 8, sd * -20)


# ---- B: The Stilt Tyrant ------------------------------------------------------------------------------------------

def stilt_tyrant(model, tongue):
    rnd = random.Random(7)
    k = 4
    root = model.group("root_body", (0, 0, 0))
    # the front end rides high on long straight arms: the trunk and head pitched up
    body = root.group("body", (0, 32, 14), (14, 0, 0))
    octo(body, "trunk", (0, 32, 16), (46, 30, 50), "skin", 0.38)
    octo(body, "rump", (0, 32, 40), (40, 24, 14), "skin", 0.4, rot=(28, 0, 0))
    body.box("belly", (0, 17.5, 14), (36, 3, 42), "belly")
    # a ridge of glowing pustules down the back, tallest over the shoulders, smaller pairs beside it
    for i in range(7):
        z = -2 + i * 7
        r = 7 - i * 0.6
        wart(body, f"spine_{i}", (0, 47 + r * 0.2 - i * 0.4, z), r, (rnd.uniform(-6, 6), 0, 0))
        if i % 2 == 0 and i < 6:
            for sd in (-1, 1):
                wart(body, f"side_{i}_{sd}", (sd * 15, 43, z + 3), r * 0.65, (0, 0, -sd * 22), core=i < 4)
    hd = body.group("hi_head", (0, 34, -8), (-8, 0, 0))
    frog_head(hd, k, 24, -20, eye_k=1.15, tongue=tongue)
    for sd in (-1, 1):
        gland(hd, f"gland_{sd}", (sd * 13, 49, -2), (9, 8, 16), sd * -10)
    crown(hd, "crown", (0, 55, -6), 12, 15, (0.8, 0.6, 0.8), tilt=(-10, 0, 0))
    legs = root.group("legs", (0, 0, 0))
    for sd in (-1, 1):
        # over-long hind legs folded high: the knee rises above the back, the shin plunges to a long foot
        hind_leg(legs, f"leg_{sd}", sd, (sd * 20, 26, 32), (sd * 34, 68, 14), (sd * 32, 8, 48), (sd * 36, 0.5, 60),
                 5, 19, 10, sd * -25)
        front_leg(legs, f"arm_{sd}", sd, (sd * 18, 34, -10), (sd * 25, 18, -18), (sd * 25, 0.5, -28), 5, 8, sd * -15)


# ---- C: The Lantern Throat ----------------------------------------------------------------------------------------

def lantern_throat(model, tongue):
    rnd = random.Random(11)
    k = 4
    root = model.group("root_body", (0, 0, 0))
    # sitting up on its haunches, the front raised, so the bladder can hang under the chin
    body = root.group("body", (0, 20, 22), (16, 0, 0))
    octo(body, "trunk", (0, 28, 20), (62, 36, 50), "skin", 0.38)
    octo(body, "rump", (0, 26, 42), (54, 28, 16), "skin", 0.4, rot=(24, 0, 0))
    # a back crowded with warts, big and small packed together, cracked and glowing
    for i in range(20):
        a = rnd.uniform(-1, 1)
        x, z = a * 24, rnd.uniform(2, 40)
        r = rnd.uniform(3.5, 7.5)
        y = 47 - abs(a) * 8
        wart(body, f"wart_{i}", (x, y, z), r, (rnd.uniform(-8, 8), rnd.uniform(-30, 30), -a * 30), core=r > 5)
    hd = body.group("hi_head", (0, 34, -4))
    frog_head(hd, k, 24, -14, tongue=tongue)
    # the throat bladder: the croaking sac swollen into a glowing ball of toxin, the skin stretched over it in bands
    sac = hd.group("sac", (0, 22, -22))
    ball(sac, "bladder", (0, 8, -26), (40, 36, 36), "sac", 0.34)
    octo(sac, "band_z", (0, 8, -26), (41, 37, 2), "vein", 0.34)
    octo(sac, "band_x", (0, 8, -26), (2, 37.5, 37), "vein", 0.34, axis="x")
    sac.box("neck", (0, 24, -20), (26, 6, 20), "skin_dark")
    for sd in (-1, 1):
        gland(hd, f"gland_{sd}", (sd * 15, 47, -2), (12, 10, 20), sd * -12)
    # the heaviest crown: five points a side, slipping off to one side
    crown(hd, "crown", (3, 54, -2), 17, 12, (0.72, 0.6, 0.72), tilt=(-6, 0, -14))
    legs = root.group("legs", (0, 0, 0))
    for sd in (-1, 1):
        hind_leg(legs, f"leg_{sd}", sd, (sd * 32, 22, 42), (sd * 42, 30, 18), (sd * 40, 6, 44), (sd * 46, 0.5, 56),
                 5, 20, 11, sd * -35)
        front_leg(legs, f"arm_{sd}", sd, (sd * 24, 24, -2), (sd * 34, 14, -12), (sd * 32, 0.5, -24), 5, 9, sd * -20)

BUILD = {"A": glowback, "B": stilt_tyrant, "C": lantern_throat}
TONGUE_REACH = 4.5   # blocks, the pose for the pull attack


def build(key, tongue=0.0):
    model = Model(f"occultech_mire_monarch_{key.lower()}" + ("_tongue" if tongue else ""))
    BUILD[key](model, tongue)
    return model


VIEWS = v1.VIEWS + [
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": -18, "height": 1.9, "dist": 10, "player": False},
]
TONGUE_VIEWS = [
    {"name": "tongue_34", "mode": "flat", "camera": "persp", "yaw": -40, "height": 3.5, "dist": 11},
    {"name": "tongue_side", "mode": "silhouette", "camera": "ortho_side"},
]


def main(keys=None, quick=False):
    keys = keys or list(DIRECTIONS)
    if not quick:
        for old in OUT.glob("*"):            # earlier takes stay in git history
            if old.is_dir():
                shutil.rmtree(old)
            elif old.suffix == ".png" or old.name == "README.md":
                old.unlink()
    items = []
    for key in keys:
        title = DIRECTIONS[key]
        out = OUT / key
        out.mkdir(parents=True, exist_ok=True)
        model = build(key)
        model.write_bbmodel(out / f"{model.name}.bbmodel")
        views = [v for v in VIEWS if v["name"] in ("sil_side", "flat_34", "flat_front", "clay_34")] if quick else VIEWS
        v2.run_blender(model.render_json(PALETTE), out, views)
        stats = model.stats()
        (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        v2.run_blender(build(key, TONGUE_REACH).render_json(PALETTE), out, TONGUE_VIEWS)
        if not quick:
            sheet.direction_sheet(out, f"Mire Monarch - {key} {title}", stats, out / "sheet.png")
        items.append((key, title))
        print(key, stats["size_blocks"], stats["cubes"])
    sheet.compare_sheet(OUT, items, OUT / "compare.png", heading="Mire Monarch - three directions (session 1, take 5)",
                        views=("flat_34", "sil_side", "flat_front", "tongue_34"))


if __name__ == "__main__":
    main([a for a in sys.argv[1:] if a in DIRECTIONS], quick="quick" in sys.argv)
