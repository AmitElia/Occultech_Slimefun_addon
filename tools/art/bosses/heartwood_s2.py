"""Heartwood Horror, session 2: design lock (plan: docs/art/bosses/heartwood_horror/overhaul/plan.md).

The user picked take C, the Crutch (heartwood_s1.py), with one change: the sleeper is not half out of the resin, it
sleeps whole inside it, curled like a foetus. This rebuilds C as a rig:

- every limb is a chain of bones laid out straight in the rest pose and bent by its bones' rotations (the bind pose is
  the stalk). Cubes sit square in their bone (or turned 45 degrees on one axis), so each bone is one display entity;
- the trunk: hips > trunk0..4 (up from the hips, over the hump, down to the brow), twisted a fifth of a turn above the
  hips; two broken branches on the hump;
- five arms grown out of the trunk: the crutch (left, planted ahead, knuckles down), the great arm (right, high spidery
  elbow), the lesser arm (right, drooping), the thin arm (right, over the shoulder, hanging), the back arm (out of the
  hump, arching over and trailing). Each ends in a hand bone with its root fingers;
- two backward-kneed stilt legs (thigh, shin, cannon) with a foot bone of root toes;
- the womb: a resin shell under the hunch (its own bone), the sleeper curled inside it whole (its own bone), its shut
  eyes on glow_sleeper (dark now; the vulnerable window lights them);
- the face: a creaking heart caged in roots (hi_lantern) hanging from the brow on a three-bone root, its eye on
  glow_lantern;
- eyeblossoms on the arms and the hump, their eyes on glow_ bones (a creak can tint them shut);
- strands of pale hanging moss on their own bones (they hang straight down in every pose and can sway);
- the hitbox (ob_hitbox): the trunk, the womb, the legs and the lantern, not the trailing arms.

Poses for the fight's key moments are set from world-space targets: chains are fitted along a curve through control
points at their fixed bone lengths and pulled onto their end point (FABRIK); legs by two-bone IK onto the floor.

Run from the repository root: python tools/art/bosses/heartwood_s2.py [pose ...]
"""
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Group, Model, add_hitbox, rotation_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s2 as v2  # noqa: E402
from bosses.heartwood_s1 import PALETTE as P1, curve  # noqa: E402

OUT = ROOT / "docs/art/bosses/heartwood_horror/overhaul/s2_design"
NAME = "occultech_heartwood_horror"
PALETTE = dict(P1, hitbox=(220, 60, 60), eyelid=(70, 62, 60), resin=(228, 132, 34, 120), resin_core=(120, 50, 18))
GLOW = {"bloom", "glow", "sleeper_eye"}
UP, DOWN = np.array([0.0, 1, 0]), np.array([0.0, -1, 0])
PIVOT = np.array([1.0, 80, 10])          # the trunk turns above this point (take C's twist)
TWIST = 0.0                              # the Stoop's straight body (take C was turned 30 degrees)


# ---- maths ------------------------------------------------------------------------------------------------------------

def _n(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


def euler(R):
    y = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    return [math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(y), math.degrees(math.atan2(R[1, 0], R[0, 0]))]


def turn_to(d0, d):
    """The smallest rotation taking direction d0 to d."""
    a, b = _n(d0), _n(d)
    v, c = np.cross(a, b), float(a @ b)
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3) if c > 0 else rotation_matrix((180, 0, 0))
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k / (1 + c)


def roty(deg):
    return rotation_matrix((0, deg, 0))


def yaw_about(p, deg, pivot=PIVOT):
    return pivot + roty(deg) @ (np.array(p, float) - pivot)


def wR(g):
    return g.world_matrix()[:3, :3]


def wpos(g, p):
    return (g.world_matrix() @ np.array([*p, 1.0]))[:3]


def to_rest(g, p):
    """A world point in g's rest space."""
    return (np.linalg.inv(g.world_matrix()) @ np.array([*p, 1.0]))[:3]


def set_world_R(g, R):
    g.rotation = euler(wR(g.parent).T @ R)


def fit(ctrl, lengths):
    """Joints at the given bone lengths along a smooth curve through the control points (carried straight on past
    its end if the curve is short)."""
    pts = curve(ctrl, 240)
    seg = [np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)]
    cum = np.concatenate([[0], np.cumsum(seg)])
    out, s = [pts[0]], 0.0
    for L in lengths:
        s += L
        if s <= cum[-1]:
            i = min(int(np.searchsorted(cum, s)) - 1, len(seg) - 1)
            t = (s - cum[i]) / max(seg[i], 1e-9)
            out.append(pts[i] + (pts[i + 1] - pts[i]) * t)
        else:
            out.append(out[-1] + _n(pts[-1] - pts[-2]) * L)
    return out


def fabrik(joints, lengths, target, iters=40, floor=None):
    """FABRIK; with floor, every joint but the end is kept at or above that height."""
    J = [np.array(p, float) for p in joints]
    root, target = J[0].copy(), np.array(target, float)
    if np.linalg.norm(target - root) >= sum(lengths) - 1e-6:
        d = _n(target - root)
        return [root + d * sum(lengths[:k]) for k in range(len(J))]
    for _ in range(iters):
        J[-1] = target.copy()
        for k in range(len(J) - 2, -1, -1):
            J[k] = J[k + 1] + _n(J[k] - J[k + 1]) * lengths[k]
            if floor is not None and k > 0:
                J[k][1] = max(J[k][1], floor)
        J[0] = root.copy()
        for k in range(len(J) - 1):
            J[k + 1] = J[k] + _n(J[k + 1] - J[k]) * lengths[k]
            if floor is not None and k + 1 < len(J) - 1:
                J[k + 1][1] = max(J[k + 1][1], floor)
    return J


def ik(root_pt, target, hint, l1, l2):
    """Two-bone IK: the middle joint for fixed lengths, bending towards `hint`."""
    root_pt, target, hint = (np.array(v, float) for v in (root_pt, target, hint))
    d = target - root_pt
    dist = min(np.linalg.norm(d), l1 + l2 - 0.05)
    u = _n(d)
    a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    p = hint - root_pt
    p = p - u * (p @ u)
    p = _n(p) if np.linalg.norm(p) > 1e-6 else _n(np.cross(u, (1, 0, 0)))
    return root_pt + u * a + p * h


# ---- chains -----------------------------------------------------------------------------------------------------------

class Chain:
    """Bones laid out straight from a root along `u` in the rest pose; place() bends them onto world joints."""

    def __init__(self, parent, name, world_joints, u, names=None):
        self.u = _n(u)
        J = [np.array(p, float) for p in world_joints]
        self.lengths = [float(np.linalg.norm(J[k + 1] - J[k])) for k in range(len(J) - 1)]
        self.parent = parent
        pt = to_rest(parent, J[0])
        self.rest = [pt + self.u * sum(self.lengths[:k]) for k in range(len(J))]
        self.bones, p = [], parent
        for k in range(len(self.lengths)):
            b = p.group(names[k] if names else f"{name}{k}", tuple(self.rest[k]))
            self.bones.append(b)
            p = b
        self.place(J)

    def place(self, J):
        Rp = wR(self.parent)
        for k, b in enumerate(self.bones):
            R = turn_to(self.u, J[k + 1] - J[k])
            b.rotation = euler(Rp.T @ R)
            Rp = R

    def joints(self):
        return [wpos(self.bones[0], self.rest[0])] + [wpos(b, self.rest[k + 1]) for k, b in enumerate(self.bones)]

    def seg(self, k, f):
        """Rest-space point a fraction f along bone k."""
        return self.rest[k] + self.u * self.lengths[k] * f

    def pose_along(self, ctrl, exact=True):
        root = self.joints()[0]
        J = fit([root] + [np.array(c, float) for c in ctrl], self.lengths)
        if exact:
            J = fabrik(J, self.lengths, ctrl[-1], floor=8)
        self.place(J)

    def drag_to(self, target):
        """Keeps the end where it was (a dragging hand stays on the floor) after the root moved."""
        self.place(fabrik(self.joints(), self.lengths, target, floor=8))


# ---- parts ------------------------------------------------------------------------------------------------------------

def octo_seg(g, name, a, u, L, w, d, mat, chamfer=True):
    """A bark segment from rest point a along u (+-y), w by d, with a 45-degree chamfer cube (one axis)."""
    c = np.array(a, float) + u * L / 2
    g.box(name, tuple(c), (w, L + min(w, 6) * 0.5, d), mat)
    if chamfer and min(w, d) > 5:
        g.box(name + "_c", tuple(c), (min(w, d) * 0.76, L + min(w, 6) * 0.3, min(w, d) * 0.76), mat, rotation=(0, 45, 0))


def flower(g, glow, name, centre, n, open_=True, s=8.0):
    """An eyeblossom on a bark face with rest-space normal n (one of +-x, +-z): two petal blades crossed at 45 degrees
    on that one axis, the eye on the glow bone; closed: a grey bud."""
    c, n = np.array(centre, float), np.array(n, float)
    ax = int(np.argmax(np.abs(n)))
    if open_:
        for k, ang in enumerate((45, -45)):
            if ax == 0:
                g.box(f"{name}_petal{k}", tuple(c + n * 0.6), (1, s, s * 0.4), "petal", rotation=(ang, 0, 0))
            else:
                g.box(f"{name}_petal{k}", tuple(c + n * 0.6), (s, s * 0.4, 1), "petal", rotation=(0, 0, ang))
        size = [3, 3, 3]
        size[ax] = 1.0
        glow.box(f"{name}_eye", tuple(c + n * 1.6), tuple(size), "bloom")
    else:
        size = [3, 3, 3]
        size[ax] = 6.0
        g.box(f"{name}_bud", tuple(c + n * 3), tuple(size), "bud")


def moss_bone(parent, name, world_top, length):
    """A strand of pale hanging moss: a bone hanging straight down, two crossed planes."""
    g = parent.group(name, tuple(to_rest(parent, world_top)))
    top = np.array(g.origin)
    g.box(name + "_a", tuple(top - [0, length / 2, 0]), (4, length, 1), "moss")
    g.box(name + "_b", tuple(top - [0, length * 0.42, 0]), (1, length * 0.84, 4), "moss")
    set_world_R(g, np.eye(3))
    return g


def hand_bone(parent, name, world_at, drag, fingers=3, spread=22.5, length=16, curl=0.0):
    """Root fingers fanning from the hand along `drag` (flat on the floor); curl tips them down into it."""
    g = parent.group(name, tuple(to_rest(parent, world_at)))
    o = np.array(g.origin)
    for i in range(fingers):
        ang = -spread * (fingers - 1) / 2 + spread * i
        ln = length * (1.2 if i == fingers // 2 else 0.9)
        d = roty(ang) @ np.array([0, 0, 1.0])
        g.box(f"{name}_finger{i}", tuple(o + d * ln / 2 + [0, -1, 0]), (3.5, 3, ln), "root", rotation=(0, ang, 0))
    aim_hand(g, drag, curl)
    return g


def aim_hand(g, drag, curl=0.0):
    d = np.array(drag, float)
    yaw = math.degrees(math.atan2(d[0], d[2]))
    set_world_R(g, roty(yaw) @ rotation_matrix((-curl, 0, 0)))     # curl < 0 tips the fingers down


# ---- the rig ----------------------------------------------------------------------------------------------------------

S1_SPINE = [(0, 62, 12), (1, 80, 10), (0, 94, 0), (-1, 97, -18), (1, 86, -34)]
TRUNK_W = (24, 32, 36, 32, 26)
SHOULDERS = {"crutch": ((-16, 94, -18), 3), "great": ((17, 93, -22), 3), "lesser": ((20, 80, 0), 2),
             "thin": ((10, 102, 4), 2), "back": ((-6, 104, 0), 2)}        # s1 point, trunk bone it grows from
ARMS = {   # bind control points (world, after the shoulder), widths, segments, fingers, drag
    "crutch": ([(-32, 98, -26), (-46, 94, -42), (-50, 60, -58), (-46, 26, -66), (-43, 9, -68)], 15, 7, 7, 4, (0, 0, -1)),
    "great": ([(30, 104, -22), (44, 108, -10), (52, 76, 6), (52, 36, 24), (46, 10, 42), (42, 4, 54)], 14, 4, 7, 3,
              (0, 0, 1)),
    "lesser": ([(24, 70, -10), (32, 54, -2), (32, 32, 18), (26, 10, 40), (22, 4, 58)], 9, 3.5, 6, 3, (0, 0, 1)),
    "thin": ([(16, 118, 8), (26, 124, 22), (34, 108, 38), (34, 76, 50), (30, 46, 56)], 6, 2.6, 5, 2, (0, -1, 0.3)),
    "back": ([(-8, 118, 10), (-14, 124, 26), (-22, 112, 44), (-24, 80, 58), (-20, 40, 70), (-16, 4, 86)], 10, 3.5, 7, 3,
             (0, 0, 1)),
}
BLOOMS = {"crutch": (1, 2, 4), "great": (1, 2, 3), "lesser": (1, 2), "thin": (1, 2), "back": (0, 1, 2, 3)}
MOSS = {"crutch": ((1, 0.5, 20), (2, 0.4, 14)), "great": ((1, 0.6, 24), (2, 0.3, 16)), "lesser": ((1, 0.5, 18),),
        "back": ((2, 0.5, 22),)}
WOMB = np.array([1.0, 79, -16])          # the resin bulge's centre, world: up in the chest, under the hump
WOMB_SIZE = (24, 26, 24)
WOMB_TILT = -32                           # tipped forward with the chest (the Stoop's bulge)
LANTERN_ANCHOR = np.array([1.0, 80, -40])   # under the brow's tip, clear of the womb
SLEEPER = 1.0                             # the sleeper: vanilla creaking parts at 1x
LEGS = {"right": ((9, 62, 14), (14, 42, -2), (15, 20, 18), (15, 2, 8)),
        "left": ((-9, 62, 16), (-16, 40, 2), (-17, 18, 22), (-16, 2, 10))}


class Rig:
    def __init__(self):
        m = self.m = Model(NAME)
        self.hips = m.group("hips", (0, 62, 12))
        self.hips.box("pelvis", (0, 60, 13), (22, 12, 18), "bark")
        self.hips.box("pelvis_c", (0, 60, 13), (17, 12, 17), "bark", rotation=(0, 45, 0))
        # the trunk: five bones up from the hips, over the hump, down to the brow; the top turned TWIST degrees
        J = curve(S1_SPINE, 5)
        J = [J[0], J[1]] + [yaw_about(p, TWIST) for p in J[2:]]
        self.trunk = Chain(self.hips, "trunk", J, UP)
        for k, b in enumerate(self.trunk.bones):
            w = TRUNK_W[k]
            octo_seg(b, f"trunk{k}_bark", self.trunk.rest[k], self.trunk.u, self.trunk.lengths[k], w, w * 0.86, "bark")
            if k in (1, 2, 3):
                b.box(f"trunk{k}_ridge", tuple(self.trunk.seg(k, 0.5) + [w * 0.42, 0, 0]),
                      (4, self.trunk.lengths[k] * 0.8, 6), "bark_dark")
            if k in (1, 3):
                b.box(f"trunk{k}_knot", tuple(self.trunk.rest[k] + [-w * 0.3, 0, w * 0.2]), (9, 8, 9), "bark_dark")
        t2, t3, t4 = self.trunk.bones[2], self.trunk.bones[3], self.trunk.bones[4]
        # the hump: a broad mass on the back (rest +z of the bent bones), a cluster of eyeblossoms on top
        hump = self.trunk.seg(2, 0.85) + [0, 0, 9]
        t2.box("hump", tuple(hump), (36, 26, 20), "bark")
        t2.box("hump_c", tuple(hump + [0, 0, 3]), (28, 24, 28), "bark", rotation=(0, 45, 0))
        t2.box("hump_r", tuple(hump + [0, 0, 5]), (34, 22, 22), "bark", rotation=(45, 0, 0))
        t2.box("hump_cap", tuple(hump + [0, 0, 12]), (24, 16, 6), "bark_dark")
        glow_h = t2.group("glow_hump_blooms", tuple(hump))
        rng = np.random.default_rng(7)
        for i in range(8):
            x, y = rng.uniform(-12, 12), rng.uniform(-8, 8)
            flower(t2, glow_h, f"hump_bloom{i}", hump + [x, y, 7], (0, 0, 1), open_=i % 3 != 2)
        # the brow: the trunk's end bent down over the lantern
        brow = self.trunk.seg(4, 0.9)
        t4.box("brow", tuple(brow), (26, 16, 22), "bark_dark")
        t4.box("brow_c", tuple(brow), (20, 16, 20), "bark_dark", rotation=(0, 45, 0))
        t4.box("brow_r", tuple(brow), (24, 14, 14), "bark_dark", rotation=(45, 0, 0))
        # two broken branches on the hump
        self.stubs = []
        for name, pts in (("stub_left", [(-4, 104, -2), (-9, 113, 6), (-8, 121, 16)]),
                          ("stub_right", [(8, 103, -12), (14, 111, -16), (22, 114, -10)])):
            ch = Chain(t3, name, [yaw_about(p, TWIST) for p in pts], UP)
            for k, b in enumerate(ch.bones):
                octo_seg(b, f"{name}{k}_bark", ch.rest[k], ch.u, ch.lengths[k], 6 - 2 * k, 6 - 2 * k, "bark", False)
            ch.bones[-1].box(f"{name}_end", tuple(ch.rest[-1]), (4, 4, 4), "wood")
            self.stubs.append(ch)
        self.womb_parts(t2)
        self.lantern_parts(t4)
        self.arms = {k: self.arm_parts(k) for k in ARMS}
        self.legs = {k: self.leg_parts(k) for k in LEGS}
        self.bind_hands = {k: a.joints()[-1] for k, a in self.arms.items()}
        self.moss = []
        for i, (bone, f, dx, dz, length) in enumerate(((1, 0.6, -8, 0, 18), (2, 0.4, 9, -6, 14), (3, 0.5, -10, -6, 22),
                                                        (3, 0.8, 11, -4, 14), (4, 0.4, -6, -8, 16))):
            b = self.trunk.bones[bone]
            top = wpos(b, self.trunk.seg(bone, f) + [dx, 0, dz]) + [0, -6, 0]
            self.moss.append(moss_bone(b, f"moss_belly{i}", top, length))

    # -- the womb and the sleeper --
    def womb_parts(self, t2):
        """The resin shell hangs upright under the hunch, part of the chest; the sleeper curls whole inside it,
        upright and facing out: knees drawn up, the head bowed onto them, the long arms wrapped round the shins."""
        womb = self.womb = t2.group("womb", tuple(to_rest(t2, WOMB)))
        set_world_R(womb, rotation_matrix((WOMB_TILT, 0, 0)))
        o = np.array(womb.origin)
        womb.box("resin", tuple(o), WOMB_SIZE, "resin")
        # (no inner chamfer layer: through the translucent shell its rims showed as bars across the window)
        hx, hy, hz = (v / 2 for v in WOMB_SIZE)
        for i, (dx, dy, dz, size) in enumerate(((-hx, hy - 3, -hz + 4, (5, 8, 8)), (hx, hy - 5, -hz + 6, (5, 7, 9)),
                                                 (-hx + 3, -hy, -hz + 5, (8, 4, 9)), (hx - 4, -hy, 2, (9, 4, 8)))):
            womb.box(f"resin_rim{i}", tuple(o + [dx, dy, dz]), size, "resin_dark")
        # the chamber: opaque amber plates just inside the shell's back, sides and top. The front and the bottom (what
        # players look into from below) are windows; through them only the sleeper and this amber show, never parts
        # drawn by other bones behind the shell
        t = 1.0
        chamber = womb.group("glow_womb", tuple(o))          # full-bright: the womb glows from inside at night
        for name, off, size in (("back", (0, 0, hz - 0.1 - t / 2), (2 * hx - 2, 2 * hy - 2, t)),
                                ("left", (-(hx - 0.1 - t / 2), 0, 0), (t, 2 * hy - 2, 2 * hz - 2)),
                                ("right", (hx - 0.1 - t / 2, 0, 0), (t, 2 * hy - 2, 2 * hz - 2)),
                                ("top", (0, hy - 0.1 - t / 2, 0), (2 * hx - 2, t, 2 * hz - 2))):
            chamber.box(f"chamber_{name}", tuple(o + np.array(off)), size, "resin_core")
        sl = self.sleeper = womb.group("sleeper", tuple(o))
        k = SLEEPER
        q = o + [0, -0.5, 3]
        sl.box("sleeper_body", tuple(q + [0, 2, 3]), (6 * k, 13 * k, 5 * k), "sleeper", rotation=(22.5, 0, 0))
        for s_, side in ((-1, "left"), (1, "right")):
            sl.box(f"sleeper_thigh_{side}", tuple(q + [s_ * 2.4 * k, -6 * k, -3 * k]), (3 * k, 3 * k, 13 * k), "sleeper")
            sl.box(f"sleeper_shin_{side}", tuple(q + [s_ * 2.4 * k, -9.4 * k, -1 * k]), (3 * k, 3 * k, 12 * k), "sleeper")
            sl.box(f"sleeper_arm_{side}", tuple(q + [s_ * 5 * k, -2.5 * k, -3 * k]), (3 * k, 3 * k, 18 * k), "sleeper",
                   rotation=(45, 0, 0))
        head = q + [0, 4.5 * k, -5 * k]
        sl.box("sleeper_head", tuple(head), (6 * k, 10 * k, 6 * k), "sleeper", rotation=(-45, 0, 0))
        top = head + np.array([0, 0.707, -0.707]) * 6.5 * k
        sl.box("sleeper_crown", tuple(top), (6 * k, 3 * k, 6 * k), "bark_dark", rotation=(-45, 0, 0))
        for s_, side in ((-1, "left"), (1, "right")):
            sl.box(f"sleeper_leaf_{side}", tuple(head + [s_ * 4.6 * k, 1.5 * k, -1.5 * k]), (1, 9 * k, 7 * k),
                   "bark_dark", rotation=(-45, 0, 0))
        eyes = sl.group("glow_sleeper", tuple(head))
        face = np.array([0, -0.707, -0.707])
        for s_, side in ((-1, "left"), (1, "right")):
            eyes.box(f"sleeper_eye_{side}", tuple(head + face * 3.2 * k + [s_ * 1.6 * k, 0, 0] + [0, 0.707, -0.707]),
                     (2, 1, 1), "eyelid", rotation=(-45, 0, 0))

    # -- the lantern: the face, hanging from the brow on a root --
    def lantern_parts(self, t4):
        anchor = LANTERN_ANCHOR
        J = [anchor + DOWN * 9 * k + [0.6 * k, 0, -0.4 * k] for k in range(4)]
        self.lroot = Chain(t4, "lantern_root", J, DOWN)
        for k, b in enumerate(self.lroot.bones):
            octo_seg(b, f"lantern_root{k}_bark", self.lroot.rest[k], DOWN, self.lroot.lengths[k], 5 - k * 0.6,
                     5 - k * 0.6, "root", False)
        end = self.lroot.joints()[-1]
        last = self.lroot.bones[-1]
        lan = self.lantern = last.group("hi_lantern", tuple(to_rest(last, end)))
        c = np.array(lan.origin) + [0, -11, 0]
        lan.box("heart", tuple(c), (16, 16, 16), "heart")             # the vanilla creaking heart, one block
        for i, (x, z) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
            lan.box(f"cage{i}", tuple(c + [x * 8.5, 0, z * 8.5]), (3, 19, 3), "heart_frame")
        lan.box("cage_top", tuple(c + [0, 9.5, 0]), (13, 3, 13), "heart_frame", rotation=(0, 45, 0))
        lan.box("cage_foot", tuple(c + [0, -9.5, 0]), (10, 3, 10), "heart_frame", rotation=(0, 45, 0))
        lan.box("tail", tuple(c + [0, -14, 0]), (3, 6, 3), "root")
        # its glow: the same block a quarter texel bigger (inflate), only the awake heart's orange cracks drawn on it,
        # full-bright; the bark between them stays lit by the world
        glow = lan.group("glow_lantern", tuple(c))
        glow.box("heart_glow", tuple(c), (16, 16, 16), "glow").inflate = 0.25
        set_world_R(lan, roty(TWIST * 0.5))

    # -- arms --
    def arm_parts(self, key):
        (s1pt, bone), (ctrl, w0, w1, n, fingers, drag) = SHOULDERS[key], ARMS[key]
        tb = self.trunk.bones[bone]
        S = yaw_about(s1pt, TWIST)
        pts = curve([S] + list(ctrl), 400)
        total = sum(np.linalg.norm(pts[i + 1] - pts[i]) for i in range(400))
        J = fit([S] + list(ctrl), [total / n] * n)
        ch = Chain(tb, f"arm_{key}", J, DOWN)
        ws = [w1 + (w0 - w1) * (1 - (k + 0.5) / n) ** 1.4 for k in range(n)]
        ch.widths = ws
        ch.bones[0].box(f"arm_{key}_flare", tuple(ch.rest[0]), (w0 * 1.3, w0 * 1.1, w0 * 1.3), "bark")
        for k, b in enumerate(ch.bones):
            w = ws[k]
            octo_seg(b, f"arm_{key}{k}_bark", ch.rest[k], DOWN, ch.lengths[k], w, w * 0.9, "bark")
            if k in (2, 4) and w > 5:
                b.box(f"arm_{key}{k}_knot", tuple(ch.rest[k]), (w * 1.3, w, w * 1.3), "bark_dark")
        # eyeblossoms: on the bark face that looks most upward in the bind pose
        for k in BLOOMS[key]:
            b = ch.bones[k]
            R = wR(b)
            faces = [np.array(f, float) for f in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1))]
            order = sorted(faces, key=lambda f: -(R @ f)[1])
            glow = b.group(f"glow_blooms_{key}{k}", tuple(ch.seg(k, 0.5)))
            for j, (f, frac) in enumerate(((order[0], 0.3), (order[0], 0.72), (order[1], 0.5))):
                c = ch.seg(k, frac) + f * (ws[k] * (0.5 if abs(f[0]) else 0.45))
                flower(b, glow, f"arm_{key}{k}_bloom{j}", c, f, open_=(j + k) % 3 != 2)
        ch.moss = []
        for i, (k, f, length) in enumerate(MOSS.get(key, ())):
            b = ch.bones[k]
            top = wpos(b, ch.seg(k, f)) + [0, -ws[k] * 0.45, 0]
            ch.moss.append(moss_bone(b, f"moss_{key}{i}", top, length))
        ch.hand = hand_bone(ch.bones[-1], f"hand_{key}", ch.joints()[-1], drag, fingers=fingers,
                            curl=-25 if key == "crutch" else 0)
        ch.drag = drag
        return ch

    # -- legs: thigh, shin, cannon, then the foot's toes --
    def leg_parts(self, side):
        J = [np.array(p, float) for p in LEGS[side]]
        ch = Chain(self.hips, f"leg_{side}", J, DOWN, names=[f"thigh_{side}", f"shin_{side}", f"cannon_{side}"])
        for k, (b, w) in enumerate(zip(ch.bones, (9, 7, 6))):
            octo_seg(b, f"leg_{side}{k}_bark", ch.rest[k], DOWN, ch.lengths[k], w, w, "bark")
        ch.bones[0].box(f"knee_{side}", tuple(ch.rest[1]), (10, 9, 10), "bark_dark")
        ch.bones[1].box(f"hock_{side}", tuple(ch.rest[2]), (8, 8, 8), "bark_dark")
        foot = ch.bones[2].group(f"foot_{side}", tuple(ch.rest[3]))
        o = np.array(foot.origin)
        for i, ang in enumerate((-22.5, 0, 22.5, 180)):
            ln = 8 if ang == 180 else 14
            d = roty(ang) @ np.array([0, 0, -1.0])
            foot.box(f"toe_{side}{i}", tuple(o + d * ln / 2 + [0, 0.5, 0]), (3.5, 3, ln), "root", rotation=(0, ang, 0))
        set_world_R(foot, np.eye(3))
        ch.foot = foot
        return ch

    # ---- posing ----------------------------------------------------------------------------------------------------
    def chains(self):
        return [self.trunk, self.lroot] + self.stubs + list(self.arms.values()) + list(self.legs.values())

    def rehang(self):
        """After a pose: moss hangs straight down again, the lantern root hangs (with its swing), hands lie flat."""
        for g in self.moss + [s for a in self.arms.values() for s in a.moss]:
            set_world_R(g, np.eye(3))

    def pose(self, p):
        if "hips" in p:
            dy, dz, pitch = p["hips"]
            translate(self.hips, (0, dy, dz))
            for ch in self.chains():
                ch.rest = [r + np.array([0, dy, dz]) for r in ch.rest]
            self.hips.rotation = [pitch, 0, 0]
        if "trunk" in p:          # extra pitch per trunk joint (world x, cumulative) and a yaw
            pitches, yaw = p["trunk"]
            J = self.trunk.joints()
            for k, a in enumerate(pitches):
                R = rotation_matrix((a, 0, 0))
                J = J[:k + 1] + [J[k] + R @ (q - J[k]) for q in J[k + 1:]]
            J = [J[0]] + [J[0] + roty(yaw) @ (q - J[0]) for q in J[1:]]
            self.trunk.place(J)
        for side, (foot, hock_dir, hint) in p.get("legs", {}).items():
            ch = self.legs[side]
            hip = ch.joints()[0]
            foot = np.array(foot, float)
            hock = foot + _n(hock_dir) * ch.lengths[2]
            knee = ik(hip, hock, hip + np.array(hint, float), ch.lengths[0], ch.lengths[1])
            ch.place([hip, knee, hock, foot])
            set_world_R(ch.foot, roty(p.get("foot_yaw", {}).get(side, 0)))
        for key, ch in self.arms.items():
            if key not in p.get("arms", {}) and ("trunk" in p or "hips" in p):
                ch.drag_to(self.bind_hands[key] + np.array(p.get("drag_shift", (0, 0, 0)), float))
                aim_hand(ch.hand, ch.drag, -25 if key == "crutch" else 0)
        for key, spec in p.get("arms", {}).items():
            ch = self.arms[key]
            ctrl, drag, curl = spec[0], spec[1], spec[2] if len(spec) > 2 else 0
            ch.pose_along(ctrl)
            aim_hand(ch.hand, drag, curl)
        if "lantern" in p:        # the root hangs from the brow; swing tips it (a world direction added to down)
            swing, length_scale = p["lantern"]
            a = self.lroot.joints()[0]
            d = _n(DOWN + np.array(swing, float))
            J = [a]
            low = 26 if abs(p.get("lantern_tilt", 0)) < 45 else 16
            for k, L in enumerate(self.lroot.lengths):
                q = J[-1] + _n(d + DOWN * 0.15 * k) * L
                q[1] = max(q[1], low)
                J.append(J[-1] + _n(q - J[-1]) * L)
            self.lroot.place(J)
            set_world_R(self.lantern, roty(p.get("lantern_yaw", TWIST * 0.5)) @ rotation_matrix((p.get("lantern_tilt", 0), 0, 0)))
        self.rehang()
        return self


def translate(g, d):
    d = np.array(d, float)
    g.origin = (np.array(g.origin) + d).tolist()
    for ch in g.children:
        if isinstance(ch, Group):
            translate(ch, d)
        else:
            ch.frm, ch.to, ch.origin = [(np.array(v) + d).tolist() for v in (ch.frm, ch.to, ch.origin)]


# ---- the key poses (world targets) --------------------------------------------------------------------------------------

POSES = {
    "idle": ("idle: the stalk (the bind pose)", {}),
    "walk": ("walk: the crutch swung ahead, the legs striding, the arms dragging", {
        "trunk": ([4, 0, 0, 0, 0], 0),
        "legs": {"right": ((14, 2, -12), (0, 1, 0.9), (0, 0, -20)), "left": ((-14, 2, 30), (0, 1, 0.6), (0, 0, -20))},
        "arms": {"crutch": ([(-36, 92, -40), (-38, 60, -58), (-33, 9, -64)], (0, 0, -1), -25),
                 "great": ([(44, 108, -10), (52, 76, 8), (52, 36, 30), (44, 4, 64)], (0, 0, 1)),
                 "back": ([(-14, 124, 26), (-24, 100, 50), (-22, 40, 66), (-12, 4, 80)], (0, 0, 1))},
        "lantern": ((0, 0, 0.3), 1)}),
    "swipe": ("swipe (wind-up): rears and coils, the great arm raised over its head", {
        "trunk": ([10, 6, 0, 0, 0], -12),
        "legs": {"right": ((24, 2, -4), (0, 1, 0.8), (0, 0, -20)), "left": ((-22, 2, 22), (0, 1, 0.6), (0, 0, -20))},
        "arms": {"great": ([(36, 130, -10), (40, 156, 4), (30, 160, 26), (18, 146, 38)], (0, -0.6, 1)),
                 "crutch": ([(-38, 84, -34), (-40, 50, -44), (-36, 9, -48)], (0, 0, -1), -25),
                 "lesser": ([(32, 60, 0), (36, 40, 20), (30, 4, 40)], (0, 0, 1))},
        "lantern": ((0, 0, 0.35), 1), "lantern_tilt": 12}),
    "lunge": ("lunge: thrown forward onto the crutch, the great arm reaching low", {
        "hips": (-8, -10, 0),
        "trunk": ([-14, -6, 0, 0, 0], 4),
        "legs": {"right": ((16, 2, -16), (0, 1, 0.5), (0, 0, -20)), "left": ((-14, 2, 34), (0, 0.7, 1), (0, 0, -20))},
        "arms": {"crutch": ([(-36, 82, -56), (-38, 46, -76), (-32, 9, -88)], (0, 0, -1), -25),
                 "great": ([(40, 96, -46), (46, 74, -74), (36, 34, -100), (20, 12, -116)], (0, -0.2, -1))},
        "lantern": ((0, 0, -0.45), 1), "lantern_tilt": -15}),
    "eruption": ("root eruption: every hand driven into the floor", {
        "hips": (-6, 0, 0),
        "trunk": ([-8, -4, 0, 0, 0], 0),
        "legs": {"right": ((22, 2, 2), (0, 1, 0.8), (0, 0, -20)), "left": ((-22, 2, 18), (0, 1, 0.6), (0, 0, -20))},
        "arms": {"crutch": ([(-44, 96, -30), (-56, 90, -44), (-58, 40, -54), (-50, 7, -58)], (0, 0, -1), -30),
                 "great": ([(44, 112, -16), (62, 112, -24), (70, 60, -32), (60, 7, -36)], (0, 0, -1), -30),
                 "lesser": ([(34, 66, -10), (46, 50, -4), (50, 7, 8)], (0.5, 0, 0.5), -30),
                 "back": ([(-14, 124, 26), (-36, 112, 40), (-56, 60, 40), (-52, 7, 30)], (-0.5, 0, 0.5), -30)},
        "lantern": ((0, 0, -0.1), 1)}),
    "sap": ("sap rain: rears up, the womb lifted, the arms flung wide", {
        "hips": (2, 2, 0),
        "trunk": ([10, 6, 4, 0, 0], 0),
        "legs": {"right": ((18, 2, 0), (0, 1, 0.8), (0, 0, -20)), "left": ((-18, 2, 20), (0, 1, 0.6), (0, 0, -20))},
        "arms": {"great": ([(40, 122, -6), (58, 140, 4), (66, 146, 18), (60, 132, 34)], (1, -0.4, 0.4)),
                 "back": ([(-14, 130, 20), (-36, 146, 26), (-50, 144, 40), (-48, 128, 56)], (-1, -0.4, 0.4)),
                 "thin": ([(26, 132, 16), (34, 150, 30), (40, 160, 42)], (0.4, 1, 0.2)),
                 "crutch": ([(-38, 90, -30), (-42, 50, -40), (-38, 9, -44)], (0, 0, -1), -25)},
        "lantern": ((0, 0, 0.5), 1), "lantern_tilt": 18}),
    "slam": ("ground slam: the crutch and the great arm brought down together ahead", {
        "hips": (-8, -6, 0),
        "trunk": ([-16, -8, 0, 0, 0], 0),
        "legs": {"right": ((20, 2, -4), (0, 1, 0.6), (0, 0, -20)), "left": ((-20, 2, 20), (0, 1, 0.6), (0, 0, -20))},
        "arms": {"crutch": ([(-40, 104, -44), (-44, 92, -66), (-34, 40, -84), (-20, 7, -90)], (0.3, 0, -1), -30),
                 "great": ([(42, 106, -44), (48, 94, -66), (36, 40, -86), (20, 7, -92)], (-0.3, 0, -1), -30)},
        "lantern": ((0, 0, -0.2), 0.9)}),
    "death": ("death: the legs give, it folds onto its crutch and topples, the lantern on the floor", {
        "hips": (-30, -6, 0),
        "trunk": ([-30, -18, 0, 0, 0], 8),
        "legs": {"right": ((24, 2, -16), (0, 0.25, 1), (0, 0, -20)), "left": ((-22, 2, 14), (0, 0.25, 1), (0, 0, -20))},
        "arms": {"crutch": ([(-46, 50, -40), (-60, 20, -54), (-66, 4, -60)], (-0.6, 0, -1)),
                 "great": ([(46, 50, -30), (60, 20, -20), (70, 4, 4)], (1, 0, 0.6)),
                 "lesser": ([(32, 30, -4), (40, 10, 20), (36, 4, 40)], (0, 0, 1)),
                 "back": ([(-20, 74, 24), (-36, 40, 44), (-40, 4, 64)], (0, 0, 1)),
                 "thin": ([(24, 80, 10), (36, 50, 20), (40, 6, 30)], (0, 0, 1))},
        "lantern": ((0, 0, -0.9), 1), "lantern_tilt": 80}),
}


# ---- checks, renders, sheets ------------------------------------------------------------------------------------------

def displays(m):
    """BetterModel display estimate: one per bone with cubes, plus one per cube not square in its bone or turned on
    one axis by 22.5 or 45 degrees."""
    ok = {0.0, 22.5, 45.0, -22.5, -45.0}
    n = 0
    for g in m.groups:
        cubes = [c for c in g.children if not isinstance(c, Group)]
        if not cubes:
            continue
        n += 1
        for c in cubes:
            turned = [a for a in c.rotation if abs(a) > 1e-6]
            if len(turned) > 1 or (turned and round(turned[0], 3) not in ok):
                n += 1
    return n


def in_subtree(c, names):
    g = c.group
    while g is not None:
        if any(g.name.startswith(n) for n in names):
            return True
        g = g.parent
    return False


def hitbox_bounds(m):
    pts = np.vstack([c.corners() for c in m.cubes if not in_subtree(c, ("arm_", "hand_", "moss_", "stub_", "glow_bl",
                                                                        "glow_hump"))])
    lo, hi = pts.min(0), pts.max(0)
    return tuple(float(np.floor(v)) for v in (lo[0], 0.0, lo[2])), tuple(float(np.ceil(v)) for v in hi)


def visible_boxes(m, palette, alpha=True):
    boxes = []
    for c in m.cubes:
        col = palette[c.mat]
        b = {"name": c.name, "mat": c.mat, "color": [v / 255 for v in col[:3]], "corners": c.corners().tolist()}
        if alpha and len(col) > 3 and col[3] < 255:
            b["alpha"] = col[3] / 255
        boxes.append(b)
    return boxes


def blender(boxes, out, views, extra=None):
    out.mkdir(parents=True, exist_ok=True)
    f = out / "render_job.json"
    f.write_text(json.dumps(dict({"boxes": boxes, "out": out.as_posix(), "views": views, "res": [900, 700]},
                                 **(extra or {}))), encoding="utf-8")
    r = subprocess.run([str(v2.BLENDER), "-b", "--factory-startup", "--python",
                        str(ROOT / "tools/art/bosskit/blender_render.py"), "--", str(f)], capture_output=True, text=True)
    if r.returncode or "RENDER_DONE" not in r.stdout:
        raise SystemExit(r.stdout[-2000:] + r.stderr[-2000:])
    f.unlink()


def render_glowing(m, out, views):
    """A normal render, then an unlit pass with only the glow coloured, laid over it with a bloom."""
    blender(visible_boxes(m, PALETTE), out, views)
    dark = {k: (v if k in GLOW else (0, 0, 0)) for k, v in PALETTE.items()}
    blender(visible_boxes(m, dark, alpha=False), out / "glow", [dict(v, light="FLAT") for v in views],
            {"ground": [0, 0, 0], "sky": [0, 0, 0], "player_color": [0, 0, 0]})
    for v in views:
        if v["mode"] != "flat":
            continue
        base = Image.open(out / f"{v['name']}.png").convert("RGB")
        mask = Image.open(out / "glow" / f"{v['name']}.png").convert("RGB")
        lit = mask.convert("L").point(lambda x: 255 if x > 24 else 0)
        base.paste(mask, (0, 0), lit)
        bloom = mask.filter(ImageFilter.GaussianBlur(6)).point(lambda x: min(255, int(x * 1.1)))
        ImageChops.screen(base, bloom).save(out / f"{v['name']}.png")
    shutil.rmtree(out / "glow")


def parts_list(m):
    rows = []
    for g in m.groups:
        cubes = [c for c in g.children if not isinstance(c, Group)]
        if cubes:
            mats = sorted({c.mat for c in cubes})
            parent = g.parent.name if g.parent is not None and g.parent.name != "root" else "-"
            rows.append(f"| `{g.name}` | {parent} | {len(cubes)} | {', '.join(mats)} |")
    return "\n".join(["| Bone | Parent | Cubes | Materials |", "|---|---|---|---|"] + rows)


MAIN_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 35, "height": 4.2, "dist": 15, "target_z": 3.4},
    {"name": "flat_front", "mode": "flat", "camera": "ortho_front"},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
    {"name": "clay_34", "mode": "clay", "camera": "persp", "yaw": -40, "height": 3.0, "dist": 15, "target_z": 3.6,
     "player": False},
]
CHEST = {"name": "chest", "mode": "flat", "camera": "persp", "yaw": 28, "height": 2.4, "dist": 19, "target_z": 4.4,
         "lens": 62, "player": False}
POSE_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 40, "height": 4.0, "dist": 16, "target_z": 3.4,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
]


def womb_closeup(r):
    """The womb alone, its resin faded, to show the sleeper's curl (front and side); checks it sits inside."""
    w = r.womb
    Rw, c, half = wR(w), wpos(w, w.origin), np.array(WOMB_SIZE) / 2
    inner = [cu for cu in r.m.cubes if in_subtree(cu, ("sleeper", "glow_sleeper"))]
    margin = max(float((np.abs((Rw.T @ (cu.corners() - c).T).T) - half).max()) for cu in inner)
    if margin > -0.5:
        raise SystemExit(f"the sleeper pokes out of the resin ({margin:.1f})")
    pal = dict(PALETTE, resin=(228, 132, 34, 60))
    boxes = [b for b, cu in zip(visible_boxes(r.m, pal), r.m.cubes) if in_subtree(cu, ("womb",))]
    views = [{"name": "womb_front", "mode": "flat", "camera": "persp", "yaw": 10, "height": 4.0, "dist": 3.0, "lens": 38,
              "player": False}, {"name": "womb_side", "mode": "flat", "camera": "ortho_side", "player": False}]
    blender(boxes, OUT / "womb", views, {"player": False, "ground": [0.16, 0.15, 0.19]})
    a, b = (Image.open(OUT / "womb" / f"{n}.png") for n in ("womb_front", "womb_side"))
    img = Image.new("RGB", (a.width + b.width + 10, a.height), sheet.BG)
    img.paste(a, (0, 0))
    img.paste(b, (a.width + 10, 0))
    img.save(OUT / "womb.png")
    return round(-margin, 1)


def build(key="idle"):
    r = Rig()
    r.pose(POSES[key][1])
    v2.snap(r.m)
    return r


def main(args):
    v2.PALETTE.update(PALETTE)
    only = [a for a in args if a in POSES]
    if not only:
        if OUT.exists():
            for old in OUT.iterdir():
                if old.is_dir():
                    shutil.rmtree(old)
                elif old.name != "README.md":
                    old.unlink()
        OUT.mkdir(parents=True, exist_ok=True)
        bind = build()
        frm, to = hitbox_bounds(bind.m)
        bb = bind.m.to_bbmodel()
        add_hitbox(bb, frm, to)
        (OUT / "design").mkdir()
        (OUT / "design" / f"{NAME}_blockout.bbmodel").write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
        render_glowing(bind.m, OUT / "design", MAIN_VIEWS + [CHEST])
        gap = womb_closeup(bind)
        stats = dict(bind.m.stats(), displays=displays(bind.m), sleeper_gap=gap, hitbox_blocks=[round((t - f) / 16, 2)
                                                                               for f, t in zip(frm, to)])
        (OUT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(stats))
        sheet.compare_sheet(OUT, [("design", "the design lock (the stalk)")], OUT / "design.png",
                            heading="Heartwood Horror - design lock (session 2)",
                            views=("flat_34", "flat_front", "sil_side", "clay_34"))
        boxes = visible_boxes(bind.m, PALETTE, alpha=False)
        for b in boxes:
            b["color"] = [c * 0.55 + 0.4 for c in b["color"]]
        boxes.append(v2.box_json("hitbox", frm, to, "hitbox"))
        blender(boxes, OUT / "hitbox", [{"name": "hitbox_front", "mode": "flat", "camera": "ortho_front"},
                                        {"name": "hitbox_side", "mode": "flat", "camera": "ortho_side"}])
        a, b = (Image.open(OUT / "hitbox" / f"hitbox_{v}.png") for v in ("front", "side"))
        both = Image.new("RGB", (a.width + b.width + 10, a.height), sheet.BG)
        both.paste(a, (0, 0))
        both.paste(b, (a.width + 10, 0))
        both.save(OUT / "hitbox.png")
        (OUT / "parts.md").write_text("# Heartwood Horror rig parts (session 2)\n\nGenerated by "
                                      "`tools/art/bosses/heartwood_s2.py`. Cube sizes are whole texels.\n\n"
                                      + parts_list(bind.m) + "\n", encoding="utf-8")
    for key in only or POSES:
        r = build(key)
        render_glowing(r.m, OUT / "poses" / key, POSE_VIEWS)
        lo, hi = r.m.bounds()
        print(key, "size", [round(float(v) / 16, 2) for v in hi - lo], "lowest", round(float(lo[1]), 1))
    if not only:
        keys = list(POSES)
        for i, chunk in enumerate((keys[:3], keys[3:6], keys[6:])):
            sheet.compare_sheet(OUT / "poses", [(k, POSES[k][0].split(":")[0]) for k in chunk],
                                OUT / f"poses_{i + 1}.png",
                                heading="Heartwood Horror - key poses from the rig (" + ", ".join(chunk) + ")",
                                views=("flat_34", "sil_side"))


if __name__ == "__main__":
    main(sys.argv[1:])
