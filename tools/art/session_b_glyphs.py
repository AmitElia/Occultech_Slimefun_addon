"""Session B, part 2: runes (an original Occultech alphabet), footprints and crown pieces."""
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from glyphkit import Glyph, asymmetry, style, tint  # noqa: E402
from session_b import OUT, TINTS, sheet  # noqa: E402

# ------------------------------------------------------------------ runes (16 x 16)
# (name, strokes, symmetric). Strokes are polylines in 16 px space; the centre staff is x = 8.

RUNE_W = 2.0
RUNES = [
    ("ascend", [[(8, 2.5), (8, 14)], [(4, 7.5), (8, 2.5), (12, 7.5)]], True),
    ("root", [[(8, 2), (8, 9)], [(4, 14), (8, 9), (12, 14)]], True),
    ("eye", [[(8, 2.5), (13, 8), (8, 13.5), (3, 8), (8, 2.5)]], True),
    ("bind", [[(3.5, 2.5), (12.5, 2.5), (3.5, 13.5), (12.5, 13.5), (3.5, 2.5)]], True),
    ("gate", [[(4.5, 2), (4.5, 14)], [(11.5, 2), (11.5, 14)], [(4.5, 5), (8, 9), (11.5, 5)]], True),
    ("flame", [[(4, 2.5), (8, 7), (12, 2.5)], [(8, 7), (8, 14)]], True),
    ("hook", [[(9, 2), (9, 11), (8, 13.5), (5.5, 13.5), (4, 11)], [(9, 4.5), (12, 2.5)]], False),
    ("tide", [[(2.5, 6), (5.5, 3), (8.5, 6), (11.5, 3), (13.5, 5)], [(2.5, 12), (5.5, 9), (8.5, 12), (11.5, 9), (13.5, 11)]], False),
    ("moon", "moon", False),
    ("sun", "sun", True),
    ("ward", [[(8, 2), (8, 14)], [(3, 5.5), (13, 5.5)], [(3, 10.5), (13, 10.5)]], True),
    ("chain", "chain", True),
    ("spirit", "spirit", True),
    ("bone", [[(8, 4.5), (8, 11.5)], [(4.5, 2), (8, 4.5), (11.5, 2)], [(4.5, 14), (8, 11.5), (11.5, 14)]], True),
    ("thorn", [[(6, 2), (6, 14)], [(6, 4.5), (11.5, 8), (6, 11.5)]], False),
    ("star", [[(8, 2), (8, 14)], [(3, 5), (13, 11)], [(13, 5), (3, 11)]], True),
    ("seal", [[(3.5, 3.5), (12.5, 3.5), (12.5, 12.5), (3.5, 12.5), (3.5, 3.5)], [(8, 6.5), (8, 9.5)]], True),
    ("descend", [[(8, 2), (8, 13.5)], [(4, 9.5), (8, 13.5), (12, 9.5)]], True),
    ("crown", [[(3, 3), (5, 9), (8, 4.5), (11, 9), (13, 3)], [(4, 13), (12, 13)]], True),
    ("storm", [[(10.5, 2), (6, 8), (10, 8), (5.5, 14)]], False),
    ("twin", "twin", True),
    ("hollow", "hollow", True),
    ("key", "key", False),
    ("veil", [[(4, 3.5), (8, 7.5), (12, 3.5)], [(4, 9), (8, 13), (12, 9)]], True),
]


def rune(strokes):
    g = Glyph(16)
    if strokes == "moon":
        g.ring(9, 8, 5.2, RUNE_W)
        g.erase_disc(12.2, 6.8, 4.6)
    elif strokes == "twin":
        g.polyline([(4.5, 2.5), (4.5, 13.5), (11.5, 13.5), (11.5, 2.5)], RUNE_W)
        g.disc(8, 6.5, 1.6)
    elif strokes == "chain":
        g.ring(5.6, 8, 3.2, RUNE_W)
        g.ring(10.4, 8, 3.2, RUNE_W)
    elif strokes == "sun":
        g.ring(8, 8, 3.0, RUNE_W)
        for (a, b) in (((8, 1.5), (8, 3.6)), ((8, 12.4), (8, 14.5)), ((1.5, 8), (3.6, 8)), ((12.4, 8), (14.5, 8))):
            g.line(a, b, RUNE_W)
    elif strokes == "spirit":
        g.ring(8, 5, 2.8, RUNE_W)
        g.line((8, 7.8), (8, 13.5), RUNE_W)
        g.line((4.5, 13.5), (11.5, 13.5), RUNE_W)
    elif strokes == "hollow":
        g.ring(8, 8, 5.0, RUNE_W)
        g.line((8, 1.5), (8, 14.5), RUNE_W)
    elif strokes == "key":
        g.ring(8, 4.5, 2.6, RUNE_W)
        g.line((8, 7.1), (8, 14), RUNE_W)
        g.line((8, 10.5), (11.5, 10.5), RUNE_W)
        g.line((8, 13.5), (11, 13.5), RUNE_W)
    else:
        for stroke in strokes:
            g.polyline(stroke, RUNE_W)
    return g


# ------------------------------------------------------------------ footprints (16 x 16) and crown pieces

def footprint_boot():
    g = Glyph(16)
    g.d.ellipse((4.0 * 8, 1.0 * 8, 10.6 * 8, 9.6 * 8), fill=255)
    g.d.ellipse((5.0 * 8, 10.4 * 8, 10.2 * 8, 15.0 * 8), fill=255)
    return g


def footprint_bare():
    g = Glyph(16)
    g.d.ellipse((4.4 * 8, 6.0 * 8, 10.6 * 8, 15.2 * 8), fill=255)
    g.disc(5.6, 3.0, 1.8)
    g.d.ellipse((8.6 * 8, 1.6 * 8, 12.8 * 8, 4.8 * 8), fill=255)
    return g


def footprint_paw():
    g = Glyph(16)
    g.d.ellipse((4.6 * 8, 8.8 * 8, 11.4 * 8, 14.8 * 8), fill=255)
    for (x, y) in ((2.8, 7.0), (5.6, 3.4), (10.4, 3.4), (13.2, 7.0)):
        g.disc(x, y, 1.45)
    return g


def crown_band():
    g = Glyph(32, 16)
    g.polygon([(2, 15), (30, 15), (30, 11.5), (2, 11.5)])
    g.polygon([(2, 15), (30, 15), (30, 9), (2, 9)])
    for x, h in ((4.0, 5.5), (10.0, 3.5), (16.0, 2.5), (22.0, 3.5), (28.0, 5.5)):
        g.polygon([(x - 3.4, 9.5), (x + 3.4, 9.5), (x, h + 1.0)])
        g.disc(x, h, 1.6)
    g.erase_polygon([(16, 10.2), (17.6, 12), (16, 13.8), (14.4, 12)])
    return g


def soul_flame():
    g = Glyph(16)
    g.disc(8, 10.6, 4.2)
    g.polygon([(3.9, 9.8), (12.1, 9.8), (8, 0.4)])
    g.erase_disc(8, 11.4, 1.9)
    g.erase_polygon([(6.3, 10.8), (9.7, 10.8), (8, 6.4)])
    return g


def sparkle():
    g = Glyph(16)
    # a light sprite: no dark outline (see PIECES), the glow carries the twinkle
    g.polygon([(8, 0.4), (9.0, 7.0), (15.6, 8), (9.0, 9.0), (8, 15.6), (7.0, 9.0), (0.4, 8), (7.0, 7.0)])
    return g


def gem():
    g = Glyph(16)
    g.polygon([(5.0, 2.0), (11.0, 2.0), (14.5, 6.0), (8, 14.5), (1.5, 6.0)])
    g.erase_polygon([(3.5, 5.6), (12.5, 5.6), (12.5, 6.6), (3.5, 6.6)])
    return g


def halo_ring():
    g = Glyph(32, 16)
    g.d.ellipse((2 * 8, 4 * 8, 30 * 8, 12.5 * 8), fill=255)
    g.d.ellipse((4.6 * 8, 5.9 * 8, 27.4 * 8, 10.6 * 8), fill=0)
    return g


PIECES = [("footprint boot", footprint_boot, False), ("footprint bare", footprint_bare, False), ("footprint paw", footprint_paw, True),
          ("crown band", crown_band, True), ("soul flame", soul_flame, True), ("sparkle", sparkle, True, False), ("gem", gem, True),
          ("halo ring", halo_ring, True)]


def rune_sheet(runes, path, scale=4):
    """All runes in a grid (each tinted by a tier in turn, 4x and 1x), plus the alphabet as a line of text."""
    cols = 6
    cell = 16 * scale + 24
    rows = (len(runes) + cols - 1) // cols
    out = Image.new("RGB", (cols * (cell + 70) + 20, rows * (cell + 30) + 120), (30, 28, 36))
    d = ImageDraw.Draw(out)
    tints = list(TINTS.values())
    for i, (name, img) in enumerate(runes):
        x = 20 + (i % cols) * (cell + 70)
        y = 20 + (i // cols) * (cell + 30)
        big = tint(img, tints[i % 4]).resize((16 * scale, 16 * scale), Image.NEAREST)
        out.paste(big, (x, y), big)
        out.paste(img, (x + 16 * scale + 8, y + 16 * scale - 16), img)
        sym = asymmetry(img)
        d.text((x, y + 16 * scale + 4), name + (" (sym)" if sym == 0 else ""), fill=(220, 220, 230))
    y = 20 + rows * (cell + 30)
    d.text((20, y), "as a line of text, 1x and 2x:", fill=(180, 180, 190))
    for i, (_, img) in enumerate(runes):
        out.paste(img, (20 + i * 17, y + 20), img)
        big = img.resize((32, 32), Image.NEAREST)
        out.paste(big, (20 + i * 34, y + 44), big)
    out.save(path)
    return path


if __name__ == "__main__":
    which = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else "v1"
    if which == "runes":
        made = []
        for name, strokes, symmetric in RUNES:
            img = style(rune(strokes).pixels(mirror=symmetric))
            img.save(os.path.join(OUT, "rune_" + name + ".png"))
            made.append((name, img))
        print(rune_sheet(made, os.path.join(OUT, f"review-runes-{version}.png")))
    elif which == "pieces":
        made = []
        for name, make, symmetric, *flags in PIECES:
            img = style(make().pixels(mirror=symmetric), outline=flags[0] if flags else True)
            img.save(os.path.join(OUT, name.replace(" ", "_") + ".png"))
            made.append((name, img))
            if name.startswith("footprint") and not symmetric:
                right = img.transpose(Image.FLIP_LEFT_RIGHT)
                right.save(os.path.join(OUT, name.replace(" ", "_") + "_right.png"))
                made.append((name + " (right)", right))
        print(sheet(made, os.path.join(OUT, f"review-pieces-{version}.png"), scale=4))
