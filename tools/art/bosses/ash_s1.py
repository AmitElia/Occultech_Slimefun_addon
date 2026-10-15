"""The Elder of Ash, session 1 step 3: the full blockout (plan: docs/art/bosses/elder_of_ash/overhaul/plan.md).

The whole toad from cuboids at B2's size (step 1 take 2), with the locked face (step 2 take 2: F3's wide eyes and
angled brow ridges, the Hermit's ash-white brows sweeping out past the eyes, the pipe in his right mouth corner):
- crouched: the front legs propped under the head, elbows out, big four-fingered hands; the hind legs folded at his
  sides (a huge thigh, the shin under it, a long foot with three big toes);
- the body tall and domed, the rump round; the volcano grows out of the back: an ash-grey crust where the warts
  harden, then the basalt cone, concave (steep near the top), a jagged rim round a glowing crater;
- lava streams from the rim down the cone, over the crust and down his sides;
- long tribal markings in ember, painted like a shaman's: a stroke from each eye down the cheek and back along the
  jaw, an arrow down the brow, chevrons on the chin, bands round the arms, a band along each flank with chevrons
  hanging from it, an angular spiral on each thigh;
- smoke from the crater and the pipe's bowl (particles in game; here translucent cubes).

Units are model pixels (16 = one block). The front is -z; his right is +x.

Run from the repository root: python tools/art/bosses/ash_s1.py
"""
import json
import math

import numpy as np
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import ash_face as f1, ash_face2 as f2  # noqa: E402

OUT = ROOT / "docs/art/bosses/elder_of_ash/overhaul/s1_blockout"
beam = f1.beam
MARK_W = 2.0                 # a painted stroke's width
CONE_Z = 6                   # the volcano's axis (z), over the hump
CONE_TOP = 106


# ---- painted strokes -----------------------------------------------------------------------------------------------

def stroke_xy(g, name, pts, z, w=MARK_W):
    """A painted stroke on a face that looks along -z (at depth z): straight runs between the (x, y) points."""
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) + w * 0.9
        g.box(f"{name}_{i}", ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, z), (ln, w, 0.4), "mark",
              rotation=(0, 0, math.degrees(math.atan2(dy, dx))))


def stroke_zy(g, name, pts, x, w=MARK_W):
    """A painted stroke on a face that looks along x (at x): straight runs between the (z, y) points."""
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        dz, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dz, dy) + w * 0.9
        g.box(f"{name}_{i}", (x, (a[1] + b[1]) / 2, (a[0] + b[0]) / 2), (0.4, w, ln), "mark",
              rotation=(-math.degrees(math.atan2(dy, dz)), 0, 0))


# ---- the body --------------------------------------------------------------------------------------------------------

def panel(g, name, a, b, length, thick, mat, axis="z", side=1):
    """A sloped plane whose outer face runs from a to b ((x, y) for a panel along z, (z, y) for one along x), the solid
    behind it, thick deep. side picks which side of a->b is outside."""
    du, dv = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(du, dv)
    nu, nv = dv / ln * side, -du / ln * side             # outward normal
    cu = (a[0] + b[0]) / 2 - nu * thick / 2
    cv = (a[1] + b[1]) / 2 - nv * thick / 2
    ang = math.degrees(math.atan2(dv, du))
    if axis == "z":
        g.box(name, (cu, cv, length[0]), (ln, thick, length[1]), mat, rotation=(0, 0, ang))
    else:
        g.box(name, (length[0], cv, cu), (length[1], thick, ln), mat, rotation=(-ang, 0, 0))


Z0, Z1 = -24, 40             # the body's front (behind the head) and its rump


def taper(g, name, a, b, steps, mat):
    """A limb segment from a to b that tapers: overlapping beams from a, each reaching further and thinner.
    steps: [(fraction of the length, width), ...] from the thickest (shortest) to the thinnest (full length)."""
    for i, (f, w) in enumerate(steps):
        end = tuple(a[k] + (b[k] - a[k]) * f for k in range(3))
        beam(g, f"{name}_{i}", a, end, w, mat, w)


def finger(g, name, base, yaw, length, w=4.0):
    """A slim toad finger lying on the ground from base, yawed (0 = straight ahead), with a round bump at its tip."""
    a = math.radians(yaw)
    tip = (base[0] + math.sin(a) * length, base[1], base[2] - math.cos(a) * length)
    mid = ((base[0] + tip[0]) / 2, base[1], (base[2] + tip[2]) / 2)
    g.box(name, mid, (w, w * 0.85, length), "toe", rotation=(0, -yaw, 0))
    bump = w * 1.75
    g.box(name + "_tip", (tip[0], base[1] + 0.5, tip[2]), (bump, bump * 0.75, bump), "pad", rotation=(0, -yaw, 0))
    g.box(name + "_tip_r", (tip[0], base[1] + 0.5, tip[2]), (bump * 0.95, bump * 0.7, bump * 0.95), "pad",
          rotation=(0, -yaw + 45, 0))


ARM = {"sh": (36, 18, -16), "el": (58, 16, -30), "wr": (52, 5, -44)}
UPPER = [(0.32, 20), (0.62, 18), (1.0, 15)]
FORE = [(0.38, 17), (0.7, 13.5), (1.0, 10.5)]


def front_leg(root, sd):
    """A buff front leg, tapered: a thick upper arm narrowing to the elbow, a forearm with its muscle up by the elbow
    narrowing to a slim wrist, a broad hand with four slim fingers ending in bumps."""
    sh, el, wr = ((sd * v[0], v[1], v[2]) for v in (ARM["sh"], ARM["el"], ARM["wr"]))
    arm = root.group(f"arm_{sd}", sh)
    taper(arm, f"arm_{sd}_upper", sh, el, UPPER, "limb")
    arm.box(f"arm_{sd}_elbow", el, (16, 15, 16), "limb")
    taper(arm, f"arm_{sd}_fore", el, wr, FORE, "limb")
    arm.box(f"arm_{sd}_wrist", wr, (11, 9, 11), "limb")
    arm.box(f"arm_{sd}_palm", (sd * 52, 2.6, -48), (15, 5, 12), "toe")
    for i, yaw in enumerate((-50, -17, 17, 50)):
        finger(arm, f"arm_{sd}_finger{i}", (sd * 52 + sd * yaw * 0.08, 2.4, -51), sd * yaw, 12 if abs(yaw) < 30 else 10)


def body(root):
    """Seen from the front an octagon: the belly tucked under, the flanks bulging, the back sloping in to the volcano's
    foot. The back rises from behind the head, and the rump slopes and tucks down behind; its corners are rounded."""
    b = root.group("body", (0, 24, 8))
    b.box("low", (0, 17, 8), (80, 26, 60), "flank")                   # the belly: y 4..30, x +-40
    b.box("high", (0, 41, 11), (56, 22, 46), "skin")                  # the back: y 30..52
    panel(b, "neck_slope", (-25, 36), (-10, 52), (0, 56), 12, "skin", "x", side=1)
    b.box("belly", (0, 3.5, 8), (74, 3, 56), "belly")
    b.box("chest", (0, 15, -22.6), (58, 18, 1.4), "belly")
    for sd in (-1, 1):
        b.box(f"flank_{sd}", (sd * 43, 21, 8), (6, 18, 56), "flank")                                # the bulge
        panel(b, f"tuck_{sd}", (sd * 46, 12), (sd * 39, 3.6), (8, 54), 7, "flank", "z", side=-sd)  # under the belly
        panel(b, f"slope_{sd}", (sd * 46, 30), (sd * 28, 52), (8, 52), 10, "skin", "z", side=sd)
    panel(b, "rump_slope", (30, 52), (41, 43), (0, 54), 10, "skin", "x", side=-1)      # the rump curves over and down
    panel(b, "rump_back", (40, 44.5), (46, 26), (0, 66), 10, "flank", "x", side=-1)
    panel(b, "rump_tuck", (46, 26), (42, 5), (0, 70), 8, "flank", "x", side=-1)
    for i, (x, y, z, s) in enumerate(((-46.2, 22, -12, 6), (46.2, 18, 14, 7), (-46.2, 26, 22, 5), (46.2, 24, -14, 5))):
        b.box(f"wart{i}", (x + (0.8 if x > 0 else -0.8), y, z), (1.6, s, s), "wart")
    return b


def hind_leg(root, sd):
    """The folded hind leg at his side, a Z seen from the side: a round thigh muscle at the hip, the thigh tapering
    down and forward to the knee beside the belly, the shin back along the ground under it, the long foot forward with
    three slim toes ending in bumps. Returns the leg's group and the hip's centre (the spiral marking sits on the hip)."""
    hip, knee, ankle = (sd * 50, 24, 30), (sd * 54, 10, 1), (sd * 55, 5, 36)
    leg = root.group(f"leg_{sd}", hip)
    leg.box(f"hip_{sd}", hip, (22, 28, 28), "flank")
    leg.box(f"hip_{sd}_round", hip, (21.6, 23, 23), "flank", rotation=(45, 0, 0))       # an octagon from the side
    taper(leg, f"thigh_{sd}", hip, knee, [(0.35, 21), (0.65, 17), (1.0, 13)], "flank")
    leg.box(f"knee_{sd}", knee, (13, 12, 12), "flank")
    # the shin's thin beam starts a third of the way down: one beam the full 35 long breaks the client's item-model
    # limit (-16..32) and draws as a purple-black missing model in game
    taper(leg, f"shin_{sd}", knee, ankle, [(0.5, 10)], "limb")
    mid = tuple(knee[k] + (ankle[k] - knee[k]) * 0.3 for k in range(3))
    beam(leg, f"shin_{sd}_1", mid, ankle, 8, "limb", 8)
    leg.box(f"foot_{sd}", (sd * 58, 2.0, 18), (12, 4, 32), "toe")
    for i, yaw in enumerate((-20, 6, 32)):
        finger(leg, f"toe_{sd}_{i}", (sd * 58 + sd * (i - 1) * 3.5, 2.0, 3), sd * yaw, 13)
    return leg, hip


# ---- the volcano: it grows out of the back in rings that get steeper as they rise ------------------------------------

KF, KB = 0.62, 0.85          # the foot ring is squashed front and back to sit on the back (front: over the neck)


def ring(n, r, y, a0=0.0, kf=1.0, kb=1.0):
    for i in range(n):
        a = math.radians(a0 + i * 360 / n)
        k = kf if math.cos(a) > 0 else kb
        yield i, a, (math.sin(a) * r, y, CONE_Z - math.cos(a) * r * k)


def slab_ring(v, name, n, r0, y0, r1, y1, width, thick, mats, a0=0.0, kf=1.0, kb=1.0):
    """n slabs leaning in, their outer faces running from radius r0 at y0 up to r1 at y1: one ring of a cone."""
    ln = math.hypot(r0 - r1, y1 - y0)
    tilt = math.degrees(math.atan2(r0 - r1, y1 - y0))
    rc = (r0 + r1) / 2 - thick / 2 * math.cos(math.radians(tilt))
    yc = (y0 + y1) / 2 + thick / 2 * math.sin(math.radians(tilt))
    for i, a, p in ring(n, rc, yc, a0, kf, kb):
        v.box(f"{name}_{i}", p, (width, ln, thick), mats[i % len(mats)], rotation=(tilt, -math.degrees(a), 0))


FOOT = (36.5, 40, 22, 64)       # r0, y0, r1, y1: the foot ring, lying on the back's slope and turning to rock
SKIRT = (24, 60, 17, 75)
CONE = (19, 70, 9, CONE_TOP)
CAP_Y = CONE_TOP - 12        # where the cap (blown off at 33%) starts


def volcano(root):
    v = root.group("volcano", (0, 52, CONE_Z))
    v.box("core_low", (0, 56, CONE_Z), (44, 14, 36), "skin_ash")
    v.box("core_mid", (0, 69, CONE_Z), (32, 14, 28), "ash_dark")
    v.box("core_high", (0, (75 + CAP_Y) / 2, CONE_Z), (15, CAP_Y - 75, 15), "basalt")     # stops at the cap
    # the foot: skin turning to ash, lying on the back's slope (as steep as it), studded with hardened warts
    slab_ring(v, "foot", 16, *FOOT, 15, 8, ("skin_ash", "ash", "skin_ash", "ash_dark"), 0, KF, KB)
    slab_ring(v, "skirt", 12, *SKIRT, 14, 7, ("ash_dark", "basalt", "ash_dark"), 8, 0.8, 0.9)
    # the cone up to its cap; the cap (the top, the rim and the crater) is its own bone, so at 33% it can be hidden and
    # the blown-open top shown instead (session 6)
    r_cap = CONE[0] + (CONE[2] - CONE[0]) * (CAP_Y - CONE[1]) / (CONE[3] - CONE[1])
    slab_ring(v, "cone", 12, CONE[0], CONE[1], r_cap, CAP_Y + 1, 12, 7, ("basalt", "basalt", "basalt_lit"), 15, 0.85, 0.9)
    cap = v.group("cone_cap", (0, CAP_Y, CONE_Z))
    cap.box("core_cap", (0, (CAP_Y + CONE_TOP - 3) / 2, CONE_Z), (11, CONE_TOP - 3 - CAP_Y, 11), "basalt")
    slab_ring(cap, "cap", 12, r_cap + 0.4, CAP_Y - 0.5, CONE[2], CONE_TOP, 12, 7, ("basalt", "basalt", "basalt_lit"), 15,
              0.85, 0.9)
    for i, a, p in ring(9, 9.5, CONE_TOP, 5, 0.85, 0.9):
        h = (4, 6, 3, 5, 7, 3, 5, 4, 6)[i]
        cap.box(f"rim_{i}", (p[0], CONE_TOP - 1 + h / 2, p[2]), (5.5, h, 4), "basalt", rotation=(12, -math.degrees(a), 0))
    cap.box("crater", (0, CONE_TOP - 1.0, CONE_Z), (13, 1, 13), "lava")
    cap.box("crater_hot", (0, CONE_TOP - 0.4, CONE_Z), (6, 1, 6), "lava_hot")
    # the blown top (33%): the cap gone, broken stumps leaning out round a crater twice as wide, lava welling in it
    blown = v.group("cone_blown", (0, CAP_Y, CONE_Z))
    blown.visible = False
    for i, a, p in ring(11, r_cap - 1.5, CAP_Y, 9, 0.85, 0.9):
        h = (5, 2, 7, 3, 4, 8, 2, 6, 3, 5, 4)[i]
        blown.box(f"stump_{i}", (p[0], CAP_Y - 1 + h / 2, p[2]), (6.5, h, 5), "basalt_lit" if i % 3 == 0 else "basalt",
                  rotation=(-24 - (i % 3) * 8, -math.degrees(a), 0))
    blown.box("crater_blown", (0, CAP_Y + 0.6, CONE_Z), (2 * r_cap - 4, 1, 2 * r_cap - 4), "lava")       # above the core
    blown.box("crater_blown_hot", (0, CAP_Y + 1.2, CONE_Z), (r_cap, 1, r_cap), "lava_hot")
    # hardened warts: rock lumps on the foot, and smaller skin warts below them on the back's slope
    for i, a, p in ring(11, 31, 52, 12, KF, KB):
        s = 5 + (i * 7) % 4
        v.box(f"rock_{i}", p, (s, s * 0.8, s), "ash_dark", rotation=(20, -math.degrees(a) + 15, 0))
    for i, a, p in ring(9, 37.5, 41, 30, 0.7, 0.9):
        if abs(math.sin(a)) > 0.45:                     # only on the side slopes
            v.box(f"wart_slope_{i}", p, (4, 3, 4), "wart", rotation=(36, -math.degrees(a), 0))
    return v


def cone_r(y):
    """The mountain's outer radius at height y (sides; front and back are squashed)."""
    if y >= 72:
        r0, y0, r1, y1 = CONE
    elif y >= 62:
        r0, y0, r1, y1 = SKIRT
    else:
        r0, y0, r1, y1 = FOOT
    return r0 + (r1 - r0) * (y - y0) / (y1 - y0)


def lava(root):
    """Lava streams like real flows, not a matched set: each starts at its own notch of the rim and runs its own length,
    meandering down the cone. Where a raised rock sits in its way it splits round it; at the cone's foot and the back's
    edge it pools wider; it ends in a drip down a flank or the rump, or stops short in a cooling bulb.

      the main flow   right side, the longest: forks round a rock high on the cone; the right branch runs over the
                      shoulder and down the right flank, the left branch dies on the foot
      the left flow   down the left side to the flank; a branch splits off at the foot round a rock and spills
                      back over the rump
      the back flow   down the back; forks round a rock low on the cone, both arms down the rump to different lengths
      a short flow    front-left, stops a third of the way down in a cooling bulb
      a trickle       front-right, thin, barely leaves the rim
    """
    g = root.group("lava", (0, 52, CONE_Z))
    vol = next(ch for ch in root.children if getattr(ch, "name", "") == "volcano")

    def at(a_deg, y, out=2.2):
        a = math.radians(a_deg)
        r = cone_r(y) + out
        k = (KF if y < 62 else 0.85) if math.cos(a) > 0 else (KB if y < 62 else 0.9)
        return (math.sin(a) * r, y, CONE_Z - math.cos(a) * r * k)

    def side(x_sd, z, y):
        """On the back's slope (from the flank's top at y 30 up to the back at y 52) or down the flank below it."""
        if y >= 30:
            return (x_sd * (46 - 18 * (y - 30) / 22 + 0.7), y, z)
        return (x_sd * 46.7, y, z)

    def rump(x, y):
        if y >= 43:
            z = 30 + 11 * (52 - y) / 9
        elif y >= 26:
            z = 40 + 6 * (44.5 - y) / 18.5
        else:
            z = 46 - 4 * (26 - y) / 21
        return (x, y, z + 0.8)

    def dense(ctrl, phase, amp=3.0):
        """Control points (angle, y) on the cone made into a meandering line, a point every 4 units of height."""
        out = []
        for (a0, y0), (a1, y1) in zip(ctrl, ctrl[1:]):
            n = max(1, int(abs(y1 - y0) / 4))
            for i in range(n):
                t = i / n
                y = y0 + (y1 - y0) * t
                a = a0 + (a1 - a0) * t + amp * math.sin(phase + y * 0.33)
                out.append(at(a, y))
        out.append(at(*ctrl[-1]))
        return out

    def flow(name, pts, w0, w1, pool_at=(), end="drip"):
        n = len(pts) - 1
        for i, (p, q) in enumerate(zip(pts, pts[1:])):
            w = w0 + (w1 - w0) * i / max(1, n - 1)
            d = np.array(q) - np.array(p)
            d = d / (np.linalg.norm(d) or 1) * 0.6         # each run overlaps the next a little: no notches
            beam(g, f"{name}_{i}", tuple(np.array(p) - d), tuple(np.array(q) + d), w, "lava", 2.0)
        for k, i in enumerate(pool_at):                     # widening where the slope eases
            p, q = np.array(pts[i]), np.array(pts[min(i + 1, n)])
            beam(g, f"{name}_pool{k}", tuple(p), tuple(p + (q - p) * 0.6), w0 * 1.9, "lava", 1.2)
        last, before = np.array(pts[-1]), np.array(pts[-2])
        if end == "drip":                                   # a drip hanging off the end, and a drop below it
            g.box(f"{name}_drip", (last[0], last[1] - 2.2, last[2]), (w1 * 0.8, 3.6, w1 * 0.8), "lava")
            g.box(f"{name}_drop", (last[0], last[1] - 5.6, last[2]), (w1 * 0.55, 2, w1 * 0.55), "lava_hot")
        else:                                               # a cooling bulb where it stopped
            beam(g, f"{name}_bulb", tuple(before + (last - before) * 0.5), tuple(last), w1 * 1.7, "lava", 1.6)
        beam(g, f"{name}_core", tuple(pts[0]), tuple(pts[min(3, n)]), max(1.2, w0 * 0.35), "lava_hot", 1.6)

    def rock(name, a_deg, y, s=6):
        """A raised rock in a stream's way: the stream splits round it."""
        p = at(a_deg, y, out=1.5)
        vol.box(name, p, (s, s * 0.8, s), "basalt_lit", rotation=(0, -a_deg, 0))

    top = CONE_TOP - 0.5
    # the main flow, right side
    main = dense([(66, top), (72, 94), (79, 82)], 0.4)
    right = dense([(79, 82), (88, 72), (86, 62), (91, 52), (92, 46)], 1.7)
    zr = right[-1][2]
    right += [side(1, zr + 1, 40), side(1, zr + 2, 30), side(1, zr + 1, 22), side(1, zr + 3, 12)]
    left_arm = dense([(79, 82), (70, 74), (63, 64), (59, 54)], 2.9, 2.0)
    rock("lava_rock_main", 80, 76)
    flow("lava_main", main + right[1:], 4.6, 3.0, pool_at=(len(main) + len(right) - 9,))
    flow("lava_main_fork", left_arm, 3.0, 2.2, end="bulb")
    # the left flow
    lf = dense([(-116, top), (-122, 94), (-114, 82), (-122, 70), (-128, 58), (-124, 46)], 2.2)
    zl = lf[-1][2]
    lf += [side(-1, zl - 1, 40), side(-1, zl, 29), side(-1, zl - 2, 18)]
    flow("lava_left", lf, 4.0, 2.8, pool_at=(len(lf) - 5,))
    rock("lava_rock_left", -134, 54, 5)
    spill = dense([(-128, 58), (-144, 52), (-150, 47)], 0.8, 1.5)
    xs = spill[-1][0]
    spill += [rump(xs * 0.9, 44), rump(xs * 0.9, 36), rump(xs * 0.95, 28)]
    flow("lava_left_spill", spill, 2.8, 2.0)
    # the back flow, forking low on the cone, both arms down the rump to different lengths
    back = dense([(172, top), (178, 92), (170, 80), (175, 68), (178, 60)], 3.6)
    flow("lava_back", back, 4.2, 3.4)
    rock("lava_rock_back", 182, 55, 5)
    arm_a = dense([(178, 60), (170, 52), (168, 47)], 0.3, 1.0)
    arm_a += [rump(arm_a[-1][0], 44), rump(arm_a[-1][0] * 1.1, 34), rump(arm_a[-1][0] * 1.15, 22), rump(arm_a[-1][0] * 1.2, 13)]
    arm_b = dense([(178, 60), (192, 52), (196, 47)], 1.1, 1.0)
    arm_b += [rump(arm_b[-1][0], 44), rump(arm_b[-1][0] * 1.05, 36)]
    flow("lava_back_a", arm_a, 3.2, 2.4, pool_at=(2,))
    flow("lava_back_b", arm_b, 2.8, 2.2)
    # a short flow that cooled a third of the way down, and a thin trickle
    flow("lava_short", dense([(-34, top), (-40, 96), (-33, 87), (-39, 80)], 1.3, 2.0), 3.4, 2.4, end="bulb")
    flow("lava_trickle", dense([(18, top), (14, 99), (21, 93)], 0.2, 1.5), 2.2, 1.8, end="bulb")


# ---- the markings: a few ember strokes, laid on by hand ------------------------------------------------------------
# Take 2 (user, 2026-10-14: "too many, rework them to look more natural"): no sawtooth, chevrons, bars or angular
# spirals. Each mark is one curved stroke that swells in the middle and tapers to a point at both ends, a little uneven,
# like paint pulled by a finger, and they follow the toad's forms. Four kinds in all: a sweep under each eye, the long
# stripe down each flank, a crescent on each haunch, a band round each wrist.

def curve(p0, p1, p2, n=10):
    """Points along a quadratic curve through p0 and p2, pulled towards p1."""
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c for a, b, c in zip(p0, p1, p2)))
    return out


def stroke_widths(n, w, wobble=0.12, seed=0.0):
    """Widths along a stroke: swelling in the middle, pointed at both ends, a little uneven."""
    return [max(0.6, w * math.sin(math.pi * (i + 0.5) / n) ** 0.7 * (1 + wobble * math.sin(seed + i * 2.1)))
            for i in range(n)]


def brush_xy(g, name, pts, z, w, seed=0.0):
    """A tapered stroke on a face that looks along -z."""
    for i, ((a, b), wi) in enumerate(zip(zip(pts, pts[1:]), stroke_widths(len(pts) - 1, w, seed=seed))):
        stroke_xy(g, f"{name}_{i}", [a, b], z, wi)


def brush_zy(g, name, pts, x, w, seed=0.0):
    """A tapered stroke on a face that looks along x."""
    for i, ((a, b), wi) in enumerate(zip(zip(pts, pts[1:]), stroke_widths(len(pts) - 1, w, seed=seed))):
        stroke_zy(g, f"{name}_{i}", [a, b], x, wi)


def face_markings(h):
    """Tribal face paint: three stripes running down from under each eye over the snout's slope and down the cheek,
    the middle one longest, each tapering to a point, the outer ones leaning a little out (take 2's sweep across the
    cheek read as a moustache; take 1's single strokes by the mouth read as tusks)."""
    x, y, z = f1.EYE_AT
    # the snout's slope under the eyes: a box turned 45 degrees about x, centre (y 35.4, z -56.4), half-diagonal 5.66
    by, bz, hd = 35.4, -56.4, 8 * math.sqrt(2) / 2
    for sd in (-1, 1):
        for i, (dx, lean, bottom, w) in enumerate(((-5.5, -0.6, 25.5, 2.0), (0.0, 0.4, 22.6, 2.4), (5.5, 1.6, 26.5, 2.0))):
            cx = sd * (x + dx)
            # down the slope's upper face (facing up and forward) and its lower face (down and forward)
            h.box(f"mark_cheek_{sd}_{i}_up", (cx, by + hd / 2 + 0.2, bz - hd / 2 - 0.2), (w, hd, 0.4), "mark",
                  rotation=(45, 0, 0))
            h.box(f"mark_cheek_{sd}_{i}_lo", (cx, by - hd / 4 - 0.2, bz - hd * 0.75 - 0.2), (w, hd / 2, 0.4), "mark",
                  rotation=(-45, 0, 0))
            # then down the cheek, tapering to a point
            top = by - hd / 2 + 0.2                               # where the slope meets the face (y about 32.4)
            pts = [(cx + sd * lean * t, top - (top - bottom) * t) for t in (0, 0.25, 0.5, 0.75, 1.0)]
            for k, ((p0, p1), wk) in enumerate(zip(zip(pts, pts[1:]), (w, w * 0.9, w * 0.7, w * 0.45))):
                stroke_xy(h, f"mark_cheek_{sd}_{i}_{k}", [p0, p1], -59.3, max(0.8, wk))


def arm_markings(root):
    """One band round each wrist."""
    for sd in (-1, 1):
        sh, el, wr = ((sd * v[0], v[1], v[2]) for v in (ARM["sh"], ARM["el"], ARM["wr"]))
        g = root.group(f"arm_marks_{sd}", el)
        f2.band(g, f"mark_fore_{sd}_0", el, wr, 0.78, 10.5, 10.5)


def flank_markings(b, sd):
    """The long stripe down each flank, like a toad's lateral stripe: from behind the head, dipping along the body,
    rising to fade before the haunch."""
    brush_zy(b, f"mark_flank_{sd}", curve((-22.0, 27.0), (-4.0, 21.0), (15.0, 26.5), 12), sd * 46.2, 3.2,
             seed=2.0 + sd)


def slope_markings(b, sd):
    """None: the back is left to the skin and the lava."""


def thigh_markings(leg, sd, c):
    """A crescent on the outside of each haunch, opening towards the tail."""
    x = c[0] + sd * 11.1
    cy, cz = c[1], c[2]
    brush_zy(leg, f"mark_thigh_{sd}", curve((cz - 8, cy + 9), (cz - 13, cy - 1), (cz - 4, cy - 10), 10), x, 3.0,
             seed=0.7 + sd)


# ---- the whole toad --------------------------------------------------------------------------------------------------

def build(model):
    root = model.group("root", (0, 0, 0))
    b = body(root)
    volcano(root)
    lava(root)
    for sd in (-1, 1):
        front_leg(root, sd)
        thigh, c = hind_leg(root, sd)
        thigh_markings(thigh, sd, c)
        flank_markings(b, sd)
        slope_markings(b, sd)
    arm_markings(root)
    h = root.group("hi_head", (0, 26, -26))
    f1.head_base(h)
    x, y, z = f1.EYE_AT
    for sd in (-1, 1):
        front = f1.eye(h, sd, (sd * x, y, z), open_=0.85)
        h.box(f"brow_{sd}", (sd * (x + 0.5), y + 6.8, front + 2.6), (21, 3.6, 8), "brow", rotation=(-8, 0, sd * 11))
        f2.ash_brows(h, sd, x, y, front)
    face_markings(h)
    f1.pipe(h, "clenched")
    smoke = root.group("smoke", (0, CONE_TOP, CONE_Z))
    for i in range(6):                                  # the crater's plume (particles in game)
        t = i / 5
        s = 6 + 10 * t
        smoke.box(f"plume{i}", (math.sin(i * 1.3) * 3, CONE_TOP + 7 + 30 * t, CONE_Z + 10 * t), (s, s, s),
                  "smoke" if i < 3 else "smoke_thin", rotation=(i * 13, i * 31, i * 7))
    return root


VIEWS = [
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front"},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
    {"name": "front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 2.4, "dist": 16, "target_z": 3.2},
    {"name": "three_quarter", "mode": "flat", "camera": "persp", "yaw": 38, "height": 4.0, "dist": 15, "target_z": 2.8},
    {"name": "side", "mode": "flat", "camera": "persp", "yaw": 90, "height": 2.6, "dist": 15, "target_z": 2.8,
     "player": False},
    {"name": "back", "mode": "flat", "camera": "persp", "yaw": 150, "height": 4.4, "dist": 15, "target_z": 2.6,
     "player": False},
    {"name": "player_eye", "mode": "flat", "camera": "persp", "yaw": -22, "height": 1.62, "dist": 10, "target_z": 3.0,
     "lens": 24, "player": False},
    {"name": "clay", "mode": "clay", "camera": "persp", "yaw": -32, "height": 3.6, "dist": 15, "target_z": 2.8,
     "player": False},
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "idle"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    model = Model("occultech_elder_of_ash_blockout")
    build(model)
    model.write_bbmodel(out / f"{model.name}.bbmodel")
    f1.render(model, out, VIEWS, {"player_at": [-5.2, 1.0]})
    stats = model.stats()
    (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(stats)
    sheet.compare_sheet(OUT, [("idle", "front, three-quarter, side, back")], OUT / "views_a.png",
                        heading="The Elder of Ash - blockout (session 1, step 3)",
                        views=("front", "three_quarter", "side", "back"))
    sheet.compare_sheet(OUT, [("idle", "player's eye, clay, silhouettes")], OUT / "views_b.png",
                        heading="The Elder of Ash - blockout, more views",
                        views=("player_eye", "clay", "sil_front", "sil_side"))


if __name__ == "__main__":
    main()
