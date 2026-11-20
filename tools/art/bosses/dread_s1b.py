"""Dread Riders, session 1, round 2: Pestilence and War, built as crafted models (2026-11-20).

Round 1 was rejected: the horses read as a donkey and a toy, the lance as goofy, the banner as cardboard. The user:
"the vanguard horse should look like a buffed warhorse, and should still be a zombie, like its rider ... the skeleton
horse looks like a donkey/pony. make it look intimidating, scary."

What changed:
- **One design per rider**, built part by part like a Blockbench model (whole-unit sizes, chamfered masses, every part
  placed by hand), not three generated takes.
- **The vanilla horse's head kept at a whole scale (1.6x)**: its cranium (6x5x7) and narrower muzzle (4x5x5), the ears,
  the head tilted down off a thick neck. Everything else at real horse proportions.
- **War's horse:** a buffed zombie destrier: a deep chest, heavy shoulders and haunches, a thick arched crest,
  feathered fetlocks over big hooves; rotting green-grey hide with wounds that show ribs and teeth, a torn ear, ember
  eyes; plate fitted to it (chanfron, crinet, peytral), a war saddle.
- **Pestilence's horse:** a skeleton horse as a predator: tall and long-legged, the head low and forward, the jaw
  hanging open; a spiked spine along the withers, a deep ribcage with a sick green plague glow inside it, hide rotting
  off the bones in rags, mould, bile.
- **The lance:** a war lance: a tapered shaft, a flared vamplate guarding the hand, a slim leaf blade.
- **The banner:** fastened along the lance like a flag, made of pleated strips so it falls in folds, a swallowtail
  end, a red sigil; streaming back when the lance is couched.

Model units: 16 = one block, y up, facing -z, its right side is +x.
Run from the repository root: python tools/art/bosses/dread_s1b.py [war] [pestilence] [quick]
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

OUT = ROOT / "docs/art/bosses/dread_riders/overhaul/s1_round2"
PALETTE = {
    # the zombie warhorse and War
    "zhide": (86, 104, 74), "zhide_dark": (62, 76, 56), "hair": (40, 44, 36), "flesh": (122, 50, 46),
    "wound": (60, 24, 24), "hoof": (44, 40, 36), "ember": (255, 126, 44), "teeth": (206, 196, 168),
    "plate": (92, 46, 38), "plate_edge": (150, 78, 52), "plate_dark": (48, 34, 32), "cloth": (124, 26, 24),
    "leather": (72, 52, 40), "wood": (78, 58, 42), "steel": (168, 166, 160), "banner": (30, 28, 30),
    "sigil": (178, 32, 28), "gold": (176, 140, 72),
    # the skeleton horse and Pestilence
    "bone": (222, 214, 192), "bone_dark": (160, 150, 128), "socket": (30, 30, 26), "plague": (170, 232, 80),
    "hide_rot": (96, 88, 72), "mould": (128, 150, 70), "bile": (150, 176, 52), "sinew": (118, 62, 54),
    "robe": (176, 170, 150), "robe_dark": (118, 112, 96), "crown": (172, 146, 84),
}
REST, ACT = "rest", "act"


def fbox(g, name, center, e1, e2, size, mat):
    """A box with its x along e1, its y along e2 (made orthogonal to e1): size (along e1, along e2, across both)."""
    e1 = _n(e1)
    e2 = _n(np.array(e2, float) - e1 * (np.array(e2, float) @ e1))
    e3 = np.cross(e1, e2)
    return g.box(name, tuple(np.array(center, float)), size, mat, rotation=tuple(euler(np.column_stack([e1, e2, e3]))))


def limb(g, name, a, b, w, d, mat, side=(1, 0, 0), extra=0.0):
    """A limb segment from a to b, w across (along `side`) and d deep; a little longer so joints overlap."""
    a, b = np.array(a, float), np.array(b, float)
    ln = float(np.linalg.norm(b - a))
    e1 = (b - a) / ln
    e2 = _n(np.cross(side, e1)) if abs(_n(side) @ e1) < 0.95 else _n(np.cross([0, 0, 1.0], e1))
    return fbox(g, name, (a + b) / 2, e1, e2, (ln + extra, d, w), mat)


# ==== War's zombie warhorse ============================================================================================

WAR_H = 40


def war_horse(g, pose):
    gallop = pose == ACT
    # -- the body: a deep chest, a heavy barrel, shoulders and haunches as their own masses
    ball(g, "barrel", (0, 30, 0), (20, 18, 30), "zhide")
    ball(g, "chest", (0, 29, -15), (19, 20, 12), "zhide", rot=(-8, 0, 0))
    ball(g, "rump", (0, 32, 15), (21, 18, 15), "zhide")
    ball(g, "croup", (0, 38.6, 13), (15, 5, 16), "zhide")
    ball(g, "withers", (0, 39.4, -9), (9, 5, 12), "zhide")
    for s in (-1, 1):
        ball(g, f"shoulder{s}", (s * 7.6, 30, -12), (6, 19, 14), "zhide", rot=(-18, 0, s * 4))
        ball(g, f"haunch{s}", (s * 7.8, 28.5, 15), (7, 19, 15), "zhide", rot=(10, 0, -s * 3))
    # wounds: a torn patch on the left flank with ribs showing, a gash on the right haunch
    g.box("flank_wound", (-10.2, 30, 1), (1, 10, 12), "wound")
    for r in range(4):
        g.box(f"flank_rib{r}", (-10.5, 30, -3.5 + r * 3), (1, 9, 1.6), "teeth", rotation=(-8, 0, 0))
    g.box("flank_flesh", (-10.4, 25.6, 1), (1, 2, 12), "flesh")
    g.box("haunch_gash", (11.6, 31, 15), (1, 2.4, 9), "flesh", rotation=(-20, 0, 0))
    # -- the neck: thick and arched, a stallion's crest
    base, mid, poll = np.array([0, 33.5, -19.0]), np.array([0, 44.0, -24.5]), np.array([0, 52.5, -28.0])
    if gallop:
        mid, poll = mid + [0, -2, -3], poll + [0, -4, -7]
    limb(g, "neck0", base, mid, 12, 16, "zhide")
    limb(g, "neck1", mid, poll, 9.5, 12, "zhide")
    ball(g, "crest", tuple((base + poll) / 2 + [0, 2.5, 4.5]), (8.5, 17, 8), "zhide", rot=(-30 if not gallop else -40, 0, 0))
    g.box("neck_gash", tuple((base + mid) / 2 + [6.2, 0, -2]), (1, 7, 2.2), "flesh", rotation=(-30, 0, 0))
    # mane: heavy, ragged, falling on the right side of the crest
    for i in range(6):
        p = base + (poll - base) * (0.1 + i * 0.16) + [3.8, 5.5, 6.0 - i * 0.6]
        g.box(f"mane{i}", tuple(p + [0, -4 - (i % 2) * 2, 0]), (2.2, 11 + (i % 3) * 3, 4.2), "hair",
              rotation=(-25 + (i % 2) * 8, 0, -12))
    # -- the head: vanilla's at 1.6x (cranium 6x5x7, muzzle 4x5x5), tilted down off the poll
    head = g.group("head", tuple(poll), (-52 if not gallop else -38, 0, 0))
    hx = np.array(poll)
    head.box("cranium", tuple(hx + [0, 0, -4.5]), (9.6, 8, 11.2), "zhide")
    head.box("muzzle", tuple(hx + [0, -0.8, -14.4]), (6.4, 7.6, 8.8), "zhide")
    ball(head, "jaw", tuple(hx + [0, -3.6, -5]), (8.4, 6, 10), "zhide_dark")
    head.box("nostrils", tuple(hx + [0, 0.6, -18.9]), (5, 2.2, 0.6), "wound")
    for s in (-1, 1):
        head.box(f"eye{s}", tuple(hx + [s * 4.85, 1.2, -6]), (0.6, 1.6, 2.6), "ember")
        # ears pinned back: angry
        ear = 5.2 if s > 0 else 3.0                                  # the left one torn
        head.box(f"ear{s}", tuple(hx + [s * 2.6, 4.6 + ear / 2 - 1, 0.6]), (2.6, ear, 1.6), "zhide",
                 rotation=(48, 0, s * -10))
    # the left cheek rotted through: teeth showing
    head.box("cheek_hole", tuple(hx + [-3.25, -2.6, -12]), (0.8, 3.4, 7), "wound")
    for k in range(4):
        head.box(f"tooth{k}", tuple(hx + [-3.3, -2.4, -9.5 - k * 1.8]), (0.9, 2.2, 1.2), "teeth")
    # chanfron: a plate down the face with a ridge and flared eye guards
    head.box("chanfron", tuple(hx + [0, 4.4, -9]), (8.4, 1.4, 15), "plate")
    head.box("chanfron_ridge", tuple(hx + [0, 5.3, -9]), (2, 1, 14), "plate_edge")
    for s in (-1, 1):
        head.box(f"eye_guard{s}", tuple(hx + [s * 5, 3, -6]), (1.2, 3.6, 4.4), "plate", rotation=(0, s * 20, s * -25))
    # crinet: overlapping lames down the crest
    for i in range(4):
        p = base + (poll - base) * (0.18 + i * 0.22) + [0, 6.2, 5.0 - i * 0.6]
        fbox(g, f"crinet{i}", p, poll - base, [0, 1, 0.6], (7.6, 1.4, 9.5 - i * 0.6), "plate")
    # peytral: a curved chest guard with a central boss
    g.box("peytral", (0, 29, -21.6), (13, 13, 1.8), "plate", rotation=(-10, 0, 0))
    for s in (-1, 1):
        g.box(f"peytral_side{s}", (s * 8.6, 29, -19.2), (6.5, 12, 1.8), "plate", rotation=(-8, s * -42, 0))
    g.box("peytral_rim", (0, 23, -22.6), (21, 1.4, 1.6), "plate_edge")
    ball(g, "peytral_boss", (0, 30, -23), (4, 4, 2.4), "plate_edge")
    # the war saddle and its red cloth
    g.box("seat", (0, 41.2, -1), (11, 2.4, 13), "leather")
    g.box("cantle", (0, 44, 5.6), (10.5, 5, 2.4), "leather", rotation=(-12, 0, 0))
    g.box("pommel", (0, 43.4, -7.4), (7.5, 4, 2.4), "leather", rotation=(10, 0, 0))
    for s in (-1, 1):
        g.box(f"saddlecloth{s}", (s * 10.6, 33, -1), (1, 15, 20), "cloth", rotation=(0, 0, s * 5))
        for t in range(5):
            g.box(f"dag{s}_{t}", (s * 10.3, 24.2, -8.6 + t * 3.8), (1, 3, 2.8), "cloth", rotation=(0, 0, s * 5))
        g.box(f"girth{s}", (s * 10.4, 30, -6), (1, 18, 2.6), "leather", rotation=(0, 0, s * 4))
    # -- the legs: thick forearms and gaskins, knees and hocks as knobs, feathered fetlocks, big hooves
    for s in (-1, 1):
        if gallop and s > 0:       # leading foreleg reaching out
            fl = [(s * 6.4, 31, -12.5), (s * 6.3, 22, -18), (s * 6.2, 17, -25), (s * 6.2, 12, -30)]
        elif gallop:               # the other folded under
            fl = [(s * 6.4, 31, -12.5), (s * 6.2, 21, -14), (s * 6.2, 13, -10), (s * 6.2, 13, -3)]
        else:
            fl = [(s * 6.4, 31, -12.5), (s * 6.3, 20, -13.2), (s * 6.2, 12.5, -13.6), (s * 6.2, 4.5, -14.4)]
        if gallop and s > 0:       # hind pushing off, stretched back
            hl = [(s * 7.2, 30, 14), (s * 7.2, 22, 15), (s * 7.0, 15, 26), (s * 6.8, 4.5, 33)]
        elif gallop:               # hind reaching under
            hl = [(s * 7.2, 30, 14), (s * 7.2, 21, 9), (s * 7.0, 15, 13), (s * 6.8, 4.5, 3)]
        else:
            hl = [(s * 7.2, 30, 14), (s * 7.2, 22.5, 12.4), (s * 7.0, 14, 19), (s * 6.8, 4.5, 17.2)]
        for tag, pts, wu in (("front", fl, 7.4), ("hind", hl, 7.8)):
            p = [np.array(q, float) for q in pts]
            limb(g, f"{tag}_upper{s}", p[0], p[1], wu, wu + 1.5, "zhide", extra=2)
            limb(g, f"{tag}_lower{s}", p[1], p[2], wu - 2, wu - 1, "zhide", extra=1.5)
            g.box(f"{tag}_joint{s}", tuple(p[2]), (wu - 2.2, 4, wu - 1.6), "zhide_dark")
            limb(g, f"{tag}_cannon{s}", p[2], p[3], 4.4, 5, "zhide_dark", extra=1)
            hoof_at = p[3] + _n(p[3] - p[2]) * 2.6
            for k in range(5):
                ang = math.radians(-60 + k * 60 + (30 if tag == "hind" else 0))
                out = np.array([math.sin(ang), 0, math.cos(ang)])
                root_p = p[3] + [0, 1.6, 0]
                limb(g, f"{tag}_feather{s}{k}", root_p, root_p + out * 3.4 + [0, -4.4, 0], 2.4, 1.2, "hair",
                     side=out)
            down = _n(p[3] - p[2])
            fbox(g, f"{tag}_hoof{s}", hoof_at, np.cross([1, 0, 0], down), -down, (7.2, 3.4, 6.6), "hoof")
    # -- the tail: thick and ragged, carried high in the gallop
    tail = [(0, 37.5, 22), (0, 35, 26.5), (0, 26, 29.5), (0, 15, 29)] if not gallop else \
        [(0, 37.5, 22), (0, 38, 28), (0, 34, 36), (0, 30, 43)]
    for i in range(3):
        limb(g, f"tail{i}", tail[i], tail[i + 1], 5 - i, 5.5 - i, "hair", extra=1.5)
    for k, dx in enumerate((-1.6, 1.4)):
        a = np.array(tail[2], float) + [dx, 0, 0]
        limb(g, f"tail_strand{k}", a, a + (np.array(tail[3]) - np.array(tail[2])) * (1.15 + 0.15 * k) + [dx, 0, 1],
             1.6, 1.6, "hair")
    return poll


# ==== War ==============================================================================================================

def war_rider(g, pose):
    gallop = pose == ACT
    lean = 20 if gallop else 4
    seat = np.array([0, 43.5, 0.0])
    # legs in greaves, astride; sabatons in the stirrups
    for s in (-1, 1):
        hip, knee, foot = seat + [s * 3.4, 2, 0], seat + [s * 11, -3, -8], seat + [s * 11.6, -15.5, -5]
        limb(g, f"thigh{s}", hip, knee, 6.6, 6.6, "plate_dark", extra=3)
        limb(g, f"greave{s}", knee, foot, 5.8, 6.2, "plate", extra=2)
        g.box(f"poleyn{s}", tuple(knee + [0, 0.5, -2.8]), (5.4, 4.4, 2), "plate_edge")
        g.box(f"sabaton{s}", tuple(foot + [0, -1.6, -2.2]), (6.2, 3.4, 9), "plate")
        g.box(f"stirrup{s}", tuple(foot + [0, -3.6, -1.8]), (7, 1.2, 6), "steel")
    t = g.group("torso", tuple(seat + [0, 2, 0]), (-lean, 0, 0))
    o = seat + [0, 2, 0]
    # faulds and the red tabard
    t.box("faulds", tuple(o + [0, 2.5, 0]), (15, 5, 10), "plate_dark")
    t.box("tabard", tuple(o + [0, -2.5, -5.4]), (9, 10, 1), "cloth")
    for k in range(3):
        t.box(f"tabard_dag{k}", tuple(o + [-3 + k * 3, -8.6, -5.4]), (2.4, 2.4 + (k % 2), 1), "cloth")
    # the cuirass: a barrel chest with a ridge, a waist
    octo(t, "cuirass", tuple(o + [0, 11, 0]), (15.5, 15, 10), "plate", cham=0.32, axis="z")
    t.box("cuirass_ridge", tuple(o + [0, 11, -5.2]), (2, 13, 1), "plate_edge")
    t.box("waist", tuple(o + [0, 4.6, 0]), (13, 3, 8.6), "plate_dark")
    # pauldrons: three lames each, sweeping out and down
    nk = o + [0, 19, 0]
    for s in (-1, 1):
        for i, (dx, dy, w, ang) in enumerate(((8.6, 0.4, 10.5, 18), (10.4, -2.4, 9.5, 30), (11.8, -5, 8.4, 42))):
            t.box(f"pauldron{s}_{i}", tuple(nk + [s * dx, dy, 0]), (w, 3, 11.5 - i), "plate" if i else "plate_edge",
                  rotation=(0, 0, -s * ang))
        t.box(f"pauldron_spike{s}", tuple(nk + [s * 8.2, 3.2, 0]), (2.2, 4.2, 2.2), "plate_dark", rotation=(0, 45, -s * 20))
    t.box("gorget", tuple(nk + [0, 1.4, 0]), (9, 3.6, 8.4), "plate_dark")
    # the great helm: faceted, an ember slit, breaths, a fin crest swept back
    hd = nk + [0, 9.2, -0.4]
    octo(t, "helm", tuple(hd), (12, 13, 12), "plate", cham=0.28, axis="y")
    t.box("helm_brow", tuple(hd + [0, 2.6, -6.1]), (10, 1.6, 1), "plate_edge")
    t.box("visor_slit", tuple(hd + [0, 1.1, -6.15]), (8.4, 1.2, 0.6), "ember")
    for k in range(3):
        t.box(f"breath{k}", tuple(hd + [2 + k * 1.2, -3, -6.1]), (0.6, 2.6, 0.6), "plate_dark")
    for i in range(4):
        t.box(f"crest{i}", tuple(hd + [0, 7.6 + i * 0.5 - (i == 3) * 1.6, -3.5 + i * 2.6]), (1.6, 4 + i * 0.6, 3.2),
              "plate_dark", rotation=(-12 - i * 6, 0, 0))
    # arms: the right in plate holding the lance; the left a bare zombie arm out of a torn sleeve, on the reins
    rh = o + ([11, 7, -9] if not gallop else [8.5, 8.5, -4])
    lh = o + [-6.5, 6, -12]
    for s, hand in ((1, rh), (-1, lh)):
        sh = nk + [s * 9, -2.5, 0]
        elbow = sh + [s * 2.5, -9, 3 if s > 0 else 1]
        limb(t, f"upper_arm{s}", sh, elbow, 6, 6, "plate" if s > 0 else "cloth", extra=2)
        limb(t, f"forearm{s}", elbow, hand, 5.6, 5.6, "plate" if s > 0 else "zhide", extra=1.5)
        t.box(f"hand{s}", tuple(hand), (5.4, 5.4, 5.4), "plate" if s > 0 else "zhide_dark")
    t.box("sleeve_rag", tuple(nk + [-10.2, -7.5, 0.5]), (1.2, 6, 5), "cloth", rotation=(0, 0, 12))
    return t, rh, lh


# ---- the lance and the banner -----------------------------------------------------------------------------------------

def lance(g, grip, axis, length=80, back=14):
    """A war lance through `grip` along `axis` (toward the tip): a tapered shaft, a flared vamplate guarding the
    hand, a socket and a slim leaf blade. Returns (tip, the point where the banner's top fastens)."""
    a = _n(axis)
    side = _n(np.cross(a, [0, 1, 0])) if abs(a[1]) < 0.9 else np.array([1.0, 0, 0])
    butt = grip - a * back
    tip = butt + a * length
    limb(g, "lance_butt", butt - a * 1.5, butt + a * 4, 3.2, 3.2, "plate_dark", side=side)
    limb(g, "lance_grip", butt + a * 4, grip + a * 3, 3.0, 3.0, "leather", side=side)
    # the vamplate: a cone of stacked octagonal discs flaring toward the front
    for i, (d, off) in enumerate(((5.5, 3.5), (7.5, 4.6), (9.5, 5.7))):
        c = grip + a * off
        o = g.group(f"vamplate{i}", tuple(c), (0, 0, 0))
        frame = np.column_stack([side, a, np.cross(side, a)])
        sub = o.group(f"vamplate{i}_r", tuple(c), tuple(euler(frame)))
        octo(sub, f"vamplate{i}_d", tuple(c), (d, 1.3, d), "plate", cham=0.3, axis="z")
    shaft = [(grip + a * 6.4, 3.2), (grip + a * 30, 2.6), (tip - a * 15, 2.0)]
    for i in range(2):
        limb(g, f"shaft{i}", shaft[i][0], shaft[i + 1][0], shaft[i][1], shaft[i][1], "wood", side=side, extra=1)
    socket = tip - a * 15
    limb(g, "socket", socket - a * 1, socket + a * 3.4, 2.8, 2.8, "steel", side=side)
    # the leaf blade: a diamond section (turned 45 degrees about the shaft), widest a third of the way up
    blade = [(socket + a * 3.4, 2.6), (socket + a * 7, 4.4), (socket + a * 11.5, 3.0), (tip, 0.8)]
    for i in range(3):
        a0, w0 = blade[i]
        a1, w1 = blade[i + 1]
        w = (w0 + w1) / 2
        c = (a0 + a1) / 2
        e2 = _n(side + np.cross(a, side))
        fbox(g, f"blade{i}", c, a, e2, (float(np.linalg.norm(a1 - a0)) + 0.6, w, w * 0.45), "steel")
        fbox(g, f"blade{i}_x", c, a, np.cross(a, e2), (float(np.linalg.norm(a1 - a0)) + 0.6, w * 0.45, w), "steel")
    return tip, socket - a * 1.5


def gonfanon(g, top, back=(0, 0, 1), width=24, height=34):
    """The war banner at rest: hung from a crossbar fixed under the lance's blade, falling in folds. Five panels
    across, each in two parts (the lower swung back a little, as cloth moves), pleated in and out, the bottom dagged into
    three points; a red sigil on both faces; gold finials on the bar, a cord."""
    back = _n(back)
    side = _n(np.cross([0, 1.0, 0], back))
    end = top + back * (width + 2)
    limb(g, "crossbar", top - back * 1.5, end, 1.8, 1.8, "wood", side=side)
    g.box("finial", tuple(end + back * 1.2), (2.6, 2.6, 2.6), "gold", rotation=(45, 0, 45))
    limb(g, "cord", end - back * 1, end + [0, -9, 0] + back * 0.5, 0.7, 0.7, "gold")
    g.box("tassel", tuple(end + [0, -10.5, 0] + back * 0.5), (1.6, 3, 1.6), "gold")
    panels = 5
    pw = width / panels
    drops = [height, height - 5, height + 3, height - 5, height]          # dagged: three points
    for i in range(panels):
        x0 = top + back * (1 + pw * (i + 0.5)) + side * (0.9 if i % 2 else -0.5)
        pleat = side * (0.9 if i % 2 else -0.5)
        h1 = drops[i] * 0.55
        h2 = drops[i] - h1
        c1 = x0 + [0, -h1 / 2 - 1, 0]
        fbox(g, f"banner{i}a", c1, back + pleat * 0.2, [0, 1, 0], (pw + 0.5, h1, 0.7), "banner")
        lower_top = x0 + [0, -h1 - 1, 0]
        sway = back * 2.4 + side * 0.4
        lower_end = lower_top + [0, -h2, 0] + sway
        fbox(g, f"banner{i}b", (lower_top + lower_end) / 2, back, lower_top - lower_end, (pw + 0.5, h2 + 0.6, 0.7),
             "banner")
        if i in (1, 2, 3):              # the sigil: a red flame-crowned blade across the middle panels
            for f in (-1, 1):
                fbox(g, f"sigil{i}{f}", c1 + [0, -2, 0] + side * f * 0.45, back, [0, 1, 0],
                     (pw + 0.1, h1 * (0.62 if i == 2 else 0.34), 0.3), "sigil")
        # the point at the bottom of each panel: a turned square half hidden in the cloth
        fbox(g, f"banner_tip{i}", lower_end + [0, 0.2, 0] - back * 0.2, back + [0, 1, 0], np.cross(side, back + [0, 1, 0]),
             (pw * 0.7, pw * 0.7, 0.7), "banner")
    limb(g, "banner_border", top + back * 0.6 + [0, -1.6, 0], top + back * (width + 0.6) + [0, -1.6, 0], 1.4, 1.2,
         "sigil", side=side)


def streamer(g, top, along, width=22, length=30, waves=8):
    """The war banner in the charge: fastened under the lance's blade and streaming back along it, rippling, its end
    split into tails. `along` points back along the shaft."""
    along = _n(along)
    down = _n(np.array([0, -1.0, 0]) - along * (-along[1]))
    n = np.cross(along, down)
    sl = length / waves
    pts = [top + along * sl * i + n * 1.1 * math.sin(i * math.pi / 2) + down * 0.06 * (i * sl) ** 1.3
           for i in range(waves + 1)]
    for i in range(waves):
        a, b = pts[i], pts[i + 1]
        w = width * (1 - 0.25 * i / waves)
        e = _n(b - a)
        c = (a + b) / 2 + down * w / 2
        fbox(g, f"streamer{i}", c, e, down, (float(np.linalg.norm(b - a)) + 0.5, w, 0.7), "banner")
        if 1 <= i <= 4:
            for f in (-1, 1):
                fbox(g, f"sigil{i}{f}", c + n * f * 0.4 - down * 1, e, down,
                     (float(np.linalg.norm(b - a)) + 0.1, w * 0.4, 0.3), "sigil")
    for k, f in enumerate((0.2, 0.75)):    # the two tails
        a = pts[-1] + down * width * 0.75 * f
        limb(g, f"streamer_tail{k}", a, a + along * 9 + down * (2 + 2 * k), width * 0.32, 0.7, "banner", side=n)
    limb(g, "streamer_border", top + down * 0.3, pts[-1] + down * 0.3, 1.2, 1.2, "sigil", side=n)


# ==== Pestilence's skeleton horse =======================================================================================

def bone_horse(g, pose):
    # -- the spine: vertebrae from the withers to the sacrum, the withers' spines rising tall and swept back
    heights = [9.5, 11, 10, 8.5, 6.5, 5, 4, 3.4, 3, 3, 3.2, 3.4]
    for k, hs in enumerate(heights):
        z = -15 + k * 2.75
        y = 38.6 - (0.6 if 4 < k < 9 else 0)
        g.box(f"vertebra{k}", (0, y, z), (3.4, 3.2, 2.4), "bone")
        a = np.array([0, y + 1.2, z])
        limb(g, f"spine_spike{k}", a, a + [0, hs, hs * 0.45], 1.6, 2.2 - 0.06 * k, "bone_dark" if k % 3 == 1 else "bone")
    # -- the ribcage: deep, curved ribs out from the spine and down to the sternum; floating ribs at the back
    for k in range(9):
        z = -14 + k * 2.9
        deep = 19.5 + abs(k - 2.5) * 0.9 if k < 7 else 26 + (k - 7) * 3
        for s in (-1, 1):
            p0 = np.array([s * 1.6, 37.6, z])
            p1 = np.array([s * 8.6, 33.5, z + 1.2])
            p2 = np.array([s * 9.4, 26.5, z + 2.4])
            p3 = np.array([s * (3 if k < 7 else 7.5), deep, z + 3.4])
            for i, (a, b) in enumerate(((p0, p1), (p1, p2), (p2, p3))):
                limb(g, f"rib{s}_{k}_{i}", a, b, 1.8, 2.2, "bone", side=(0, 0, 1), extra=1.2)
    limb(g, "sternum", (0, 20, -16), (0, 21.5, 2), 3.4, 2.4, "bone_dark", extra=1)
    # the plague: a sick green glow in the hollow of the ribcage
    ball(g, "plague", (0, 29.5, -4), (10, 11, 15), "plague")
    for s in (-1, 1):
        fbox(g, f"scapula{s}", (s * 8.4, 33, -12.5), [0, -1, -0.35], [0, 0, 1], (15, 8, 1.6), "bone")
        # the pelvis: the hip bones' wings, the ischium behind
        fbox(g, f"ilium{s}", (s * 6.8, 37.4, 13), [0, 0, 1], [s, 1.4, 0], (11, 5, 2), "bone")
        g.box(f"ischium{s}", (s * 4.6, 31, 19.5), (2.6, 7, 3.4), "bone", rotation=(-25, 0, 0))
    g.box("sacrum", (0, 37.8, 15.5), (5, 3, 9), "bone")
    # -- the neck: vertebrae rising forward, the head low and forward, a predator's
    neck = [np.array(p, float) for p in ((0, 37, -17), (0, 41, -22), (0, 43, -27.5), (0, 42, -33), (0, 39, -37.5))]
    for i in range(len(neck) - 1):
        limb(g, f"neck_vertebra{i}", neck[i], neck[i + 1], 4.6 - i * 0.3, 4.4 - i * 0.3, "bone", extra=-0.6)
        g.box(f"neck_spur{i}", tuple((neck[i] + neck[i + 1]) / 2 + [0, 3, 0]), (1.4, 2.4, 2), "bone_dark")
        for s in (-1, 1):
            g.box(f"neck_wing{s}{i}", tuple((neck[i] + neck[i + 1]) / 2 + [s * 2.6, -0.4, 0]), (1.6, 1.6, 3), "bone_dark")
    # the nuchal cord: a dried sinew from the tallest spine to the skull, slack
    limb(g, "nuchal", (0, 49, -11), (0, 44, -27), 1.2, 1.2, "sinew")
    limb(g, "nuchal_b", (0, 44, -27), neck[-1] + [0, 3, 0], 1.2, 1.2, "sinew")
    # -- the skull: vanilla's horse head at 1.6x as bone, pointed down and forward, the jaw hanging open
    poll = neck[-1]
    sk = g.group("skull", tuple(poll), (-58 if pose == REST else -46, 0, 0))
    hx = np.array(poll)
    octo(sk, "cranium", tuple(hx + [0, 0, -5]), (10.6, 9, 12.6), "bone", cham=0.25, axis="z")
    octo(sk, "snout", tuple(hx + [0, -0.8, -16.4]), (7, 6.8, 10.5), "bone", cham=0.25, axis="z")
    sk.box("nasal", tuple(hx + [0, 2.6, -14]), (2.6, 0.6, 6), "socket")
    for s in (-1, 1):
        sk.box(f"socket{s}", tuple(hx + [s * 4.9, 1.2, -7]), (1.4, 4, 4.6), "socket")
        sk.box(f"eye{s}", tuple(hx + [s * 5.25, 1.2, -7.2]), (0.6, 1.6, 1.6), "plague")
        sk.box(f"brow{s}", tuple(hx + [s * 4.6, 4.2, -7.2]), (2.6, 1.6, 5.6), "bone_dark", rotation=(0, 0, s * -14))
        sk.box(f"ear{s}", tuple(hx + [s * 2.6, 5, 1]), (2.2, 4, 1.4), "hide_rot", rotation=(40, 0, s * -18))
    for k in range(5):
        sk.box(f"tooth_up{k}", tuple(hx + [0, -4.6, -12 - k * 2]), (5.2, 1.8, 1.3), "teeth")
    jaw = sk.group("mandible", tuple(hx + [0, -3, 0]), (16 if pose == REST else 26, 0, 0))
    jaw.box("jaw", tuple(hx + [0, -5.4, -10.5]), (6, 2.6, 19), "bone")
    for k in range(4):
        jaw.box(f"tooth_low{k}", tuple(hx + [0, -3.9, -12.5 - k * 2]), (4.4, 1.6, 1.3), "teeth")
    for k, (dz, ln) in enumerate(((-12, 7), (-15.5, 10), (-17.5, 5))):
        jaw.box(f"drool{k}", tuple(hx + [(k - 1) * 1.4, -6 - ln / 2, dz]), (0.8, ln, 0.8), "bile")
    # -- legs: long bones, knobbed joints, bone hooves
    for s in (-1, 1):
        fl = [(s * 7.2, 31, -12), (s * 6.4, 23, -14), (s * 6.2, 12.5, -14 if s > 0 else -16),
              (s * 6.1, 4.2, -15 if s > 0 else -18.5)]
        hl = [(s * 7.4, 34, 13), (s * 7.2, 24, 8.6), (s * 6.8, 14, 19.5), (s * 6.6, 4.2, 17.6)]
        for tag, pts in (("front", fl), ("hind", hl)):
            p = [np.array(q, float) for q in pts]
            limb(g, f"{tag}_upper{s}", p[0], p[1], 3.8, 4.2, "bone", extra=1.5)
            g.box(f"{tag}_knob1{s}", tuple(p[1]), (4.4, 3.4, 4.4), "bone_dark")
            limb(g, f"{tag}_mid{s}", p[1], p[2], 2.8, 3.2, "bone", extra=1.2)
            g.box(f"{tag}_knob2{s}", tuple(p[2]), (3.8, 3.4, 4.2), "bone_dark")
            limb(g, f"{tag}_cannon{s}", p[2], p[3], 2.4, 2.6, "bone", extra=1)
            g.box(f"{tag}_fetlock{s}", tuple(p[3]), (3.2, 2.8, 3.4), "bone_dark")
            fbox(g, f"{tag}_hoof{s}", p[3] + [0, -2.4, -0.8], [0, 0, -1], [0, 1, 0.3], (5.4, 3, 4.6), "bone_dark")
            if tag == "hind":         # sinew still binding the hock
                limb(g, f"tendon{s}", p[1] + [0, 0, 2], p[2] + [0, 1, 1.8], 1, 1, "sinew")
    # -- the tail: a chain of shrinking vertebrae, a few rotten hair strands
    tail = [np.array(p, float) for p in ((0, 37.6, 20.5), (0, 35, 24.5), (0, 30, 27), (0, 24, 28), (0, 18, 27.5))]
    for i in range(len(tail) - 1):
        limb(g, f"tail_vertebra{i}", tail[i], tail[i + 1], 2.6 - i * 0.4, 2.6 - i * 0.4, "bone", extra=-0.8)
    for k, dx in enumerate((-1.2, 1.0)):
        limb(g, f"tail_hair{k}", tail[2] + [dx, 0, 0.6], tail[4] + [dx * 1.6, -9 - 3 * k, 2], 1.4, 0.8, "hide_rot")
    # -- rot: hide hanging off the bones in rags; a scrap of hide still on the hindquarters; mould
    rags = [((-5.5, 38, -6), 15, -8), ((6, 37.5, -1), 12, 10), ((-6.5, 37, 6), 16, -6), ((5.5, 36.5, 9), 10, 8),
            ((8.8, 32, -10), 9, 14)]
    for k, (p, ln, tilt) in enumerate(rags):
        p = np.array(p, float)
        fbox(g, f"rag{k}", p + [math.copysign(1.2, p[0]), -ln / 2, 0], [0, -1, 0.15], [0, 0, 1], (ln, 3.6, 0.8),
             "hide_rot")
    fbox(g, "hide_scrap", (5.4, 35.5, 15.5), [0, 0, 1], [1, -0.7, 0], (13, 6, 0.9), "hide_rot")
    for k, (p, sz) in enumerate((((-9.4, 28, -4), (0.6, 3, 4)), ((0, 41.2, -11), (2.6, 0.6, 3)),
                                 ((7.4, 22, -14), (0.6, 4, 2)))):
        g.box(f"mould{k}", p, sz, "mould")
    return poll


# ==== Pestilence =======================================================================================================

def pestilence_rider(g, pose):
    aim = pose == ACT
    seat = np.array([0, 41.5, 0.0])
    g.box("blanket", (0, 39.6, 0), (16, 1.2, 15), "robe_dark")
    for s in (-1, 1):
        fbox(g, f"blanket_side{s}", (s * 8.6, 35, 0.5), [0, -1, 0], [0, 0, 1], (10, 15, 0.8), "robe_dark")
        hip, knee, foot = seat + [s * 3, 1.5, 0.5], seat + [s * 10, -3, -7], seat + [s * 10.4, -15, -4]
        limb(g, f"femur{s}", hip, knee, 3.2, 3.2, "bone", extra=1.5)
        limb(g, f"shin{s}", knee, foot, 2.8, 2.8, "bone", extra=1.5)
        g.box(f"foot{s}", tuple(foot + [0, -1, -2]), (3.2, 2, 5.6), "bone_dark")
    hunch = 26 if not aim else 14
    t = g.group("torso", tuple(seat + [0, 2, 0]), (-hunch, 0, 0))
    o = seat + [0, 2, 0]
    t.box("pelvis", tuple(o + [0, 1, 0]), (10, 3.6, 5), "bone")
    limb(t, "spine", o + [0, 1, 1], o + [0, 21, 1], 2.4, 2.4, "bone_dark")
    # vanilla skeleton's ribcage: four ribs over a hollow, the plague glowing inside like the horse's
    ball(t, "chest_glow", tuple(o + [0, 13, 0]), (7, 8, 4), "plague")
    for k in range(4):
        t.box(f"rib{k}", tuple(o + [0, 9 + k * 2.8, -1.6]), (11 - abs(k - 1.5) * 0.8, 1.4, 4.4), "bone")
    nk = o + [0, 21, 0.6]
    # the rotten robe: hanging down the back and draping over the horse, in tatters
    for i in range(7):
        x = -7.5 + i * 15 / 6
        ln = 22 + 6 * ((i * 3) % 4)
        top = world(t, nk + [x, -4, 3.6])
        mid = top + _n([x * 0.02, -1, 0.05 if not aim else 0.3]) * ln * 0.45
        end = mid + _n([x * 0.03, -0.85, 1]) * ln * 0.6
        fbox(g, f"robe{i}a", (top + mid) / 2, mid - top, [0, 0, 1], (ln * 0.45 + 1, 3.6 - (i % 2) * 0.6, 0.9),
             "robe" if i % 3 else "robe_dark")
        fbox(g, f"robe{i}b", (mid + end) / 2, end - mid, [0, 1, 0], (ln * 0.6 + 1, 3.2 - (i % 2) * 0.6, 0.8),
             "robe_dark")
    # the skull in a deep hood: a long skull (a brow ridge over hollow sockets, cheekbones, the jaw hanging), the eyes
    # burning sick green out of the hood's shadow; the plague crown over the hood (a band, one triangle per point)
    hd = nk + [0, 7.4, -1.2]
    octo(t, "hood", tuple(hd + [0, 0.6, 1.6]), (13.4, 13.6, 13), "robe", cham=0.3, axis="z")
    t.box("hood_shadow", tuple(hd + [0, 0, -4.6]), (9.8, 10.2, 1), "socket")
    for f in (-1, 1):
        t.box(f"hood_lip{f}", tuple(hd + [f * 5.6, 0, -5]), (1.8, 11, 2.4), "robe_dark", rotation=(0, f * 10, 0))
    t.box("hood_peak", tuple(hd + [0, 6.4, -4.4]), (11, 2, 3), "robe_dark", rotation=(16, 0, 0))
    t.box("skull", tuple(hd + [0, -0.4, -2.6]), (8, 8.6, 7.6), "bone")
    t.box("brow_ridge", tuple(hd + [0, 2.2, -6.4]), (8, 1.6, 1.6), "bone")
    for f in (-1, 1):
        t.box(f"socket{f}", tuple(hd + [f * 2, 0.4, -6.5]), (2.8, 2.6, 0.6), "socket")
        t.box(f"eye{f}", tuple(hd + [f * 2, 0.4, -6.85]), (1.2, 1.2, 0.4), "plague")
        t.box(f"cheek{f}", tuple(hd + [f * 3.3, -1.8, -6]), (1.6, 1.8, 2), "bone_dark")
    t.box("nose", tuple(hd + [0, -1.6, -6.6]), (1.4, 1.8, 0.5), "socket")
    t.box("teeth_up", tuple(hd + [0, -3.3, -6.3]), (4.6, 1.2, 1), "teeth")
    jw = t.group("rider_jaw", tuple(hd + [0, -3.6, -3]), (14, 0, 0))
    jw.box("rider_jaw", tuple(hd + [0, -5, -5.2]), (5.6, 1.8, 4.4), "bone")
    jw.box("teeth_low", tuple(hd + [0, -4.1, -6.8]), (4.2, 1, 0.9), "teeth")
    t.box("crown_band", tuple(hd + [0, 7.2, 1.2]), (12.6, 2.4, 12.6), "crown", rotation=(-6, 0, 0))
    for c in range(5):
        a = math.radians(-90 + c * 45)
        p = hd + [math.sin(a) * 5.6, 8.8, -math.cos(a) * 5.6 + 1.2]
        t.box(f"crown_point{c}", tuple(p), (2.6, 2.6, 0.9), "crown", rotation=(0, -math.degrees(a), 45))
    # long thin arms (vanilla skeleton's 2x12x2 at 1.5x); the bow and the draw
    if aim:
        lh, rh = o + [-2, 24, -21], o + [3.5, 26, -1]
    else:
        lh, rh = o + [-10, 11, -8], o + [7, 12, -7]
    for s, hand in ((-1, lh), (1, rh)):
        sh = nk + [s * 7, -2, 0]
        elbow = sh + (hand - sh) * 0.5 + [s * 3.5, -3 if not aim else 1, 3]
        limb(t, f"humerus{s}", sh, elbow, 3, 3, "bone", extra=1)
        limb(t, f"radius{s}", elbow, hand, 2.6, 2.6, "bone", extra=1)
        t.box(f"hand{s}", tuple(hand), (3.2, 3.2, 3.2), "bone_dark")
    # the rib bow: a long recurve of bone bound with sinew
    up = np.array([0, 1.0, 0.0]) if aim else _n([0, 1, -0.25])
    fwd = np.array([0, 0, -1.0])
    bow = [lh + up * 26 + fwd * 5, lh + up * 20 + fwd * -1, lh + up * 9 + fwd * -2.5, lh,
           lh - up * 9 + fwd * -2.5, lh - up * 20 + fwd * -1, lh - up * 26 + fwd * 5]
    for i in range(len(bow) - 1):
        limb(t, f"bow{i}", bow[i], bow[i + 1], 2.4 - abs(i - 2.5) * 0.3, 2.8 - abs(i - 2.5) * 0.3, "bone",
             side=(1, 0, 0), extra=0.8)
    for k in (-1, 1):
        t.box(f"bow_wrap{k}", tuple(lh + up * k * 3), (3, 1.4, 3.4), "sinew")
    nock = rh if aim else (bow[0] + bow[-1]) / 2
    limb(t, "string_a", bow[0], nock, 0.6, 0.6, "sinew")
    limb(t, "string_b", nock, bow[-1], 0.6, 0.6, "sinew")
    if aim:
        limb(t, "arrow", rh, lh + fwd * 9, 0.9, 0.9, "bone_dark")
        t.box("arrow_head", tuple(lh + fwd * 10.5), (1.8, 1.8, 3), "plague")
    # the quiver on its back: bone-fletched arrows
    q = o + [5, 15, 5.5]
    limb(t, "quiver", q + [0, -9, 0], q + [-2, 7, 0], 4.2, 4.2, "leather", side=(0, 0, 1))
    for k in range(3):
        limb(t, f"fletch{k}", q + [-2 + k * 1.2, 7, 0], q + [-2.6 + k * 1.3, 11.5, 0.5], 1, 1.6, "bone")
    return t


# ==== building, rendering ==============================================================================================

def build(rider, pose):
    m = Model(f"dread_{rider}_{pose}")
    root = m.group(rider, (0, 0, 0))
    if rider == "war":
        war_horse(root, pose)
        t, rh, lh = war_rider(root, pose)
        if pose == REST:
            tip, top = lance(t, rh, [0, 1, 0], length=82, back=20)
            gonfanon(t, top + [0, -1, 0])
        else:
            axis = np.array([-0.05, 0.36, -1])
            tip, top = lance(t, rh, axis, length=82, back=18)
            streamer(t, top, -_n(axis))
        limb(t, "rein", lh, lh + [5, -10, -14], 0.8, 0.8, "leather")
    else:
        bone_horse(root, pose)
        pestilence_rider(root, pose)
    return m


VIEWS = [
    {"name": "hero", "mode": "flat", "camera": "persp", "yaw": 42, "height": 2.6, "dist": 8.0, "target_z": 2.5},
    {"name": "front", "mode": "flat", "camera": "persp", "yaw": -18, "height": 2.2, "dist": 8.0, "target_z": 2.4,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "low", "mode": "clay", "camera": "persp", "yaw": 30, "height": 1.62, "dist": 7.5, "target_z": 2.9,
     "player": False},
]
LABELS = {"hero": "three-quarter", "front": "front-left", "sil_side": "side, silhouette", "low": "a player's eye"}
NAMES = {("war", REST): "War", ("war", ACT): "War, the charge", ("pestilence", REST): "Pestilence",
         ("pestilence", ACT): "Pestilence, the snipe"}


def main(args):
    quick = "quick" in args
    riders = [r for r in ("war", "pestilence") if r in args] or ["war", "pestilence"]
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    views = VIEWS[:1] + VIEWS[2:3] if quick else VIEWS
    rows = []
    for rider in riders:
        for pose in ((REST,) if quick else (REST, ACT)):
            m = build(rider, pose)
            d = OUT / rider / pose
            if d.exists():
                shutil.rmtree(d)
            v2.run_blender(m.render_json(v2.PALETTE), d, views)
            lo, hi = m.bounds()
            print(rider, pose, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
            rows.append((rider, pose))
    tw, th, pad, top = 440, 340, 12, 60
    img = Image.new("RGB", (pad + len(views) * (tw + pad), top + len(rows) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Dread Riders, session 1 round 2: Pestilence and War", font=sheet._font(26), fill=sheet.INK)
    for r, (rider, pose) in enumerate(rows):
        for c, v in enumerate(views):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / rider / pose / f"{v['name']}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{NAMES[(rider, pose)]}: {LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / ("sheet_" + "_".join(riders) + ("_quick" if quick else "") + ".png"))


if __name__ == "__main__":
    main(sys.argv[1:])
