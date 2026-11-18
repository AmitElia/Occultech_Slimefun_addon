"""The Tempest redesign, session 1 step 2: the head and core study for the Frozen Blast with the Full Storm wind.

Vanilla's breeze face (26.2 client, breeze.png / breeze_eyes.png): the face IS the visor band. Its eyes are two white
strokes that start on the band's sides and step down onto its front, towards the middle: an angry V that wraps the
corners. The heavy core's faces (heavy_core.png) are a raised frame round a dark recess.

  Heads (each over the plain keystone K1)
    H1  Vanilla Fury     the vanilla head at 4x, its wraparound V eyes exactly
    H2  Seal Circlet     a cracked ring of the seal's stone round the crown, tilted, a glyph lit, a gap at the break
    H3  Gale Crest       the visor band streams off the back of the head as wind ribbons, a swept crest on top
  Cores (each under H1)
    K1  Vanilla Keystone the heavy core on its corner, each face a raised frame round a glowing recess
    K2  Seal Setting     the keystone set in a broken stone collar (the seal's inner ring) that cups its lower corner
    K3  Cracked Heart    the core split into eight blocks with glowing seams; its top tip blown off and floating,
                         the light pouring up into the head

Model units: 16 = one block, y up, the face towards -z. Colours are zones, not the palette.
Run from the repository root: python tools/art/bosses/tempest_study.py
"""
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, rotation_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import tempest_silhouettes as ts, volley_crone_s2 as v2  # noqa: E402
from bosses.tide_silhouettes import plank  # noqa: E402

OUT = ROOT / "docs/art/bosses/tempest/overhaul/s1_study"
PALETTE = dict(ts.PALETTE, wind=(196, 210, 240), wind_dark=(150, 160, 214), recess=(30, 34, 40), eye_gold=(249, 213, 100))
K = ts.K
CORE, CORE_Y, TIP = ts.CORE, ts.CORE_Y, ts.CORE_TIP
HEAD_Y = CORE_Y + TIP - 4          # the head's underside sits on the core's top point


# ---- heads ------------------------------------------------------------------------------------------------------------

def head_base(g, y):
    """Vanilla's head and band at K, with the wraparound V eyes (texel = K units)."""
    g.box("skull", (0, y + 4 * K, 0), (8 * K, 8 * K, 8 * K), "breeze")
    band_lo, front, half = y + 2 * K, -4.2 * K, 5 * K
    # vanilla's band (10x3x4) is clear in breeze.png apart from the white V brows, which are the eye_* cubes below;
    # the blue band you see is painted on the skull itself
    for sx in (-1, 1):
        # bottom row: on the front, 1..3 texels in from the edge
        g.box(f"eye_lo_{sx}", (sx * (half - 2 * K), band_lo + 0.5 * K, front - 0.2), (2 * K, K, 0.5), "eye")
        # middle row: round the corner, last texel of the front and first of the side
        g.box(f"eye_mid_f{sx}", (sx * (half - 0.5 * K), band_lo + 1.5 * K, front - 0.2), (K, K, 0.5), "eye")
        g.box(f"eye_mid_s{sx}", (sx * (half + 0.2), band_lo + 1.5 * K, front + 0.5 * K), (0.5, K, K), "eye")
        # top row: on the side
        g.box(f"eye_hi_{sx}", (sx * (half + 0.2), band_lo + 2.5 * K, front + 1.75 * K), (0.5, K, 1.5 * K), "eye")
        # vanilla's real eyes: one yellow texel each side just under the band, wrapping the head's corner
        skull = 4 * K
        g.box(f"eye_gold_f{sx}", (sx * (skull - 0.5 * K), y + 1.5 * K, -skull - 0.25), (K, K, 0.5), "eye_gold")
        g.box(f"eye_gold_s{sx}", (sx * (skull + 0.25), y + 1.5 * K, -skull + 0.5 * K), (0.5, K, K), "eye_gold")


def h1(g, y):
    head_base(g, y)


def h2(g, y):
    head_base(g, y)
    cy = y + 6.2 * K
    c = g.group("circlet", (0, cy, 0), (-14, 20, 0))   # tilted down at the front, turned a little
    r, n = 26.0, 14
    for i in range(n):
        a = 360 * i / n
        if i in (2, 3):         # the break, front right
            continue
        ar = math.radians(a)
        w = 2 * r * math.tan(math.pi / n) * 1.1
        hgt = 8 if i % 2 else 10
        c.box(f"circ_{i}", (r * math.sin(ar), cy, r * math.cos(ar)), (w, hgt, 5), "stone", rotation=(0, a, 0))
        if i in (0, 6, 9, 12):
            c.box(f"circ_glyph_{i}", ((r + 2.8) * math.sin(ar), cy, (r + 2.8) * math.cos(ar)), (3.5, 4, 0.6),
                  "glyph", rotation=(0, a, 0))
    # the broken-off chunk, drifting off the break
    a = math.radians(360 * 2.5 / 14)
    c.box("circ_chunk", ((r + 8) * math.sin(a), cy + 7, (r + 8) * math.cos(a)), (8, 9, 5), "stone",
          rotation=(20, 360 * 2.5 / 14, 25))


def h3(g, y):
    head_base(g, y)
    band_y = y + 3.5 * K
    # the band's two ends stream back off the head as ribbons, rising and curling
    for sx in (-1, 1):
        for j, (lift, spread, length, wdt) in enumerate(((0, 4, 46, 11), (9, 10, 36, 7), (-8, 7, 30, 6))):
            pts = []
            for i in range(9):
                t = i / 8
                x = sx * (5 * K + spread * t + 4 * t * t)
                yy = band_y + lift * t + 10 * t * t
                z = -2 * K + length * t
                pts.append((x, yy, z))
            for i in range(8):
                w = wdt * (1 - i / 8) ** 0.7 + 1.2
                plank(g, f"tail{sx}_{j}_{i}", pts[i], pts[i + 1], w, 1.4, "wind" if j != 1 else "wind_dark",
                      up=(sx * 0.35, 1, 0))
    # a swept crest along the top, back over the crown
    pts = [(0, y + 8 * K + 2 + 18 * (i / 8) ** 1.6, -10 + 40 * i / 8) for i in range(9)]
    for i in range(8):
        plank(g, f"crest_{i}", pts[i], pts[i + 1], 12 * (1 - i / 8) + 2, 1.6, "wind", up=(0, 1, -0.6))


# ---- cores ------------------------------------------------------------------------------------------------------------

def framed(c, name, centre, edge, glow=True):
    """A heavy-core cube: the block plus, on each face, a raised frame round a recess (lit or dark)."""
    x, y, z = centre
    c.box(name, centre, (edge, edge, edge), "steel")
    inset = edge * 0.5
    rim = edge * 0.14
    for ax in range(3):
        for s in (-1, 1):
            off = [0.0, 0.0, 0.0]
            off[ax] = s * (edge / 2 + 0.25)
            size = [inset + 2 * rim] * 3
            size[ax] = 0.5
            c.box(f"{name}_rim{ax}{s}", (x + off[0], y + off[1], z + off[2]), tuple(size), "steel_dark")
            off[ax] = s * (edge / 2 + 0.5)
            size = [inset] * 3
            size[ax] = 0.5
            c.box(f"{name}_pit{ax}{s}", (x + off[0], y + off[1], z + off[2]), tuple(size), "core_glow" if glow else "recess")


def k1(g):
    c = g.group("core", (0, CORE_Y, 0), ts.CORE_ROT)
    framed(c, "core", (0, CORE_Y, 0), CORE)


def k2(g):
    k1(g)
    # a broken stone collar: two tilted rows of tiles cupping the lower corner, a third of it gone
    for row, (y, r, tilt, h) in enumerate(((CORE_Y - 12, 18, 38, 9), (CORE_Y - 3, 24, 22, 7))):
        n = 12
        for i in range(n):
            a = 360 * i / n + 15 * row
            if 300 <= a % 360 or a % 360 < 20:     # the missing third, front left
                continue
            ar = math.radians(a)
            w = 2 * r * math.tan(math.pi / n) * 1.12
            g.box(f"collar{row}_{i}", (r * math.sin(ar), y, r * math.cos(ar)), (w, h, 4), "stone", rotation=(-tilt, a, 0))
            if row == 1 and i % 3 == 0:
                g.box(f"collar_glyph_{i}", ((r + 2) * math.sin(ar), y, (r + 2) * math.cos(ar)), (3, 3, 0.6), "glyph",
                      rotation=(-tilt, a, 0))
    # the broken piece of collar, dropping away
    g.box("collar_chunk", (-24, CORE_Y - 22, -14), (9, 7, 4), "stone", rotation=(30, -40, 35))


def k3(g):
    """Eight octant blocks with seams of light; the top one (the tip under the head) blown up and off."""
    rot = rotation_matrix(ts.CORE_ROT)
    q = CORE / 4
    octs = [(sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    tip = max(octs, key=lambda o: (rot @ np.array(o, float))[1])
    c = g.group("core", (0, CORE_Y, 0), ts.CORE_ROT)
    c.box("core_light", (0, CORE_Y, 0), (CORE * 0.86, CORE * 0.86, CORE * 0.86), "core_glow")
    for o in octs:
        centre = (o[0] * q, CORE_Y + o[1] * q, o[2] * q)
        if o == tip:
            continue
        c.box(f"oct{o}", centre, (CORE / 2 - 1.2,) * 3, "steel")
    # the blown tip floats free, turned, off to the front right of the head line
    lift = rot.T @ np.array([26.0, -2.0, -18.0])
    at = (tip[0] * q + lift[0], CORE_Y + tip[1] * q + lift[1], tip[2] * q + lift[2])
    t = c.group("tip", at, (25, 30, -20))
    t.box("tip_block", at, (CORE / 2 - 1.2,) * 3, "steel")


HEADS = {"H1": ("Vanilla Fury", h1), "H2": ("Seal Circlet", h2), "H3": ("Gale Crest", h3)}
CORES = {"K1": ("Vanilla Keystone", k1), "K2": ("Seal Setting", k2), "K3": ("Cracked Heart", k3)}


def build(key):
    m = Model(f"tempest_study_{key}")
    g = m.group("body", (0, 0, 0))
    if key in HEADS:
        HEADS[key][1](g, HEAD_Y)
        k1(g)
    else:
        CORES[key][1](g)
        h1(g, HEAD_Y)
    return m


def views():
    mid = (CORE_Y + 20) / 16
    return [
        {"name": "close_34", "mode": "flat", "camera": "persp", "yaw": 32, "height": mid + 0.9, "dist": 8.0, "target_z": mid,
         "player": False, "lens": 40},
        {"name": "below", "mode": "clay", "camera": "persp", "yaw": -28, "height": 1.62, "dist": 7.5, "target_z": mid + 0.2,
         "player": False, "lens": 40},
    ]


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    v2.PALETTE.update(PALETTE)
    vs = views()
    rows = [("Heads (over K1)", HEADS), ("Cores (under H1)", CORES)]
    tw, th, pad, top = 430, 430, 10, 56
    cols = 3 * len(vs)
    img = Image.new("RGB", (pad + cols * (tw + pad), top + len(rows) * (th + 56 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Tempest: head and core study (three-quarter, and from below as a player sees it)", font=sheet._font(24), fill=sheet.INK)
    for r, (label, items) in enumerate(rows):
        y0 = top + r * (th + 56 + pad)
        for i, (key, (title, _)) in enumerate(items.items()):
            m = build(key)
            v2.run_blender(m.render_json(v2.PALETTE), OUT / key, vs)
            print(key, title, "cubes", len(m.cubes))
            for j, v in enumerate(vs):
                x = pad + (i * len(vs) + j) * (tw + pad)
                img.paste(sheet._tile(OUT / key / f"{v['name']}.png", tw, th), (x, y0 + 26))
            dr.text((pad + i * len(vs) * (tw + pad), y0 + 2), f"{key}  {title}", font=sheet._font(19), fill=sheet.INK)
    img.save(OUT / "study.png")


if __name__ == "__main__":
    main()
