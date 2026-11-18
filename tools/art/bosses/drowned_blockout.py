"""The Drowned Elder (the Wyrm), session 1 step 3: the full blockout.

Picked so far (docs/art/bosses/drowned_elder/overhaul/plan.md): the Abyssal Serpent, body plan B (the Wyrm: overlapping
segments, a row of tall spikes down the back, swimming in humps), head H3 (the Spike Hood: vanilla's elder head at 3x
with a webbed fan of nine long spikes behind it) and segment S2 (the Shingle: plates tilted back over the next segment,
the side shingle swinging out like a gill cover to show the eye).

The whole boss, in the four moments that matter to the fight:
  idle   swimming in humps a block over the floor, the hood folded back along the neck
  aim    the multi-beam tell: three segments swing their gill shingles open on the players, the body curls to face them
  stare  the Mining Fatigue pulse: it coils overhead in a ring, the head hanging down out of it, the hood flared, the
         eye lit
  surge  the Tidal Surge: it dives head first into the floor, the hood swept back, the body arched over the arena

Model units: 16 = one block, y up, the face towards -z. The blue figure is a player (1.8 blocks).
Run from the repository root: python tools/art/bosses/drowned_blockout.py [idle aim stare surge]
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
from bosses.drowned_serpent import K, Spine, along, n, obox, spike, tail  # noqa: E402
from bosses import drowned_study as st  # noqa: E402

OUT = ROOT / "docs/art/bosses/drowned_elder/overhaul/s1_blockout"
POSES = ("idle", "aim", "stare", "surge")
COUNT = 10
EYES = (2, 4, 6)                        # the three segments that carry the beam eyes


def shingle(g, sp, s, i, w, ln, eye, dorsal):
    """S2: a core with four plates tilted back over the next segment (the bottom one flush); the side shingles swing
    out to 55 degrees to show the eye under them. eye: None (no eye), "shut" or "open"."""
    c, F = sp.at(s + ln / 2)
    r, u, f = F.T
    obox(g, f"seg{i}", c, (w, w, ln), F, "hide")
    for name, side, ax in (("r", r, u), ("l", -r, u), ("t", u, r), ("b", -u, r)):
        if eye == "open" and name in ("r", "l"):
            lift = math.radians(55)
        else:
            lift = math.radians({"t": 14, "b": 0}.get(name, 7))
        hinge = c + side * (w / 2 + 1) + f * ln * 0.45
        d = n(-f * math.cos(lift) + side * math.sin(lift))
        thick = n(np.cross(d, ax))
        obox(g, f"seg{i}_sh{name}", hinge + d * ln * 0.62, (w, 2.6, ln * 1.25), np.column_stack([ax, thick, d]), "plate")
        if eye is not None and name in ("r", "l"):
            obox(g, f"seg{i}_eye{name}", c + side * (w / 2 + 0.6), (1.2, w * 0.5, w * 0.5), F,
                 "glow" if eye == "open" else "lid")
    spike(g, f"seg{i}_dorsal", c + u * (w / 2 + 2) - f * ln * 0.3, u - f * 0.7, dorsal, max(3, w / 5))
    return c, F


def wyrm(g, pts, pose):
    sp = Spine(pts)
    st.h3(g, sp, {"stare": st.STARE, "surge": "tuck"}.get(pose, st.REST))
    s = 16 * K - 2
    first = None
    for i in range(COUNT):
        t = i / (COUNT - 1)
        w, ln = 28 - 16 * t, 26 - 8 * t
        eye = ("open" if pose == "aim" else "shut") if i in EYES else None
        frame = shingle(g, sp, s, i, w, ln, eye, 44 - 22 * t)
        first = first or frame
        s += ln - 2
    # pectoral fins on the first segment, swept back and down
    c, F = first
    r, u, f = F.T
    for sx in (-1, 1):
        d = n(r * sx * 0.55 - f - u * 0.45)
        along(g, f"pectoral{sx}", c + r * sx * 18 + d * 16, d, (1.2, 36, 22), "fin", thin=u)
    tail(g, sp, s, 11, 36)


def ring(cx, cy, cz, radius, a0, a1, y0, y1, count):
    return [(cx + radius * math.cos(math.radians(a)), y, cz + radius * math.sin(math.radians(a)))
            for a, y in zip(np.linspace(a0, a1, count), np.linspace(y0, y1, count))]


SPINES = {
    "idle": [(0, 60, 0), (0, 52, 40), (4, 88, 96), (0, 40, 156), (-4, 76, 212), (0, 36, 266), (2, 58, 318),
             (0, 40, 380), (0, 40, 460)],
    # it curls to face the players spread round its front: the beam segments turn their sides towards them
    "aim": [(0, 66, 0), (-6, 58, 40), (-40, 70, 86), (-30, 50, 146), (20, 60, 180), (56, 44, 230), (30, 40, 290),
            (-10, 44, 330), (-20, 40, 400)],
    # a ring overhead, the head hanging down out of it towards the front
    "stare": [(0, 60, 0), (0, 96, 22), (0, 124, 52)] + ring(0, 140, 0, 66, 80, 400, 142, 128, 10),
    "surge": [(0, 0, -50), (0, 40, -42), (0, 110, -10), (6, 150, 50), (0, 140, 120), (-8, 100, 180), (0, 70, 240),
              (6, 56, 300), (0, 50, 380), (0, 48, 460)],
}
FLOOR = {"idle": 20.0, "aim": 20.0, "stare": 36.0, "surge": -8.0}


def build(pose):
    m = Model(f"drowned_blockout_{pose}")
    g = m.group("body", (0, 0, 0))
    wyrm(g, SPINES[pose], pose)
    shift = FLOOR[pose] - float(m.bounds()[0][1])
    for c in m.cubes:
        c.frm[1] += shift
        c.to[1] += shift
        c.origin[1] += shift
    return m


VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 38, "height": 7.0, "dist": 22},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
    {"name": "sil_top", "mode": "silhouette", "camera": "ortho_top"},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -35, "height": 1.62, "dist": 18},
    {"name": "flat_close", "mode": "flat", "camera": "persp", "yaw": 100, "height": 4.0, "dist": 12, "player": False},
]
LABELS = {"flat_34": "three-quarter", "sil_side": "side, silhouette", "sil_top": "top, silhouette",
          "clay_eye": "a player's eye", "flat_close": "close, from the right"}


def main(poses=POSES):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(st.PAL)
    for pose in poses:
        if (OUT / pose).exists():
            shutil.rmtree(OUT / pose)
        m = build(pose)
        v2.run_blender(m.render_json(v2.PALETTE), OUT / pose, VIEWS)
        stats = m.stats()
        print(pose, stats["cubes"], "cubes, size (blocks)", stats["size_blocks"], "lowest", stats["min"][1])
    tw, th, pad, top = 380, 294, 12, 60
    img = Image.new("RGB", (pad + len(VIEWS) * (tw + pad), top + len(POSES) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Drowned Elder: the Wyrm, full blockout (H3 Spike Hood + S2 Shingle)", font=sheet._font(26),
            fill=sheet.INK)
    for r, pose in enumerate(POSES):
        for c, vw in enumerate(VIEWS):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / pose / f"{vw['name']}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{pose}: {LABELS[vw['name']]}", font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "blockout.png")


if __name__ == "__main__":
    main(tuple(sys.argv[1:]) or POSES)
