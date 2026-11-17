"""The Tidebreaker redesign, session 1 step 1: three takes on the Last Harpooner, as cuboid blockouts.

The brief (docs/art/bosses/tidebreaker/overhaul/plan.md, 2026-11-04): a drowned whaler in a sou'wester, barnacled
and mutated, riding a colossal nautilus wrapped in harpoon lines and nets. The front of the shell (the end away from
the tentacles: a nautilus swims shell first) is a makeshift ship's bow of planks with one decorated figurehead, a
piece of an old ship nailed onto it.

The nautilus is built the way a cuboid model can be round: the coil's keel is a drum of tilted panels round the x
axis (an octagonal cross-section: a top panel, two 45-degree shoulders), its flanks 16-sided plates, the panels left
out at the back where the body sits in the opening: the hood, the side eyes, the tentacles trailing behind.
The three takes differ in the piece of ship and where he rides:
  A  the Maiden's Prow    a merchantman's carvel bow, a bowsprit with the whaler's lantern, a carved maiden
                          leaning out under it; he sits in a lashed saddle on the shell's crest
  B  the Serpent Stem     a clinker-built bow whose stem post rises and curls into a carved sea serpent, the
                          lantern hanging from its jaws; he sits on the crest
  C  the Harpooner's Bow  a bigger, broken bow section with a carved eagle spreading its wings along the planks; he
                          stands braced in it like a whaleboat's harpooner, the shell rising behind him
Each is shown idle and in the ram (the tentacles pulled in, the bow dipped, the harpoon lowered like a lance).
Model units: 16 = one block, y up, the bow towards -z. The blue figure is a player (1.8 blocks). Colours are blockout
zones, not the palette; the net is see-through.

Run from the repository root: python tools/art/bosses/tide_silhouettes.py [A B C]
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import monarch_s1 as ms, volley_crone_s2 as v2, volley_s1 as v1  # noqa: E402

OUT = ROOT / "docs/art/bosses/tidebreaker/overhaul/s1_silhouettes"
PALETTE = {
    "shell": (226, 212, 186), "stripe": (176, 78, 56), "shell_in": (150, 128, 112), "nacre": (206, 214, 222),
    "body": (172, 66, 52), "hood": (112, 50, 42), "tentacle": (198, 92, 70), "naut_eye": (226, 196, 120),
    "pupil": (16, 18, 22),
    "wood": (116, 100, 84), "wood_dark": (74, 62, 54), "iron": (88, 90, 96), "rope": (172, 146, 100),
    "net": (160, 138, 98, 110), "glow": (255, 214, 110),
    "paint_white": (222, 214, 196), "paint_red": (150, 52, 44), "paint_blue": (64, 84, 124), "paint_green": (70, 110, 84),
    "oilskin": (196, 160, 72), "oilskin_dark": (132, 106, 52), "skin": (90, 138, 122), "skin_dark": (62, 98, 88),
    "barnacle": (204, 198, 182), "eye": (255, 226, 130), "boot": (52, 46, 42),
}
K = 1.3                       # the rider: a drowned at 1.3 times


# ---- placing cubes by frame ----------------------------------------------------------------------------------------

def _n(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


def euler(m):
    """bosskit's rotation (degrees, X then Y then Z) for a rotation matrix whose columns are the cube's local axes."""
    y = math.asin(max(-1.0, min(1.0, -m[2, 0])))
    x = math.atan2(m[2, 1], m[2, 2])
    z = math.atan2(m[1, 0], m[0, 0])
    return tuple(math.degrees(a) for a in (x, y, z))


def frame(xdir, ydir):
    """A right-handed frame: local x along xdir, local y as close to ydir as it can be."""
    x = _n(xdir)
    z = _n(np.cross(x, ydir))
    return np.column_stack([x, np.cross(z, x), z])


def obox(g, name, center, size, m, mat):
    return g.box(name, tuple(center), size, mat, rotation=euler(m))


def plank(g, name, a, b, h, t, mat, up=(0, 1, 0), out=0.0):
    """A flat board from a to b: h tall (towards up), t thick; out pushes it along its face normal."""
    a, b = np.array(a, float), np.array(b, float)
    m = frame(b - a, up)
    c = (a + b) / 2 + m[:, 2] * out
    return obox(g, name, c, (float(np.linalg.norm(b - a)) + 0.6, h, t), m, mat)


def beam(g, name, a, b, w, mat):
    return v1.beam(g, name, tuple(map(float, a)), tuple(map(float, b)), w, mat)


def plate(g, name, c, r, t, mat):
    """A round plate across the x axis: a true octagon of apothem r (a cross of two bars, four 45-degree corner plates
    filling its notches), each piece a hair thinner than the last so no two faces share a plane."""
    x, y, z = c
    side = 2 * r * math.tan(math.pi / 8)
    cut = r - side / 2
    thick = cut / math.sqrt(2) + 0.8
    reach = (r - thick / 2) / math.sqrt(2)
    g.box(name + "_h", (x, y, z), (t, side, 2 * r), mat)
    g.box(name + "_v", (x, y, z), (t - 0.15, 2 * r, side), mat)
    for i, (sz, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1))):
        g.box(f"{name}_c{i}", (x, y + sy * reach, z + sz * reach), (t - 0.3, thick, side + 0.4), mat,
              rotation=(45 * sz * sy, 0, 0))


# ---- the nautilus --------------------------------------------------------------------------------------------------

CY, CZ, R, W = 28.0, 4.0, 26.0, 28.0          # the coil's centre (y, z), its radius, its width: 3.25 x 1.75 blocks
CH = 6.0                                        # the shoulders' chamfer: a narrow, rounded keel


def shell_point(theta, r=R):
    """A point on the keel circle: theta 0 at the top, 90 at the front (-z), 180 under, 270 at the back."""
    t = math.radians(theta)
    return np.array([0.0, CY + r * math.cos(t), CZ - r * math.sin(t)])


def front_z(y, r=R):
    return CZ - math.sqrt(max(0.0, r * r - (y - CY) ** 2))


def shell(g, n=22, t=3.0, skip=(212, 328), stripes=True):
    """The coil: a drum of panels round the x axis (an octagonal section: a narrow keel, two 45-degree shoulders),
    its flanks domed in three octagon steps to the callus, tiger stripes radiating over them. Panels with theta
    inside skip are left out: the opening at the back, whose two edges flare out into the lip."""
    chord = 2 * R * math.tan(math.pi / n) * 1.06
    ths = [360 * i / n + 180 / n for i in range(n)]
    lips = {max(i for i, th in enumerate(ths) if th < skip[0]), min(i for i, th in enumerate(ths) if th > skip[1])}
    for i, th in enumerate(ths):
        if skip[0] < th < skip[1]:
            continue
        rad = _n(shell_point(th) - np.array([0, CY, CZ]))
        tan = np.array([0.0, -math.sin(math.radians(th)), -math.cos(math.radians(th))])
        striped = stripes and i % 2 == 0 and not (190 < th < 345)
        mat = "stripe" if striped else "shell"
        lip = 2.0 if i in lips else 0.0
        p = np.array([0, CY, CZ]) + rad * (R - t / 2 + lip * 0.5)
        obox(g, f"keel_{i}", p, (W - 2 * CH + 0.4 + lip, t, chord), frame((1, 0, 0), rad), mat)
        for s in (-1, 1):
            nrm = _n(rad + np.array([s, 0, 0]))
            q = (np.array([0, CY, CZ]) + rad * (R - CH / 2 - t / 2 * 0.7 + lip * 0.5)
                 + np.array([s * (W / 2 - CH / 2 - t / 2 * 0.7 + lip * 0.5), 0, 0]))
            obox(g, f"shoulder_{i}_{s}", q, (chord, t, CH * math.sqrt(2) + 0.6), frame(tan, nrm), mat)
    for s in (-1, 1):
        side = "l" if s < 0 else "r"
        plate(g, f"flank_{side}", (s * (W / 2 - t / 2), CY, CZ), R - CH - 0.6, t, "shell")
        plate(g, f"dome_{side}", (s * (W / 2 + 1.0), CY, CZ), R * 0.66, 2.4, "shell")
        plate(g, f"whorl_{side}", (s * (W / 2 + 2.6), CY, CZ), R * 0.36, 2.2, "shell")
        plate(g, f"callus_{side}", (s * (W / 2 + 3.8), CY, CZ), R * 0.15, 1.6, "shell_in")
        if stripes:                                          # the tiger stripes: in from the rim, fading out
            for j, th in enumerate(th for i, th in enumerate(ths) if i % 2 == 0 and not (190 < th < 345)):
                a, b = shell_point(th, R - CH - 1.5), shell_point(th - 14, R * 0.5)
                plank(g, f"stripe_{side}{j}", (s * (W / 2 - 0.1), a[1], a[2]), (s * (W / 2 + 1.9), b[1], b[2]), 4.6,
                      0.6, "stripe", up=(1, 0, 0))


def body(g, tentacles=1.0):
    """The animal in the opening at the back: a chamfered body, the leathery hood sloping down over it, an eye on each
    side, the siphon, and the tentacle mass trailing behind and curling down (tentacles: 1 idle, small when pulled in
    for the ram)."""
    zb = CZ + R * 0.62
    ms.octo(g, "body", (0, CY - 3, zb + 3), (W - 6, R * 0.95, 16), "body", cham=0.32)
    ms.octo(g, "hood", (0, CY + R * 0.4, zb + 7), (W - 2, 11, 19), "hood", cham=0.4, rot=(-18, 0, 0))
    for s in (-1, 1):
        side = "l" if s < 0 else "r"
        plate(g, f"eye_{side}", (s * ((W - 6) / 2 + 0.8), CY + 2, zb + 5), 4.4, 1.6, "naut_eye")
        g.box(f"pupil_{side}", (s * ((W - 6) / 2 + 1.7), CY + 2, zb + 5), (0.6, 1.6, 5.4), "pupil")
    beam(g, "siphon", (0, CY - 12, zb + 8), (0, CY - 14, zb + 16), 5.5, "body")
    mouth = np.array([0, CY - 4, zb + 11])
    for i in range(12):
        a = math.radians(i * 30 + 15)
        ring_r = 9 if i % 2 == 0 else 6
        base = mouth + np.array([math.cos(a) * ring_r, math.sin(a) * ring_r * 0.8, 0])
        sp = np.array([math.cos(a), math.sin(a) * 0.6, 0])
        long_ = (1.0 if i % 2 == 0 else 0.7) * (1 + 0.15 * ((i * 7) % 3)) * tentacles
        dirs = [sp * 0.45 + (0, -0.15, 1), sp * 0.3 + (0, -0.6, 0.8), sp * 0.15 + (0, -1, 0.15)]
        p0 = base
        for j, (d, ln, w) in enumerate(zip(dirs, (10, 9, 7), (4.4, 3.4, 2.4))):
            p1 = p0 + _n(d) * ln * long_
            beam(g, f"tentacle{i}_{j}", p0, p1, w, "tentacle")
            p0 = p1


def lashing(g, name, z, out=1.0, w=1.4):
    """A rope belted round the coil at one z: over the keel, down both flanks, under it."""
    h = math.sqrt(max(0.0, R * R - (z - CZ) ** 2)) + out
    hw = W / 2 + out
    pts = [(-hw + CH, CY + h), (hw - CH, CY + h), (hw, CY + h - CH), (hw, CY - h + CH), (hw - CH, CY - h),
           (-hw + CH, CY - h), (-hw, CY - h + CH), (-hw, CY + h - CH)]
    for i, (a, b) in enumerate(zip(pts, pts[1:] + pts[:1])):
        beam(g, f"{name}_{i}", (a[0], a[1], z), (b[0], b[1], z), w, "rope")


def net(g, th0=282, th1=352, n=20):
    """A fishing net thrown over the back of the crest and hanging down the flanks."""
    chord = 2 * (R + 1) * math.tan(math.pi / n) * 1.1
    for i in range(n):
        th = 360 * i / n + 180 / n
        if th0 < th < th1:
            rad = _n(shell_point(th) - np.array([0, CY, CZ]))
            obox(g, f"net_{i}", np.array([0, CY, CZ]) + rad * (R + 0.8), (W + 3, 0.6, chord), frame((1, 0, 0), rad),
                 "net")
    for s in (-1, 1):
        g.box(f"net_side_{s}", (s * (W / 2 + 1.4), CY + 9, CZ + 9), (0.6, 13, 16), "net", rotation=(-30, 0, 0))


def stuck_harpoon(g, name, at, d, seat, length=15):
    """An old harpoon stuck in the shell, its line running up to the saddle."""
    at, d = np.array(at, float), _n(d)
    end = at + d * length
    beam(g, name + "_shaft", at, end, 1.4, "wood_dark")
    beam(g, name + "_head", at - d * 1.5, at + d * 2, 2.6, "iron")
    sag = (end + np.array(seat)) / 2 + np.array([0, -4, 0])
    beam(g, name + "_line_a", end, sag, 1.0, "rope")
    beam(g, name + "_line_b", sag, seat, 1.0, "rope")


# ---- the bow -------------------------------------------------------------------------------------------------------

def bow(g, d_top=16.0, d_bot=5.0, top=34.0, bottom=138.0, step=4.4, h=4.7, clinker=False, flank_back=9.0,
        ragged=False, flare=0.16, sheer=6.0):
    """A ship's bow nailed over the front of the coil: horizontal strakes from the stem round to the flanks, a stem
    post down to the forefoot. Returns the stem's top (where a figurehead or bowsprit goes) and the gunwale's y."""
    yt, yb = CY + R * math.cos(math.radians(top)), CY + R * math.cos(math.radians(bottom))
    ys = np.arange(yt, yb, -step)
    stem = []
    for k, y in enumerate(ys):
        f = (y - yb) / (yt - yb)
        d = d_bot + (d_top - d_bot) * f
        zf = front_z(y, R + 0.5)
        hw = (W / 2 + 1.5) * min(1.0, 1.35 * math.sqrt(max(0.0, 1 - ((y - CY) / R) ** 2)))
        back = flank_back * (0.6 + 0.4 * f) + (((k * 7) % 5) - 2) * 1.6 * ragged
        zs = zf - d
        lift = sheer * f * f                                  # the sheer: each strake sweeps up to the stem
        stem.append((y + lift, zs))
        for s in (-1, 1):
            side = "l" if s < 0 else "r"
            pts = [(0, y + lift, zs), (s * hw * 0.64, y + lift * 0.3, zf - d * 0.42), (s * hw, y, zf + back)]
            up = (s * flare, 1, 0)
            for j, (a, b) in enumerate(zip(pts, pts[1:])):
                plank(g, f"strake{k}_{side}{j}", a, b, h + (0.8 if clinker else 0), 2.0, "wood", up=up,
                      out=(0.5 * k if clinker else 0))
            if k == 0:                                       # the gunwale's cap rail
                for j, (a, b) in enumerate(zip(pts, pts[1:])):
                    beam(g, f"rail_{side}{j}", np.array(a) + (0, h / 2 + 0.6, 0), np.array(b) + (0, h / 2 + 0.6, 0),
                         2.4, "wood_dark")
    for k, ((y0, z0), (y1, z1)) in enumerate(zip(stem, stem[1:])):
        beam(g, f"stem{k}", (0, y0 + 1, z0 - 0.8), (0, y1, z1 - 0.8), 3.6, "wood_dark")
    # the forefoot: the stem curving under the coil, shod with iron (the ram's cutting edge)
    y_last, z_last = stem[-1]
    prev = np.array([0, y_last, z_last - 0.8])
    for k, th in enumerate(np.linspace(bottom + 6, 176, 4)):
        p = shell_point(th, R + 2.5)
        beam(g, f"forefoot{k}", prev, p, 3.6, "wood_dark")
        beam(g, f"cutwater{k}", prev + (0, 0, -1.6), p + (0, 0, -1.6), 1.6, "iron")
        prev = p
    return np.array([0, stem[0][0], stem[0][1]]), stem[0][0] + h / 2


def lantern(g, name, hang):
    x, y, z = hang
    beam(g, name + "_cord", (x, y, z), (x, y - 3, z), 0.8, "rope")
    g.box(name + "_cap", (x, y - 3.6, z), (3.6, 1.2, 3.6), "iron")
    g.box(name, (x, y - 6, z), (3, 4, 3), "glow")
    g.box(name + "_base", (x, y - 8.4, z), (3.6, 1, 3.6), "iron")


def maiden(g, base, lean=-40, k=1.7):
    """A carved maiden leaning out under the bowsprit: a scroll into the stem, robe, arms crossed, hair blown back."""
    f = g.group("figurehead", tuple(base), (lean, 0, 0))
    x, y, z = base
    f.box("scroll", (x, y + 2.5 * k, z), (5.5 * k, 5 * k, 5 * k), "paint_white")
    f.box("robe", (x, y + 8 * k, z), (5.4 * k, 7 * k, 4.2 * k), "paint_blue")
    f.box("torso", (x, y + 13.2 * k, z), (4.8 * k, 4.6 * k, 3.2 * k), "paint_white")
    f.box("arms", (x, y + 12.6 * k, z - 1.9 * k), (5.8 * k, 2 * k, 1.4 * k), "paint_white")
    f.box("head", (x, y + 17.4 * k, z - 0.3 * k), (3.8 * k, 4.2 * k, 3.8 * k), "paint_white")
    f.box("hair", (x, y + 16.6 * k, z + 2.2 * k), (4.4 * k, 5.4 * k, 1.4 * k), "paint_red")
    return f


def serpent(g, top):
    """The stem post rising and curling forward into a carved sea serpent, jaws open; a fin down its neck."""
    p = top + np.array([0, 0, -0.8])
    pts = [p, p + (0, 7, -3), p + (0, 13, -3), p + (0, 17, -1)]
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        beam(g, f"neck{i}", a, b, 4.2 - i * 0.4, "paint_green")
    head = pts[-1] + np.array([0, 0.5, -5])
    g.box("serpent_skull", head, (5, 4.6, 8), "paint_green")
    g.box("serpent_snout", head + (0, -0.4, -5.6), (3.8, 3.2, 4), "paint_green")
    g.box("serpent_jaw", head + (0, -3.8, -3.6), (4, 1.6, 8), "paint_green", rotation=(-22, 0, 0))
    for s in (-1, 1):
        g.box(f"serpent_eye_{s}", head + (s * 2.6, 1.0, -1.8), (0.6, 1.6, 1.6), "paint_red")
        g.box(f"serpent_horn_{s}", head + (s * 1.6, 3.4, 2.6), (1.2, 1.2, 4.5), "paint_red", rotation=(28, 0, 0))
    for i, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
        m = (a + b) / 2 + np.array([0, 0, 2.4])
        g.box(f"fin{i}", m, (0.8, 3.6, 2.8), "paint_red", rotation=(-20 + 25 * i, 0, 0))
    return head + np.array([0, -5, -6])                       # where the lantern hangs (from the jaw)


def eagle(g, y, z_stem, zf, hw):
    """A carved eagle at the stem, head and beak forward, its wings spread back along both sides of the bow."""
    g.box("eagle_head", (0, y + 2, z_stem - 2.5), (4.4, 4.6, 5), "paint_white")
    g.box("eagle_beak", (0, y + 1, z_stem - 6), (2.4, 2.6, 3.4), "oilskin", rotation=(18, 0, 0))
    g.box("eagle_breast", (0, y - 3, z_stem - 1.2), (5, 6, 3.5), "paint_red")
    for s in (-1, 1):
        side = "l" if s < 0 else "r"
        a = np.array([s * 1.5, y - 1, z_stem + 0.5])
        b = np.array([s * hw * 0.78, y + 3, zf - 1.0])
        plank(g, f"wing_{side}", a, b, 7, 1.4, "paint_white", up=(s * 0.14, 1, 0), out=-1.4 * s)
        for i in range(4):
            c = b + np.array([s * 0.7, -2.5 + i * 2.2, 3.0 + i * 1.6])
            plank(g, f"feather_{side}{i}", b + np.array([0, -1 + i * 1.5, 0]), c, 2.2, 1.2, "paint_white",
                  up=(s * 0.14, 1, 0), out=-1.4 * s)


# ---- the rider -----------------------------------------------------------------------------------------------------

def sou_wester(g, top, k=K):
    """The whaler's sou'wester: a low crown, a short front brim and a long back brim turned down over the neck."""
    x, y, z = top
    g.box("hat_crown", (x, y + 1.6 * k, z + 0.4), (8.6 * k, 3.2 * k, 8.6 * k), "oilskin")
    g.box("hat_brim_front", (x, y - 0.1, z - 5.0 * k), (10 * k, 0.7 * k, 2.4 * k), "oilskin", rotation=(-12, 0, 0))
    for s in (-1, 1):
        g.box(f"hat_brim_{s}", (x + s * 5.2 * k, y - 0.6 * k, z + 0.8 * k), (2.2 * k, 0.7 * k, 9 * k), "oilskin",
              rotation=(0, 0, -16 * s))
    g.box("hat_brim_back", (x, y - 2.2 * k, z + 5.8 * k), (10.6 * k, 0.7 * k, 5.2 * k), "oilskin_dark",
          rotation=(34, 0, 0))


def harpoon(g, hand, d, back=13, ahead=29):
    """His harpoon: the vanilla trident's shape at boss size, its line tied to the butt."""
    hand, d = np.array(hand, float), _n(d)
    butt, tip = hand - d * back, hand + d * ahead
    beam(g, "harpoon_shaft", butt, tip, 1.6, "wood_dark")
    side = _n(np.cross(d, (0, 1, 0)) if abs(d[1]) < 0.9 else np.cross(d, (1, 0, 0)))
    beam(g, "harpoon_bar", tip - side * 3.4, tip + side * 3.4, 1.4, "iron")
    beam(g, "harpoon_prong", tip, tip + d * 7, 1.4, "iron")
    for s in (-1, 1):
        beam(g, f"harpoon_prong_{s}", tip + side * s * 3.0, tip + side * s * 3.0 + d * 4.6, 1.3, "iron")
    return butt


def rider(g, hip, pose, seated=True, k=K):
    """The drowned whaler. pose: 'idle' (harpoon upright, the other hand on the line to the bow) or 'ram' (leaning
    in, the harpoon couched and lowered like a lance). Seated he straddles the crest; standing he braces in the bow."""
    lean = {"idle": -6, "ram": -24}[pose]
    hx, hy, hz = hip
    r = g.group("rider", tuple(hip), (lean, 0, 0))
    # legs (in the mount's space, not leaning)
    if seated:
        for s in (-1, 1):
            knee = (s * (W / 2 + 2.2), hy - 3.5, hz - 5.5)
            foot = (s * (W / 2 + 2.8), hy - 14, hz - 3)
            beam(g, f"thigh_{s}", (s * 2.2 * k, hy, hz), knee, 4 * k, "oilskin_dark")
            beam(g, f"shin_{s}", knee, foot, 3.8 * k, "oilskin_dark")
            g.box(f"boot_{s}", (s * (W / 2 + 2.9), hy - 15, hz - 4.2), (4.2 * k, 3 * k, 5.6 * k), "boot")
    else:
        for s, knee, foot in ((-1, (-2.2 * k, hy - 5.5 * k, hz - 5 * k), (-2.4 * k, hy - 11.5 * k, hz - 4.5 * k)),
                              (1, (2.4 * k, hy - 6 * k, hz + 2.5 * k), (2.6 * k, hy - 11.5 * k, hz + 5.5 * k))):
            beam(g, f"thigh_{s}", (s * 2.2 * k, hy, hz), knee, 4 * k, "oilskin_dark")
            beam(g, f"shin_{s}", knee, foot, 3.8 * k, "oilskin_dark")
            g.box(f"boot_{s}", (foot[0], foot[1] - 0.6, foot[2] - 1.0), (4.2 * k, 2.4 * k, 5.6 * k), "boot")
    # the coat: hips, a skirt over the thighs, the torso
    r.box("coat_hips", (hx, hy + 1.6 * k, hz), (8.6 * k, 3.2 * k, 4.8 * k), "oilskin")
    if seated:
        for s in (-1, 1):
            r.box(f"coat_tail_{s}", (hx + s * 3.6 * k, hy - 1.0 * k, hz + 1.4 * k), (2.4 * k, 6 * k, 4.4 * k),
                  "oilskin", rotation=(18, 0, -14 * s))
    else:
        r.box("coat_skirt", (hx, hy - 2.6 * k, hz + 0.4 * k), (9.4 * k, 6.4 * k, 5.6 * k), "oilskin")
    r.box("torso", (hx, hy + 8 * k, hz), (8.4 * k, 10 * k, 4.6 * k), "oilskin")
    r.box("collar", (hx, hy + 12.6 * k, hz + 0.6 * k), (9 * k, 2 * k, 5.4 * k), "oilskin_dark")
    r.box("hump", (hx - 2.2 * k, hy + 11.4 * k, hz + 2.2 * k), (4.4 * k, 3.4 * k, 2 * k), "barnacle")
    # the head: the drowned's, barnacled, the jaw hanging a little open, the eyes the only light on him
    head = np.array([hx, hy + 17.4 * k, hz - 0.4 * k])
    r.box("head", tuple(head), (8 * k, 7 * k, 8 * k), "skin")
    r.box("jaw", tuple(head + (0, -4.4 * k, -0.6 * k)), (7.2 * k, 2.2 * k, 6.6 * k), "skin_dark", rotation=(8, 0, 0))
    for s in (-1, 1):
        r.box(f"eye_{s}", tuple(head + (s * 1.8 * k, 0.6 * k, -4.05 * k)), (1.6 * k, 1 * k, 0.4), "eye")
    for i, (dx, dy, sz) in enumerate(((2.8, -1.8, 1.8), (3.6, -0.4, 1.2), (-3.2, -2.4, 1.4))):
        r.box(f"barnacle{i}", tuple(head + (dx * k, dy * k, -4.2 * k)), (sz * k, sz * k, 1.2 * k), "barnacle")
    sou_wester(r, tuple(head + (0, 3.5 * k, 0)), k)
    # arms and the harpoon (in the rider's rest space, before his lean)
    sh_r, sh_l = np.array([hx + 5.4 * k, hy + 11.6 * k, hz]), np.array([hx - 5.4 * k, hy + 11.6 * k, hz])
    if pose == "idle":
        el_r, hand_r, d = sh_r + (1.2 * k, -5.5 * k, -1.5 * k), sh_r + (1.2 * k, -8 * k, -6 * k), (0, 1, -0.12)
        el_l, hand_l = sh_l + (-0.8 * k, -5.5 * k, -2 * k), sh_l + (1.6 * k, -7 * k, -7.5 * k)
    else:
        el_r, hand_r, d = sh_r + (0.6 * k, -4.5 * k, 3.0 * k), sh_r + (-0.6 * k, -5.5 * k, -4.5 * k), (-0.1, 0.32, -1)
        el_l, hand_l = sh_l + (1.2 * k, -3.5 * k, -5.0 * k), sh_l + (6.0 * k, -3.6 * k, -10.5 * k)
    for side, sh, el, hd in (("r", sh_r, el_r, hand_r), ("l", sh_l, el_l, hand_l)):
        beam(r, f"arm_{side}", sh, el, 3.8 * k, "oilskin")
        beam(r, f"forearm_{side}", el, hd, 3.5 * k, "oilskin")
        r.box(f"hand_{side}", tuple(hd), (3 * k, 3 * k, 3 * k), "skin")
    butt = harpoon(r, hand_r, d, back=13 if pose == "idle" else 16, ahead=29 if pose == "idle" else 30)
    return r, hand_l, butt


# ---- the takes -----------------------------------------------------------------------------------------------------

def mount(m, pose):
    root = m.group("root", (0, 0, 0))
    pitch = -9 if pose == "ram" else 0                        # the ram: the bow dips
    return root.group("mount", (0, CY, CZ), (pitch, 0, 0))


def crest_rider(g, pose):
    seat_y = CY + R + 1.6
    g.box("saddle", (0, seat_y, CZ - 1), (11, 2.6, 10), "wood_dark")
    g.box("saddle_back", (0, seat_y + 2.6, CZ + 4), (10, 3.4, 2), "wood_dark", rotation=(12, 0, 0))
    for i, z in enumerate((CZ - 4, CZ + 2)):
        lashing(g, f"girth{i}", z, out=1.2)
    _, hand_l, butt = rider(g, (0, seat_y + 1.6, CZ - 1), pose)
    return np.array([0, seat_y, CZ + 4])


def take_a(m, pose):
    g = mount(m, pose)
    shell(g)
    body(g, 1.0 if pose == "idle" else 0.35)
    top, gun = bow(g)
    lashing(g, "lash_bow", CZ - 7.5, out=2.6)
    beam(g, "bowsprit", top + (0, 2, 2), top + (0, 16, -26), 3.6, "wood_dark")
    beam(g, "bowsprit_stay", top + (0, 15, -24), top + (0, -8, -3), 0.9, "rope")
    lantern(g, "lantern", top + (0, 15.4, -24.5))
    maiden(g, top + (0, -6, -1.5))
    seat = crest_rider(g, pose)
    net(g)
    stuck_harpoon(g, "old_harpoon_l", (-W / 2 + 1, CY + 9, CZ + 9), (-0.7, 0.45, 0.6), seat + (-4, 0, 0))
    stuck_harpoon(g, "old_harpoon_r", (W / 2 - 1, CY - 6, CZ + 4), (0.8, 0.1, 0.55), seat + (4, 0, 0))


def take_b(m, pose):
    g = mount(m, pose)
    shell(g)
    body(g, 1.0 if pose == "idle" else 0.35)
    top, gun = bow(g, d_top=9, d_bot=3, clinker=True, step=3.6)
    lashing(g, "lash_bow", CZ - 7.5, out=3.4)
    hang = serpent(g, top)
    lantern(g, "lantern", hang + (0, 2.5, 0))
    seat = crest_rider(g, pose)
    net(g, 270, 352)
    stuck_harpoon(g, "old_harpoon_l", (-W / 2 + 1, CY + 2, CZ + 11), (-0.75, 0.3, 0.6), seat + (-4, 0, 0))
    stuck_harpoon(g, "old_harpoon_r", (W / 2 - 1, CY + 10, CZ + 7), (0.75, 0.5, 0.45), seat + (4, 0, 0))


def take_c(m, pose):
    g = mount(m, pose)
    shell(g)
    body(g, 1.0 if pose == "idle" else 0.35)
    top, gun = bow(g, d_top=20, d_bot=5, top=46, step=4.2, flank_back=11, ragged=True, flare=0.22, sheer=4)
    deck_y = CY + 2
    zf = front_z(deck_y, R)
    g.box("deck", (0, deck_y, (top[2] + zf) / 2 + 1), (W - 3, 1.6, zf - top[2] + 2), "wood_dark")
    g.box("thwart", (0, deck_y + 5, top[2] + 9), (W - 2, 1.8, 3), "wood_dark")
    beam(g, "bowsprit_stub", top + (0, 0.5, 1), top + (0, 4.5, -9), 3.4, "wood_dark")
    lantern(g, "lantern", top + (0, 4.2, -8.4))
    eagle(g, CY + 2, front_z(CY + 2, R + 0.5) - (5 + (20 - 5) * ((CY + 2) - (CY + R * math.cos(math.radians(138))))
                                                 / (R * math.cos(math.radians(46)) - R * math.cos(math.radians(138)))),
          front_z(CY + 2, R), W / 2 + 1.5)
    lashing(g, "lash_bow", CZ - 2, out=1.4)
    lashing(g, "lash_bow2", CZ + 5, out=1.4)
    rider(g, (0, deck_y + 1 + 11.6 * K, (top[2] + zf) / 2 + 3), pose, seated=False)
    net(g, 262, 352)
    seat = np.array([0, deck_y + 4, zf + 2])
    stuck_harpoon(g, "old_harpoon_l", (-W / 2 + 1, CY + 8, CZ + 10), (-0.7, 0.5, 0.5), seat + (-6, 0, 0))
    for i in range(3):                                        # spare harpoons racked inside the bow
        beam(g, f"rack{i}", (W / 2 - 1, deck_y + 2 + i * 1.6, top[2] + 6), (W / 2 + 0.5, deck_y + 7 + i * 1.6,
                                                                              zf + 4), 1.3, "iron")


TAKES = {"A": ("The Maiden's Prow", take_a), "B": ("The Serpent Stem", take_b), "C": ("The Harpooner's Bow", take_c)}
VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 38, "height": 3.4, "dist": 10.5, "target_z": 2.4},
    {"name": "flat_side", "mode": "flat", "camera": "persp", "yaw": 90, "height": 2.6, "dist": 10.5, "target_z": 2.4,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -28, "height": 1.62, "dist": 10, "target_z": 2.8,
     "player": False},
]
LABELS = {"flat_34": "three-quarter", "flat_side": "side", "sil_side": "side, silhouette", "clay_eye": "a player's eye"}


def main(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    quick = "quick" in (only or [])
    keys = [k for k in (only or TAKES) if k in TAKES] or list(TAKES)
    for key in keys:
        title, fn = TAKES[key]
        for old in (OUT / key).rglob("*") if (OUT / key).exists() else ():
            if old.is_file():
                old.unlink()
        for pose in ("idle", "ram"):
            m = Model(f"tidebreaker_{key}_{pose}")
            fn(m, pose)
            views = VIEWS[:1] if quick else VIEWS
            v2.run_blender(m.render_json(v2.PALETTE), OUT / key / pose, views)
            if pose == "idle":
                lo, hi = m.bounds()
                print(key, title, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
        if quick:
            continue
        tw, th, pad, top = 400, 320, 12, 60
        img = Image.new("RGB", (pad + 4 * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Tidebreaker {key}: {title}", font=sheet._font(26), fill=sheet.INK)
        for r, pose in enumerate(("idle", "ram")):
            for col, v in enumerate(VIEWS):
                x, y = pad + col * (tw + pad), top + r * (th + 34 + pad)
                img.paste(sheet._tile(OUT / key / pose / f"{v['name']}.png", tw, th), (x, y))
                label = "idle" if pose == "idle" else "the ram"
                dr.text((x, y + th + 6), f"{label}: {LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / f"{key}_{title.lower().replace(' ', '_').replace(chr(39), '')}.png")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
