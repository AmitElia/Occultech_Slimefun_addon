"""Session A test icons: Ritual Chalk (tier 0), Spirit Essence (tier 1), Hollow Sigil (tier 3)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from palettes import RAMPS  # noqa: E402
from pixelkit import Icon, Part  # noqa: E402
import review  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "art", "session-a")
os.makedirs(OUT, exist_ok=True)


def ritual_chalk():
    icon = Icon(16)
    # grip end top-right, worn drawing tip bottom-left
    a, b = (4.6, 10.4), (11.4, 3.6)
    vx, vy = b[0] - a[0], b[1] - a[1]
    ll = vx * vx + vy * vy

    def t_of(p):
        return ((p[0] + 0.5 - a[0]) * vx + (p[1] + 0.5 - a[1]) * vy) / ll

    stick = icon.capsule(a, b, 2.6)
    # the drawing tip is worn flat: cut the capsule's lower end
    # both ends are cut flat: worn drawing tip below, snapped end above (a cylinder end, not a rolled tube)
    stick = Part({p: n for p, n in stick.normals.items() if -0.14 < t_of(p) < 1.12})
    icon.paint(stick, RAMPS["chalk"])
    worn = [p for p in stick.keys() if t_of(p) < -0.03]
    icon.pixels(worn, RAMPS["chalk"][5])
    snapped = [p for p in stick.keys() if t_of(p) > 1.02]
    icon.pixels(snapped, RAMPS["chalk"][3])
    # chalky speckle on the lit face
    icon.pixels([(6, 7), (8, 6), (5, 9)], RAMPS["chalk"][3])
    # a facet edge along the stick: a hexagonal chalk stick, not a rolled tube
    for k in range(-1, 9):
        x, y = round(5.9 + k * 0.72), round(10.7 - k * 0.72)
        if (x, y) in stick.normals and k % 2 == 0:
            icon.pixels([(x, y)], RAMPS["chalk"][2])
    # the curved stroke it is drawing, from under the tip
    stroke = [(1, 14), (2, 14), (3, 15), (4, 15), (5, 15), (6, 15), (7, 14), (8, 14), (9, 13)]
    icon.pixels(stroke, RAMPS["chalk"][4])
    icon.pixels([(2, 15), (8, 13)], RAMPS["chalk"][3])
    # a little dust puff at the tip
    icon.pixels([(1, 12), (2, 11), (0, 13)], RAMPS["chalk"][5])
    icon.pixels([(1, 10)], RAMPS["chalk"][3])
    return icon


def spirit_essence():
    icon = Icon(16)
    body = icon.sphere(7.4, 10.8, 4.8)
    liquid = Part({p: n for p, n in body.normals.items() if p[1] >= 8})
    air = body - liquid
    icon.paint(air, RAMPS["glass"], outline=False, bias=-0.05)
    icon.paint(liquid, RAMPS["spirit"], outline=False, bias=0.0)
    icon.outline(body, RAMPS["glass"])
    neck = icon.box(5.9, 3.8, 8.9, 6.9, bevel=1.0)
    icon.paint(neck, RAMPS["glass"])
    cork = icon.box(5.4, 2.2, 9.4, 4.1, bevel=1.0)
    icon.paint(cork, RAMPS["wood"])
    # a spirit swirling inside the liquid
    icon.pixels([(6, 10), (7, 9), (8, 9), (9, 10), (9, 11), (8, 12), (7, 12)], RAMPS["spirit"][4])
    icon.pixels([(7, 11)], RAMPS["spirit"][5])
    # glass glint
    icon.pixels([(4, 8), (4, 9), (5, 7)], RAMPS["glass"][5])
    # the spirit escaping round the cork: a thick tendril rising right into a little ghost
    # tail: thickest near the ghost, thinning down into the cork
    icon.pixels([(9, 3), (10, 4)], RAMPS["spirit"][2])
    icon.pixels([(10, 3), (11, 3), (11, 4)], RAMPS["spirit"][3])
    ghost = icon.sphere(13.0, 2.7, 2.5, squash=0.9)
    icon.paint(ghost, RAMPS["spirit"], bias=0.28)
    icon.pixels([(12, 2), (14, 2)], RAMPS["spirit"][0])
    icon.pixels([(13, 4)], RAMPS["spirit"][1])
    return icon


def star_points(cx, cy, r_out, r_in, n=5, rot=-math.pi / 2):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def hollow_sigil():
    icon = Icon(16)
    star = icon.polygon(star_points(8.0, 8.4, 7.7, 3.0), bevel=1.3)
    icon.paint(star, RAMPS["bone"], bias=0.05)
    # the pentacle's circle runs across the arms, glowing hollow-cyan
    ring = icon.ring(8.0, 8.4, 6.0, 5.1)
    icon.paint(ring, RAMPS["hollowcy"], bias=0.1, outline_ramp=RAMPS["sculk"], outline_over=False)
    # sculk cracks in the old bone
    icon.pixels([(7, 3), (11, 9)], RAMPS["sculk"][2])
    core = icon.sphere(8.0, 8.6, 1.7)
    icon.paint(core, RAMPS["crimson"], bias=0.2, outline_ramp=RAMPS["sculk"])
    return icon


if __name__ == "__main__":
    icons = [("Ritual Chalk (T0)", ritual_chalk()), ("Spirit Essence (T1)", spirit_essence()), ("Hollow Sigil (T3)", hollow_sigil())]
    for name, icon in icons:
        icon.save(os.path.join(OUT, name.split(" (")[0].lower().replace(" ", "_") + ".png"))
    version = sys.argv[1] if len(sys.argv) > 1 else "v1"
    print(review.sheet([(n, i.img) for n, i in icons], os.path.join(OUT, f"review-{version}.png")))
