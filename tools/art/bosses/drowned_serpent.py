"""The Drowned Elder redesign, session 1 step 1: three body plans for the Abyssal Serpent, as cuboid blockouts.

The brief (docs/art/bosses/drowned_elder/overhaul/plan.md, 2026-11-17): the Elder Guardian grown into a sea serpent. Its
head is vanilla's elder (GuardianModel, 26.2 client: the 12x12x16 body, 2-texel plates on four sides, twelve 2x9x2
spikes on the edges, the 2x2 eye) at 3x; about ten armoured segments trail behind it, ending in the guardian's fin.

The takes differ in how the body is built and how it holds itself:
  A  the Chain     a string of guardian barrels, each with its plates and four diagonal spikes, a gap between them;
                   it swims flat, in a sideways S, close to the arena floor
  B  the Wyrm      overlapping armoured segments with one tall spike per segment along the back, pectoral fins behind
                   the head; it swims in humps that rise and dip, the classic sea serpent
  C  the Oarfish   a tall, narrow ribbon body without spikes, a continuous crest along the back and long crest rays
                   sweeping from the head (the real oarfish, an omen of disaster); it rears upright, head high over you

Each is shown idle, aiming (three segments open their eyes on the players) and in the surge dive (head into the floor).
Model units: 16 = one block, y up, the face towards -z. The blue figure is a player (1.8 blocks).

Run from the repository root: python tools/art/bosses/drowned_serpent.py [A B C]
"""
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
from bosses.tide_silhouettes import euler  # noqa: E402

OUT = ROOT / "docs/art/bosses/drowned_elder/overhaul/s1_serpent"
PALETTE = {
    "hide": (184, 178, 160), "plate": (146, 140, 120), "spike": (122, 108, 150), "eye": (222, 228, 214),
    "lid": (96, 90, 82), "glow": (110, 232, 206), "fin": (150, 136, 156), "crest": (170, 120, 132),
}
K = 3.0                                  # the head: vanilla elder texels -> model units
IDLE, AIM, SURGE = "idle", "aim", "surge"
POSES = (IDLE, AIM, SURGE)
UP = np.array([0.0, 1.0, 0.0])


def n(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


# ---- the spine ----------------------------------------------------------------------------------------------------------

class Spine:
    """A smooth curve through control points (head first), sampled densely, with frames carried along it."""

    def __init__(self, pts, samples=1200, up0=None):
        p = [np.array(q, float) for q in pts]
        p = [2 * p[0] - p[1]] + p + [2 * p[-1] - p[-2]]
        dense = []
        for i in range(1, len(p) - 2):
            p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
            for t in np.linspace(0, 1, samples // (len(p) - 3), endpoint=False):
                dense.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                    + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        dense.append(p[-2])
        self.p = np.array(dense)
        seg = np.linalg.norm(np.diff(self.p, axis=0), axis=1)
        self.s = np.concatenate([[0], np.cumsum(seg)])
        # forward = towards the head; up carried along by parallel transport (no flips where it turns vertical)
        fwd = [n(self.p[0] - self.p[1])]
        for i in range(1, len(self.p)):
            fwd.append(n(self.p[i - 1] - self.p[i]))
        up = []
        # up0: the head's up from the frame before (an animation), so a head pointing straight up or down keeps its roll
        ref = UP if up0 is None else np.asarray(up0, float)
        u = ref - fwd[0] * np.dot(ref, fwd[0])
        if np.linalg.norm(u) < 0.2 and up0 is None:
            u = np.array([0.0, 0, 1]) - fwd[0] * fwd[0][2]
        u = n(u) if np.linalg.norm(u) > 1e-3 else np.array([0.0, 0, 1])
        for f in fwd:
            u = n(u - f * np.dot(u, f))
            up.append(u)
        self.fwd, self.up = np.array(fwd), np.array(up)

    def at(self, s):
        """(point, frame) at arc length s from the head; frame columns: right, up, forward."""
        i = int(np.clip(np.searchsorted(self.s, s), 1, len(self.s) - 1))
        t = (s - self.s[i - 1]) / max(1e-9, self.s[i] - self.s[i - 1])
        p = self.p[i - 1] + (self.p[i] - self.p[i - 1]) * t
        f, u = self.fwd[i], self.up[i]
        return p, np.column_stack([np.cross(u, f), u, f])


def obox(g, name, centre, size, F, mat):
    g.box(name, tuple(np.array(centre, float)), tuple(size), mat, rotation=euler(F))


def along(g, name, centre, d, size, mat, thin=None):
    """A box whose local y runs along d; its local x (thin axis) as close to `thin` as it can be."""
    y = n(d)
    r = np.array(thin if thin is not None else (1, 0, 0), float)
    if abs(np.dot(n(r), y)) > 0.95:
        r = np.array([0.0, 0, 1])
    x = n(r - y * np.dot(r, y))
    obox(g, name, centre, size, np.column_stack([x, y, np.cross(x, y)]), mat)


def spike(g, name, base, d, length, width):
    """Vanilla's guardian spike: a square rod, half sunk, a thinner tip."""
    d = n(d)
    along(g, name + "_a", base + d * length * 0.2, d, (width, length * 0.6, width), "spike")
    along(g, name + "_b", base + d * length * 0.65, d, (width * 0.55, length * 0.5, width * 0.55), "spike")


# ---- the head: vanilla's elder at 3x -------------------------------------------------------------------------------------

def head(g, sp, frill=False):
    """The head is the elder's whole body: its face (with the eye) at arc length 0."""
    c, F = sp.at(8 * K)
    r, u, f = F.T
    obox(g, "head", c, np.array([12, 12, 16]) * K, F, "hide")
    pl = 2 * K
    for sx in (-1, 1):                                    # vanilla's plates: on the sides, top and bottom, 12 deep
        obox(g, f"plate_x{sx}", c + r * sx * (6 * K + pl / 2), (pl, 12 * K, 12 * K), F, "plate")
        obox(g, f"plate_y{sx}", c + u * sx * (6 * K + pl / 2), (12 * K, pl, 12 * K), F, "plate")
    obox(g, "eye", c + f * (8 * K + 0.6), (2 * K, 2 * K, 1.2), F, "eye")
    # twelve spikes, one from the middle of each edge, pointing out along the edge's diagonal
    edges = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            edges.append((r * sx * 6 * K + u * sy * 6 * K, r * sx + u * sy))          # 4 along the body
            edges.append((u * sy * 6 * K + f * sx * 8 * K, u * sy + f * sx * 0.6))   # 4 across, top and bottom
            edges.append((r * sy * 6 * K + f * sx * 8 * K, r * sy + f * sx * 0.6))   # 4 upright, front and back
    for i, (off, d) in enumerate(edges):
        d = n(d)
        if frill and np.dot(d, u) > 0.3:
            continue                                       # the oarfish's top spikes became its crest rays
        under = np.dot(d, u) < -0.3
        spike(g, f"hspike{i}", c + off, d - f * 0.35, (5 if under else 9) * K, 2 * K)
    return c, F


# ---- the body ------------------------------------------------------------------------------------------------------------

def segments(g, sp, count, w0, w1, l0, l1, gap, start, shape=(1.0, 1.0), plates=True, eyes=None, spikes="diag",
             dorsal=0.0, crest=0.0):
    """count armoured segments behind the head. Sizes run from (w0, l0) to (w1, l1) model units; gap < 0 overlaps.
    eyes: {index: open} - an eye on both sides, glowing when open, a closed slit when not. Returns the arc length after
    the last segment."""
    s = start
    for i in range(count):
        t = i / max(1, count - 1)
        w, ln = w0 + (w1 - w0) * t, l0 + (l1 - l0) * t
        c, F = sp.at(s + ln / 2)
        r, u, f = F.T
        wx, wy = w * shape[0], w * shape[1]
        obox(g, f"seg{i}", c, (wx, wy, ln), F, "hide")
        if plates:
            pl = w / 6
            for sx in (-1, 1):
                obox(g, f"seg{i}_px{sx}", c + r * sx * (wx / 2 + pl / 2), (pl, wy * 0.84, ln * 0.72), F, "plate")
                obox(g, f"seg{i}_py{sx}", c + u * sx * (wy / 2 + pl / 2), (wx * 0.84, pl, ln * 0.72), F, "plate")
        if spikes == "diag":
            for sx in (-1, 1):
                for sy in (-1, 1):
                    d = r * sx + u * sy * (1 if sy > 0 else 0.6)
                    spike(g, f"seg{i}_sp{sx}{sy}", c + r * sx * wx / 2 + u * sy * wy / 2, n(d) - f * 0.5,
                          w * (0.85 if sy > 0 else 0.45), max(2.5, w / 6))
        if dorsal:
            spike(g, f"seg{i}_dorsal", c + u * wy / 2, u - f * 0.55, dorsal * (1 - 0.55 * t), max(3, w / 5))
            for sx in (-1, 1):
                spike(g, f"seg{i}_side{sx}", c + r * sx * wx / 2, r * sx - f * 0.6, w * 0.35, max(2, w / 8))
        if crest:
            h = crest * (1 - 0.6 * t)
            obox(g, f"seg{i}_crest", c + u * (wy / 2 + h / 2 - 1), (1.2, h, ln + max(0, gap) + 7), F, "crest")
        if eyes and i in eyes:
            side = wx / 2 + (w / 6 if plates else 0)
            for sx in (-1, 1):
                if eyes[i]:
                    obox(g, f"seg{i}_eye{sx}", c + r * sx * (side + 2.0), (4, w * 0.55, w * 0.55), F, "glow")
                else:
                    obox(g, f"seg{i}_lid{sx}", c + r * sx * (side + 0.6), (1.2, w * 0.3, w * 0.12), F, "lid")
        s += ln + gap
    return s


def tail(g, sp, s, w, fin):
    """Vanilla's tail: two tapering pieces, then a forked fluke: two flat blades in the body's upright plane, swept
    back from the tail's tip (one square fin read as a flyswatter on a stick)."""
    for i, (ww, ln) in enumerate(((w, 2.4 * w), (w * 0.72, 2.2 * w))):
        c, F = sp.at(s + ln / 2 - 1)
        obox(g, f"tail{i}", c, (ww, ww, ln), F, "hide")
        s += ln - 2
    tip, F = sp.at(s)
    r, u, f = F.T
    for sy in (-1, 1):
        d = n(u * sy * 0.75 - f)
        along(g, f"fluke{sy}", tip + d * fin / 2, d, (1.2, fin, fin * 0.34), "fin", thin=r)
        along(g, f"fluke{sy}_root", tip + d * fin * 0.22, d, (1.6, fin * 0.45, fin * 0.5), "fin", thin=r)


# ---- the three takes ----------------------------------------------------------------------------------------------------

SURGE_PTS = [(0, 0, -50), (0, 40, -42), (0, 110, -10), (6, 150, 50), (0, 140, 120), (-8, 100, 180), (0, 70, 240),
             (6, 56, 300), (0, 50, 380), (0, 48, 460)]
EYES = (2, 4, 6)


def eyes(pose):
    return {i: pose == AIM for i in EYES}


def take_a(g, pose):
    pts = {IDLE: [(0, 44, 0), (12, 42, 50), (-26, 40, 120), (22, 38, 190), (-16, 36, 260), (4, 36, 330), (0, 36, 420)],
           AIM: [(0, 58, 0), (6, 48, 46), (-34, 40, 104), (6, 38, 160), (40, 38, 222), (14, 36, 292), (-24, 36, 360),
                 (0, 36, 440)],
           SURGE: SURGE_PTS}[pose]
    sp = Spine(pts)
    head(g, sp)
    s = segments(g, sp, 8, 25, 12, 26, 17, 4, 16 * K + 4, eyes=eyes(pose))
    tail(g, sp, s, 10, 30)


def take_b(g, pose):
    pts = {IDLE: [(0, 60, 0), (0, 52, 40), (4, 88, 96), (0, 40, 156), (-4, 76, 212), (0, 36, 266), (2, 58, 318),
                  (0, 40, 380), (0, 40, 460)],
           AIM: [(0, 70, 0), (-4, 58, 40), (-14, 94, 96), (0, 44, 150), (16, 80, 206), (6, 38, 262), (-6, 58, 316),
                 (0, 40, 380), (0, 40, 460)],
           SURGE: SURGE_PTS}[pose]
    sp = Spine(pts)
    c, F = head(g, sp)
    r, u, f = F.T
    for sx in (-1, 1):                                    # pectoral fins: flat, swept back and down behind the head
        d = n(r * sx * 0.55 - f - u * 0.4)
        along(g, f"pectoral{sx}", c + r * sx * (8 * K + 8) - f * (6 * K) - u * 6 + d * 18, d, (1.2, 40, 26), "fin",
              thin=u)
    s = segments(g, sp, 10, 28, 12, 26, 18, -4, 16 * K - 2, spikes=None, dorsal=40, eyes=eyes(pose))
    tail(g, sp, s, 11, 36)


def take_c(g, pose):
    pts = {IDLE: [(0, 158, -10), (0, 150, 26), (0, 118, 50), (0, 80, 36), (0, 50, 2), (0, 30, 40), (0, 24, 110),
                  (2, 20, 180), (0, 18, 260), (0, 18, 340)],
           AIM: [(0, 150, -26), (0, 156, 12), (-10, 124, 40), (8, 84, 34), (-6, 52, 0), (0, 30, 40), (10, 24, 110),
                 (-6, 20, 180), (0, 18, 260), (0, 18, 340)],
           SURGE: SURGE_PTS}[pose]
    sp = Spine(pts)
    c, F = head(g, sp, frill=True)
    r, u, f = F.T
    # the crest rays: long, thin, sweeping back over the body from the top of the head (the oarfish's plume)
    for i, (sx, lift, length) in enumerate(((0, 1.0, 120), (-1, 0.75, 96), (1, 0.75, 96), (-2, 0.45, 70), (2, 0.45, 70))):
        base = c + u * 6 * K + f * (5 * K) + r * sx * 7
        d = n(u * lift - f * 1.0 + r * sx * 0.12)
        along(g, f"ray{i}", base + d * length / 2, d, (2.4, length, 2.4), "crest")
    s = segments(g, sp, 19, 32, 10, 19, 13, -6, 16 * K - 4, shape=(0.62, 1.25), plates=False, spikes=None, crest=20,
                 eyes={i: pose == AIM for i in (3, 6, 9)})
    tail(g, sp, s, 9, 26)


TAKES = {"A": ("The Chain", take_a), "B": ("The Wyrm", take_b), "C": ("The Oarfish", take_c)}


def build(key, pose):
    title, fn = TAKES[key]
    m = Model(f"drowned_{key}_{pose}")
    g = m.group("body", (0, 0, 0))
    fn(g, pose)
    # hover: idle and aim float ~1.2 blocks clear of the floor; the surge drives the head half a block into it
    floor = -8.0 if pose == SURGE else 20.0
    shift = floor - float(m.bounds()[0][1])
    for c in m.cubes:
        c.frm[1] += shift
        c.to[1] += shift
        c.origin[1] += shift
    return m, title


VIEWS = [
    {"name": "clay_34", "mode": "clay", "camera": "persp", "yaw": 38, "height": 8.0, "dist": 21},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
    {"name": "sil_top", "mode": "silhouette", "camera": "ortho_top"},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -40, "height": 1.62, "dist": 19},
]
LABELS = {"clay_34": "three-quarter", "sil_side": "side, silhouette", "sil_top": "top, silhouette",
          "clay_eye": "a player's eye"}


def main(only=None, poses=POSES):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    for key in (only or TAKES):
        if (OUT / key).exists():
            shutil.rmtree(OUT / key)
        for pose in poses:
            m, title = build(key, pose)
            v2.run_blender(m.render_json(v2.PALETTE), OUT / key / pose, VIEWS)
            lo, hi = m.bounds()
            print(key, pose, title, "size (blocks)", [round(float(x) / 16, 1) for x in hi - lo], "lowest",
                  round(float(lo[1]), 1), "cubes", len(m.cubes))
        tw, th, pad, top = 440, 340, 12, 60
        img = Image.new("RGB", (pad + len(VIEWS) * (tw + pad), top + len(poses) * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Drowned Elder {key}: {title}", font=sheet._font(26), fill=sheet.INK)
        for r, pose in enumerate(poses):
            for c, vw in enumerate(VIEWS):
                x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
                img.paste(sheet._tile(OUT / key / pose / f"{vw['name']}.png", tw, th), (x, y))
                dr.text((x, y + th + 6), f"{pose}: {LABELS[vw['name']]}", font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / f"{key}_{title.lower().replace(' ', '_')}.png")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
