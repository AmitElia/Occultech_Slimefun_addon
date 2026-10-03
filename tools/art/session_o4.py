"""Session O4: floor markings for boss fights - flat floor holograms like the ritual sigils.

- Attack warnings: a ring at the exact hit radius, a fill that grows from the centre to the edge over the warning (when
  it's full, the hit lands), and the attack's symbol in the middle. Drawn in shaded light tones and tinted to each
  attack's colour by the game (the item model's dye tint), so fourteen attacks keep their colours from one set.
- Ground zones (they hurt while you stand in them): animated, fully coloured pixel-art surfaces - acid, web, yolk (the
  ones the bosses use), fire, poison, frost, shadow (ready for new attacks).

Every pixel solid or clear (the fill and a few zone surfaces are evenly see-through so the floor shows), crisp edges.
Models are parts (the plugin shows them): `python tools/art/session_o4.py`.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from palettes import RAMPS, hexes  # noqa: E402
from PIL import Image  # noqa: E402
import session_g as g  # noqa: E402

N = 32
C = 16.0
GREY = [(40, 40, 44), (92, 92, 98), (150, 150, 156), (200, 200, 204), (236, 236, 240), (255, 255, 255)]


def blank(n=N):
    return Image.new("RGBA", (n, n), (0, 0, 0, 0))


def rgba(c, a=255):
    return tuple(c[:3]) + (a,)


def dist(x, y, cx=C, cy=C):
    return math.hypot(x + 0.5 - cx, y + 0.5 - cy)


# ------------------------------------------------------------------ attack warnings (tinted)

def warning_ring():
    """The edge of the hit: a bright band with a dark line inside and out, and eight ticks pointing in."""
    img = blank()
    for y in range(N):
        for x in range(N):
            d = dist(x, y)
            if 14.0 <= d < 15.6:
                ang = math.atan2(y + 0.5 - C, x + 0.5 - C)
                lit = 0.5 - 0.5 * math.sin(ang + math.pi / 4)               # brighter toward the top-left
                img.putpixel((x, y), rgba(GREY[4] if lit > 0.5 else GREY[3]))
            elif 13.2 <= d < 14.0 or 15.6 <= d < 16.0:
                img.putpixel((x, y), rgba(GREY[1]))
    for k in range(8):                                                       # ticks pointing in
        a = k * math.pi / 4
        for r in (11.6, 12.6):
            img.putpixel((int(C + r * math.cos(a)), int(C + r * math.sin(a))), rgba(GREY[4]))
    return img


def warning_fill():
    """The fill that grows to the edge: an even, see-through disc with a slightly stronger rim and faint rings."""
    img = blank()
    for y in range(N):
        for x in range(N):
            d = dist(x, y)
            if d < 16.0:
                a = 150 if d > 14.6 else 105 if int(d) % 4 == 0 else 80
                img.putpixel((x, y), rgba(GREY[4], a))
    return img


def wedge(filled):
    """A 90-degree wedge, its point at the bottom centre, opening toward the top (north): the outline (bright edge, dark
    lines either side) or the see-through fill."""
    img = blank()
    ax, ay = 16.0, 31.5
    for y in range(N):
        for x in range(N):
            dx, dy = x + 0.5 - ax, ay - (y + 0.5)
            if dy <= 0:
                continue
            r = math.hypot(dx, dy)
            ang = abs(math.degrees(math.atan2(dx, dy)))
            if r > 31.5 or ang > 45:
                continue
            edge_d = min(31.5 - r, (45 - ang) * math.pi / 180 * r)
            if filled:
                img.putpixel((x, y), rgba(GREY[4], 150 if edge_d < 1.2 else 95 if int(r) % 5 == 0 else 75))
            elif edge_d < 1.4:
                img.putpixel((x, y), rgba(GREY[4] if (x + y) < 34 else GREY[3]))
            elif edge_d < 2.1:
                img.putpixel((x, y), rgba(GREY[1]))
    return img


def lane(filled):
    """A charge lane running from the bottom (its start) to the top: edges, and chevrons pointing the way."""
    img = blank()
    for y in range(N):
        for x in range(N):
            if filled:
                img.putpixel((x, y), rgba(GREY[4], 140 if x in (0, 31) else 80))
                continue
            if x in (0, 1, 30, 31):
                img.putpixel((x, y), rgba(GREY[4] if x in (1, 30) else GREY[1]))
            cy = y % 8
            if abs(abs(x - 15.5) - (cy * 1.6 + 1)) < 1.0 and 6 <= x <= 25:
                img.putpixel((x, y), rgba(GREY[3]))
    return img


def wave_ring():
    """A travelling wave: a bright crest at the edge and a fading wake behind it (inside)."""
    img = blank()
    for y in range(N):
        for x in range(N):
            d = dist(x, y)
            if 14.6 <= d < 16.0:
                img.putpixel((x, y), rgba(GREY[5] if (x + y) < 32 else GREY[4]))
            elif 13.0 <= d < 14.6:
                img.putpixel((x, y), rgba(GREY[3], 170))
            elif 11.0 <= d < 13.0:
                img.putpixel((x, y), rgba(GREY[3], 90))
    return img


def splash():
    """A splat where something burst: a ragged star of droplets round a bright centre."""
    img = blank()
    rnd = random.Random(9)
    arms = [(k * 45 + rnd.uniform(-12, 12), rnd.uniform(9, 14)) for k in range(8)]
    for y in range(N):
        for x in range(N):
            d = dist(x, y)
            a = math.degrees(math.atan2(y + 0.5 - C, x + 0.5 - C)) % 360
            reach = 6.5
            for ang, length in arms:
                diff = min(abs(a - ang % 360), 360 - abs(a - ang % 360))
                if diff < 9:
                    reach = max(reach, length - diff * 0.5)
            if d < reach:
                img.putpixel((x, y), rgba(GREY[5] if d < 3 else GREY[4] if d < reach - 1 else GREY[2]))
    for ang, length in arms:                                   # a droplet past each arm
        px = int(C + (length + 2.2) * math.cos(math.radians(ang)))
        py = int(C + (length + 2.2) * math.sin(math.radians(ang)))
        if 0 <= px < N and 0 <= py < N:
            img.putpixel((px, py), rgba(GREY[4]))
    return img


SYMBOLS = {   # 16 px, drawn in light greys with a dark outline; tinted to the attack's colour
    "slam": [   # an impact burst
        "................",
        ".......##.......",
        "...#...##...#...",
        "....#..##..#....",
        ".....#.##.#.....",
        "......####......",
        ".#############..",
        "..############..",
        "......####......",
        ".....#.##.#.....",
        "....#..##..#....",
        "...#...##...#...",
        ".......##.......",
        "................",
        "................",
        "................",
    ],
    "dive": [   # three claw slashes
        "................",
        "..#.....#....#..",
        "..##....##...##.",
        "...##....##...#.",
        "...##....##...##",
        "....##....##..##",
        "....##....##...#",
        ".....##....##..#",
        ".....##....##...",
        "......##....##..",
        "......##....##..",
        ".......#.....#..",
        "................",
        "................",
        "................",
        "................",
    ],
    "web": [
        "................",
        "#......#......#.",
        ".#.....#.....#..",
        "..#..#####..#...",
        "...##..#..##....",
        "..#.#..#..#.#...",
        ".#...#.#.#...#..",
        "#######O#######.",
        ".#...#.#.#...#..",
        "..#.#..#..#.#...",
        "...##..#..##....",
        "..#..#####..#...",
        ".#.....#.....#..",
        "#......#......#.",
        "................",
        "................",
    ],
    "flame": [
        "................",
        "........#.......",
        ".......##.......",
        ".......###......",
        "......####......",
        "...#..#####.....",
        "...##.######.#..",
        "...##########...",
        "....##########..",
        "...###OO#######.",
        "...##OOOO#####..",
        "...##OOOOO####..",
        "....#OOOOO###...",
        ".....##OOO##....",
        "................",
        "................",
    ],
    "storm": [   # a lightning bolt
        "................",
        ".........####...",
        "........####....",
        ".......####.....",
        "......####......",
        ".....#########..",
        "....#########...",
        "........####....",
        ".......####.....",
        "......####......",
        ".....###........",
        "....##..........",
        "...#............",
        "................",
        "................",
        "................",
    ],
    "spikes": [
        "................",
        "................",
        "...#...#....#...",
        "...#...##...#...",
        "..###..##..###..",
        "..###.####.###..",
        "..###.####.###..",
        ".#####.##.#####.",
        ".#####.##.#####.",
        "################",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    "wind": [   # a spiral
        "................",
        ".....######.....",
        "...##......##...",
        "..#...####...#..",
        ".#...#....#...#.",
        ".#..#..##..#..#.",
        ".#..#.#..#.#..#.",
        ".#..#.#.##.#..#.",
        ".#..#..#...#..#.",
        ".#...#....#...#.",
        "..#...####...#..",
        "...#.........#..",
        "....##.....##...",
        "......#####.....",
        "................",
        "................",
    ],
    "roots": [
        "................",
        ".......##.......",
        ".......##.......",
        "......####......",
        "..#...####...#..",
        "...#..####..#...",
        "....#.####.#....",
        ".....######.....",
        "..##..####..##..",
        "....##.##.##....",
        ".....#.##.#.....",
        "...##..##..##...",
        "..#....##....#..",
        ".......##.......",
        "................",
        "................",
    ],
    "sweep": [   # a crescent swing
        "................",
        "..#######.......",
        "#####...###.....",
        "###.......##....",
        "##.........##...",
        "#...........#...",
        "#...........##..",
        "............##..",
        "............##..",
        "...........###..",
        "..........###...",
        "........####....",
        ".....######.....",
        "................",
        "................",
        "................",
    ],
    "curse": [   # a hexing eye
        "................",
        "................",
        "................",
        "....########....",
        "..##........##..",
        ".#....####....#.",
        "#....##OO##....#",
        "#....#OOOO#....#",
        ".#....####....#.",
        "..##........##..",
        "....########....",
        "................",
        ".....#.#..#.#...",
        "......#....#....",
        "................",
        "................",
    ],
    "danger": [   # an exclamation mark
        "................",
        ".......##.......",
        "......####......",
        "......####......",
        "......####......",
        "......####......",
        ".......##.......",
        ".......##.......",
        ".......##.......",
        "................",
        "......####......",
        "......####......",
        ".......##.......",
        "................",
        "................",
        "................",
    ],
}


def symbol(rows):
    """A symbol: light greys lit from the top-left (# body, O inner highlight), a dark outline round it."""
    img = blank(16)
    filled = {(x, y) for y, row in enumerate(rows) for x, ch in enumerate(row) if ch != "."}
    for (x, y) in filled:
        ch = rows[y][x]
        lit = (x + y) < 14
        img.putpixel((x, y), rgba(GREY[5] if ch == "O" else GREY[4] if lit else GREY[3]))
    for (x, y) in filled:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in filled and 0 <= q[0] < 16 and 0 <= q[1] < 16:
                img.putpixel(q, rgba(GREY[0]))
    return img


# ------------------------------------------------------------------ ground zones (fully coloured, animated)

def edge(x, y, f, wobble=0.6, seed=0):
    """Distance from the centre with a slightly irregular (still crisp) edge that stays put between frames."""
    a = math.atan2(y + 0.5 - C, x + 0.5 - C)
    return dist(x, y) + wobble * math.sin(a * 5 + seed) + wobble * 0.5 * math.sin(a * 9 + seed * 2)


def zone_acid(f):
    """Bubbling acid: a lime pool, darker toward its rim, a lit rim edge, bubbles that swell and pop in turn."""
    gl = hexes("#1d3a10", "#2f6418", "#4f9a22", "#7cc83a", "#b4ec6a", "#e8ffc0")
    img = blank()
    rnd = random.Random(5)
    bubbles = [(rnd.randrange(6, 26), rnd.randrange(6, 26), rnd.randrange(8)) for _ in range(9)]
    for y in range(N):
        for x in range(N):
            d = edge(x, y, f, seed=1)
            if d >= 15.5:
                continue
            if d >= 14.4:
                img.putpixel((x, y), rgba(gl[1]))
                continue
            t = 3 if d < 6 else 2 if d < 11 else 1
            if d >= 13.4 and (x + y) < 30:
                t = 3
            img.putpixel((x, y), rgba(gl[t], 225))
    for (bx, by, phase) in bubbles:
        age = (f + phase) % 8
        if age < 5:
            r = [0.6, 1.1, 1.6, 2.0, 2.2][age]
            for y in range(by - 3, by + 4):
                for x in range(bx - 3, bx + 4):
                    dd = math.hypot(x - bx, y - by)
                    if dd <= r and img.getpixel((x, y))[3]:
                        img.putpixel((x, y), rgba(gl[5] if (x < bx and y < by) else gl[4] if dd > r - 0.9 else gl[3]))
    return img


def zone_web(f):
    """Sticky web: silk strands (spokes and rings) with gaps the floor shows through; a glint runs round the rings."""
    sk = hexes("#5a5a64", "#8c8c96", "#bcbcc4", "#e2e2e8", "#ffffff")
    img = blank()
    for y in range(N):
        for x in range(N):
            d = dist(x, y)
            if d >= 15.5:
                continue
            a = math.degrees(math.atan2(y + 0.5 - C, x + 0.5 - C)) % 360
            spoke = min(a % 45, 45 - a % 45) * math.pi / 180 * d < 0.6
            ring = any(abs(d - r - 0.6 * math.sin(math.radians(a * 8))) < 0.5 for r in (4.0, 8.0, 12.0, 15.0))
            if spoke or ring:
                glint = ring and int(((a + f * 45) % 360) // 45) == 0
                img.putpixel((x, y), rgba(sk[4] if glint else sk[3] if (x + y) < 32 else sk[2]))
            elif d < 2:
                img.putpixel((x, y), rgba(sk[3]))
    return img


def zone_yolk(f):
    """A splash of yolk: a rim of egg white round a glossy yellow pool that wobbles a little."""
    yk = hexes("#7a3c00", "#c26a00", "#f0a010", "#ffd040", "#fff090", "#ffffff")
    wh = hexes("#b8b0a0", "#d8d2c4", "#f0ece2", "#ffffff")
    img = blank()
    for y in range(N):
        for x in range(N):
            d = edge(x, y, f, wobble=0.9, seed=2)
            if d >= 15.5:
                continue
            if d >= 9.5 + 0.5 * math.sin(f * math.pi / 2 + x * 0.4):
                img.putpixel((x, y), rgba(wh[2] if (x + y) < 30 else wh[1]))
            else:
                hl = dist(x, y, 12, 12) < 3.5
                img.putpixel((x, y), rgba(yk[5] if dist(x, y, 12, 12) < 1.6 else yk[4] if hl else yk[3] if d < 6 else yk[2]))
    return img


def zone_fire(f):
    """Burning ground: charred earth with glowing cracks, flames licking up in clusters that flicker in turn."""
    ash, em = RAMPS["ash"], RAMPS["ember"]
    img = blank()
    rnd = random.Random(11)
    flames = [(rnd.randrange(5, 27), rnd.randrange(5, 27), rnd.randrange(4)) for _ in range(10)]
    for y in range(N):
        for x in range(N):
            d = edge(x, y, f, seed=3)
            if d >= 15.5:
                continue
            crack = (x * 7 + y * 3) % 11 == 0 or (x * 3 + y * 5) % 13 == 0
            img.putpixel((x, y), rgba(em[3] if crack and d < 13 else ash[1] if d > 13.5 else ash[0]))
    for (fx, fy, phase) in flames:
        h = [2, 3, 4, 3][(f + phase) % 4]
        for k in range(h):
            for dx in range(-1 + (k > 1), 2 - (k > 1)):
                x, y = fx + dx, fy - k
                if 0 <= x < N and 0 <= y < N and img.getpixel((x, y))[3]:
                    img.putpixel((x, y), rgba(em[5] if k == 0 else em[4] if k < h - 1 else em[3]))
    return img


def zone_poison(f):
    """Poison: a sickly violet-green pool with a slow swirl of brighter fumes through it."""
    pz = hexes("#1e1030", "#3a1f52", "#5a3a6e", "#6f8a3a", "#9fc04a", "#d8f080")
    img = blank()
    for y in range(N):
        for x in range(N):
            d = edge(x, y, f, seed=4)
            if d >= 15.5:
                continue
            a = math.atan2(y + 0.5 - C, x + 0.5 - C)
            swirl = math.sin(a * 3 + d * 0.55 - f * math.pi / 2)
            t = 4 if swirl > 0.75 else 3 if swirl > 0.35 else 2 if d < 13 else 1
            img.putpixel((x, y), rgba(pz[t], 215))
    return img


def zone_frost(f):
    """Frost: a sheet of pale ice with crisp cracks, a glint crossing it."""
    fr = RAMPS["frost"]
    img = blank()
    for y in range(N):
        for x in range(N):
            d = edge(x, y, f, wobble=0.4, seed=5)
            if d >= 15.5:
                continue
            crack = (abs(x - y) < 1 and d < 12) or (abs(x + y - 31) < 1 and 4 < d < 13) or (y == 16 and 8 < d < 14)
            glint = abs((x + y) - (f * 10 + 6)) < 1.2
            t = 5 if glint else 1 if crack else 4 if d < 8 else 3 if d < 13.5 else 2
            img.putpixel((x, y), rgba(fr[min(t, len(fr) - 1)], 230))
    return img


def zone_shadow(f):
    """Shadow: a pool of near-black violet with tendrils of darkness slowly turning in it, a faint violet rim."""
    vi, ink = RAMPS["violet"], RAMPS["ink"]
    img = blank()
    for y in range(N):
        for x in range(N):
            d = edge(x, y, f, wobble=0.8, seed=6)
            if d >= 15.5:
                continue
            a = math.atan2(y + 0.5 - C, x + 0.5 - C)
            tendril = math.sin(a * 4 - d * 0.4 + f * math.pi / 2) > 0.7
            img.putpixel((x, y), rgba(vi[2] if d > 14.2 else vi[1] if tendril else ink[0], 235))
    return img


ZONES = {"acid": zone_acid, "web": zone_web, "yolk": zone_yolk, "fire": zone_fire, "poison": zone_poison,
         "frost": zone_frost, "shadow": zone_shadow}
GLOWING_ZONES = {"acid", "fire"}


# ------------------------------------------------------------------ models

def plane(key, textures, tint=False, light=0):
    """A flat floor plane, 16 units square at the model's centre height, a texture on both faces."""
    m = g.Model(key)
    m.part = True
    t = m.texture("face", textures)
    e = m.box((0, 8, 0), (16, 8, 16), {"up": (t, [0, 0, 16, 16]), "down": (t, [0, 16, 16, 0])}, shade=False, light=light)
    if tint:
        for face in e["faces"].values():
            face["tintindex"] = 0
        m.tinted = True
    return m


def models():
    out = [plane("floor_warning_ring", warning_ring(), tint=True, light=15),
           plane("floor_warning_fill", warning_fill(), tint=True, light=15),
           plane("floor_warning_wedge", wedge(False), tint=True, light=15),
           plane("floor_warning_wedge_fill", wedge(True), tint=True, light=15),
           plane("floor_warning_lane", lane(False), tint=True, light=15),
           plane("floor_warning_lane_fill", lane(True), tint=True, light=15),
           plane("floor_wave", wave_ring(), tint=True, light=15),
           plane("floor_splash", splash(), tint=True, light=15)]
    for name, rows in SYMBOLS.items():
        for row in rows:
            assert len(row) == 16, (name, row)
        out.append(plane(f"floor_mark_{name}", symbol(rows), tint=True, light=15))
    for name, make in ZONES.items():
        out.append(plane(f"floor_zone_{name}", [make(f) for f in range(8 if name in ("acid",) else 4)],
                         light=15 if name in GLOWING_ZONES else 0))
    return out


def save(m):
    g.save(m)
    if getattr(m, "tinted", False):
        open(os.path.join(g.OUT, m.key, "tint.txt"), "w").write("dye\n")


if __name__ == "__main__":
    ms = models()
    for m in ms:
        save(m)
    sheet = Image.new("RGBA", (len(ms) * 100 + 10, 220), (60, 58, 66, 255))
    for i, m in enumerate(ms):
        tex = m.textures["face"]
        img = (tex[0] if isinstance(tex, list) else tex).resize((96, 96), Image.NEAREST)
        sheet.alpha_composite(img, (10 + i * 100, 10))
        if isinstance(tex, list):
            img2 = tex[len(tex) // 2].resize((96, 96), Image.NEAREST)
            sheet.alpha_composite(img2, (10 + i * 100, 115))
    path = os.path.join(g.OUT, "review-o4.png")
    sheet.save(path)
    print(path, len(ms), "models")
