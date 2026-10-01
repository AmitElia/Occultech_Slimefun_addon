"""Glyph toolkit: crisp, symmetric line art (sigils, runes, footprints, crown pieces).

Shapes are drawn on a supersampled mask with exact geometry, reduced to crisp pixels by coverage, optionally mirrored
for exact symmetry, then styled in grayscale so the game can tint them (a font glyph's colours are multiplied by the
text colour): white core, soft edge, dark outline, faint glow.
"""
from PIL import Image, ImageDraw

SS = 8  # supersampling factor


class Glyph:
    def __init__(self, w, h=None):
        self.w, self.h = w, h or w
        self.mask = Image.new("L", (self.w * SS, self.h * SS), 0)
        self.d = ImageDraw.Draw(self.mask)

    def _p(self, x, y):
        return (x * SS, y * SS)

    # ------------------------------------------------------------------ drawing (coordinates in output pixels)

    def line(self, a, b, width):
        """A stroke with rounded ends."""
        w = width * SS
        self.d.line([self._p(*a), self._p(*b)], fill=255, width=round(w))
        for (x, y) in (a, b):
            r = w / 2
            self.d.ellipse((x * SS - r, y * SS - r, x * SS + r, y * SS + r), fill=255)

    def polyline(self, points, width, closed=False):
        pts = list(points) + ([points[0]] if closed else [])
        for a, b in zip(pts, pts[1:]):
            self.line(a, b, width)

    def ring(self, cx, cy, r, width):
        """A circle stroke, drawn on its own layer and merged (its hole never erases earlier strokes)."""
        from PIL import ImageChops
        layer = Image.new("L", self.mask.size, 0)
        ld = ImageDraw.Draw(layer)
        ro, ri = (r + width / 2) * SS, (r - width / 2) * SS
        ld.ellipse((cx * SS - ro, cy * SS - ro, cx * SS + ro, cy * SS + ro), fill=255)
        ld.ellipse((cx * SS - ri, cy * SS - ri, cx * SS + ri, cy * SS + ri), fill=0)
        self.mask = ImageChops.lighter(self.mask, layer)
        self.d = ImageDraw.Draw(self.mask)

    def disc(self, cx, cy, r):
        self.d.ellipse((cx * SS - r * SS, cy * SS - r * SS, cx * SS + r * SS, cy * SS + r * SS), fill=255)

    def polygon(self, points):
        self.d.polygon([self._p(*p) for p in points], fill=255)

    def erase_disc(self, cx, cy, r):
        ImageDraw.Draw(self.mask).ellipse((cx * SS - r * SS, cy * SS - r * SS, cx * SS + r * SS, cy * SS + r * SS), fill=0)

    # ------------------------------------------------------------------ to pixels

    def pixels(self, mirror=False, rot=None):
        """Coverage >= 50% becomes a pixel. mirror: copy the left half onto the right (exact symmetry)."""
        small = self.mask.resize((self.w, self.h), Image.BOX)
        bits = [[small.getpixel((x, y)) >= 128 for x in range(self.w)] for y in range(self.h)]
        if mirror:
            for y in range(self.h):
                for x in range(self.w // 2):
                    bits[y][self.w - 1 - x] = bits[y][x]
        return bits


def style(bits, glow=True, outline=True):
    """Grayscale styling (tintable): white core, grey inner edge, dark outline, faint glow."""
    h, w = len(bits), len(bits[0])
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    def on(x, y):
        return 0 <= x < w and 0 <= y < h and bits[y][x]

    for y in range(h):
        for x in range(w):
            if bits[y][x]:
                edge = not all(on(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                img.putpixel((x, y), (205, 205, 205, 255) if edge else (255, 255, 255, 255))
    if outline:
        for y in range(h):
            for x in range(w):
                if not bits[y][x] and any(on(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    img.putpixel((x, y), (36, 36, 44, 255))
    if glow:
        for y in range(h):
            for x in range(w):
                if img.getpixel((x, y))[3] == 0:
                    near = any(on(x + dx, y + dy) for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2) if abs(dx) + abs(dy) <= 3)
                    if near:
                        img.putpixel((x, y), (255, 255, 255, 46))
    return img


def tint(img, color):
    """What the game shows for a glyph drawn with text colour `color` (channels multiplied)."""
    out = Image.new("RGBA", img.size)
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = img.getpixel((x, y))
            out.putpixel((x, y), (r * color[0] // 255, g * color[1] // 255, b * color[2] // 255, a))
    return out


def asymmetry(img):
    """Pixels whose opacity differs from the vertical-axis mirror image (0 = exactly symmetric)."""
    w = img.width
    return sum(1 for y in range(img.height) for x in range(w // 2)
               if (img.getpixel((x, y))[3] > 0) != (img.getpixel((w - 1 - x, y))[3] > 0))
