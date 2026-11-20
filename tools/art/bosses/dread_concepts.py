"""Dread Riders, session 1 (fresh start, 2026-11-20): three concepts, the warhorses first.

The user's brief (nothing from the earlier Dread Riders rounds carries over):
- the WAR HORSES are the main focus, and they are large;
- the riders' heads are vanilla's (the zombie's and the skeleton's) at a whole scale (2x, 16-unit heads), under
  helmets that fit a dark vanguard lancer (the Vanguard, zombie) and a cavalry archer-mage (the Outrider, skeleton);
- references: a fully barded black charger (spikes on the chanfron and crest, a boss on the chest, armoured boots, a
  banner behind the saddle) and an articulated bone horse (chunky bones, knobby joints, rope tack, a glowing eye).

Both horses keep vanilla's horse head at 2x (cranium 6x5x7, muzzle 4x5x5) on real horse proportions: legs as long as
the body is deep, a long neck carried high. The destrier stands ~3.4 blocks at the withers, the courser ~3.2.
Tier 3 palette: netherite-dark plate, old bone, hollow cyan (the Outrider's storm) and crimson (the Vanguard).

Model units: 16 = one block, y up, facing -z, the right side is +x.
Run from the repository root: python tools/art/bosses/dread_concepts.py [A] [B] [C] [vanguard] [outrider] [quick]
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
from bosses.monarch_s1 import ball, octo  # noqa: E402
from bosses.heartwood_s1 import _n, world  # noqa: E402
from bosses.heartwood_s2 import euler  # noqa: E402

OUT = ROOT / "docs/art/bosses/dread_riders/overhaul/s1_concepts"
PALETTE = {
    # the zombie destrier and the Vanguard
    "zhorse": (78, 98, 70), "zhorse_dark": (56, 70, 52), "hair": (34, 34, 32), "hoof": (44, 40, 38),
    "plate": (64, 58, 64), "plate_edge": (104, 96, 102), "plate_dark": (40, 36, 42), "crimson": (226, 44, 52),
    "cloth": (40, 34, 50), "trim": (138, 30, 36), "leather": (78, 56, 42), "wood": (84, 62, 46), "horn": (46, 40, 38),
    "horn_tip": (150, 140, 120), "chain": (88, 86, 92), "zskin": (98, 138, 74), "zface": (34, 50, 30),
    # the bone courser and the Outrider
    "bone": (218, 212, 194), "bone_dark": (168, 160, 140), "socket": (34, 34, 38), "cyan": (96, 236, 226),
    "rope": (136, 50, 46), "blanket": (110, 98, 92), "iron": (126, 126, 132), "iron_dark": (74, 74, 82),
    "skel": (196, 196, 192), "skel_dark": (60, 60, 62), "coat": (58, 70, 86), "coat_dark": (38, 46, 58),
    "mail": (112, 114, 120), "plume": (150, 34, 40), "gold": (176, 142, 74), "lamellar": (82, 84, 96),
}
REST, ACT = "rest", "act"


# ==== shape helpers ====================================================================================================

def fbox(g, name, center, e1, e2, size, mat):
    """A box with its x along e1, its y along e2 (made orthogonal to e1): size (along e1, along e2, across both)."""
    e1 = _n(e1)
    e2 = np.array(e2, float)
    e2 = _n(e2 - e1 * (e2 @ e1))
    e3 = np.cross(e1, e2)
    return g.box(name, tuple(np.array(center, float)), size, mat, rotation=tuple(euler(np.column_stack([e1, e2, e3]))))


def limb(g, name, a, b, w, d, mat, side=(1, 0, 0), extra=0.0):
    """A segment from a to b, w across (along `side`) and d deep; `extra` longer so joints overlap."""
    a, b = np.array(a, float), np.array(b, float)
    e1 = _n(b - a)
    sd = _n(side)
    e2 = _n(np.cross(sd, e1)) if abs(sd @ e1) < 0.95 else _n(np.cross([0, 0, 1.0], e1))
    return fbox(g, name, (a + b) / 2, e1, e2, (float(np.linalg.norm(b - a)) + extra, d, w), mat)


def perp(d):
    d = _n(d)
    a = _n(np.cross(d, [0, 1, 0]) if abs(d[1]) < 0.9 else np.cross(d, [1, 0, 0]))
    return a, np.cross(d, a)


def spike(g, name, base, d, length, width, mat, tip=None):
    """A tapering spike: two diamond-section boxes (the tip in `tip`, when given)."""
    d = _n(d)
    base = np.array(base, float)
    a, b = perp(d)
    e2 = (a + b) / math.sqrt(2)
    fbox(g, name + "_a", base + d * length * 0.3, d, e2, (length * 0.62, width, width), mat)
    fbox(g, name + "_b", base + d * length * 0.74, d, e2, (length * 0.52, width * 0.5, width * 0.5), tip or mat)


def strand(g, name, pts, w0, w1, mat, side=(1, 0, 0)):
    """A tapering chain of segments through pts."""
    n = len(pts) - 1
    for i in range(n):
        w = w0 + (w1 - w0) * i / max(1, n - 1)
        limb(g, f"{name}{i}", pts[i], pts[i + 1], w, w, mat, side=side, extra=w * 0.6)


def disc(g, name, c, normal, size, thick, mat):
    """A flat octagon: a square plus a 45-degree square (reads as a round guard at a distance)."""
    a, b = perp(normal)
    fbox(g, name + "_a", c, a, b, (size, size, thick), mat)
    fbox(g, name + "_b", c, (a + b), (b - a), (size * 0.83, size * 0.83, thick * 0.9), mat)


# ==== the horse frame ==================================================================================================

BUILDS = {
    # destrier: a heavy warhorse, 4.3 blocks at the withers; courser: taller in the leg, longer in the neck
    "destrier": dict(L=38, W=33, by=53, bh=33, nk=1.0, nd=((0, 16, -10), (0, 14, -6)), neckd=(28, 17),
                     front=(10, -11, 13), hind=(10, -9, -15), fsegs=(18, 13, 6), hsegs=(21, 15, 6), seat=28),
    "courser": dict(L=34, W=25, by=55, bh=27, nk=1.0, nd=((0, 14, -14), (0, 11, -10)), neckd=(20, 14),
                    front=(8, -11, 13), hind=(8.5, -8, -15), fsegs=(21, 15, 6), hsegs=(23, 17, 6), seat=26),
    # take 2 (2026-11-20, "more buff even though it's a skeleton"): a war-horse frame, a deep ribcage, heavy bones
    "courser_buff": dict(L=37, W=31, by=55, bh=32, nk=1.0, nd=((0, 15, -13), (0, 12, -9)), neckd=(24, 16),
                         front=(10, -12, 13), hind=(10.5, -9, -15), fsegs=(21, 15, 6), hsegs=(23, 17, 6), seat=28,
                         bone=1.5),
}
# joint angles from straight down, positive = forward (-z): upper, cannon, pastern
LEGS = {
    REST: {"fl": (0, 0, 28), "fr": (0, 0, 28), "hl": (-30, 4, 28), "hr": (-30, 4, 28)},
    "charge": {"fl": (58, 22, 62), "fr": (14, -82, -52), "hl": (-62, -52, -32), "hr": (8, 46, 72)},
    "snipe": {"fl": (34, -72, -34), "fr": (0, 0, 28), "hl": (-30, 4, 28), "hr": (-26, 2, 28)},
}


def chain(top, segs, angs):
    pts = [np.array(top, float)]
    for ln, a in zip(segs, angs):
        r = math.radians(a)
        pts.append(pts[-1] + np.array([0, -ln * math.cos(r), -ln * math.sin(r)]))
    return pts


def frame(kind, pose):
    b = BUILDS[kind]
    L, W, by, bh = b["L"], b["W"], b["by"], b["bh"]
    f = {"kind": kind, "b": b, "pose": pose}
    n0 = np.array([0, by + 7, -L + 8], float)
    if pose == "charge":
        mid = n0 + np.array([0, 14, -14]) * b["nk"]
        poll = mid + np.array([0, 10, -13]) * b["nk"]
        f["head_pitch"] = -30
    else:
        mid = n0 + np.array(b["nd"][0]) * b["nk"]
        poll = mid + np.array(b["nd"][1]) * b["nk"]
        f["head_pitch"] = -46 if kind == "destrier" else -40
    legs, grounded = {}, set()
    for key in ("fl", "fr", "hl", "hr"):
        s = -1 if key[1] == "l" else 1
        front = key[0] == "f"
        x, dy, dz = b["front"] if front else b["hind"]
        top = np.array([s * x, by + dy, (-L if front else L) + dz], float)
        segs = list(b["fsegs"] if front else b["hsegs"])
        angs = LEGS[pose][key]
        if pose != "charge" and not (pose == "snipe" and key == "fl"):
            r = [math.radians(a) for a in angs]
            segs[1] = (top[1] - segs[0] * math.cos(r[0]) - segs[2] * math.cos(r[2]) - 5) / math.cos(r[1])
            grounded.add(key)
        legs[key] = chain(top, segs, angs)
    bottoms = [p[-1][1] - 5 if k in grounded else p[-1][1] + _n(p[-1] - p[-2])[1] * 5 for k, p in legs.items()]
    shift = np.array([0, (3 if pose == "charge" else 0) - min(bottoms), 0])
    f.update({
        "by": by + shift[1], "L": L, "W": W, "bh": bh, "grounded": grounded,
        "barrel": np.array([0, by, 0.]) + shift, "chest": np.array([0, by, -L + 9.]) + shift,
        "rump": np.array([0, by + 2, L - 11.]) + shift, "withers": np.array([0, by + bh / 2, -L + 13.]) + shift,
        "neck": [n0 + shift, mid + shift, poll + shift],
        "legs": {k: [p + shift for p in v] for k, v in legs.items()},
        "tail": np.array([0, by + bh / 2 - 2, L + 1.]) + shift,
        "seat": np.array([0, by + bh / 2 + 1, -L + b["seat"]]) + shift,
    })
    return f




def neck_at(f, t):
    """A point on the neck's crest (t 0 base .. 1 poll), the crest's outward normal, the neck's direction there."""
    n0, mid, poll = f["neck"]
    nd = f["b"]["neckd"]
    if t < 0.5:
        a, b, u, d = n0, mid, t * 2, nd[0] + (nd[1] - nd[0]) * t
    else:
        a, b, u, d = mid, poll, t * 2 - 1, nd[0] + (nd[1] - nd[0]) * t
    e1 = _n(b - a)
    nrm = _n(np.cross([1, 0, 0], e1))
    k = 1.0 if f["kind"] == "destrier" else 0.6
    return a + (b - a) * u + nrm * d / 2 * k, nrm, e1


def horse_head(g, f, mat, muzzle_mat=None, ears=True):
    """Vanilla's horse head at 2x: cranium 12x10x14, muzzle 8x10x10, ears 4x6x2; pitched down off the poll."""
    poll = f["neck"][2]
    h = g.group("head", tuple(poll), (f["head_pitch"], 0, 0))
    P = np.array(poll)
    h.box("cranium", tuple(P + [0, -4, -7]), (12, 10, 14), mat)
    h.box("muzzle", tuple(P + [0, -4, -19]), (8, 10, 10), muzzle_mat or mat)
    h.box("jowl", tuple(P + [0, -9.5, -5]), (11, 4, 9), mat, rotation=(-10, 0, 0))
    if ears:
        for s in (-1, 1):
            h.box(f"ear{s}", tuple(P + [s * 3.5, 2, -2]), (4, 6, 2), mat, rotation=(62, 0, s * -12))
    return h, P


def flesh_legs(g, f, mat, hoof_mat, feather=None, wf=10, wc=7.5):
    for key, pts in f["legs"].items():
        front = key[0] == "f"
        w0 = wf if front else wf + 1
        limb(g, f"{key}_upper", pts[0] + [0, 6, 0], pts[1], w0, w0 + 1, mat)
        limb(g, f"{key}_cannon", pts[1], pts[2], wc, wc + 0.5, mat, extra=2)
        limb(g, f"{key}_pastern", pts[2], pts[3], wc - 0.5, wc, mat, extra=2)
        g.box(f"{key}_knee", tuple(pts[1] + ([0, 0, 0] if front else [0, 0, 1.5])), (wc + 1.5, wc + 1, wc + 2), mat)
        g.box(f"{key}_fetlock", tuple(pts[2]), (wc + 1, wc, wc + 1.5), mat)
        hoof(g, f, key, pts, hoof_mat, wc + 2.5)
        if feather:
            d = _n(pts[3] - pts[2])
            fbox(g, f"{key}_feather", pts[2] + d * 3 + [0, 0, 1], d, [0, 0, 1], (8, wc + 4, wc + 3), feather)


def hoof(g, f, key, pts, mat, w):
    if key in f["grounded"]:
        g.box(f"{key}_hoof", tuple(pts[3] + [0, -2.5, -1]), (w, 5, w + 1.5), mat)
    else:
        d = _n(pts[3] - pts[2])
        fbox(g, f"{key}_hoof", pts[3] + d * 2.5, d, np.cross([1, 0, 0], d), (5, w + 1.5, w), mat)


def oseg(g, name, a, b, w, d, mat, cham=0.3, extra=0.0):
    """A chamfered (octagonal) segment from a to b: w across x, d across the other side."""
    a, b = np.array(a, float), np.array(b, float)
    z = _n(b - a)
    x = _n(np.array([1.0, 0, 0]) - z * z[0])
    y = np.cross(z, x)
    return octo(g, name, tuple((a + b) / 2), (w, d, float(np.linalg.norm(b - a)) + extra), mat, cham,
                rot=tuple(euler(np.column_stack([x, y, z]))))


# the body's profile, front to back: z (x L), top (from the back line), bottom (from the belly line), half width (x W/2)
PROFILE = [(-1.06, -14, 4, 0.6), (-0.82, -6, 0, 0.9), (-0.52, 1, -1, 1.0), (-0.15, -2, 0, 1.04), (0.24, -1, 3, 1.0),
           (0.6, 0, 6, 1.04), (0.94, -6, 7, 0.86), (1.08, -13, 11, 0.5)]


def flesh_body(g, f, mat, dark):
    """A horse's body lofted along its profile: the breast, withers, a dip in the back, the croup sloping to the tail;
    the belly deepest at the girth, rising to the flank. Shoulder blades and haunches sit on the sides."""
    L, W, by, bh = f["L"], f["W"], f["by"], f["bh"]
    back, belly = by + bh / 2, by - bh / 2
    k = bh / 29
    st = [(z * L, back + t * k, belly + u * k, h * W / 2) for z, t, u, h in PROFILE]
    for i, (p, q) in enumerate(zip(st, st[1:])):
        w = (p[3] + q[3])
        hu = [(p[1] - p[2]) * 0.62, (q[1] - q[2]) * 0.62]
        oseg(g, f"body_top{i}", (0, p[1] - hu[0] / 2, p[0]), (0, q[1] - hu[1] / 2, q[0]), w, (hu[0] + hu[1]) / 2,
             mat, extra=2)
        oseg(g, f"body_low{i}", (0, p[2] + hu[0] / 2, p[0]), (0, q[2] + hu[1] / 2, q[0]), w * 0.94,
             (hu[0] + hu[1]) / 2, mat, extra=2)
    for s in (-1, 1):
        oseg(g, f"scapula{s}", (s * (W / 2 - 3.5), back - 3, -L + 16), (s * (W / 2 - 3), by - 5, -L + 5), 7, 13, mat)
        oseg(g, f"forearm_mass{s}", (s * (W / 2 - 3.5), by - 4, -L + 9), (s * (W / 2 - 4), by - 15, -L + 11), 10, 11, mat)
        oseg(g, f"haunch{s}", (s * (W / 2 - 2), back - 4, L - 18), (s * (W / 2 - 2.5), by - 6, L - 7), 8, 18, mat)


def neck_flesh(g, f, mat):
    """A tapered, arched neck: three chamfered segments and a crest along the top."""
    n0, mid, poll = f["neck"]
    NECK_D = f["b"]["neckd"]
    root = n0 + (n0 - mid) * 0.35
    W = f["W"]
    oseg(g, "neck0", root, n0 + (mid - n0) * 0.5, W * 0.5, NECK_D[0] + 2, mat)
    oseg(g, "neck1", n0 + (mid - n0) * 0.3, mid + (poll - mid) * 0.3, W * 0.41, (NECK_D[0] + NECK_D[1]) / 2, mat)
    oseg(g, "neck2", mid + (poll - mid) * 0.1, poll + (poll - mid) * 0.05, W * 0.34, NECK_D[1], mat)
    c0, n_0, _ = neck_at(f, 0.15)
    c1, n_1, _ = neck_at(f, 0.85)
    oseg(g, "crest", c0 - n_0 * 3, c1 - n_1 * 3, 8, 7, mat, extra=4)


def tail_points(f, flow):
    t = f["tail"]
    if f["pose"] == "charge":
        return [t, t + [0, 1, 7], t + [0, -1, 17], t + [0, -4, 28]]
    return [t, t + [0, -5, 4], t + [0 + flow, -17, 7], t + [flow * 1.5, -30, 6]]


# ==== the destrier (the Vanguard's zombie warhorse) ====================================================================

def destrier(g, f, take):
    flesh_body(g, f, "zhorse", "zhorse_dark")
    neck_flesh(g, f, "zhorse")
    h, P = horse_head(g, f, "zhorse")
    flesh_legs(g, f, "zhorse", "hoof", feather="hair" if take != "A" else None, wf=13, wc=10)
    if take == "bare":
        return
    # mane and tail: zombie horse hair
    for i in range(5):
        c, nrm, e1 = neck_at(f, 0.08 + i * 0.2)
        fbox(g, f"mane{i}", c + nrm * 0.5 + [3, -3, 0], e1, nrm, (6, 3, 3), "hair")
    strand(g, "tail", tail_points(f, 1.0), 7, 4, "hair")
    {"A": barding_spiked, "B": barding_scaled, "C": barding_horned}[take](g, h, P, f)
    saddle(g, f, take)


def chanfron(h, P, mat="plate", eye=True):
    h.box("chanfron_top", tuple(P + [0, 1.6, -7]), (13.4, 1.6, 14.5), mat)
    h.box("chanfron_nose", tuple(P + [0, 1.4, -19.5]), (9.4, 1.6, 11), mat)
    h.box("chanfron_ridge", tuple(P + [0, 2.6, -13]), (2.2, 1, 22), "plate_edge")
    for s in (-1, 1):
        # the cheek guard sits below the eye, so the eye stays open (session 5 review: it was covered)
        h.box(f"cheek{s}", tuple(P + [s * 6.8, -6.4, -10]), (1.4, 3.4, 11), mat)
        if eye:
            h.box(f"eye{s}", tuple(P + [s * 6.2, -2.6, -6.5]), (0.6, 2, 3), "crimson")
            h.box(f"brow{s}", tuple(P + [s * 7.0, 0.0, -6.5]), (1.6, 1.4, 6), "plate_edge", rotation=(0, 0, s * -20))


def barding_spiked(g, h, P, f):
    """A: the reference charger, our way: spikes fan from the poll and run up the crest, a boss on the chest, boots."""
    L, W, by, bh = f["L"], f["W"], f["by"], f["bh"]
    chanfron(h, P)
    # the fan of spikes at the poll (local +z = back/up once the head is pitched)
    for i, (dx, dy) in enumerate(((0, 0.25), (-0.55, 0.1), (0.55, 0.1), (-0.9, -0.15), (0.9, -0.15))):
        spike(h, f"poll_spike{i}", P + [dx * 3.5, 1.5, 1.8], [dx, 0.35 + dy, 1], 13 - abs(dx) * 4, 3.2, "plate", "plate_edge")
    spike(h, "brow_spike", P + [0, 2.4, -10], [0, 1, -0.35], 8, 2.6, "plate", "plate_edge")
    for s in (-1, 1):
        spike(h, f"brow_side{s}", P + [s * 7.6, 0.8, -4], [s, 0.3, 0.8], 7, 2.2, "plate", "plate_edge")
    # crinet: lames up the crest, one swept spike on each
    for i in range(5):
        c, nrm, e1 = neck_at(f, 0.06 + i * 0.2)
        fbox(g, f"crinet{i}", c + nrm * 1.2, e1, nrm, (8, 2, 13 - i * 0.6), "plate")
        spike(g, f"crest_spike{i}", c + nrm * 2, _n(nrm + [0, 0.6, 0.6]), 16 - i * 1.6, 3.6 - i * 0.2, "plate", "plate_edge")
    # peytral with a round boss, spikes along its lower rim
    front = -L - 0.5
    g.box("peytral", (0, by + 1, front), (W - 1, 20, 2.4), "plate", rotation=(-8, 0, 0))
    for s in (-1, 1):
        g.box(f"peytral_wing{s}", (s * (W / 2 - 0.5), by + 1, front + 7), (2.4, 19, 13), "plate", rotation=(-6, s * -24, 0))
    disc(g, "boss", (0, by + 2, front - 2), [0, 0.12, -1], 13, 2.4, "plate_edge")
    g.box("boss_sigil", (0, by + 2, front - 3.6), (3, 3, 1), "crimson", rotation=(0, 0, 45))
    for i in range(5):
        x = -10 + i * 5
        spike(g, f"peytral_spike{i}", (x, by - 8.5, front - 0.5), [x * 0.04, -0.25, -1], 8, 2.6, "plate", "plate_edge")
    # flanchards and the crupper over the rump
    for s in (-1, 1):
        g.box(f"flanchard{s}", (s * (W / 2 + 1.2), by + 1, -1), (2, 15, 20), "plate")
        g.box(f"crupper_side{s}", (s * (W / 2 + 1.6), by + 2, L - 11), (2.2, 17, 22), "plate", rotation=(0, 0, s * -4))
    g.box("crupper", (0, by + bh / 2 + 0.6, L - 11), (W + 3, 2.4, 22), "plate", rotation=(6, 0, 0))
    g.box("crupper_tail", (0, by + bh / 2 - 6, L + 0.4), (W - 2, 13, 2.2), "plate", rotation=(-12, 0, 0))
    for i in range(3):
        spike(g, f"crupper_spike{i}", (0, by + bh / 2 + 1.5, L - 18 + i * 7), [0, 1, 0.5], 7, 2.4, "plate", "plate_edge")
    # armoured boots (greaves over the cannons, a spiked knee cop, a sabaton on the hoof)
    for key, pts in f["legs"].items():
        d = _n(pts[2] - pts[1])
        limb(g, f"{key}_greave", pts[1] + d * 2, pts[2] + d * 1, 10.5, 11, "plate")
        g.box(f"{key}_cop", tuple(pts[1]), (11.5, 6, 11.5), "plate_edge")
        out = [0, 0, -1] if key[0] == "f" else [0, 0, 1]
        spike(g, f"{key}_cop_spike", pts[1] + np.array(out) * 5, _n(np.array(out) + [0, 0.2, 0]), 7, 2.6, "plate", "plate_edge")
        g.box(f"{key}_cuff", tuple(pts[2] + [0, -1.5, 0]), (11, 4, 12), "plate")
    banner(g, f)


def barding_scaled(g, h, P, f):
    """B: a cataphract's horse: a coat of lamellar to the knees (a heavy bell shape), a full mask with a tall plume."""
    L, W, by, bh = f["L"], f["W"], f["by"], f["bh"]
    charge = f["pose"] == "charge"
    chanfron(h, P)
    h.box("mask_back", tuple(P + [0, -3, 0.2]), (13.4, 10, 1.6), "plate")
    # the plume: black horsehair rising from the poll and falling back
    plume = [P + [0, 2, 1], P + [0, 7, 4], P + [0, 13, 9], P + [0, 15, 16], P + [0, 13, 22]]
    strand(h, "plume", plume, 5, 3, "hair")
    spike(h, "poll_spike", P + [0, 2, -3], [0, 1, 0.3], 7, 2.6, "plate", "plate_edge")
    # the neck sleeve: four bands
    for i in range(4):
        t0 = 0.05 + i * 0.24
        n0, mid, poll = f["neck"]
        a = n0 + (mid - n0) * min(1, t0 * 2) if t0 < 0.5 else mid + (poll - mid) * (t0 * 2 - 1)
        c, nrm, e1 = neck_at(f, t0 + 0.1)
        fbox(g, f"sleeve{i}", (a + c) / 2 + nrm * 1, e1, nrm, (8, 21 - i * 2, 16 - i * 1.2), "plate" if i % 2 else "plate_dark")
    # the coat over the body
    ball(g, "coat", tuple(f["barrel"] + [0, 1.5, 0]), (W + 3, bh + 1, 2 * L - 4), "plate")
    g.box("coat_spine", (0, by + bh / 2 + 2, 0), (5, 2, 2 * L - 10), "plate_edge")
    # the skirt: lamellar panels hanging to the knees and flaring out
    swing = -24 if charge else 0
    top_y = by - 2
    for s in (-1, 1):
        for i in range(7):
            z = -L + 6 + i * 9.6
            g.box(f"skirt{s}_{i}", (s * (W / 2 + 2.6), top_y - 8, z), (1.8, 18, 10.4),
                  "plate" if i % 2 else "plate_dark", rotation=(swing, 0, s * 10), origin=(s * (W / 2 + 1.5), top_y, z))
    for i in range(3):
        x = -9 + i * 9
        g.box(f"skirt_front{i}", (x, top_y - 6, -L - 2.6), (9.6, 16, 1.8), "plate_dark" if i % 2 else "plate",
              rotation=(-10 + swing * 0.5, 0, 0), origin=(x, top_y + 2, -L - 1))
        g.box(f"skirt_back{i}", (x, top_y - 4, L + 2.4), (9.6, 15, 1.8), "plate_dark" if i % 2 else "plate",
              rotation=(10 - swing * 0.2, 0, 0), origin=(x, top_y + 4, L + 1))
    g.box("chest_band", (0, by + 4, -L - 2.6), (W + 2, 3, 2), "plate_edge")


def barding_horned(g, h, P, f):
    """C: the dread horns: a horned skull mask, great spiked spaulders on the horse's shoulders, chains."""
    L, W, by, bh = f["L"], f["W"], f["by"], f["bh"]
    chanfron(h, P)
    # bull horns from the poll: out, up (local +z), and the tips forward (local +y)
    for s in (-1, 1):
        pts = [P + [s * 6, -1, -2], P + [s * 13, 1, 2], P + [s * 18, 5, 8], P + [s * 19, 12, 9], P + [s * 16, 17, 5]]
        strand(h, f"horn{s}_", pts, 6, 2.6, "horn")
        spike(h, f"horn{s}_tip", pts[-1], pts[-1] - pts[-2], 6, 2.4, "horn_tip")
    h.box("jaw_guard", tuple(P + [0, -9.4, -18]), (9.4, 1.6, 12), "plate")
    for k in range(4):
        h.box(f"jaw_tooth{k}", tuple(P + [-3 + k * 2, -10.6, -22.5]), (1, 2, 1), "plate_edge")
    # spaulders: three lames on each shoulder, a great spike from the top one
    for s in (-1, 1):
        for i in range(3):
            g.box(f"spaulder{s}_{i}", (s * (W / 2 + 1.5 + i * 1.4), by + 8 - i * 6, -L + 12 - i * 0.5),
                  (2.4, 8, 17 - i), "plate" if i % 2 == 0 else "plate_dark", rotation=(-10, 0, s * -(18 + i * 7)))
        spike(g, f"spaulder_spike{s}", (s * (W / 2 + 2), by + 11, -L + 12), [s * 0.9, 0.7, -0.5], 18, 4, "plate", "plate_edge")
        spike(g, f"spaulder_spike{s}b", (s * (W / 2 + 3), by + 6, -L + 18), [s * 1, 0.4, 0.2], 11, 3, "plate", "plate_edge")
    # the crinet: heavy plates with short spikes, the peytral as a ram's brow
    for i in range(4):
        c, nrm, e1 = neck_at(f, 0.1 + i * 0.25)
        fbox(g, f"crinet{i}", c + nrm * 1.2, e1, nrm, (9, 2.4, 14 - i), "plate")
        spike(g, f"crest_spike{i}", c + nrm * 2.4, _n(nrm + [0, 0, 0.5]), 7, 2.6, "plate", "plate_edge")
    g.box("peytral", (0, by + 2, -L - 0.5), (W - 2, 18, 3), "plate", rotation=(-8, 0, 0))
    g.box("peytral_brow", (0, by + 10, -L - 1.6), (W - 4, 4, 3), "plate_edge", rotation=(-8, 0, 0))
    g.box("peytral_eye", (0, by + 2, -L - 2.2), (3, 3, 1), "crimson", rotation=(0, 0, 45))
    # crupper with a row of spikes down the spine
    g.box("crupper", (0, by + bh / 2 + 0.6, L - 12), (W + 2, 2.4, 22), "plate", rotation=(6, 0, 0))
    for s in (-1, 1):
        g.box(f"crupper_side{s}", (s * (W / 2 + 1.4), by + 3, L - 12), (2.2, 15, 21), "plate")
    for i in range(4):
        spike(g, f"spine_spike{i}", (0, by + bh / 2 + 1.5, L - 22 + i * 6), [0, 1, 0.6], 8 - i, 2.6, "plate", "plate_edge")
    # spiked knee cops and hock spikes
    for key, pts in f["legs"].items():
        g.box(f"{key}_cop", tuple(pts[1]), (10.5, 6, 11), "plate")
        out = np.array([0, 0.25, -1] if key[0] == "f" else [0, 0.25, 1])
        spike(g, f"{key}_cop_spike", pts[1] + out * 5, out, 8, 2.8, "plate", "plate_edge")
    # chains looped along both flanks
    for s in (-1, 1):
        a, b = np.array([s * (W / 2 + 3.2), by + 8, -L + 18]), np.array([s * (W / 2 + 3.2), by + 8, L - 8])
        n = 11
        for k in range(n + 1):
            t = k / n
            p = a + (b - a) * t + [0, -10 * math.sin(math.pi * t), 0]
            g.box(f"chain{s}_{k}", tuple(p), (0.8 if k % 2 else 2.2, 2.2, 2.6), "chain",
                  rotation=(0, 0, 0) if k % 2 else (0, 0, 0))


def saddle(g, f, take):
    s = f["seat"]
    W, L = f["W"], f["L"]
    g.box("saddle_seat", tuple(s + [0, -0.5, 0]), (14, 3, 18), "leather")
    g.box("pommel", tuple(s + [0, 2, -9]), (11, 6, 3), "leather" if take != "C" else "plate", rotation=(-12, 0, 0))
    g.box("cantle", tuple(s + [0, 3.5, 9]), (15, 8, 3), "leather" if take != "C" else "plate", rotation=(14, 0, 0))
    if take != "B":
        g.box("saddle_cloth", tuple(s + [0, -2.3, 1]), (W + 5, 1.2, 24), "cloth")
        for k in (-1, 1):
            g.box(f"cloth_side{k}", (k * (W / 2 + 3.3), s[1] - 9, s[2] + 1), (1.2, 15, 24), "cloth")
            g.box(f"cloth_trim{k}", (k * (W / 2 + 3.5), s[1] - 16, s[2] + 1), (1.3, 1.6, 24.4), "trim")
    for k in (-1, 1):
        g.box(f"stirrup{k}", (k * (W / 2 + 6), s[1] - 22, s[2] - 4), (5, 1.4, 6), "iron_dark")


def banner(g, f):
    """The war banner on a pole behind the cantle; it hangs at rest and streams back in the charge."""
    s = f["seat"]
    base = s + [0, 0, 12]
    top = base + [0, 52, 4]
    limb(g, "banner_pole", base + [0, -8, 0], top, 2.4, 2.4, "wood")
    spike(g, "banner_finial", top, top - base, 9, 3, "plate", "plate_edge")
    if f["pose"] != "charge":
        g.box("banner_bar", tuple(top + [0, -6, 8]), (2, 2, 20), "plate_edge")
        for i, h in enumerate((30, 34, 31, 27)):
            z = top[2] + 1 + i * 4.6
            g.box(f"banner{i}", (top[0], top[1] - 7 - h / 2, z), (1, h, 4.8), "cloth", rotation=(0, (-10, 10)[i % 2], 0))
        g.box("banner_sigil", (top[0], top[1] - 21, top[2] + 8), (1.6, 7, 7), "trim", rotation=(45, 0, 0))
    else:
        for i in range(6):
            z = top[2] + 2 + i * 5.2
            sag = -i * 1.4
            g.box(f"banner{i}", (top[0] + (1.6 if i % 2 else -1.6), top[1] - 13 + sag, z), (1, 24 - i * 1.2, 5.6),
                  "cloth", rotation=(0, (-18, 18)[i % 2], 0))
        g.box("banner_sigil", (top[0], top[1] - 13, top[2] + 9), (2.6, 7, 7), "trim", rotation=(45, 0, 0))


# ==== the courser (the Outrider's bone horse) ==========================================================================

def back_line(f):
    L, by, bh = f["L"], f["by"], f["bh"]
    return [np.array(p, float) + [0, 0, 0] for p in (
        (0, by + bh / 2 - 1, -L + 9), (0, by + bh / 2, -L + 16), (0, by + bh / 2 - 2.5, 0),
        (0, by + bh / 2 - 1, L - 12), (0, by + bh / 2 - 3, L + 1))]


def courser(g, f, take):
    L, W, by, bh = f["L"], f["W"], f["by"], f["bh"]
    bone, dark = "bone", "bone_dark"
    kb = f["b"].get("bone", 1.0)          # bone thickness (the buff build's heavier bones)
    # the spine: vertebrae with processes, tallest over the withers
    line = back_line(f)
    k = 0
    for a, b in zip(line, line[1:]):
        n = max(1, int(np.linalg.norm(b - a) / 6))
        for i in range(n):
            p = a + (b - a) * (i + 0.5) / n
            g.box(f"vert{k}", tuple(p), (6 * kb, 5 * kb, 4.4), bone)
            hgt = max(2.5, 9 * kb - abs(p[2] - (-L + 15)) * 0.25)
            g.box(f"proc{k}", tuple(p + [0, hgt / 2 + 2 * kb, 0.6]), (2 * kb, hgt, 2.6), dark, rotation=(24, 0, 0))
            k += 1
    # the ribcage: thick ribs curving out and under, a sternum
    for i in range(6):
        z = -L + 10 + i * 6.2
        top_y = by + bh / 2 - 3.5
        wide = W / 2 * (0.78 + 0.22 * math.sin(math.pi * (i + 1) / 8)) * (1.06 if kb > 1 else 1)
        low = by - bh / 2 + 3 + i * 1.3
        for s in (-1, 1):
            pts = [np.array([s * 2.5, top_y, z]), np.array([s * wide, top_y - 5, z + 1]),
                   np.array([s * (wide + 0.5), (top_y + low) / 2 - 2, z + 2]), np.array([s * (wide - 3), low, z + 3])]
            if i < 5:
                pts.append(np.array([s * 2.5, low - 1.5, z + 3.5]))
            strand(g, f"rib{i}{'lr'[s > 0]}", pts, 4.2 * kb ** 0.6, 3.4 * kb ** 0.6, bone, side=(0, 0, 1))
    limb(g, "sternum", (0, by - bh / 2 + 1.5, -L + 7), (0, by - bh / 2 + 3, -L + 32), 5 * kb, 3 * kb, dark)
    if kb > 1:                              # a keel: the breastbone jutting forward between the shoulders
        limb(g, "keel", (0, by - bh / 2 + 3, -L + 10), (0, by - 2, -L - 1), 6, 8, bone)
    # shoulders: scapula plate and humerus; hips: pelvis, wings, femur
    for s in (-1, 1):
        sj = np.array([s * (W / 2 - 1.5), by - 1, -L + 7])
        limb(g, f"scapula{s}", (s * (W / 2 - 3.5), by + bh / 2 - 2, -L + 16), sj, 9 * kb, 2.6 * kb, bone,
             side=(0, 0, 1))
        g.box(f"shoulder_joint{s}", tuple(sj), (6 * kb, 6 * kb, 6 * kb), bone)
        limb(g, f"humerus{s}", sj, f["legs"]["fl" if s < 0 else "fr"][0], 5.5 * kb, 5.5 * kb, bone, extra=3)
        hj = np.array([s * (W / 2 - 2), by + 3, L - 12])
        g.box(f"hip_wing{s}", (s * (W / 2 - 2.5), by + bh / 2 - 4, L - 17), (6 * kb, 5 * kb, 7 * kb), bone)
        g.box(f"ischium{s}", (s * 4, by + 1, L - 3), (4 * kb, 8 * kb, 5 * kb), bone, rotation=(20, 0, 0))
        g.box(f"hip_joint{s}", tuple(hj), (6.5 * kb, 6.5 * kb, 6.5 * kb), bone)
        limb(g, f"femur{s}", hj, f["legs"]["hl" if s < 0 else "hr"][0], 6 * kb, 6 * kb, bone, extra=3)
    g.box("pelvis", (0, by + bh / 2 - 5, L - 12), (W - 7, 6 * kb, 16), bone, rotation=(-10, 0, 0))
    # legs: chunky bones and knobby joints
    for key, pts in f["legs"].items():
        front = key[0] == "f"
        k1, k2 = kb, kb ** 0.75             # shafts thicken with the build, joints a little less
        kc = kb ** 0.55                     # the cannon and pastern stay slimmer, so the legs taper
        limb(g, f"{key}_upper", pts[0], pts[1], 6.5 * k1, 7 * k1, bone, extra=2)
        limb(g, f"{key}_cannon", pts[1], pts[2], 5 * kc, 5.5 * kc, bone, extra=2)
        limb(g, f"{key}_pastern", pts[2], pts[3], 5 * kc, 5 * kc, bone, extra=2)
        g.box(f"{key}_elbow", tuple(pts[0]), (8 * k2 + 1, 8 * k2, 8 * k2), bone)
        g.box(f"{key}_knee", tuple(pts[1] + ([0, 0, 0] if front else [0, 0, 1.5])), (8.5 * k2 + 1, 8 * k2, 8.5 * k2), bone)
        g.box(f"{key}_fetlock", tuple(pts[2]), (7.5 * kc + 1, 6.5 * kc, 7.5 * kc), bone)
        hoof(g, f, key, pts, dark, 8 * k2 + 1)
    # the neck: vertebrae along the curve, a ligament up the crest
    n0, mid, poll = f["neck"]
    for i in range(6):
        t = (i + 0.5) / 6
        p = n0 + (mid - n0) * min(1, t * 2) if t < 0.5 else mid + (poll - mid) * (t * 2 - 1)
        d = _n(mid - n0) if t < 0.5 else _n(poll - mid)
        fbox(g, f"neck_vert{i}", p, d, np.cross([1, 0, 0], d), (5.6 * kb ** 0.7, (7 - i * 0.4) * kb, (7 - i * 0.6) * kb), bone)
        fbox(g, f"neck_proc{i}", p + np.cross([1, 0, 0], d) * 4.5 * kb, d, np.cross([1, 0, 0], d),
             (2.4, 4 * kb, 2 * kb), dark)
    # the skull: vanilla's horse head at 2x as bone, the jaw hanging a little open, the sockets lit
    h = g.group("head", tuple(poll), (f["head_pitch"], 0, 0))
    P = np.array(poll)
    h.box("cranium", tuple(P + [0, -4, -7]), (12, 10, 14), bone)
    h.box("muzzle", tuple(P + [0, -1.5, -19]), (8, 5, 10), bone)
    h.box("jaw", tuple(P + [0, -7.5, -16]), (7, 3, 16), bone, rotation=(6, 0, 0), origin=tuple(P + [0, -7, -8]))
    h.box("nasal", tuple(P + [0, -1.5, -24.1]), (4, 2.4, 0.4), "socket")
    if kb > 1:
        h.box("jaw_heavy", tuple(P + [0, -9.6, -9]), (10, 4, 10), bone, rotation=(6, 0, 0), origin=tuple(P + [0, -7, -8]))
        for s in (-1, 1):
            h.box(f"cheekbone{s}", tuple(P + [s * 6.6, -5.5, -10]), (1.6, 2.4, 9), dark)
    for k2 in range(4):
        h.box(f"tooth{k2}", tuple(P + [-3 + k2 * 2, -4.6, -22]), (1, 1.6, 1), dark)
    for s in (-1, 1):
        h.box(f"socket{s}", tuple(P + [s * 5.85, -2.4, -6.5]), (0.6, 4, 4.4), "socket")
        h.box(f"eye{s}", tuple(P + [s * 6.05, -2.4, -6.5]), (0.5, 1.6, 1.6), "cyan")
        h.box(f"ear{s}", tuple(P + [s * 3.5, 2, -2]), (4, 6, 2), dark, rotation=(62, 0, s * -12))
    if take == "bare":
        return
    {"A": tack_rope, "B": tack_iron, "C": tack_storm}[take](g, h, P, f)
    saddle_light(g, f, take)


def tack_rope(g, h, P, f):
    """A: the reference bone horse, our way: a saddle blanket and red rope lashings, a dark horsehair tail."""
    L, W, by, bh = f["L"], f["W"], f["by"], f["bh"]
    s = f["seat"]
    g.box("blanket", tuple(s + [0, -2.2, 1]), (W + 4, 1.2, 26), "blanket")
    for k in (-1, 1):
        for i in range(4):
            g.box(f"blanket{k}_{i}", (k * (W / 2 + 2.6), s[1] - 9 - (i % 2) * 1.5, s[2] - 9 + i * 6.6),
                  (1.2, 15 + (i % 2) * 3, 6.4), "blanket", rotation=(0, 0, k * -4))
        # the girth rope round the ribcage and a crossed lashing over the blanket
        limb(g, f"girth{k}", (k * (W / 2 + 3.4), s[1] - 2, s[2] - 6), (k * (W / 2 - 1), by - bh / 2 + 4, s[2] - 4),
             1.4, 1.4, "rope")
        limb(g, f"lash{k}", (k * (W / 2 + 3.5), s[1] - 2, s[2] - 10), (k * (W / 2 + 3.5), s[1] - 17, s[2] + 10),
             1.3, 1.3, "rope", side=(0, 0, 1))
    limb(g, "girth_under", (-(W / 2 - 1), by - bh / 2 + 4, s[2] - 4), ((W / 2 - 1), by - bh / 2 + 4, s[2] - 4),
         1.4, 1.4, "rope", side=(0, 0, 1))
    for k in (-1, 1):
        h.box(f"halter{k}", tuple(P + [k * 4.4, -3, -16]), (0.8, 6.4, 1.2), "rope")
    h.box("halter_nose", tuple(P + [0, 0.8, -16]), (9, 0.8, 1.2), "rope")
    strand(g, "tail_hair", tail_points(f, 0.0), 5, 3, "hair")
    for i in range(3):
        p = f["tail"] + [0, -1.5 * i, 2.5 * i]
        g.box(f"tail_vert{i}", tuple(p), (4 - i, 4 - i, 3), "bone")


def tack_iron(g, h, P, f):
    """B: the ironbound: the bones held together with dark iron: bands, a muzzle cage, shoes, chain reins."""
    L, W, by, bh = f["L"], f["W"], f["by"], f["bh"]
    for key, pts in f["legs"].items():
        for j, (a, b) in enumerate(((pts[0], pts[1]), (pts[1], pts[2]))):
            m = (a + b) / 2
            limb(g, f"{key}_band{j}", m - _n(b - a) * 1.5, m + _n(b - a) * 1.5, 6.4, 6.8, "iron_dark")
        if key in f["grounded"]:
            g.box(f"{key}_shoe", tuple(pts[3] + [0, -4.6, -1]), (9.4, 1.8, 10.4), "iron")
    h.box("cap", tuple(P + [0, 1.6, -7]), (13, 1.6, 12), "iron_dark")
    h.box("cap_ridge", tuple(P + [0, 2.6, -8]), (2, 1.2, 12), "iron")
    for k in range(3):
        h.box(f"cage{k}", tuple(P + [0, -4, -15 - k * 4]), (9.6, 11.6, 1.2), "iron_dark")
    h.box("cage_top", tuple(P + [0, 1.6, -19]), (2, 1.2, 10), "iron_dark")
    for s in (-1, 1):
        g.box(f"rib_strap{s}", (s * (W / 2 + 1.2), by + 2, -L + 24), (1.6, 3, 34), "iron_dark")
        g.box(f"quiver_case{s}", (s * (W / 2 + 4), by + 2, f["seat"][2] + 10), (4, 20, 6), "leather",
              rotation=(-30, 0, 0)) if s > 0 else None
    g.box("collar", tuple(f["neck"][0] + [0, 1, 1]), (16, 4, 18), "iron_dark", rotation=(-40, 0, 0))
    for i in range(3):
        p = f["tail"] + [0, -1.5 * i, 2.5 * i]
        g.box(f"tail_vert{i}", tuple(p), (4 - i, 4 - i, 3), "bone")
    g.box("tail_ring", tuple(f["tail"] + [0, -3, 5]), (4, 4, 1.6), "iron")
    strand(g, "tail_hair", tail_points(f, 0.0)[1:], 4, 2.5, "hair")


def tack_storm(g, h, P, f):
    """C: the storm steed: a mane and tail of lightning, a storm caught in the ribcage, sparks at the hooves."""
    L, W, by, bh = f["L"], f["W"], f["by"], f["bh"]
    for i in range(4):
        c, nrm, e1 = neck_at(f, 0.08 + i * 0.27)
        up = _n(nrm + [0, 0.9, 0.7])
        p0 = c + nrm * 3
        p1 = p0 + up * 6 + e1 * 2.5
        p2 = p1 + up * 4 - e1 * 3
        p3 = p2 + up * (7 - i) + e1 * 2
        for j, (a2, b2) in enumerate(((p0, p1), (p1, p2), (p2, p3))):
            limb(g, f"bolt_mane{i}_{j}", a2, b2, 1, 3.4 - j * 0.8, "cyan", extra=1.5)
    t = f["tail"]
    pts = [t, t + [0, 3, 7], t + [0, -5, 11], t + [0, 1, 18], t + [0, -8, 22], t + [0, -3, 30]]
    if f["pose"] != "charge":
        pts = [t, t + [0, -2, 6], t + [0, -10, 4], t + [0, -14, 10], t + [0, -23, 7], t + [0, -28, 12]]
    for i in range(len(pts) - 1):
        limb(g, f"bolt_tail{i}", pts[i], pts[i + 1], 3.2, 1, "cyan", extra=1)
    ball(g, "storm", tuple(f["barrel"] + [0, 1, -9]), (9, 9, 9), "cyan")
    for i, d in enumerate(([1, 0.5, 0.2], [-1, 0.3, -0.3], [0.6, -1, 0.4], [-0.5, -0.8, -0.6])):
        a = f["barrel"] + [0, 1, -9]
        limb(g, f"arc{i}", a + _n(d) * 4, a + _n(d) * 11 + [0, (i % 2) * 2, 0], 1, 1, "cyan")
    for key, pts in f["legs"].items():
        if key in f["grounded"]:
            for j, (dx, dz) in enumerate(((5, -4), (-5, 2))):
                g.box(f"{key}_spark{j}", tuple(pts[3] + [dx, -3.5, dz]), (0.8, 3, 0.8), "cyan", rotation=(0, 0, 30 * (j * 2 - 1)))


def saddle_light(g, f, take):
    s = f["seat"]
    W = f["W"]
    g.box("saddle_seat", tuple(s + [0, -0.6, 0]), (13, 2.6, 16), "leather" if take != "B" else "iron_dark")
    g.box("pommel", tuple(s + [0, 1.6, -8]), (8, 4, 2.4), "leather", rotation=(-14, 0, 0))
    g.box("cantle", tuple(s + [0, 2.4, 8]), (12, 5, 2.4), "leather", rotation=(14, 0, 0))
    if take == "C":
        g.box("saddle_rune", tuple(s + [0, -0.6, 0]), (13.4, 1, 3), "cyan")
    for k in (-1, 1):
        g.box(f"stirrup{k}", (k * (W / 2 + 5), s[1] - 21, s[2] - 4), (4, 1.2, 5), "iron_dark")


# ==== the riders (vanilla zombie / skeleton at 2x) =====================================================================

ARMS = {
    # torso-local offsets from the hip: (elbow, hand) per side
    ("vanguard", REST): {1: ((13, 10, -4), (12, 4, -12)), -1: ((-13, 10, -5), (-6, 6, -16))},
    ("vanguard", "charge"): {1: ((15, 13, 5), (12, 12, -5)), -1: ((-12, 12, -8), (-5, 9, -18))},
    ("outrider", REST): {-1: ((-11, 10, -2), (-11, 2, -9)), 1: ((11, 10, 1), (8, 3, -8))},
    ("outrider", "snipe"): {-1: ((-10, 23, -10), (-8, 24, -21)), 1: ((12, 25, 7), (3, 27, -4))},
}


def rider(g, f, kind, take, helm=None):
    pose = f["pose"]
    zombie = kind == "vanguard"
    s = f["seat"]
    W = f["W"]
    hip = s + [0, 3, 1]
    lw = 8 if zombie else 4
    legmat = "plate" if zombie else ("coat" if take == "B" else "skel")
    for k in (-1, 1):
        a, kn = hip + [k * 4, 0, 0], hip + [k * (W / 2 + lw / 2 + 1.5), -7, -9]
        an = hip + [k * (W / 2 + lw / 2 + 2), -20, -5]
        limb(g, f"thigh{k}", a, kn, lw, lw, legmat, extra=lw * 0.5)
        limb(g, f"shin{k}", kn, an, lw, lw, legmat if zombie else "skel", extra=lw * 0.5)
        g.box(f"foot{k}", tuple(an + [0, -1.5, -2]), (lw + 1, 3, lw + 5), "plate_dark" if zombie else "leather")
    lean = {REST: 0, "charge": -16, "snipe": -4}[pose]
    t = g.group("torso", tuple(hip), (lean, 0, 0))
    body = {"vanguard": "plate", "outrider": "skel"}[kind]
    t.box("torso", tuple(hip + [0, 12, 0]), (16, 24, 8), body if not zombie else "zskin")
    hd = t.group("headbone", tuple(hip + [0, 24, 0]), (0, 0, 0))
    hc = hip + [0, 32, 0]
    vanilla_head(hd, hc, zombie)
    aw = 8 if zombie else 4
    hands = {}
    for side, (el, hand) in ARMS[(kind, pose)].items():
        sh = hip + [side * (8 + aw / 2), 22, 0]
        el, hand = hip + np.array(el, float), hip + np.array(hand, float)
        armmat = "plate" if zombie else ("coat" if take == "B" else "skel")
        limb(t, f"arm{side}_upper", sh, el, aw, aw, armmat, extra=aw * 0.5)
        limb(t, f"arm{side}_fore", el, hand, aw, aw, "plate_dark" if zombie else "skel", extra=aw * 0.5)
        hands[side] = hand
    if zombie:
        vanguard_gear(t, hd, hip, hc, take, pose, hands, helm or take)
    else:
        outrider_gear(t, hd, hip, hc, take, pose, hands, helm or take)
    return hc, lean, hip


def vanilla_head(hd, hc, zombie):
    """The vanilla head at 2x, face on -z (the face pattern blocked in as thin boxes)."""
    hd.box("head", tuple(hc), (16, 16, 16), "zskin" if zombie else "skel")
    fz = hc[2] - 8.15
    if zombie:
        for k in (-1, 1):
            hd.box(f"eye{k}", (hc[0] + k * 4, hc[1] - 1, fz), (4, 2, 0.4), "zface")
        hd.box("mouth", (hc[0], hc[1] - 5, fz), (8, 2, 0.4), "zface")
    else:
        for k in (-1, 1):
            hd.box(f"eye{k}", (hc[0] + k * 4, hc[1] + 0, fz), (4, 4, 0.4), "skel_dark")
        hd.box("nose", (hc[0], hc[1] - 3, fz), (4, 2, 0.4), "skel_dark")
        hd.box("mouth", (hc[0], hc[1] - 5, fz), (12, 2, 0.4), "skel_dark")


def cap(hd, hc, mat, rim, low=-3.0, dome=True):
    """A helmet bowl worn ON the vanilla head: it covers the crown, the sides behind the face and the back of the skull,
    and stops at the brow (y + 3.3), so the face pattern (eyes, nose, mouth) stays bare."""
    x, y, z = hc
    if dome:
        ball(hd, "bowl", (x, y + 7.6, z + 0.4), (18.6, 7.4, 18.6), mat, cham=0.35)
    else:
        hd.box("bowl", (x, y + 7.6, z + 0.4), (18.6, 7.4, 18.6), mat)
    h = 8 - low
    for k in (-1, 1):
        hd.box(f"cap_side{k}", (x + k * 9.2, y + (8 + low) / 2, z + 2.5), (2.2, h, 14), mat)
    hd.box("cap_back", (x, y + (8 + low) / 2 - 1, z + 9.2), (18.6, h + 2, 2.2), mat)
    hd.box("cap_rim", (x, y + 4.6, z - 8.8), (18.8, 2.6, 2), rim)


def vanguard_gear(t, hd, hip, hc, take, pose, hands, helm):
    charge = pose == "charge"
    # armour
    t.box("breastplate", tuple(hip + [0, 15, -0.5]), (18, 15, 11), "plate")
    t.box("breast_ridge", tuple(hip + [0, 15, -6.2]), (2, 13, 1), "plate_edge")
    t.box("faulds", tuple(hip + [0, 5, -0.5]), (19, 6, 11.5), "plate_dark")
    if take == "A":
        for k in (-1, 1):
            t.box(f"pauldron{k}", tuple(hip + [k * 13, 24, 0]), (11, 4, 12), "plate", rotation=(0, 0, k * -22))
            spike(t, f"pauldron_spike{k}", hip + [k * 14, 26, 0], [k * 0.4, 1, 0.2], 9, 2.6, "plate", "plate_edge")
    elif take == "B":
        for k in (-1, 1):
            for i in range(3):
                t.box(f"pauldron{k}_{i}", tuple(hip + [k * (12 + i * 1.2), 24 - i * 3.6, 0]), (10, 3, 12 - i),
                      "plate" if i % 2 == 0 else "plate_dark", rotation=(0, 0, k * -(14 + i * 8)))
    else:
        for k in (-1, 1):
            t.box(f"pauldron{k}", tuple(hip + [k * 13.5, 23.5, 0]), (12, 6, 13), "plate", rotation=(0, 0, k * -16))
            spike(t, f"pauldron_spike{k}", hip + [k * 16, 25, 0], [k * 1, 0.6, 0], 9, 3, "plate", "plate_edge")
    vanguard_helm(hd, hc, helm)
    # the lance
    r = hands[1]
    if charge:
        axis = _n([-0.12, 0.04, -1])
        lance(t, r, axis, 108, 20, take)
    else:
        lance(t, r, _n([0.14, 0.78, -0.62]), 74, 24, take)
    limb(t, "rein", hands[-1], hands[-1] + [3, -6, -14], 0.8, 0.8, "leather")


def vanguard_helm(hd, hc, helm):
    x, y, z = hc
    if helm == "A":
        # a spiked sallet: a bowl to the brow, a short peak, a long tail over the nape, a crest of swept spikes
        cap(hd, hc, "plate", "plate_edge", low=-4)
        hd.box("peak", (x, y + 3.8, z - 11), (17, 1.4, 5), "plate_edge", rotation=(-8, 0, 0))
        hd.box("tail", (x, y - 1.5, z + 14), (17, 2, 11), "plate", rotation=(28, 0, 0))
        for i, (dz, ln) in enumerate(((-6, 9), (-1.5, 12), (3, 11), (7.5, 8))):
            spike(hd, f"helm_spike{i}", (x, y + 10.5, z + dz), [0, 1, 0.55], ln, 3.2, "plate", "plate_edge")
        hd.box("bevor", (x, y - 9.6, z - 3), (17, 3.4, 12), "plate")
    elif helm == "B":
        # a burgonet: a peak shading the eyes, an arched comb, hinged cheek pieces, a flared neck guard
        cap(hd, hc, "plate", "plate_edge", low=-6)
        hd.box("peak", (x, y + 4, z - 12), (16, 1.4, 7), "plate_edge", rotation=(-10, 0, 0))
        for i, (dz, hh, ln) in enumerate(((-5.5, 3, 7), (0.5, 5, 7), (6.5, 3, 7))):
            hd.box(f"comb{i}", (x, y + 11 + hh / 2, z + dz), (2, hh, ln), "plate_edge", rotation=((i - 1) * -14, 0, 0))
        hd.box("comb_crest", (x, y + 16.4, z + 0.5), (1.4, 1.2, 8), "crimson")
        for k in (-1, 1):
            hd.box(f"cheek{k}", (x + k * 9.8, y - 4, z - 5), (2, 10, 7), "plate", rotation=(0, k * -10, 0))
        hd.box("neck_guard", (x, y - 6, z + 12), (18, 7, 2), "plate", rotation=(34, 0, 0))
    else:
        # a horned armet: a bowl, a raised ridge, a bevor below the mouth, horns that echo the horse's
        cap(hd, hc, "plate", "plate_edge", low=-5)
        hd.box("bevor", (x, y - 9.4, z - 2), (18.4, 4, 14), "plate")
        hd.box("bevor_lip", (x, y - 7.8, z - 9.2), (18.4, 1.6, 1.4), "plate_edge")
        for k in (-1, 1):
            pts = [np.array([x + k * 9, y + 5, z]), np.array([x + k * 14, y + 7, z + 1]),
                   np.array([x + k * 17, y + 12, z]), np.array([x + k * 16, y + 17, z - 3])]
            strand(hd, f"helm_horn{k}_", pts, 4, 2, "horn")
            spike(hd, f"helm_horn{k}_tip", pts[-1], pts[-1] - pts[-2], 4, 1.8, "horn_tip")
        hd.box("ridge", (x, y + 11.6, z), (2, 2, 17), "plate_edge")


def lance(t, hand, axis, length, back, take):
    a, b = perp(axis)
    butt, tip = hand - axis * back, hand + axis * length
    limb(t, "lance_butt", butt, hand + axis * 4, 3.6, 3.6, "wood")
    limb(t, "lance_shaft", hand + axis * 4, tip, 2.8, 2.8, "wood")
    limb(t, "lance_grip", hand - axis * 4, hand + axis * 4, 4.4, 4.4, "leather")
    if take == "A":
        disc(t, "vamplate", hand + axis * 7, axis, 13, 1.6, "plate")
        for i, d in enumerate((a, -a, b, -b)):
            spike(t, f"vamplate_spike{i}", hand + axis * 7 + d * 5, d * 0.6 + axis, 6, 1.8, "plate", "plate_edge")
        spike(t, "lance_head", tip, axis, 26, 4.6, "plate", "plate_edge")
    elif take == "B":
        limb(t, "socket", tip - axis * 2, tip + axis * 5, 3.6, 3.6, "plate")
        fbox(t, "blade", tip + axis * 14, axis, a, (20, 6.5, 1.4), "plate_edge")
        fbox(t, "blade_tip", tip + axis * 25, axis, a, (6, 3.2, 1.2), "plate_edge")
        for i in range(3):
            limb(t, f"wrap{i}", hand + axis * (16 + i * 6), hand + axis * (17.5 + i * 6), 3.6, 3.6, "trim")
    else:
        limb(t, "socket", tip - axis * 2, tip + axis * 6, 4, 4, "plate")
        spike(t, "lance_head", tip + axis * 4, axis, 22, 5, "plate", "plate_edge")
        for k in (-1, 1):
            spike(t, f"barb{k}", tip + axis * 8 + a * k * 1.5, -axis + a * k * 0.9, 9, 2.2, "plate", "plate_edge")
        for i in range(6):
            p = hand + axis * (10 + i * 3.2) + a * (2 if i % 2 else -2)
            t.box(f"lance_chain{i}", tuple(p), (2, 2, 2), "chain")


def outrider_gear(t, hd, hip, hc, take, pose, hands, helm):
    snipe = pose == "snipe"
    x, y, z = hc
    # the archer's dress
    if take == "A":
        t.box("jerkin", tuple(hip + [0, 13, 0]), (17, 18, 9), "leather")
        t.box("cape", tuple(hip + [0, 14, 6]), (18, 22, 1.4), "coat_dark", rotation=(10, 0, 0))
    elif take == "B":
        t.box("kaftan", tuple(hip + [0, 13, 0]), (17, 22, 9), "coat")
        t.box("sash", tuple(hip + [0, 6, 0]), (17.6, 3, 9.6), "plume")
        for k in (-1, 1):
            t.box(f"coat_tail{k}", tuple(hip + [k * 6, -6, 6]), (7, 16, 1.4), "coat", rotation=(20, 0, k * -10))
    else:
        t.box("robe", tuple(hip + [0, 13, 0]), (17, 22, 9), "coat_dark")
        t.box("mantle", tuple(hip + [0, 22, 0.5]), (22, 5, 12), "coat")
        t.box("mantle_rune", tuple(hip + [0, 19.6, -5.6]), (18, 1.2, 1), "cyan")
        t.box("cape", tuple(hip + [0, 10, 6]), (20, 28, 1.4), "coat", rotation=(14, 0, 0))
    t.box("quiver", tuple(hip + [5, 18, 6]), (5, 18, 5), "leather", rotation=(0, 0, -24))
    for i in range(3):
        t.box(f"fletch{i}", tuple(hip + [8.5 + i * 0.6, 28.5 + i * 0.4, 6 + (i - 1) * 1.4]), (1.6, 4, 1.2), "bone",
              rotation=(0, 0, -24))
    # helmets
    if helm == "A2":
        steppe_helm(hd, hc)
    elif helm == "A":
        # a steppe helm: a bowl and a four-plate spire, a brow band, a mail aventail, a horsehair plume
        cap(hd, hc, "iron", "gold", low=-1, dome=False)
        for k, (nx, nz) in enumerate(((0, -1), (0, 1), (-1, 0), (1, 0))):
            hd.box(f"spire{k}", (x + nx * 5.2, y + 13, z + nz * 5.2), (18 if nz else 1.6, 10, 1.6 if nz else 18),
                   "iron", rotation=(nz * 32, 0, -nx * 32))
        hd.box("spire_cap", (x, y + 17.6, z), (5, 3, 5), "iron")
        limb(hd, "spike", (x, y + 18, z), (x, y + 25, z), 1.6, 1.6, "iron")
        strand(hd, "plume", [np.array([x, y + 24, z]), np.array([x, y + 25, z + 5]), np.array([x, y + 21, z + 11]),
                             np.array([x, y + 15, z + 14])], 2.6, 1.6, "plume")
        hd.box("aventail_back", (x, y - 7, z + 10.4), (19, 14, 1.6), "mail")
        for k in (-1, 1):
            hd.box(f"aventail{k}", (x + k * 10.4, y - 6, z + 1.5), (1.6, 13, 16), "mail")
    elif helm == "B":
        # a chichak: a fluted dome, a peak, a raised nasal, lamellar neck guard and a trailing scarf
        cap(hd, hc, "iron", "gold", low=-2)
        ball(hd, "dome", (x, y + 11, z + 0.4), (14, 6, 14), "iron", cham=0.4)
        hd.box("finial", (x, y + 16, z), (2.6, 5, 2.6), "gold")
        hd.box("peak", (x, y + 4.2, z - 11), (14, 1.2, 5.4), "iron", rotation=(-14, 0, 0))
        hd.box("nasal", (x, y + 10, z - 9.9), (1.6, 9, 1.2), "gold", rotation=(-10, 0, 0))
        for k in (-1, 1):
            hd.box(f"cheek{k}", (x + k * 9.8, y - 3, z - 4), (1.6, 10, 7), "iron")
        for i in range(3):
            hd.box(f"neck_lame{i}", (x, y + 1 - i * 3.6, z + 9.8 + i * 0.6), (18, 3.4, 1.6), "iron" if i % 2 else "iron_dark")
        strand(hd, "scarf", [np.array([x - 5, y + 5, z + 9]), np.array([x - 7, y - 4, z + 15]),
                             np.array([x - 6, y - 14, z + 19]), np.array([x - 8, y - 24, z + 20])], 4.4, 3, "plume")
    else:
        # the storm-caller: an open bascinet with fins at the temples and a forked lightning rod that glows
        cap(hd, hc, "iron_dark", "iron", low=-3)
        limb(hd, "rod", (x, y + 13, z + 2), (x, y + 30, z + 5), 1.8, 1.8, "iron")
        for k in (-1, 1):
            limb(hd, f"fork{k}", (x, y + 29, z + 5), (x + k * 3.2, y + 34, z + 6), 1.2, 1.2, "iron")
            hd.box(f"fork_glow{k}", (x + k * 3.4, y + 34.4, z + 6), (1.6, 1.6, 1.6), "cyan")
            fbox(hd, f"fin{k}", (x + k * 10.4, y + 7, z + 3), [0.2 * k, 0.7, 1], [k, 0, 0], (16, 1.2, 7), "iron")
        hd.box("brow_rune", (x, y + 4.6, z - 9.9), (8, 1.4, 0.6), "cyan")
    # the bow
    lh, rh = hands[-1], hands[1]
    if snipe:
        bow(t, lh, _n([0.18, 1, 0]), _n([0, 0, -1]), rh, take)
    else:
        bow(t, lh, _n([0, 1, 0.12]), _n([0, 0, -1]), None, take)


def steppe_helm(hd, hc):
    """Take 2 of A's steppe helm (the first read as a bowl on the head): no bowl. An iron band hugs the head from the
    brow to the crown, and an eight-sided cone rises straight off it in three tiers to a spike, ribbed in gold like a
    spangenhelm; a gold rim at the brow, a mail aventail hanging from the band over the neck and shoulders, a red
    horsehair plume falling from the spike."""
    x, y, z = hc
    c = np.array(hc, float)
    # the band: flush on the head (one unit proud), from the brow up to the crown
    # an octagon round the square head: face plates 13.6 wide, corner plates laid just outside the head's corners
    for j in range(8):
        phi = math.radians(j * 45)
        n = np.array([math.sin(phi), 0, -math.cos(phi)])
        e1 = np.array([math.cos(phi), 0, math.sin(phi)])
        corner = j % 2 == 1
        r, w = (11.9, 3.8) if corner else (8.6, 13.6)
        fbox(hd, f"band{j}", c + n * r + [0, 5.8, 0], e1, [0, 1, 0], (w, 5.0, 1.2), "iron")
        fbox(hd, f"rim{j}", c + n * (r + 0.6) + [0, 3.9, 0], e1, [0, 1, 0], (w + (0.6 if corner else 0.4), 1.6, 1.2),
             "gold")
    # the cone: eight plates per tier, leaning in, the seams ribbed
    levels = [(8.2, 10.1), (11.4, 9.5), (15.6, 7.0), (19.4, 3.8), (22.0, 1.6)]
    for ti, ((y0, r0), (y1, r1)) in enumerate(zip(levels, levels[1:])):
        for j in range(8):
            phi = math.radians(j * 45)
            n = np.array([math.sin(phi), 0, -math.cos(phi)])
            e1 = np.array([math.cos(phi), 0, math.sin(phi)])
            e2 = _n(-n * (r0 - r1) + [0, y1 - y0, 0])
            rm = (r0 + r1) / 2 - 0.6
            ln = math.hypot(y1 - y0, r0 - r1) + 0.6
            w = 0.83 * (r0 + r1) / 2 + 0.6
            fbox(hd, f"cone{ti}_{j}", c + n * rm + [0, (y0 + y1) / 2, 0], e1, e2, (w, ln, 1.2), "iron")
            if j % 2 == 0:
                seam = _n(n + _n(np.cross([0, 1, 0], n)) * 0.0)
                fbox(hd, f"rib{ti}_{j}", c + seam * (rm + 0.7) + [0, (y0 + y1) / 2, 0], e1, e2, (1.4, ln, 0.6), "gold")
    hd.box("cone_top", (x, y + 22.2, z), (3, 1.6, 3), "gold")
    limb(hd, "spike", c + [0, 22.2, 0], c + [0, 28, 0], 1.6, 1.6, "iron")
    hd.box("plume_socket", (x, y + 26, z), (2.4, 2, 2.4), "gold")
    strand(hd, "plume", [c + [0, 27, 0], c + [0, 28, 4], c + [0, 25, 9], c + [0, 19, 12], c + [0, 12, 13]],
           3, 1.8, "plume")
    # the aventail: mail from the band's lower edge over the cheeks' back half, the nape and the shoulders
    hd.box("aventail_back", (x, y - 3.6, z + 9.6), (17, 14, 1.4), "mail", rotation=(8, 0, 0))
    for k in (-1, 1):
        hd.box(f"aventail{k}", (x + k * 9.6, y - 3.4, z + 1.8), (1.4, 13.4, 11), "mail", rotation=(0, 0, k * 6))
        fbox(hd, f"aventail_corner{k}", c + [k * 8.6, -3.6, 8.6], [k, 0, 1], [0, 1, 0], (4, 14, 1.4), "mail")


def bow(t, hand, up, fwd, draw, take):
    mat = {"A": "wood", "B": "iron", "C": "coat_dark"}[take]
    t.box("bow_grip", tuple(hand), (3.4, 6, 3.4), "leather")
    tips = []
    for k, name in ((1, "upper"), (-1, "lower")):
        u = up * k
        if take == "B":
            pts = [hand + u * 2, hand + u * 14 + fwd * 2.5, hand + u * 26 + fwd * 1.5]
        else:
            pts = [hand + u * 2, hand + u * 11 + fwd * 3.5, hand + u * 19 + fwd * 3, hand + u * 24 + fwd * 6]
        strand(t, f"bow_{name}", pts, 3, 2, mat, side=np.cross(up, fwd))
        tips.append(pts[-1])
    if take == "C":
        top = tips[0]
        limb(t, "staff_head", top, top + up * 6 + fwd * 1, 2, 2, "iron")
        ball(t, "staff_gem", tuple(top + up * 8 + fwd * 1), (4, 5, 4), "cyan")
    if draw is None:
        limb(t, "string", tips[0], tips[1], 0.5, 0.5, "skel")
    else:
        limb(t, "string_a", tips[0], draw, 0.5, 0.5, "skel")
        limb(t, "string_b", draw, tips[1], 0.5, 0.5, "skel")
        tip = hand + fwd * 8
        limb(t, "arrow", draw, tip, 1, 1, "wood")
        spike(t, "arrow_head", tip, fwd, 4, 1.8, "cyan" if take != "A" else "iron")


# ==== building, rendering ==============================================================================================

TAKES = {
    "A": "the Spiked Charger and the Bone Courser",
    "B": "the Cataphract and the Ironbound",
    "C": "the Dread Horns and the Storm Steed",
}
POSES = {"vanguard": (REST, "charge"), "outrider": (REST, "snipe")}


def build(take, kind, pose, helm=None, horse=None):
    m = Model(f"dread_{take}_{kind}_{pose}")
    root = m.group(kind, (0, 0, 0))
    f = frame(horse or ("destrier" if kind == "vanguard" else "courser"), pose)
    (destrier if kind == "vanguard" else courser)(root, f, take)
    if take == "bare":
        return m, f["neck"][2]
    rg = root.group("rider", (0, 0, 0))
    hc, lean, hip = rider(rg, f, kind, take, helm)
    headbone = next(g for g in m.groups if g.name == "headbone")
    return m, world(headbone, hc)


VIEWS = [
    {"name": "hero", "mode": "flat", "camera": "persp", "yaw": 40, "height": 3.4, "dist": 10.5, "target_z": 3.9},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "low", "mode": "clay", "camera": "persp", "yaw": -30, "height": 1.62, "dist": 9.0, "target_z": 3.8,
     "player": False},
]
LABELS = {"hero": "three-quarter", "sil_side": "side, silhouette", "low": "a player's eye", "head": "the rider's head"}
NAMES = {("vanguard", REST): "Vanguard", ("vanguard", "charge"): "Vanguard, the charge",
         ("outrider", REST): "Outrider", ("outrider", "snipe"): "Outrider, the snipe"}


BARE_VIEWS = [
    {"name": "side", "mode": "flat", "camera": "ortho_side", "player": False},
    {"name": "hero", "mode": "flat", "camera": "persp", "yaw": 40, "height": 2.4, "dist": 9.0, "target_z": 2.4},
    {"name": "front", "mode": "flat", "camera": "persp", "yaw": -12, "height": 2.0, "dist": 9.0, "target_z": 2.4,
     "player": False},
]


def bare():
    """The horses alone, every pose: the anatomy check before any dressing."""
    v2.PALETTE.update(PALETTE)
    tiles = []
    for kind, horse in (("vanguard", "destrier"), ("outrider", "courser")):
        for pose in POSES[kind]:
            m, _ = build("bare", kind, pose)
            d = OUT / "bare" / horse / pose
            v2.run_blender(m.render_json(v2.PALETTE), d, BARE_VIEWS)
            lo, hi = m.bounds()
            print(horse, pose, [round(float(v) / 16, 2) for v in hi - lo], len(m.cubes))
            tiles.append((f"{horse} {pose}", d))
    tw, th, pad = 440, 340, 12
    img = Image.new("RGB", (pad + 3 * (tw + pad), 50 + len(tiles) * (th + 34)), sheet.BG)
    dr = ImageDraw.Draw(img)
    for r, (label, d) in enumerate(tiles):
        for c, v in enumerate(BARE_VIEWS):
            x, y = pad + c * (tw + pad), 50 + r * (th + 34)
            img.paste(sheet._tile(d / f"{v['name']}.png", tw, th), (x, y))
            dr.text((x, y + th + 4), f"{label}: {v['name']}", font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "bare.png")


def main(args):
    if "bare" in args:
        return bare()
    quick = "quick" in args
    takes = [t for t in "ABC" if t in args] or list("ABC")
    kinds = [k for k in ("vanguard", "outrider") if k in args] or ["vanguard", "outrider"]
    v2.PALETTE.update(PALETTE)
    for take in takes:
        rows = []
        for kind in kinds:
            for pose in (POSES[kind][:1] if quick else POSES[kind]):
                m, head = build(take, kind, pose)
                d = OUT / take / kind / pose
                if d.exists():
                    shutil.rmtree(d)
                views = list(VIEWS[:2] if quick else VIEWS)
                views.append({"name": "head", "mode": "flat", "camera": "persp", "yaw": 32, "dist": 3.2,
                              "height": 0.4, "target": [float(v) for v in head], "player": False, "lens": 40})
                v2.run_blender(m.render_json(v2.PALETTE), d, views)
                lo, hi = m.bounds()
                print(take, kind, pose, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
                rows.append((kind, pose, [v["name"] for v in views]))
        tw, th, pad, top = 440, 340, 12, 60
        ncol = max(len(r[2]) for r in rows)
        img = Image.new("RGB", (pad + ncol * (tw + pad), top + len(rows) * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Dread Riders, session 1: take {take}, {TAKES[take]}", font=sheet._font(26), fill=sheet.INK)
        for r, (kind, pose, names) in enumerate(rows):
            for c, name in enumerate(names):
                x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
                img.paste(sheet._tile(OUT / take / kind / pose / f"{name}.png", tw, th), (x, y))
                dr.text((x, y + th + 6), f"{NAMES[(kind, pose)]}: {LABELS[name]}", font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / f"take_{take}{'_quick' if quick else ''}.png")
    if not quick and len(takes) == 3:
        compare()


def compare():
    tw, th, pad, top = 520, 400, 12, 60
    img = Image.new("RGB", (pad + 3 * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Dread Riders, session 1: three takes side by side", font=sheet._font(26), fill=sheet.INK)
    for c, take in enumerate("ABC"):
        for r, kind in enumerate(("vanguard", "outrider")):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / take / kind / REST / "hero.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{take}: {TAKES[take].split(' and ')[r]}", font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "compare.png")


if __name__ == "__main__" and "take2" not in sys.argv:
    main(sys.argv[1:])


# ==== take 2 (2026-11-20): the user's picks ===========================================================================
# The Vanguard: A's spiked charger and A's armour and lance, under C's horned armet.
# The Outrider: A's steppe helm reworked (it read as a bowl on the head), on a buff bone courser with A's rope tack.

OUT2 = ROOT / "docs/art/bosses/dread_riders/overhaul/s1_take2"
TAKE2 = {"vanguard": dict(take="A", helm="C", horse=None), "outrider": dict(take="A", helm="A2", horse="courser_buff")}


def take2():
    v2.PALETTE.update(PALETTE)
    rows = []
    for kind, cfg in TAKE2.items():
        for pose in POSES[kind]:
            m, head = build(cfg["take"], kind, pose, cfg["helm"], cfg["horse"])
            d = OUT2 / kind / pose
            if d.exists():
                shutil.rmtree(d)
            hv = [float(v) for v in head]
            views = list(VIEWS) + [
                {"name": "head", "mode": "flat", "camera": "persp", "yaw": 32, "dist": 3.4, "height": 0.6,
                 "target": hv, "player": False, "lens": 40},
                {"name": "head_side", "mode": "flat", "camera": "persp", "yaw": -90, "dist": 3.6, "height": 0.4,
                 "target": hv, "player": False, "lens": 40},
            ]
            v2.run_blender(m.render_json(v2.PALETTE), d, views)
            lo, hi = m.bounds()
            print(kind, pose, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
            rows.append((kind, pose, [v["name"] for v in views]))
    labels = dict(LABELS, head_side="the rider's head, side")
    tw, th, pad, top = 360, 280, 10, 56
    ncol = max(len(r[2]) for r in rows)
    img = Image.new("RGB", (pad + ncol * (tw + pad), top + len(rows) * (th + 30 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Dread Riders, session 1 take 2: A's charger under C's horned armet; the steppe archer on a buff "
                       "bone horse", font=sheet._font(24), fill=sheet.INK)
    for r, (kind, pose, names) in enumerate(rows):
        for c, name in enumerate(names):
            x, y = pad + c * (tw + pad), top + r * (th + 30 + pad)
            img.paste(sheet._tile(OUT2 / kind / pose / f"{name}.png", tw, th), (x, y))
            dr.text((x, y + th + 5), f"{NAMES[(kind, pose)]}: {labels[name]}", font=sheet._font(15), fill=sheet.DIM)
    img.save(OUT2 / "sheet.png")
    # the skeleton horse before and after, bare, side by side
    tiles = []
    for horse in ("courser", "courser_buff"):
        m, _ = build("bare", "outrider", REST, horse=horse)
        d = OUT2 / "bare" / horse
        v2.run_blender(m.render_json(v2.PALETTE), d, BARE_VIEWS)
        tiles.append((horse, d))
    tw, th = 440, 340
    img = Image.new("RGB", (pad + 3 * (tw + pad), top + 2 * (th + 30 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "The bone horse: take 1 (top) and the buff build (bottom)", font=sheet._font(24), fill=sheet.INK)
    for r, (horse, d) in enumerate(tiles):
        for c, v in enumerate(BARE_VIEWS):
            x, y = pad + c * (tw + pad), top + r * (th + 30 + pad)
            img.paste(sheet._tile(d / f"{v['name']}.png", tw, th), (x, y))
            dr.text((x, y + th + 5), f"{'take 1' if r == 0 else 'buff'}: {v['name']}", font=sheet._font(15), fill=sheet.DIM)
    img.save(OUT2 / "bone_horse.png")


if __name__ == "__main__" and "take2" in sys.argv:
    take2()
