"""Heartwood Horror, session 7: animation (plan: docs/art/bosses/heartwood_horror/overhaul/plan.md).

The clips are authored as motion on the session 2 rig, not as poses blended in joint space:
- Poses are keyed in world space (where each hand, foot and the trunk's bend should be) and solved every 1/20 s onto
  the rig: arms fitted along a curve through their control points at their fixed bone lengths and pulled onto their
  end (FABRIK, joints kept above the floor), legs by two-bone IK onto the floor.
- Overlap and follow-through: down each arm, every control point runs a little behind the one before it, so the
  shoulder leads and the hand trails, overshoots and settles.
- Anticipation, a fast strike, an overshoot past the contact and a slow settle on every attack (ease-in strikes,
  back-out snaps).
- Secondary motion is simulated, not keyed: the lantern hangs on its root as a damped pendulum driven by the brow it
  hangs from, and every strand of moss is its own little pendulum. Loops are simulated three times round and the
  last pass kept, so they close.
- A collision checker runs on the exported tracks (what BetterModel will interpolate): every arm, leg and trunk
  segment is a capsule, the lantern and the womb spheres; any limb passing into another part is reported with the
  clip and the time. The clips are tuned until none does.
- Keys every 0.05 s, each bone's Euler angles kept next to the key before (no long-way-round spins).

Clips, timed to HeartwoodHorror.java (session 8 moves the hits onto these contacts and the walk speed onto the stride):
  idle      4.0 s loop   breathing, the trunk creaking, the arms shifting, a sudden creaking twitch of the thin arm
  walk      2.0 s loop   a lurching three-beat gait: the crutch swings ahead and plants, the body vaults over it, then
                         the right and the left leg; the dragging hands slide behind (1.6 blocks a second)
  spawn     4.2 s        curled in the circle like the sleeper, it shudders, unfolds limb by limb, rears and roars
                         (2.8 s), settles into the stalk
  swipe     1.4 s        coils right with the great arm high, rakes it down on the target (contact 0.55 s), digs in,
                         swings it back round its right side
  lunge     1.2 s        arrives crouched behind its prey (the creak's teleport) and stabs forward (contact 0.3 s)
  eruption  2.4 s        rears with every hand off the floor, drives them in (0.55 s), strains while the lanes charge,
                         wrenches (the roots burst, 1.5 s)
  sap       2.6 s        rears up, the womb lifted, arms flung wide and trembling; the sap falls (1.75 s)
  slam      2.3 s        a long rise with the crutch and the great arm raised overhead, brought down together (1.5 s)
  creak     1.0 s        stop-motion jerks like a watched creaking, folding in before it vanishes
  twitch    0.5 s        a heart breaks: a sharp flinch
  stagger   1.8 s        the last heart breaks: rears back, the crutch slips, it sags and recovers
  death     3.6 s hold   the legs give, it leans on the crutch, the crutch buckles, it topples; a last twitch

Run from the repository root, with the folder holding assets/ from the 26.2 client as the last argument:
python tools/art/bosses/heartwood_s7.py [--no-gifs] [clip ...] <folder>
"""
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
from bosskit.bbmodel import pivot_matrix, rotation_matrix  # noqa: E402
from bosses import archevoker_s6 as a6, volley_crone_s4 as v4  # noqa: E402
from bosses.volley_crone_s7 import matrices  # noqa: E402
from bosses import heartwood_s2 as s2, heartwood_s3 as s3, heartwood_s4 as s4, heartwood_s6 as s6  # noqa: E402

OUT = ROOT / "docs/art/bosses/heartwood_horror/overhaul/s7_animation"
DT = 0.05
SPEED = 25.6                      # model units a second: the walk's 1.6 blocks a second
G = 157.0                         # gravity, model units / s^2
N = 5                             # control points per arm (after the shoulder)

# ---- easing -------------------------------------------------------------------------------------------------------------


def clamp01(x):
    return min(1.0, max(0.0, x))


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_in(x, p=2.6):            # accelerating: a strike, a fall
    return clamp01(x) ** p


def ease_out(x, p=2.2):           # decelerating: a rise, a settle
    return 1 - (1 - clamp01(x)) ** p


def back_out(x, s=1.7):           # past the mark and back: a snap that settles
    x = clamp01(x) - 1
    return 1 + x * x * ((s + 1) * x + s)


def snap(x):                      # a creaking jerk: there almost at once, then still
    return smooth(clamp01(x / 0.3))


EASE = {"smooth": smooth, "in": ease_in, "out": ease_out, "back": back_out, "snap": snap, "linear": clamp01}

# ---- the bind pose as world targets --------------------------------------------------------------------------------------

SHOULDER0 = {k: np.array(s2.yaw_about(p, s2.TWIST)) for k, (p, _) in s2.SHOULDERS.items()}
ARM0 = {k: [np.array(p, float) for p in v[0]] for k, v in s2.ARMS.items()}
DRAG0 = {k: np.array(v[5], float) for k, v in s2.ARMS.items()}
CURL0 = {k: (-25.0 if k == "crutch" else 0.0) for k in s2.ARMS}
LEG0 = {s: (np.array(v[3], float), s2._n(np.array(v[2]) - np.array(v[3])), np.array([0, 0, -20.0]))
        for s, v in s2.LEGS.items()}


def resample(pts, n=N):
    """n points along the curve through pts (by arc length), the first and last kept."""
    c = s2.curve([np.array(p, float) for p in pts], 120)
    seg = [np.linalg.norm(c[i + 1] - c[i]) for i in range(len(c) - 1)]
    cum = np.concatenate([[0], np.cumsum(seg)])
    out = []
    for k in range(n):
        s = cum[-1] * k / (n - 1)
        i = min(int(np.searchsorted(cum, s)) - 1, len(seg) - 1)
        i = max(i, 0)
        f = (s - cum[i]) / max(seg[i], 1e-9)
        out.append(c[i] + (c[i + 1] - c[i]) * f)
    return out


def bind_pose():
    P = {"hips": np.zeros(5), "trunk": np.zeros(7), "lantern": np.zeros(3)}
    for k in ARM0:
        P["arm:" + k] = np.concatenate([p - SHOULDER0[k] for p in resample(ARM0[k])])
        P["drag:" + k] = DRAG0[k].copy()
        P["curl:" + k] = np.array([CURL0[k]])
    for s, (foot, hock, hint) in LEG0.items():
        P["leg:" + s] = np.concatenate([foot, hock, hint])
    return P


BIND = bind_pose()


def pose(base=None, hips=None, trunk=None, arms=None, legs=None, lantern=None):
    """A key pose: changes over a base pose. arms: {name: (world points, drag, curl)} (points as at the bind pose's
    shoulder; any count, resampled); legs: {side: (foot, hock direction, knee hint)}; trunk: (pitches of joints 0..4,
    yaw, roll); hips: (dy, dz, pitch, yaw, roll); lantern: an extra push on the pendulum (world, units/s)."""
    P = {k: v.copy() for k, v in (base or BIND).items()}
    if hips is not None:
        P["hips"] = np.array(hips, float)
    if trunk is not None:
        P["trunk"] = np.array(trunk, float)
    for k, spec in (arms or {}).items():
        pts, drag = spec[0], spec[1] if len(spec) > 1 else None
        P["arm:" + k] = np.concatenate([np.array(p) - SHOULDER0[k] for p in resample(pts)])
        if drag is not None:
            P["drag:" + k] = np.array(drag, float)
        if len(spec) > 2:
            P["curl:" + k] = np.array([spec[2]], float)
    for s, (foot, hock, hint) in (legs or {}).items():
        P["leg:" + s] = np.concatenate([np.array(foot, float), s2._n(hock), np.array(hint, float)])
    if lantern is not None:
        P["lantern"] = np.array(lantern, float)
    return P


def shift(P, key, d):
    """A copy of P with every point of an arm moved by d (the hand included)."""
    Q = {k: v.copy() for k, v in P.items()}
    Q["arm:" + key] = Q["arm:" + key] + np.tile(np.array(d, float), N)
    return Q


# ---- timelines -------------------------------------------------------------------------------------------------------


def slerp_dir(a, b, f):
    """A direction turned a fraction f of the way from a to b (round the vertical when they are opposite)."""
    a, b = s2._n(a), s2._n(b)
    c = float(np.clip(a @ b, -1, 1))
    ang = math.acos(c)
    if ang < 1e-4:
        return a
    axis = np.cross(a, b)
    if np.linalg.norm(axis) < 1e-6:
        axis = np.cross(a, [0, 1.0, 0]) if abs(a[1]) < 0.9 else np.cross(a, [1.0, 0, 0])
    return axis_angle_R(axis, ang * f) @ a


def mix_pose(pa, pb, f):
    out = {}
    for k in pa:
        if k.startswith("drag:"):
            out[k] = slerp_dir(pa[k], pb[k], f)
        else:
            out[k] = pa[k] + (pb[k] - pa[k]) * f
    return out


class Clip:
    def __init__(self, name, length, loop, keys, layer=None, lag=0.035, contact=None, interp="catmullrom", dt=DT):
        """keys: [(time, pose, ease into this key)]; layer(t, P) adds procedural motion on top; dt: the key step
        (fast strikes get denser keys so the interpolation follows the whip)."""
        self.name, self.length, self.loop, self.keys = name, length, loop, keys
        self.layer, self.lag, self.contact, self.interp, self.dt = layer, lag, contact, interp, dt

    def sample_raw(self, t):
        keys = self.keys
        if self.loop == "loop":
            t = t % self.length
        if t <= keys[0][0]:
            return keys[0][1]
        for (ta, pa, _), (tb, pb, eb) in zip(keys, keys[1:]):
            if ta <= t <= tb:
                f = EASE[eb]((t - ta) / max(1e-9, tb - ta))
                return mix_pose(pa, pb, f)
        if self.loop == "loop":            # from the last key round to the first
            (ta, pa, _), (tb, pb, eb) = keys[-1], (self.length + keys[0][0], keys[0][1], keys[0][2])
            f = EASE[eb]((t - ta) / max(1e-9, tb - ta))
            return mix_pose(pa, pb, f)
        return keys[-1][1]

    def sample(self, t):
        P = dict(self.sample_raw(t))
        for k in ARM0:                     # overlap: point i of an arm runs lag*i behind the shoulder
            pts = P["arm:" + k].reshape(N, 3).copy()
            for i in range(1, N):
                tt = t - self.lag * i
                if self.loop != "loop":
                    tt = max(0.0, tt)
                pts[i] = self.sample_raw(tt)["arm:" + k].reshape(N, 3)[i]
            P["arm:" + k] = pts.reshape(-1)
        if self.layer:
            P = self.layer(t, {k: v.copy() for k, v in P.items()})
        return P


# ---- solving a pose onto the rig -------------------------------------------------------------------------------------------


class Sim:
    """State carried from frame to frame: the lantern's and the moss's pendulums, each hand's last heading."""

    def __init__(self):
        self.lantern = None
        self.moss = {}
        self.hand_yaw = {}
        self.rot = {}
        self.roll = {}


def axis_angle_R(axis, ang):
    a = s2._n(axis)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K


def toward(A, B, f):
    """A turned a fraction f of the way to B (both rotation matrices)."""
    D = A.T @ B
    ang = math.acos(max(-1.0, min(1.0, (np.trace(D) - 1) / 2)))
    if ang < 1e-6:
        return A
    axis = np.array([D[2, 1] - D[1, 2], D[0, 2] - D[2, 0], D[1, 0] - D[0, 1]])
    if np.linalg.norm(axis) < 1e-9:
        return A
    return A @ axis_angle_R(axis, ang * f)


_TWIST = {}


def bind_twist(chain):
    """Per bone: (its bind twist: the bind local rotation with the swing taken out, its bind local rotation)."""
    name = chain.bones[0].name
    if name not in _TWIST:
        b = next(c for c in bind_rig().chains() if c.bones[0].name == name)
        out = []
        for bone in b.bones:
            L = rotation_matrix(bone.rotation)
            out.append((s2.turn_to(b.u, L @ b.u).T @ L, L))
        _TWIST[name] = out
    return _TWIST[name]


GIMBAL = 0.94                     # |sin(euler y)| above this counts as near gimbal lock


def clear_gimbal(L, axis, key, sim):
    """L rolled about its own `axis` (local) by the smallest remembered offset that keeps |L[2, 0]| (the sine of the
    Euler y angle) below GIMBAL; the offset relaxes back to zero when it isn't needed."""
    phi = sim.roll.get(key, 0.0)

    def rolled(a):
        return L @ axis_angle_R(axis, math.radians(a))

    relaxed = phi * 0.8
    if abs(rolled(relaxed)[2, 0]) <= GIMBAL:
        phi = relaxed
    elif abs(rolled(phi)[2, 0]) > GIMBAL:
        for step in range(1, 31):
            for a in (phi + 2 * step, phi - 2 * step):
                if abs(rolled(a)[2, 0]) <= GIMBAL:
                    phi = a
                    break
            else:
                continue
            break
    sim.roll[key] = phi
    return rolled(phi)


def place(chain, J, sim):
    """Bends a chain onto world joints J. Each bone turns the least it can from where it was the frame before, so it
    never flips round its own length; its twist is pulled gently back to its bind twist, so it never drifts either."""
    Rp = s2.wR(chain.parent)
    twist = bind_twist(chain)
    prev = sim.rot.get(chain.bones[0].name)
    out = []
    for k, b in enumerate(chain.bones):
        d = Rp.T @ (J[k + 1] - J[k])
        L0 = prev[k] if prev is not None else twist[k][1]
        L = s2.turn_to(L0 @ chain.u, d) @ L0
        if float(s2._n(d) @ chain.u) > -0.85:              # away from the singular direction: spring to bind twist
            Ls = s2.turn_to(chain.u, d) @ twist[k][0]
            L = toward(L, Ls, 0.2)
            L = s2.turn_to(L @ chain.u, d) @ L
        Lg = clear_gimbal(L, chain.u, b.name, sim)
        b.rotation = s2.euler(Lg)
        Rp = Rp @ Lg
        out.append(L)
    sim.rot[chain.bones[0].name] = out


def set_world_guarded(g, R, axis, sim):
    L = s2.wR(g.parent).T @ R
    g.rotation = s2.euler(clear_gimbal(L, axis, g.name, sim))


def aim_hand(g, key, drag, curl, sim):
    """Root fingers along drag in 3D (heading, then elevation), curled down by -curl. When the fingers point nearly
    straight up or down the heading is kept from the frame before, so the hand never spins round."""
    d = np.array(drag, float)
    flat = math.hypot(d[0], d[2])
    yaw = sim.hand_yaw.get(key, math.degrees(math.atan2(d[0], d[2])))
    if flat > 0.25:
        new = math.degrees(math.atan2(d[0], d[2]))
        yaw = yaw + ((new - yaw + 180) % 360 - 180)
    sim.hand_yaw[key] = yaw
    elev = math.degrees(math.atan2(d[1], max(flat, 1e-6)))
    set_world_guarded(g, s2.roty(yaw) @ rotation_matrix((-curl - elev, 0, 0)), np.array([0, 0, 1.0]), sim)


def solve(P, sim, dt=DT):
    r = s2.Rig()
    dy, dz, hp, hyaw, hroll = P["hips"]
    if abs(dy) > 1e-6 or abs(dz) > 1e-6:
        s2.translate(r.hips, (0, dy, dz))
        for ch in r.chains():
            ch.rest = [p + np.array([0, dy, dz]) for p in ch.rest]
    r.hips.rotation = [hp, hyaw, hroll]
    # the trunk: each joint bends the rest of the trunk beyond it (pitch, roll), then the whole turns (yaw)
    J = r.trunk.joints()
    pitches, yaw, roll = P["trunk"][:5], P["trunk"][5], P["trunk"][6]
    for k in range(5):
        R = rotation_matrix((pitches[k], 0, roll * (0.2 if k else 0)))
        J = J[:k + 1] + [J[k] + R @ (q - J[k]) for q in J[k + 1:]]
    J = [J[0]] + [J[0] + s2.roty(yaw) @ (q - J[0]) for q in J[1:]]
    place(r.trunk, J, sim)
    # legs: two-bone IK onto the foot, the cannon along its hock direction
    for side, ch in r.legs.items():
        v = P["leg:" + side]
        foot, hock_dir, hint = v[:3], s2._n(v[3:6]), v[6:9]
        hip = ch.joints()[0]
        hock = foot + hock_dir * ch.lengths[2]
        knee = s2.ik(hip, hock, hip + hint, ch.lengths[0], ch.lengths[1])
        place(ch, [hip, knee, hock, foot], sim)
        set_world_guarded(ch.foot, np.eye(3), np.array([0, 1.0, 0]), sim)
    # arms: points relative to the shoulder where it is now
    for k, ch in r.arms.items():
        S = ch.joints()[0]
        pts = P["arm:" + k].reshape(N, 3) + SHOULDER0[k]
        # points near the shoulder ride along with the body; the hand stays where it is keyed (planted hands stay)
        w = np.array([(1 - i / (N - 1)) ** 1.3 for i in range(N)])[:, None]
        pts = pts + w * (S - SHOULDER0[k])
        pts = fit_length(S, list(pts), sum(ch.lengths))
        Jc = s2.fit([S] + list(pts), ch.lengths)
        place(ch, s2.fabrik(Jc, ch.lengths, pts[-1], floor=8), sim)
        aim_hand(ch.hand, k, P["drag:" + k], float(P["curl:" + k][0]), sim)
    # the lantern: a damped pendulum hanging from the brow
    a = r.lroot.joints()[0]
    L = sum(r.lroot.lengths) + 11.0
    if sim.lantern is None:
        sim.lantern = [a + s2.DOWN * L, a + s2.DOWN * L]
    p, q = sim.lantern
    nxt = p + (p - q) * 0.93 + (np.array([0, -G, 0]) + P["lantern"]) * dt * dt
    nxt = a + s2._n(nxt - a) * L
    womb = s2.wpos(r.womb, r.womb.origin)
    tj = r.trunk.joints()
    for _ in range(4):                                     # it bumps off the womb and the trunk instead of passing in
        nxt[1] = max(nxt[1], 12.0)
        if np.linalg.norm(nxt - womb) < 24:
            nxt = womb + s2._n(nxt - womb) * 24
        for k in range(len(tj) - 1):
            p0, p1 = tj[k], tj[k + 1]
            f = clamp01(float((nxt - p0) @ (p1 - p0)) / float((p1 - p0) @ (p1 - p0)))
            c = p0 + (p1 - p0) * f
            rad = s2.TRUNK_W[k] * 0.38 + 11
            if np.linalg.norm(nxt - c) < rad:
                nxt = c + s2._n(nxt - c) * rad
        for leg in r.legs.values():
            lj2 = leg.joints()
            for k in range(len(lj2) - 1):
                p0, p1 = lj2[k], lj2[k + 1]
                f = clamp01(float((nxt - p0) @ (p1 - p0)) / float((p1 - p0) @ (p1 - p0)))
                c = p0 + (p1 - p0) * f
                if np.linalg.norm(nxt - c) < 15:
                    nxt = c + s2._n(nxt - c) * 15
        nxt = a + s2._n(nxt - a) * L
    sim.lantern = [nxt, p]
    d = s2._n(nxt - a)
    lj = [a]
    side = s2._n(np.cross(d, [1.0, 0, 0])) if abs(d[0]) < 0.9 else np.array([0, 0, 1.0])
    for k, seg in enumerate(r.lroot.lengths):          # the root sags a little between brow and lantern
        bend = side * 1.2 * math.sin(math.pi * (k + 1) / (len(r.lroot.lengths) + 1))
        lj.append(lj[-1] + s2._n(d + bend / 20) * seg)
    place(r.lroot, lj, sim)
    set_world_guarded(r.lantern, s2.turn_to(s2.DOWN, d) @ s2.roty(s2.TWIST * 0.5), np.array([0, 1.0, 0]), sim)
    # moss: each strand a short pendulum from where it hangs
    for g in r.moss + [s for arm in r.arms.values() for s in arm.moss]:
        top = s2.wpos(g.parent, to_rest_origin(g))
        length = 16.0
        st = sim.moss.get(g.name)
        if st is None:
            st = [top + s2.DOWN * length, top + s2.DOWN * length]
        p, q = st
        nxt = p + (p - q) * 0.72 + np.array([0, -G, 0]) * dt * dt
        nxt = top + s2._n(nxt - top) * length
        dv = s2._n(nxt - top)
        if dv @ s2.DOWN < math.cos(math.radians(55)):
            side = s2._n(dv - s2.DOWN * float(dv @ s2.DOWN))
            dv = s2.DOWN * math.cos(math.radians(55)) + side * math.sin(math.radians(55))
            nxt = top + dv * length
        sim.moss[g.name] = [nxt, p]
        set_world_guarded(g, s2.turn_to(s2.DOWN, nxt - top), np.array([0, 1.0, 0]), sim)
    return r


def curve_length(pts):
    c = s2.curve(pts, 60)
    return sum(np.linalg.norm(c[i + 1] - c[i]) for i in range(len(c) - 1))


def fit_length(S, pts, length):
    """If the curve from the shoulder through pts is shorter than the arm, its interior points bow out (away from
    the shoulder-hand line, and up) until it is as long: the elbow rises instead of the arm crumpling at the hand."""
    pts = [np.array(p, float) for p in pts]
    if curve_length([S] + pts) >= length * 0.985:
        return pts
    H = pts[-1]
    u = s2._n(H - S)
    up = s2._n(np.array([0, 1.0, 0]) - u * u[1]) if abs(u[1]) < 0.95 else np.array([1.0, 0, 0])
    base = []
    for p in pts[:-1]:
        proj = S + u * float((p - S) @ u)
        o = p - proj
        if np.linalg.norm(o) < 3:
            o = o + up * 3
        base.append((proj, o))

    def bowed(k):
        return [proj + o * k for proj, o in base] + [H]

    lo, hi = 1.0, 8.0
    for _ in range(24):
        mid = (lo + hi) / 2
        if curve_length([S] + bowed(mid)) < length:
            lo = mid
        else:
            hi = mid
    return bowed((lo + hi) / 2)


def to_rest_origin(g):
    return np.array(g.origin)


# ---- tracks ---------------------------------------------------------------------------------------------------------------

_BIND = None


def bind_rig():
    global _BIND
    if _BIND is None:
        _BIND = s2.Rig()
    return _BIND


def wrap(a):
    return (a + 180) % 360 - 180


def pick(r_abs, rest, prev):
    """The offset from rest, choosing between the two equal Euler forms and whole turns so it stays next to the
    previous key."""
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


def tracks(clip):
    b = bind_rig()
    rest = {g.name: np.array(g.rotation, float) for g in b.m.groups}
    r_org = {g.name: np.array(g.origin) for g in b.m.groups}
    times = [round(i * clip.dt, 4) for i in range(int(round(clip.length / clip.dt)) + 1)]
    sim = Sim()
    warm = 2 if clip.loop == "loop" else 0
    if clip.loop != "loop":                 # settle the pendulums on the first pose before the clip starts
        for _ in range(30):
            solve(clip.sample(0.0), sim, clip.dt)
    for _ in range(warm):
        for t in times[:-1]:
            solve(clip.sample(t), sim, clip.dt)
    rot, pos = ({g: [] for g in rest} for _ in range(2))
    prev = {g: None for g in rest}
    for t in times:
        r = solve(clip.sample(t), sim, clip.dt)
        moved = {g.name: np.array(g.origin) - r_org[g.name] for g in r.m.groups}
        for g in r.m.groups:
            d = pick(np.array(g.rotation, float), rest[g.name], prev[g.name])
            prev[g.name] = d
            rot[g.name].append((t, tuple(round(float(v), 2) for v in d), clip.interp))
            parent = moved.get(g.parent.name, np.zeros(3)) if g.parent is not None else np.zeros(3)
            pos[g.name].append((t, tuple(round(float(v), 3) for v in moved[g.name] - parent), clip.interp))
    if clip.loop == "loop":
        for track in (rot, pos):
            for g in rest:
                track[g][-1] = (track[g][-1][0], track[g][0][1], clip.interp)
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


def interp_error(bones):
    """(largest true turn between two keys, largest error of the Euler midpoint against the true halfway turn), in
    degrees, with the bone and the time: what BetterModel's interpolation actually shows."""
    rest = {g.name: np.array(g.rotation, float) for g in bind_rig().m.groups}
    worst_step, worst_err = (0.0, "", 0.0), (0.0, "", 0.0)
    for b, ch in bones.items():
        keys = ch.get("rotation", [])
        for (_, v0, _), (t1, v1, _) in zip(keys[:-1], keys[1:]):
            R0 = rotation_matrix(rest[b] + np.array(v0))
            R1 = rotation_matrix(rest[b] + np.array(v1))
            D = R0.T @ R1
            ang = math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(D) - 1) / 2))))
            if ang > worst_step[0]:
                worst_step = (round(ang, 1), b, t1)
            Rm = rotation_matrix(rest[b] + (np.array(v0) + np.array(v1)) / 2)
            E = Rm.T @ toward(R0, R1, 0.5)
            err = math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(E) - 1) / 2))))
            if err > worst_err[0]:
                worst_err = (round(err, 1), b, t1)
    return worst_step, worst_err


def jumps(bones):
    worst = (0.0, "", 0.0)
    for b, ch in bones.items():
        keys = ch.get("rotation", [])
        for (_, v0, _), (t1, v1, _) in zip(keys[:-1], keys[1:]):
            d = max(abs(v1[i] - v0[i]) for i in range(3))
            if d > worst[0]:
                worst = (d, b, t1)
    return worst


# ---- the collision check (on the exported tracks) -------------------------------------------------------------------------

def capsules(model, mats):
    """(name, owner, a, b, radius) for every limb and trunk segment; spheres as a == b."""
    rig = bind_rig()
    out = []

    def seg(chain, owner, widths, scale=0.5):
        for k, bone in enumerate(chain.bones):
            m = mats[bone.name]
            a = (m @ np.array([*chain.rest[k], 1.0]))[:3]
            b = (m @ np.array([*chain.rest[k + 1], 1.0]))[:3]
            out.append((bone.name, owner, k, a, b, widths[k] * scale))

    seg(rig.trunk, "trunk", [w * 0.86 for w in s2.TRUNK_W], 0.42)
    for key, ch in rig.arms.items():
        seg(ch, "arm_" + key, ch.widths, 0.5)
    for side, ch in rig.legs.items():
        seg(ch, "leg_" + side, (9, 7, 6), 0.5)
    seg(rig.lroot, "lroot", (4, 4, 4), 0.5)
    heart = next(c for c in model.cubes if c.name == "heart")
    hc = (mats[heart.group.name] @ np.array([*((np.array(heart.frm) + heart.to) / 2), 1.0]))[:3]
    out.append(("lantern", "lantern", 0, hc, hc, 10.0))
    w = mats["womb"] @ np.array([*np.array(next(g for g in model.groups if g.name == "womb").origin), 1.0])
    out.append(("womb", "womb", 0, w[:3], w[:3], 12.0))
    return out


def seg_dist(a, b, c, d):
    """The closest distance between segments ab and cd."""
    u, v, w = b - a, d - c, a - c
    A, B, C, D, E = u @ u, u @ v, v @ v, u @ w, v @ w
    den = A * C - B * B
    s = clamp01((B * E - C * D) / den) if den > 1e-9 else 0.0
    t = (A * E - B * D) / den if den > 1e-9 else (E / C if C > 1e-9 else 0.0)
    t = clamp01(t) if C > 1e-9 else 0.0
    s = clamp01((t * B - D) / A) if A > 1e-9 else 0.0
    t = clamp01((s * B + E) / C) if C > 1e-9 else 0.0
    return float(np.linalg.norm((a + u * s) - (c + v * t)))


def skip(p, q):
    (_, o1, k1, *_), (_, o2, k2, *_) = p, q
    if o1 == o2:
        return o1 == "trunk" or abs(k1 - k2) <= 1
    pair = {o1, o2}
    if pair == {"lroot", "lantern"} or pair == {"lroot", "trunk"} or pair == {"womb", "trunk"}:
        return True
    if "trunk" in pair:                     # where a limb grows out of the trunk
        k = k1 if o1 != "trunk" else k2
        other = o1 if o1 != "trunk" else o2
        if other.startswith("arm_") and k <= 1:
            return True
        if other.startswith("leg_") and k == 0:
            return True
    if pair <= {"leg_right", "leg_left"} and min(k1, k2) == 0:
        return True
    if "womb" in pair and any(o.startswith("arm_") for o in pair):
        k = k1 if o1 != "womb" else k2
        return k == 0
    return False


def collisions(model, bones, length, tol=1.5):
    worst = []
    for t in np.arange(0, length + 1e-6, DT):
        caps = capsules(model, matrices(model, bones, float(t)))
        for i in range(len(caps)):
            for j in range(i + 1, len(caps)):
                p, q = caps[i], caps[j]
                if skip(p, q):
                    continue
                pen = p[5] + q[5] - seg_dist(p[3], p[4], q[3], q[4])
                if pen > tol:
                    worst.append((round(pen, 1), round(float(t), 2), p[0], q[0]))
    worst.sort(reverse=True)
    return worst


def pairs(hits):
    """The worst penetration per pair of parts, with when it happens."""
    out = {}
    for pen, t, a, b in hits:
        key = " / ".join(sorted((a, b)))
        if key not in out or pen > out[key][0]:
            out[key] = (pen, t)
    return dict(sorted(out.items(), key=lambda kv: -kv[1][0])[:12])


def floor(model, bones, length):
    low, where = 1e9, None
    for t in np.arange(0, length + 1e-6, DT):
        mats = matrices(model, bones, float(t))
        for c in model.cubes:
            if c.name.startswith(("hand_", "moss_")):
                continue
            m = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
            lo, hi = np.array(c.frm), np.array(c.to)
            pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
            y = float((m @ pts)[1].min())
            if y < low:
                low, where = y, (c.name, round(float(t), 2))
    return round(low, 1), where




# ---- lit GIFs -------------------------------------------------------------------------------------------------------------

FPS = 10
GIF_VIEW = {"location": (10, 15, 7.5), "target": (0, 0.5, 3.6), "scale": 15.0}


def tinted(atlas, masks, cols):
    img = np.array(atlas).astype(float)
    for zone, rgb in cols.items():
        img[masks[zone], :3] *= np.array(rgb) / 255
    return img


def frame_job(tag, i, t, model, bones, bb, atlas, masks, state, view):
    mats = matrices(model, bones, t)
    boxes = []
    for j, c in enumerate(model.cubes):
        m = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
        lo, hi = np.array(c.frm) - c.inflate, np.array(c.to) + c.inflate
        pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
        world = (m @ pts)[:3]
        if world[1].max() < -1:
            continue
        boxes.append({"corners": world.T.tolist(), "from": c.frm, "to": c.to, "glow": c.mat in s4.GLOWING,
                      "uv": bb["elements"][j]["faces"]})
    img = tinted(atlas, masks, state)
    tex = a6.save(img, OUT / "_tmp" / tag / f"atlas_{i:03d}.png")
    out = OUT / "_tmp" / tag / f"f{i:03d}"
    out.mkdir(parents=True, exist_ok=True)
    v = dict(view, name="frame", player=False, res=view.get("res", (760, 560)))
    job = out / "job.json"
    job.write_text(json.dumps({"texture": str(tex), "out": out.as_posix(), "boxes": boxes, "views": [v],
                               "translucent": True}), encoding="utf-8")
    r = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                        str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job)],
                       capture_output=True, text=True)
    if r.returncode or "TEXTURED_RENDER_DONE" not in r.stdout:
        raise SystemExit(r.stdout[-2000:] + r.stderr[-2000:])
    return out / "frame.png"


def gif(name, clip, bones, model, bb, atlas, masks):
    from bosses.heartwood_clips import STATE, VIEWS
    times = list(np.arange(0, clip.length - (1e-6 if clip.loop == "loop" else -1e-6), 1 / FPS))
    view = dict(GIF_VIEW, **VIEWS.get(name, {}))
    with ThreadPoolExecutor(max_workers=6) as pool:
        paths = list(pool.map(lambda it: frame_job(name, it[0], float(it[1]), model, bones, bb, atlas, masks,
                                                   STATE(name, float(it[1])), view), enumerate(times)))
    frames = [Image.open(p).convert("RGB") for p in paths]
    seq = frames + ([frames[-1]] * 6 if clip.loop != "loop" else [])
    pal = [f.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in seq]
    path = OUT / "lit" / f"heartwood_{name}.gif"
    path.parent.mkdir(parents=True, exist_ok=True)
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=int(1000 / FPS), loop=0, disposal=2)
    shutil.rmtree(OUT / "_tmp" / name, ignore_errors=True)
    return path


def main(argv):
    from bosses.heartwood_clips import CLIPS      # the clips themselves, kept apart (they import this module)
    OUT.mkdir(parents=True, exist_ok=True)
    only = [a for a in argv if a in CLIPS]
    model = s3.model()
    for c in model.cubes:
        if c.name.startswith("lantern_root"):
            c.mat = "bark_dark"
    clip_set, report = {}, {}
    for name, clip in CLIPS.items():
        if only and name not in only and "--no-gifs" in argv:
            continue
        bones = tracks(clip)
        clip_set[name] = (clip.length, clip.loop, bones)
        j = jumps(bones)
        step, err = interp_error(bones)
        hits = collisions(model, bones, clip.length)
        report[name] = {"length": clip.length, "loop": clip.loop, "contact": clip.contact,
                        "largest_step_deg": step[0], "step_bone": step[1], "step_at": step[2],
                        "interp_error_deg": err[0], "err_bone": err[1], "err_at": err[2],
                        "lowest": floor(model, bones, clip.length),
                        "collisions": len(hits), "worst": hits[:6], "pairs": pairs(hits)}
        print(name, json.dumps(report[name]), flush=True)
    (OUT / "clips.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if only and "--no-gifs" in argv:
        return
    from bosses import tempest_s7 as t7           # its exporter; it reads the assets folder (argv[-1]) on import
    t7.OVERRIDE = tuple(n for n in CLIPS if n not in ("idle", "walk"))
    t7._uuid = __import__("bosskit.bbmodel", fromlist=["_uuid"])._uuid
    rig = json.loads((s6.OUT / f"{s4.NAME}.bbmodel").read_text(encoding="utf-8"))
    rig["animations"] = t7.animations(s4.NAME, clip_set)
    p = OUT / f"{s4.NAME}.bbmodel"
    p.write_text(json.dumps(rig, separators=(",", ":")) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(p, s3.SERVER_MODELS / p.name)
    if "--no-gifs" in argv:
        return
    s6.neutral()
    atlas = np.array(Image.open(s6.OUT / f"{s4.NAME}.png")).astype(float)
    masks = s6.masks(atlas.shape[:2])
    bb = json.loads(p.read_text(encoding="utf-8"))
    for name in only or CLIPS:
        print("gif", gif(name, CLIPS[name], clip_set[name][2], model, bb, atlas, masks), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:-1] if len(sys.argv) > 1 and Path(sys.argv[-1]).is_dir() else sys.argv[1:])
