"""The Drowned Elder (the Wyrm), session 1 step 2: the head and segment study.

Three heads, each built from vanilla's Elder Guardian at 3x, each shown at rest and in its "stare" (the Mining Fatigue
pulse, when the head shows its eye):
  H1  the Elder        vanilla's head as it is: the box body, its plates, the twelve edge spikes, the eye on its face
  H2  the Petal Maw    vanilla's four plates have become jaws hinged at mid-head; at rest they close into a tapered snout
                       over the eye, in the stare they peel open like petals and the eye stares out of the throat
  H3  the Spike Hood   the back spikes have grown into a fan of long spikes webbed with fin, a cobra's hood; folded back
                       along the neck at rest, flared wide in the stare

Three segments for the body, each shown as a short run with the middle segment's eye shut and open (the beam tell):
  S1  the Barrel       vanilla's barrel: a core, four plates, the dorsal spike; the side plate slides back off the eye
  S2  the Shingle      the plates tilt back and overlap the next segment like roof shingles (a saw-tooth back); the side
                       shingle lifts off the eye
  S3  the Vertebra     a slimmer core with a raised collar of plates at the front of each segment and the spikes in a
                       ring round the collar, like a spine; a lid slides off the eye between two collars

Model units: 16 = one block, y up, the face towards -z.
Run from the repository root: python tools/art/bosses/drowned_study.py [H1 H2 H3 S1 S2 S3]
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
from bosses.drowned_serpent import K, PALETTE, Spine, along, n, obox, spike  # noqa: E402

OUT = ROOT / "docs/art/bosses/drowned_elder/overhaul/s1_study"
PAL = dict(PALETTE, throat=(54, 46, 58), membrane=(132, 122, 146))
REST, STARE = "rest", "stare"
SHUT, OPEN = "shut", "open"

NECK = [(0, 48, 0), (0, 46, 60), (0, 44, 120), (0, 44, 200)]          # a straight-ish neck behind the head
RUN = [(0, 40, 0), (4, 42, 40), (10, 46, 80), (10, 46, 140)]          # a gently bending run of segments


# ---- heads --------------------------------------------------------------------------------------------------------------

def edge_spikes(g, c, F, keep):
    """Vanilla's twelve edge spikes; keep(direction) decides which stay."""
    r, u, f = F.T
    i = 0
    for sx in (-1, 1):
        for sy in (-1, 1):
            for off, d in ((r * sx * 6 * K + u * sy * 6 * K, r * sx + u * sy),
                           (u * sy * 6 * K + f * sx * 8 * K, u * sy + f * sx * 0.6),
                           (r * sy * 6 * K + f * sx * 8 * K, r * sy + f * sx * 0.6)):
                d = n(d)
                if keep(off, d):
                    under = np.dot(d, u) < -0.3
                    spike(g, f"hspike{i}", c + off, d - f * 0.35, (5 if under else 9) * K, 2 * K)
                i += 1


def head_core(g, sp, plates=True, eye=True):
    c, F = sp.at(8 * K)
    r, u, f = F.T
    obox(g, "head", c, np.array([12, 12, 16]) * K, F, "hide")
    if plates:
        pl = 2 * K
        for sx in (-1, 1):
            obox(g, f"plate_x{sx}", c + r * sx * (6 * K + pl / 2), (pl, 12 * K, 12 * K), F, "plate")
            obox(g, f"plate_y{sx}", c + u * sx * (6 * K + pl / 2), (12 * K, pl, 12 * K), F, "plate")
    if eye:
        obox(g, "eye", c + f * (8 * K + 0.6), (2 * K, 2 * K, 1.2), F, "eye")
    return c, F


def h1(g, sp, state):
    c, F = head_core(g, sp)
    edge_spikes(g, c, F, lambda off, d: True)
    if state == STARE:
        obox(g, "eye_glow", c + F[:, 2] * (8 * K + 1.2), (2 * K, 2 * K, 1.2), F, "glow")


def h2(g, sp, state):
    """The plates are four jaws hinged at mid-head: closed into a snout at rest, peeled open in the stare. Each jaw
    tapers to a hooked point and has a row of teeth on its inner face (flat flaps read as a cardboard box)."""
    c, F = head_core(g, sp, plates=False, eye=False)
    r, u, f = F.T
    a = math.radians(-12 if state == REST else 58)
    length = 15 * K
    for name, side in (("jaw_r", r), ("jaw_l", -r), ("jaw_t", u), ("jaw_b", -u)):
        axis = n(np.cross(side, f))
        hinge = c + side * 7 * K - f * 1 * K
        d = f * math.cos(a) + side * math.sin(a)
        thick = n(np.cross(d, axis))
        inner = thick if np.dot(thick, side) < 0 else -thick
        Fj = np.column_stack([axis, thick, d])
        width = 13 * K if name in ("jaw_t", "jaw_b") else 11 * K
        obox(g, name, hinge + d * length * 0.3, (width, 2 * K, length * 0.6), Fj, "plate")
        obox(g, name + "_mid", hinge + d * length * 0.68, (width * 0.68, 2 * K, length * 0.3), Fj, "plate")
        obox(g, name + "_tip", hinge + d * length * 0.9, (width * 0.34, 2 * K, length * 0.24), Fj, "plate")
        obox(g, name + "_ridge", hinge + d * length * 0.45 - inner * 1.4 * K, (2 * K, 1 * K, length * 0.8), Fj, "plate")
        # the hooked point and a row of teeth on the inner face, pointing into the mouth
        spike(g, name + "_fang", hinge + d * length * 0.98, n(d + inner * 1.1), 4.5 * K, 1.6 * K)
        for t, (along_d, across) in enumerate(((0.5, -0.28), (0.5, 0.28), (0.72, -0.16), (0.72, 0.16), (0.36, 0.0))):
            base = hinge + d * length * along_d + axis * width * across * (0.9 if along_d < 0.6 else 0.6)
            spike(g, f"{name}_tooth{t}", base + inner * 0.8 * K, n(inner + d * 0.35), 3 * K, 1.0 * K)
    # the throat: the whole face is a dark recess with the eye deep in it
    obox(g, "throat", c + f * (8 * K + 0.3), (11 * K, 11 * K, 1.0), F, "throat")
    obox(g, "eye", c + f * (8 * K + 0.9), (3 * K, 3 * K, 1.2), F, "glow" if state == STARE else "eye")
    # only the back spikes stay; the front ones were the jaws' edges
    edge_spikes(g, c, F, lambda off, d: np.dot(off, f) < -1)


def h3(g, sp, state):
    """Vanilla's head; the back spikes become a webbed fan, folded back at rest, flared in the stare."""
    c, F = head_core(g, sp)
    r, u, f = F.T
    edge_spikes(g, c, F, lambda off, d: np.dot(off, f) > -1 and np.dot(d, u) < 0.3 and np.dot(d, u) > -0.3)
    spread = {REST: 0.35, STARE: 3.2}.get(state, 0.08)      # any other state: tucked flat (the dive)
    tips = []
    angles = (-100, -75, -50, -25, 0, 25, 50, 75, 100)
    for i, th in enumerate(angles):
        t = math.radians(th)
        out = u * math.cos(t) + r * math.sin(t)
        base = c - f * 6 * K + out * 7 * K
        length = (23 - 8 * abs(th) / 100) * K
        d = n(out * spread - f)
        spike(g, f"hood{i}", base, d, length, 2 * K)
        tips.append((base, d, length))
    for i in range(len(tips) - 1):                         # fin webbing between neighbouring spikes
        (b0, d0, l0), (b1, d1, l1) = tips[i], tips[i + 1]
        m0, m1 = b0 + d0 * l0 * 0.38, b1 + d1 * l1 * 0.38
        dm = n(d0 + d1)
        across = m1 - m0
        thin = n(np.cross(dm, across))
        y = dm
        x = thin
        Fw = np.column_stack([x, y, np.cross(x, y)])
        obox(g, f"web{i}", (m0 + m1) / 2, (1.0, (l0 + l1) / 2 * 0.62, float(np.linalg.norm(across)) + 1), Fw, "membrane")
    if state == STARE:
        obox(g, "eye_glow", c + f * (8 * K + 1.2), (2 * K, 2 * K, 1.2), F, "glow")


# ---- segments -----------------------------------------------------------------------------------------------------------

def seg_frame(sp, s, ln):
    c, F = sp.at(s + ln / 2)
    return c, F, F.T


def s1(g, sp, s, i, w, ln, eye):
    c, F, (r, u, f) = seg_frame(sp, s, ln)
    obox(g, f"seg{i}", c, (w, w, ln), F, "hide")
    pl = w / 6
    for sx in (-1, 1):
        slide = -f * ln * 0.5 if (eye == OPEN) else 0
        obox(g, f"seg{i}_px{sx}", c + r * sx * (w / 2 + pl / 2) + slide, (pl, w * 0.84, ln * 0.8), F, "plate")
        obox(g, f"seg{i}_py{sx}", c + u * sx * (w / 2 + pl / 2), (w * 0.84, pl, ln * 0.8), F, "plate")
        spike(g, f"seg{i}_side{sx}", c + r * sx * w / 2 - f * ln * 0.2, r * sx - f * 0.6, w * 0.35, max(2, w / 8))
        if eye is not None:
            obox(g, f"seg{i}_eye{sx}", c + r * sx * (w / 2 + 0.6) + f * ln * 0.15, (1.2, w * 0.5, w * 0.5), F,
                 "glow" if eye == OPEN else "lid")
    spike(g, f"seg{i}_dorsal", c + u * w / 2, u - f * 0.55, 40, max(3, w / 5))


def s2(g, sp, s, i, w, ln, eye):
    c, F, (r, u, f) = seg_frame(sp, s, ln)
    obox(g, f"seg{i}", c, (w, w, ln), F, "hide")
    tilt = math.radians(14)
    for name, side, ax in (("x1", r, u), ("x-1", -r, u), ("y1", u, r), ("y-1", -u, r)):
        lift = math.radians(55) if (eye == OPEN and name in ("x1", "x-1")) else             {"y1": tilt, "y-1": 0.0}.get(name, math.radians(7))
        hinge = c + side * (w / 2 + 1) + f * ln * 0.45
        d = n(-f * math.cos(lift) + side * math.sin(lift))
        thick = n(np.cross(d, ax))
        Fs = np.column_stack([ax, thick, d])
        obox(g, f"seg{i}_sh{name}", hinge + d * ln * 0.62, (w * 1.0, 2.6, ln * 1.25), Fs, "plate")
        if eye is not None and name in ("x1", "x-1"):
            obox(g, f"seg{i}_eye{name}", c + side * (w / 2 + 0.6), (1.2, w * 0.5, w * 0.5) if name else (1, 1, 1), F,
                 "glow" if eye == OPEN else "lid")
    spike(g, f"seg{i}_dorsal", c + u * (w / 2 + 2) - f * ln * 0.3, u - f * 0.7, 40, max(3, w / 5))


def s3(g, sp, s, i, w, ln, eye):
    c, F, (r, u, f) = seg_frame(sp, s, ln)
    core = w * 0.72
    obox(g, f"seg{i}", c, (core, core, ln + 2), F, "hide")
    front = c + f * ln * 0.32
    cl = ln * 0.3
    for sx in (-1, 1):
        obox(g, f"seg{i}_cx{sx}", front + r * sx * (w / 2), (w / 5, w * 1.0, cl), F, "plate")
        obox(g, f"seg{i}_cy{sx}", front + u * sx * (w / 2), (w * 1.0, w / 5, cl), F, "plate")
        d = n(r * sx + u)
        spike(g, f"seg{i}_ring{sx}", front + (r * sx + u) * w * 0.45, d - f * 0.45, w * 0.7, max(2.5, w / 7))
        spike(g, f"seg{i}_side{sx}", front + r * sx * w * 0.55, r * sx - f * 0.45, w * 0.45, max(2.5, w / 7))
        if eye is not None:
            pos = c - f * ln * 0.12 + r * sx * (core / 2 + 0.6)
            obox(g, f"seg{i}_eye{sx}", pos, (1.2, core * 0.6, core * 0.6), F, "glow" if eye == OPEN else "lid")
            if eye == OPEN:
                obox(g, f"seg{i}_lid{sx}", pos - f * core * 0.55 + r * sx * 1.2, (1.2, core * 0.62, core * 0.3), F, "lid")
    spike(g, f"seg{i}_dorsal", front + u * (w / 2 + 2), u - f * 0.55, 40, max(3, w / 5))


SEGS = {"S1": ("The Barrel", s1, -4), "S2": ("The Shingle", s2, -2), "S3": ("The Vertebra", s3, -2)}
HEADS = {"H1": ("The Elder", h1), "H2": ("The Petal Maw", h2), "H3": ("The Spike Hood", h3)}


def build_head(key, state):
    m = Model(f"drowned_{key}_{state}")
    g = m.group("body", (0, 0, 0))
    sp = Spine(NECK)
    HEADS[key][1](g, sp, state)
    s = 16 * K - 2
    for i in range(2):                                       # two plain segments behind it for context
        s1(g, sp, s, i, 28 - 2 * i, 26, None)
        s += 22
    return m


def build_run(key, eye_state):
    m = Model(f"drowned_{key}_{eye_state}")
    g = m.group("body", (0, 0, 0))
    sp = Spine(RUN)
    _, fn, gap = SEGS[key]
    s = 0.0
    for i in range(4):
        w, ln = 28 - 1.5 * i, 26 - i
        fn(g, sp, s, i, w, ln, eye_state if i == 1 else None)
        s += ln + gap
    return m


HEAD_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 38, "height": 4.4, "dist": 13, "player": False},
    {"name": "flat_side", "mode": "flat", "camera": "persp", "yaw": 90, "height": 3.6, "dist": 13, "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -18, "height": 1.62, "dist": 12, "player": False},
]
RUN_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 62, "height": 4.4, "dist": 9, "player": False},
    {"name": "flat_top", "mode": "flat", "camera": "persp", "yaw": 80, "height": 9.0, "dist": 6, "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front", "player": False},
]


def render(m, out, views):
    v2.run_blender(m.render_json(v2.PALETTE), out, views)


def compose(rows, views, title, path):
    """rows: [(label, folder)]; one row per state, one column per view."""
    tw, th, pad, top = 440, 340, 12, 60
    img = Image.new("RGB", (pad + len(views) * (tw + pad), top + len(rows) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), title, font=sheet._font(26), fill=sheet.INK)
    for r, (label, folder) in enumerate(rows):
        for c, vw in enumerate(views):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(folder / f"{vw['name']}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{label}: {vw['name'].replace('_', ' ')}", font=sheet._font(17), fill=sheet.DIM)
    img.save(path)


def main(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PAL)
    for key in (only or list(HEADS) + list(SEGS)):
        if (OUT / key).exists():
            shutil.rmtree(OUT / key)
        if key in HEADS:
            rows = []
            for state in (REST, STARE):
                m = build_head(key, state)
                render(m, OUT / key / state, HEAD_VIEWS)
                rows.append((state, OUT / key / state))
                print(key, state, m.stats()["cubes"], "cubes", m.stats()["size_blocks"])
            title = HEADS[key][0]
            compose(rows, HEAD_VIEWS, f"Drowned Elder head {key}: {title}",
                    OUT / f"{key}_{title.lower().replace(' ', '_')}.png")
        else:
            rows = []
            for state in (SHUT, OPEN):
                m = build_run(key, state)
                render(m, OUT / key / state, RUN_VIEWS)
                rows.append((f"eye {state}", OUT / key / state))
                print(key, state, m.stats()["cubes"], "cubes")
            title = SEGS[key][0]
            compose(rows, RUN_VIEWS, f"Drowned Elder segment {key}: {title}",
                    OUT / f"{key}_{title.lower().replace(' ', '_')}.png")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
