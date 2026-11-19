"""Heartwood Horror, session 1: blockouts of the combined direction the user picked (2026-11-18).

The user's brief, combined from five pitches:
- a hunched torso on long thin stilt legs, 4 or 5 long arms that drag behind it, nothing symmetric: a twisted,
  grown tree (the Stilt Walker's silhouette);
- an older creaking curled up like a foetus, sealed in a shell of resin that is part of the giant's chest (the Amber
  Reliquary);
- many limbs covered in eyeblossoms (the Eyeblossom Watcher);
- pale hanging moss on it as texture, never a veil (the Mourning Willow);
- its face is a creaking heart hanging below the torso like a lantern (the Stilt Walker).

The takes share all of that and differ in how the body is put together:

  A  the Stoop    two backward-kneed legs; the trunk bent over nearly level; four arms (a high spidery elbow and a
                  drooping one on the right, a wide one on the left, one growing out of the hump and arching over the
                  back); the resin womb bulges from the chest with the sleeper's face and knees pressing out of it; the
                  lantern hangs on a short root under the trunk's front
  B  the Split    the trunk split open down the front like a lightning-struck oak, the two halves bowed apart around the
                  womb; five arms (three right, two left, all different lengths); one straight stilt leg and one
                  backward-kneed leg; the lantern hangs from the bottom of the split
  C  the Crutch   the trunk twisted a third of a turn above the hips; five arms, one of them planted ahead as a crutch it
                  knuckle-walks on; the resin shell cracked open on one side, the sleeper half out; the lantern swings
                  on a long root

Each is shown resting (stalking), walking (the arms dragging) and striking (one great arm raised over its head).
Model units: 16 = one block, y up, it faces -z, its right side is +x. Colours are blockout zones; the resin is drawn
see-through in the flat views only to show the sleeper inside (whether resin can be see-through in game is a session 4
question).

Run from the repository root: python tools/art/bosses/heartwood_s1.py [A B C] [quick]
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
from bosses import volley_crone_s2 as v2  # noqa: E402
from bosses.monarch_s1 import ball  # noqa: E402

OUT = ROOT / "docs/art/bosses/heartwood_horror/overhaul/s1_blockout"
PALETTE = {
    "bark": (92, 84, 80), "bark_dark": (64, 58, 56), "wood": (196, 186, 172), "root": (104, 94, 88),
    "resin": (228, 132, 34, 140), "resin_dark": (176, 86, 22), "sleeper": (118, 110, 106), "sleeper_eye": (255, 150, 40),
    "heart": (238, 136, 36), "heart_frame": (70, 62, 58), "glow": (255, 196, 90),
    "petal": (232, 228, 222), "bud": (150, 146, 150), "bloom": (255, 146, 36), "moss": (156, 166, 154),
}
REST, WALK, STRIKE = "rest", "walk", "strike"
POSES = (REST, WALK, STRIKE)
PELVIS = np.array([0.0, 62.0, 12.0])


def _n(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


def world(g, p):
    return (g.world_matrix() @ np.array([*p, 1.0]))[:3]


def cbox(g, name, a, b, w, d, mat, twist=0.0):
    """A box from a to b, w by d in section, turned `twist` degrees about its own length."""
    a, b = np.array(a, float), np.array(b, float)
    dx, dy, dz = b - a
    roll = math.degrees(math.atan2(dy, dx))
    yaw = math.degrees(math.atan2(-dz, math.hypot(dx, dy)))
    return g.box(name, tuple((a + b) / 2), (float(np.linalg.norm(b - a)) + min(w, d) * 0.35, w, d), mat,
                 rotation=(twist, yaw, roll))


def curve(ctrl, n):
    """n+1 points along a Catmull-Rom curve through the control points."""
    c = [np.array(p, float) for p in ctrl]
    c = [2 * c[0] - c[1]] + c + [2 * c[-1] - c[-2]]
    segs = len(ctrl) - 1
    out = []
    for k in range(n + 1):
        u = k / n * segs
        i = min(int(u), segs - 1)
        t = u - i
        p0, p1, p2, p3 = c[i], c[i + 1], c[i + 2], c[i + 3]
        out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return out


def branch(g, name, ctrl, w0, w1, n=8, amp=1.6, seed=0, mat="bark", knots=True):
    """A gnarled, twisting branch along a curve: thick at the base, tapering hard, a little crooked, a knot here and
    there. Returns its points and widths."""
    pts = curve(ctrl, n)
    rng = np.random.default_rng(seed)
    for i in range(1, n):
        d = _n(pts[i + 1] - pts[i - 1])
        side = _n(np.cross(d, [0, 1, 0]) if abs(d[1]) < 0.9 else np.cross(d, [1, 0, 0]))
        up = np.cross(side, d)
        pts[i] = pts[i] + (side * rng.uniform(-1, 1) + up * rng.uniform(-1, 1)) * amp
    ws = [w1 + (w0 - w1) * (1 - i / n) ** 1.5 for i in range(n + 1)]
    for i in range(n):
        w = (ws[i] + ws[i + 1]) / 2
        tw = 5 * i + seed * 7
        cbox(g, f"{name}{i}", pts[i], pts[i + 1], w, w * 0.9, mat, tw)
        if w > 5:
            cbox(g, f"{name}{i}_c", pts[i], pts[i + 1], w * 0.78, w * 0.7, mat, tw + 45)
        if knots and i in (2, 5) and w > 4:
            k = w * 1.35
            g.box(f"{name}_knot{i}", tuple(pts[i]), (k, k * 0.8, k), "bark_dark",
                  rotation=(17 * i, 31 * i + seed, 23 * i))
    return pts, ws


def flower(g, name, p, up=(0, 1, 0), open_=True, s=8.0):
    """An eyeblossom on the bark: open = four white petals in an X round an orange eye; closed = a grey bud."""
    p, up = np.array(p, float), _n(up)
    pitch = math.degrees(math.atan2(-up[2], up[1])) if abs(up[1]) > 0.2 else (90 if up[2] < 0 else -90)
    roll = math.degrees(math.asin(np.clip(up[0], -1, 1)))
    rot = (pitch, 0, -roll)
    if open_:
        for k in (0, 1):
            g.box(f"{name}_petal{k}", tuple(p + up * 1.2), (s, 1.2, s * 0.38), "petal",
                  rotation=(rot[0], 45 + 90 * k, rot[2]))
        g.box(f"{name}_eye", tuple(p + up * 2.0), (s * 0.36, 1.4, s * 0.36), "bloom", rotation=rot)
    else:
        g.box(f"{name}_bud", tuple(p + up * s * 0.4), (s * 0.34, s * 0.8, s * 0.34), "bud", rotation=rot)


def moss(g, name, top, length, yaw=0.0):
    """A strand of pale hanging moss: two crossed planes hanging straight down from top."""
    top = np.array(top, float)
    c = top - [0, length / 2, 0]
    g.box(f"{name}_a", tuple(c), (3.2, length, 0.5), "moss", rotation=(0, yaw, 0))
    g.box(f"{name}_b", tuple(c), (3.2, length * 0.8, 0.5), "moss", rotation=(0, yaw + 90, 0))


def claws(g, name, hand, back, n=3, length=16, spread=30):
    """Root fingers fanning out from the hand along `back` (the way they trail), the middle one longest."""
    back = _n(back)
    side = _n(np.cross(back, [0, 1, 0])) if abs(back[1]) < 0.95 else np.array([1.0, 0, 0])
    for i in range(n):
        a = math.radians(-spread + 2 * spread * i / max(1, n - 1))
        d = _n(back * math.cos(a) + side * math.sin(a))
        ln = length * (1.25 if i == n // 2 else 0.9)
        mid = hand + d * ln * 0.55
        tip = hand + d * ln
        if hand[1] < 10:
            mid[1], tip[1] = max(mid[1], 2.0), max(tip[1], 1.0)
        tip = tip + side * (1.5 if i % 2 else -1.5)
        cbox(g, f"{name}{i}a", hand, mid, 3.6, 3.2, "root", i * 20)
        cbox(g, f"{name}{i}b", mid, tip, 2.6, 2.4, "root", i * 20 + 30)


# ---- the trunk --------------------------------------------------------------------------------------------------------

SPINE = [(0, 62, 12), (1, 80, 10), (0, 94, 0), (-1, 97, -18), (1, 86, -34)]
SPINE_W = (22, 30, 34, 26, 20)


def trunk(t, split=False):
    """The hunched trunk in the upper group: up from the hips, over a hump, bent down at the front; twisted and
    chamfered like a grown trunk, broken branches on the hump."""
    pts = curve(SPINE, 6)
    ws = np.interp(np.linspace(0, 4, 7), range(5), SPINE_W)
    for i in range(6):
        w = (ws[i] + ws[i + 1]) / 2
        a, b = pts[i], pts[i + 1]
        if split and i >= 3:   # two halves bowed apart down the front, round the womb
            for s, tag in ((-1, "left"), (1, "right")):
                bow = np.array([s * (6 + 3 * (i - 2)), 0, 0])
                cbox(t, f"trunk{i}_{tag}", a + bow, b + bow + [s * 3, 0, 0], w * 0.42, w * 0.8, "bark", 10 * i * s)
                cbox(t, f"split_edge{i}_{tag}", a + bow + [-s * w * 0.22, -3, 0], b + bow + [-s * w * 0.2, -3, 0],
                     1.6, w * 0.5, "wood")
        else:
            cbox(t, f"trunk{i}", a, b, w, w * 0.86, "bark", 4 * i)
            cbox(t, f"trunk{i}_c", a, b, w * 0.84, w * 0.76, "bark", 4 * i + 45)
            cbox(t, f"ridge{i}", a + [w * 0.32, 2, 0], b + [w * 0.3, 2, 0], 4, 5, "bark_dark", 12 * i)
    ball(t, "hump", (0, 100, -6), (30, 14, 30), "bark", rot=(0, 18, -6))
    if not split:
        ball(t, "brow", (1, 86, -36), (22, 16, 18), "bark_dark", rot=(20, -14, 8))
    branch(t, "stub_a", [(-4, 104, -2), (-9, 113, 6), (-8, 121, 16)], 7, 2.5, n=4, seed=3)
    branch(t, "stub_b", [(8, 103, -12), (14, 111, -16), (22, 114, -10)], 6, 2.4, n=4, seed=5)
    t.box("stub_b_end", (22, 114, -10), (3.4, 3.4, 3.4), "wood")


def sleeper(t, c, pitch=-30, out=0.0):
    """An older creaking curled up like a foetus (vanilla creaking parts at 1.5x): the head bowed onto its knees,
    the long arms wrapped round its shins. out pushes it forward (its face breaks the resin's surface)."""
    g = t.group("sleeper", c, (pitch, 8, 0))
    c = np.array(c, float) + [0, 0, -out]
    k = 1.5
    g.box("sleeper_body", tuple(c + [0, 0, 3]), (6 * k, 11 * k, 5 * k), "sleeper", rotation=(30, 0, 0))
    g.box("sleeper_head", tuple(c + [0, 8, -6]), (6 * k, 10 * k, 6 * k), "sleeper", rotation=(-58, 0, 0))
    g.box("sleeper_crown", tuple(c + [0, 16, -12]), (6 * k, 3 * k, 6 * k), "bark_dark", rotation=(-58, 0, 0))
    for s in (-1, 1):
        g.box(f"sleeper_leaf{s}", tuple(c + [s * 9, 12, -8]), (0.6, 13, 10), "bark_dark", rotation=(-58, 0, s * 20))
        g.box(f"sleeper_eye{s}", tuple(c + [s * 2.2, 5, -13.2]), (2, 1.4, 0.4), "sleeper_eye", rotation=(-58, 0, 0))
        g.box(f"sleeper_shin{s}", tuple(c + [s * 6, -2, -8]), (3 * k, 14 * k, 3 * k), "sleeper", rotation=(-10, 0, 0))
        g.box(f"sleeper_arm{s}", tuple(c + [s * 9, 0, -4]), (3 * k, 16 * k, 3 * k), "sleeper",
              rotation=(-70, s * 20, 0))


def womb(t, kind):
    """The resin shell in the chest, under the hunched trunk, holding the sleeper."""
    if kind == "bulge":       # A: a lump bulging from the chest, the sleeper's face and knees pressing out
        c = (1, 76, -20)
        ball(t, "womb", c, (26, 30, 24), "resin", rot=(-34, 6, 0))
        sleeper(t, c, pitch=-40, out=3.0)
        for i, (x, y, z) in enumerate(((-12, 86, -16), (13, 85, -14), (-9, 64, -20), (11, 65, -19))):
            t.box(f"womb_rim{i}", (x, y, z), (7, 6, 10), "resin_dark", rotation=(i * 30, i * 50, i * 20))
    elif kind == "split":     # B: in the split, the trunk's halves round it
        c = (0, 82, -24)
        ball(t, "womb", c, (18, 30, 22), "resin", rot=(-40, 0, 0))
        sleeper(t, c, pitch=-46)
    else:                     # C: cracked open on the right, the sleeper half out
        c = (4, 75, -21)
        ball(t, "womb", (c[0] - 4, c[1], c[2] + 2), (22, 30, 22), "resin", rot=(-30, -10, 0))
        sleeper(t, (c[0] + 3, c[1] + 1, c[2] - 2), pitch=-30)
        for i, (x, y, z, r) in enumerate(((14, 88, -24, 30), (16, 74, -30, -20), (12, 63, -24, 60))):
            t.box(f"womb_shard{i}", (x, y, z), (3, 12, 9), "resin", rotation=(r, 40, r * 0.5))


def lantern(g, anchor, length, swing=(0, 0, 0)):
    """The face: a creaking heart hanging under the trunk on a root, bound in a cage of roots, its eye glowing."""
    a = np.array(anchor, float)
    sw = np.array(swing, float)
    bottom = a + _n(np.array([0, -1, 0]) + sw) * length
    branch(g, "lantern_root", [a, (a + bottom) / 2 + [2, 0, 1], bottom], 5, 3.4, n=4, amp=0.8, seed=9, mat="root",
           knots=False)
    c = bottom - [0, 11, 0] + sw * 8
    rot = (sw[2] * -30, 10, sw[0] * 30)
    g.box("lantern_heart", tuple(c), (17, 19, 17), "heart", rotation=rot)
    for i, (x, z) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        g.box(f"lantern_bar{i}", tuple(c + [x * 9, 0, z * 9]), (2.8, 22, 2.8), "heart_frame", rotation=rot)
    g.box("lantern_cap", tuple(c + [0, 11.4, 0]), (14, 3.6, 14), "heart_frame", rotation=(rot[0], 55, rot[2]))
    g.box("lantern_foot", tuple(c + [0, -11.4, 0]), (11, 3.2, 11), "heart_frame", rotation=(rot[0], 55, rot[2]))
    g.box("lantern_eye", tuple(c + [0, 1, -8.7]), (9, 3.4, 0.6), "glow", rotation=rot)
    cbox(g, "lantern_tail0", c - [0, 12, 0], c - [0, 18, -1], 2.6, 2.6, "root")
    cbox(g, "lantern_tail1", c - [0, 18, -1], c - [2, 23, -3], 1.8, 1.8, "root")
    return c


# ---- arms and legs ----------------------------------------------------------------------------------------------------

def arm(g, name, ctrl, w0, w1, blooms=(), mosses=(), drag=(0, 0, 1), seed=0, fingers=3):
    """An arm growing out of the trunk (a flare where it joins); blooms: (fraction along it, open);
    mosses: (fraction, length)."""
    pts, ws = branch(g, name, ctrl, w0, w1, n=9, amp=1.8, seed=seed)
    ball(g, f"{name}_flare", pts[0], (w0 * 1.25, w0 * 1.2, w0 * 1.25), "bark", rot=(0, seed * 13, 0))
    n = len(pts) - 1

    def at(f):
        u = f * n
        i = min(int(u), n - 1)
        return pts[i] + (pts[i + 1] - pts[i]) * (u - i), ws[i] + (ws[i + 1] - ws[i]) * (u - i), _n(pts[i + 1] - pts[i])

    for k, (f, op) in enumerate(blooms):
        p, w, d = at(f)
        up = _n(np.array([0, 1, 0]) - d * d[1]) if abs(d[1]) < 0.97 else np.array([0, 0, 1.0])
        side = _n(np.cross(d, up))
        nrm = _n(up + side * (k % 3 - 1) * 0.6)
        flower(g, f"{name}_bloom{k}", p + nrm * (w / 2), nrm, op)
    for k, (f, length) in enumerate(mosses):
        p, w, _ = at(f)
        moss(g, f"{name}_moss{k}", p - [0, w / 2, 0], length, yaw=k * 37 + seed)
    claws(g, f"{name}_claw", pts[-1], drag, n=fingers)
    return pts


def leg(g, name, hip, knee, hock, foot, straight=False, seed=0):
    ctrl = [hip, knee, foot] if straight else [hip, knee, hock, foot]
    branch(g, name, ctrl, 8, 4.5, n=7, amp=1.0, seed=seed)
    f = np.array(foot, float)
    for i, (dx, dz) in enumerate(((-0.6, -1), (0.1, -1), (0.7, -0.8), (0.1, 1))):
        cbox(g, f"{name}_toe{i}", f, f + _n([dx, -0.1, dz]) * (13 if dz < 0 else 8), 3.2, 3, "root", i * 25)


def legs(root, pose, straight_right=False):
    hip_r, hip_l = PELVIS + [9, 0, 2], PELVIS + [-9, 0, 4]
    if pose == REST:
        r = ((14, 42, -2), (15, 20, 18), (15, 2, 8))
        l = ((-16, 40, 2), (-17, 18, 22), (-16, 2, 10))
    elif pose == WALK:
        r = ((13, 44, -14), (14, 22, 4), (14, 2, -10))
        l = ((-14, 38, 12), (-15, 16, 34), (-14, 2, 28))
    else:
        r = ((20, 40, -4), (24, 18, 14), (26, 2, 2))
        l = ((-20, 38, 8), (-24, 16, 28), (-26, 2, 20))
    if straight_right:      # a straight stilt: hip, knee straight under it, foot
        r = ((r[0][0], 32, r[2][2] * 0.5), r[1], (r[2][0], 2, r[2][2]))
    leg(root, "leg_right", hip_r, *r, straight=straight_right, seed=1)
    leg(root, "leg_left", hip_l, *l, seed=2)


# ---- the takes --------------------------------------------------------------------------------------------------------

BLOOMS = ((0.12, True), (0.22, False), (0.32, True), (0.4, True), (0.5, False), (0.58, True), (0.7, True))
MOSSES = ((0.18, 22), (0.3, 14), (0.45, 18), (0.55, 10))


def hump_blooms(t, centre, n=9, spread=13, seed=1):
    rng = np.random.default_rng(seed)
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.3, 0.3)
        r = spread * math.sqrt(rng.uniform(0.25, 1))
        nrm = _n([math.cos(a) * 0.5, 1, math.sin(a) * 0.5])
        flower(t, f"hump_bloom{i}", np.array(centre) + [math.cos(a) * r, 0, math.sin(a) * r], nrm, i % 3 != 2)


def belly_moss(t, spots):
    for i, (x, y, z, l) in enumerate(spots):
        moss(t, f"belly_moss{i}", (x, y, z), l, yaw=i * 41)


def sway(ctrl, pose, dz):
    """The walk: the dragging hands swing; the last two control points move by dz."""
    if pose != WALK:
        return ctrl
    return ctrl[:-2] + [tuple(np.array(c, float) + [0, 0, dz]) for c in ctrl[-2:]]


def upper(root, pose, yaw, roll):
    lean = {REST: 0, WALK: 4, STRIKE: -10}[pose]
    return root.group("upper", (1, 80, 10), (lean, yaw, roll))


def take_A(m, pose):
    root = m.group("body", (0, 0, 0))
    t = upper(root, pose, {REST: 0, WALK: -6, STRIKE: 10}[pose], 4)
    trunk(t)
    womb(t, "bulge")
    hump_blooms(t, (0, 107, -6))
    belly_moss(t, ((-8, 80, -2, 18), (6, 82, -10, 12), (-10, 72, -30, 22), (12, 74, -32, 16), (-12, 66, 6, 14)))
    lantern(root, world(t, (1, 76, -40)), {REST: 24, WALK: 24, STRIKE: 18}[pose],
            {REST: (0, 0, 0), WALK: (0, 0, 0.25), STRIKE: (0, 0, -0.5)}[pose])
    S = {k: world(t, p) for k, p in {"r1": (17, 93, -22), "r2": (14, 80, -8), "l1": (-16, 94, -16),
                                         "b1": (-6, 104, 0)}.items()}
    if pose == STRIKE:
        arm(root, "arm_r1", [S["r1"], (32, 112, -24), (40, 138, -20), (34, 154, -40), (22, 146, -60), (12, 124, -70)],
            14, 4, BLOOMS, MOSSES, drag=(-0.2, -0.7, -1), seed=1)
        arm(root, "arm_l1", [S["l1"], (-30, 92, -26), (-40, 74, -44), (-36, 48, -62), (-28, 24, -74), (-22, 8, -80)],
            12, 4, BLOOMS, MOSSES, drag=(0, -0.3, -1), seed=2)
    else:
        arm(root, "arm_r1", sway([S["r1"], (30, 104, -20), (42, 110, -8), (48, 80, 8), (50, 40, 26), (46, 12, 44),
                                  (42, 3, 56)], pose, 10), 14, 4, BLOOMS, MOSSES, seed=1)
        arm(root, "arm_l1", sway([S["l1"], (-30, 96, -12), (-46, 88, 0), (-54, 62, 16), (-52, 28, 36), (-46, 3, 54)],
                                 pose, -10), 12, 4, BLOOMS, MOSSES, seed=2)
    arm(root, "arm_r2", [S["r2"], (24, 72, -10), (32, 58, -2), (34, 36, 16), (30, 12, 40), (26, 3, 58)], 9, 3.5,
        BLOOMS[:5], MOSSES[:2], seed=3)
    arm(root, "arm_b1", [S["b1"], (-8, 118, 10), (-14, 124, 26), (-22, 112, 44), (-24, 80, 58), (-20, 40, 70),
                         (-16, 3, 86)], 10, 3.5, BLOOMS, MOSSES, seed=4)
    legs(root, pose)
    return m


def take_B(m, pose):
    root = m.group("body", (0, 0, 0))
    t = upper(root, pose, {REST: 0, WALK: -6, STRIKE: 12}[pose], -3)
    trunk(t, split=True)
    womb(t, "split")
    hump_blooms(t, (0, 107, -2), n=8, spread=11, seed=3)
    belly_moss(t, ((-10, 76, -8, 16), (10, 76, -8, 20), (0, 70, 4, 14), (-14, 70, -30, 20), (14, 70, -30, 12)))
    lantern(root, world(t, (0, 66, -32)), {REST: 18, WALK: 18, STRIKE: 14}[pose],
            {REST: (0, 0, 0), WALK: (0, 0, 0.25), STRIKE: (0, 0, -0.5)}[pose])
    S = {k: world(t, p) for k, p in {"r1": (18, 94, -20), "r2": (15, 84, -6), "r3": (12, 72, 6),
                                         "l1": (-17, 95, -14), "l2": (-13, 80, -2)}.items()}
    if pose == STRIKE:
        arm(root, "arm_r1", [S["r1"], (34, 116, -18), (40, 140, -14), (32, 156, -36), (20, 146, -58), (10, 126, -66)],
            14, 4, BLOOMS, MOSSES, drag=(-0.2, -0.7, -1), seed=1)
        arm(root, "arm_l1", [S["l1"], (-28, 118, -10), (-32, 138, -22), (-24, 146, -42), (-14, 132, -56)],
            12, 4, BLOOMS, MOSSES, drag=(0.2, -0.7, -1), seed=2)
    else:
        arm(root, "arm_r1", sway([S["r1"], (34, 90, -18), (52, 82, -6), (60, 56, 12), (56, 22, 36), (48, 3, 56)],
                                 pose, 10), 14, 4, BLOOMS, MOSSES, seed=1)
        arm(root, "arm_l1", sway([S["l1"], (-28, 108, -18), (-38, 118, -6), (-44, 92, 12), (-46, 50, 30),
                                  (-42, 14, 48), (-38, 3, 60)], pose, -10), 12, 4, BLOOMS, MOSSES, seed=2)
    arm(root, "arm_r2", [S["r2"], (28, 74, -4), (36, 50, 12), (32, 20, 38), (28, 3, 62)], 9, 3.5, BLOOMS[:5],
        MOSSES[:2], seed=3)
    arm(root, "arm_r3", [S["r3"], (20, 56, 14), (20, 30, 34), (16, 6, 52), (12, 3, 66)], 6, 2.8, BLOOMS[:3],
        MOSSES[:1], seed=4, fingers=2)
    arm(root, "arm_l2", [S["l2"], (-24, 66, -4), (-30, 44, 14), (-26, 16, 42), (-20, 3, 70)], 8, 3.2, BLOOMS[:4],
        MOSSES[:2], seed=5)
    legs(root, pose, straight_right=True)
    return m


def take_C(m, pose):
    root = m.group("body", (0, 0, 0))
    t = upper(root, pose, {REST: 30, WALK: 24, STRIKE: 42}[pose], 6)
    trunk(t)
    womb(t, "cracked")
    hump_blooms(t, (0, 107, -6), n=10, spread=14, seed=7)
    belly_moss(t, ((-8, 80, -2, 18), (6, 82, -10, 12), (-10, 72, -30, 22), (12, 74, -32, 14)))
    lantern(root, world(t, (1, 76, -40)), {REST: 34, WALK: 34, STRIKE: 28}[pose],
            {REST: (0.15, 0, 0), WALK: (0.2, 0, 0.35), STRIKE: (0, 0, -0.6)}[pose])
    S = {k: world(t, p) for k, p in {"r1": (17, 93, -22), "r2": (14, 80, -6), "l1": (-16, 94, -18),
                                         "b1": (-6, 104, 0), "r3": (10, 102, 4)}.items()}
    crutch = {REST: (-36, 4, -46), WALK: (-32, 4, -62), STRIKE: (-40, 4, -42)}[pose]
    arm(root, "arm_l1", [S["l1"], (-32, 96, -24), (-42, 86, -36), (crutch[0] - 4, 50, crutch[2] + 4),
                         (crutch[0] - 1, 20, crutch[2] + 1), crutch], 15, 7, BLOOMS, MOSSES, drag=(0, -0.3, -1),
        seed=2, fingers=4)
    if pose == STRIKE:
        arm(root, "arm_r1", [S["r1"], (32, 112, -24), (42, 136, -26), (38, 154, -48), (26, 146, -70), (16, 124, -80)],
            14, 4, BLOOMS, MOSSES, drag=(-0.2, -0.7, -1), seed=1)
    else:
        arm(root, "arm_r1", sway([S["r1"], (30, 104, -22), (44, 108, -10), (52, 76, 6), (52, 36, 24), (46, 10, 42),
                                  (42, 3, 54)], pose, 10), 14, 4, BLOOMS, MOSSES, seed=1)
    arm(root, "arm_r2", [S["r2"], (24, 70, -10), (32, 54, -2), (32, 32, 18), (26, 10, 40), (22, 3, 58)], 9, 3.5,
        BLOOMS[:5], MOSSES[:2], seed=3)
    arm(root, "arm_r3", [S["r3"], (16, 118, 8), (26, 124, 22), (34, 108, 38), (34, 76, 50), (30, 44, 56)], 6, 2.6,
        BLOOMS[:4], MOSSES[:2], drag=(0, -1, 0.3), seed=4, fingers=2)
    arm(root, "arm_b1", [S["b1"], (-8, 118, 10), (-14, 124, 26), (-22, 112, 44), (-24, 80, 58), (-20, 40, 70),
                         (-16, 3, 86)], 10, 3.5, BLOOMS, MOSSES, seed=5)
    legs(root, pose)
    return m


TAKES = {"A": ("The Stoop", take_A), "B": ("The Split", take_B), "C": ("The Crutch", take_C)}
VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 35, "height": 4.2, "dist": 15, "target_z": 3.4},
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front", "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_low", "mode": "clay", "camera": "persp", "yaw": -32, "height": 1.62, "dist": 12, "target_z": 3.6,
     "player": False},
]
LABELS = {"flat_34": "three-quarter", "sil_front": "front, silhouette", "sil_side": "side, silhouette",
          "clay_low": "a player's eye"}


def build(key, pose):
    m = Model(f"heartwood_{key}_{pose}")
    return TAKES[key][1](m, pose)


def main(args):
    quick = "quick" in args
    keys = [a for a in args if a in TAKES] or list(TAKES)
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    views = VIEWS[:1] + VIEWS[2:3] if quick else VIEWS
    poses = (REST,) if quick else POSES
    for key in keys:
        if (OUT / key).exists():
            shutil.rmtree(OUT / key)
        for pose in poses:
            m = build(key, pose)
            v2.run_blender(m.render_json(v2.PALETTE), OUT / key / pose, views)
            if pose == REST:
                lo, hi = m.bounds()
                print(key, TAKES[key][0], "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo],
                      "cubes", len(m.cubes))
        tw, th, pad, top = 400, 320, 12, 60
        img = Image.new("RGB", (pad + len(views) * (tw + pad), top + len(poses) * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Heartwood Horror, {key}: {TAKES[key][0]}", font=sheet._font(26), fill=sheet.INK)
        for r, pose in enumerate(poses):
            for c, v in enumerate(views):
                x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
                img.paste(sheet._tile(OUT / key / pose / f"{v['name']}.png", tw, th), (x, y))
                dr.text((x, y + th + 6), f"{pose}: {LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / f"{key}_{TAKES[key][0].lower().replace(' ', '_')}.png")
        if not quick:     # the chest close up: the womb and the lantern from a little below
            v2.run_blender(build(key, REST).render_json(v2.PALETTE), OUT / key / "chest", [CHEST])
    if not quick and keys == list(TAKES):
        compare()


CHEST = {"name": "chest", "mode": "flat", "camera": "persp", "yaw": 28, "height": 2.2, "dist": 19, "target_z": 4.2, "lens": 62,
         "player": False}


def compare():
    cols = [(REST, "flat_34", "three-quarter"), (REST, "sil_front", "front"), (REST, "sil_side", "side"),
            ("chest", "chest", "the chest: womb and lantern")]
    tw, th, pad, top = 400, 320, 12, 60
    img = Image.new("RGB", (pad + len(cols) * (tw + pad), top + len(TAKES) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Heartwood Horror, session 1: three takes on the combined design", font=sheet._font(26),
            fill=sheet.INK)
    for r, key in enumerate(TAKES):
        for c, (folder, view, label) in enumerate(cols):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / key / folder / f"{view}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{key} {TAKES[key][0]}: {label}", font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "compare.png")


if __name__ == "__main__":
    main(sys.argv[1:])
