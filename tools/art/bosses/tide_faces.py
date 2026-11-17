"""The Tidebreaker redesign, session 1 step 2: close-up studies of the two faces the boss is read by.

Take 2 (the Viking Longship) was approved on 2026-11-08. Each face comes in three versions, as real cuboids at the
size they have on the model:
  the Viking (a drowned at 1.45 times), his bust under the horned helmet:
    V1  the Spectacle Helm  an iron guard round both eyes, the glow deep in its sockets, a heavy beard
    V2  the Open Jaw        a nasal only: sunken eyes, the jaw hanging, broken teeth, two ringed braids, wide ox horns
    V3  the Crusted One     barnacles swallowing half his face and one eye, one horn snapped off
  the carved serpent on the stem, with the lantern:
    S1  the Longship Head   long and narrow, jaws open, a carved curl behind the skull, the lantern hanging
    S2  the Dragon          a heavy brow, two swept horns, cheek fins, two great fangs, the lantern hanging
    S3  the Sea Eel         a round gaping head with rows of teeth, gill fins, the lantern lit inside its throat

Colours are blockout zones; eye veins, carving lines and wear are texture later. Model units: 16 = one block, y up,
the faces towards -z.

Run from the repository root: python tools/art/bosses/tide_faces.py [V1 V2 V3 S1 S2 S3]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import archevoker_silhouettes as arch, monarch_s1 as ms, tide_silhouettes as t1, tide_take2 as t2, volley_crone_s2 as v2  # noqa: E402
from bosses.tide_silhouettes import beam, plank  # noqa: E402

OUT = ROOT / "docs/art/bosses/tidebreaker/overhaul/s1_faces"
PALETTE = dict(t2.PALETTE, dark=(14, 16, 18), tooth=(214, 206, 180), gum=(96, 44, 46), iron_light=(122, 124, 130))
K = t2.K
H = np.array([0.0, 64.0, 0.0])                # the head's centre
TOP = H + (0, 3.5 * K, 0)                     # the top of the skull: the helmet's seat


def at(*offset):
    """A point relative to the head, in the Viking's head units."""
    return tuple(H + np.array(offset) * K)


def barnacle(g, name, c, s):
    """One barnacle on a face looking forward: two plates turned 45 degrees and a smaller cap. Its opening is texture
    (a modelled square hole read as one more eye)."""
    x, y, z = c
    g.box(name, (x, y, z), (s, s, 1.2), "barnacle")
    g.box(name + "_b", (x, y, z - 0.1), (s * 0.82, s * 0.82, 1.3), "barnacle", rotation=(0, 0, 45))
    g.box(name + "_top", (x, y, z - 0.75), (s * 0.5, s * 0.5, 0.7), "shell_in", rotation=(0, 0, 22))


def bust(g):
    """What is under every head: shoulders in torn leather and the fur collar."""
    g.box("torso", at(0, -9.5, 0.2), (8.4 * K, 6 * K, 4.6 * K), "leather")
    g.box("fur_collar", at(0, -6.6, 0.4), (10.6 * K, 2.6 * K, 6.2 * K), "fur")
    g.box("neck", at(0, -5, 0), (5 * K, 3 * K, 5 * K), "skin_dark")


def dome(g, tilt=0.0):
    """A spangenhelm: four plates rising to a point over the brow band, an iron rib up each joint and a knob on top."""
    h = g.group("helm_g", tuple(TOP), (0, 0, tilt))
    x, y, z = TOP
    arch.ring_panels(h, "helm_plate", y + 3.9 * K, y - 0.9 * K, 1.5 * K, 4.3 * K, "iron", n=4, t=1.4, fill=1.12, start=0, cx=x, cz=z)
    h.box("helm_cap", (x, y + 4.0 * K, z), (3.0 * K, 0.8 * K, 3.0 * K), "iron")
    h.box("helm_knob", (x, y + 4.9 * K, z), (1.2 * K, 1.2 * K, 1.2 * K), "iron", rotation=(0, 45, 0))
    h.box("helm_band", (x, y - 1.2 * K, z), (9.3 * K, 1.4 * K, 9.3 * K), "iron")
    for sx in (-1, 1):
        for sz in (-1, 1):
            beam(h, f"helm_rib_{sx}_{sz}", (x + sx * 4.3 * K, y - 0.6 * K, z + sz * 4.3 * K),
                 (x + sx * 1.35 * K, y + 3.9 * K, z + sz * 1.35 * K), 1.0 * K, "iron_light")


def spline(pts, each=3):
    """Catmull-Rom through pts: a smooth curve instead of a few long bent segments."""
    pts = [np.array(q, float) for q in pts]
    q = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(q) - 2):
        a, b, c, d = q[i - 1], q[i], q[i + 1], q[i + 2]
        for j in range(each):
            t = j / each
            out.append(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (3 * b - a - 3 * c + d) * t ** 3))
    out.append(pts[-1])
    return out


def horn(g, name, pts, w0, tip=0.55):
    """A horn tapering smoothly to a point; each short piece runs into the next, so no gaps open at the bends."""
    c = spline([TOP + np.array(q) * K for q in pts])
    for i, (a, b) in enumerate(zip(c, c[1:])):
        d = (b - a) / np.linalg.norm(b - a)
        f = i / max(1, len(c) - 2)
        beam(g, f"{name}_{i}", a - d * 0.5, b + d * 0.5, (w0 + (tip - w0) * f) * K, "horn")


def hair(g):
    """Matted hair out from under the helmet at the back and sides, in uneven locks."""
    g.box("hair_back", at(0, -1.0, 4.3), (8.8 * K, 6.0 * K, 1.0 * K), "hair")
    for i, (x, ln) in enumerate(((-3.3, 3.4), (-1.0, 5.0), (1.3, 3.0), (3.3, 4.4))):
        g.box(f"hair_lock{i}", at(x, -4.0 - ln / 2, 4.5), (2.0 * K, ln * K, 0.9 * K), "hair", rotation=(8, 0, x))
    for s in (-1, 1):
        g.box(f"hair_side_{s}", at(s * 4.3, -0.8, 1.9), (1.0 * K, 5.6 * K, 4.4 * K), "hair")
        g.box(f"hair_side_lock_{s}", at(s * 4.4, -4.6, 2.4), (0.9 * K, 3.4 * K, 2.2 * K), "hair", rotation=(0, 0, 6 * s))


def beard(g, cx=0.0, w=7.2):
    """A heavy beard: a full mass, then uneven hanks tapering down; thin ends carry the shape, not a flat slab."""
    g.box("beard", at(cx, -5.4, -3.6), (w * K, 4.4 * K, 2.6 * K), "hair", rotation=(-8, 0, 0))
    for i, (x, ln, wd) in enumerate(((-0.34, 4.4, 2.0), (-0.06, 6.6, 2.4), (0.24, 5.2, 2.2), (0.42, 3.0, 1.5))):
        g.box(f"beard_hank{i}", at(cx + x * w, -7.4 - ln / 2, -4.2 - (i % 2) * 0.25), (wd * K, ln * K, 1.5 * K), "hair",
              rotation=(-11, 0, x * 16))


CRESCENT = [(4.0, 0.4, 0.4), (7.0, 1.6, 0), (8.8, 4.2, -1.2), (8.4, 6.8, -3.0), (6.8, 8.2, -4.8)]
OX = [(4.0, 0.2, 0.2), (8.4, 0.8, -0.2), (11.8, 2.6, -0.8), (13.2, 5.8, -1.6), (13.0, 8.8, -2.6)]


def spectacle(g):
    g.box("head", at(0, 0, 0), (8 * K, 7 * K, 8 * K), "skin")
    bust(g)
    dome(g)
    for s in (-1, 1):
        horn(g, f"horn_{s}", [(s * x, y, z) for x, y, z in CRESCENT], 2.9)
        g_x = s * 2.2
        g.box(f"socket_{s}", at(g_x, 0.2, -3.95), (3.2 * K, 2.1 * K, 0.5), "dark", rotation=(0, 0, s * 15))
        g.box(f"eye_{s}", at(g_x, 0.15, -4.2), (1.9 * K, 0.55 * K, 0.4), "eye", rotation=(0, 0, s * 15))
        g.box(f"guard_outer_{s}", at(s * 4.1, 0.1, -4.2), (0.9 * K, 3.4 * K, 1.0 * K), "iron")
        g.box(f"guard_low_{s}", at(g_x, -1.5, -4.3), (3.8 * K, 0.9 * K, 1.0 * K), "iron", rotation=(0, 0, s * 6))
        g.box(f"guard_brow_{s}", at(s * 2.3, 1.6, -4.35), (4.8 * K, 1.2 * K, 1.1 * K), "iron", rotation=(0, 0, s * 15))
    g.box("guard_nasal", at(0, -0.2, -4.45), (1.2 * K, 4.4 * K, 1.0 * K), "iron")
    g.box("jaw", at(0, -3.9, -0.4), (7.2 * K, 2.0 * K, 6.8 * K), "skin_dark", rotation=(6, 0, 0))
    g.box("moustache", at(0, -2.8, -4.3), (6.0 * K, 1.2 * K, 1.0 * K), "hair")
    beard(g)
    hair(g)
    barnacle(g, "barnacle0", at(3.2, -2.6, -4.2), 2.8)
    barnacle(g, "barnacle1", at(4.2, 4.0, -4.5), 2.4)


def open_jaw(g):
    g.box("head", at(0, 0.8, 0), (8 * K, 5.4 * K, 8 * K), "skin")
    bust(g)
    dome(g)
    g.box("helm_nasal", at(0, 0.4, -4.45), (1.3 * K, 4.4 * K, 0.9 * K), "iron")
    for s in (-1, 1):
        horn(g, f"horn_{s}", [(s * x, y, z) for x, y, z in OX], 2.9)
        g.box(f"socket_{s}", at(s * 2.4, 0.9, -3.97), (3.0 * K, 2.0 * K, 0.5), "dark", rotation=(0, 0, s * 16))
        g.box(f"eye_{s}", at(s * 2.5, 0.8, -4.2), (1.5 * K, 0.6 * K, 0.4), "eye", rotation=(0, 0, s * 16))
    g.box("mouth", at(0, -2.4, -0.1), (6.2 * K, 2.4 * K, 7.2 * K), "dark")
    g.box("upper_gum", at(0, -1.6, -3.65), (6.0 * K, 0.5 * K, 0.8 * K), "gum")
    hair(g)
    for i, (x, h, tilt) in enumerate(((-2.5, 1.5, 8), (-0.7, 0.8, -6), (1.9, 1.9, -10))):     # broken, gaps between
        g.box(f"tooth{i}", at(x, -1.9 - h / 2, -3.75), (0.8 * K, h * K, 0.6 * K), "tooth", rotation=(0, 0, tilt))
    jaw = g.group("jaw_g", at(0, -2.8, 3.2), (-20, 0, 0))
    jaw.box("jaw", at(0, -4.3, -0.5), (7.2 * K, 1.8 * K, 7 * K), "skin_dark")
    jaw.box("jaw_gum", at(0, -3.3, -3.4), (5.8 * K, 0.5 * K, 0.9 * K), "gum")
    for i, (x, h) in enumerate(((-1.6, 1.3), (1.5, 0.9))):
        jaw.box(f"tooth_low{i}", at(x, -3.1 + h / 2, -3.5), (0.8 * K, h * K, 0.6 * K), "tooth")
    for s in (-1, 1):
        a = np.array(at(s * 2.7, -6.2, -3.4))
        b, c = a + (s * -0.8, -5, -1.2), a + (s * -1.6, -9.5, -1.6)
        jaw.box(f"beard_root_{s}", tuple(a), (3.2 * K, 2.8 * K, 2 * K), "hair")
        beam(jaw, f"braid_{s}_a", a, b, 2.1 * K, "hair")
        jaw.box(f"braid_ring_{s}", tuple(b), (2.5 * K, 1.1 * K, 2.5 * K), "iron")
        beam(jaw, f"braid_{s}_b", b, c, 1.7 * K, "hair")
    barnacle(g, "barnacle0", at(3.5, -0.8, -4.2), 2.4)


def crusted(g):
    g.box("head", at(0, 0, 0), (8 * K, 7 * K, 8 * K), "skin")
    bust(g)
    dome(g, tilt=-5)
    g.box("helm_nasal", at(0.1, 0.1, -4.45), (1.3 * K, 4.2 * K, 0.9 * K), "iron", rotation=(0, 0, -5))
    horn(g, "horn_r", [(-x, y, z) for x, y, z in CRESCENT], 3.0)
    horn(g, "horn_stump", [(4.0, 0.4, 0.4), (5.6, 0.9, 0.2), (7.2, 1.7, 0)], 3.0, tip=2.4)
    g.box("horn_break", tuple(TOP + np.array((7.5, 2.0, -0.2)) * K), (1.2 * K, 1.8 * K, 1.5 * K), "horn",
          rotation=(0, 0, -36))
    # his right half (model +x) is under the crust: seen from the front, on the viewer's left
    ms.ball(g, "crust", at(2.6, -0.8, -3.8), (5.0 * K, 7.4 * K, 3.0 * K), "barnacle", cham=0.32)
    for i, (x, y, sz) in enumerate(((1.4, 1.8, 3.8), (3.8, 1.2, 4.4), (1.8, -1.2, 3.4), (4.1, -2.2, 3.8), (2.1, -3.8, 3.2),
                                    (4.9, 3.2, 2.8))):
        barnacle(g, f"crust_b{i}", at(x, y, -5.45 - (i % 2) * 0.25), sz)
    g.box("socket", at(-2.2, 0.4, -3.97), (3.0 * K, 2.0 * K, 0.5), "dark", rotation=(0, 0, -16))
    g.box("eye", at(-2.2, 0.3, -4.2), (1.8 * K, 0.7 * K, 0.4), "eye", rotation=(0, 0, -16))
    g.box("mouth", at(-1.6, -2.7, -3.97), (3.8 * K, 0.8 * K, 0.5), "dark")
    g.box("jaw", at(0, -3.9, -0.4), (7.2 * K, 2 * K, 6.8 * K), "skin_dark", rotation=(6, 0, 0))
    beard(g, -1.6, 4.6)
    hair(g)


# ---- the serpent --------------------------------------------------------------------------------------------------

S = np.array([0.0, 64.0, 0.0])                # the jaw hinge


def p(*offset):
    return tuple(S + np.array(offset, float))


def teeth(g, name, y, z_from, n, dz, h, down, half):
    d = -1 if down else 1
    for s in (-1, 1):
        for i in range(n):
            g.box(f"{name}_{s}_{i}", p(s * half, y + d * h / 2, z_from - i * dz), (1.2, h, 1.2), "tooth")


def neck(g, pts, w0, mat="wood"):
    pts = [S + np.array(q, float) for q in pts]
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        beam(g, f"neck{i}", a, b, w0 - i * 0.5, mat)
    return pts


def lamp(g, offset):
    t1.lantern(g, "lantern", tuple(S + np.array(offset, float)))


def longship_head(g):
    neck(g, [(0, -22, 13), (0, -12, 10), (0, -4, 8), (0, 1, 6)], 7.0)
    g.box("hinge", p(0, 1, 5), (7, 8, 9), "wood")
    up = g.group("upper", p(0, 0, 3), (12, 0, 0))
    up.box("skull", p(0, 3.2, -2), (7.4, 6.4, 11), "wood")
    up.box("snout", p(0, 2.2, -13), (5, 4.4, 12), "wood")
    up.box("snout_end", p(0, 2.4, -20), (3.8, 3.4, 2.6), "wood")
    up.box("nose_band", p(0, 2.3, -15.5), (5.6, 5.0, 1.2), "paint_red")
    up.box("skull_band", p(0, 3.4, -7), (7.9, 6.9, 1.2), "paint_red")
    teeth(up, "t_up", 0.2, -8, 4, 3.4, 2.2, True, 1.9)
    for s in (-1, 1):
        up.box(f"eye_{s}", p(s * 3.75, 4.2, -4), (0.5, 2.6, 3.4), "paint_white")
        up.box(f"pupil_{s}", p(s * 4.05, 4.2, -4), (0.3, 1.2, 1.2), "dark")
        up.box(f"brow_{s}", p(s * 3.1, 7, -4), (1.8, 1.4, 6), "wood_dark", rotation=(-10, 0, 0))
    curl = [(0, 6.4, 2), (0, 11, 5), (0, 15, 9.5), (0, 15.6, 14), (0, 12.5, 16.5), (0, 9.2, 15), (0, 8.6, 11.6), (0, 11, 10)]
    for i, (a, b) in enumerate(zip(curl, curl[1:])):
        beam(up, f"curl{i}", p(*a), p(*b), 3.8 - i * 0.3, "paint_red" if i % 2 else "wood")
    jaw = g.group("jaw", p(0, 0, 3), (-20, 0, 0))
    jaw.box("jaw_back", p(0, -1.2, -3), (6.6, 2.4, 10), "wood")
    jaw.box("jaw_front", p(0, -1.2, -13), (4.4, 2.2, 11), "wood")
    jaw.box("tongue", p(0, 0.2, -11), (1.8, 0.6, 11), "paint_red")
    teeth(jaw, "t_low", 0, -10, 3, 3.6, 2, False, 1.6)
    lamp(g, (0, -2, -18))


def dragon_head(g, neck_pts=((0, -22, 12), (0, -12, 9), (0, -4, 7), (0, 2, 4)), neck_w=8.0):
    neck(g, list(neck_pts), neck_w)
    up = g.group("upper", p(0, 0, 4), (10, 0, 0))
    up.box("skull", p(0, 3.8, -2), (10, 7.6, 11), "wood")
    up.box("snout", p(0, 2.8, -11), (7.4, 5.6, 9), "wood")
    up.box("nose", p(0, 5.2, -15), (4.4, 2.2, 2.4), "paint_red")
    teeth(up, "fang", 0, -13.4, 1, 3, 5.4, True, 2.8)
    teeth(up, "t_up", 0, -8.4, 2, 3, 2, True, 3.0)
    for s in (-1, 1):
        up.box(f"socket_{s}", p(s * 4.9, 4.2, -4.4), (0.5, 2.2, 3.6), "dark")
        up.box(f"eye_{s}", p(s * 5.2, 4.2, -4.8), (0.3, 1.1, 1.8), "paint_white")
        plank(up, f"brow_{s}", p(s * 3.0, 7.4, -10.0), p(s * 5.3, 10.0, 0.5), 2.4, 2.4, "wood_dark", up=(0, 1, 0))
        pts = [(s * 3.6, 7.5, 1.8), (s * 5.0, 10.5, 8), (s * 5.2, 12.4, 14), (s * 4.2, 15.6, 19)]
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            beam(up, f"horn_{s}_{i}", p(*a), p(*b), 3 - i * 0.7, "paint_red" if i == 2 else "wood_dark")
        for i in range(3):
            plank(up, f"frill_{s}_{i}", p(s * 4.8, 0.6 + i * 2.8, 2), p(s * 9.4, -3 + i * 5.4, 8.5 - abs(i - 1) * 2), 5.0, 0.9, "paint_red", up=(0, 1, 0))
    jaw = g.group("jaw", p(0, 0, 4), (-24, 0, 0))
    jaw.box("jaw_back", p(0, -1.6, -3), (9, 3.2, 11), "wood")
    jaw.box("jaw_front", p(0, -1.5, -12), (6.8, 3, 8), "wood")
    jaw.box("tongue", p(0, 0.4, -9), (2.4, 0.7, 11), "paint_red")
    teeth(jaw, "fang_low", 0, -13.2, 1, 3, 3.8, False, 2.4)
    lamp(g, (0, -5, -15))


def eel_head(g):
    neck(g, [(0, -22, 11), (0, -12, 9), (0, -5, 7), (0, 1, 5)], 8.8)
    up = g.group("upper", p(0, 0, 5), (26, 0, 0))
    ms.octo(up, "skull", p(0, 3.4, -6), (11, 7.4, 17), "wood", cham=0.34)
    up.box("palate", p(0, 0, -7.5), (8.4, 0.5, 14), "gum")
    for i, (z, half) in enumerate(((-14.5, 0), (-13, 2.4), (-9.5, 4), (-5, 4.2))):
        for s in ((-1, 1) if half else (1,)):
            up.box(f"t_up{i}_{s}", p(s * half, -1.5, z), (1.3, 3.0, 1.3), "tooth")
    for s in (-1, 1):
        up.box(f"eye_{s}", p(s * 5.6, 4.4, -7.8), (0.5, 2.4, 2.4), "paint_white")
        up.box(f"pupil_{s}", p(s * 5.9, 4.4, -7.8), (0.3, 1.6, 0.8), "dark")
    jaw = g.group("jaw", p(0, 0, 5), (-22, 0, 0))
    ms.octo(jaw, "jaw_mass", p(0, -2.4, -6), (10.4, 4.4, 16.5), "wood", cham=0.34)
    jaw.box("mouth_floor", p(0, -0.05, -7), (8, 0.5, 13), "gum")
    for i, (z, half) in enumerate(((-13.2, 1.6), (-10, 3.6), (-5.8, 4))):
        for s in (-1, 1):
            jaw.box(f"t_low{i}_{s}", p(s * half, 1.0, z), (1.3, 2.4, 1.3), "tooth")
    g.box("throat", p(0, 1.0, 4), (9, 7, 2), "dark")
    g.box("lantern", p(0, 1.0, 0.6), (4.4, 5.0, 4.4), "glow")
    g.box("lantern_cap", p(0, 4.0, 0.6), (5.4, 1.2, 5.4), "iron")
    g.box("lantern_base", p(0, -2.0, 0.6), (5.4, 1.2, 5.4), "iron")
    for sx in (-1, 1):
        for sz in (-1, 1):
            g.box(f"lantern_bar_{sx}_{sz}", p(sx * 2.3, 1.0, 0.6 + sz * 2.3), (0.7, 5.2, 0.7), "iron")
    for s in (-1, 1):
        for i in range(3):
            plank(g, f"gill_{s}_{i}", p(s * 4.8, -2.4 + i * 3.2, 6.5), p(s * 9.6, -6.0 + i * 5.2, 12 - abs(i - 1) * 2), 5.2, 0.9, "paint_red", up=(0, 1, 0))
    for i, (y, z, h) in enumerate(((10, 3, 4.2), (8.5, 8, 5.0), (3, 11.5, 5.2), (-5, 13, 4.6))):
        g.box(f"fin{i}", p(0, y, z), (0.9, h, 4.4), "paint_red", rotation=(-40 + i * 16, 0, 0))


V = {"V1": ("The Spectacle Helm", spectacle), "V2": ("The Open Jaw", open_jaw), "V3": ("The Crusted One", crusted)}
SER = {"S1": ("The Longship Head", longship_head), "S2": ("The Dragon", dragon_head), "S3": ("The Sea Eel", eel_head)}
Z = 4.05


def views(dist):
    return [{"name": "front", "mode": "flat", "camera": "persp", "yaw": 0, "height": Z + 0.1, "dist": dist, "target_z": Z,
             "lens": 50, "player": False},
            {"name": "q", "mode": "flat", "camera": "persp", "yaw": -38, "height": Z + 0.5, "dist": dist, "target_z": Z,
             "lens": 50, "player": False},
            {"name": "side", "mode": "flat", "camera": "persp", "yaw": 90, "height": Z + 0.1, "dist": dist, "target_z": Z,
             "lens": 50, "player": False},
            {"name": "under", "mode": "flat", "camera": "persp", "yaw": -24, "height": 1.62, "dist": dist + 1.5, "target_z": Z,
             "lens": 50, "player": False}]


LAB = {"front": "front", "q": "three-quarter", "side": "side", "under": "from a player's eye, below"}


def sheet_of(group, keys, title, name):
    tw, th, pad, top = 400, 320, 12, 60
    vs = views(1)
    img = Image.new("RGB", (pad + len(vs) * (tw + pad), top + len(keys) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), title, font=sheet._font(26), fill=sheet.INK)
    for r, k in enumerate(keys):
        for c, v in enumerate(vs):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / k / f"{v['name']}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{k} {group[k][0]}: {LAB[v['name']]}", font=sheet._font(16), fill=sheet.DIM)
    img.save(OUT / name)


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    every = {**V, **SER}
    for key in [a for a in argv if a in every] or list(every):
        m = Model("tide_" + key)
        every[key][1](m.group("root", (0, 0, 0)))
        v2.run_blender(m.render_json(v2.PALETTE), OUT / key, views(3.6 if key in V else 4.4))
        print(key, every[key][0], "cubes", len(m.cubes))
    sheet_of(V, list(V), "Tidebreaker: the Viking's face", "viking_faces.png")
    sheet_of(SER, list(SER), "Tidebreaker: the carved serpent", "serpent_heads.png")


if __name__ == "__main__":
    main(sys.argv[1:])
