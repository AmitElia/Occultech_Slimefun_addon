"""Dread Riders, session 7: animation (plan: docs/art/bosses/dread_riders/overhaul/plan.md).

Authored as motion, not a few poses blended in joint space:
- **Gaits from leg phases.** Each leg runs its own cycle (a stance that sweeps the hoof back along the floor, a swing
  that folds the knee or hock and reaches forward), offset per gait: the walk is four-beat (LH, LF, RH, RF a quarter
  apart); the gallop is the transverse gallop on the right lead (LH, RH, LF, RF, then a moment of suspension). The body
  is grounded on its lowest hoof every key, rocks nose-up on the push and nose-down on the landing, and the neck swings
  against it like a real horse's. The tail and the banner stream and flutter.
- **The rider rides the horse.** Rider and horse are two entities (two models), so every gait clip also moves the
  rider's root with the saddle (the seat's real path through the mount's pose: rise, fall and pitch). Attack clips
  animate the torso, arms and weapon only, never the rider's root, so they can layer over a gait (session 8 checks
  BetterModel layers them; if not, the gait's bob pauses for the attack).
- **Weight:** a crouch before the rear, an overshoot on landing, the lance swung back before the sweep, the bow held a
  beat at full draw; dense keys (12-20 per cycle, 0.05-0.08 s in the attacks), every angle continuous with the last.

Clips (same names on a pair's mount and rider; timed to DreadRiders.java, session 8 moves the attacks onto the contacts):
The Vanguard
  idle      3.0 s loop  breathing, a slow toss of the head, the tail swishing; the rider sways, the lance carried
  walk      1.4 s loop  a four-beat walk (the spawn's approach, moving slowly)
  gallop    0.72 s loop the gallop the fight rides at (0.3 blocks a tick); the banner streams
  charge    1.25 s once full stretch (the 25-tick charge, 2.5 strides) (0.8 blocks a tick): longer reach, lower neck, lance couched across the neck
  rear      1.0 s hold  the charge's 1 s warning: a crouch, the rear (front hooves pawing high, lance raised), the drop
                        forward into the charge at 1.0 s
  stunned   2.0 s once  a charge cut short: the nose goes down, the forelegs buckle, a shake of the head, it gathers
                        itself; the rider slumps and the lance trails, then he straightens
  sweep     0.8 s once  melee (rider only): the lance drawn back, swept round the front (contact 0.35 s), recovered
  throw     1.0 s once  the enraged spear throw (rider only): raised over the shoulder, hurled (contact 0.55 s)
  flinch    0.4 s once  the horse tosses its head, the rider recoils
  spawn     2.6 s once  the ritual arrival: the horse rears up out of a crouch and stamps down, the rider raises the lance
  death     2.6 s hold  the horse rears weakly and collapses onto its knees, the rider slumps forward, the lance falls
The Outrider
  idle      3.0 s loop  as above, the bow lowered
  walk      1.4 s loop  four-beat walk
  gallop    0.72 s loop circling at 0.34 blocks a tick, the rider leaning into it, the bow low
  halt      0.7 s hold  the rein-in every 10 s: a sliding stop, haunches down, forelegs braced
  draw      2.4 s once  the aimed snipe (the 40-tick beam): the forehoof paws, the bow raised, the arrow nocked, drawn to
                        the cheek (by 1.0 s), held, loosed at 2.0 s (contact), the hand flung back
  snipe     1.8 s once  the snipes loosed at the gallop (the 30-tick beam, rider only): loose at 1.5 s
  volley    0.6 s once  the three-arrow volley (rider only): a quick draw and loose (contact 0.35 s)
  rain      1.2 s once  the arrow rain (rider only): leaning back, aiming high, loosed at 0.45 s
  flinch, spawn, death  as above

Run from the repository root, after dread_s6.py, with the folder holding assets/ from the 26.2 client as the argument:
python tools/art/bosses/dread_s7.py <client folder> [clip ...] [--server] [--gifs]
"""
import copy
import json
import math
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import _uuid, pivot_matrix, rotation_matrix  # noqa: E402
from bosses import archevoker_s6 as a6, volley_crone_s4 as v4  # noqa: E402
from bosses.volley_crone_s7 import matrices  # noqa: E402
from bosses import dread_s2 as s2, dread_s3 as s3, dread_s4 as s4, dread_s6 as s6  # noqa: E402
from bosses.heartwood_s1 import _n  # noqa: E402

OUT = ROOT / "docs/art/bosses/dread_riders/overhaul/s7_animation"
REST = s2.REST
K = s3.SCALE


# ==== easing and blending ==============================================================================================

def clamp01(x):
    return max(0.0, min(1.0, x))


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def span(t, a, b):
    return clamp01((t - a) / (b - a))


def back_out(x, s=1.4):
    x = clamp01(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def lerp(a, b, w):
    return a + (b - a) * w


def blend(A, B, w):
    """Two pose specs mixed: numbers and tuples lerped, directions nlerped, legs and arms per side."""
    out = {}
    for k in set(A) | set(B):
        a, b = A.get(k), B.get(k)
        if a is None or b is None:
            out[k] = b if w >= 0.5 and b is not None else (a if a is not None else b)
        elif k in ("legs", "arms"):
            out[k] = {}
            for side in set(a) | set(b):
                if side in a and side in b:
                    v = lerp(np.array(a[side], float), np.array(b[side], float), w)
                    out[k][side] = tuple(tuple(r) for r in v) if v.ndim == 2 else tuple(v)
                else:
                    out[k][side] = b.get(side, a.get(side))
        elif k in ("lance",):
            out[k] = tuple(_n(lerp(_n(a), _n(b), w)))
        elif k == "bow":
            out[k] = (tuple(_n(lerp(_n(a[0]), _n(b[0]), w))), tuple(_n(lerp(_n(a[1]), _n(b[1]), w))))
        elif isinstance(a, bool):
            out[k] = b if w >= 0.5 else a
        elif isinstance(a, (tuple, list)):
            out[k] = tuple(lerp(np.array(a, float), np.array(b, float), w))
        else:
            out[k] = lerp(a, b, w)
    return out


def chain(*keys):
    """Piecewise blend through (time, spec, ease) keys."""
    def at(t):
        if t <= keys[0][0]:
            return keys[0][1]
        for (t0, a, _), (t1, b, ease) in zip(keys, keys[1:]):
            if t <= t1:
                return blend(a, b, ease(span(t, t0, t1)))
        return keys[-1][1]
    return at


# ==== the horse's gaits ================================================================================================

REST_LEGS = s2.dc.LEGS[REST]


def leg_angles(key, s, stance, reach, fold, lift=1.0):
    """World angles (upper, cannon, pastern; forward positive) of one leg at its own phase s (0 = hoof strikes)."""
    front = key[0] == "f"
    r = REST_LEGS[key]
    if s < stance:                                       # stance: the hoof sweeps back along the floor
        k = s / stance
        d = reach * (1 - 2 * k)
        heel = 30 * max(0.0, k - 0.7) / 0.3
        return (r[0] + d, r[1] + d * (1.0 if front else 0.9), r[2] + d - heel)
    k = (s - stance) / (1 - stance)                      # swing: fold, carry forward, reach
    d = -reach + 2 * reach * smooth(k)
    f = math.sin(math.pi * k) * lift
    if front:
        u = r[0] + d + 10 * f
        c = u - fold * f
        return (u, c, c - 0.45 * fold * f)
    g = r[0] + d - 0.32 * fold * f
    c = g + (r[1] - r[0]) + 0.62 * fold * f
    return (g, c, c + 0.2 * fold * f)


GAITS = {
    # order of footfalls (phase offsets), stance share, reach, fold, body rock, neck swing, phase of the rock
    "walk": dict(off={"hl": 0.0, "fl": 0.25, "hr": 0.5, "fr": 0.75}, stance=0.62, reach=17, fold=70, rock=1.5,
                 neck=4, cycles=2),
    "gallop": dict(off={"hl": 0.0, "hr": 0.12, "fl": 0.42, "fr": 0.54}, stance=0.34, reach=34, fold=105, rock=6,
                   neck=9, cycles=1),
    "charge": dict(off={"hl": 0.0, "hr": 0.1, "fl": 0.4, "fr": 0.5}, stance=0.3, reach=44, fold=118, rock=8,
                   neck=7, cycles=1),
}


def gait_spec(name, p, f, neck_base=None, head_base=None):
    G = GAITS[name]
    legs = {key: leg_angles(key, (p - o) % 1.0, G["stance"], G["reach"], G["fold"]) for key, o in G["off"].items()}
    w = 2 * math.pi * G["cycles"]
    rock = G["rock"] * math.sin(w * p + 0.6)
    neck_base = neck_base if neck_base is not None else {"walk": 34, "gallop": 46, "charge": 58}[name]
    head_base = head_base if head_base is not None else {"walk": -44, "gallop": -34, "charge": -24}[name]
    return {"legs": legs, "tilt": rock, "neck": neck_base + G["neck"] * math.sin(w * p - 1.2),
            "head": head_base + 0.6 * G["neck"] * math.sin(w * p - 0.6),
            "tail": (-48 if name != "walk" else -8) + 6 * math.sin(w * p * 2), "tail_yaw": 4 * math.sin(w * p),
            "banner": ((-62 if name == "charge" else -46) if name != "walk" else -10) + 8 * math.sin(w * p * 2 + 1),
            "lift": {"walk": 0, "gallop": 1.5, "charge": 2.5}[name] * max(0.0, math.sin(w * p - 2.2))}


def stand(neck=None, head=None, **kw):
    s = {"legs": {k: tuple(float(v) for v in REST_LEGS[k]) for k in REST_LEGS}, "tilt": 0.0, "neck": 30.0 if neck is None else neck,
         "head": -46.0 if head is None else head, "tail": -6.0, "tail_yaw": 0.0, "banner": 0.0, "lift": 0.0}
    s.update(kw)
    return s


# ==== posing the models ================================================================================================

def pose_mount(mm, f, spec):
    """Like dread_s2.pose_mount, with the extras animation needs (tail, banner, jaw, head yaw)."""
    B = s2.bones_of(mm)
    s2.reset(mm)
    tilt = spec.get("tilt", 0.0)
    B["base"].rotation = [float(tilt), 0.0, float(spec.get("roll", 0.0))]
    for key in s2.LEGS:
        r = REST_LEGS[key]
        p = [a - tilt for a in spec["legs"][key]]
        B[f"leg_{key}"].rotation = [p[0] - r[0], 0, 0]
        B[f"leg_{key}_lower"].rotation = [(p[1] - r[1]) - (p[0] - r[0]), 0, 0]
        B[f"leg_{key}_hoof"].rotation = [(p[2] - r[2]) - (p[1] - r[1]), 0, 0]
    n0, mid, poll = f["neck"]
    dn = spec["neck"] + tilt - s2.neck_ang(poll - n0)
    B["neck"].rotation = [-dn, float(spec.get("neck_yaw", 0.0)), 0]
    B["head"].rotation = [float(spec["head"]) - tilt + dn, float(spec.get("head_yaw", 0.0)), float(spec.get("head_roll", 0.0))]
    B["tail"].rotation = [float(spec.get("tail", 0.0)), float(spec.get("tail_yaw", 0.0)), 0]
    if "banner_cloth" in B:
        B["banner_cloth"].rotation = [float(spec.get("banner", 0.0)), 0, 0]
    if "jaw" in B:
        B["jaw"].rotation = [float(spec.get("jaw", 0.0)), 0, 0]
    lo = min(c.corners()[:, 1].min() for c in mm.cubes)
    return -lo + spec.get("lift", 0.0) - spec.get("sink", 0.0)


def seated_info(info, seat):
    """The rider's named points moved into the seat-origin model's space."""
    i = copy.deepcopy(info)
    i["hip"] = np.array(info["hip"]) - seat
    i["arms"] = {k: tuple(np.array(p) - seat for p in v) for k, v in info["arms"].items()}
    for name in ("string_upper", "string_lower"):
        if name in info:
            i[name] = (np.array(info[name][0]) - seat, info[name][1])
    return i


# ==== the clips ========================================================================================================

def vanguard_rider(name):
    return dict(s2.RIDER_POSES["vanguard"].get(name, {}))


R_REST_V = {"lean": 0.0, "twist": 0.0, "head": 0.0, "arms": {1: ((13, 10, -4), (12, 4, -12)), -1: ((-13, 10, -5), (-6, 6, -16))},
            "lance": (0.14, 0.78, -0.62)}
R_REST_O = {"lean": 0.0, "twist": 0.0, "head": 0.0, "arms": {-1: ((-11, 10, -2), (-11, 2, -9)), 1: ((11, 10, 1), (8, 3, -8))},
            "bow": ((0, 1, 0.12), (0, 0, -1)), "draw": False}


def rider_spec(base, **kw):
    s = copy.deepcopy(base)
    s.update(kw)
    return s


V_CHARGE = rider_spec(R_REST_V, lean=-16.0, arms={1: ((15, 13, 5), (12, 12, -5)), -1: ((-12, 12, -8), (-5, 9, -18))},
                      lance=(-0.12, 0.04, -1))
V_RAISED = rider_spec(R_REST_V, lean=8.0, arms={1: ((15, 16, 2), (13, 22, -6)), -1: ((-13, 10, -6), (-6, 8, -16))},
                      lance=(0.06, 1, 0.12))
V_REAR = rider_spec(V_RAISED, lean=-24.0, head=10.0)       # leans into the horse's neck against the rear, lance high
V_SLUMP = rider_spec(R_REST_V, lean=-24.0, head=-22.0,
                     arms={1: ((14, 8, -2), (14, -4, -6)), -1: ((-13, 9, -3), (-12, -2, -8))}, lance=(0.45, -0.3, -0.84))
O_GALLOP = rider_spec(R_REST_O, lean=-12.0, arms={-1: ((-11, 11, -5), (-10, 6, -14)), 1: ((11, 10, -2), (8, 6, -12))})
O_DRAW = rider_spec(R_REST_O, lean=-4.0, arms={-1: ((-10, 23, -10), (-8, 24, -21)), 1: ((16, 25, 8), (3, 27, -4))},
                    bow=((0.18, 1, 0), (0, 0, -1)), draw=True)
O_NOCK = rider_spec(R_REST_O, lean=-3.0, arms={-1: ((-10, 22, -10), (-8, 23, -21)), 1: ((18, 17, -4), (-4, 23, -16))},
                    bow=((0.18, 1, 0), (0, 0, -1)), draw=True)
O_LOOSE = rider_spec(R_REST_O, lean=-4.0, arms={-1: ((-10, 23, -10), (-8, 24, -21)), 1: ((16, 24, 7), (24, 24, 6))},
                     bow=((0.18, 1, 0), (0, 0, -1)), draw=False)
O_RAIN = rider_spec(R_REST_O, lean=10.0, head=24.0, arms={-1: ((-10, 29, -9), (-7, 37, -17)), 1: ((12, 28, 6), (3, 31, -3))},
                    bow=((0.1, 0.66, 0.75), (0, 0.75, -0.66)), draw=True)
O_RAIN_LOOSE = rider_spec(O_RAIN, draw=False, arms={-1: ((-10, 29, -9), (-7, 37, -17)), 1: ((16, 27, 8), (24, 28, 8))})

E, S, B = (lambda x: x), smooth, back_out


def make_clips(kind, f):
    neck0 = s2.neck_ang(f["neck"][2] - f["neck"][0])
    head0 = f["head_pitch"]
    idle_m = lambda t: stand(neck=neck0 + 2 * math.sin(2 * math.pi * t / 3.0), head=head0 + 4 * math.sin(2 * math.pi * t / 3.0 - 0.8),
                             head_yaw=6 * math.sin(2 * math.pi * t / 3.0 + 1.0), tail_yaw=10 * math.sin(2 * math.pi * t / 1.5),
                             banner=6 * math.sin(2 * math.pi * t / 1.5 + 0.5), jaw=3 + 3 * math.sin(2 * math.pi * t / 3.0),
                             tilt=0.8 * math.sin(2 * math.pi * t / 3.0))
    rest_r = R_REST_V if kind == "vanguard" else R_REST_O
    idle_r = lambda t: rider_spec(rest_r, lean=1.5 * math.sin(2 * math.pi * t / 3.0), head=-3 + 4 * math.sin(2 * math.pi * t / 3.0 - 1),
                                  twist=3 * math.sin(2 * math.pi * t / 3.0 + 1.0))
    gait = lambda name, L: (lambda t: gait_spec(name, (t / L) % 1.0, f))
    C = {}
    C["idle"] = (3.0, "loop", idle_m, idle_r, True)
    C["walk"] = (1.4, "loop", gait("walk", 1.4), lambda t: rider_spec(rest_r, lean=-2.0), True)
    C["gallop"] = (0.72, "loop", gait("gallop", 0.72),
                   (lambda t: rider_spec(rest_r, lean=-8.0)) if kind == "vanguard" else (lambda t: O_GALLOP), True)
    C["flinch"] = (0.4, "once", chain((0, stand(neck=neck0, head=head0), E), (0.12, stand(neck=neck0 - 10, head=head0 + 22, head_yaw=-8), B),
                                      (0.4, stand(neck=neck0, head=head0), S)),
                   chain((0, rest_r, E), (0.12, rider_spec(rest_r, lean=9.0, head=12.0), B), (0.4, rest_r, S)), True)
    crouch = stand(neck=neck0 - 6, head=head0 + 6, 
                   legs={"fl": (6, 4, 30), "fr": (6, 4, 30), "hl": (-44, 2, 24), "hr": (-44, 2, 24)}, tilt=-3.0)
    reared = dict(s2.MOUNT_POSES["rear"], tail=-30.0, tail_yaw=0.0, banner=-20.0, lift=0.0)
    reared = {**stand(), **reared, "head": -20.0, "neck": 8.0}
    paw_a = {**reared, "legs": {**reared["legs"], "fl": (95, -10, 0), "fr": (40, -95, -50)}}
    paw_b = {**reared, "legs": {**reared["legs"], "fl": (45, -95, -50), "fr": (90, -15, 0)}}
    landing = {**gait_spec("gallop", 0.42, f), "tilt": -6.0}
    spawn_m = chain((0, crouch, E), (0.5, crouch, S), (0.95, reared, B), (1.3, paw_a, S), (1.55, paw_b, S), (1.8, reared, S),
                    (2.15, {**landing, "lift": 0.0}, S), (2.6, stand(neck=neck0, head=head0), S))
    collapse = stand(neck=70, head=-80, tilt=-14.0, legs={"fl": (-20, -150, -170), "fr": (-10, -150, -170),
                                                          "hl": (-60, 10, 30), "hr": (-60, 10, 30)}, tail=-10.0, jaw=12.0)
    death_m = chain((0, stand(neck=neck0, head=head0), E), (0.5, {**reared, "tilt": 16.0}, S), (1.0, stand(neck=neck0, head=head0 + 10), S),
                    (1.6, collapse, S), (2.6, {**collapse, "neck": 82.0, "head": -95.0}, S))
    if kind == "vanguard":
        rider_death = chain((0, rest_r, E), (0.5, V_RAISED, S), (1.0, rest_r, S), (1.6, V_SLUMP, S),
                            (2.6, rider_spec(V_SLUMP, lean=-34.0, head=-30.0, lance=(0.7, -0.6, -0.4)), S))
        C["spawn"] = (2.6, "once", spawn_m, chain((0, rider_spec(rest_r, lean=-10.0), E), (0.9, V_RAISED, S), (1.8, V_RAISED, S),
                                                  (2.6, rest_r, S)), True)
        C["death"] = (2.6, "hold", death_m, rider_death, True)
        C["charge"] = (1.25, "once", gait("charge", 0.5), lambda t: V_CHARGE, True)   # the 25-tick charge
        C["rear"] = (1.0, "hold", chain((0, stand(neck=neck0, head=head0), E), (0.18, crouch, S), (0.45, reared, B),
                                        (0.62, paw_a, S), (0.78, paw_b, S), (1.0, landing, S)),
                     chain((0, rest_r, E), (0.18, rider_spec(rest_r, lean=-8.0), S), (0.45, V_REAR, B), (0.85, V_REAR, S),
                           (1.0, V_CHARGE, S)), True)
        buckled = stand(neck=78, head=-88, tilt=-10.0, legs={"fl": (30, -60, -40), "fr": (24, -70, -44),
                                                                       "hl": (-40, -6, 22), "hr": (-36, -2, 24)}, jaw=10.0)
        C["stunned"] = (2.0, "once", chain((0, landing, E), (0.25, buckled, B), (0.6, {**buckled, "head_yaw": 18.0}, S),
                                           (0.85, {**buckled, "head_yaw": -18.0}, S), (1.1, {**buckled, "head_yaw": 10.0}, S),
                                           (1.4, {**buckled, "neck": 55.0, "head": -60.0}, S),
                                           (2.0, stand(neck=neck0, head=head0), S)),
                        chain((0, V_CHARGE, E), (0.25, V_SLUMP, B), (1.4, V_SLUMP, S), (2.0, rest_r, S)), True)
        wind = rider_spec(rest_r, twist=24.0, arms={1: ((17, 18, 8), (18, 20, 2)), -1: ((-13, 10, -6), (-6, 8, -16))},
                          lance=(0.75, 0.45, 0.48))
        hit = rider_spec(rest_r, twist=-30.0, arms={1: ((17, 16, -6), (20, 14, -16)), -1: ((-13, 10, -6), (-6, 8, -16))},
                         lance=(0.55, 0.05, -0.83))
        follow = rider_spec(rest_r, twist=-40.0, lean=-6.0, arms={1: ((14, 15, -10), (6, 13, -18)), -1: ((-13, 10, -6), (-6, 8, -16))},
                            lance=(-0.55, 0.0, -0.84))
        C["sweep"] = (0.8, "once", None, chain((0, rest_r, E), (0.25, wind, S), (0.35, hit, E), (0.45, follow, S),
                                               (0.8, rest_r, S)), False)
        cocked = rider_spec(rest_r, lean=8.0, twist=-14.0, arms={1: ((17, 30, 8), (14, 38, 4)), -1: ((-12, 16, -10), (-8, 20, -20))},
                            lance=(0.04, 0.2, -1))
        hurl = rider_spec(rest_r, lean=-14.0, twist=6.0, arms={1: ((15, 26, -8), (12, 26, -18)), -1: ((-12, 12, -6), (-8, 8, -12))},
                          lance=(0.02, -0.05, -1))
        C["throw"] = (1.0, "once", None, chain((0, rest_r, E), (0.4, cocked, S), (0.46, cocked, E), (0.58, hurl, S),
                                               (1.0, rest_r, S)), False)
    else:
        rider_death = chain((0, rest_r, E), (0.5, rider_spec(rest_r, lean=10.0), S), (1.0, rest_r, S),
                            (1.6, rider_spec(rest_r, lean=-26.0, head=-20.0), S), (2.6, rider_spec(rest_r, lean=-36.0, head=-30.0,
                            arms={-1: ((-11, 8, -4), (-11, -6, -8)), 1: ((11, 8, -2), (11, -6, -6))}), S))
        C["spawn"] = (2.6, "once", spawn_m, chain((0, rider_spec(rest_r, lean=-10.0), E), (0.9, rider_spec(rest_r, lean=6.0), S),
                                                  (1.8, O_DRAW, S), (2.6, rest_r, S)), True)
        C["death"] = (2.6, "hold", death_m, rider_death, True)
        braced = stand(neck=neck0 - 8, head=head0 + 10, tilt=9.0,
                       legs={"fl": (22, 18, 40), "fr": (18, 14, 36), "hl": (-8, 20, 34), "hr": (-12, 18, 32)}, tail=-20.0)
        C["halt"] = (0.7, "hold", chain((0, {**gait_spec("gallop", 0.0, f)}, E), (0.35, braced, B), (0.7, stand(neck=neck0, head=head0), S)),
                     chain((0, O_GALLOP, E), (0.35, rider_spec(rest_r, lean=8.0), B), (0.7, rest_r, S)), True)
        paw_up = {**stand(neck=neck0, head=head0), "legs": {**stand()["legs"], "fl": tuple(s2.dc.LEGS["snipe"]["fl"])}}
        draw_m = chain((0, stand(neck=neck0, head=head0), E), (0.3, paw_up, S), (0.55, stand(neck=neck0, head=head0), S),
                       (0.85, paw_up, S), (1.1, stand(neck=neck0, head=head0), S), (2.0, stand(neck=neck0 + 4, head=head0 + 4), S),
                       (2.15, stand(neck=neck0 - 4, head=head0 + 10), B), (2.4, stand(neck=neck0, head=head0), S))
        tremble = lambda t: rider_spec(O_DRAW, head=1.5 * math.sin(t * 40))
        C["draw"] = (2.4, "once", draw_m, chain((0, rest_r, E), (0.6, O_NOCK, S), (1.0, O_DRAW, S), (1.5, tremble(1.5), S),
                                                (1.95, tremble(1.95), S), (2.075, O_LOOSE, B), (2.4, rest_r, S)), True)
        # the snipes loosed on the move (a 30-tick beam): nock, full draw by 0.75 s, loose at 1.5 s
        C["snipe"] = (1.8, "once", None, chain((0, O_GALLOP, E), (0.4, O_NOCK, S), (0.75, O_DRAW, S), (1.45, tremble(1.45), S),
                                               (1.575, O_LOOSE, B), (1.8, O_GALLOP, S)), False)
        C["volley"] = (0.6, "once", None, chain((0, rest_r, E), (0.15, O_NOCK, S), (0.3, O_DRAW, S), (0.4, O_LOOSE, B),
                                                (0.6, rest_r, S)), False)
        C["rain"] = (1.2, "once", None, chain((0, rest_r, E), (0.3, O_RAIN, S), (0.52, O_RAIN_LOOSE, B), (0.7, O_RAIN_LOOSE, S),
                                              (1.2, rest_r, S)), False)
    return C


# ==== tracks ===========================================================================================================

def wrap(a):
    return (a + 180) % 360 - 180


def pick(r_abs, rest, prev):
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


def step_for(length):
    return length / 24 if length < 1.0 else 0.025


def tracks(P, info, clip):
    """Per model: {bone: {channel: [(t, value, interp)]}}, values relative to the bind pose; positions in final (scaled)
    units."""
    length, loop, mfn, rfn, gait_bob = clip
    mm, rm, f = P["mount"], P["rider"], P["frame"]
    seat = np.array(P["seat"])
    mb = {g.name: np.array(g.rotation, float) for g in mm.groups}
    s2.pose_mount(mm, f, s2.MOUNT_POSES[REST])
    mb = {g.name: np.array(g.rotation, float) for g in mm.groups}
    s2.reset(rm)
    rb = {g.name: np.array(g.rotation, float) for g in rm.groups}
    times = [round(float(t), 4) for t in np.arange(0, length - 1e-6, step_for(length))] + [length]
    out = {"mount": {}, "rider": {}}
    prev = {"mount": {}, "rider": {}}
    arm_state = {}
    base_lift0 = pose_mount(mm, f, stand(neck=s2.neck_ang(f["neck"][2] - f["neck"][0]), head=f["head_pitch"]))
    for t in times:
        if mfn is not None:
            lift = pose_mount(mm, f, mfn(t))
            Mb = s2.bones_of(mm)["base"].world_matrix()
            for g in mm.groups:
                d = pick(np.array(g.rotation, float), mb[g.name], prev["mount"].get(g.name))
                prev["mount"][g.name] = d
                out["mount"].setdefault(g.name, {}).setdefault("rotation", []).append((t, tuple(round(float(v), 2) for v in d)))
            out["mount"].setdefault("base", {}).setdefault("position", []).append((t, (0.0, round(float(lift) * K, 3), 0.0)))
        spec = rfn(t)
        s2.pose_rider(rm, info, spec, arm_state)
        for g in rm.groups:
            d = pick(np.array(g.rotation, float), rb[g.name], prev["rider"].get(g.name))
            prev["rider"][g.name] = d
            out["rider"].setdefault(g.name, {}).setdefault("rotation", []).append((t, tuple(round(float(v), 2) for v in d)))
            sc = getattr(g, "scale", None)
            out["rider"][g.name].setdefault("scale", []).append((t, tuple(round(float(v), 3) for v in (sc or (1, 1, 1)))))
        if gait_bob and mfn is not None:
            # the saddle's path: the rider's root follows the seat through the mount's pose
            seat_now = (Mb @ np.array([*seat, 1.0]))[:3] + [0, lift, 0]
            d = (seat_now - seat - np.array([0, base_lift0, 0])) * K
            tilt = float(s2.bones_of(mm)["base"].rotation[0])
            rr = out["rider"]["rider"]
            rr["rotation"][-1] = (t, (round(tilt, 2), 0.0, 0.0))
            rr.setdefault("position", []).append((t, tuple(round(float(v), 3) for v in d)))
    s2.pose_mount(mm, f, s2.MOUNT_POSES[REST])
    s2.reset(rm)
    s2.hide_arrow(rm)
    clean = {}
    for part, bones in out.items():
        keep = {}
        for b, ch in bones.items():
            c2 = {}
            for name, keys in ch.items():
                ident = (1, 1, 1) if name == "scale" else (0, 0, 0)
                if any(any(abs(v - i) > (0.05 if name == "rotation" else 1e-3) for v, i in zip(k[1], ident)) for k in keys):
                    if loop == "loop":
                        keys = keys[:-1] + [(keys[-1][0], keys[0][1])]
                    c2[name] = [(t, v, "catmullrom") for t, v in keys]
            if c2:
                keep[b] = c2
        clean[part] = keep
    return clean


def animations(model_id, clips, part):
    anims = []
    for name, (length, loop, tr) in clips.items():
        bones = tr[part]
        if not bones:
            continue
        animators = {}
        for bone, channels in bones.items():
            frames = []
            for ch, keys in channels.items():
                for t, v, interp in keys:
                    if ch == "rotation":
                        point = {"x": round(-v[0], 2), "y": round(-v[1], 2), "z": round(v[2], 2)}
                    elif ch == "position":
                        point = {"x": round(-v[0], 3), "y": round(v[1], 3), "z": round(v[2], 3)}
                    else:
                        point = {"x": v[0], "y": v[1], "z": v[2]}
                    frames.append({"channel": ch, "data_points": [point], "time": round(t, 4), "color": -1,
                                   "interpolation": interp, "uuid": _uuid(f"{model_id}/{name}/{bone}/{ch}/{t}")})
            animators[_uuid(f"{model_id}/group/{bone}")] = {"name": bone, "type": "bone", "keyframes": frames}
        anims.append({"uuid": _uuid(f"{model_id}/anim/{name}"), "name": name, "loop": loop, "override": False,
                      "length": length, "snapping": 40, "selected": False, "anim_time_update": "", "blend_weight": "",
                      "start_delay": "", "loop_delay": "", "animators": animators})
    return anims


# ==== checks ===========================================================================================================

def as_tracks(bones):
    """Our tracks in the sampler's format (rotation deltas in degrees as the bones' own rotation offsets)."""
    return {b: {ch: [(t, v, i) for t, v, i in keys] for ch, keys in chs.items()} for b, chs in bones.items()}


def floor_check(model, bones, length, dt=0.05):
    low = 1e9
    for t in np.arange(0, length + 1e-6, dt):
        mats = matrices(model, as_tracks(bones), float(t))
        for c in model.cubes:
            m = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
            lo, hi = np.array(c.frm), np.array(c.to)
            pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
            low = min(low, float((m @ pts)[1].min()))
    return round(low / 16, 2)


def true_jump(bones, model):
    """The largest real turn of any bone between neighbouring keys (degrees), from the rotation matrices."""
    rest = {g.name: np.array(g.rotation, float) for g in model.groups}
    worst = (0.0, "", 0.0)
    for b, ch in bones.items():
        ks = ch.get("rotation", [])
        for (_, v0, _), (t1, v1, _) in zip(ks[:-1], ks[1:]):
            R0, R1 = rotation_matrix(rest[b] + np.array(v0)), rotation_matrix(rest[b] + np.array(v1))
            a = math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(R0.T @ R1) - 1) / 2))))
            if a > worst[0]:
                worst = (a, b, t1)
    return [round(worst[0], 1), worst[1], worst[2]]


def jumps(bones):
    worst = (0.0, "", 0.0)
    for b, ch in bones.items():
        keys = ch.get("rotation", [])
        for (_, v0, _), (t1, v1, _) in zip(keys[:-1], keys[1:]):
            d = max(abs(v1[i] - v0[i]) for i in range(3))
            if d > worst[0]:
                worst = (d, b, t1)
    return [round(worst[0], 1), worst[1], worst[2]]


# ==== lit GIFs =========================================================================================================

FPS = 12


def tint_at(kind, clip, t):
    st = s6.STATES[kind]
    calm = st["calm"]
    hot = st["tell"] if kind == "vanguard" else st["lock"]
    mix = lambda a, b, k: tuple(a[i] + (b[i] - a[i]) * k for i in range(3))
    if clip in ("rear", "charge"):
        return mix(calm, hot, smooth(span(t, 0.1, 0.5))) if clip == "rear" else hot
    if clip == "stunned":
        return mix(st["stunned"], calm, smooth(span(t, 1.4, 2.0)))
    if clip == "draw":
        return mix(calm, hot, smooth(span(t, 0.8, 1.1))) if t < 2.0 else mix(hot, calm, smooth(span(t, 2.0, 2.3)))
    if clip == "death":
        return mix(calm, st["dead"], smooth(span(t, 1.0, 2.2)))
    if clip == "spawn":
        return mix(st["dead"], calm, smooth(span(t, 0.4, 1.4)))
    return calm


def gif(kind, clip_name, length, tr, P, bbs, atlases, masks, view):
    mm, rm = P["mount"], P["rider"]
    seat = np.array(P["seat"])
    tag = f"{kind}_{clip_name}"
    tmp = OUT / "lit" / "_tmp" / tag
    times = [float(t) for t in np.arange(0, length + 1e-6, 1 / FPS)]
    wm = atlases[0].shape[1]

    def frame(it):
        i, t = it
        boxes = []
        for model, bb, dx, shift, part in ((mm, bbs[0], 0, np.zeros(3), "mount"), (rm, bbs[1], wm, seat, "rider")):
            mats = matrices(model, as_tracks(tr[part]), t)
            for j, c in enumerate(model.cubes):
                hidden = any(not g.visible for g in s2.subtree_up(c.group))
                if hidden and not (clip_name in ("draw", "volley", "rain") and c.group.name in ("arrow", "glow_arrow")):
                    continue
                M = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
                lo, hi = np.array(c.frm), np.array(c.to)
                pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
                world = (M @ pts)[:3].T + shift
                if world[:, 1].max() < -0.5:
                    continue
                faces = {}
                for fn, d in bb["elements"][j]["faces"].items():
                    u = list(d["uv"])
                    if d.get("texture") is not None:
                        u = [u[0] + dx, u[1], u[2] + dx, u[3]]
                    faces[fn] = dict(d, uv=u)
                boxes.append({"corners": world.tolist(), "from": c.frm, "to": c.to, "glow": c.mat in s4.GLOWING, "uv": faces})
        colour = tint_at(kind, clip_name, t)
        imgs = [a6.tinted(a, m, colour) for a, m in zip(atlases, masks)]
        combo = np.zeros((max(a.shape[0] for a in imgs), wm + imgs[1].shape[1], 4))
        combo[:imgs[0].shape[0], :wm] = imgs[0]
        combo[:imgs[1].shape[0], wm:] = imgs[1]
        tex = a6.save(combo, tmp / f"atlas_{i:03d}.png")
        out = tmp / f"f{i:03d}"
        out.mkdir(parents=True, exist_ok=True)
        job = out / "job.json"
        job.write_text(json.dumps({"texture": str(tex), "out": out.as_posix(), "boxes": boxes,
                                   "views": [dict(view, name="frame", player=False, res=(640, 500))]}), encoding="utf-8")
        r = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                            str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job)],
                           capture_output=True, text=True)
        if r.returncode or "TEXTURED_RENDER_DONE" not in r.stdout:
            raise SystemExit(r.stdout[-2000:] + r.stderr[-2000:])
        return out / "frame.png"

    with ThreadPoolExecutor(max_workers=6) as pool:
        paths = list(pool.map(frame, enumerate(times)))
    frames = [Image.open(p).convert("RGB") for p in paths]
    pal = [fr.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for fr in frames]
    path = OUT / "lit" / f"{tag}.gif"
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=int(1000 / FPS), loop=0, disposal=2)
    for p in tmp.rglob("*"):
        if p.is_file():
            p.unlink()
    return path


VIEW = {"location": (10, 9, 4.5), "target": (0, 0, 2.6), "scale": 10.5}
SIDE = {"location": (16, 0, 3.0), "target": (0, 0, 2.6), "scale": 10.5}


# ==== main =============================================================================================================

def main(argv):
    client = argv[0]
    wanted = [a for a in argv[1:] if not a.startswith("--")]
    s6_dir = s6.OUT
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for kind in ("vanguard", "outrider"):
        P = s3.build_pair(kind)
        info = seated_info(P["info"], np.array(P["seat"]))
        clips = make_clips(kind, P["frame"])
        if wanted:
            clips = {k: v for k, v in clips.items() if k in wanted}
        built = {}
        for name, clip in clips.items():
            tr = tracks(P, info, clip)
            built[name] = (clip[0], clip[1], tr)
            report[f"{kind}/{name}"] = {"largest_euler_step": {p: jumps(tr[p]) for p in tr},
                                        "largest_true_step": {p: true_jump(tr[p], P["mount" if p == "mount" else "rider"]) for p in tr}}
        # floor and size checks run on the final (scaled) models
        s3.scale_model(P["mount"])
        s3.scale_model(P["rider"])
        for name, (length, loop, tr) in built.items():
            if tr["mount"]:
                report[f"{kind}/{name}"]["mount_lowest_blocks"] = floor_check(P["mount"], tr["mount"], length)
        paths = {}
        for part, model_id in (("mount", f"occultech_dread_{kind}_mount_rig"), ("rider", f"occultech_dread_{kind}_rig")):
            rig = json.loads((s6_dir / f"{model_id}.bbmodel").read_text(encoding="utf-8"))
            rig["animations"] = animations(model_id, built, part)
            p = OUT / f"{model_id}.bbmodel"
            p.write_text(json.dumps(rig, separators=(",", ":")) + "\n", encoding="utf-8")
            paths[part] = p
            if "--server" in argv and s3.SERVER_MODELS.is_dir():
                shutil.copyfile(p, s3.SERVER_MODELS / p.name)
        if "--gifs" in argv:
            P["seat"] = np.array(P["seat"]) * K
            bbs = [json.loads(paths[p].read_text(encoding="utf-8")) for p in ("mount", "rider")]
            atlases, masks = [], []
            for model_id, model in ((f"occultech_dread_{kind}_mount_rig", P["mount"]), (f"occultech_dread_{kind}_rig", P["rider"])):
                a = np.array(Image.open(s6_dir / f"{model_id}.png")).astype(float)
                atlases.append(a)
                masks.append(glow_mask_from_bb(json.loads((s6_dir / f"{model_id}.bbmodel").read_text(encoding="utf-8")), model, a.shape[:2]))
            for name, (length, loop, tr) in built.items():
                view = SIDE if name in ("gallop", "charge", "walk", "rear", "halt", "stunned") else VIEW
                print("gif", gif(kind, name, length, tr, P, bbs, atlases, masks, view), flush=True)
    (OUT / "report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))


def glow_mask_from_bb(bb, model, shape):
    mask = np.zeros(shape, bool)
    for e, c in zip(bb["elements"], model.cubes):
        if c.mat in s6.GLOW_MATS:
            for d in e["faces"].values():
                if d.get("texture") is not None:
                    x0, y0, x1, y1 = (int(round(v)) for v in d["uv"])
                    mask[min(y0, y1):max(y0, y1), min(x0, x1):max(x0, x1)] = True
    return mask


if __name__ == "__main__":
    main(sys.argv[1:])
