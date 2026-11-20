"""Dread Riders, session 1: blockouts of the direction the user picked (2026-11-20): Pestilence and War.

The user's brief:
- two of the four horsemen: the Outrider is **Pestilence** (the bow), the Vanguard is **War**;
- War carries a **war banner** (the Lancer's Pennant he drops is a black banner);
- Pestilence may be a little gross as well as eerie.
Mechanics are fixed: the Outrider is fragile and evasive and snipes from 14 blocks; the Vanguard is a tank with warned lance
charges. Both are fast; the horses can't be hurt.

The takes share that and differ in how far each idea goes:

  A  the Pale Crown and the Standard
     Pestilence: a hooded skeleton with a thin tarnished crown, a bow carved from a single rib, a grave shroud; its horse
     is starved, head hanging, ribs showing through holes in the hide, shelf fungus on the flank, drool.
     War: full plate, a great helm with an ember slit; a barded warhorse in a dagged caparison; the banner hangs from a
     crossbar on his cleaver-headed lance.
  B  Rot and Ruin
     Pestilence: a gaunt skeleton standing in the stirrups, no hood, a crown of thorns, a bow made of a spine, shroud
     streaming; its horse is bloated, the belly swollen and split with fungus spilling out, bile dripping.
     War: molten seams in heavy plate with huge pauldrons; a bare red roan with a burning mane and tail; the banner flies
     from a pole strapped to his back, so it's up even in the charge.
  C  the Plague Doctor and the Siege
     Pestilence: a beak-masked plague doctor in a rotten wide-brimmed hat and long coat, a censer of spores at the saddle;
     its horse is a skeleton at the front and bloated rotting flesh behind.
     War: a spiked crown-helm; the horse in plate barding like a siege engine, a ram spike on its chest and brow; the banner
     on the lance, larger.

Each rider is shown at rest and in its moment: Pestilence drawing the bow (the snipe), War charging with the lance couched.
Model units: 16 = one block, y up, it faces -z, its right side is +x.

Run from the repository root: python tools/art/bosses/dread_s1.py [A B C] [quick]
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
from bosses.heartwood_s1 import cbox, curve, _n  # noqa: E402

OUT = ROOT / "docs/art/bosses/dread_riders/overhaul/s1_blockout"
PALETTE = {
    # Pestilence
    "bone": (226, 218, 196), "bone_dark": (168, 158, 136), "hide": (210, 204, 190), "wound": (112, 54, 50),
    "rot": (112, 116, 84), "fungus": (196, 188, 104), "bile": (150, 172, 60), "shroud": (196, 190, 168),
    "shroud_dark": (146, 138, 118), "crown": (168, 142, 86), "sinew": (132, 72, 62), "eye_sick": (186, 230, 90),
    "beak": (120, 104, 84), "leather": (84, 70, 58),
    # War
    "plate": (112, 52, 40), "plate_dark": (62, 40, 36), "ember": (255, 122, 40), "roan": (148, 74, 58),
    "roan_dark": (96, 48, 40), "flame": (255, 160, 60), "banner": (36, 32, 34), "sigil": (176, 34, 30),
    "cloth": (128, 30, 30), "wood": (104, 78, 56), "steel": (142, 140, 138), "hoof": (52, 46, 42),
}
REST, ACT = "rest", "act"
POSES = (REST, ACT)


def seg(g, name, a, b, h, w, mat, extra=0.3):
    """A box from a to b with an explicit frame: h across it in the vertical plane through it, w to its side (for
    necks, heads and cloth, where which way is wide matters)."""
    from bosses.heartwood_s2 import euler
    a, b = np.array(a, float), np.array(b, float)
    d = _n(b - a)
    up = np.array([0, 1.0, 0]) if abs(d[1]) < 0.95 else np.array([0, 0, -1.0])
    u = _n(up - d * (up @ d))
    z = np.cross(d, u)
    R = np.column_stack([d, u, z])
    length = float(np.linalg.norm(b - a)) + min(h, w) * extra
    return g.box(name, tuple((a + b) / 2), (length, h, w), mat, rotation=tuple(euler(R)))


# ---- the horse --------------------------------------------------------------------------------------------------------

class Horse:
    """Real horse proportions: H is the height at the withers, L the body's length, W its width, D the barrel's depth."""

    def __init__(self, H, L, W, D):
        self.H, self.L, self.W, self.D = H, L, W, D
        self.saddle = np.array([0.0, H + 1, -0.04 * L])


def leg_points(h, side, end, pose, phase):
    """Hip/shoulder to hoof for one leg. end 'front' or 'hind'; phase picks the stride in the gallop."""
    H, L, D = h.H, h.L, h.D
    x = side * h.W * 0.3
    if end == "front":
        z = -0.36 * L
        if pose == "gallop" and phase == 0:       # reaching forward
            return [(x, H - 5, z), (x, H - D + 3, z - 1), (x, 0.5 * H, z - 0.18 * H), (x, 0.36 * H, z - 0.36 * H),
                    (x, 0.3 * H, z - 0.42 * H)]
        if pose == "gallop":                      # folded under
            return [(x, H - 5, z), (x, H - D + 2, z + 1), (x, 0.44 * H, z - 0.04 * H), (x, 0.4 * H, z + 0.16 * H),
                    (x, 0.32 * H, z + 0.2 * H)]
        dz = 2 if phase == 0 else -1
        return [(x, H - 5, z), (x, H - D + 1, z + 1), (x, 0.31 * H, z + dz), (x, 4, z + dz - 1), (x, 1.5, z + dz - 2)]
    z = 0.34 * L
    if pose == "gallop" and phase == 0:           # pushing off, stretched back
        return [(x, H - 4, z), (x, H - D + 1, z - 0.06 * L), (x, 0.3 * H, z + 0.16 * L + 0.1 * H),
                (x, 0.1 * H, z + 0.16 * L + 0.32 * H), (x, 1.5, z + 0.16 * L + 0.36 * H)]
    if pose == "gallop":                          # reaching under the body
        return [(x, H - 4, z), (x, H - D - 1, z - 0.16 * L), (x, 0.4 * H, z - 0.06 * L), (x, 0.13 * H, z - 0.36 * L),
                (x, 1.5, z - 0.4 * L)]
    if phase == 1:                                # resting a hind hoof on its tip
        return [(x, H - 4, z), (x, H - D, z - 0.1 * L), (x, 0.38 * H, z + 0.08 * L), (x, 5, z + 0.02 * L),
                (x, 1.5, z - 0.02 * L)]
    return [(x, H - 4, z), (x, H - D, z - 0.1 * L), (x, 0.36 * H, z + 0.1 * L), (x, 4, z + 0.06 * L),
            (x, 1.5, z + 0.05 * L)]


def leg(g, name, pts, w_up, w_low, mat, joint_mat=None, hoof="hoof"):
    pts = [np.array(p, float) for p in pts]
    widths = [w_up * 1.15, w_up, (w_up + w_low) / 2, w_low]
    for i in range(4):
        cbox(g, f"{name}{i}", pts[i], pts[i + 1], widths[i], widths[i] * 0.9, mat)
    if joint_mat:                                 # knobbly joints on a starved or skeletal leg
        for i in (2, 3):
            g.box(f"{name}_joint{i}", tuple(pts[i]), (w_low * 1.6, w_low * 1.4, w_low * 1.6), joint_mat)
    f = pts[4]
    g.box(f"{name}_hoof", tuple(f + [0, 0.4, -0.6]), (w_low * 1.6, 3.2, w_low * 1.9), hoof)


def legs(g, h, pose, mat, w_up, w_low, joint_mat=None, front_mat=None):
    for end in ("front", "hind"):
        for side, phase in ((1, 0), (-1, 1)):
            leg(g, f"leg_{end}_{'right' if side > 0 else 'left'}", leg_points(h, side, end, pose, phase),
                w_up * (1.1 if end == "hind" else 1), w_low, (front_mat if end == "front" and front_mat else mat),
                joint_mat)


def neck_head(g, h, head, mat, head_mat=None, skull=False):
    """The neck along a curve and the long head. head: 'high' (a warhorse), 'mid', or 'low' (hanging, sick)."""
    H, L = h.H, h.L
    base = np.array([0, H - 7, -0.36 * L])
    if head == "high":
        ctrl = [base, (0, H + 8, -0.48 * L), (0, H + 16, -0.56 * L)]
        muzzle_d = np.array([0, -0.62, -0.78])
    elif head == "mid":
        ctrl = [base, (0, H + 3, -0.5 * L), (0, H + 6, -0.62 * L)]
        muzzle_d = np.array([0, -0.8, -0.6])
    else:
        ctrl = [base, (0, H - 3, -0.54 * L), (0, H - 10, -0.72 * L)]
        muzzle_d = np.array([0, -0.8, -0.6])
    pts = curve(ctrl, 4)
    for i in range(4):
        w = 0.36 * H - i * 0.05 * H
        seg(g, f"neck{i}", pts[i], pts[i + 1], w, 0.22 * H - i * 0.015 * H, mat)
    poll = pts[-1]
    muzzle = poll + _n(muzzle_d) * 0.5 * H
    hm = head_mat or mat
    seg(g, "head", poll, poll + (muzzle - poll) * 0.5, 0.22 * H, 0.16 * H, hm)
    seg(g, "cheek", poll + (muzzle - poll) * 0.15 + [0, -1.5, 0], poll + (muzzle - poll) * 0.45 + [0, -1.5, 0], 0.2 * H,
        0.17 * H, hm)
    seg(g, "muzzle", poll + (muzzle - poll) * 0.45, muzzle, 0.15 * H, 0.12 * H, hm)
    for s in (-1, 1):
        cbox(g, f"ear{s}", poll + [s * 2.5, 1, 1], poll + [s * 3.5, 6.5, 2.5], 1.6, 2.4, hm)
        if skull:
            g.box(f"socket{s}", tuple(poll + (muzzle - poll) * 0.3 + [s * 3.3, 0, 0]), (1.2, 3.2, 3.6), "wound")
    return poll, muzzle, pts


def tail(g, h, mat, pose, w=3.2, flame=False):
    H, L = h.H, h.L
    root = np.array([0, H - 1, 0.5 * L])
    if pose == "gallop":
        ctrl = [root, root + [0, 2, 8], root + [0, -2, 18], root + [0, -6, 26]]
    else:
        ctrl = [root, root + [0, -3, 5], root + [0, -12, 7], root + [0, -22, 6]]
    pts = curve(ctrl, 4)
    for i in range(4):
        cbox(g, f"tail{i}", pts[i], pts[i + 1], w * (1.2 - i * 0.15), w * 0.7, mat)
        if flame:
            g.box(f"tail_flame{i}", tuple(pts[i + 1] + [0, 2.5, 0]), (w * 1.4, 5, w * 1.4), "flame",
                  rotation=(20 * i, 30 * i, 0))


def mane(g, pts, mat, h, flame=False, n=6, length=5.0):
    """Along the neck's crest: offset from the neck's centre line by half its depth, toward the top and back."""
    for k in range(n):
        i = min(int(k / n * (len(pts) - 1)), len(pts) - 2)
        f = k / n * (len(pts) - 1) - i
        p = pts[i] + (pts[i + 1] - pts[i]) * f
        d = _n(pts[i + 1] - pts[i])
        u = _n(np.array([0, 1.0, 0]) - d * d[1])
        depth = 0.36 * h.H - i * 0.05 * h.H
        size = (2.4, length * (1.7 if k % 2 else 1.1), 4) if flame else (1.6, length, 3)
        g.box(f"mane{k}", tuple(p + u * (depth / 2 + size[1] * 0.35)), size, mat,
              rotation=(-math.degrees(math.atan2(u[2], u[1])), 0, 0))


def barrel(g, h, mat, belly=1.0, rump_mat=None, chest_mat=None):
    H, L, W, D = h.H, h.L, h.W, h.D
    cy = H - D / 2
    ball(g, "barrel", (0, cy - 1.5 - (belly - 1) * D * 0.3, 0), (W * (0.95 + 0.3 * (belly - 1)), D * belly * 0.94, L * 0.66),
         mat)
    ball(g, "chest", (0, cy, -0.38 * L), (W * 0.9, D * 1.0, 0.3 * L), chest_mat or mat, rot=(-10, 0, 0))
    ball(g, "rump", (0, cy + 1.5, 0.36 * L), (W * 1.04, D * 0.98, 0.34 * L), rump_mat or mat, rot=(12, 0, 0))
    ball(g, "croup", (0, H - 1, 0.3 * L), (W * 0.8, 6, 0.3 * L), rump_mat or mat, rot=(8, 0, 0))
    ball(g, "withers", (0, H - 2, -0.26 * L), (W * 0.6, 7, 0.2 * L), chest_mat or mat)
    for s in (-1, 1):
        ball(g, f"shoulder{s}", (s * W * 0.28, H - D * 0.62, -0.31 * L), (W * 0.42, D * 1.05, 0.26 * L), chest_mat or mat,
             rot=(-12, 0, 0))
        ball(g, f"thigh{s}", (s * W * 0.3, H - D * 0.7, 0.3 * L), (W * 0.44, D * 1.2, 0.3 * L), rump_mat or mat,
             rot=(14, 0, 0))


def starved_detail(g, h, holes=True):
    """Ribs through holes in the hide, the hip bones and spine jutting, shelf fungus, drool."""
    H, L, W, D = h.H, h.L, h.W, h.D
    for s in (-1, 1):
        x = s * (W / 2 + 0.2)
        if holes:
            g.box(f"hole{s}", (x, H - D * 0.5, -0.02 * L + s * 2), (1.2, D * 0.62, 0.32 * L), "wound")
        for r in range(6):
            z = -0.2 * L + r * 0.075 * L
            g.box(f"rib{s}_{r}", (x + s * 0.4, H - D * 0.5, z), (1.4, D * 0.8, 1.8), "bone", rotation=(-12, 0, s * 6))
        g.box(f"hip_bone{s}", (s * W * 0.42, H + 1, 0.3 * L), (4, 3.2, 4.5), "bone", rotation=(0, 20 * s, 15 * s))
        g.box(f"shelf{s}", (x + s * 1.6, H - D * 0.7, 0.24 * L), (3.2, 1.4, 7), "fungus", rotation=(0, 0, s * 18))
        g.box(f"shelf_b{s}", (x + s * 1.4, H - D * 0.48, 0.3 * L), (2.6, 1.2, 5), "fungus", rotation=(0, 0, s * 14))
    for k in range(7):
        g.box(f"spine{k}", (0, H + 0.6, -0.3 * L + k * 0.1 * L), (2.4, 2.6, 2.2), "bone")


def drool(g, muzzle, n=3, length=7.0):
    for k in range(n):
        g.box(f"drool{k}", tuple(muzzle + [(k - 1) * 1.6, -length * (0.5 + 0.25 * k) / 2 - 1, 0]),
              (0.9, length * (0.5 + 0.25 * k), 0.9), "bile")


def caparison(g, h, pose, mat="cloth"):
    """A dagged cloth skirt over the flanks from the barrel's top to the knees; in the gallop it flares back."""
    H, L, W = h.H, h.L, h.W
    flare = 10 if pose == "gallop" else 0
    for s in (-1, 1):
        top = H + 1
        drop = H * 0.58
        sk = g.group(f"skirt{s}", (s * (W / 2 + 1), top, 0), (flare, 0, s * 4))
        sk.box(f"skirt{s}", (s * (W / 2 + 1), top - drop / 2, 0), (1.4, drop, L * 1.08), mat)
        for t in range(7):
            sk.box(f"dag{s}_{t}", (s * (W / 2 + 1), top - drop - 2.5, -L * 0.48 + t * L * 0.16), (1.4, 5, 4.2), mat,
                   rotation=(0, 0, 0))
    g.box("crupper", (0, H + 2, 0.34 * L), (W * 1.12, 2, 0.36 * L), mat)


def barding(g, h, poll, muzzle, neck_pts, siege=False):
    """Plate on the horse: chanfron on the face, crinet down the neck, peytral over the chest."""
    H, L, W = h.H, h.L, h.W
    seg(g, "chanfron", poll + [0, 1.2, -0.8], poll + (muzzle - poll) * 0.8 + [0, 1.2, -0.8], 0.2 * H, 0.18 * H, "plate")
    for i in range(len(neck_pts) - 1):
        seg(g, f"crinet{i}", neck_pts[i] + [0, 4, 2], neck_pts[i + 1] + [0, 4, 2], 4, 0.26 * H - i * 1.2, "plate")
    ball(g, "peytral", (0, H - h.D * 0.45, -0.45 * L), (W * 1.1, h.D * 0.9, 6), "plate")
    if siege:
        cbox(g, "ram", (0, H - h.D * 0.45, -0.5 * L), (0, H - h.D * 0.5, -0.5 * L - 18), 5, 5, "steel")
        cbox(g, "ram_tip", (0, H - h.D * 0.5, -0.5 * L - 18), (0, H - h.D * 0.5, -0.5 * L - 26), 2.6, 2.6, "steel")
        cbox(g, "brow_spike", poll + [0, 3, -3], poll + [0, 10, -12], 2.4, 2.4, "steel")
        for s in (-1, 1):
            g.box(f"flank_plate{s}", (s * (W / 2 + 1.4), H - h.D * 0.45, 0), (2, h.D * 1.1, L * 0.92), "plate")
            for t in range(5):
                g.box(f"flank_rivet{s}_{t}", (s * (W / 2 + 2.5), H - 2, -0.36 * L + t * 0.18 * L), (1.2, 2, 2),
                      "plate_dark")
        ball(g, "rump_plate", (0, H, 0.36 * L), (W * 1.2, 8, 0.36 * L), "plate")


# ---- the riders -------------------------------------------------------------------------------------------------------

def straddle(g, h, mat, boot_mat, k, stand=False):
    """Thighs over the barrel, shins down the flanks to the stirrups."""
    S = h.saddle
    for s in (-1, 1):
        hip = S + [s * 4, 3 + (6 if stand else 0), 2]
        knee = S + [s * (h.W / 2 + 3), -2 + (3 if stand else 0), -7]
        foot = S + [s * (h.W / 2 + 3.5), -15, -4]
        cbox(g, f"thigh{s}", hip, knee, 3.2 * k, 3.2 * k, mat)
        cbox(g, f"shin{s}", knee, foot, 2.8 * k, 2.8 * k, boot_mat)
        g.box(f"stirrup{s}", tuple(foot + [0, -1.5, -1]), (4, 1.2, 6), "steel")


def pestilence(m, take, pose):
    """The Outrider."""
    root = m.group("pestilence", (0, 0, 0))
    kind = {"A": "starved", "B": "bloated", "C": "half"}[take]
    h = Horse(36, 40, 10 if kind != "bloated" else 11, 14)
    hp = "stand"
    # the horse
    if kind == "half":          # skeleton at the front, bloated rotting flesh behind
        for r in range(6):
            z = -0.4 * h.L + r * 0.075 * h.L
            for s in (-1, 1):
                a, b, c = (s * 1.5, h.H, z), (s * (h.W / 2 + 3), h.H - h.D * 0.45, z + 1), (s * 2, h.H - h.D * 0.95, z + 2)
                cbox(root, f"cage{s}_{r}a", a, b, 1.8, 1.8, "bone")
                cbox(root, f"cage{s}_{r}b", b, c, 1.6, 1.6, "bone")
        cbox(root, "sternum", (0, h.H - h.D * 0.95, -0.42 * h.L), (0, h.H - h.D * 0.95, -0.02 * h.L), 3, 2.4, "bone")
        cbox(root, "spine_front", (0, h.H, -0.42 * h.L), (0, h.H, 0.04 * h.L), 3, 3, "bone")
        for s in (-1, 1):
            cbox(root, f"scapula{s}", (s * 4, h.H, -0.32 * h.L), (s * 5, h.H - h.D * 0.7, -0.4 * h.L), 5, 1.4, "bone")
        ball(root, "rump", (0, h.H - h.D / 2 - 1, 0.26 * h.L), (h.W * 1.6, h.D * 1.4, 0.56 * h.L), "rot")
        root.box("rot_edge", (0, h.H - h.D / 2, 0.0), (h.W * 1.5, h.D * 1.1, 2.4), "wound")
        for k, (x, y, z) in enumerate(((5, 30, 4), (-6, 26, 10), (4, 22, 16), (-3, 34, 18))):
            root.box(f"spill{k}", (x, y, z), (5, 3, 6), "fungus", rotation=(k * 30, k * 50, k * 20))
        legs(root, h, hp, "rot", 3.6, 2.2, joint_mat="bone", front_mat="bone")
        poll, muzzle, npts = neck_head(root, h, "mid", "bone", skull=True)
        for i in range(len(npts) - 1):
            root.box(f"vertebra{i}", tuple((npts[i] + npts[i + 1]) / 2 + [0, 4, 0]), (2, 4, 2), "bone")
        tail(root, h, "rot", hp, w=2.4)
        drool(root, muzzle, 2, 6)
    else:
        barrel(root, h, "hide", belly=1.0 if kind == "starved" else 1.55)
        starved_detail(root, h, holes=(kind == "starved"))
        if kind == "bloated":   # the belly swollen and split, fungus spilling out
            ball(root, "belly_sac", (0, h.H - h.D - 3, 0.02 * h.L), (h.W * 1.7, h.D * 0.95, h.L * 0.56), "rot",
                 rot=(4, 0, 0))
            cy = h.H - h.D / 2 - h.D * 0.55 * 0.3 - 5
            root.box("split", (0, cy - h.D * 0.62, 0.02 * h.L), (h.W * 0.9, 2.2, 0.42 * h.L), "wound")
            for k in range(6):
                root.box(f"spill{k}", (((k % 3) - 1) * 4.5, cy - h.D * 0.72 - (k // 3) * 2.5, -8 + k * 3.4),
                         (4.2, 3.2, 4.2), "fungus", rotation=(k * 25, k * 40, k * 15))
            for k in range(4):
                root.box(f"belly_drip{k}", ((k - 1.5) * 3, cy - h.D * 0.85 - 4, -6 + k * 4), (0.9, 6 + 3 * (k % 2), 0.9),
                         "bile")
        legs(root, h, hp, "hide", 3.6, 2.2, joint_mat="bone")
        poll, muzzle, npts = neck_head(root, h, "low" if kind == "starved" else "mid", "hide")
        mane(root, npts, "shroud_dark", h, n=5, length=6)
        tail(root, h, "shroud_dark", hp, w=2.2)
        drool(root, muzzle, 3, 8 if kind == "starved" else 6)
        # shelf fungus on the neck and the face
        root.box("neck_shelf", tuple(npts[2] + [3.4, 0, 0]), (3, 1.2, 5), "fungus", rotation=(0, 0, 20))
        root.box("face_shelf", tuple(poll + (muzzle - poll) * 0.4 + [-3.2, 0, 0]), (2.6, 1.1, 4), "fungus",
                 rotation=(0, 0, -20))
    # the rider: a skeleton, thin, hunched
    k = 1.6
    S = h.saddle
    stand = take == "B"
    straddle(root, h, "bone", "bone", k * 0.7, stand=stand)
    pelvis = S + [0, 3 + (6 if stand else 0), 2]
    hunch = {"A": 30, "B": 8, "C": 22}[take] + (-8 if pose == ACT else 0)
    t = root.group("torso", tuple(pelvis), (-hunch, 0, 0))
    t.box("pelvis", tuple(pelvis), (9, 4, 5), "bone")
    cbox(t, "spine", pelvis, pelvis + [0, 18, 0], 2.6, 2.6, "bone")
    ball(t, "ribcage", tuple(pelvis + [0, 13, 0]), (12, 12, 7), "bone_dark")
    for r in range(4):
        t.box(f"rib{r}", tuple(pelvis + [0, 9 + r * 2.6, -3.4]), (11.5, 1.2, 1.2), "bone")
    neck = pelvis + [0, 21, 0]
    head = neck + [0, 6, -1]
    if take == "C":             # the plague doctor: a long coat over the frame
        ball(t, "coat", tuple(pelvis + [0, 11, 0.5]), (14, 22, 9), "leather")
    t.box("skull", tuple(head), (9.5, 9.5, 10), "bone")
    for s in (-1, 1):
        t.box(f"eye{s}", tuple(head + [s * 2.2, 0.6, -5.1]), (2.2, 2.2, 0.6), "eye_sick")
    t.box("jaw", tuple(head + [0, -5.2, -1]), (7, 2.4, 7.5), "bone_dark")
    if take == "A":             # a grave shroud's hood and a thin tarnished crown
        ball(t, "hood", tuple(head + [0, 1.5, 2.5]), (15, 15, 15), "shroud")
        for c in range(5):
            a = math.radians(-60 + c * 30)
            t.box(f"crown{c}", tuple(head + [math.sin(a) * 6, 8.5, -math.cos(a) * 6 + 1]), (1.4, 4.5 + (c == 2) * 2, 1.4),
                  "crown")
        t.box("crown_band", tuple(head + [0, 6.4, 0]), (13, 1.6, 13), "crown")
    elif take == "B":           # a crown of thorns
        for c in range(9):
            a = 2 * math.pi * c / 9
            t.box(f"thorn{c}", tuple(head + [math.cos(a) * 6.2, 6.5, math.sin(a) * 6.2]), (1.2, 4 + (c % 3), 1.2), "sinew",
                  rotation=(math.degrees(math.sin(a)) * 0.5, 0, -math.degrees(math.cos(a)) * 0.5))
        t.box("thorn_band", tuple(head + [0, 5.4, 0]), (13.4, 1.8, 13.4), "sinew", rotation=(0, 20, 0))
    else:                       # the beak mask and the hat
        cbox(t, "beak", head + [0, -1, -5], head + [0, -6, -17], 4.6, 4.2, "beak")
        cbox(t, "beak_tip", head + [0, -6, -17], head + [0, -8, -20], 2.2, 2.2, "beak")
        t.box("hat_brim", tuple(head + [0, 6.4, 0]), (24, 1.4, 24), "leather", rotation=(-6, 0, 4))
        t.box("hat_crown", tuple(head + [0, 10, 0.5]), (11, 7, 11), "leather")
        for s in (-1, 1):
            t.box(f"lens{s}", tuple(head + [s * 2.8, 0.6, -5.8]), (3.2, 3.2, 1), "eye_sick")
    # the shroud: tattered strips from the shoulders that hang with gravity, then drape back over the horse
    from bosses.heartwood_s1 import world
    sh = pelvis + [0, 18, 0]
    strips = 6 if take != "C" else 4
    stream = pose == ACT
    for i in range(strips):
        x = -7 + i * 14 / (strips - 1)
        length = 24 + 7 * ((i * 5) % 3) + (10 if take == "B" else 0)
        top = world(t, sh + [x, -1, 3.5])
        mid = top + _n([x * 0.03, -1, 0.35 if not stream else 0.8]) * length * 0.45
        end = mid + _n([x * 0.04, -0.55 if not stream else -0.25, 1]) * length * 0.6
        mat = "shroud" if take != "C" else "leather"
        seg(root, f"shroud{i}a", top, mid, 1.2, 5.2, mat)
        seg(root, f"shroud{i}b", mid, end, 1.2, 4.6 - (i % 2), "shroud_dark" if take != "C" else "leather")
    # arms and the bow
    bow_mat = "bone"
    if pose == REST:
        lh = pelvis + [-11, 6, -8]
        rh = pelvis + [9, 4, -4]
        bow = [lh + [0, -20, 4], lh + [0, -8, -3], lh, lh + [0, 12, -3], lh + [0, 24, 4]]
        string = [bow[0], bow[-1]]
    else:
        lh = pelvis + [-3, 24, -20]
        rh = pelvis + [3, 25, -1]
        bow = [lh + [0, -24, 7], lh + [0, -12, 1], lh, lh + [0, 12, 1], lh + [0, 24, 7]]
        string = [bow[0], rh, bow[-1]]
    for s, hand in ((-1, lh), (1, rh)):
        shoulder = sh + [s * 7, 0, 0]
        elbow = (shoulder + hand) / 2 + [s * 3, -4 if pose == REST else 1, 2]
        cbox(t, f"upper_arm{s}", shoulder, elbow, 2.6, 2.6, "bone")
        cbox(t, f"forearm{s}", elbow, hand, 2.4, 2.4, "bone")
    big = 1.25 if take == "B" else 1.0
    bow = [lh + (p - lh) * big for p in bow]
    if pose == ACT:
        string = [bow[0], rh, bow[-1]]
    else:
        string = [bow[0], bow[-1]]
    pts = curve(bow, 6)
    for i in range(6):
        cbox(t, f"bow{i}", pts[i], pts[i + 1], 2.4 - abs(i - 2.5) * 0.3, 2.2, bow_mat)
        if take == "B":         # a spine: vertebrae along it
            t.box(f"vert{i}", tuple(pts[i]), (3.4, 2, 3.4), "bone_dark")
    for i in range(len(string) - 1):
        cbox(t, f"string{i}", string[i], string[i + 1], 0.6, 0.6, "sinew")
    if pose == ACT:
        cbox(t, "arrow", rh, lh + [0, 0, -10], 0.9, 0.9, "bone_dark")
        t.box("arrow_tip", tuple(lh + [0, 0, -11]), (1.8, 1.8, 3), "bile")
    if take == "C":             # the censer of spores at the saddle
        c = S + [8, -6, 6]
        cbox(root, "censer_chain", S + [7, 1, 5], c, 0.8, 0.8, "steel")
        ball(root, "censer", tuple(c + [0, -3, 0]), (5, 5, 5), "plate_dark")
        root.box("censer_spores", tuple(c + [0, -3, 0]), (3.6, 3.6, 3.6), "eye_sick")
    return m


def war(m, take, pose):
    """The Vanguard."""
    root = m.group("war", (0, 0, 0))
    h = Horse(40, 44, 16, 18)
    hp = "gallop" if pose == ACT else "stand"
    hide = "roan"
    barrel(root, h, hide)
    legs(root, h, hp, hide, 5.0, 2.8, front_mat="roan_dark")
    poll, muzzle, npts = neck_head(root, h, "high", hide)
    if take == "A":
        caparison(root, h, hp)
        barding(root, h, poll, muzzle, npts)
        mane(root, npts, "roan_dark", h, n=6, length=5)
        tail(root, h, "roan_dark", hp, w=3.6)
    elif take == "B":           # bare, a burning mane and tail
        seg(root, "chanfron", poll + [0, 1.2, -0.8], poll + (muzzle - poll) * 0.8 + [0, 1.2, -0.8], 0.2 * h.H,
            0.18 * h.H, "plate")
        mane(root, npts, "flame", h, flame=True, n=7, length=8)
        tail(root, h, "roan_dark", hp, w=3.4, flame=True)
        root.box("saddle_cloth", (0, h.H + 1.5, -0.04 * h.L), (h.W * 1.25, 2, 16), "cloth")
    else:
        barding(root, h, poll, muzzle, npts, siege=True)
        mane(root, npts, "roan_dark", h, n=6, length=5)
        tail(root, h, "roan_dark", hp, w=3.6)
    # the rider: a zombie in heat-reddened plate
    k = 1.75
    S = h.saddle
    straddle(root, h, "plate_dark", "plate", k, stand=False)
    pelvis = S + [0, 3, 2]
    lean = 18 if pose == ACT else 0
    t = root.group("torso", tuple(pelvis), (-lean, 0, 0))
    t.box("faulds", tuple(pelvis + [0, 1, 0]), (15, 6, 10), "plate_dark")
    big = 1.25 if take == "B" else 1.0
    ball(t, "cuirass", tuple(pelvis + [0, 13, 0]), (17, 19, 11), "plate")
    neck = pelvis + [0, 23, 0]
    for s in (-1, 1):
        ball(t, f"pauldron{s}", tuple(neck + [s * 10 * big, -1, 0]), (11 * big, 9 * big, 12 * big), "plate",
             rot=(0, 0, s * -18))
    if take == "B":             # molten seams
        for i, y in enumerate((6, 12, 18)):
            t.box(f"seam{i}", tuple(pelvis + [0, y, -5.6]), (14 - i, 1.1, 0.8), "ember")
        for s in (-1, 1):
            t.box(f"pauldron_seam{s}", tuple(neck + [s * 12.5, -1, -5.5]), (10, 1, 0.8), "ember", rotation=(0, 0, s * -18))
    head = neck + [0, 7.5, 0]
    t.box("gorget", tuple(neck + [0, 1, 0]), (11, 4, 10), "plate_dark")
    t.box("helm", tuple(head), (12, 13.5, 12), "plate")
    t.box("visor_slit", tuple(head + [0, 1.5, -6.1]), (9, 1.4, 0.6), "ember")
    if take == "A":
        for i in range(3):
            t.box(f"crest{i}", tuple(head + [0, 8 + i * 0.6, -3 + i * 3]), (1.4, 4 + i, 3), "plate_dark")
    elif take == "C":           # a spiked crown-helm
        for c in range(7):
            a = math.radians(-90 + c * 30)
            t.box(f"spike{c}", tuple(head + [math.sin(a) * 5, 9 + (c == 3) * 2, -math.cos(a) * 5]),
                  (1.8, 7 + (c == 3) * 4, 1.8), "plate_dark", rotation=(-math.cos(a) * 18, 0, -math.sin(a) * 18))
    # the arms, the lance and the banner
    if pose == REST:
        rh = pelvis + [12, 12, -8]
        lh = pelvis + [-7, 10, -12]
    else:
        rh = pelvis + [9, 15, -6]
        lh = pelvis + [-6, 13, -14]
    for s, hand in ((-1, lh), (1, rh)):
        shoulder = neck + [s * 9, -3, 0]
        elbow = (shoulder + hand) / 2 + [s * 4, -4, 4]
        cbox(t, f"upper_arm{s}", shoulder, elbow, 5, 5, "plate")
        cbox(t, f"forearm{s}", elbow, hand, 4.4, 4.4, "plate_dark")
        t.box(f"gauntlet{s}", tuple(hand), (5, 5, 5), "plate")
    length = 84 if take == "C" else 76
    if pose == REST:
        butt, tip = rh + [0, -22, 0], rh + [0, length - 22, 0]
    else:
        d = _n([-0.06, 0.2, -1])
        butt, tip = rh - d * 18, rh + d * (length - 18)
    cbox(t, "lance", butt, tip, 2.4, 2.4, "wood")
    ld = _n(tip - butt)
    cbox(t, "cleaver", tip - ld * 2, tip + ld * 12, 2, 8, "steel")
    t.box("cleaver_back", tuple(tip + ld * 6 + np.array([0, 0, 3.5 if pose == REST else 0])), (1.6, 6, 4), "steel")
    scale = 1.3 if take == "C" else 1.0
    if take == "B":             # the banner on a pole strapped to his back, always flying
        top = pelvis + [0, 70, 10]
        cbox(t, "back_pole", pelvis + [0, 6, 7], top, 2.2, 2.2, "wood")
        cbox(t, "crossbar", top + [0, -2, -2], top + [0, -2, 22], 1.6, 1.6, "wood")
        bw, bh = 26, 34
        if pose == ACT:         # streaming straight back in the wind of the charge
            c = top + [0, -2 - bh * 0.3, bw * 0.62]
            t.box("banner", tuple(c), (1.2, bh * 0.6, bw * 1.25), "banner")
            t.box("sigil", tuple(c + [-0.5, 0, -2]), (1.4, 8, 10), "sigil")
            for i in range(3):
                t.box(f"tail{i}", tuple(c + [0, -bh * 0.18 + i * bh * 0.18, bw * 0.62 + 5 + 2 * (i % 2)]),
                      (1.2, bh * 0.14, 10), "banner")
        else:                   # hanging from the crossbar
            c = top + [0, -2 - bh / 2, bw / 2]
            t.box("banner", tuple(c), (1.2, bh, bw), "banner")
            t.box("sigil", tuple(c + [-0.5, 2, 0]), (1.4, 10, 8), "sigil")
            for i in range(3):
                t.box(f"tail{i}", tuple(c + [0, -bh / 2 - 4, -bw / 3 + i * bw / 3]), (1.2, 8 + 4 * (i % 2), bw / 3.6),
                      "banner")
    elif pose == REST:          # hanging from a crossbar near the lance's head, seen from the side
        bar = tip - ld * 14
        bw, bh = 22 * scale, 32 * scale
        cbox(t, "crossbar", bar + [0, 0, -3], bar + [0, 0, bw], 1.6, 1.6, "wood")
        c = bar + [0, -bh / 2 - 1, bw / 2 - 2]
        t.box("banner", tuple(c), (1.2, bh, bw), "banner")
        t.box("sigil", tuple(c + [-0.5, 3, 0]), (1.4, 12 * scale, 9 * scale), "sigil")
        for i in range(3):
            t.box(f"tail{i}", tuple(c + [0, -bh / 2 - 4, -bw / 3 + i * bw / 3]), (1.2, 8 + 4 * (i % 2), bw / 3.6),
                  "banner")
    else:                       # couched: it streams back under the shaft
        a = tip - ld * 14
        bw, bh = 30 * scale, 20 * scale
        c = a - ld * (bw / 2) + [0, -bh / 2 - 1, 0]
        yaw = math.degrees(math.atan2(-ld[0], -ld[2]))
        t.box("banner", tuple(c), (1.2, bh, bw), "banner", rotation=(-8, yaw, 0))
        t.box("sigil", tuple(c + [0.5, 1, 0]), (1.4, 9 * scale, 10 * scale), "sigil", rotation=(-8, yaw, 0))
        for i in range(3):
            t.box(f"tail{i}", tuple(c - ld * (bw / 2 + 5) + [0, -bh / 2 + 3 + i * 6, 0]), (1.2, 4.5, 10), "banner",
                  rotation=(-14 + i * 6, yaw, 0))
    # reins
    cbox(t, "rein", lh, muzzle + [0, 2, 0], 0.7, 0.7, "leather")
    return m


TAKES = {"A": "The Pale Crown and the Standard", "B": "Rot and Ruin", "C": "The Plague Doctor and the Siege"}
RIDERS = {"pestilence": pestilence, "war": war}
VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 58, "height": 3.0, "dist": 8.5, "target_z": 2.4},
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front", "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_low", "mode": "clay", "camera": "persp", "yaw": -34, "height": 1.62, "dist": 8.5, "target_z": 2.8,
     "player": False},
]
LABELS = {"flat_34": "three-quarter", "sil_front": "front, silhouette", "sil_side": "side, silhouette",
          "clay_low": "a player's eye"}
POSE_NAME = {"pestilence": {REST: "rest", ACT: "the snipe"}, "war": {REST: "rest", ACT: "the charge"}}


def build(take, rider, pose):
    return RIDERS[rider](Model(f"dread_{take}_{rider}_{pose}"), take, pose)


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
        rows = []
        for rider in RIDERS:
            for pose in poses:
                m = build(key, rider, pose)
                v2.run_blender(m.render_json(v2.PALETTE), OUT / key / rider / pose, views)
                rows.append((rider, pose))
                if pose == REST:
                    lo, hi = m.bounds()
                    print(key, rider, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
        # both together, from the side and three-quarter
        p = build(key, "pestilence", REST)
        w = build(key, "war", REST)
        boxes = shifted(p, -34) + shifted(w, 34)
        v2.run_blender(boxes, OUT / key / "pair", [PAIR_34, PAIR_SIDE])
        tw, th, pad, top = 400, 320, 12, 60
        img = Image.new("RGB", (pad + len(views) * (tw + pad), top + len(rows) * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Dread Riders, {key}: {TAKES[key]}", font=sheet._font(26), fill=sheet.INK)
        for r, (rider, pose) in enumerate(rows):
            for c, v in enumerate(views):
                x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
                img.paste(sheet._tile(OUT / key / rider / pose / f"{v['name']}.png", tw, th), (x, y))
                dr.text((x, y + th + 6), f"{rider.title()}, {POSE_NAME[rider][pose]}: {LABELS[v['name']]}",
                        font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / f"{key}_{TAKES[key].lower().replace(' ', '_')}.png")
    if not quick and keys == list(TAKES):
        compare()


def shifted(m, dx):
    """The model's boxes moved dx model units along x (to stand the two riders side by side)."""
    boxes = m.render_json(v2.PALETTE)
    for b in boxes:
        b["corners"] = [[p[0] + dx, p[1], p[2]] for p in b["corners"]]
    return boxes


PAIR_34 = {"name": "pair_34", "mode": "flat", "camera": "persp", "yaw": 30, "height": 3.2, "dist": 14, "target_z": 2.4}
PAIR_SIDE = {"name": "pair_side", "mode": "silhouette", "camera": "ortho_side", "player": True}


def compare():
    cols = [("pestilence/rest", "flat_34", "Pestilence"), ("pestilence/act", "flat_34", "Pestilence, the snipe"),
            ("war/rest", "flat_34", "War"), ("war/act", "flat_34", "War, the charge")]
    tw, th, pad, top = 400, 320, 12, 60
    img = Image.new("RGB", (pad + len(cols) * (tw + pad), top + len(TAKES) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Dread Riders, session 1: Pestilence and War, three takes", font=sheet._font(26), fill=sheet.INK)
    for r, key in enumerate(TAKES):
        for c, (folder, view, label) in enumerate(cols):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / key / folder / f"{view}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{key}: {label}", font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "compare.png")


if __name__ == "__main__":
    main(sys.argv[1:])
