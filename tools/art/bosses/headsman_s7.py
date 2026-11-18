"""The Hollow Warlord (the Headsman), session 7: animation (plan: docs/art/bosses/hollow_warlord/overhaul/plan.md).

Authored as motion, not as a few poses blended in joint space:
- **Pose parameters, not joint angles.** A frame is a pose spec: the torso's lean and twist, the head, where each
  ankle and each hand is, where the sword's grip is and where it points, where each taken skull floats. Specs blend
  (and are animated) in that space, and every frame is solved by two-bone IK at fixed bone lengths, so the feet stay
  planted, the hands stay on the grip and nothing folds through itself in between.
- **The pauldrons ride the arms:** each turns with its upper arm (60% of the arm's swing, at most 60 degrees), so a
  raised arm lifts its shoulder plate.
- **Edge first:** every cut travels in the blade's own plane (the sweep with the flat level, the chop with the flat
  upright), and `edge_report` checks it: at speed the blade's flat must never lead.
- **Paths, not blends,** wherever a blend would cut through him: the sweep's arc, the chop over the top, the sword
  carried round his right side (`carry`), shouldered over the top in the enrage.
- **Weight:** slow anticipation and a held beat before each blow, the body sinking into every impact and every
  footfall, the head held on the target while the body turns under it; the hits barely move him.
- **Dense keys** (0.025-0.1 s), each joint angle kept continuous with the key before it.

Clips, timed to HollowWarlord.java (session 8 moves the attacks onto these contacts):
  idle           4.0 s loop   tall over his prey, the sword hanging behind him with its end on the floor; deep slow
                              breaths, a slow turn of the head
  walk           1.6 s loop   a stalking stride that sinks into every footfall, the sword dragged behind him
  windup         1.0 s hold   the soul sweep's 1 s warning: the blade lifted off the floor and drawn far back, the
                              body coiled and trembling, the eyes on you
  sweep          1.8 s once   the whirl round the front to his left (contact 0.3 s), a held follow-through, the
                              blade swung back round one-handed and let fall behind him
  attack         1.5 s once   melee: the sword raised high over his head, a held beat, the chop down in front
                              (contact 0.72 s), the blade wrenched up and let swing back behind him
  call           2.2 s once   the warband answers: the sword driven into the floor, his fist raised, the skulls
                              flaring up (contact 0.9 s: the guards appear)
  enrage         2.4 s once   below 35%: he buckles, raises the sword point-down high in both hands and drives it
                              into the floor (contact 1.05 s), roars with the skulls whirling round him, wrenches it
                              out and levels its point at you
  idle_enraged   4.8 s loop   lower and wider, a low two-handed guard with the point at you, breathing hard; the skulls circle his head
  flinch         0.5 s once   hit: a short recoil, then the head drops back onto you
  spawn          3.4 s once   from a kneel over the planted sword, the skulls rising from the floor, he stands,
                              wrenches the sword out and lets it hang behind him
  death          3.2 s hold   staggers, swings the sword round to plant it and drops to one knee; the skulls fall

Run from the repository root, after headsman_s6.py, with the folder holding assets/ from the 26.2 client as the last
argument: python tools/art/bosses/headsman_s7.py <folder>
"""
import copy
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses import headsman_s2 as s2, headsman_s3 as s3, headsman_s4 as s4, headsman_study as st  # noqa: E402
from bosses.headsman_silhouettes import _n  # noqa: E402

OUT = ROOT / "docs/art/bosses/hollow_warlord/overhaul/s7_animation"
S6 = ROOT / "docs/art/bosses/hollow_warlord/overhaul/s6_variants"
CONTACT = {"windup": 1.0, "sweep": 0.3, "attack": 0.72, "call": 0.9, "enrage": 1.05, "spawn": 3.0}
OVERRIDE = ("windup", "sweep", "attack", "call", "enrage", "flinch", "spawn", "death")
TAU = 2 * math.pi
A = s2.A                      # an ankle's height above the floor


# ---- easing -------------------------------------------------------------------------------------------------------------

def clamp01(x):
    return max(0.0, min(1.0, x))


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_in(x, p=2.4):
    return clamp01(x) ** p


def ease_out(x, p=2.4):
    return 1 - (1 - clamp01(x)) ** p


def back_out(x, s=1.7):
    x = clamp01(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def soft_back(x, s=1.2):
    """Out of a standstill (no jolt at the start), past the mark and back."""
    return back_out(smooth(x), s)


def span(t, t0, t1):
    return clamp01((t - t0) / (t1 - t0))


# ---- pose specs ---------------------------------------------------------------------------------------------------------

DEFAULT_HAND_L = (-27, 27, -6)


def base(name):
    """Session 2's key pose as a full spec (every field present, so specs blend)."""
    p = copy.deepcopy(s2.POSES[name][1])
    F = {"lean": p["lean"], "twist": p["twist"], "head": [p["head"][0], p["head"][1], 0.0], "drop": p["drop"],
         "sink": 0.0, "hip_yaw": 0.0,
         "legs": {k: [list(v[0]), list(v[1]), list(v[2])] for k, v in p["legs"].items()},
         "grip": list(p["sword"][0]), "tip": list(_n(p["sword"][1])), "normal": list(_n(p["sword"][2])),
         "elbow_r": list(p["elbow_r"]), "elbow_l": list(p["elbow_l"]),
         "hand_l": list(p.get("hand_l") or DEFAULT_HAND_L), "lg": 1.0 if p.get("left") == "grip" else 0.0,
         "tabard": [0.0, 0.0], "halo": 1.0, "lift": 0.0, "spread": 1.0, "orbit": 0.0, "bob": 0.0, "fall": 0.0}
    return F


def lerp(a, b, w):
    if isinstance(a, dict):
        return {k: lerp(a[k], b[k], w) for k in a}
    if isinstance(a, (list, tuple)):
        return [lerp(x, y, w) for x, y in zip(a, b)]
    return a + (b - a) * w


def mix(*pairs):
    """mix((F0, _), (F1, w1), ...): starts from F0, then blends towards each next spec by its weight in turn."""
    F = copy.deepcopy(pairs[0][0])
    for G, w in pairs[1:]:
        F = lerp(F, G, w)
    return F


def add(F, **kw):
    """Small additions (breaths, sways): numbers add, lists add element-wise."""
    F = copy.deepcopy(F)
    for k, v in kw.items():
        if isinstance(v, (list, tuple)):
            F[k] = [F[k][i] + v[i] for i in range(len(v))]
        else:
            F[k] = F[k] + v
    return F


def put(F, **kw):
    F = copy.deepcopy(F)
    for k, v in kw.items():
        F[k] = copy.deepcopy(v)
    return F


# ---- solving a spec on the rig ------------------------------------------------------------------------------------------

_BIND = None
HALO_FLOOR = {"c": ((4, 8.4, 26), (-80, 20, 0)), "l": ((-30, 8.4, -6), (-80, -50, 0)), "r": ((32, 8.4, 8), (-80, 35, 0))}
# fallen skulls lie tipped onto the backs of their heads, the severed vertebra along the floor behind them
PHASE = {"c": 0.0, "l": 2.1, "r": 4.2}
FOLLOW, FOLLOW_MAX = 0.45, 40.0      # how much of the upper arm's swing its pauldron takes, and at most (degrees)


def bind():
    global _BIND
    if _BIND is None:
        _BIND = s3.rest_model()
    return _BIND


PREV = {}            # each limb's world orientation in the previous frame (tracks() resets it per clip)


UNWIND_HALF = 0.5   # seconds for a limb to unwind half the twist it carried in (while it points anywhere but up)
STEP = [0.05]        # the key step of the clip being solved (tracks() sets it)


def point(g, d):
    """Aims a limb bone down its length along d, turning from where it pointed last frame (so its twist never flips
    when the limb swings past straight up). Whenever the limb points anywhere but up, the twist it carried in eases
    back to the plain one, so every clip comes to rest the way the idle stands."""
    down = np.array([0, -1.0, 0])
    R0 = PREV.get(g.name)
    Rc = s2.turn_to(down, d)
    if R0 is None:
        R = Rc
    else:
        R = s2.turn_to(R0 @ down, d) @ R0
        if float(_n(d) @ down) > -0.5:
            M = Rc.T @ R                                # a turn about the bone's own length
            phi = math.atan2(M[0, 2], M[0, 0]) * 0.5 ** (STEP[0] / UNWIND_HALF)
            R = Rc @ np.array([[math.cos(phi), 0, math.sin(phi)], [0, 1, 0], [-math.sin(phi), 0, math.cos(phi)]])
    PREV[g.name] = R
    s2.aim(g, R)


def ik(key, root_pt, target, hint, l1, l2):
    """Two-bone IK whose bend direction is kept close to last frame's: a hint passing through the limb's line can't
    flip the elbow or knee to the other side between two keys."""
    root_pt, target, hint = (np.array(v, float) for v in (root_pt, target, hint))
    d = target - root_pt
    dist = min(np.linalg.norm(d), l1 + l2 - 0.05)
    u = _n(d)
    a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    p = hint - root_pt
    p = p - u * (p @ u)
    p = _n(p) if np.linalg.norm(p) > 1e-6 else _n(np.cross(u, (1, 0, 0)))
    prev = PREV.get("bend_" + key)
    if prev is not None:
        q = prev - u * (prev @ u)
        if np.linalg.norm(q) > 1e-6:
            p = _n(_n(q) * 0.65 + p * 0.35)
    PREV["bend_" + key] = p
    return root_pt + u * a + p * h, root_pt + u * dist


def axis_angle(axis, deg):
    x, y, z = _n(axis)
    K = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    r = math.radians(deg)
    return np.eye(3) + math.sin(r) * K + (1 - math.cos(r)) * K @ K


def follow_pauldron(m, torso, side, upper):
    """The shoulder plate turns with its upper arm (a share of the arm's swing away from hanging, no twist)."""
    TR = torso.world_matrix()[:3, :3]
    d = _n(TR.T @ np.asarray(upper, float))
    d0 = np.array([0.0, -1.0, 0.0])
    ang = math.degrees(math.acos(max(-1.0, min(1.0, float(d0 @ d)))))
    axis = np.cross(d0, d)                              # horizontal; it wavers when the arm points near straight up
    prev = PREV.get("pauldron_axis_" + side)
    if prev is not None:
        axis = axis + prev * 0.35                       # so last frame's axis steadies it
    R = np.eye(3)
    if np.linalg.norm(axis) > 1e-6:
        PREV["pauldron_axis_" + side] = _n(axis)
        R = axis_angle(axis, min(ang * FOLLOW, FOLLOW_MAX))
    s2.aim(s2.group(m, f"pauldron_{side}"), TR @ R)


def place_arm(m, torso, side, wrist_target, hint):
    arm, fore = s2.group(m, f"arm_{side}"), s2.group(m, f"forearm_{side}")
    sh = s2.wpos(torso, arm.origin)
    el, wr = ik("arm_" + side, sh, wrist_target, hint, *s2.ARM)
    point(arm, el - sh)
    point(fore, wr - el)
    follow_pauldron(m, torso, side, el - sh)


def apply(F, t=0.0):
    m = copy.deepcopy(bind())
    G = s2.group
    hips, torso = G(m, "hips"), G(m, "torso")
    reach = sum(s2.LEG) - 0.4
    drop = F["drop"]
    for side, (ankle, _, _) in F["legs"].items():
        s = 1 if side == "right" else -1
        h = math.hypot(ankle[0] - s * s2.HIP_X, ankle[2])
        drop = max(drop, s2.HIP - (ankle[1] + math.sqrt(max(0.0, reach * reach - h * h))))
    drop += F["sink"]                                   # sinking into an impact: on top of what the legs need
    if drop:
        s2.translate(hips, (0, -drop, 0))
    hips.rotation = [0, F["hip_yaw"], 0]               # the hips turn on the planted feet (the legs follow by IK)
    torso.rotation = [-F["lean"], F["twist"], 0]
    G(m, "hi_head").rotation = list(F["head"])
    for side, (ankle, hint, toe) in F["legs"].items():
        hip = s2.wpos(hips, G(m, f"leg_{side}").origin)
        knee, ank = ik("leg_" + side, hip, ankle, hint, *s2.LEG)
        point(G(m, f"leg_{side}"), knee - hip)
        point(G(m, f"shin_{side}"), ank - knee)
        s2.aim(G(m, f"foot_{side}"), s2.turn_to((0, 0, -1), _n(toe)))
    grip, a = np.array(F["grip"], float), _n(F["tip"])
    R = s2.sword_frame(a, F["normal"]) @ s2.sword_frame(*s2.SWORD_REST).T
    d = _n(grip - np.array(F["elbow_r"], float))
    place_arm(m, torso, "right", grip - d * 3.5, F["elbow_r"])
    sw = G(m, "sword")
    s2.aim(sw, R)
    off = grip - s2.wpos(sw.parent, sw.origin)
    if np.linalg.norm(off) > 0.3:
        s2.translate(sw, np.linalg.inv(sw.parent.world_matrix()[:3, :3]) @ off)
    target = np.array(F["hand_l"], float) * (1 - F["lg"]) + (grip - a * 6) * F["lg"]
    d = _n(target - np.array(F["elbow_l"], float))
    place_arm(m, torso, "left", target - d * 3.5, F["elbow_l"])
    G(m, "tabard_front").rotation = [F["tabard"][0], 0, 0]
    G(m, "tabard_back").rotation = [F["tabard"][1], 0, 0]
    # the taken skulls: their halo round the head (not its lean), bobbing on their own phases, spread and circling
    # (their places only: each keeps facing the front, so no turn ever winds up); or fallen to the floor
    head_c = next(c for c in m.cubes if c.name == "skull").corners().mean(0)
    ang = math.radians(F["twist"] + F["orbit"])
    for k, (off3, yaw, roll) in s2.SKULLS.items():
        g = G(m, f"skull_{k}")
        ph = PHASE[k]
        P = F.get("bob_period", 3.2)                    # a loop's length, so the drift closes on itself
        bob = F["bob"] * np.array([math.sin(TAU * t / P + ph) * 1.2, math.sin(2 * TAU * t / P + ph) * 1.6,
                                   math.cos(TAU * t / P + ph) * 1.0])
        ox, oz = off3[0] * F["spread"], off3[2] * F["spread"]
        x, z = ox * math.cos(ang) + oz * math.sin(ang), -ox * math.sin(ang) + oz * math.cos(ang)
        halo_p = head_c + [x, off3[1] + F["lift"], z] + bob
        sway = F["bob"] * 6 * math.sin(TAU * t / P + ph + 1)
        halo_r = np.array([sway * 0.5, yaw + F["twist"] + sway, roll])
        fp, fr = HALO_FLOOR[k]
        fk = F["fall"] if not isinstance(F["fall"], dict) else F["fall"][k]
        p = halo_p * (1 - fk) + np.array(fp, float) * fk
        if 0 < fk < 1:
            p[1] += 10 * math.sin(math.pi * fk) * (1 if F.get("rise") else 0)
        g.rotation = list(halo_r * (1 - fk) + np.array(fr, float) * fk)
        s2.translate(g, p - np.array(g.origin))
    m.left_hand = target
    return m


# ---- sword paths --------------------------------------------------------------------------------------------------------

BLADE = 64.3                                            # the grip to the blade's squared end


def trail(grip, flat=(0.22, 0, 1), floor=1.5):
    """The blade hanging from the grip back behind him with its end resting on the floor."""
    grip = np.array(grip, float)
    k = max(-1.0, min(1.0, (floor - grip[1]) / BLADE))
    return list(_n(_n(flat) * math.sqrt(1 - k * k) + np.array([0, k, 0])))


def bezier(a, via, b, w):
    a, via, b = (np.array(v, float) for v in (a, via, b))
    return list((1 - w) ** 2 * a + 2 * w * (1 - w) * via + w * w * b)


def carry(F0, F1, w, via=None, legs_w=None):
    """F0 -> F1 at weight w; the grip on a curve through `via` (round his body, not through it). Feet blend by
    legs_w (an overshooting w must not slide them)."""
    F = mix((F0, 1), (F1, w))
    if via is not None:
        F["grip"] = bezier(F0["grip"], via, F1["grip"], w)
    if legs_w is not None:
        F["legs"] = lerp(F0["legs"], F1["legs"], legs_w)
    return F


def lift_foot(F, side, s, h=5.0):
    """Raises a foot while it moves to its new place (s runs 0..1 over the step)."""
    F = copy.deepcopy(F)
    F["legs"][side][0][1] += h * math.sin(math.pi * clamp01(s))
    return F


def side_angle(v):
    """The angle of a direction in his side (y-z) plane: 0 = straight back, 90 = up, 180 = straight ahead."""
    return math.degrees(math.atan2(v[1], v[2]))


def swing_tip(tip0, tip1, s, turn):
    """The tip turned through `turn` degrees in the side plane from tip0 (positive: back -> up -> ahead), its sideways
    lean blended to tip1's."""
    th = math.radians(side_angle(tip0) + turn * s)
    x = tip0[0] * (1 - s) + tip1[0] * s
    h = math.sqrt(max(0.0, 1 - x * x))
    return list(_n([x, h * math.sin(th), h * math.cos(th)]))


def turn_between(tip0, tip1, positive=True):
    d = side_angle(tip1) - side_angle(tip0)
    while positive and d <= 0:
        d += 360
    while not positive and d >= 0:
        d -= 360
    return d


# ---- the clips ----------------------------------------------------------------------------------------------------------

def _idle():
    F = base("idle")
    F.update(lean=12.0, head=[6.0, 0.0, 0.0], drop=0.0, bob=1.0)
    F["legs"] = {"right": [[13, A, 1], [12, 18, -7], [0.2, 0, -1]], "left": [[-13, A, -4], [-12, 18, -11], [-0.2, 0, -1]]}
    F["grip"] = [21.0, 31.0, 7.0]
    F["tip"] = trail(F["grip"])
    F["normal"] = list(_n([1, 0, -0.22]))              # the flat to the side: it rests on its edge
    F["elbow_r"] = [29.0, 48.0, 6.0]
    F["hand_l"], F["elbow_l"], F["lg"] = [-25.0, 30.0, -5.0], [-30.0, 48.0, 2.0], 0.0
    return F


IDLE = _idle()
WALK = put(base("walk"), lean=20.0, head=[12.0, 0.0, 0.0], bob=1.0, normal=IDLE["normal"])
WINDUP_LEGS = {"right": [[18, A, 10], [14, 16, 2], [0.3, 0, -1]], "left": [[-18, A, -8], [-14, 16, -12], [-0.2, 0, -1]]}
SWEEP = put(base("sweep"), legs=WINDUP_LEGS, bob=1.0)
ENRAGED = put(base("enraged"), grip=[4.0, 44.0, -34.0], tip=list(_n([0.08, -0.5, -1])), normal=[1.0, 0.0, 0.0],
              lg=1.0, elbow_r=[26.0, 52.0, -24.0], elbow_l=[-24.0, 52.0, -26.0], twist=0.0,
              head=[8.0, 0.0, 0.0], lift=4.0, spread=1.15, bob=1.0)      # a low guard, the point levelled at you
DEATH = base("death")
WIDE = {"right": [[16, A, 2], [15, 18, -6], [0.25, 0, -1]], "left": [[-16, A, -6], [-15, 18, -14], [-0.25, 0, -1]]}


def breathe(F, t, period, depth=1.0):
    b = math.sin(TAU * t / period)
    return add(F, lean=0.9 * b * depth, head=[-0.6 * b * depth, 0, 0], drop=-0.5 * b * depth,
               tabard=[1.5 * math.sin(TAU * t / period - 0.8), -1.5 * math.sin(TAU * t / period - 0.8)])


def idle(t, L=4.0):
    F = breathe(IDLE, t, L, 1.5)
    s = math.sin(TAU * t / L - 0.6)
    F["head"][1] += 12 * math.copysign(abs(s) ** 0.7, s)     # a slow turn that lingers at either side
    F["grip"][1] += 0.8 * math.sin(TAU * t / L)                # the shoulders heave: the blade's end stays down
    F["tip"] = trail(F["grip"])
    F["bob_period"] = L
    return F


def walk(t, L=1.6):
    """In place (the server moves him): stance pushes back flat on the floor, the swing lifts and reaches forward; the
    body sinks into each footfall and the head stays on the target."""
    F = copy.deepcopy(WALK)
    F["bob_period"] = L
    p = (t / L) % 1.0
    for side, off in (("right", 0.0), ("left", 0.5)):
        q = (p + off) % 1.0
        sg = 1 if side == "right" else -1
        if q < 0.6:                                     # stance: the foot slides back under him
            z, y = 12 - 24 * (q / 0.6), A
            toe = [0.15 * sg, 0, -1]
        else:                                           # swing: lifted and carried forward
            s = smooth((q - 0.6) / 0.4)
            z, y = -12 + 24 * s, A + 6.0 * math.sin(math.pi * (q - 0.6) / 0.4)
            toe = [0.15 * sg, -0.25 * math.sin(math.pi * (q - 0.6) / 0.4), -1]
        F["legs"][side] = [[10 * sg, y, -z], [10 * sg, 18, -z - 8], toe]
    ph = (2 * p) % 1.0
    impact = smooth(ph / 0.06) * (1 - smooth(ph / 0.4))   # each footfall: a quick sink, a slow recovery
    F = add(F, sink=2.4 * impact - 0.8 * math.sin(math.pi * ph), twist=7 * math.sin(TAU * p), lean=2.0 * impact,
            head=[1.6 * impact, -6 * math.sin(TAU * p), 0])
    sw = math.sin(TAU * p)
    F["hand_l"] = [-25, 29 + 2 * abs(sw), -16 * sw]
    F["elbow_l"] = [-27, 46, -8 * sw]
    F["tabard"] = [-7 * math.sin(TAU * p - 0.6) + 3 * impact, 7 * math.sin(TAU * p - 0.6) - 3 * impact]
    grip = [21, 29 - 1.8 * impact, 11 + 2 * math.sin(TAU * p)]
    F["grip"], F["tip"] = grip, trail(grip)
    return F


def chest_matrix(F):
    """The torso's world matrix for a spec (solved without disturbing the limbs' frame-to-frame memory)."""
    saved = copy.deepcopy(PREV)
    m = apply(F)
    PREV.clear()
    PREV.update(saved)
    return s2.group(m, "torso").world_matrix()


TURN_SHARE, TURN_MAX, HANDS_MAX = 0.55, 80.0, 78.0


def sweep_arc(phi, lead=0.0, dip=0.0):
    """The sword level round him at angle phi (0 = his right, 90 = straight ahead, 180 = his left), in both hands, the
    flat level so the edge leads. The body does the travelling, as in a real two-handed swing: hips and chest turn up
    to 80 degrees towards the blade (hips 40%, chest 60%; `lead` turns them ahead of it), and the hands only cover the
    rest on a short arc in front of the chest, so they never pass behind his back or through his body."""
    dev = phi - 90
    c = max(-TURN_MAX, min(TURN_MAX, TURN_SHARE * (dev + lead)))
    local = max(-HANDS_MAX, min(HANDS_MAX, dev - c))
    F = copy.deepcopy(SWEEP)
    F["hip_yaw"], F["twist"] = -0.4 * c, -0.6 * c      # right is +
    F["head"] = [8.0, max(-60.0, min(60.0, 0.85 * c)), 0.0]   # the eyes stay on the front
    M = chest_matrix(F)
    pl = math.radians(90 + local)
    grip_l = np.array([10 * math.cos(pl), 46, -22 - 8 * math.sin(pl)])      # well in front of the chest, never behind
    to_w = lambda p: list((M @ np.array([*p, 1.0]))[:3])
    F["grip"] = to_w(grip_l)
    F["elbow_r"] = to_w([26, 50, -20])                 # elbows out and forward of the chest, so no arm crosses it
    F["elbow_l"] = to_w([-26, 50, -20])
    r = math.radians(phi)
    F["tip"] = list(_n([math.cos(r), 0.04 - dip, -math.sin(r)]))
    F["normal"] = [0.0, 1.0, 0.0]
    F["lg"] = 1.0
    return F


def windup(t):
    """The sweep's 1 s warning: the blade lifted off the floor and out to his right, then drawn far back low behind
    him in both hands; the stance widens, he coils and sinks, and holds trembling."""
    lift = smooth(span(t, 0.0, 0.4))
    draw = back_out(span(t, 0.35, 0.85), 1.2)
    phi = -78 + 50 * lift - 37 * draw
    arc = sweep_arc(phi, dip=0.25 * clamp01(draw))
    F = mix((IDLE, 1), (arc, smooth(span(t, 0.0, 0.85))))
    F["grip"] = bezier(IDLE["grip"], [40, 40, -6], arc["grip"], lift)
    F["tip"] = list(_n(np.array(IDLE["tip"]) * (1 - lift) + np.array(arc["tip"]) * lift
                       + [0.6 * math.sin(math.pi * lift), 0, 0]))          # swung out wide of his hip
    roll = smooth(span(t, 0.1, 0.3))                   # the flat turned up once clear of the hip: the edge leads
    F["normal"] = list(_n(np.array(IDLE["normal"]) * (1 - roll) + np.array(arc["normal"]) * roll))
    F["lg"] = smooth(span(t, 0.35, 0.7))
    sr, sl = span(t, 0.05, 0.35), span(t, 0.3, 0.6)    # the stance widens, a step each foot
    F["legs"] = {"right": lerp(IDLE["legs"]["right"], WINDUP_LEGS["right"], smooth(sr)),
                 "left": lerp(IDLE["legs"]["left"], WINDUP_LEGS["left"], smooth(sl))}
    F = lift_foot(lift_foot(F, "right", sr), "left", sl)
    coil = smooth(span(t, 0.35, 0.9))
    trem = span(t, 0.7, 1.0)
    F = add(F, sink=3.5 * coil, lean=4 * coil + 0.5 * trem * math.sin(TAU * 7 * t),
            grip=[0, 0.6 * trem * math.sin(TAU * 8 * t), 0.5 * trem * math.sin(TAU * 11 * t)])
    return add(F, tabard=[4 * math.sin(TAU * t), -4 * math.sin(TAU * t)])


_WINDUP = []


def windup_end():
    """The windup's last frame (built on first use: solving it needs the rig, which needs the client's skin)."""
    if not _WINDUP:
        _WINDUP.append(windup(1.0))
    return _WINDUP[0]


def sweep(t):
    """From the windup (blade low behind his right side) round the front to his left, a held follow-through, then
    swung back round the front one-handed and let fall behind him."""
    if t < 0.45:                                        # the whirl: 305 degrees in 0.45 s, fastest at the contact
        u = ease_in(span(t, 0.0, 0.12), 1.6) * 0.18 + ease_out(span(t, 0.12, 0.45), 2.2) * 0.82
        F = mix((sweep_arc(-65 + 265 * u), 1), (windup_end(), 1 - smooth(span(t, 0, 0.12))))
        F["lean"] = SWEEP["lean"] + 6 * math.sin(math.pi * span(t, 0, 0.45))
        F["sink"] = 3.5 * (1 - smooth(span(t, 0, 0.12))) + 3.0 * math.sin(math.pi * span(t, 0.05, 0.45))
    else:
        rec = smooth(span(t, 0.75, 1.45))
        phi = (200 - 8 * smooth(span(t, 0.45, 0.75))) * (1 - rec) - 20 * rec
        F = sweep_arc(phi, dip=0.2 * rec)
        F["lg"] = 1 - smooth(span(t, 0.85, 1.1))        # the left hand lets go: one hand brings it back
        F["lean"] += 2 * math.sin(TAU * span(t, 0.45, 0.85))          # a heavy breath after the blow
        sr, sl = span(t, 0.9, 1.2), span(t, 1.15, 1.45)
        F["legs"] = {"right": lerp(WINDUP_LEGS["right"], IDLE["legs"]["right"], smooth(sr)),
                     "left": lerp(WINDUP_LEGS["left"], IDLE["legs"]["left"], smooth(sl))}
        F = lift_foot(lift_foot(F, "right", sr), "left", sl)
        F = carry(F, IDLE, smooth(span(t, 1.4, 1.8)), via=[40, 40, -8])     # down round his right hip
        w = smooth(span(t, 1.4, 1.8))
        F["tip"] = list(_n(np.array(F["tip"]) + [0.6 * math.sin(math.pi * w), 0, 0]))     # wide of his hip
        k = smooth(span(t, 1.4, 1.6))                   # the flat turned back while still clear of the hip
        F["normal"] = list(_n(np.array([0.0, 1.0, 0.0]) * (1 - k) + np.array(IDLE["normal"]) * k))
    F["tabard"] = [10 * math.sin(math.pi * span(t, 0, 0.9)), -10 * math.sin(math.pi * span(t, 0, 0.9))]
    return F


def _attack_poses():
    """The high guard: both hands in front of his face, the blade up and back over the hat; the chop in front."""
    up = put(IDLE, grip=[0.0, 84.0, -24.0], tip=list(_n([0.05, 0.85, 0.5])), normal=[1.0, 0.0, 0.0],
             elbow_r=[24.0, 76.0, -30.0], elbow_l=[-24.0, 76.0, -30.0], lg=1.0, lean=6.0, head=[10.0, 0.0, 0.0])
    up["legs"] = {"right": [[13, A, 6], [12, 18, -2], [0.2, 0, -1]], "left": [[-12, A, -10], [-11, 18, -18], [-0.1, 0, -1]]}
    held = add(up, grip=[0, 2, -1], lean=-2, head=[2, 0, 0])
    chop = put(up, grip=[4.0, 30.0, -34.0], tip=list(_n([0.04, -0.55, -1])), elbow_r=[20.0, 44.0, -28.0],
               elbow_l=[-14.0, 44.0, -30.0], lean=34.0, sink=4.0, head=[26.0, 0.0, 0.0])
    return up, held, chop


UP, HELD, CHOP = _attack_poses()
CHOP_C = np.array([2.0, 58.0, -16.0])
SHOULDER_R = np.array([20.0, 64.0, 0.0])


def round_shoulder(p0, p1, w, out=(1, 0, -0.3), pull=2.0, centre=SHOULDER_R):
    """The hand from p0 to p1 on a sphere round the shoulder, bulging out towards `out`: the arm swings wide and
    straight instead of folding past the shoulder."""
    c = np.array(centre, float)
    d0, d1 = np.array(p0, float) - c, np.array(p1, float) - c
    r0, r1 = np.linalg.norm(d0), np.linalg.norm(d1)
    u = _n(np.array(bezier(d0 / r0, _n(out) * pull, d1 / r1, w)))
    return list(c + u * (r0 + (r1 - r0) * w))                    # the hands circle this point in the chop


def chop_frame(s):
    """The chop over the top: the tip from back-down past straight up to down in front (the flat upright, so the
    edge leads), the hands on a circle in front of his chest."""
    F = mix((HELD, 1), (CHOP, s))
    F["tip"] = swing_tip(HELD["tip"], CHOP["tip"], s, turn_between(HELD["tip"], CHOP["tip"]))
    d0, d1 = np.array(HELD["grip"]) - CHOP_C, np.array(CHOP["grip"]) - CHOP_C
    b0, b1 = math.atan2(-d0[2], d0[1]), math.atan2(-d1[2], d1[1])
    r = math.hypot(d0[1], d0[2]) * (1 - s) + math.hypot(d1[1], d1[2]) * s
    b = b0 + (b1 - b0) * s
    F["grip"] = [d0[0] * (1 - s) + d1[0] * s + CHOP_C[0], CHOP_C[1] + r * math.cos(b), CHOP_C[2] - r * math.sin(b)]
    return F


def raise_path(w):
    return np.array(round_shoulder(IDLE["grip"], UP["grip"], w, out=(1, 0, -1.4), pull=1.2))


def raise_frame(t):
    """Up in front of his right side into the high guard, the arm swung round the shoulder (not folded past it), the
    flat kept to his side: mostly the blade rises along its own plane."""
    w = soft_back(span(t, 0.0, 0.46), 1.15)
    sl = span(t, 0.05, 0.35)
    F = carry(IDLE, UP, w, legs_w=smooth(sl))
    g = smooth(span(t, 0.0, 0.46))
    F["grip"] = list(raise_path(g))
    F["normal"] = list(_n(np.array(IDLE["normal"]) * (1 - g) + np.array(UP["normal"]) * g))   # the flat to his side
    grip_l = np.array(F["grip"]) - _n(F["tip"]) * 6
    F["hand_l"], F["lg"] = bezier(IDLE["hand_l"], [-32, 58, -34], grip_l, smooth(span(t, 0.05, 0.46))), 0.0
    F["elbow_l"] = list(np.array(IDLE["elbow_l"]) * (1 - g) + np.array(UP["elbow_l"]) * g)
    return lift_foot(F, "left", sl)


def attack(t):
    """Melee: the sword raised high over his head, a held beat, the chop down in front, wrenched up, let swing back."""
    if t < 0.46:
        F = raise_frame(t)
    elif t < 0.56:
        F = mix((raise_frame(0.46), 1), (HELD, smooth(span(t, 0.46, 0.56))))
    elif t < 0.72:
        F = chop_frame(ease_in(span(t, 0.56, 0.72), 1.7))
    elif t < 1.0:
        F = add(CHOP, sink=1.8 * math.sin(math.pi * span(t, 0.72, 0.9)))     # the blade bites; he sinks into it
    else:
        w = smooth(span(t, 1.0, 1.5))
        sl = span(t, 1.05, 1.35)
        F = carry(CHOP, IDLE, w, via=[30, 36, -22], legs_w=smooth(sl))
        grip_l = np.array(CHOP["grip"]) - _n(CHOP["tip"]) * 6       # the left hand lets go and drops out to his side
        k = smooth(span(t, 1.0, 1.4))
        F["hand_l"], F["lg"] = bezier(grip_l, [-32, 40, -24], IDLE["hand_l"], k), 0.0
        F["elbow_l"] = bezier(CHOP["elbow_l"], [-44, 46, -14], IDLE["elbow_l"], k)   # the elbow goes out, not across
        F = lift_foot(F, "left", sl)
    return add(F, tabard=[6 * math.sin(math.pi * span(t, 0.5, 1.1)), -6 * math.sin(math.pi * span(t, 0.5, 1.1))])


def call(t):
    """The warband answers: the sword swung round and driven point-down into the floor, the left fist raised, head up;
    the skulls flare upwards. Then wrenched out and let hang behind him again."""
    high = put(IDLE, grip=[8.0, 66.0, -30.0], tip=list(_n([0, -1, -0.08])), normal=[1.0, 0.0, 0.0],
               elbow_r=[24.0, 62.0, -24.0], lean=10.0)
    plant = put(high, grip=[6.0, 44.0, -30.0], elbow_r=[22.0, 52.0, -26.0], lean=14.0, sink=2.0)
    roar = put(plant, hand_l=[-24.0, 98.0, -10.0], elbow_l=[-32.0, 76.0, -4.0], head=[28.0, 0.0, 0.0], lean=4.0,
               sink=0.0, lift=12.0)
    if t < 0.35:
        F = carry(IDLE, high, smooth(span(t, 0.0, 0.35)), via=[30, 56, -26])
    elif t < 0.5:
        F = mix((high, 1), (plant, ease_in(span(t, 0.35, 0.5), 2.2)))
    elif t < 1.4:
        w = soft_back(span(t, 0.5, 0.9), 1.4)
        F = mix((plant, 1), (roar, w))
        F["hand_l"] = bezier(plant["hand_l"], [-46, 62, -14], roar["hand_l"], w)
        F = add(F, lean=0.4 * span(t, 0.9, 1.4) * math.sin(TAU * 9 * t))
    elif t < 1.65:
        k = smooth(span(t, 1.4, 1.65))
        F = mix((roar, 1), (high, k))
        F["hand_l"] = bezier(roar["hand_l"], [-46, 62, -14], high["hand_l"], k)
    else:
        F = carry(high, IDLE, smooth(span(t, 1.65, 2.2)), via=[30, 52, -26])
    F["bob"] = 1.0
    return add(F, tabard=[3 * math.sin(TAU * t), -3 * math.sin(TAU * t)])


def _enrage_poses():
    brk = add(IDLE, lean=18, head=[-14, 0, 0], sink=5, lift=-6)
    high = put(IDLE, grip=[2.0, 80.0, -28.0], tip=list(_n([0, -1, -0.1])), normal=[0.0, 0.0, 1.0], lg=1.0,
               elbow_r=[24.0, 70.0, -26.0], elbow_l=[-22.0, 70.0, -26.0], head=[20.0, 0.0, 0.0], lean=12.0, lift=2.0,
               legs=WIDE)
    slam = put(high, grip=[2.0, 46.0, -32.0], lean=24.0, sink=9.0, head=[10.0, 0.0, 0.0], lift=-2.0,
               elbow_r=[20.0, 50.0, -28.0], elbow_l=[-18.0, 50.0, -28.0])
    roar = put(slam, lean=10.0, sink=4.0, head=[36.0, 0.0, 0.0], lift=14.0, spread=1.35)
    out = put(roar, grip=[2.0, 62.0, -32.0], lean=16.0, sink=3.0, head=[10.0, 0.0, 0.0], lift=8.0, spread=1.25)
    return brk, high, slam, roar, out


BRK, HIGH, SLAM, ROAR, PULLED = _enrage_poses()


def enrage(t):
    """Below 35%: he buckles, rises with the sword point-down high in both hands, drives it into the floor, roars as the
    skulls whirl round him, wrenches it free and levels the point at you (the enraged low guard)."""
    if t < 0.4:
        F = mix((IDLE, 1), (BRK, smooth(span(t, 0.0, 0.4))))
    elif t < 0.85:
        w = soft_back(span(t, 0.4, 0.85), 1.2)
        sr, sl = span(t, 0.45, 0.7), span(t, 0.55, 0.8)
        F = carry(BRK, HIGH, w, via=[30, 66, -36])
        grip_l = np.array(F["grip"]) - _n(F["tip"]) * 6
        F["hand_l"] = bezier(BRK["hand_l"], [-30, 56, -30], grip_l, smooth(span(t, 0.4, 0.85)))
        F["lg"] = 0.0
        F["legs"] = {"right": lerp(BRK["legs"]["right"], WIDE["right"], smooth(sr)),
                     "left": lerp(BRK["legs"]["left"], WIDE["left"], smooth(sl))}
        F = lift_foot(lift_foot(F, "right", sr), "left", sl)
    elif t < 1.05:
        F = mix((HIGH, 1), (SLAM, ease_in(span(t, 0.85, 1.05), 2.2)))
    elif t < 1.7:
        F = mix((SLAM, 1), (ROAR, back_out(span(t, 1.05, 1.4), 1.3)))
        F = add(F, lean=0.6 * span(t, 1.2, 1.7) * math.sin(TAU * 9 * t))
    elif t < 1.9:
        F = mix((ROAR, 1), (PULLED, ease_out(span(t, 1.7, 1.9), 2.0)))
    else:                                               # the point swung up off the floor and levelled at you
        s = soft_back(span(t, 1.9, 2.4), 1.2)
        F = carry(PULLED, ENRAGED, s, legs_w=smooth(span(t, 1.95, 2.35)))
        F["tip"] = swing_tip(PULLED["tip"], ENRAGED["tip"], s, turn_between(PULLED["tip"], ENRAGED["tip"], False))
        F = lift_foot(F, "left", span(t, 1.95, 2.35))
    F["orbit"] = 360 * smooth(span(t, 1.05, 2.3))      # the skulls whirl once round him
    F["bob"] = 1.0
    F["bob_period"] = 2.4
    return add(F, tabard=[5 * math.sin(math.pi * span(t, 0.85, 1.6)), -5 * math.sin(math.pi * span(t, 0.85, 1.6))])


def idle_enraged(t, L=4.8):
    F = breathe(ENRAGED, t, 1.2, 1.8)
    F["bob_period"] = L
    F["orbit"] = 360 * t / L                            # the skulls circle his head
    return add(F, grip=[0, 1.2 * math.sin(TAU * t / 1.2), 0], head=[0, 6 * math.sin(TAU * t / L), 0])


def flinch(t):
    """A hit barely moves him: a short recoil, then the head drops back onto you."""
    k = math.sin(math.pi * span(t, 0, 0.3))
    g = math.sin(math.pi * span(t, 0.2, 0.5))
    return add(IDLE, lean=-4 * k + 2 * g, head=[7 * k - 5 * g, 0, 0], sink=0.8 * k, tabard=[-4 * k, 4 * k])


def kneel():
    F = copy.deepcopy(DEATH)
    F["fall"] = 1.0
    F["normal"] = [1, 0, 0]                            # the flat to the side (no flip on the way)
    F["grip"], F["lean"] = [0.0, 40.0, -34.0], 20.0    # far enough out that the bowed head clears the pommel
    F["elbow_r"], F["elbow_l"] = [16.0, 42.0, -28.0], [-16.0, 42.0, -28.0]
    F["legs"]["right"][2] = [0, -0.08, 1]              # the kneeling foot lies along the floor, toes behind
    F["tabard"] = [-14.0, 28.0]                        # the cloth lies out over the floor, not through it
    return F


def roll_toe(F, F0, F1, w):
    """The right foot going down onto (or up off) its knee: the toe turns through pointing down, never sideways."""
    t0, t1 = F0["legs"]["right"][2], F1["legs"]["right"][2]
    down = side_angle(t1) < 0 and side_angle(t1) > -90       # kneeling: toes behind and down
    F["legs"]["right"][2] = swing_tip(t0, t1, w, turn_between(t0, t1, positive=down))
    return F


def death(t):
    stagger = add(IDLE, lean=-10, head=[18, 0, 0], twist=-8, grip=[1, 3, 3])
    stagger["tip"] = trail(stagger["grip"])
    if t < 0.5:
        F = mix((IDLE, 1), (stagger, back_out(span(t, 0, 0.5), 1.2)))
    else:
        w = ease_in(span(t, 0.5, 1.4), 1.8)
        F = roll_toe(carry(stagger, kneel(), w, via=[30, 44, -24]), stagger, kneel(), w)
        F = add(F, drop=-1.5 * math.sin(math.pi * span(t, 1.4, 1.7)))          # the knee hits: a small rebound
    F["fall"] = {k: ease_in(span(t, 0.9 + d, 1.6 + d), 2.0) for k, d in (("c", 0.0), ("l", 0.25), ("r", 0.45))}
    F["bob"] = 1 - span(t, 0.6, 1.2)
    F["head"] = [F["head"][0] - 14 * smooth(span(t, 1.6, 2.6)), F["head"][1], 0]
    return F


def spawn(t):
    """From the kneel over the planted sword: the skulls rise from the floor, he stands on the hilt, wrenches the sword
    out and lets it swing back to hang behind him; the head comes up last."""
    k = kneel()
    k["head"] = [k["head"][0] - 14, 0, 0]
    stand = put(IDLE, grip=k["grip"], tip=k["tip"], normal=k["normal"], lg=1.0, lean=20.0,
                elbow_r=[20.0, 48.0, -28.0], elbow_l=[-20.0, 48.0, -28.0], head=[-6.0, 0.0, 0.0])
    pulled = put(stand, grip=[2.0, 60.0, -32.0], lean=14.0)
    if t < 1.2:
        F = copy.deepcopy(k)
    elif t < 2.3:
        F = mix((k, 1), (stand, soft_back(span(t, 1.2, 2.3), 1.1)))
        F["legs"] = lerp(k["legs"], stand["legs"], smooth(span(t, 1.2, 2.2)))
        F = roll_toe(F, k, stand, smooth(span(t, 1.2, 2.2)))
    elif t < 2.6:
        F = mix((stand, 1), (pulled, ease_out(span(t, 2.3, 2.6), 2.0)))
    else:
        F = carry(pulled, IDLE, smooth(span(t, 2.6, 3.3)), via=[30, 50, -24])
    F["head"] = [F["head"][0] + 16 * math.sin(math.pi * span(t, 2.6, 3.4)), F["head"][1], 0]   # the look up
    F["fall"] = {key: 1 - smooth(span(t, 0.3 + d, 1.4 + d)) for key, d in (("c", 0.0), ("l", 0.2), ("r", 0.35))}
    F["rise"] = True
    F["bob"] = smooth(span(t, 1.0, 2.0))
    return F


CLIPS = {  # name: (length, loop, frame at t, key step)
    "idle": (4.0, "loop", idle, 0.1),
    "walk": (1.6, "loop", walk, 0.05),
    "windup": (1.0, "hold", windup, 0.025),
    "sweep": (1.8, "once", sweep, 0.025),
    "attack": (1.5, "once", attack, 0.025),
    "call": (2.2, "once", call, 0.025),
    "enrage": (2.4, "once", enrage, 0.025),
    "idle_enraged": (4.8, "loop", idle_enraged, 0.1),
    "flinch": (0.5, "once", flinch, 0.05),
    "spawn": (3.4, "once", spawn, 0.05),
    "death": (3.2, "hold", death, 0.05),
}


# ---- tracks -------------------------------------------------------------------------------------------------------------

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


def tracks(name):
    length, loop, fn, step = CLIPS[name]
    b = bind()
    rest = {g.name: np.array(g.rotation, float) for g in b.groups}
    r_org = {g.name: np.array(g.origin) for g in b.groups}
    times = list(np.arange(0, length - 1e-6, step)) + [length]
    PREV.clear()
    STEP[0] = step
    rot, pos = ({g: [] for g in rest} for _ in range(2))
    prev = {g: None for g in rest}
    for t in times:
        F = fn(float(t))
        m = apply(F, float(t))
        moved = {g.name: np.array(g.origin) - r_org[g.name] for g in m.groups}
        for g in m.groups:
            d = pick(np.array(g.rotation, float), rest[g.name], prev[g.name])
            prev[g.name] = d
            tt = round(float(t), 3)
            rot[g.name].append((tt, tuple(round(float(v), 2) for v in d), "catmullrom"))
            parent = moved.get(g.parent.name, np.zeros(3)) if g.parent is not None else np.zeros(3)
            pos[g.name].append((tt, tuple(round(float(v), 3) for v in moved[g.name] - parent), "catmullrom"))
    if loop == "loop":                                  # the last key is the first again (a whole turn kept whole)
        for g in rest:
            f0, fl = np.array(rot[g][0][1]), np.array(rot[g][-1][1])
            v = f0 + 360 * np.round((fl - f0) / 360)
            rot[g][-1] = (rot[g][-1][0], tuple(round(float(x), 2) for x in v), "catmullrom")
            pos[g][-1] = (pos[g][-1][0], pos[g][0][1], "catmullrom")
    bones = {}
    for g in rest:
        ch = {}
        if any(any(abs(v) > 0.05 for v in k[1]) for k in rot[g]):
            ch["rotation"] = rot[g]
        if any(any(abs(v) > 1e-3 for v in k[1]) for k in pos[g]):
            ch["position"] = pos[g]
        if ch:
            bones[g] = ch
    return bones


def jumps(bones):
    worst = (0.0, "", 0.0)
    for b, ch in bones.items():
        keys = ch.get("rotation", [])
        for (_, v0, _), (t1, v1, _) in zip(keys[:-1], keys[1:]):
            d = max(abs(v1[i] - v0[i]) for i in range(3))
            if d > worst[0]:
                worst = (d, b, t1)
    return worst


def edge_report(name, dt=0.025, fast=160.0):
    """How flat-on the blade travels: at every moment its middle moves faster than `fast` units a second, the share of
    its speed along the flat's normal (0 = the edge leads exactly, 1 = the flat slaps). Worst moment returned."""
    length, _, fn, _ = CLIPS[name]
    PREV.clear()
    hand = np.array(s2.group(bind(), "sword").origin, float)
    mid = np.array([*(hand + [0, 0, -40.0]), 1.0])
    prev, worst = None, (0.0, 0.0, 0.0)
    for t in np.arange(0, length + 1e-6, dt):
        m = apply(fn(float(t)), float(t))
        W = s2.group(m, "sword").world_matrix()
        p, n = (W @ mid)[:3], W[:3, :3] @ np.array([1.0, 0, 0])
        if prev is not None:
            v = (p - prev) / dt
            speed = float(np.linalg.norm(v))
            if speed > fast:
                c = abs(float(v @ n)) / speed
                if c > worst[0]:
                    worst = (c, float(t), speed)
        prev = p
    PREV.clear()
    return {"flat_share": round(worst[0], 2), "at": round(worst[1], 3), "speed": round(worst[2])}


def build_all(names=None):
    clip_set, report = {}, {}
    for name in (names or CLIPS):
        length, loop, _, _ = CLIPS[name]
        bones = tracks(name)
        clip_set[name] = (length, loop, bones)
        j, r = jumps(bones), true_steps(bones)
        report[name] = {"largest_euler_step": round(j[0], 1), "bone": j[1], "at": j[2],
                        "largest_true_step": round(r[0], 1), "true_bone": r[1], "true_at": r[2],
                        "edge": edge_report(name)}
        print(name, report[name], flush=True)
    return clip_set, report


def animations(model_id, clip_set):
    """The clips as Blockbench animations (Blockbench's animator turns X and Y the other way round to the group
    rotation, and mirrors X positions)."""
    from bosskit.bbmodel import _uuid
    anims = []
    for clip, (length, loop, bones) in clip_set.items():
        animators = {}
        for bone, channels in bones.items():
            frames = []
            for ch, keys in channels.items():
                for t, v, interp in keys:
                    if ch == "rotation":
                        point = {"x": round(-v[0], 2), "y": round(-v[1], 2), "z": round(v[2], 2)}
                    else:
                        point = {"x": round(-v[0], 3), "y": round(v[1], 3), "z": round(v[2], 3)}
                    frames.append({"channel": ch, "data_points": [point], "time": round(t, 3), "color": -1,
                                   "interpolation": interp, "uuid": _uuid(f"{model_id}/{clip}/{bone}/{ch}/{t}")})
            animators[_uuid(f"{model_id}/group/{bone}")] = {"name": bone, "type": "bone", "keyframes": frames}
        anims.append({"uuid": _uuid(f"{model_id}/anim/{clip}"), "name": clip, "loop": loop,
                      "override": clip in OVERRIDE, "length": length, "snapping": 40, "selected": False,
                      "anim_time_update": "", "blend_weight": "", "start_delay": "", "loop_delay": "",
                      "animators": animators})
    return anims


def floor_check(clip_set, model):
    """The lowest point of the model (the sword aside: it may cut the floor) every 1/20 s of every clip."""
    from bosses.volley_crone_s7 import matrices
    from bosskit.bbmodel import pivot_matrix
    worst = {}
    for name, (length, _, bones) in clip_set.items():
        low = 1e9
        for t in np.arange(0, length + 1e-6, 0.05):
            mats = matrices(model, bones, t)
            for c in model.cubes:
                if c.group.name in ("sword", "glow_brand"):
                    continue
                m = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
                lo, hi = np.array(c.frm), np.array(c.to)
                pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
                low = min(low, float((m @ pts)[1].min()))
        worst[name] = round(low, 1)
    return worst


BODY_GROUPS = ("torso", "hips", "hi_head", "leg_left", "leg_right", "shin_left", "shin_right")
MOVING_GROUPS = ("forearm_left", "forearm_right", "sword")


def clip_check(clip_set, model, dt=0.05, names=None):
    """Clipping, measured on the keys BetterModel plays: points through each forearm, hand and the sword's blade and
    guard, tested against every cube of the torso, belt, head and legs. Per clip the deepest point inside the body
    (units), and what it was in."""
    from bosses.volley_crone_s7 import matrices
    from bosskit.bbmodel import pivot_matrix
    g = np.linspace(0.1, 0.9, 3)
    grid = np.array([[a, b, c] for a in g for b in g for c in g])
    body = [c for c in model.cubes if c.group.name in BODY_GROUPS]
    moving = [c for c in model.cubes if c.group.name in MOVING_GROUPS]
    out = {}
    for name, (length, _, bones) in clip_set.items():
        if names and name not in names:
            continue
        worst = (0.0, "", 0.0)
        for t in np.arange(0, length + 1e-6, dt):
            mats = matrices(model, bones, float(t))
            pts, owner = [], []
            for c in moving:
                lo, hi = np.array(c.frm), np.array(c.to)
                local = lo + grid * (hi - lo)
                M = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
                pts.append((M @ np.c_[local, np.ones(len(local))].T)[:3].T)
                owner += [c.name] * len(local)
            pts = np.vstack(pts)
            for b in body:
                M = mats[b.group.name] @ pivot_matrix(b.origin, b.rotation)
                loc = (np.linalg.inv(M) @ np.c_[pts, np.ones(len(pts))].T)[:3].T
                lo, hi = np.array(b.frm), np.array(b.to)
                depth = np.minimum(loc - lo, hi - loc).min(axis=1)
                i = int(np.argmax(depth))
                if depth[i] > worst[0]:
                    worst = (float(depth[i]), f"{owner[i]} in {b.name}", round(float(t), 3))
        out[name] = {"deepest": round(worst[0], 1), "what": worst[1], "at": worst[2]}
    return out


def true_steps(bones):
    """The largest real turn of any bone between two neighbouring keys (degrees), not the Euler difference."""
    from bosskit.bbmodel import rotation_matrix
    rest = {g.name: np.array(g.rotation, float) for g in bind().groups}
    worst = (0.0, "", 0.0)
    for b, ch in bones.items():
        ks = ch.get("rotation", [])
        for (_, v0, _), (t1, v1, _) in zip(ks[:-1], ks[1:]):
            R0, R1 = rotation_matrix(rest[b] + np.array(v0)), rotation_matrix(rest[b] + np.array(v1))
            ang = math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(R0.T @ R1) - 1) / 2))))
            if ang > worst[0]:
                worst = (ang, b, t1)
    return worst


def main(argv):
    st.SKIN = Image.open(Path(argv[-1]) / "assets/minecraft/textures/entity/skeleton/wither_skeleton.png").convert("RGBA")
    OUT.mkdir(parents=True, exist_ok=True)
    names = [a for a in argv[:-1] if a in CLIPS]
    clip_set, report = build_all(names or None)
    if names:                                           # a quick look at some clips: report only
        return
    rig = json.loads((S6 / f"{s4.NAME}.bbmodel").read_text(encoding="utf-8"))
    rig["animations"] = animations(s4.NAME, clip_set)
    p = OUT / f"{s4.NAME}.bbmodel"
    p.write_text(json.dumps(rig, separators=(",", ":")) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(p, s3.SERVER_MODELS / p.name)
    model = s3.rest_model()
    floors = floor_check(clip_set, model)
    clips = clip_check(clip_set, model)
    summary = {k: {"length": CLIPS[k][0], "loop": CLIPS[k][1], "lowest_y": floors[k], "clipping": clips[k], **report[k]}
               for k in CLIPS}
    (OUT / "clips.json").write_text(json.dumps({"contact_seconds": CONTACT, "clips": summary}, indent=2) + "\n",
                                    encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
