"""Session C: tier-0 item icons (16 px). Tier 0 is humble stuff - chalk, bone, wax, iron, wood, ash - with an ember
accent; whatever is magical glows and moves (see docs/art/REFERENCES.md, the Occultech look).

Run: python tools/art/session_c.py c1 [version]     (c1 materials, c2 drops/components, c3 gear)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from palettes import RAMPS  # noqa: E402
from pixelkit import Icon, Part, _norm  # noqa: E402
import review  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "art", "session-c")
os.makedirs(OUT, exist_ok=True)


def cut(part, keep):
    """The pixels of a part for which keep(x, y) is true."""
    return Part({p: n for p, n in part.normals.items() if keep(*p)})


def put(icon, pts, color, alpha=255):
    for (x, y) in pts:
        if 0 <= x < icon.w and 0 <= y < icon.h:
            icon.img.putpixel((x, y), color[:3] + (alpha,))


def flat_face(icon, points, normal):
    return icon.facet(points, normal)


# ================================================================== C1: materials

def grave_salt(frame=0):
    """A wooden scoop heaped with coarse grave salt; a few grains fall from it."""
    icon = Icon(16)
    wood, salt = RAMPS["wood"], RAMPS["chalk"]
    handle = icon.capsule((11.0, 9.5), (14.6, 5.4), 1.25)
    icon.paint(handle, wood, bias=0.05)
    bowl = cut(icon.sphere(7.0, 9.2, 5.6, squash=0.95), lambda x, y: y >= 9)
    heap = cut(icon.sphere(7.0, 9.6, 4.9, squash=0.72), lambda x, y: y < 10)
    icon.paint(bowl, wood, bias=0.0, outline_over=False)
    icon.paint(heap, salt, bias=0.12, outline_ramp=RAMPS["chalk"], outline_over=False)
    # coarse crystals: hard little facets on the heap (light top-left faces, shadowed lower-right)
    put(icon, [(4, 7), (7, 6), (9, 7), (6, 8)], salt[5])
    put(icon, [(5, 8), (8, 7), (10, 8), (7, 9)], salt[2])
    # the rim of the scoop, catching the light
    put(icon, [(x, 10) for x in range(2, 12)], wood[4])
    put(icon, [(x, 10) for x in range(8, 12)], wood[3])
    # grains falling off the front
    put(icon, [(2, 12), (1, 14)], salt[4])
    put(icon, [(3, 14)], salt[3])
    return icon


def soul_ash(frame=0):
    """A mound of grey ash with embers breathing inside it and a curl of smoke. Animated: the embers pulse in turn and
    the smoke drifts."""
    icon = Icon(16)
    ash, em, ch = RAMPS["ash"], RAMPS["ember"], RAMPS["chalk"]
    mound = cut(icon.sphere(8.0, 14.6, 7.2, squash=0.95), lambda x, y: y <= 14)
    icon.paint(mound, ash + [ch[2]], bias=0.16, outline_ramp=[ash[0], ash[1]])
    put(icon, [(x, 15) for x in range(1, 15)], ash[0])
    # cracks in the crust where the embers show
    put(icon, [(3, 11), (4, 11), (10, 12), (9, 11)], ash[0])
    embers = [(4, 12), (5, 12), (5, 13), (10, 13), (11, 13), (8, 14), (12, 14)]
    for i, p in enumerate(embers):
        hot = (i + frame) % 4
        put(icon, [p], em[5] if hot == 0 else em[4] if hot == 1 else em[3] if hot == 2 else em[2])
    # a thick curl of pale smoke, puffing out at the top; it drifts sideways a step each frame
    sway = [0, 1, 1, 0][frame % 4]
    curl = [(8, 7), (8, 6), (7, 5), (7, 4), (8, 3), (9, 2)]
    for i, (x, y) in enumerate(curl):
        dx = sway if i >= 3 else 0
        put(icon, [(x + dx, y), (x + dx + 1, y)], ch[3], 230 - i * 22)
    put(icon, [(9 + sway, 1), (10 + sway, 1), (10 + sway, 2), (11 + sway, 1)], ch[4], 150)
    return icon


def occult_ink(frame=0):
    """A squat inkwell: smoky glass shows only at its lit edges, the ink inside is near black with a violet sheen."""
    icon = Icon(16)
    glass, ink = RAMPS["glass"], RAMPS["ink"]
    body = icon.box(2.6, 7.6, 13.4, 14.6, bevel=1.8)
    icon.paint(body, ink, bias=-0.12, spec=False, outline_ramp=[glass[0], glass[1]])
    shoulder = icon.polygon([(3.0, 8.0), (13.0, 8.0), (10.6, 5.6), (5.4, 5.6)], bevel=1.0)
    icon.paint(shoulder, glass, bias=-0.15, outline_ramp=[glass[0], glass[1]], outline_over=False)
    neck = icon.box(5.8, 3.4, 10.2, 5.8, bevel=1.0)
    icon.paint(neck, glass, bias=-0.1, outline_ramp=[glass[0], glass[1]], outline_over=False)
    lip = icon.box(5.0, 2.4, 11.0, 3.8, bevel=0.8)
    icon.paint(lip, RAMPS["iron"], bias=0.1, outline_over=False)
    put(icon, [(6, 3), (7, 3)], RAMPS["iron"][5])
    # the glass: a bright rim along the lit edges, a glint, a pale line where the ink meets the shoulder
    put(icon, [(3, 9), (3, 10), (3, 11), (3, 12)], glass[4])
    put(icon, [(4, 9), (4, 10)], glass[5])
    put(icon, [(x, 8) for x in range(4, 12)], glass[3])
    # the ink's violet sheen and a drip running from the lip down the side
    put(icon, [(10, 12), (11, 11), (9, 13)], ink[4])
    put(icon, [(11, 4), (12, 5), (12, 6), (12, 7)], ink[3])
    put(icon, [(12, 8)], ink[5])
    return icon


def warded_silver(frame=0):
    """A silver ingot seen from three quarters (top, left and right faces), a ward rune inlaid in its top that glows
    ember. Animated: the inlay breathes."""
    icon = Icon(16)
    ir, em = RAMPS["iron"], RAMPS["ember"]
    # a long bar lying diagonally, seen from above-front: top face, left (long) face, right (short end) face
    a, b, c, d = (1.4, 9.4), (10.0, 3.6), (13.8, 5.8), (5.2, 11.6)
    h = 3.0
    top = flat_face(icon, [a, b, c, d], (0, -0.8, 0.6))
    left = flat_face(icon, [a, d, (d[0], d[1] + h), (a[0], a[1] + h)], (-0.4, 0.5, 0.75))
    right = flat_face(icon, [d, c, (c[0], c[1] + h), (d[0], d[1] + h)], (0.6, 0.4, 0.7))
    icon.paint(left, ir, outline=False, flat=3)
    icon.paint(right - left, ir, outline=False, flat=2)
    icon.paint(top, ir, outline=False, flat=4)
    icon.outline(top | left | right, ir)
    # hard edges: the long lit edge of the top bright, the front ridge crisp
    put(icon, [(2, 9), (3, 8), (4, 7), (5, 7), (6, 6), (7, 5), (8, 5), (9, 4)], ir[5])
    put(icon, [(5, 12), (5, 13), (5, 14)], ir[4])
    put(icon, [(6, 11), (7, 10), (8, 10), (9, 9), (10, 8), (11, 8), (12, 7), (13, 6)], ir[3])
    # the inlaid ward rune (a small diamond with a hot core), glowing
    core = [em[5], em[5], em[4], em[4]][frame % 4]
    ring = [em[3], em[4], em[3], em[2]][frame % 4]
    # the ward: a groove glowing along the bar, crossed in the middle
    put(icon, [(4, 8), (5, 8), (6, 7), (8, 6), (9, 6), (10, 5)], ring)
    put(icon, [(6, 6), (8, 8)], ring)
    put(icon, [(7, 7)], core)
    return icon


def binding_thread(frame=0):
    """A wooden spool wound with red binding thread (the occult red string); the loose end trails off to a knot."""
    icon = Icon(16)
    wood, red = RAMPS["wood"], RAMPS["crimson"]
    core = icon.box(4.6, 3.8, 11.4, 12.2, bevel=2.6)
    icon.paint(core, red, bias=0.1)
    for y in range(5, 12, 2):   # the winding: every other row a shade darker
        put(icon, [(x, y) for x in range(5, 11) if icon.img.getpixel((x, y))[3]], red[2])
    put(icon, [(5, 4), (6, 5), (5, 6)], red[5])
    top = icon.sphere(8.0, 3.0, 6.6, squash=0.34)
    bottom = icon.sphere(8.0, 13.0, 6.6, squash=0.34)
    icon.paint(bottom, wood, bias=-0.05, outline_over=False)
    icon.paint(top, wood, bias=0.12, outline_over=False)
    put(icon, [(7, 3), (8, 3)], wood[0])   # the spool's hole
    # the loose end, trailing down and out to a knot
    put(icon, [(11, 9), (12, 10), (13, 11), (13, 12), (14, 13)], red[3])
    put(icon, [(14, 14), (15, 14), (14, 15)], red[4])
    put(icon, [(15, 15)], red[2])
    return icon


def tallow_candle(frame=0):
    """A stubby tallow candle, wax run down its sides, a flame that sways (3 frames)."""
    icon = Icon(16)
    wax, em = RAMPS["wax"], RAMPS["ember"]
    body = icon.box(4.6, 7.0, 11.4, 15.0, bevel=2.0)
    wax = RAMPS["bone"]  # tallow is creamy, not orange - the flame is the only accent
    icon.paint(body, wax, bias=0.05)
    # the melted rim and drips running down (lighter wax)
    put(icon, [(x, 7) for x in range(5, 11)], wax[5])
    put(icon, [(5, 8), (5, 9), (5, 10), (9, 8), (9, 9), (10, 8)], wax[4])
    put(icon, [(5, 11), (9, 10)], wax[5])
    # wick
    put(icon, [(8, 6), (8, 5)], RAMPS["ash"][0])
    # flame: a teardrop whose tip sways
    sway = [0, 1, 0, -1][frame % 4]
    flame = icon.sphere(8.0, 4.0, 1.7) | icon.polygon([(6.6, 3.8), (9.4, 3.8), (8.0 + sway, 0.2)], bevel=0.3)
    for (x, y) in flame.keys():
        d = math.hypot(x + 0.5 - 8.0, (y + 0.5 - 4.2) * 0.8)
        put(icon, [(x, y)], em[5] if d < 0.9 else em[4] if d < 1.6 else em[3])
    icon.glow(em[3], radius=1.5, strength=0.28)
    return icon


C1 = [("Grave Salt", grave_salt, 1), ("Soul Ash", soul_ash, 4), ("Occult Ink", occult_ink, 1),
      ("Warded Silver", warded_silver, 4), ("Binding Thread", binding_thread, 1), ("Tallow Candle", tallow_candle, 4)]


# ================================================================== C2: boss drops and components

def brood_silk(frame=0):
    """A spindle-shaped silk cocoon hanging from its strand, criss-crossed with wraps, web strands to its sides."""
    icon = Icon(16)
    silk = RAMPS["bone"]   # creamy, so it stands out on the grey slot
    cocoon = icon.capsule((8.0, 5.4), (8.0, 12.2), 3.7)
    icon.paint(cocoon, silk, bias=0.1, outline_ramp=[silk[0], silk[1]])
    # wraps: two diagonal families crossing (wound silk), darker on the shadow side
    for (x, y) in cocoon.keys():
        if (x + y) % 4 == 0 or ((x - y) % 5 == 0 and y > 7):
            put(icon, [(x, y)], silk[1] if x >= 8 else silk[2])
    put(icon, [(6, 4), (6, 5)], silk[5])
    # the strand above, web threads out to the sides
    put(icon, [(8, 0), (8, 1)], silk[4])
    put(icon, [(4, 8), (3, 7), (2, 6), (1, 5)], silk[3], 210)
    put(icon, [(12, 10), (13, 11), (14, 12), (15, 13)], silk[3], 210)
    put(icon, [(4, 13), (3, 14)], silk[3], 160)
    return icon


def fletchers_quill(frame=0):
    """A long barred quill (a hawk's flight feather) with an ember-dyed tip, its nib cut to a sharp iron point."""
    icon = Icon(16)
    bone, ash, ir, em = RAMPS["bone"], RAMPS["ash"], RAMPS["iron"], RAMPS["ember"]
    vane = icon.polygon([(3.6, 12.4), (5.0, 8.2), (8.6, 4.2), (13.4, 1.0), (15.0, 1.4), (12.2, 5.8), (8.4, 10.0)], bevel=1.2)
    icon.paint(vane, bone, bias=0.0)
    ax, ay, bx, by = 3.6, 12.4, 14.6, 1.2
    for (x, y) in vane.keys():
        t = ((x + 0.5 - ax) * (bx - ax) + (y + 0.5 - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)
        if t > 0.82:
            put(icon, [(x, y)], em[3] if (x + y) % 2 else em[4])        # the dyed tip
        elif int(t * 9) % 2 == 1:
            put(icon, [(x, y)], ash[3] if x + y < 16 else ash[2])       # dark bars
    put(icon, [(4, 12), (5, 11), (6, 10), (7, 9), (8, 8), (9, 7), (10, 6), (11, 5), (12, 4), (13, 3)], bone[5])
    put(icon, [(3, 13), (2, 14)], ir[4])
    put(icon, [(1, 15)], ir[5])
    put(icon, [(2, 13)], ir[2])
    return icon


def coven_brew_base(frame=0):
    """A little three-legged iron cauldron of sickly, glowing witch brew with a swirl in it; bubbles rise and pop and a
    wisp of vapour curls up (4 frames)."""
    icon = Icon(16)
    ir, br = RAMPS["iron"], RAMPS["brew"]
    for (x0, x1) in ((3.0, 4.8), (11.2, 13.0)):
        icon.paint(icon.box(x0, 12.6, x1, 15.6, bevel=0.6), ir, bias=0.0)
    pot = cut(icon.sphere(8.0, 8.4, 6.4, squash=0.98), lambda x, y: y >= 8)
    icon.paint(pot, ir, bias=0.05, outline_over=False)
    rim = icon.sphere(8.0, 8.0, 6.6, squash=0.32)
    icon.paint(rim, ir, bias=0.3, outline_over=False)
    brew = icon.sphere(8.0, 8.0, 5.0, squash=0.24)
    for p in brew.keys():
        put(icon, [p], br[3])
    swirl = [[(5, 8), (6, 8), (9, 7)], [(6, 8), (7, 8), (10, 8)], [(7, 8), (8, 8), (5, 7)], [(9, 8), (10, 8), (6, 7)]][frame % 4]
    put(icon, swirl, br[5])
    put(icon, [(x, 9) for x in range(3, 13)], ir[2])        # the inner lip throws a shadow on the pot
    for (x, start) in ((6, 0), (10, 2)):
        stage = (frame + start) % 4
        y = 6 - stage
        if stage < 3:
            put(icon, [(x, y)], br[4] if stage else br[5])
        else:
            put(icon, [(x - 1, y), (x + 1, y)], br[4], 150)
    vapour = [(8, 5), (8, 4), (9, 3), (9, 2), (8, 1)]
    for i, (x, y) in enumerate(vapour):
        put(icon, [(x + (1 if (i + frame) % 4 == 0 else 0), y)], br[4], 170 - i * 28)
    return icon


def sovereign_gel(frame=0):
    """A drop of royal slime resting on the ground, peaked on top like a fresh drip: glossy (a crisp white highlight),
    clear (reflected light in its lower edge, little bubbles suspended inside). Animated: it wobbles."""
    icon = Icon(16)
    gel, gold = RAMPS["gel"], RAMPS["gold"]
    sq = [0.8, 0.72, 0.8, 0.88][frame % 4]
    r = [6.0, 6.4, 6.0, 5.7][frame % 4]
    cy = 15.0 - r * sq
    top = round(cy - r * sq)
    body = cut(icon.sphere(8.0, cy, r, squash=sq), lambda x, y: y <= 14)
    peak = icon.polygon([(5.6, top + 1.6), (10.4, top + 1.6), (8.4 + [0, 1, 0, -1][frame % 4], top - 2.4)], bevel=1.0)
    blob = body | peak
    icon.paint(blob, gel, bias=0.0, outline_ramp=[gel[0], gel[1]])
    # reflected light: a bright crescent inside the lower right edge
    for (x, y) in blob.keys():
        if (x + 1, y + 1) not in blob.normals and y > cy and x > 7:
            put(icon, [(x, y)], gel[4])
    # bubbles suspended in the gel, and a fleck of gold
    put(icon, [(10, round(cy) - 1), (11, round(cy) + 1)], gel[5])
    put(icon, [(10, round(cy)), (11, round(cy) + 2)], gel[2])
    put(icon, [(7, round(cy) + 3)], gold[4])
    # the glossy highlight: a crisp white streak on the lit shoulder
    put(icon, [(4, top + 3), (5, top + 2), (5, top + 3)], gel[5])
    put(icon, [(4, top + 4)], gel[4])
    return icon


def sovereigns_catalyst(frame=0):
    """A cube of royal gel with a gold crown suspended in it. Animated: a glint slides down the cube, a twinkle."""
    icon = Icon(16)
    gel, gold = RAMPS["gel"], RAMPS["gold"]
    top = flat_face(icon, [(8, 1.2), (14.6, 4.6), (8, 8.0), (1.4, 4.6)], (0, -0.9, 0.5))
    left = flat_face(icon, [(1.4, 4.6), (8, 8.0), (8, 15.4), (1.4, 12.0)], (-0.6, 0.3, 0.7))
    right = flat_face(icon, [(8, 8.0), (14.6, 4.6), (14.6, 12.0), (8, 15.4)], (0.6, 0.3, 0.7))
    icon.paint(left, gel, outline=False, flat=3)
    icon.paint(right - left, gel, outline=False, flat=2)
    icon.paint(top - left - right, gel, outline=False, flat=4)
    icon.outline(top | left | right, [gel[0], gel[1]])
    put(icon, [(8, y) for y in range(8, 15)], gel[4])
    put(icon, [(2, 5), (3, 5), (4, 6), (5, 6), (6, 7), (7, 7)], gel[5])
    # the crown inside: three points, a band, a crimson stone (seen through the gel, so slightly muted)
    crown = {8: "#..#..#", 9: "##.#.##", 10: "#######", 11: "#######"}
    for y, row in crown.items():
        for i, c in enumerate(row):
            if c == "#":
                put(icon, [(5 + i, y)], gold[4] if y < 10 else gold[3] if y == 10 else gold[2])
    put(icon, [(8, 10)], RAMPS["crimson"][4])
    put(icon, [(5, 7), (8, 7), (11, 7)], gold[5])     # ball tips
    g = [(3, 7), (3, 8), (4, 10), (5, 12)][frame % 4]
    put(icon, [g, (g[0], g[1] + 1)], gel[5])
    icon.twinkle(13, 2, [3, 2, 1, 0][frame % 4], gold)
    return icon


def initiates_sigil(frame=0):
    """The tier-0 core component: a diamond-shaped plaque of carved bone (its silhouette alone sets it apart from the
    round Warding Charm), the Initiate sigil cut into it and glowing ember. Animated: the glow pulses, a twinkle."""
    icon = Icon(16)
    bone, em = RAMPS["bone"], RAMPS["ember"]
    plaque = icon.polygon([(8, 0.6), (15.4, 8.0), (8, 15.4), (0.6, 8.0)], bevel=2.2)
    icon.paint(plaque, bone, bias=-0.05)
    pulse = frame % 4 in (1, 2)
    inner = [(8, 3), (9, 4), (10, 5), (11, 6), (12, 7), (13, 8), (12, 9), (11, 10), (10, 11), (9, 12), (8, 13),
             (7, 12), (6, 11), (5, 10), (4, 9), (3, 8), (4, 7), (5, 6), (6, 5), (7, 4)]
    put(icon, inner, em[4] if pulse else em[3])
    # the cut's lower lip catches the light (it is carved into the bone)
    put(icon, [(9, 13), (10, 12), (11, 11), (12, 10), (13, 9)], bone[5])
    heart = icon.sphere(8.0, 8.0, 1.9)
    icon.paint(heart, em, bias=0.35 if pulse else 0.15, outline_ramp=[bone[0], bone[1]])
    put(icon, [(8, 5), (11, 8), (8, 11), (5, 8)], em[2])
    icon.twinkle(13, 2, [0, 1, 3, 1][frame % 4], em)
    return icon


C2 = [("Brood Silk", brood_silk, 1), ("Fletcher's Quill", fletchers_quill, 1), ("Coven Brew Base", coven_brew_base, 4),
      ("Sovereign Gel", sovereign_gel, 4), ("Sovereign's Catalyst", sovereigns_catalyst, 4),
      ("Initiate's Sigil", initiates_sigil, 4)]


# ================================================================== C3: gear and utility

def line_px(a, b):
    """Pixels of a 1 px line from a to b (Bresenham)."""
    (x0, y0), (x1, y1) = (round(a[0]), round(a[1])), (round(b[0]), round(b[1]))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err, out = dx + dy, []
    while True:
        out.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return out
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


class BookFrame:
    """A closed book lying flat, seen from above-front like the vanilla book icon: the cover is a tilted
    parallelogram, the page block shows along the front edge, the spine along the left. cover(u, v) maps cover
    coordinates (0..1, u along the front edge, v from the spine-top toward the front) to the screen."""

    def __init__(self, tl=(0.8, 4.8), tr=(12.0, 1.2), bl=(3.6, 10.6), thick=3.2):
        self.tl, self.tr, self.bl = tl, tr, bl
        self.br = (tr[0] + bl[0] - tl[0], tr[1] + bl[1] - tl[1])
        self.thick = thick
        ux, uy = tr[0] - tl[0], tr[1] - tl[1]
        vx, vy = bl[0] - tl[0], bl[1] - tl[1]
        self.det = ux * vy - uy * vx
        self.u, self.v = (ux, uy), (vx, vy)

    def cover(self, u, v):
        return (self.tl[0] + u * self.u[0] + v * self.v[0], self.tl[1] + u * self.u[1] + v * self.v[1])

    def uv(self, x, y):
        """Cover coordinates of a pixel centre."""
        dx, dy = x + 0.5 - self.tl[0], y + 0.5 - self.tl[1]
        return ((dx * self.v[1] - dy * self.v[0]) / self.det, (self.u[0] * dy - self.u[1] * dx) / self.det)

    def down(self, p, d):
        return (p[0], p[1] + d)


def occult_codex(frame=0):
    """The Occult Codex as a spellbook in the vanilla book's pose (lying flat, cover tilted, pages along the front),
    built the way Iron's Spells' spellbooks are: thick leather covers overhanging the page block, iron corner guards,
    a raised ember emblem with a gem at its heart, a strap and clasp over the page edge. Animated: the emblem pulses,
    a twinkle comes and goes."""
    icon = Icon(16)
    lea, bone, ir, em = RAMPS["leather"], RAMPS["bone"], RAMPS["iron"], RAMPS["ember"]
    b = BookFrame()
    t = b.thick
    # the back cover's edge, then the page block (inset: the covers overhang it), then the spine
    back = icon.facet([b.down(b.bl, t - 1.0), b.down(b.br, t - 1.0), b.down(b.br, t), b.down(b.bl, t)], (0, 0.8, 0.6))
    icon.paint(back, lea, outline=False, flat=1)
    p0, p1 = b.cover(0.05, 1.0), b.cover(0.97, 1.0)
    pages = icon.facet([p0, p1, b.down(p1, t - 1.0), b.down(p0, t - 1.0)], (0.1, 0.9, 0.45))
    icon.paint(pages, bone, outline=False, flat=4)
    p2, p3 = b.down(p0, t * 0.55), b.down(p1, t * 0.55)   # one page line along the block
    put(icon, [p for p in line_px(p2, p3) if p in pages.normals], bone[3])
    put(icon, [p for p in line_px(b.down(p0, 0.6), b.down(p1, 0.6)) if p in pages.normals], bone[5])
    spine = icon.facet([b.tl, b.bl, b.down(b.bl, t), b.down(b.tl, t)], (-0.9, 0.3, 0.4))
    icon.paint(spine, lea, outline=False, flat=2)
    cover = icon.polygon([b.tl, b.tr, b.br, b.bl], bevel=1.3)
    icon.paint(cover, lea, bias=-0.06, outline=False)
    icon.outline(cover | spine | pages | back, lea)
    # spine bands
    for v in (0.25, 0.55, 0.85):
        x, y = b.cover(0.0, v)
        put(icon, [(round(x - 0.6), round(y + 1.0)), (round(x - 0.6), round(y + 2.0))], lea[4])
    # iron corner guards: the cover's corners in cover space
    for (x, y) in cover.keys():
        u, v = b.uv(x, y)
        cu, cv = min(u, 1 - u), min(v, 1 - v)
        if cu + cv < 0.17:
            put(icon, [(x, y)], ir[4] if u < 0.5 and v < 0.5 else ir[3] if u < 0.5 or v < 0.5 else ir[2])
    # the emblem: a raised ring with a gem at its heart, marks at the four points
    pulse = frame % 4 in (1, 2)
    for (x, y) in cover.keys():
        u, v = b.uv(x, y)
        d = ((u - 0.5) ** 2 + ((v - 0.5) * 0.85) ** 2) ** 0.5
        if 0.12 <= d < 0.21:   # the iron bezel
            put(icon, [(x, y)], ir[4] if v < 0.5 else ir[2])
        elif d < 0.12:        # the jewel
            put(icon, [(x, y)], em[4] if pulse else em[3])
    gx, gy = b.cover(0.47, 0.47)
    put(icon, [(math.floor(gx), math.floor(gy))], em[5])
    # a strap and clasp over the page edge, near the front right
    for (x, y) in list(cover.keys()) + list(pages.keys()):
        u, v = b.uv(x, y)
        if 0.74 <= u <= 0.84 and v >= 0.78:
            put(icon, [(x, y)], lea[2] if (x, y) in pages.normals else lea[3])
    cx, cy = b.cover(0.79, 1.0)
    put(icon, [(round(cx), round(cy) + 1), (round(cx), round(cy) + 2)], ir[5])
    put(icon, [(round(cx) + 1, round(cy) + 1)], ir[3])
    icon.twinkle(4, 1, [0, 1, 2, 1][frame % 4], em)
    return icon


def warding_charm(frame=0):
    """An amulet on a beaded cord: a silver disc with a warding eye that glows ember and, now and then, blinks."""
    icon = Icon(16)
    tw, bone, ir, em = RAMPS["twine"], RAMPS["bone"], RAMPS["iron"], RAMPS["ember"]
    put(icon, line_px((4, 1), (7, 5)) + line_px((11, 1), (8, 5)), tw[3])
    put(icon, [(x, 0) for x in range(5, 11)], tw[3])
    put(icon, [(4, 1), (11, 1)], tw[2])
    for (x, y) in ((5, 3), (10, 3)):
        icon.paint(icon.sphere(x + 0.5, y + 0.5, 1.1), bone, bias=0.15, outline=False)
    disc = icon.sphere(8.0, 10.2, 5.2)
    icon.paint(disc, ir, bias=0.1)
    face = icon.sphere(8.0, 10.2, 3.9)
    face = Part({p: _norm((n[0] * 0.3, n[1] * 0.3, n[2])) for p, n in face.normals.items()})
    icon.paint(face, ir, outline=False, bias=-0.2)
    put(icon, [(7, 5), (8, 5)], ir[4])   # the bail
    blink = frame % 4 == 3
    if blink:   # the lids closed: one glowing line
        put(icon, [(5, 10), (6, 10), (7, 10), (8, 10), (9, 10), (10, 10)], em[3])
    else:       # an almond of glowing lids round a dark eye with a bright iris
        put(icon, [(4, 10), (11, 10), (5, 9), (6, 8), (7, 8), (8, 8), (9, 8), (10, 9),
                   (5, 11), (6, 12), (7, 12), (8, 12), (9, 12), (10, 11)], em[3])
        put(icon, [(6, 9), (7, 9), (8, 9), (9, 9), (6, 11), (7, 11), (8, 11), (9, 11), (5, 10), (6, 10), (9, 10), (10, 10)], em[2])
        put(icon, [(7, 9), (8, 9), (7, 11), (8, 11)], em[5] if frame % 4 == 1 else em[4])
        put(icon, [(7, 10), (8, 10)], RAMPS["ash"][0])   # the pupil
    return icon


def quillshot_bow(state=0):
    """The Quillshot Bow in its four textures (standby, pulling 0-2), laid out like the vanilla bow so it sits right in
    the hand: dark wood limbs with silver recurve tips, a leather grip set with an ember, and at full draw three
    arrows fanned - it fires a burst."""
    icon = Icon(16)
    wood, ir, lea, em, ch = RAMPS["wood"], RAMPS["iron"], RAMPS["leather"], RAMPS["ember"], RAMPS["chalk"]
    a, c, b = (14.4, 1.4), (0.8, 0.8), (1.4, 14.4)
    pts = [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0],
            (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]) for t in [i / 16 for i in range(17)]]
    limb = icon.tubes(list(zip(pts, pts[1:])), 1.15)
    icon.paint(limb, wood, bias=-0.08)
    for (x, y) in limb.keys():   # silver caps on both tips
        if x + y >= 14 and (x >= 12 or y >= 12):
            put(icon, [(x, y)], ir[4] if (x < 14 and y < 2) or (x < 2 and y < 14) else ir[3])
    put(icon, [(15, 2), (2, 15)], ir[5])   # the recurve flick
    put(icon, [(3, 4), (4, 3), (3, 5), (5, 3)], lea[3])   # grip wrap
    put(icon, [(4, 4)], em[5])
    pull = [0.0, 2.6, 4.2, 5.6][state]
    apex = (7.6 + pull, 7.6 + pull)
    string = line_px((14, 2), apex) + line_px(apex, (2, 14)) if pull else line_px((14, 2), (2, 14))
    put(icon, [p for p in string if p not in limb.normals], ch[3], 220)
    if state:
        arrows = [0.0] if state < 3 else [-0.32, 0.32, 0.0]
        for k, ang in enumerate(arrows):
            ca, sa = math.cos(ang), math.sin(ang)
            dx, dy = -0.7071 * ca + 0.7071 * sa, -0.7071 * ca - 0.7071 * sa
            tail = apex
            length = 9.6 + pull * 0.4
            if ang:   # the burst: two shorter arrows nocked beside the main one, parallel to it
                side = 1 if ang > 0 else -1
                ox, oy = side * 0.7071 * 2.2, -side * 0.7071 * 2.2
                start = (tail[0] + ox - 0.7071 * 2.0, tail[1] + oy - 0.7071 * 2.0)
                tip = (tail[0] + ox - 0.7071 * length * 0.78, tail[1] + oy - 0.7071 * length * 0.78)
                shaft = line_px(start, tip)
                put(icon, shaft[:-1], wood[2])
                put(icon, shaft[-1:], ir[5])
                put(icon, shaft[:1], em[3])
                continue
            head = (tail[0] + dx * length, tail[1] + dy * length)
            shaft = line_px(tail, head)
            put(icon, shaft[1:-2], wood[4])
            put(icon, shaft[-2:], ir[5])
            put(icon, shaft[1:3], em[3])   # ember-barred fletching
    return icon


C3 = [("Occult Codex", occult_codex, 4), ("Warding Charm", warding_charm, 4)]
BOW_STATES = ["standby", "pulling_0", "pulling_1", "pulling_2"]
# ================================================================== C4: Banishing Salt (Session P2)

def banishing_salt(frame=0):
    """A little leather pouch, its mouth tied with twine and spilling white salt; a pale warding rune glints in the salt
    and motes of it drift up and fade (4 frames)."""
    icon = Icon(16)
    lea, tw, salt, sp = RAMPS["leather"], RAMPS["twine"], RAMPS["chalk"], RAMPS["spirit"]
    pouch = icon.sphere(7.6, 10.4, 4.9, squash=0.92) | icon.polygon([(5.0, 6.6), (10.2, 6.6), (11.4, 8.8), (3.8, 8.8)], bevel=0.8)
    icon.paint(pouch, lea, bias=0.05)
    # the gathered neck and its twine tie
    neck = icon.box(5.6, 4.6, 9.6, 6.8, bevel=0.6)
    icon.paint(neck, lea, bias=0.15)
    put(icon, [(x, 6) for x in range(5, 10)], tw[3])
    put(icon, [(10, 7), (11, 8), (11, 9)], tw[2])
    # salt heaped in the open mouth, spilling over the lip to the right
    heap = cut(icon.sphere(7.6, 4.6, 2.6, squash=0.7), lambda x, y: y <= 4)
    icon.paint(heap, salt, bias=0.2, outline_ramp=[salt[1], salt[2]], outline_over=False)
    put(icon, [(10, 4), (11, 5)], salt[4])
    put(icon, [(12, 7)], salt[3])
    # a ward rune stitched on the pouch, pulsing pale
    rune = [(7, 9), (7, 10), (7, 11), (7, 12), (6, 10), (8, 10), (6, 12), (8, 12)]
    pulse = [5, 4, 3, 4][frame % 4]
    put(icon, rune, sp[pulse])
    # motes rising from the salt and fading
    for i, (x, y) in enumerate([(6, 2), (9, 1), (8, 3)]):
        rise = (frame + i) % 4
        put(icon, [(x + (rise % 2), y - rise // 2)], sp[5], 230 - rise * 55)
    return icon


C4 = [("Banishing Salt", banishing_salt, 4)]

GROUPS = {"c1": C1, "c2": C2, "c3": C3, "c4": C4}


def slug(name):
    return name.lower().replace("'", "").replace(" ", "_")


def tier0_set():
    """Every tier-0 icon (Session A's Ritual Chalk included), first frame, in recipe-book order."""
    from PIL import Image
    chalk = Image.open(os.path.join(OUT, "..", "session-a", "ritual_chalk.png")).convert("RGBA")
    icons = [("Ritual Chalk", chalk)]
    for group in (C1, C2, C3):
        icons += [(name, make(0).img) for name, make, _ in group]
    icons.append(("Quillshot Bow", quillshot_bow(0).img))
    return icons


if __name__ == "__main__" and sys.argv[1:2] == ["set"]:
    icons = tier0_set()
    print(review.inventory(icons, os.path.join(OUT, "review-tier0-inventory.png")))
    print(review.inventory(icons, os.path.join(OUT, "review-tier0-inventory-1x.png"), scale=2))
    anim = [(name, make, n) for group in (C1, C2, C3) for name, make, n in group if n > 1]
    review.gif([[make(f).img for f in range(n)] for _, make, n in anim], os.path.join(OUT, "preview-tier0-animated.gif"), ms=160, scale=6)
    review.gif([[quillshot_bow(i).img for i in range(4)]], os.path.join(OUT, "preview-quillshot-draw.gif"), ms=260)
    sys.exit()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "c1"
    version = sys.argv[2] if len(sys.argv) > 2 else "final"
    suffix = "" if version == "final" else "-" + version
    statics, animated = [], []
    for name, make, frames in GROUPS[which]:
        icons = [make(f) for f in range(frames)]
        if frames == 1:
            icons[0].save(os.path.join(OUT, slug(name) + ".png"))
        else:
            for f, icon in enumerate(icons):
                icon.save(os.path.join(OUT, f"{slug(name)}_{f}.png"))
            animated.append((name, [i.img for i in icons]))
        statics.append((name, icons[0].img))
    if which == "c3":   # the bow: four states, shown as separate rows and as a draw sequence
        bows = [quillshot_bow(i) for i in range(4)]
        for state, icon in zip(BOW_STATES, bows):
            icon.save(os.path.join(OUT, f"quillshot_bow_{state}.png"))
            statics.append((f"Quillshot Bow ({state})", icon.img))
        animated.append(("Quillshot Bow (draw)", [i.img for i in bows]))
    print(review.sheet(statics, os.path.join(OUT, f"review-{which}{suffix}.png")))
    if animated:
        from session_b import frame_sheet
        print(frame_sheet(animated, os.path.join(OUT, f"review-{which}-anim{suffix}.png")))
