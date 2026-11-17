"""The Blaze Choir redesign, session 1 step 2, round 2: the Bass's head.

Picked from round 1 (choir_heads.py): the Soprano's Chime Fringe, the Alto's Finger Cymbals and the singing mouth on all
three. None of the Bass's three was picked, so here are three more, all with the singing mouth:
  B4  Bell Helm       a smaller bell worn as a helmet, its lip just above the eyes
  B5  Handbell Ring   a broad band with a ring of small handbells hanging from it
  B6  Bell Wheel      the wooden wheel and yoke that swing a church bell, behind and over the head

Run from the repository root, with the folder holding assets/ from the 26.2 client as the argument:
python tools/art/bosses/choir_heads2.py <folder>
"""
import math
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit import sheet  # noqa: E402
from bosses import choir_heads as h, choir_silhouettes as cs, volley_crone_s2 as v2  # noqa: E402
from bosses.archevoker_silhouettes import ring_panels, vocto  # noqa: E402

OUT = ROOT / "docs/art/bosses/blaze_choir/overhaul/s1_heads2"


def small_bell(g, name, x, y, z, s):
    """A bell hanging with its top at y; s is its height."""
    for i, (a, ra, b, rb) in enumerate(((0, 0.3, 0.5, 0.42), (0.5, 0.42, 1, 0.8))):
        ring_panels(g, f"{name}_{i}", y - a * s, y - b * s, ra * s, rb * s, "brass", n=8, t=0.9, cx=x, cz=z)
    g.box(f"{name}_top", (x, y, z), (0.7 * s, 0.8, 0.7 * s), "brass_dark")


def bell_helm(g, x, y, k):
    profile = ((y + 19, 6.5), (y + 14, 11), (y + 5, 15), (y + 0.5, 17.7), (y - 5, 21))
    for i in range(len(profile) - 1):
        (y1, r1), (y2, r2) = profile[i], profile[i + 1]
        ring_panels(g, f"helm_{i}", y1, y2, r1, r2, "brass", n=12, t=1.5, start=15, cx=x)
    ring_panels(g, "helm_lip", y - 3.5, y - 6, 20, 22.2, "brass_dark", n=12, t=2, start=15, cx=x)
    ring_panels(g, "helm_band", y + 12, y + 9.5, 12.3, 13.6, "brass_dark", n=12, t=1.8, start=15, cx=x)
    vocto(g, "helm_top", (x, y + 19, 0), 14, 1.6, 14, "brass_dark", cham=0.29)
    for a in (0, 90):
        g.box(f"helm_canon_{a}", (x, y + 22, 0), (10, 4, 2.6), "brass_dark", rotation=(0, a, 0))


def handbell_ring(g, x, y, k):
    w = 8 * k + 2
    vocto(g, "ring_band", (x, y - 0.5, 0), w, 4, w, "brass", cham=0.1)
    vocto(g, "ring_brim", (x, y + 2, 0), w + 11, 1.8, w + 11, "brass_dark", cham=0.29)
    ring_panels(g, "ring_cap", y + 9, y + 3, 5, 12.5, "cord", n=8, t=1.4, start=22.5, cx=x)
    g.box("ring_knob", (x, y + 10.5, 0), (3.6, 3.6, 3.6), "brass_dark", rotation=(0, 45, 45))
    for i in range(8):
        a = math.radians(45 * i + 22.5)
        px, pz = x + 19 * math.sin(a), 19 * math.cos(a)
        g.box(f"ring_hook{i}", (px, y + 0.5, pz), (0.8, 2.6, 0.8), "brass_dark")
        small_bell(g, f"hb{i}", px, y - 1, pz, 7.5)


def bell_wheel(g, x, y, k):
    c = (x, y - 8, 16)
    r = 26
    cx, cy, cz = c
    for i in range(16):
        a = 360 * i / 16
        ar = math.radians(a)
        g.box(f"wheel_{i}", (cx + r * math.sin(ar), cy + r * math.cos(ar), cz), (r * 0.42, 3.6, 3), "wood", rotation=(0, 0, -a))
    for i in range(4):
        g.box(f"spoke_{i}", (cx, cy, cz), (2.4, 2 * r, 2.2), "wood", rotation=(0, 0, 22.5 + 45 * i))
    g.box("hub", (cx, cy, cz), (9, 9, 4), "brass_dark", rotation=(0, 0, 45))
    g.box("yoke", (x, y + 3.5, 0), (40, 6, 9), "wood")
    for sx in (-1, 1):
        g.box(f"yoke_strap_{sx}", (x + sx * 10, y + 3.5, 0), (2.2, 6.6, 9.6), "brass_dark")
        g.box(f"yoke_end_{sx}", (x + sx * 21.5, y + 3.5, 0), (3, 3.6, 3.6), "brass_dark")
        g.box(f"yoke_arm_{sx}", (x + sx * 10, y + 3.5, 10), (3, 4, 14), "brass_dark")
    g.box("yoke_cap", (x, y + 8, 0), (22, 3, 7), "brass")


ENTRIES = {
    "S3": ("soprano", "Chime Fringe (locked)", h.chime_fringe),
    "A3": ("alto", "Finger Cymbals (locked)", h.finger_cymbals),
    "B4": ("bass", "Bell Helm", bell_helm),
    "B5": ("bass", "Handbell Ring", handbell_ring),
    "B6": ("bass", "Bell Wheel", bell_wheel),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(cs.PALETTE)
    h.OPTIONS.update({k: (s, t, "sing", p) for k, (s, t, p) in ENTRIES.items()})
    h.TARGET["bass"] = 4.9
    for key, (_, title, _p) in ENTRIES.items():
        m, singer, _t = h.build(key)
        if (OUT / key).exists():
            shutil.rmtree(OUT / key)
        vs = h.views(singer)
        if singer == "bass":
            vs[0]["dist"] = vs[1]["dist"] = 4.6
            vs[0]["height"] = vs[1]["height"] = 3.9
        v2.run_blender(m.render_json(v2.PALETTE), OUT / key, vs)
        print(key, title, "cubes", len(m.cubes))
    keys = list(ENTRIES)
    tw, th, pad, top = 400, 400, 10, 56
    rows = [keys[2:], keys[:2]]
    img = Image.new("RGB", (pad + 6 * (tw + pad) + pad * 2, top + 2 * (th + 30 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Blaze Choir: three new heads for the Bass; the Soprano and the Alto with the singing mouth", font=sheet._font(26), fill=sheet.INK)
    for r, row in enumerate(rows):
        for c, key in enumerate(row):
            for i, view in enumerate(("hero", "front")):
                x, y = pad + (c * 2 + i) * (tw + pad) + c * pad, top + r * (th + 30 + pad)
                img.paste(sheet._tile(OUT / key / f"{view}.png", tw, th), (x, y))
                if i == 0:
                    dr.text((x, y + th + 5), f"{key}: {ENTRIES[key][1]}", font=sheet._font(18), fill=sheet.INK)
    img.save(OUT / "heads2.png")


if __name__ == "__main__":
    main()
