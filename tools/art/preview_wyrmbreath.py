"""Wyrmbreath in action: an animated side-view GIF driven by the real HeldWeapons numbers.

The server loop runs every 2 ticks: 7 FLAME + 4 SMALL_FLAME from the staff tip (gaussian spread 0.13, speed 0.35-0.6),
a LAVA pop + LARGE_SMOKE one call in four, heat +3 per call (overheat at 100 = 3.3 s, then a 3 s lock), a hit every
10 ticks on creatures within 8 blocks and 35 degrees (9 damage, 14-flame burst, 4 s of fire). Particles follow the
vanilla particle classes (RisingParticle friction 0.96, lava gravity, smoke rising), drawn with the vanilla sprites
read straight from the 26.2 client jar (reference only, never shipped).

    python tools/art/preview_wyrmbreath.py [client.jar] [out.gif]
"""
import json
import math
import os
import random
import sys
import zipfile
from io import BytesIO

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ART = os.path.join(ROOT, "docs", "art")

PPB = 32                  # screen px per block (scene resolution)
W, H = 13 * PPB, 7 * PPB  # 416 x 224, upscaled x2
UP = 2
GROUND = H - 48
PLAYER_X = 2.0
EYE = 1.62
FIRE_START, OVERHEAT_TICK, LOCK_TICKS, END = 12, None, 60, 160

rng = random.Random(7)


# ------------------------------------------------------------------ assets

def client_jar():
    if len(sys.argv) > 1 and sys.argv[1].endswith(".jar"):
        return sys.argv[1]
    meta = os.path.join(os.environ.get("APPDATA", ""), ".minecraft", "versions", "26.2", "26.2.jar")
    if os.path.exists(meta):
        return meta
    raise SystemExit("pass the 26.2 client.jar path")


JAR = zipfile.ZipFile(client_jar())


def tex(path):
    return Image.open(BytesIO(JAR.read("assets/minecraft/textures/" + path))).convert("RGBA")


def art(path):
    return Image.open(os.path.join(ART, path)).convert("RGBA")


FLAME = tex("particle/flame.png")
LAVA = tex("particle/lava.png")
SMOKE = [tex(f"particle/big_smoke_{i}.png") for i in range(12)]
GENERIC = [tex(f"particle/generic_{i}.png") for i in range(8)]
FIRE = tex("block/fire_0.png")
FIRE_FRAMES = [FIRE.crop((0, i * 16, 16, i * 16 + 16)) for i in range(FIRE.height // 16)]
STEVE = tex("entity/player/wide/steve.png")
ZOMBIE = tex("entity/zombie/zombie.png")
HUSK = tex("entity/zombie/husk.png")
BRICKS = tex("block/polished_blackstone_bricks.png")
TILES = tex("block/deepslate_tiles.png")
NETHERRACK = tex("block/netherrack.png")
FONT = tex("font/ascii.png")
HOTBAR = tex("gui/sprites/hud/hotbar.png")
SELECTION = tex("gui/sprites/hud/hotbar_selection.png")
ICON = [art(f"session-e/wyrmbreath_{i}.png") for i in range(4)]
METAL = sorted({c for c in art("session-g/wyrmbreath_held_using/metal.png").getdata()}, key=sum)
GRIP = sorted({c for c in art("session-g/wyrmbreath_held_using/grip.png").getdata()}, key=sum)
ORB = [art(f"session-g/wyrmbreath_held_using/orb_{i}.png").crop((3, 3, 13, 13)) for i in range(8)]


def sx(x):
    return x * PPB


def sy(y):
    return GROUND - y * PPB


# ------------------------------------------------------------------ text (the vanilla bitmap font)

def glyph_width(ch):
    if ch == " ":
        return 4
    c = ord(ch)
    gx, gy = (c % 16) * 8, (c // 16) * 8
    for col in range(7, -1, -1):
        if any(FONT.getpixel((gx + col, gy + r))[3] for r in range(8)):
            return col + 2
    return 4


def text_width(runs):
    return sum(glyph_width(ch) for _, s in runs for ch in s)


def draw_text(img, x, y, runs, scale, alpha=1.0):
    """runs: [(rgb, text)]; draws the shadow then the glyphs, like the vanilla font renderer."""
    for shadow in (True, False):
        cx = x
        for rgb, s in runs:
            col = tuple(v // 4 for v in rgb) if shadow else rgb
            for ch in s:
                c = ord(ch)
                if ch != " ":
                    g = FONT.crop(((c % 16) * 8, (c // 16) * 8, (c % 16) * 8 + 8, (c // 16) * 8 + 8))
                    mask = g.split()[3].point(lambda a: int(a * alpha))
                    g = Image.new("RGBA", g.size, col + (255,))
                    g.putalpha(mask)
                    g = g.resize((8 * scale, 8 * scale), Image.NEAREST)
                    off = scale if shadow else 0
                    img.alpha_composite(g, (cx * scale + off, y * scale + off))
                cx += glyph_width(ch)


GOLD, RED, DGRAY, GRAY, WHITE, YELLOW = (255, 170, 0), (255, 85, 85), (85, 85, 85), (170, 170, 170), (255, 255, 255), (255, 255, 85)


# ------------------------------------------------------------------ drawing helpers

def paste_rot(canvas, part, pivot, dest, angle, scale=2):
    """part (skin texels) scaled up, turned angle degrees (counter-clockwise) about pivot, pivot placed at dest."""
    part = part.resize((part.width * scale, part.height * scale), Image.NEAREST)
    px, py = pivot[0] * scale, pivot[1] * scale
    size = int(2 * (max(px, part.width - px) + max(py, part.height - py))) + 2
    pad = Image.new("RGBA", (size, size))
    pad.alpha_composite(part, (int(size / 2 - px), int(size / 2 - py)))
    pad = pad.rotate(angle, Image.NEAREST)
    canvas.alpha_composite(pad, (int(round(dest[0] - size / 2)), int(round(dest[1] - size / 2))))


def tint(img, rgb, amount):
    over = Image.new("RGBA", img.size, rgb + (0,))
    over.putalpha(img.split()[3].point(lambda a: int(a * amount)))
    out = img.copy()
    out.alpha_composite(over)
    return out


def shade(img, f):
    r, g, b, a = img.split()
    return Image.merge("RGBA", [c.point(lambda v: int(v * f)) for c in (r, g, b)] + [a])


def scepter():
    """The in-use Wyrmbreath, pointing right: pommel, wrapped grip, collar, cup, four claws round the ember orb.
    Texels follow the session-g model (1 model px = 1 texel here, turned on its side)."""
    s = Image.new("RGBA", (21, 9))
    d = ImageDraw.Draw(s)
    m0, m1, m2, m3 = METAL
    d.rectangle((0, 3, 1, 5), fill=m1)                       # pommel
    d.point((0, 3), fill=m2)
    for x in range(2, 11):                                   # wrapped grip
        d.line((x, 4, x, 4), fill=GRIP[1] if x % 3 else GRIP[3])
    d.rectangle((11, 3, 12, 5), fill=m2)                     # collar
    d.line((11, 3, 12, 3), fill=m3)
    d.rectangle((13, 2, 13, 6), fill=m1)                     # cup
    d.line((13, 2, 13, 3), fill=m2)
    for y in (1, 7):                                         # claws, hooking over the orb
        d.line((14, y, 18, y), fill=m2 if y == 1 else m0)
        d.point((19, y + (1 if y == 1 else -1)), fill=m3 if y == 1 else m1)
    return s


SCEPTER = scepter()


def orb(frame):
    return ORB[(frame // 2) % 8].resize((5, 5), Image.BOX)


# ------------------------------------------------------------------ particles

class P:
    __slots__ = ("kind", "x", "y", "z", "vx", "vy", "vz", "age", "life", "size", "fric", "grav", "glow", "col")

    def __init__(self, kind, x, y, z, vx, vy, vz, life, size, fric, grav, glow=True, col=None):
        self.kind, self.x, self.y, self.z = kind, x, y, z
        self.vx, self.vy, self.vz = vx, vy, vz
        self.age, self.life, self.size, self.fric, self.grav, self.glow, self.col = 0, life, size, fric, grav, glow, col

    def tick(self):
        self.age += 1
        self.vy -= 0.04 * self.grav
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz
        if self.y < 0.02 and self.kind != "smoke":        # hasPhysics: lands on the floor
            self.y, self.vy = 0.02, 0
            self.vx *= 0.7
            self.vz *= 0.7
        self.vx *= self.fric
        self.vy *= self.fric
        self.vz *= self.fric
        return self.age < self.life


def rising_life():
    return int(8 / (rng.random() * 0.8 + 0.2)) + 4


def flame(x, y, z, vx, vy, vz, small=False):
    q = 0.1 * (rng.random() * 0.5 + 0.5) * 2 * (0.5 if small else 1)
    return P("flame", x, y, z, vx, vy, vz, rising_life(), q, 0.96, 0)


def lava(x, y, z):
    a = rng.uniform(0, math.tau)
    sp = (rng.random() + rng.random() + 1) * 0.15 * 0.4
    q = 0.1 * (rng.random() * 0.5 + 0.5) * 2 * (rng.random() * 2 + 0.2)
    return P("lava", x, y, z, math.cos(a) * sp * 0.8, rng.random() * 0.4 + 0.05, math.sin(a) * sp * 0.8,
             int(16 / (rng.random() * 0.8 + 0.2)), q, 0.999, 0.75)


def smoke(x, y, z, big=True, vx=0.0, vy=0.0, vz=0.0):
    q = 0.1 * (rng.random() * 0.5 + 0.5) * 2 * 0.75 * (2.5 if big else 1)
    g = rng.random() * 0.3 if big else 0.45 + rng.random() * 0.3
    return P("smoke", x, y, z, vx * 0.1, vy * 0.1 + 0.01, vz * 0.1, int(8 / (rng.random() * 0.8 + 0.2) * 2.5), q, 0.96, -0.1,
             glow=False, col=(g, g, g))


def poof(x, y, z):
    g = rng.random() * 0.3 + 0.7
    return P("poof", x, y, z, rng.gauss(0, 0.02) * 2, rng.gauss(0, 0.02) * 2 + 0.03, rng.gauss(0, 0.02) * 2,
             int(16 / (rng.random() * 0.8 + 0.2)) + 2, 0.1 * (rng.random() * 0.5 + 0.5) * 2 * 0.9, 0.9, -0.05,
             glow=False, col=(g, g, g))


def sprite_of(p):
    t = p.age / max(1, p.life)
    if p.kind == "flame":
        return FLAME, p.size * (1 - t * t * 0.5)
    if p.kind == "lava":
        return LAVA, p.size * (1 - t * t)
    if p.kind == "smoke":
        img = SMOKE[min(11, int(t * 12))]
        return tint_gray(img, p.col[0]), p.size * min(1, (p.age + 2) / 8 * 1.6)
    img = GENERIC[max(0, 7 - int(t * 8))]
    return tint_gray(img, p.col[0]), p.size


_gray_cache = {}


def tint_gray(img, g):
    key = (id(img), round(g, 2))
    if key not in _gray_cache:
        _gray_cache[key] = shade(img, g)
    return _gray_cache[key]


def draw_particle(layer, glow, p):
    img, q = sprite_of(p)
    px = max(2, int(round(q * 2 * PPB)))
    spr = img.resize((px, px), Image.NEAREST)
    if p.kind == "lava" and p.age > p.life * 0.6:            # embers cool as they die
        spr = shade(spr, 1 - (p.age / p.life - 0.6) * 1.4)
    pos = (int(round(sx(p.x) - px / 2)), int(round(sy(p.y) - px / 2)))
    layer.alpha_composite(spr, pos)
    if p.glow:
        glow.alpha_composite(spr, pos)


# ------------------------------------------------------------------ mobs

class Mob:
    def __init__(self, skin, x, z, speed):
        self.skin, self.x, self.z, self.speed = skin, x, z, speed
        self.hp, self.hurt, self.kb, self.fire, self.dead_at, self.walk = 20.0, 0, 0.0, 0, None, 0.0

    @property
    def alive(self):
        return self.dead_at is None


def draw_humanoid(canvas, skin, x, t, facing_right, arm_angle, walk, hurt=0.0, fall=0.0, mirror_skin=False,
                  hold=None, legs_still=False):
    """Side view of a player-shaped model. facing_right shows the right-hand side (player); the zombie faces left and
    shows its left side, whose limbs mirror the right-limb texels."""
    feet = (sx(x), GROUND)
    part = Image.new("RGBA", (96, 96))
    cx, base = 48, 88                                       # model feet in the part image
    if facing_right:
        head, body, arm, leg = (0, 8, 8, 16), (16, 20, 20, 32), (40, 20, 44, 32), (0, 20, 4, 32)
        far_arm, far_leg = (48, 52, 52, 64), (16, 52, 20, 64)
        flip = False
    else:
        head, body, arm, leg = (16, 8, 24, 16), (28, 20, 32, 32), (40, 20, 44, 32), (0, 20, 4, 32)
        far_arm, far_leg = arm, leg
        flip = True

    def piece(box, mirrored=False):
        img = skin.crop(box)
        return img.transpose(Image.FLIP_LEFT_RIGHT) if mirrored else img

    swing = 0 if legs_still else math.sin(walk) * 32
    # far limbs first, a touch darker
    paste_rot(part, shade(piece(far_leg, flip), 0.7), (2, 0), (cx, base - 24), -swing)
    paste_rot(part, shade(piece(leg, flip), 1.0), (2, 0), (cx, base - 24), swing)
    far = shade(piece(far_arm, flip), 0.7)
    paste_rot(part, far, (2, 2), (cx, base - 44), arm_angle + (6 if facing_right else -6))
    paste_rot(part, piece(body, flip), (2, 0), (cx, base - 48), 0)
    paste_rot(part, piece(head, False), (4, 8), (cx, base - 48), 0)
    paste_rot(part, piece(arm, flip), (2, 2), (cx, base - 44), arm_angle)
    if hold is not None:
        hold(part, (cx, base - 44), arm_angle)
    if hurt > 0:
        part = tint(part, (255, 0, 0), 0.45 * hurt)
    if fall:
        canvas_rot = part.rotate(fall, Image.NEAREST, center=(cx, base))
        part = canvas_rot
    canvas.alpha_composite(part, (int(feet[0] - cx), int(feet[1] - base)))


def draw_fire(canvas, x, height, frame):
    """The vanilla burning overlay: fire sheets stacked up the body, narrowing as they climb."""
    w = 0.6 * 1.4
    y, i = 0.0, 0
    while y < height * 1.05 and i < 3:
        f = FIRE_FRAMES[(frame + i * 7) % len(FIRE_FRAMES)]
        size = int(w * PPB * (1 - 0.18 * i))
        spr = f.resize((size, size), Image.NEAREST)
        canvas.alpha_composite(spr, (int(sx(x) - size / 2), int(sy(y) - size)))
        y += size / PPB * 0.6
        i += 1


# ------------------------------------------------------------------ scene

def background():
    bg = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(bg)
    top, horizon = (16, 10, 26), (70, 22, 24)
    for yy in range(GROUND):
        t = (yy / GROUND) ** 1.6
        d.line((0, yy, W, yy), fill=tuple(int(a + (b - a) * t) for a, b in zip(top, horizon)) + (255,))
    for (bx, h) in ((0.6, 3.6), (9.4, 4.4), (11.6, 2.8)):      # ruined pillars at the back
        col = shade(TILES, 0.32)
        for k in range(int(math.ceil(h))):
            tile = col.resize((PPB, PPB), Image.NEAREST)
            bg.alpha_composite(tile, (int(sx(bx)), int(sy(k + 1) - 6)))
    for i in range(W // PPB + 1):                              # floor
        bg.alpha_composite(BRICKS.resize((PPB, PPB), Image.NEAREST), (i * PPB, GROUND))
        bg.alpha_composite(shade(NETHERRACK, 0.45).resize((PPB, PPB), Image.NEAREST), (i * PPB, GROUND + PPB))
    rng_bg = random.Random(3)
    for _ in range(40):                                        # a few stars
        d.point((rng_bg.randrange(W), rng_bg.randrange(int(GROUND * 0.55))), fill=(200, 180, 220, rng_bg.randrange(60, 160)))
    return bg


def dashed(d, a, b, col, dash=4):
    (x0, y0), (x1, y1) = a, b
    n = int(math.hypot(x1 - x0, y1 - y0) / dash)
    for i in range(0, n, 2):
        d.line((x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, x0 + (x1 - x0) * (i + 1) / n, y0 + (y1 - y0) * (i + 1) / n),
               fill=col)


def main():
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ART, "previews", "wyrmbreath-in-action.gif")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bg = background()
    mobs = [Mob(HUSK, 10.6, -0.6, 0.055), Mob(ZOMBIE, 8.4, 0.3, 0.06)]
    parts = []
    heat, locked_until, overheat_at, msg_at = 0, -1, None, None
    look_pitch = -6.0                                          # aiming a little down at the mobs
    look = (math.cos(math.radians(look_pitch)), math.sin(math.radians(look_pitch)), 0.0)
    # the orb of the raised scepter (shoulder 1.375 + arm 10 texels + 23 staff texels at 32 px per block)
    b = math.radians(look_pitch)
    mouth = (PLAYER_X + (20 + 23 * math.cos(b)) / PPB, (44 + 23 * math.sin(b)) / PPB, 0.36)
    frames = []

    for t in range(END):
        using = FIRE_START <= t and overheat_at is None
        # ---- server: every 2 ticks
        if t % 2 == 0:
            if not using and heat > 0:
                heat = max(0, heat - 2)
            if using:
                heat += 3
                if heat >= 100:
                    heat, overheat_at, msg_at, using = 100, t, t, False
                    locked_until = t + LOCK_TICKS
                    for _ in range(6):                         # the extinguish hiss: the orb smokes
                        parts.append(smoke(mouth[0] + rng.gauss(0, 0.1), mouth[1] + rng.gauss(0, 0.1), mouth[2], big=False,
                                           vy=0.6))
                else:
                    for i in range(7):
                        v = [look[k] + rng.gauss(0, 1) * 0.13 for k in range(3)]
                        n = math.sqrt(sum(c * c for c in v))
                        v = [c / n for c in v]
                        sp = 0.35 + rng.random() * 0.25
                        parts.append(flame(*mouth, *(c * sp for c in v)))
                        if i % 2 == 0:
                            parts.append(flame(*mouth, *(c * sp * 1.2 for c in v), small=True))
                    if rng.randrange(4) == 0:
                        parts.append(lava(mouth[0] + 2 * look[0], mouth[1] + 2 * look[1], mouth[2]))
                        parts.append(smoke(mouth[0] + 3 * look[0] + rng.gauss(0, 0.2), mouth[1] + 3 * look[1] + rng.gauss(0, 0.2),
                                           rng.gauss(0, 0.2), vx=rng.gauss(0, 1) * 0.01, vy=rng.gauss(0, 1) * 0.01))
                    if t % 10 == 0:
                        for m in mobs:
                            if not m.alive:
                                continue
                            dx, dy = m.x - PLAYER_X, 0.975 - EYE
                            dist = math.hypot(dx, dy)
                            ang = abs(math.degrees(math.atan2(dy, dx)) - look_pitch)
                            if dist <= 8 and ang <= 35:
                                m.hp -= 9
                                m.hurt, m.kb, m.fire = 10, 0.42, 80
                                for _ in range(14):
                                    parts.append(flame(m.x + rng.gauss(0, 0.2), 0.975 + rng.gauss(0, 0.49), m.z + rng.gauss(0, 0.2),
                                                       *(rng.gauss(0, 1) * 0.04 for _ in range(3))))
                                if m.hp <= 0:
                                    m.dead_at = t
        # ---- mobs
        for m in mobs:
            if m.alive:
                if m.x - PLAYER_X > 1.6:
                    m.x -= m.speed
                    m.walk += 0.55
                m.x += m.kb
                m.kb *= 0.6
            else:
                m.x += m.kb
                m.kb *= 0.6
                if t - m.dead_at == 20:
                    for _ in range(20):
                        parts.append(poof(m.x + rng.gauss(0, 0.3), rng.random() * 0.6 + 0.1, m.z + rng.gauss(0, 0.3)))
            m.hurt = max(0, m.hurt - 1)
            m.fire = max(0, m.fire - 1)
        parts = [p for p in parts if p.tick()]

        # ---- render
        f = bg.copy()
        layer = Image.new("RGBA", (W, H))
        glow = Image.new("RGBA", (W, H))
        cone = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(cone, "RGBA")
        if using:                                              # the hit cone (8 blocks, 35 degrees from the eye)
            ex, ey = sx(PLAYER_X), sy(EYE)
            for s in (-35, 35):
                a = math.radians(look_pitch + s)
                end = (ex + math.cos(a) * 8 * PPB, ey - math.sin(a) * 8 * PPB)
                if end[1] > GROUND:                            # clip at the floor
                    k = (GROUND - ey) / (end[1] - ey)
                    end = (ex + (end[0] - ex) * k, GROUND)
                dashed(d, (ex, ey), end, (255, 190, 120, 70))
            box = (ex - 8 * PPB, ey - 8 * PPB, ex + 8 * PPB, ey + 8 * PPB)
            d.arc(box, -(look_pitch + 35), -(look_pitch - 35), fill=(255, 190, 120, 60))
            cone.paste((0, 0, 0, 0), (0, GROUND, W, H))        # nothing below the floor
            f.alpha_composite(cone)

        for m in sorted(mobs, key=lambda m: m.z):
            if not m.alive and t - m.dead_at > 20:
                continue
            fall = 0.0 if m.alive else -min(90, (t - m.dead_at) * 9)
            skin = shade(m.skin, 0.82 if m.z < 0 else 1.0)
            draw_humanoid(f, skin, m.x, t, False, -90, m.walk, hurt=(m.hurt / 10 if m.alive else 1.0), fall=fall)
            if m.fire and fall > -45:
                draw_fire(f, m.x, 1.95, t)
                draw_fire(glow, m.x, 1.95, t)

        arm = 90 if using else 12                              # the SPEAR pose raises the arm straight ahead
        staff_angle = look_pitch if using else 55
        orb_at = []

        def hold(part, shoulder, angle):
            s = SCEPTER.copy()
            s.alpha_composite(orb(t), (14, 2))
            a = math.radians(angle)
            hx, hy = shoulder[0] + math.sin(a) * 20, shoulder[1] + math.cos(a) * 20   # the fist, 10 texels down the arm
            paste_rot(part, s, (5, 4), (hx, hy), staff_angle)                      # gripped at staff texel 5
            b = math.radians(staff_angle)
            orb_at.append((hx + 23 * math.cos(b) + 1 * math.sin(b), hy - 23 * math.sin(b) + 1 * math.cos(b)))

        draw_humanoid(f, STEVE, PLAYER_X, t, True, arm, 0, hold=hold, legs_still=True)
        ox, oy = orb_at[0][0] + sx(PLAYER_X) - 48, orb_at[0][1] + GROUND - 88
        gd = ImageDraw.Draw(glow)
        r = 6 if using else 4
        gd.ellipse((ox - r, oy - r, ox + r, oy + r), fill=(255, 150, 40, 220 if using else 140))

        for p in sorted(parts, key=lambda p: p.z):
            draw_particle(layer, glow, p)
        f.alpha_composite(layer)

        # light: additive bloom of everything that glows
        f = f.resize((W * UP, H * UP), Image.NEAREST)
        bloom = glow.resize((W * UP, H * UP), Image.BILINEAR).filter(ImageFilter.GaussianBlur(14))
        bloom = Image.merge("RGB", [c.point(lambda v: int(v * 0.85)) for c in bloom.split()[:3]])
        bloom = ImageChops.multiply(bloom, Image.new("RGB", bloom.size, (255, 170, 90)))
        f = Image.merge("RGBA", list(ImageChops.add(f.convert("RGB"), bloom).split()) + [Image.new("L", f.size, 255)])

        # ---- HUD (GUI scale 2, vanilla positions)
        gw, gh = W, H
        hb_x, hb_y = (gw - 182) // 2, gh - 22
        f.alpha_composite(HOTBAR.resize((182 * UP, 22 * UP), Image.NEAREST), (hb_x * UP, hb_y * UP))
        f.alpha_composite(SELECTION.resize((SELECTION.width * UP, SELECTION.height * UP), Image.NEAREST), ((hb_x - 1) * UP, (hb_y - 1) * UP))
        icon = ICON[(t // 4) % 4].resize((16 * UP, 16 * UP), Image.NEAREST)
        f.alpha_composite(icon, ((hb_x + 3) * UP, (hb_y + 3) * UP))
        used = (t - FIRE_START) // 20 if t >= FIRE_START else 0
        dur = 1 - (40 + max(0, min(used, 4))) / 1200
        bd = ImageDraw.Draw(f)
        bx, by = (hb_x + 5) * UP, (hb_y + 16) * UP
        bd.rectangle((bx, by, bx + 13 * UP - 1, by + 2 * UP - 1), fill=(0, 0, 0))
        hue_col = (int(255 * (1 - dur) * 2) if dur < 0.5 else int(255 * (1 - dur) * 2), 255, 0)
        bd.rectangle((bx, by, bx + int(13 * dur) * UP - 1, by + UP - 1), fill=(min(255, hue_col[0]), 255, 0))

        if using:
            filled = heat // 10
            runs = [(GOLD, "Heat ")] + [((RED if heat > 70 else GOLD) if i < filled else DGRAY, "|") for i in range(10)]
            draw_text(f, (gw - text_width(runs)) // 2, gh - 68 + 4, runs, UP)
        elif msg_at is not None and t - msg_at < 80:
            alpha = min(1.0, (80 - (t - msg_at)) / 20)
            runs = [(RED, "Wyrmbreath overheated!")]
            draw_text(f, (gw - text_width(runs)) // 2, gh - 68 + 4, runs, UP, alpha)

        # caption (outside the game UI, top left)
        if t < FIRE_START:
            sub = [(GRAY, "hold right-click")]
        elif using:
            sub = [(GRAY, "dragon-fire cone  "), (WHITE, "8 blocks, 35 deg"), (GRAY, "  9 dmg per 0.5s")]
        elif t < locked_until:
            sub = [(RED, "overheated  "), (GRAY, "locked %.1fs" % ((locked_until - t) / 20))]
        else:
            sub = [(GRAY, "cooled down: ready to fire")]
        draw_text(f, 6, 6, [(GOLD, "Wyrmbreath")], UP)
        draw_text(f, 6, 17, sub, UP)
        fade = min(1.0, (t + 1) / 6, (END - t) / 8)              # a short fade each end so the loop is seamless
        rgb = f.convert("RGB")
        frames.append(Image.blend(Image.new("RGB", rgb.size), rgb, fade) if fade < 1 else rgb)

    # one shared palette keeps the fire gradients steady from frame to frame
    sample = Image.new("RGB", (W * UP, H * UP * 4))
    for i, k in enumerate((20, 45, 70, 100)):
        sample.paste(frames[k], (0, H * UP * i))
    pal = sample.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    q = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
    q[0].save(out, save_all=True, append_images=q[1:], duration=50, loop=0, optimize=False, disposal=1)
    print(out, len(q), "frames", os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
