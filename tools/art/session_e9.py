"""Session E9: the Staff Raid's art.

- S4MURAI's katana (`s4murai_katana`, boss-only, held): a long, slightly curved blade of black steel with a dark
  crimson hamon, its cutting edge a crimson glow with a glint sweeping along it (animated); a crimson habaki, a black
  octagonal tsuba rimmed in crimson, a crimson-on-black diamond-wrapped grip and a black kashira. Built upright and laid
  on a sword's diagonal with vanilla's handheld transforms, like the Frenzy Cleaver.
- Two floor symbols in Session O4's style (light greys, tinted by the game): `floor_mark_soak` (three figures gathered
  - stand in it together) and `floor_mark_target` (a reticle - you're marked).
- `raid_wall`: an energy pane for walls and sweeping barriers - a see-through, glowing field of rising hexagonal cells
  between two bright rails, drawn in greys so each wall takes its own tint (animated).

Run: python tools/art/session_e9.py  -> parts in docs/art/session-g/, review sheet docs/art/session-e9/review-e9.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from palettes import hexes  # noqa: E402
from PIL import Image  # noqa: E402
import render3d  # noqa: E402
import session_g as g  # noqa: E402
import session_o4 as o4  # noqa: E402
import session_o5 as o5  # noqa: E402

REVIEW = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "art", "session-e9")
os.makedirs(REVIEW, exist_ok=True)

# black steel with a violet lean in the shadows and a cold highlight; crimson that warms toward white as it brightens
BLACK = hexes("#0b090e", "#17131b", "#251f2b", "#373040", "#524a5c", "#7d7488")
CRIMSON = hexes("#2a0508", "#560a10", "#8c1018", "#c41d22", "#ee4a36", "#ffb48c")


def solid(ramp, idx):
    img = g.blank()
    for y in range(16):
        for x in range(16):
            img.putpixel((x, y), ramp[idx])
    return img


# The blade is painted, not built: one 64 px texture holds its silhouette as an 8 x 64 strip (u 0-2, v 0-16 of the
# model's uv), 0.3 units a texel. Row 0 is the base at the habaki, row 63 the tip (the image is drawn tip up).
BLADE_W, BLADE_ROWS, TEXEL = 8, 64, 0.3


def blade_shape(r):
    """Where the blade is on row r (0 = base, 63 = tip): (spine, edge) in texels across the strip. The whole blade bows
    toward the spine side as it nears the tip (sori), narrows a little, and in the last rows the edge sweeps up to meet
    the spine in the point (the kissaki)."""
    t = r / (BLADE_ROWS - 1)
    spine = 2.0 - 2.0 * t * t
    width = 6.0 - 2.0 * t
    if r >= BLADE_ROWS - 9:
        k = (BLADE_ROWS - 1 - r) / 8
        width = max(0.9, width * k ** 0.6)
    return spine, spine + width


BLADE_HALF_THICK = 0.3


def blade_columns(r):
    """The first and one-past-the-last filled column of row r (as the texture draws it)."""
    spine, edge = blade_shape(r)
    cols = [c for c in range(BLADE_W) if spine <= c + 0.5 < edge]
    return (cols[0], cols[-1] + 1) if cols else (int(spine), int(spine) + 1)


def edge_side_frames(n=8):
    """The edge's own wall (the blade's thickness on its cutting side): glowing crimson, with the same white-hot glint
    as the faces' edge sweeping from the habaki (v 16) to the tip (v 0) in step with them."""
    out = []
    for fr in range(n):
        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        glint = fr * BLADE_ROWS / n
        for y in range(16):
            r = (15.5 - y) * BLADE_ROWS / 16
            near = abs(((r - glint + BLADE_ROWS / 2) % BLADE_ROWS) - BLADE_ROWS / 2)
            base = 5 if near < 2.5 else 4 if near < 6 else 3
            for x in range(16):
                img.putpixel((x, y), CRIMSON[base])
        out.append(img)
    return out


def hamon(r):
    """The temper line's place across the blade (0 = spine, 1 = edge): wavy, like a gunome hamon."""
    return 0.6 + 0.07 * math.sin(r * 0.22)


def blade_texture():
    """The blade's flat, both faces: a dark spine, the shinogi ridge catching the light, black steel, the crimson
    hamon, polished hardened steel up to the edge (the edge itself glows on its own overlay)."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for r in range(BLADE_ROWS):
        spine, edge = blade_shape(r)
        y = BLADE_ROWS - 1 - r
        for c in range(BLADE_W):
            mid = c + 0.5
            if not (spine <= mid < edge):
                continue
            f = (mid - spine) / (edge - spine)
            h = hamon(r)
            if f < 0.17:
                col = BLACK[1]                                         # the spine
            elif f < 0.34:
                col = BLACK[4]                                         # the shinogi ridge, one clean line of light
            elif abs(f - h) < 0.08:
                col = CRIMSON[1]                                       # the hamon: a long, slow, dark crimson wave
            elif f < h:
                col = BLACK[2]                                         # the flat
            elif f < 0.84:
                col = BLACK[3]                                         # hardened steel, a step brighter than the flat
            else:
                col = CRIMSON[3]                                       # the edge (glows on the overlay)
            img.putpixel((c, y), col)
    return img


def blade_glow(n=8):
    """The glowing edge on its own (everything else clear): crimson, hottest at the edge, with a white-hot glint
    sweeping from the habaki to the tip over the frames (the tip burns brightest)."""
    out = []
    for fr in range(n):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        glint = fr * BLADE_ROWS / n
        for r in range(BLADE_ROWS):
            spine, edge = blade_shape(r)
            y = BLADE_ROWS - 1 - r
            near = abs(((r - glint + BLADE_ROWS / 2) % BLADE_ROWS) - BLADE_ROWS / 2)
            tip = r >= BLADE_ROWS - 9
            for c in range(BLADE_W):
                mid = c + 0.5
                if not (spine <= mid < edge):
                    continue
                f = (mid - spine) / (edge - spine)
                if f < 0.84 and not (tip and f > 0.5):
                    continue
                base = 4 if tip else 3
                if near < 1.5:
                    base = 5
                elif near < 4:
                    base = max(base, 4)
                img.putpixel((c, y), CRIMSON[base])
        out.append(img)
    return out


def wrap():
    """Tsukamaki: crimson cord crossing over a black ray-skin core, in diamonds (lit from the top-left)."""
    img = g.blank()
    for y in range(16):
        for x in range(16):
            a = (x + y) % 8
            b = (x - y) % 8
            if a in (0, 1) or b in (0, 1):
                c = CRIMSON[3] if (a == 0 or b == 0) else CRIMSON[2]
            else:
                c = BLACK[2] if (x + y) % 3 else BLACK[1]
            img.putpixel((x, y), c)
    return img


def katana_held():
    """S4MURAI's katana in the hand (boss-only)."""
    m = g.Model("s4murai_katana")
    m.part = True
    t_black = m.texture("black", g.metal(BLACK, 991, tone=2))
    t_black_lit = m.texture("black_lit", g.metal(BLACK, 992, tone=3))
    t_crimson = m.texture("crimson", g.metal(CRIMSON, 993, tone=3))
    t_wrap = m.texture("wrap", wrap())
    # handle: kashira, wrapped grip; then the guard and collar
    g.prism(m, 1.5, -4.6, -4.0, t_black_lit)                         # kashira (pommel cap)
    g.prism(m, 1.25, -4.0, 1.4, (t_wrap, [0, 0, 2, 6]))              # the wrapped grip
    g.prism(m, 3.6, 1.4, 2.0, t_black, d=3.6)                        # tsuba (guard), octagonal: two crossed plates
    g.prism(m, 2.6, 1.42, 1.98, t_black_lit, d=4.4)
    g.prism(m, 4.4, 1.42, 1.98, t_black_lit, d=2.6)
    g.prism(m, 3.8, 1.55, 1.85, t_crimson, d=3.8)                    # its crimson rim
    g.prism(m, 1.15, 2.0, 2.9, t_crimson, d=0.9)                     # habaki (collar)
    # the blade: two painted planes 0.3 apart (front and back), the glowing edge on a plane over each
    t_blade = m.texture("blade", blade_texture())
    t_glow = m.texture("glow", blade_glow())
    m.mcmeta["glow"] = {"animation": {"frametime": 2, "interpolate": True}}
    width, length = BLADE_W * TEXEL, BLADE_ROWS * TEXEL
    x0, y0 = 8 - 4.5 * TEXEL, 2.9                                    # the base's middle over the habaki
    front, back = [0, 0, 2, 16], [2, 0, 0, 16]
    zf, zb = 8 + BLADE_HALF_THICK, 8 - BLADE_HALF_THICK
    m.box((x0, y0, zf), (x0 + width, y0 + length, zf), {"south": (t_blade, front)})
    m.box((x0, y0, zb), (x0 + width, y0 + length, zb), {"north": (t_blade, back)})
    m.box((x0, y0, zf + 0.02), (x0 + width, y0 + length, zf + 0.02), {"south": (t_glow, front)}, shade=False, light=15)
    m.box((x0, y0, zb - 0.02), (x0 + width, y0 + length, zb - 0.02), {"north": (t_glow, back)}, shade=False, light=15)
    # the blade's thickness: the spine and the edge as walls between the two faces, one long strip per run of rows where
    # the silhouette's side stays in the same column (a handful, following the curve), and the ledges where it steps
    t_side = m.texture("edge_side", edge_side_frames())
    m.mcmeta["edge_side"] = {"animation": {"frametime": 2, "interpolate": True}}
    rows = [blade_columns(r) for r in range(BLADE_ROWS)]
    def ry(r):
        return y0 + r * TEXEL
    def v(r):                                                        # the side texture runs tip (v 0) to base (v 16)
        return 16 - r * 16 / BLADE_ROWS
    for side, (face, tex, glow) in ((0, ("west", t_black, False)), (1, ("east", t_side, True))):
        r = 0
        while r < BLADE_ROWS:
            col = rows[r][side]
            r1 = r
            while r1 + 1 < BLADE_ROWS and rows[r1 + 1][side] == col:
                r1 += 1
            x = x0 + col * TEXEL
            uv = [0, v(r1 + 1), 16, v(r)] if glow else [0, 0, 1, max(1, round((r1 - r + 1) * TEXEL))]
            m.box((x, ry(r), zb), (x, ry(r1 + 1), zf), {face: (tex, uv)}, shade=not glow, light=15 if glow else 0)
            if r1 + 1 < BLADE_ROWS:                                  # the ledge where the side steps to its next column
                nxt = rows[r1 + 1][side]
                a, b = sorted((x, x0 + nxt * TEXEL))
                m.box((a, ry(r1 + 1), zb), (b, ry(r1 + 1), zf), {"up": (tex, [0, v(r1 + 1), 16, v(r1 + 1) + 0.25] if glow else [0, 0, 1, 1]),
                      "down": (tex, [0, v(r1 + 1), 16, v(r1 + 1) + 0.25] if glow else [0, 0, 1, 1])}, shade=not glow, light=15 if glow else 0)
            r = r1 + 1
    top = rows[BLADE_ROWS - 1]                                       # the very point
    m.box((x0 + top[0] * TEXEL, ry(BLADE_ROWS), zb), (x0 + top[1] * TEXEL, ry(BLADE_ROWS), zf), {"up": (t_side, [0, 0, 16, 0.25])},
          shade=False, light=15)
    # its own hold (not a sword sprite's diagonal): in the hand's frame +y runs ahead, -z down the arm and +x toward the
    # body, so turning 90 about y puts the edge (+x) downward and a slight tilt about x drops the point a little ahead.
    # Grip: the middle of the wrapped handle. 1.15x, larger than vanilla's 0.85 sword.
    m.display = g.grip_display((-12, 90, 0), (8, -1.3, 8), 1.15)
    return m


SOAK = [   # three figures gathered round: stand in it together
    "................",
    "......####......",
    "......#OO#......",
    "......####......",
    ".....######.....",
    ".....######.....",
    "................",
    "..####....####..",
    "..#OO#....#OO#..",
    "..####....####..",
    ".######..######.",
    ".######..######.",
    "................",
    "................",
    "................",
    "................",
]
def reticle():
    """A reticle: a ring, four ticks pointing in, a dot in the middle (you're marked)."""
    rows = []
    for y in range(16):
        row = ""
        for x in range(16):
            d = math.hypot(x + 0.5 - 8, y + 0.5 - 8)
            axis = abs(x + 0.5 - 8) < 1 or abs(y + 0.5 - 8) < 1
            if d < 1.2:
                row += "O"
            elif 6.0 <= d < 7.2:
                row += "#"
            elif axis and 3.8 <= d < 6.0:
                row += "#"
            else:
                row += "."
        rows.append(row)
    return rows


TARGET = reticle()


# ---------------------------------------------------------------- the raid's obstacles (round 2: no particles at all)
# Everything here is drawn in O4's greys and tinted by the game per attack. Light sprites: coloured by heat, no outline,
# brightest in the middle of the light, animated (STYLE rules 10-11).

def _px(img, x, y, tone, alpha):
    if alpha > 0:
        img.putpixel((x % 16, y % 16), o4.rgba(o4.GREY[max(0, min(5, tone))], max(0, min(255, int(alpha)))))


def wall_frames(n=8):
    """A force field (walls, sweeping barriers): bright rails top and bottom, a faint lattice of light between them, and
    a band of brightness travelling along the wall over the frames."""
    out = []
    for f in range(n):
        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        band = f * 16 / n
        for y in range(16):
            for x in range(16):
                near = abs(((x - band + 8) % 16) - 8)
                lift = 2 if near < 1.5 else 1 if near < 3.5 else 0
                if y in (0, 15):
                    _px(img, x, y, 5, 255)                               # the rails
                elif y in (1, 14):
                    _px(img, x, y, 4, 200 + 25 * lift)
                elif (x + y) % 8 == 0 or (x - y) % 8 == 0:
                    _px(img, x, y, 3 + lift, 120 + 45 * lift)            # the lattice
                else:
                    rail = min(y, 15 - y)
                    _px(img, x, y, 3, (70 if rail <= 3 else 40) + 30 * lift)
        out.append(img)
    return out


def raid_wall():
    """An upright pane, 16 units square through the model's centre, the field on both faces, glowing, tinted."""
    m = g.Model("raid_wall")
    m.part = True
    t = m.texture("field", wall_frames())
    m.mcmeta["field"] = {"animation": {"frametime": 2, "interpolate": True}}
    e = m.box((0, 0, 8), (16, 16, 8), {"south": (t, [0, 0, 16, 16]), "north": (t, [16, 0, 0, 16])}, shade=False, light=15)
    for face in e["faces"].values():
        face["tintindex"] = 0
    m.tinted = True
    return m


def raid_wall_post():
    """A pylon at each end of a wall section (scaled by the plugin to the wall's height): a dark steel post, a glowing
    tinted strip up each face pulsing upward, and a glowing cap."""
    m = g.Model("raid_wall_post")
    m.part = True
    t_body = m.texture("body", g.metal(BLACK, 995, tone=2))
    strip = []
    for f in range(8):
        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        for y in range(16):
            pulse = abs(((y - (16 - f * 2) + 8) % 16) - 8)
            for x in range(16):
                _px(img, x, y, 5 if pulse < 1.5 else 4, 255)
        strip.append(img)
    t_glow = m.texture("glow", strip)
    m.mcmeta["glow"] = {"animation": {"frametime": 2, "interpolate": True}}
    g.prism(m, 5, 0, 15, t_body)                                         # the post
    for d, frm, to in (("south", (7, 1.5, 10.55), (9, 13.5, 10.55)), ("north", (7, 1.5, 5.45), (9, 13.5, 5.45)),
                       ("east", (10.55, 1.5, 7), (10.55, 13.5, 9)), ("west", (5.45, 1.5, 7), (5.45, 13.5, 9))):
        e = m.box(frm, to, {d: (t_glow, [0, 0, 2, 12])}, shade=False, light=15)   # a glowing strip up each face
        e["faces"][d]["tintindex"] = 0
    e = m.box((6, 15, 6), (10, 16.5, 10), {d: (t_glow, [0, 0, 4, 4]) for d in ("north", "south", "east", "west", "up", "down")},
              shade=False, light=15)                                    # the cap
    for face in e["faces"].values():
        face["tintindex"] = 0
    m.tinted = True
    return m


def laser_frames(n=8):
    """A laser seen side-on (u across it, v along it): a white-hot core, a glow falling away to either side, and pulses
    of light running along it over the frames."""
    profile = {7: (5, 255), 8: (5, 255), 6: (5, 225), 9: (5, 225), 5: (4, 175), 10: (4, 175), 4: (3, 120), 11: (3, 120),
               3: (3, 70), 12: (3, 70), 2: (2, 35), 13: (2, 35)}
    out = []
    for f in range(n):
        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        for y in range(16):
            pulse = abs(((y - f * 2 + 8) % 16) - 8) % 8
            lift = 1 if pulse < 2 else 0
            for x, (tone, alpha) in profile.items():
                _px(img, x, y, tone + lift, alpha + 50 * lift)
        out.append(img)
    return out


def raid_laser():
    """A laser beam: two crossed glowing planes along the model's y (stretched by the plugin between two points)."""
    return o5.streak("raid_laser", laser_frames(), 4)


def curtain_frames(n=8, crest=False):
    """A curtain of light (u along it, v up it): brightest at the floor, fading upward to a thin bright top edge, with
    light running along it over the frames. crest: a low ring's band - bright along both its top and its bottom."""
    out = []
    for f in range(n):
        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        for y in range(16):
            for x in range(16):
                run = abs(((x - f * 2 + 8) % 16) - 8)
                lift = 1 if run < 1.5 else 0
                up = 15 - y                                                  # 0 at the floor .. 15 at the top
                if crest:
                    edge = min(up, 15 - up)
                    tone, alpha = (5, 255) if edge <= 1 else (4, 190) if edge <= 3 else (3, 55)
                    lift = lift if edge <= 3 else 0                          # the light runs along the crests only
                elif up <= 1:
                    tone, alpha = 5, 255
                elif up <= 4:
                    tone, alpha = 4, 220
                elif up < 15:
                    tone, alpha = 3, 170 - up * 8
                else:
                    tone, alpha = 4, 200
                _px(img, x, y, tone + lift, alpha + 40 * lift)
        out.append(img)
    return out


def laser_wall():
    """A full-height laser's section: an upright curtain of light through the model's centre, both faces, tinted (the
    plugin scales it to the section's length and the beam's height)."""
    m = g.Model("raid_laser_wall")
    m.part = True
    t = m.texture("curtain", curtain_frames())
    m.mcmeta["curtain"] = {"animation": {"frametime": 2, "interpolate": True}}
    e = m.box((0, 0, 8), (16, 16, 8), {"south": (t, [0, 0, 16, 16]), "north": (t, [16, 0, 0, 16])}, shade=False, light=15)
    for face in e["faces"].values():
        face["tintindex"] = 0
    m.tinted = True
    return m


RING_PANELS = 32


def ring_shell(key, frames, missing=0):
    """A ring of light: a cylinder shell of 32 upright panels, 8 units out from the centre, 16 tall (the plugin scales
    it to the ring's radius and height). missing panels are left out round the +x side: the gap of a ring you walk
    through."""
    m = g.Model(key)
    m.part = True
    t = m.texture("band", frames)
    m.mcmeta["band"] = {"animation": {"frametime": 2, "interpolate": True}}
    step = 360 / RING_PANELS
    chord = 2 * 8 * math.tan(math.radians(step / 2)) + 0.06
    for k in range(RING_PANELS):
        theta = k * step
        facing = (90 - theta) % 360                                          # where this panel ends up (atan2 of z, x)
        off = min(facing, 360 - facing)
        if missing and off < missing * step / 2 + 0.01:
            continue
        u0 = (k % 4) * 4
        e = m.box((8 - chord / 2, 0, 16), (8 + chord / 2, 16, 16),
                  {"south": (t, [u0, 0, u0 + 4, 16]), "north": (t, [u0 + 4, 0, u0, 16])}, shade=False, light=15)
        e["rotation"] = {"origin": [8, 8, 8], "axis": "y", "angle": theta}
        for face in e["faces"].values():
            face["tintindex"] = 0
    m.tinted = True
    return m


def ring_models():
    low = ring_shell("raid_ring_low", curtain_frames(crest=True))
    tall = curtain_frames()
    return [low] + [ring_shell(f"raid_ring_tall_gap{n}", tall, n) for n in range(1, 17)]


SECTOR_ARCS = (60, 70, 90, 120, 150, 180)


def sector(arc, filled):
    """A warning sector of {@code arc} degrees, its point at the centre, opening toward the top (north), its rim at the
    edge of the square: so scaled to twice the reach it covers exactly the hit (inside the reach, within half the arc of
    the aim). Outline: a bright rim and both sides, dark lines just outside them; fill: see-through, brighter at the rim."""
    img = o4.blank()
    half = arc / 2
    for y in range(32):
        for x in range(32):
            dx, dy = x + 0.5 - 16, 16 - (y + 0.5)
            r = math.hypot(dx, dy)
            if r > 15.9 or r < 0.3:
                continue
            ang = abs(math.degrees(math.atan2(dx, dy)))
            if ang > half:
                side_out = (ang - half) * math.pi / 180 * r
                if not filled and side_out < 0.9 and r < 15.9:
                    img.putpixel((x, y), o4.rgba(o4.GREY[1]))
                continue
            edge_d = min(15.9 - r, (half - ang) * math.pi / 180 * r if half < 180 else 99)
            if filled:
                img.putpixel((x, y), o4.rgba(o4.GREY[4], 150 if edge_d < 1.0 else 95 if int(r) % 4 == 0 else 70))
            elif edge_d < 1.2:
                img.putpixel((x, y), o4.rgba(o4.GREY[4] if (x + y) < 32 else o4.GREY[3]))
            elif edge_d < 1.9:
                img.putpixel((x, y), o4.rgba(o4.GREY[1]))
    return img


def sector_models():
    out = []
    for arc in SECTOR_ARCS:
        out.append(o4.plane(f"floor_warning_sector{arc}", sector(arc, False), tint=True, light=15))
        out.append(o4.plane(f"floor_warning_sector{arc}_fill", sector(arc, True), tint=True, light=15))
    return out


def models():
    return ([katana_held(), o4.plane("floor_mark_soak", o4.symbol(SOAK), tint=True, light=15),
             o4.plane("floor_mark_target", o4.symbol(TARGET), tint=True, light=15), raid_wall(), raid_wall_post(),
             raid_laser(), laser_wall()] + ring_models() + sector_models()
            + [o4.plane("floor_lawn", lawn(), light=0), raid_black_hole(), raid_cigarette(),
               raid_beer_mug(), raid_beer_keg()])


# ---------------------------------------------------------------- round 4: OldeGrumpy's lawn, Charles's black hole

GRASS = hexes("#1f3a1c", "#2c5426", "#3c6f31", "#4e8a3b", "#67a64a", "#8cc66a")


def lawn():
    """OldeGrumpy's lawn (a floor decal ~10 blocks across): a round, well-kept lawn mowed in light and dark stripes, a
    few dandelions and poppies, and a darker trimmed edge. Lit from the top-left like everything else."""
    import random
    rnd = random.Random(31)
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    for y in range(32):
        for x in range(32):
            d = math.hypot(x + 0.5 - 16, y + 0.5 - 16)
            if d > 15.6:
                continue
            stripe = (x // 4) % 2                                           # the mower's stripes
            tone = 3 if stripe else 4
            if d > 14.6:
                tone = 1                                                    # the trimmed edge
            elif d > 13.8:
                tone = 2
            elif (x + y) < 20 and rnd.random() < 0.15:
                tone = min(5, tone + 1)                                     # catching the light
            elif rnd.random() < 0.12:
                tone = max(1, tone - 1)                                     # tufts
            img.putpixel((x, y), GRASS[tone] + (255,) if len(GRASS[tone]) == 3 else GRASS[tone])
    for (x, y, c) in ((9, 11, (240, 210, 60)), (21, 8, (240, 210, 60)), (12, 22, (200, 40, 40)), (23, 19, (240, 210, 60)),
                      (17, 26, (200, 40, 40)), (6, 18, (245, 245, 240)), (25, 13, (245, 245, 240))):
        img.putpixel((x, y), c + (255,))                                    # dandelions, poppies, daisies
    return img


def black_hole_frames(n=8):
    """The accretion disk seen from above (u, v across it): a glowing ring of matter swirling round a black centre -
    violet at its outer edge, hot orange-white near the event horizon - turning over the frames."""
    out = []
    ramp = [(40, 10, 70), (90, 30, 150), (160, 70, 220), (230, 120, 90), (255, 190, 120), (255, 240, 210)]
    for f in range(n):
        img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        for y in range(32):
            for x in range(32):
                dx, dy = x + 0.5 - 16, y + 0.5 - 16
                d = math.hypot(dx, dy)
                if d < 5.5 or d > 15.5:
                    continue
                a = math.atan2(dy, dx) + d * 0.35 - f * math.pi / 4 * 0.5    # spiral arms, turning
                swirl = 0.5 + 0.5 * math.sin(a * 3)
                heat = 1 - (d - 5.5) / 10                                     # hotter toward the centre
                tone = max(0, min(5, int(heat * 4 + swirl * 1.8)))
                alpha = int(255 * min(1, 0.35 + heat * 0.5 + swirl * 0.3)) if d > 6.2 else 255
                img.putpixel((x, y), ramp[tone] + (alpha,))
        out.append(img)
    return out


def raid_black_hole():
    """Charles's black hole (shown by the plugin, grown from nothing): a black sphere (an octagonal ball of crossed
    boxes) inside a glowing, swirling accretion disk, tilted a little so it reads in three dimensions."""
    m = g.Model("raid_black_hole")
    m.part = True
    core = Image.new("RGBA", (16, 16), (6, 3, 10, 255))
    t_core = m.texture("core", core)
    t_disk = m.texture("disk", black_hole_frames())
    m.mcmeta["disk"] = {"animation": {"frametime": 2, "interpolate": True}}
    for w, h in ((5.0, 3.0), (3.0, 5.0), (4.2, 4.2)):                        # the ball: three boxes crossed
        g.prism(m, w, 8 - h / 2, 8 + h / 2, t_core, d=w)
        g.prism(m, w * 0.62, 8 - h / 2 - 0.4, 8 + h / 2 + 0.4, t_core, d=w * 0.62)
    e = m.box((0, 8, 0), (16, 8, 16), {"up": (t_disk, [0, 0, 16, 16]), "down": (t_disk, [0, 16, 16, 0])}, shade=False, light=15)
    e["rotation"] = {"origin": [8, 8, 8], "axis": "x", "angle": 18}
    return m


# ---------------------------------------------------------------- round 5: goob's cigarette tower

def raid_cigarette():
    """goob's cigarette tower (shown by the plugin, stood on the floor about 2 blocks tall): a round cigarette - an
    orange cork-pattern filter with a thin gold band, a white paper body with a faint seam, a black ash ring, and a
    glowing ember tip that flickers (red to orange-white)."""
    import random
    rnd = random.Random(77)
    m = g.Model("raid_cigarette")
    m.part = True
    cork_ramp = [(110, 50, 14), (160, 80, 24), (205, 115, 40), (235, 150, 60), (250, 185, 95)]
    cork = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            tone = 2 + (1 if x % 5 == 0 else 0) - (1 if rnd.random() < 0.25 else 0) + (1 if rnd.random() < 0.08 else 0)
            cork.putpixel((x, y), cork_ramp[max(0, min(4, tone))] + (255,))
    paper = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            c = (236, 234, 228) if x % 8 else (214, 212, 206)                  # a faint seam down the paper
            if x in (1, 2):
                c = (250, 250, 247)                                             # the lit side
            paper.putpixel((x, y), c + (255,))
    band = Image.new("RGBA", (16, 16), (214, 178, 80, 255))
    ash = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            ash.putpixel((x, y), ((30, 28, 30) if rnd.random() < 0.6 else (70, 66, 64)) + (255,))
    embers = []
    ember_ramp = [(110, 10, 8), (180, 24, 10), (230, 60, 20), (255, 120, 40), (255, 200, 120)]
    for f in range(6):
        img = Image.new("RGBA", (16, 16))
        for y in range(16):
            for x in range(16):
                heat = rnd.random() * 0.6 + 0.4 * (0.5 + 0.5 * math.sin(f * 1.1 + x * 0.7 + y * 0.9))
                img.putpixel((x, y), ember_ramp[min(4, int(heat * 5))] + (255,))
        embers.append(img)
    t_cork = m.texture("filter", cork)
    t_paper = m.texture("paper", paper)
    t_band = m.texture("band", band)
    t_ash = m.texture("ash", ash)
    t_ember = m.texture("ember", embers)
    m.mcmeta["ember"] = {"animation": {"frametime": 3, "interpolate": True}}
    def rod(w, y0, y1, tex, light=0):
        """A round section: an octagon of two crossed boxes."""
        g.prism(m, w, y0, y1, tex, d=w * 0.58, light=light)
        g.prism(m, w * 0.58, y0, y1, tex, d=w, light=light)
    rod(3.2, 0, 5.0, t_cork)                 # the filter
    rod(3.25, 5.0, 5.4, t_band)              # a thin gold band
    rod(3.2, 5.4, 14.6, t_paper)             # the paper
    rod(3.22, 14.6, 15.3, t_ash)             # the ash ring
    rod(2.9, 15.3, 16.0, t_ember, light=15)  # the lit tip
    return m


# ---------------------------------------------------------------- round 6: X's beer (Act 2)

def raid_beer_mug():
    """X's thrown beer mug (shown by the plugin, flying and spinning): a thick glass stein of amber beer - darker at the
    bottom, rising bubbles - with a white foam head that spills over the rim, a glass handle on one side."""
    import random
    rnd = random.Random(31)
    m = g.Model("raid_beer_mug")
    m.part = True
    beer_ramp = [(122, 58, 8), (170, 92, 14), (212, 132, 24), (240, 170, 44), (255, 214, 110)]
    frames = []
    for f in range(6):                                  # bubbles rise through the beer
        img = Image.new("RGBA", (16, 16))
        for y in range(16):
            for x in range(16):
                tone = 1 + (y < 9) + (y < 4) - (1 if x in (11, 12) else 0)
                img.putpixel((x, y), beer_ramp[max(0, min(4, tone))] + (255,))
        for bx in (2, 6, 9, 13):
            by = (bx * 5 - f * 2) % 16
            img.putpixel((bx, by), beer_ramp[4] + (255,))
        for x in (1, 2):                                # the glass's lit edge
            for y in range(16):
                img.putpixel((x, y), (255, 236, 180, 255))
        frames.append(img)
    foam = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            v = 250 - (14 if rnd.random() < 0.3 else 0) - (10 if y > 11 else 0)
            foam.putpixel((x, y), (v, v - 4, v - 16, 255))
    glass = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            glass.putpixel((x, y), ((214, 228, 226) if x % 5 else (246, 252, 250)) + (255,))
    bottom = Image.new("RGBA", (16, 16), (140, 104, 50, 255))
    t_beer = m.texture("beer", frames)
    m.mcmeta["beer"] = {"animation": {"frametime": 3, "interpolate": True}}
    t_foam = m.texture("foam", foam)
    t_glass = m.texture("glass", glass)
    t_bottom = m.texture("bottom", bottom)
    g.prism(m, 8.6, 0, 1.2, t_glass, cx=7)              # the thick glass base
    g.prism(m, 8.0, 1.2, 10.5, t_beer, cx=7)            # the beer
    g.prism(m, 6.4, 1.2, 10.5, t_beer, cx=7, d=9.0)     # rounded a little
    g.prism(m, 9.0, 10.5, 12.5, t_foam, cx=7)           # the foam head, spilling over the rim
    g.prism(m, 6.0, 12.5, 13.6, t_foam, cx=7.4, d=6.6)  # a mound on top
    g.prism(m, 1.6, 3.0, 9.0, t_glass, cx=13.2, d=1.8)  # the handle: an upright bar...
    g.prism(m, 2.4, 8.0, 9.4, t_glass, cx=12.0, d=1.8)  # ...joined at the top
    g.prism(m, 2.4, 2.6, 4.0, t_glass, cx=12.0, d=1.8)  # ...and the bottom
    g.prism(m, 8.0, 0, 0.2, t_bottom, cx=7)
    return m


def raid_beer_keg():
    """X's rolling beer keg (shown by the plugin, laid on its side and rolling): an oak barrel of bowed staves with
    dark iron hoops near each end and round the belly, a lid with rings of grain and a brass tap."""
    import random
    rnd = random.Random(53)
    m = g.Model("raid_beer_keg")
    m.part = True
    oak = [(74, 44, 22), (104, 64, 32), (136, 88, 46), (166, 112, 62), (196, 142, 86)]
    staves = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            tone = 2 + (1 if x % 4 == 1 else 0) - (2 if x % 4 == 0 else 0) - (1 if rnd.random() < 0.12 else 0)
            staves.putpixel((x, y), oak[max(0, min(4, tone))] + (255,))
    iron = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            v = 52 + (26 if y % 4 == 1 else 0) + (10 if rnd.random() < 0.15 else 0)
            iron.putpixel((x, y), (v, v, v + 6, 255))
    lid = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            r = math.hypot(x - 7.5, y - 7.5)
            tone = 3 if int(r) % 3 else 1
            lid.putpixel((x, y), (oak[0] if r > 7 else oak[tone]) + (255,))
    brass = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            brass.putpixel((x, y), ((232, 190, 80) if x < 2 else (184, 140, 48)) + (255,))
    t_staves = m.texture("staves", staves)
    t_iron = m.texture("iron", iron)
    t_lid = m.texture("lid", lid)
    t_brass = m.texture("brass", brass)
    def rod(w, y0, y1, tex, top=None):
        g.prism(m, w, y0, y1, tex, d=w * 0.58, top=top)
        g.prism(m, w * 0.58, y0, y1, tex, d=w, top=top)
    lid_cap = (t_lid, [0, 0, 16, 16])
    rod(11.0, 0, 3.0, t_staves, top=lid_cap)            # the barrel bows out toward its belly
    rod(12.4, 3.0, 13.0, t_staves, top=lid_cap)
    rod(11.0, 13.0, 16.0, t_staves, top=lid_cap)
    rod(11.4, 1.0, 2.2, t_iron)                         # the hoops
    rod(12.8, 5.4, 6.4, t_iron)
    rod(12.8, 9.6, 10.6, t_iron)
    rod(11.4, 13.8, 15.0, t_iron)
    g.prism(m, 1.6, 16.0, 17.2, t_brass, cx=8, cz=10.5)  # the tap on the lid
    g.prism(m, 1.2, 16.8, 17.6, t_brass, cx=8, cz=11.8, d=2.0)
    return m



def _tinted(img, tint):
    out = img.copy()
    px = out.load()
    for yy in range(out.height):
        for xx in range(out.width):
            r, gg, b, a = px[xx, yy]
            px[xx, yy] = (r * tint[0] // 255, gg * tint[1] // 255, b * tint[2] // 255, a)
    return out


def _tinted_model(m, tint):
    """A copy of m with its textures coloured like the game would (for the review renders)."""
    import copy
    c = copy.copy(m)
    c.textures = {k: ([_tinted(f, tint) for f in v] if isinstance(v, list) else _tinted(v, tint)) for k, v in m.textures.items()}
    return c


def review(ms):
    by = {m.key: m for m in ms}
    katana = by["s4murai_katana"]
    sheet = Image.new("RGBA", (1600, 1180), (40, 38, 46, 255))
    for i, (yaw, pitch, f) in enumerate(((0, 0, 0), (35, 20, 2), (90, 10, 5))):
        sheet.alpha_composite(render3d.render(katana, frame=f, yaw=yaw, pitch=pitch, s=17, size=(520, 520), center=(8, 9, 8)), (10 + i * 530, 10))
    x = 10
    for key, tint in (("floor_mark_soak", (80, 220, 110)), ("floor_mark_soak", (240, 170, 40)), ("floor_mark_target", (200, 60, 230)),
                      ("floor_mark_target", (255, 60, 60))):
        sheet.alpha_composite(_tinted(by[key].textures["face"], tint).resize((150, 150), Image.NEAREST), (x, 540))
        x += 165
    # the obstacles, tinted as the game would, in 3D
    shots = [("raid_wall", (110, 200, 255), 20, 8), ("raid_wall_post", (110, 200, 255), 30, 20), ("raid_laser", (255, 200, 40), 60, 10),
             ("raid_laser_wall", (255, 60, 60), 20, 8), ("raid_ring_low", (230, 120, 40), 30, 30), ("raid_ring_tall_gap3", (150, 80, 255), 30, 30),
             ("raid_ring_tall_gap8", (150, 80, 255), 30, 30)]
    for i, (key, tint, yaw, pitch) in enumerate(shots):
        view = render3d.render(_tinted_model(by[key], tint), frame=i, yaw=yaw, pitch=pitch, s=11, size=(300, 300), center=(8, 8, 8),
                               bg=(30, 30, 36, 255), blend=True)
        pos = (680 + (i % 3) * 305, 540 + (i // 3) * 305) if i < 6 else (350, 700)
        sheet.alpha_composite(view, pos)
    for i, arc in enumerate((60, 70, 150, 180)):
        sheet.alpha_composite(_tinted(by[f"floor_warning_sector{arc}"].textures["face"], (255, 90, 60)).resize((150, 150), Image.NEAREST),
                              (10 + i * 165, 1010))
    sheet.alpha_composite(by["floor_lawn"].textures["face"].resize((160, 160), Image.NEAREST), (10, 700))
    sheet.alpha_composite(render3d.render(by["raid_black_hole"], frame=2, yaw=30, pitch=25, s=8, size=(160, 160), center=(8, 8, 8),
                                          bg=(30, 30, 36, 255), blend=True), (175, 700))
    sheet.alpha_composite(render3d.render(by["raid_cigarette"], frame=1, yaw=30, pitch=20, s=9, size=(160, 300), center=(8, 8, 8),
                                          bg=(30, 30, 36, 255)), (175, 860))
    sheet.alpha_composite(render3d.render(by["raid_beer_mug"], frame=1, yaw=30, pitch=20, s=12, size=(220, 240), center=(8, 7, 8),
                                          bg=(30, 30, 36, 255)), (345, 860))
    sheet.alpha_composite(render3d.render(by["raid_beer_keg"], frame=0, yaw=30, pitch=25, s=11, size=(240, 260), center=(8, 8, 8),
                                          bg=(30, 30, 36, 255)), (575, 860))
    path = os.path.join(REVIEW, "review-e9.png")
    sheet.save(path)
    frames = [render3d.render(katana, frame=f, yaw=35, pitch=20, s=17, size=(420, 420), center=(8, 9, 8)).convert("RGB") for f in range(8)]
    frames[0].save(os.path.join(REVIEW, "preview-katana.gif"), save_all=True, append_images=frames[1:], duration=100, loop=0)
    ring = _tinted_model(by["raid_ring_tall_gap4"], (150, 80, 255))
    rf = [render3d.render(ring, frame=f, yaw=30, pitch=25, s=11, size=(320, 320), center=(8, 8, 8), blend=True).convert("RGB") for f in range(8)]
    rf[0].save(os.path.join(REVIEW, "preview-ring.gif"), save_all=True, append_images=rf[1:], duration=100, loop=0)
    return path


if __name__ == "__main__":
    ms = models()
    for m in ms:
        o4.save(m)
    print(review(ms))
