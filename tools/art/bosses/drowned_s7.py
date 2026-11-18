"""The Drowned Elder redesign, session 7: animation (plan: docs/art/bosses/drowned_elder/overhaul/plan.md).

A serpent sells itself through how it moves, so the clips are authored as motion, not as a few poses blended together:

- **Shapes, not joint angles.** The body at any moment is a shape: the face's position plus the direction of the body
  every 8 units down its length (`Shape`). Shapes blend by turning those directions (slerp), so every in-between
  frame is a real, unbroken body of the right length, never a joint-space average that folds through itself.
- **Motion travels down the body.** A change starts at the head and reaches the tail later (`lag`): the body flows into
  a coil, the head leads a strike and the tail follows through.
- **Path following** for the moves through the floor: the head travels along a path and every point of the body
  follows the same path behind it, so the body pours into the floor through one hole and out of another (the surge),
  and spirals up out of the summoning circle (the spawn).
- **Anticipation, overshoot and settle** on every attack (the head draws back before the beam curl, the gills and the
  hood snap open past their mark and settle, the head recoils when the beams fire), and **secondary motion** while
  swimming (the hood breathes, the pectoral fins paddle, the fluke flicks a beat behind the wave).
- **Dense keys** (every 0.05 s; 0.1 s for the swim) sampled from those curves, each joint angle kept continuous with the
  key before it, so BetterModel's smooth interpolation has nothing to guess.

Clips, timed to DrownedElder.java and Abyss.Beam (session 8 moves the attacks onto these contacts):
  idle     3.2 s loop   swimming: a wave from the neck to the fluke, hood breathing, fins paddling, the head steady
  spawn    4.0 s once   it spirals up out of the circle, arcs over, rears with a roar (2.8 s), settles into the swim
  aim      2.6 s once   draws back (0.3 s), curls on the players with the gills snapping open, holds while the beams
                        charge, tenses, fires at 2.0 s (contact: Abyss.Beam's 40-tick charge), recoils, swims on
  stare    2.6 s once   coils overhead head first, the hood flares, lunges its glare down at 1.0 s (contact), holds,
                        uncoils
  shed     1.2 s once   guardians join: two shudders run down the body, the gills flutter; at 0.5 s (contact)
  dive     1.4 s hold   the Tidal Surge: rears up and over (anticipation), hangs, strikes head first into the floor at
                        1.0 s (contact: the first wave), the body arching over the hole, and holds
  emerge   2.6 s once   carries on along the same path: the arch pours into the floor and the head bursts out of a
                        second hole behind it, rears up with a roar (1.4 s, contact), and settles into the swim
  flinch   0.5 s once   hit: the head snaps back, a ripple runs down the body, the hood twitches
  death    3.4 s hold   rears, thrashes twice, falls head first, slumps, curls into its coil; the tail's last flick

Run from the repository root, after drowned_s6.py, with the folder holding assets/ from the 26.2 client as the last
argument: python tools/art/bosses/drowned_s7.py <folder> [--no-gifs]
"""
import copy
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses import archevoker_s7 as a7  # noqa: E402
from bosses import drowned_s2 as s2, drowned_s3 as s3, drowned_s4 as s4  # noqa: E402
from bosses import tempest_s7 as t7  # noqa: E402
from bosses.tempest_silhouettes import axis_angle  # noqa: E402

OUT = ROOT / "docs/art/bosses/drowned_elder/overhaul/s7_animation"
S6 = ROOT / "docs/art/bosses/drowned_elder/overhaul/s6_variants"
a7.OUT = OUT
a7.s4.ZONES, a7.s4.GLOWING = s4.ZONES, ("glow", "eye")
CONTACT = {"spawn": 2.8, "aim": 2.0, "stare": 1.0, "shed": 0.5, "dive": 1.0, "emerge": 1.4}
OVERRIDE = ("spawn", "aim", "stare", "shed", "dive", "emerge", "flinch", "death")
TAU = 2 * math.pi
H_STEP = 8.0                          # model units between two shape points
L = 352.0                             # shape length: the whole chain (331) and a little more
NP = int(L / H_STEP) + 1
UP = np.array([0.0, 1.0, 0.0])


def n(v):
    v = np.asarray(v, float)
    d = np.linalg.norm(v)
    return v / d if d > 1e-12 else v


# ---- easing --------------------------------------------------------------------------------------------------------------

def clamp01(x):
    return min(1.0, max(0.0, x))


def smooth(x):                        # ease in and out
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def smoother(x):
    x = clamp01(x)
    return x * x * x * (x * (6 * x - 15) + 10)


def ease_in(x, p=2.4):                # accelerating: a strike, a fall
    return clamp01(x) ** p


def ease_out(x, p=2.4):               # decelerating: a rise, a settle
    return 1 - (1 - clamp01(x)) ** p


def back_out(x, s=1.9):               # past the mark and back: a snap that settles
    x = clamp01(x) - 1
    return 1 + x * x * ((s + 1) * x + s)


def span(t, t0, t1):
    return clamp01((t - t0) / max(1e-9, t1 - t0))


def pulse(t, at, width):
    return math.exp(-((t - at) / width) ** 2)


# ---- shapes --------------------------------------------------------------------------------------------------------------

class Shape:
    """The body: the face's position and the unit direction of each 8-unit step down the body."""

    def __init__(self, p0, dirs):
        self.p0, self.dirs = np.asarray(p0, float), np.asarray(dirs, float)

    def points(self):
        return np.vstack([self.p0, self.p0 + np.cumsum(self.dirs * H_STEP, axis=0)])

    @staticmethod
    def from_points(pts):
        sp = s2.Spine([tuple(p) for p in pts])
        samples = np.array([sp.at(k * H_STEP)[0] for k in range(NP)])
        dirs = np.array([n(b - a) for a, b in zip(samples[:-1], samples[1:])])
        return Shape(samples[0], dirs)


def slerp(a, b, w):
    d = float(np.clip(np.dot(a, b), -1, 1))
    if d > 0.9995:
        return n(a + (b - a) * w)
    if d < -0.999:                    # opposite: turn through the world's up (or sideways when vertical)
        axis = n(np.cross(a, UP)) if abs(a[1]) < 0.9 else n(np.cross(a, [1.0, 0, 0]))
        mid = n(np.cross(axis, a))
        return n(a * math.cos(math.pi * w) + mid * math.sin(math.pi * w))
    th = math.acos(d)
    return n((math.sin((1 - w) * th) * a + math.sin(w * th) * b) / math.sin(th))


def lag_weights(t, t0, t1, lag, ease=smooth):
    """Blend weight per shape point: the head starts at t0 and reaches 1 at t1; each point further down starts later,
    by up to `lag` seconds at the tail."""
    dur = t1 - t0
    return np.array([ease(span(t, t0 + lag * k / (NP - 1), t0 + lag * k / (NP - 1) + dur)) for k in range(NP)])


def heading(d):
    """A direction as heading (degrees round the world's up, 0 = towards -z, the swim's forward) and climb."""
    return math.degrees(math.atan2(-d[0], -d[2])), math.degrees(math.asin(float(np.clip(d[1], -1, 1))))


def from_heading(h, c):
    h, c = math.radians(h), math.radians(c)
    return np.array([-math.sin(h) * math.cos(c), math.sin(c), -math.cos(h) * math.cos(c)])


def blend(a, b, w, anchor="face"):
    """a -> b; w is a number or one weight per shape point (the face's position uses w[0]).

    Directions blend as heading and climb, the heading change unwrapped down the body: neighbouring steps always turn
    the same way by about the same amount, so a coil winds and unwinds in one sense. Turning each step by its own
    shortest way (slerp) let neighbours go opposite ways round and kinked the body (the first stare)."""
    w = np.broadcast_to(np.asarray(w, float), (NP,))
    p0 = a.p0 + (b.p0 - a.p0) * w[0]
    dirs, prev = [], None
    for k in range(NP - 1):
        ha, ca = heading(a.dirs[k])
        hb, cb = heading(b.dirs[k])
        dh = (hb - ha + 180) % 360 - 180
        if prev is not None and abs(ca) < 80 and abs(cb) < 80:
            dh += 360 * round((prev - dh) / 360)
        prev = dh if (abs(ca) < 80 and abs(cb) < 80) else prev
        if abs(ca) >= 80 or abs(cb) >= 80:                 # pointing up or down: the heading means little; slerp
            dirs.append(slerp(a.dirs[k], b.dirs[k], w[k + 1]))
        else:
            dirs.append(from_heading(ha + dh * w[k + 1], ca + (cb - ca) * w[k + 1]))
    dirs = np.array(dirs)
    if anchor == "tail":                                   # build from where the tail lies (a fall, a rear-up)
        ta, tb = a.points()[-1], b.points()[-1]
        tail = ta + (tb - ta) * w[-1]
        p0 = tail - np.sum(dirs * H_STEP, axis=0)
    return Shape(p0, dirs)


def turn(v, axis, deg):
    return axis_angle(axis, deg) @ v


def side_axis(d):
    """The axis a step turns about to bend sideways: the world's up, or across the body when it points up or down."""
    return UP if abs(d[1]) < 0.95 else np.array([1.0, 0, 0])


def wave(shape, phase, amp_deg, wavelength=120.0, start=3, vertical=0.0):
    """Adds a travelling wave to the body's heading: each step's direction swings up to amp_deg sideways (and
    `vertical` up and down) round the shape's own, the swing growing from the neck towards the tail and running down
    the body as the phase advances. A heading wave integrates into the swimming S (a wavelength of 2 x 120 units, the
    tail swinging about a block and a half each side at full size)."""
    dirs = shape.dirs.copy()
    for k in range(start, NP - 1):
        s = k * H_STEP
        grow = min(1.0, (k - start) / 12.0) * (0.75 + 0.25 * k / (NP - 2))
        d = dirs[k]
        d = turn(d, side_axis(d), amp_deg * grow * math.sin(s / wavelength * math.pi - phase))
        if vertical:
            across = n(np.cross(UP, d)) if abs(d[1]) < 0.95 else np.array([1.0, 0, 0])
            d = turn(d, across, vertical * grow * math.sin(s / (wavelength * 1.3) * math.pi - phase + 1.2))
        dirs[k] = n(d)
    return Shape(shape.p0, dirs)


def add_turns(shape, turns):
    dirs = shape.dirs.copy()
    for k, a in enumerate(turns):
        if abs(a) > 1e-6:
            dirs[k] = n(turn(dirs[k], side_axis(dirs[k]), a))
    return Shape(shape.p0, dirs)


def ripple(t, t0, speed=1.6, amp=26.0, width=0.18):
    """An impulse travelling down the body from t0 (the tail is reached 1/speed s later): per-step sideways turns."""
    out = np.zeros(NP - 1)
    for k in range(NP - 1):
        x = (t - (t0 + k / (NP - 2) / speed)) / width
        if -1 < x < 1:
            out[k] = amp * math.sin(math.pi * x) * (1 - abs(x))
    return out


# ---- the shapes the clips move between ---------------------------------------------------------------------------------

_HEAD = None


def head_y():
    """The swimming head's height (session 2's idle pose sets where the carrier holds it)."""
    global _HEAD
    if _HEAD is None:
        m = s3.build("idle")
        _HEAD = float(next(g for g in m.groups if g.name == "base").origin[1])
    return _HEAD


def straight():
    hy = head_y()
    return Shape.from_points([(0, hy, -24 + k * 40.0) for k in range(12)])


def swim(phase=0.0, amp=1.0):
    """The swim: the straight body with the travelling wave on it (sideways, a little up and down)."""
    return wave(straight(), phase, 38 * amp, vertical=9 * amp)


def from_s2(name, dy=0.0, dz=0.0):
    return Shape.from_points([(x, y + dy, z + dz) for x, y, z in s2.SPINES[name]])


_SHAPES = None


def shapes():
    global _SHAPES
    if _SHAPES is None:
        hy = head_y()
        _SHAPES = {
            "swim": swim(0.0),
            # the beam curl's anticipation: the head drawn up and back, the neck gathered under it
            "antic": Shape.from_points([(0, hy + 22, -10), (0, hy + 16, 12), (0, hy + 4, 40), (0, hy - 4, 76),
                                        (0, hy, 120), (0, hy, 180), (0, hy, 240), (0, hy, 300), (0, hy, 360),
                                        (0, hy, 420)]),
            # the beam coil: head raised, the body thrown into a wide S so the three eye segments face out three ways
            "aim": Shape.from_points([(0, hy + 24, -30), (0, hy + 18, -6), (-26, hy + 8, 14), (-52, hy + 2, 46),
                                      (-34, hy, 84), (14, hy, 100), (52, hy, 128), (40, hy, 168), (0, hy, 196),
                                      (-34, hy, 236), (-22, hy, 284), (0, hy, 330), (0, hy, 400)]),
            "stare": from_s2("stare", dy=hy + 6 - 60, dz=-24),
            "rear": Shape.from_points([(0, 150, -40), (0, 160, 0), (0, 130, 40), (0, 84, 62), (0, 48, 100),
                                       (0, 40, 170), (0, 40, 250), (0, 40, 330), (0, 40, 410)]),
            "slump": Shape.from_points([(0, 32, -40), (0, 30, 0), (6, 28, 60), (-6, 28, 120), (6, 28, 180),
                                        (-6, 28, 240), (0, 28, 300), (0, 28, 360), (0, 28, 420)]),
            "coil": from_s2("death", dy=10.0),
        }
    return _SHAPES


# ---- paths -----------------------------------------------------------------------------------------------------------------

class Path:
    """A way the whole body follows: `start` is the body as the move begins, `ahead` the head's way on from there.
    shape(p) is the body with its face p units along the way, every point of it on the same path behind."""

    def __init__(self, start, ahead):
        body = start.points()[::-1]                       # tail ... face
        ctrl = [tuple(q) for q in body[::3]] + [tuple(body[-1])] + [tuple(q) for q in ahead]
        self.sp = s2.Spine(ctrl, samples=4000)
        i = int(np.argmin(np.linalg.norm(self.sp.p - body[-1], axis=1)))
        self.face0 = float(self.sp.s[i])

    def at(self, u):
        return self.sp.at(u)[0]

    def shape(self, p):
        u0 = self.face0 + p
        pts = np.array([self.at(u0 - k * H_STEP) for k in range(NP)])
        dirs = np.array([n(b - a) for a, b in zip(pts[:-1], pts[1:])])
        return Shape(pts[0], dirs)

    def first(self, test, lo=0.0, hi=3000.0, step=2.0):
        """The first progress (from lo) at which test(face point) holds."""
        p = lo
        while p < hi:
            if test(self.at(self.face0 + p)):
                return p
            p += step
        return hi


_SURGE = None


def surge_path():
    """Up and over, head first into the floor (hole A, ahead), round under it, out of hole B (behind, near the
    carrier), up into a roar, then forward and down towards the swim."""
    global _SURGE
    if _SURGE is None:
        hy = head_y()
        ahead = [(0, hy + 8, -46), (0, hy + 46, -60), (0, 118, -66), (0, 160, -78), (0, 182, -98), (0, 178, -120),
                 (0, 150, -138), (0, 96, -146), (0, 30, -146), (0, -36, -140), (0, -100, -122), (0, -136, -76),
                 (0, -136, -30),
                 (0, -76, 12), (0, -14, 22), (10, 56, 20), (-12, 136, 10), (4, 196, -8), (0, 206, -32), (0, 184, -56),
                 (0, 140, -70), (0, 96, -76), (0, hy + 30, -84), (0, hy + 14, -110), (0, hy + 10, -150)]
        _SURGE = Path(swim(0.0), ahead)
    return _SURGE


_SPAWN = None


def spawn_path():
    """Out of the summoning circle in a rising spiral round its centre, then up and over towards the swim."""
    global _SPAWN
    if _SPAWN is None:
        cz, r = 30.0, 36.0
        start = Shape.from_points([(r, -40 - k * 40.0, cz) for k in range(10)])
        ahead, y = [], -40.0
        for i in range(1, 22):
            a = i * math.radians(26) * min(1.0, 0.35 + i * 0.13)
            y += 30 - 20 * min(1.0, i / 6)
            ahead.append((r * math.cos(a), y, cz + r * math.sin(a)))
        last = ahead[-1]
        ahead += [(last[0] * 0.5, 210, -4), (0, 200, -34), (0, 168, -56), (0, 130, -64)]
        _SPAWN = Path(start, ahead)
    return _SPAWN


# ---- what each clip does at time t ------------------------------------------------------------------------------------------

IDLE_LEN = 3.2


def idle(t, S):
    ph = TAU * t / IDLE_LEN
    return {"shape": swim(ph), "hood": 0.35 + 0.1 * math.sin(ph * 2),
            "extra": {"fin_right": (10 * math.sin(ph * 2), 0, 0), "fin_left": (10 * math.sin(ph * 2), 0, 0),
                      "hi_head": (1.5 * math.sin(ph * 2 + 0.6), 2.0 * math.sin(ph), 0),
                      "fluke": (0, 8 * math.sin(ph - 1.2), 0)}}


def aim(t, S):
    sw, antic, aimed = S["swim"], S["antic"], S["aim"]
    held = lambda tt: wave(aimed, TAU * (tt - 0.95) / 1.6, 7 * smooth(span(tt, 0.95, 1.2)), start=6)  # noqa: E731
    if t < 0.3:
        shape = blend(sw, antic, lag_weights(t, 0, 0.3, 0.12, smooth))
    elif t < 0.95:
        shape = blend(antic, aimed, lag_weights(t, 0.3, 0.75, 0.25, ease_out))
    elif t < 2.1:
        shape = held(t)
    else:
        shape = blend(held(2.1), sw, lag_weights(t, 2.1, 2.45, 0.25, smooth))
    if t >= 1.98:                                          # the recoil: a ripple runs down from the head
        shape = add_turns(shape, ripple(t, 2.0, speed=2.2, amp=22))
    gill = 7 + 41 * back_out(span(t, 0.45, 0.8)) - 41 * smooth(span(t, 2.1, 2.35))
    hood = 0.35 + 0.65 * smooth(span(t, 0, 0.6)) + 1.6 * back_out(span(t, 1.8, 1.98)) - 2.25 * smooth(span(t, 2.1, 2.5))
    kick = 12 * pulse(t, 2.06, 0.07) - 5 * smooth(span(t, 1.8, 1.98)) * (1 - smooth(span(t, 2.0, 2.1)))
    return {"shape": shape, "gill": gill, "hood": max(0.2, hood), "extra": {"hi_head": (kick, 0, 0)}}


def stare(t, S):
    sw, st = S["swim"], S["stare"]
    held = lambda tt: wave(st, TAU * (tt - 0.95) / 2.0, 9 * smooth(span(tt, 0.95, 1.3)), start=10)  # noqa: E731
    if t < 0.95:
        shape = blend(sw, st, lag_weights(t, 0.0, 0.6, 0.35, smoother))
    elif t < 2.0:
        shape = held(t)
    else:
        shape = blend(held(2.0), sw, lag_weights(t, 2.0, 2.35, 0.25, smoother))
    hood = 0.35 + 2.85 * back_out(span(t, 0.45, 0.95), 1.6) - 2.85 * smooth(span(t, 2.0, 2.45))
    lunge = -9 * pulse(t, 1.02, 0.08) + 3 * smooth(span(t, 1.1, 1.4)) * (1 - smooth(span(t, 2.0, 2.3)))
    return {"shape": shape, "hood": max(0.2, hood), "gill": 7, "extra": {"hi_head": (lunge, 0, 0)}}


def shed(t, S):
    shape = add_turns(S["swim"], ripple(t, 0.05, speed=1.4, amp=26) - ripple(t, 0.45, speed=1.4, amp=20))
    flutter = 7 + 14 * math.sin(TAU * t * 7) ** 2 * smooth(span(t, 0.2, 0.3)) * (1 - smooth(span(t, 0.75, 0.95)))
    hood = 0.35 + 0.8 * pulse(t, 0.12, 0.08) + 0.6 * pulse(t, 0.52, 0.08)
    return {"shape": shape, "gill": flutter, "hood": hood, "extra": {"hi_head": (-6 * pulse(t, 0.1, 0.07), 0, 0)}}


def flinch(t, S):
    shape = add_turns(S["swim"], ripple(t, 0.02, speed=2.4, amp=30, width=0.14))
    kick = 14 * pulse(t, 0.07, 0.06) - 3 * pulse(t, 0.22, 0.07)
    return {"shape": shape, "hood": 0.35 + 0.9 * pulse(t, 0.08, 0.07), "gill": 7, "extra": {"hi_head": (kick, 0, 0)}}


MARKS = {}


def marks():
    """Surge path progress at the apex, as the head meets the floor, where the dive holds (head half a block under),
    where the head breaks out of hole B and where it roars."""
    if not MARKS:
        P = surge_path()
        top = max(np.arange(0, 600, 2.0), key=lambda p: P.at(P.face0 + p)[1])
        MARKS["apex"] = float(top)
        MARKS["floor"] = P.first(lambda q: q[1] < 0)
        MARKS["hold"] = P.first(lambda q: q[1] < -36)
        MARKS["out"] = P.first(lambda q: q[1] > 0, lo=MARKS["hold"] + 40)
        MARKS["roar"] = P.first(lambda q: q[2] < -30, lo=MARKS["out"] + 40)
        S = spawn_path()
        MARKS["spawn_end"] = S.first(lambda q: q[2] < -50, lo=300)
        MARKS["spawn_begin"] = S.first(lambda q: q[1] > -24)
    return MARKS


def dive(t, S):
    P, d = surge_path(), marks()
    if t < 0.48:
        p = d["apex"] * 0.9 * ease_out(span(t, 0, 0.48), 2.0)
    elif t < 0.62:
        p = d["apex"] * (0.9 + 0.1 * smooth(span(t, 0.48, 0.62)))
    elif t < 1.0:
        p = d["apex"] + (d["floor"] - d["apex"]) * ease_in(span(t, 0.62, 1.0), 2.0)
    else:
        p = d["floor"] + (d["hold"] - d["floor"]) * ease_out(span(t, 1.0, 1.4))
    hood = 0.35 + 1.2 * smooth(span(t, 0.1, 0.48)) - 1.47 * smooth(span(t, 0.62, 0.85))
    look = 8 * smooth(span(t, 0.2, 0.5)) * (1 - smooth(span(t, 0.62, 0.8)))
    return {"shape": P.shape(p), "hood": max(0.08, hood), "gill": 7, "extra": {"hi_head": (look, 0, 0)}}


def emerge(t, S):
    P, d = surge_path(), marks()
    if t < 1.4:
        shape = P.shape(d["hold"] + (d["roar"] - d["hold"]) * smoother(span(t, 0, 1.4)))
    elif t < 1.6:
        shape = P.shape(d["roar"] + 6 * smooth(span(t, 1.4, 1.6)))
    else:
        shape = blend(P.shape(d["roar"] + 6), S["swim"], lag_weights(t, 1.6, 2.2, 0.4, smoother))
    hood = 0.08 + 1.3 * smooth(span(t, 0.6, 1.0)) + 2.1 * back_out(span(t, 1.25, 1.45)) - 3.13 * smooth(span(t, 1.8, 2.4))
    roar = 14 * smooth(span(t, 1.25, 1.42)) * (1 - smooth(span(t, 1.6, 1.95)))
    return {"shape": shape, "hood": max(0.08, hood), "gill": 7, "extra": {"hi_head": (roar, 0, 0)}}


def spawn(t, S):
    P, end, begin = spawn_path(), marks()["spawn_end"], marks()["spawn_begin"]
    if t < 2.6:
        shape = P.shape(begin + (end - begin) * smoother(span(t, 0, 2.6)))
    elif t < 3.0:
        shape = P.shape(end)
    else:
        shape = blend(P.shape(end), S["swim"], lag_weights(t, 3.0, 3.6, 0.4, smoother))
    hood = 0.1 + 1.0 * smooth(span(t, 1.0, 2.2)) + 2.4 * back_out(span(t, 2.6, 2.85)) - 3.15 * smooth(span(t, 3.1, 3.8))
    roar = 16 * smooth(span(t, 2.6, 2.8)) * (1 - smooth(span(t, 3.0, 3.4)))
    return {"shape": shape, "hood": max(0.1, hood), "gill": 7, "extra": {"hi_head": (roar, 0, 0)}}


def death(t, S):
    sw, rear, slump, coil = S["swim"], S["rear"], S["slump"], S["coil"]
    if t < 0.5:
        shape = blend(sw, rear, lag_weights(t, 0, 0.35, 0.15, ease_out), anchor="tail")
    elif t < 1.3:
        shape = wave(rear, TAU * 2.5 * (t - 0.5), 40 * math.sin(math.pi * span(t, 0.5, 1.3)), wavelength=80, start=3)
    elif t < 2.3:
        shape = blend(rear, slump, lag_weights(t, 1.3, 1.85, 0.45, ease_in), anchor="tail")
    elif t < 3.0:
        shape = blend(slump, coil, lag_weights(t, 2.3, 2.85, 0.3, smoother))
    else:
        shape = coil
    if 2.85 < t < 3.25:                                    # the tail's last flick
        flick = np.zeros(NP - 1)
        flick[-8:] = 26 * math.sin(math.pi * span(t, 2.85, 3.25))
        shape = add_turns(shape, flick)
    hood = 0.35 + 1.8 * smooth(span(t, 0.2, 0.6)) - 2.07 * smooth(span(t, 1.3, 2.0))
    shake = 7 * math.sin(TAU * 4 * t) * math.sin(math.pi * span(t, 0.5, 1.3))
    drop = -10 * smooth(span(t, 1.4, 1.9)) * (1 - smooth(span(t, 2.6, 3.0)))
    return {"shape": shape, "hood": max(0.08, hood), "gill": 7, "extra": {"hi_head": (drop, shake, 0)}}


CLIPS = {  # name: (length, loop, what happens at t, key step)
    "idle": (IDLE_LEN, "loop", idle, 0.1),
    "spawn": (4.0, "once", spawn, 0.05),
    "aim": (2.6, "once", aim, 0.05),
    "stare": (2.6, "once", stare, 0.05),
    "shed": (1.2, "once", shed, 0.05),
    "dive": (1.4, "hold", dive, 0.05),
    "emerge": (2.6, "once", emerge, 0.05),
    "flinch": (0.5, "once", flinch, 0.05),
    "death": (3.4, "hold", death, 0.05),
}


# ---- posing the rig from a frame, and the tracks -----------------------------------------------------------------------------

_BIND = None


def bind():
    global _BIND
    if _BIND is None:
        _BIND = s3.build(None)
    return _BIND


def set_gills(m, deg):
    for i in s2.EYES:
        for side, sx in (("r", -1), ("l", 1)):
            out = np.array([sx, 0, 0.0])
            rest = n(np.array([0, 0, 1.0]) * math.cos(math.radians(7)) + out * math.sin(math.radians(7)))
            want = n(np.array([0, 0, 1.0]) * math.cos(math.radians(deg)) + out * math.sin(math.radians(deg)))
            s2.group(m, f"gill{i}_{s2.SIDE[side]}").rotation = list(s2.euler(s2.rot_between(rest, want)))


def posed(frame, up0=None):
    """The rig in this frame's pose, and the head's up (handed to the next frame so the roll stays continuous)."""
    m = copy.deepcopy(bind())
    s2.set_hood(m, frame.get("hood", 0.35))
    set_gills(m, frame.get("gill", 7))
    sp = s2.bend(m, [tuple(p) for p in frame["shape"].points()], up0=up0)
    m.head_up = sp.up[0].copy()
    for bone, r in frame.get("extra", {}).items():
        g = s2.group(m, bone)
        g.rotation = [g.rotation[i] + r[i] for i in range(3)]
    return m


def wrap(a):
    return (a + 180) % 360 - 180


def pick(r_abs, rest, prev):
    """The offset from rest for r_abs, choosing between its two equal Euler forms and whole turns so it stays next to
    the previous key: consecutive keys never jump, so nothing swings the long way round between them."""
    x, y, z = r_abs
    best = None
    for c in ((x, y, z), (x + 180, 180 - y, z + 180)):
        d = np.array([wrap(c[i] - rest[i]) for i in range(3)])
        if prev is not None:
            d = d + 360 * np.round((prev - d) / 360)
        cost = float(np.abs(d - (prev if prev is not None else 0)).sum())
        if best is None or cost < best[0]:
            best = (cost, d)
    return best[1]


def tracks(name):
    length, loop, fn, step = CLIPS[name]
    S = shapes()
    rest = {g.name: np.array(g.rotation, float) for g in bind().groups}
    r_org = {g.name: np.array(g.origin) for g in bind().groups}
    times = list(np.arange(0, length - 1e-6, step)) + [length]
    rot, pos, scl = ({b: [] for b in rest} for _ in range(3))
    prev = {b: None for b in rest}
    up = None
    for t in times:
        m = posed(fn(t, S), up)
        up = m.head_up
        moved = {g.name: np.array(g.origin) - r_org[g.name] for g in m.groups}
        for g in m.groups:
            d = pick(np.array(g.rotation, float), rest[g.name], prev[g.name])
            prev[g.name] = d
            tt = round(float(t), 3)
            rot[g.name].append((tt, tuple(round(float(v), 2) for v in d), "catmullrom"))
            parent = moved.get(g.parent.name, np.zeros(3)) if g.parent is not None else np.zeros(3)
            pos[g.name].append((tt, tuple(round(float(v), 3) for v in moved[g.name] - parent), "catmullrom"))
            s = getattr(g, "scale", None) or (1, 1, 1)
            scl[g.name].append((tt, tuple(round(float(v), 3) for v in s), "catmullrom"))
    if loop == "loop":                                   # the loop closes on its first key exactly
        for track in (rot, pos, scl):
            for b in rest:
                track[b][-1] = (track[b][-1][0], track[b][0][1], "catmullrom")
    bones = {}
    for b in rest:
        ch = {}
        if any(any(abs(v) > 0.05 for v in k[1]) for k in rot[b]):
            ch["rotation"] = rot[b]
        if any(any(abs(v) > 1e-3 for v in k[1]) for k in pos[b]):
            ch["position"] = pos[b]
        if any(any(abs(v - 1) > 1e-3 for v in k[1]) for k in scl[b]):
            ch["scale"] = scl[b]
        if ch:
            bones[b] = ch
    return bones


def jumps(bones):
    """The largest turn of any bone between two neighbouring keys (degrees): a smoothness check."""
    worst = (0.0, "", 0.0)
    for b, ch in bones.items():
        keys = ch.get("rotation", [])
        for (_, v0, _), (t1, v1, _) in zip(keys[:-1], keys[1:]):
            d = max(abs(v1[i] - v0[i]) for i in range(3))
            if d > worst[0]:
                worst = (d, b, t1)
    return worst


def preview_model():
    m = s3.rest_model()
    s4.zone_materials(m)
    m.cubes = [c for c in m.cubes if c.mat != "hitbox"]
    return m


def build_all():
    clip_set, report = {}, {}
    for name, (length, loop, _, _) in CLIPS.items():
        bones = tracks(name)
        clip_set[name] = (length, loop, bones)
        j = jumps(bones)
        report[name] = {"largest_step_deg": round(j[0], 1), "bone": j[1], "at": j[2]}
        print(name, report[name], flush=True)
    return clip_set, report


def main(argv):
    (OUT / "gifs").mkdir(parents=True, exist_ok=True)
    for old in (OUT / "gifs").glob("*.gif"):
        old.unlink()
    clip_set, report = build_all()
    t7.OVERRIDE = OVERRIDE
    model_id = s4.NAME
    rig = json.loads((S6 / f"{model_id}.bbmodel").read_text(encoding="utf-8"))
    rig["animations"] = t7.animations(model_id, clip_set)
    p = OUT / f"{model_id}.bbmodel"
    p.write_text(json.dumps(rig, separators=(",", ":")) + "\n", encoding="utf-8")
    for folder in (s3.SERVER_MODELS, s3.TEST_MODELS):
        if folder.is_dir():
            shutil.copyfile(p, folder / p.name)
    model = preview_model()
    floors = t7.floor_check(clip_set, model)
    summary = {k: {"length": CLIPS[k][0], "loop": CLIPS[k][1], "lowest_y": floors[k], **report[k]} for k in CLIPS}
    (OUT / "clips.json").write_text(json.dumps({"contact_seconds": CONTACT, "clips": summary}, indent=2) + "\n",
                                    encoding="utf-8")
    print(json.dumps(summary, indent=1))
    if "--no-gifs" not in argv:
        s2.translate(model, s2.group(model, "base"), (0, 0, -150))
        a7.frame.__defaults__ = (-34, 12, (560, 440), 1.0, 0.86, ())
        img = a7.previews(model, clip_set, "", {"yaw": -68, "pitch": 14, "scale": 0.78}, CONTACT,
                          "Drowned Elder: key frames (session 7); the GIFs show the motion")
        img.save(OUT / "keyframes.png")


if __name__ == "__main__":
    main(sys.argv[1:])
