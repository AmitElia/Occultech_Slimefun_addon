"""Held weapons in action: side-view GIFs driven by the plugin's own numbers, one per weapon (Wyrmbreath has its own
script, preview_wyrmbreath.py). The weapon in the hand is its real 3D held model (session g) seen from the side;
mobs, particles, font and HUD are the vanilla 26.2 sprites, read from the client jar (reference only, never shipped).

    python tools/art/preview_held_actions.py client.jar [weapon ...]   -> docs/art/previews/<weapon>-in-action.gif

Numbers per weapon (see the classes): HeldWeapons (Gaze, Censer), AbyssalAnchor, HollowGearListener (Dreadlance),
GearListener (Frenzy Cleaver), BoneScepter + MinionService (Bone Scepter, Lich's Grimoire).
"""
import math
import os
import random
import sys
import zipfile
from io import BytesIO

sys.path.insert(0, os.path.dirname(__file__))
import preview_held_turntables as tt  # noqa: E402
from PIL import Image, ImageChops, ImageDraw, ImageFilter  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ART = os.path.join(ROOT, "docs", "art")
OUT = os.path.join(ART, "previews")

PPB = 32
W, H = 13 * PPB, 7 * PPB
UP = 2
GROUND = H - 48
EYE = 1.62

JAR = None


def tex(path):
    return Image.open(BytesIO(JAR.read("assets/minecraft/textures/" + path))).convert("RGBA")


def art(path):
    return Image.open(os.path.join(ART, path)).convert("RGBA")


def sx(x):
    return x * PPB


def sy(y):
    return GROUND - y * PPB


class A:
    """Vanilla sprites, loaded once the jar is open."""

    @classmethod
    def load(cls):
        p = "particle/"
        cls.FLAME, cls.SOUL_FLAME, cls.LAVA = tex(p + "flame.png"), tex(p + "soul_fire_flame.png"), tex(p + "lava.png")
        cls.SMOKE = [tex(f"{p}big_smoke_{i}.png") for i in range(12)]
        cls.GENERIC = [tex(f"{p}generic_{i}.png") for i in range(8)]
        cls.SOUL = [tex(f"{p}soul_{i}.png") for i in range(11)]
        cls.EFFECT = [tex(f"{p}effect_{i}.png") for i in range(8)]
        cls.CRIT, cls.DAMAGE, cls.ANGRY = tex(p + "critical_hit.png"), tex(p + "damage.png"), tex(p + "angry.png")
        fire = tex("block/fire_0.png")
        cls.FIRE = [fire.crop((0, i * 16, 16, i * 16 + 16)) for i in range(fire.height // 16)]
        water = tex("block/water_still.png")
        cls.WATER = [ImageChops.multiply(water.crop((0, i * 16, 16, i * 16 + 16)), Image.new("RGBA", (16, 16), (63, 118, 228, 255)))
                     for i in range(water.height // 16)]
        e = "entity/"
        cls.STEVE = tex(e + "player/wide/steve.png")
        cls.ZOMBIE, cls.HUSK = tex(e + "zombie/zombie.png"), tex(e + "zombie/husk.png")
        cls.DROWNED, cls.DROWNED_OUTER = tex(e + "zombie/drowned.png"), tex(e + "zombie/drowned_outer_layer.png")
        cls.SKELETON, cls.WITHER = tex(e + "skeleton/skeleton.png"), tex(e + "skeleton/wither_skeleton.png")
        cls.NETHERITE = tex(e + "equipment/humanoid/netherite.png")
        cls.LEATHER = ImageChops.multiply(tex(e + "equipment/humanoid/leather.png"), Image.new("RGBA", (64, 32), (160, 101, 64, 255)))
        cls.ARROW = tex(e + "projectiles/arrow.png")
        cls.BRICKS, cls.TILES = tex("block/polished_blackstone_bricks.png"), tex("block/deepslate_tiles.png")
        cls.NETHERRACK, cls.HEAVY_CORE = tex("block/netherrack.png"), tex("block/heavy_core.png")
        cls.FONT = tex("font/ascii.png")
        h = "gui/sprites/hud/"
        cls.HOTBAR, cls.SELECTION = tex(h + "hotbar.png"), tex(h + "hotbar_selection.png")
        cls.HEART_BOX, cls.HEART, cls.HEART_HALF = tex(h + "heart/container.png"), tex(h + "heart/full.png"), tex(h + "heart/half.png")
        cls.ATK_BG, cls.ATK_FG = tex(h + "hotbar_attack_indicator_background.png"), tex(h + "hotbar_attack_indicator_progress.png")
        cls.NETHERITE_SWORD, cls.IRON_SWORD, cls.BOW = tex("item/netherite_sword.png"), tex("item/iron_sword.png"), tex("item/bow.png")


# ------------------------------------------------------------------ image helpers

def paste_rot(canvas, part, pivot, dest, angle, scale=2, smooth=False):
    """part scaled up, turned angle degrees (counter-clockwise on screen) about pivot, pivot placed at dest."""
    if scale != 1:
        part = part.resize((max(1, int(part.width * scale)), max(1, int(part.height * scale))), Image.NEAREST)
    px, py = pivot[0] * scale, pivot[1] * scale
    size = int(2 * (max(px, part.width - px) + max(py, part.height - py))) + 2
    pad = Image.new("RGBA", (size, size))
    pad.alpha_composite(part, (int(size / 2 - px), int(size / 2 - py)))
    pad = pad.rotate(angle, Image.BICUBIC if smooth else Image.NEAREST)
    canvas.alpha_composite(pad, (int(round(dest[0] - size / 2)), int(round(dest[1] - size / 2))))


def tint(img, rgb, amount):
    over = Image.new("RGBA", img.size, rgb + (0,))
    over.putalpha(img.split()[3].point(lambda a: int(a * amount)))
    out = img.copy()
    out.alpha_composite(over)
    return out


def shade(img, f):
    r, g, b, a = img.split()
    return Image.merge("RGBA", [c.point(lambda v: min(255, int(v * f))) for c in (r, g, b)] + [a])


def colorize(img, rgb):
    """A grey particle sprite in a colour (what the game does with a particle's rCol/gCol/bCol)."""
    return ImageChops.multiply(img, Image.new("RGBA", img.size, tuple(rgb) + (255,)))


# ------------------------------------------------------------------ text (vanilla bitmap font)

GOLD, RED, DGRAY, GRAY, WHITE, AQUA, DAQUA, GREEN = ((255, 170, 0), (255, 85, 85), (85, 85, 85), (170, 170, 170),
                                                     (255, 255, 255), (85, 255, 255), (0, 170, 170), (85, 255, 85))
_gw = {}


def glyph_width(ch):
    if ch == " ":
        return 4
    if ch not in _gw:
        c = ord(ch)
        gx, gy = (c % 16) * 8, (c // 16) * 8
        _gw[ch] = next((col + 2 for col in range(7, -1, -1) if any(A.FONT.getpixel((gx + col, gy + r))[3] for r in range(8))), 4)
    return _gw[ch]


def text_width(runs):
    return sum(glyph_width(ch) for _, s in runs for ch in s)


def draw_text(img, x, y, runs, scale, alpha=1.0, shadow=True):
    for sh in ((True, False) if shadow else (False,)):
        cx = x
        for rgb, s in runs:
            col = tuple(v // 4 for v in rgb) if sh else rgb
            for ch in s:
                c = ord(ch)
                if ch != " ":
                    g = A.FONT.crop(((c % 16) * 8, (c // 16) * 8, (c % 16) * 8 + 8, (c // 16) * 8 + 8))
                    mask = g.split()[3].point(lambda a: int(a * alpha))
                    g = Image.new("RGBA", g.size, col + (255,))
                    g.putalpha(mask)
                    g = g.resize((8 * scale, 8 * scale), Image.NEAREST)
                    off = scale if sh else 0
                    img.alpha_composite(g, (int(cx * scale + off), int(y * scale + off)))
                cx += glyph_width(ch)


# ------------------------------------------------------------------ the held models, seen from the side

def model_sprite(key, grip, s=1.7, yaw=90, pitch=0, using=None):
    """The weapon's held model rendered from the player's right side, tip (or 'ahead') along the model's up/right
    as the turntable stands it; returns (sprite, grip pixel). Supersampled 4x for clean edges."""
    make, pre, *_ = tt.WEAPONS[key]
    model = using() if using else make()
    k = 4
    size = (int(60 * s * k), int(60 * s * k))
    img = tt.render(model, 0, yaw, pitch, s * k, size, (8, 8, 8), pre)
    cy, sy_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    x, y, z = (grip[i] - 8 for i in range(3))
    x, z = x * cy - z * sy_, x * sy_ + z * cy
    y, z = y * cp - z * sp, y * sp + z * cp
    gx, gy = size[0] / 2 + x * s * k, size[1] / 2 - y * s * k
    box = img.getbbox()
    img = img.crop(box)
    out = img.resize((max(1, img.width // k), max(1, img.height // k)), Image.LANCZOS)
    return out, ((gx - box[0]) / k, (gy - box[1]) / k), model


def model_glow_sprite(key, grip, s=1.7, yaw=90, pitch=0, using=None):
    """Only the glowing (light_emission) parts, same frame as model_sprite."""
    make, pre, *_ = tt.WEAPONS[key]
    model = using() if using else make()
    k = 4
    size = (int(60 * s * k), int(60 * s * k))
    full = tt.render(model, 0, yaw, pitch, s * k, size, (8, 8, 8), pre)
    box = full.getbbox()
    img = tt.render(model, 0, yaw, pitch, s * k, size, (8, 8, 8), pre, only_glow=True).crop(box)
    return img.resize((max(1, img.width // k), max(1, img.height // k)), Image.LANCZOS)


# ------------------------------------------------------------------ particles

class P:
    __slots__ = ("x", "y", "z", "vx", "vy", "vz", "age", "life", "size", "fric", "grav", "glow", "frames", "anim", "col",
                 "phys", "fade")

    def __init__(self, x, y, z, vx, vy, vz, life, size, frames, fric=0.96, grav=0.0, glow=False, anim="static", col=None,
                 phys=True, fade=None):
        self.x, self.y, self.z, self.vx, self.vy, self.vz = x, y, z, vx, vy, vz
        self.age, self.life, self.size, self.fric, self.grav = 0, max(1, life), size, fric, grav
        self.glow, self.frames, self.anim, self.col, self.phys, self.fade = glow, frames, anim, col, phys, fade

    def tick(self):
        self.age += 1
        self.vy -= 0.04 * self.grav
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz
        if self.phys and self.y < 0.02:
            self.y, self.vy = 0.02, 0
            self.vx *= 0.7
            self.vz *= 0.7
        self.vx *= self.fric
        self.vy *= self.fric
        self.vz *= self.fric
        return self.age < self.life

    def sprite(self):
        t = self.age / self.life
        n = len(self.frames)
        if self.anim == "age":
            img = self.frames[min(n - 1, int(t * n))]
        elif self.anim == "rev":
            img = self.frames[max(0, n - 1 - int(t * n))]
        else:
            img = self.frames[0]
        size = self.size
        if self.fade == "shrink":
            size *= 1 - t * t * 0.5
        elif self.fade == "lava":
            size *= 1 - t * t
        return img, size


def rq():
    """Particle's default quadSize: 0.1 * (random * 0.5 + 0.5) * 2."""
    return 0.1 * (rng.random() * 0.5 + 0.5) * 2


def rising_life():
    return int(8 / (rng.random() * 0.8 + 0.2)) + 4


def flame(x, y, z, vx, vy, vz, small=False, soul=False):
    return P(x, y, z, vx, vy, vz, rising_life(), rq() * (0.5 if small else 1), [A.SOUL_FLAME if soul else A.FLAME],
             glow=True, fade="shrink")


def lava(x, y, z):
    a = rng.uniform(0, math.tau)
    sp = (rng.random() + rng.random() + 1) * 0.15 * 0.4
    return P(x, y, z, math.cos(a) * sp * 0.8, rng.random() * 0.4 + 0.05, math.sin(a) * sp * 0.8, int(16 / (rng.random() * 0.8 + 0.2)),
             rq() * (rng.random() * 2 + 0.2), [A.LAVA], fric=0.999, grav=0.75, glow=True, fade="lava")


def smoke(x, y, z, big=True, light=False):
    g = 0.45 + rng.random() * 0.3 if light else rng.random() * 0.3
    return P(x, y, z, rng.gauss(0, 0.01), 0.01, rng.gauss(0, 0.01), int(8 / (rng.random() * 0.8 + 0.2) * 2.5),
             rq() * 0.75 * (2.5 if big else 1), [shade(f, g) for f in A.SMOKE], grav=-0.1, anim="age", phys=False)


def poof(x, y, z):
    g = rng.random() * 0.3 + 0.7
    return P(x, y, z, rng.gauss(0, 0.04), rng.gauss(0, 0.04) + 0.03, rng.gauss(0, 0.04), int(16 / (rng.random() * 0.8 + 0.2)) + 2,
             rq() * 0.9, [shade(f, g) for f in A.GENERIC], fric=0.9, grav=-0.05, anim="rev")


def dust(x, y, z, rgb, scale):
    b = rng.random() * 0.4 + 0.6
    col = tuple(int(c * b) for c in rgb)
    life = max(1, int(int(8 / (rng.random() * 0.8 + 0.2)) * scale))
    return P(x, y, z, rng.gauss(0, 0.01), rng.gauss(0, 0.01), rng.gauss(0, 0.01), life, rq() * 0.75 * scale,
             [colorize(f, col) for f in A.GENERIC], anim="rev", glow=True, phys=False)


def soul(x, y, z, vx=0.0, vy=0.0, vz=0.0):
    return P(x, y, z, vx, vy, vz, rising_life(), rq() * 1.5, A.SOUL, glow=True, anim="age")


def crit(x, y, z):
    g = rng.random() * 0.3 + 0.6
    return P(x, y, z, rng.gauss(0, 0.25), rng.gauss(0, 0.25) + 0.1, rng.gauss(0, 0.25), int(6 / (rng.random() * 0.8 + 0.6)),
             rq() * 0.75, [shade(A.CRIT, g)], fric=0.7, grav=0.5, phys=False)


def damage_heart(x, y, z):
    return P(x, y, z, rng.gauss(0, 0.12), 0.18 + rng.random() * 0.1, rng.gauss(0, 0.12), 20, rq() * 0.75 * 1.4, [A.DAMAGE],
             fric=0.7, grav=0.5, phys=False)


def angry(x, y, z):
    return P(x, y, z, 0, 0.02, 0, 16, rq() * 2, [A.ANGRY], fric=0.86, phys=False)


def effect_swirl(x, y, z, rgb):
    return P(x, y, z, rng.gauss(0, 0.01), 0.03 + rng.random() * 0.02, rng.gauss(0, 0.01), int(8 / (rng.random() * 0.8 + 0.2)),
             rq(), [colorize(f, rgb) for f in A.EFFECT], anim="rev", phys=False)


def draw_particle(layer, glow, p):
    img, q = p.sprite()
    px = max(2, int(round(q * 2 * PPB)))
    spr = img.resize((px, px), Image.NEAREST)
    pos = (int(round(sx(p.x) - px / 2)), int(round(sy(p.y) - px / 2)))
    layer.alpha_composite(spr, pos)
    if p.glow:
        glow.alpha_composite(spr, pos)


# ------------------------------------------------------------------ bodies

PLAYER64 = {"head_r": (0, 8, 8, 16), "head_l": (16, 8, 24, 16), "body_r": (16, 20, 20, 32), "body_l": (28, 20, 32, 32),
            "arm": (40, 20, 44, 32), "leg": (0, 20, 4, 32), "far_arm": (32, 52, 36, 64), "far_leg": (16, 52, 20, 64), "w": 4}
MOB64 = dict(PLAYER64, far_arm=(40, 20, 44, 32), far_leg=(0, 20, 4, 32))
SKEL32 = {"head_r": (0, 8, 8, 16), "head_l": (16, 8, 24, 16), "body_r": (16, 20, 20, 32), "body_l": (28, 20, 32, 32),
          "arm": (40, 18, 42, 30), "leg": (0, 18, 2, 30), "far_arm": (40, 18, 42, 30), "far_leg": (0, 18, 2, 30), "w": 2}


def piece(skin, box, flip):
    img = skin.crop(box)
    return img.transpose(Image.FLIP_LEFT_RIGHT) if flip else img


def draw_body(canvas, layout, skin, x, y, facing, near_arm, far_arm, walk=0.0, hurt=0.0, fall=0.0, scale=1.0, hold=None,
              armor=None, outer=None, alpha=1.0, glow_hold=None, glow=None):
    """A player-shaped model from the side, in its own frame facing right (flipped for facing left). Arm angles: 0
    hangs, 90 points ahead. hold(part, hand, arm_angle) draws what the near hand holds."""
    part = Image.new("RGBA", (220, 220))
    cx, base = 110, 160
    left = facing < 0
    w = layout["w"]
    head = layout["head_l" if left else "head_r"]
    body = layout["body_l" if left else "body_r"]
    swing = math.sin(walk) * 32

    def layer_of(sk, box, flip, mirrored_ok=True):
        return piece(sk, box, flip)

    for sk, inflate in ((skin, 0),) + (((outer, 0.5),) if outer else ()):
        f = 0.7
        paste_rot(part, shade(piece(sk, layout["far_leg"], left), f), (w / 2, 0), (cx, base - 24), -swing)
        paste_rot(part, piece(sk, layout["leg"], left), (w / 2, 0), (cx, base - 24), swing)
        paste_rot(part, shade(piece(sk, layout["far_arm"], left), f), (w / 2, 2), (cx, base - 44), far_arm)
        paste_rot(part, piece(sk, body, left), (2, 0), (cx, base - 48), 0)
        paste_rot(part, piece(sk, head, left), (4, 8), (cx, base - 48), 0)
    if armor:
        for sk in armor.get("body", ()):
            b = piece(sk, (28, 20, 32, 32) if left else (16, 20, 20, 32), left).resize((5, 13), Image.NEAREST)
            paste_rot(part, b, (2.5, 0.5), (cx, base - 48), 0)
        for sk in armor.get("head", ()):
            hd = piece(sk, (16, 8, 24, 16) if left else (0, 8, 8, 16), left).resize((10, 10), Image.NEAREST)
            paste_rot(part, hd, (5, 9), (cx, base - 48), 0)
    near = piece(skin, layout["arm"], left)
    paste_rot(part, near, (w / 2, 2), (cx, base - 44), near_arm)
    if outer:
        paste_rot(part, piece(outer, layout["arm"], left), (w / 2, 2), (cx, base - 44), near_arm)
    if armor:
        for sk in armor.get("body", ()):
            a = piece(sk, (40, 20, 44, 32), left).resize((w + 2, 7), Image.NEAREST)
            paste_rot(part, a, ((w + 2) / 2, 3), (cx, base - 44), near_arm)
    a = math.radians(near_arm)
    hand = (cx + math.sin(a) * 20, base - 44 + math.cos(a) * 20)
    hold_glow = None
    if hold is not None:
        hold(part, hand, near_arm)
        if glow_hold is not None:
            hold_glow = Image.new("RGBA", part.size)
            glow_hold(hold_glow, hand, near_arm)
    if hurt > 0:
        part = tint(part, (255, 0, 0), 0.45 * hurt)
    if fall:
        part = part.rotate(fall, Image.NEAREST, center=(cx, base))
    if scale != 1:
        part = part.resize((int(220 * scale), int(220 * scale)), Image.NEAREST)
        cx, base = cx * scale, base * scale
    if left:
        part = part.transpose(Image.FLIP_LEFT_RIGHT)
        cx = part.width - cx
        if hold_glow is not None:
            hold_glow = hold_glow.transpose(Image.FLIP_LEFT_RIGHT)
    if alpha < 1:
        part.putalpha(part.split()[3].point(lambda v: int(v * alpha)))
    pos = (int(sx(x) - cx), int(sy(y) - base))
    canvas.alpha_composite(part, pos)
    if hold_glow is not None and glow is not None:
        glow.alpha_composite(hold_glow, pos)
    return hand


def item_holder(sprite, pivot, angle_of, scale=1):
    """A hold() that draws a sprite gripped at pivot; angle_of(arm_angle) gives its turn."""
    def hold(part, hand, arm):
        paste_rot(part, sprite, pivot, hand, angle_of(arm), scale=scale, smooth=scale == 1)
    return hold


def draw_fire(canvas, x, y, height, frame):
    w = 0.6 * 1.4
    yy, i = 0.0, 0
    while yy < height * 1.05 and i < 3:
        f = A.FIRE[(frame + i * 7) % len(A.FIRE)]
        size = int(w * PPB * (1 - 0.18 * i))
        canvas.alpha_composite(f.resize((size, size), Image.NEAREST), (int(sx(x) - size / 2), int(sy(y + yy) - size)))
        yy += size / PPB * 0.6
        i += 1


def name_tag(img, x, y, runs):
    """A name tag over a mob (on the upscaled frame): the vanilla see-through black plate and its text."""
    tw = text_width(runs)
    cx, cy = sx(x) * UP, sy(y) * UP
    s = 1
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((cx - tw * s / 2 - 1 * s, cy - 1 * s, cx + tw * s / 2, cy + 8 * s), fill=(0, 0, 0, 64))
    draw_text(img, (cx - tw * s / 2) / s, cy / s, runs, s, shadow=False)


# ------------------------------------------------------------------ mobs

class Mob:
    def __init__(self, kind, x, z=0.0, speed=0.05, hp=20, facing=-1, y=0.0):
        self.kind, self.x, self.z, self.y, self.speed, self.hp, self.facing = kind, x, z, y, speed, hp, facing
        self.vx, self.vy, self.walk, self.hurt, self.fire, self.dead_at = 0.0, 0.0, 0.0, 0, 0, None
        self.slow, self.target, self.swing, self.cool, self.gone, self.tag, self.spawned = 0, None, 0, 0, False, None, None
        self.floor = y

    @property
    def alive(self):
        return self.dead_at is None and not self.gone

    def on_ground(self):
        return self.y <= self.floor + 1e-6

    def knockback(self, from_x, strength=0.4):
        d = 1 if self.x >= from_x else -1
        self.vx = self.vx / 2 + d * strength
        if self.on_ground():
            self.vy = min(0.4, self.vy / 2 + 0.4)

    def physics(self, walk_to=None, stop_at=1.2):
        ground = self.on_ground()
        if self.alive and walk_to is not None and ground and abs(self.vx) < 0.15:
            gap = walk_to - self.x
            if abs(gap) > stop_at:
                sp = self.speed * (0.55 if self.slow else 1)
                self.x += sp if gap > 0 else -sp
                self.facing = 1 if gap > 0 else -1
                self.walk += 0.5 * (0.55 if self.slow else 1)
        self.x += self.vx
        self.y += self.vy
        if self.y <= self.floor:
            self.y, self.vy = self.floor, 0.0
        else:
            self.vy = (self.vy - 0.08) * 0.98
        self.vx *= 0.546 if self.on_ground() else 0.91
        self.hurt = max(0, self.hurt - 1)
        self.fire = max(0, self.fire - 1)
        self.slow = max(0, self.slow - 1)
        self.swing = max(0, self.swing - 1)
        self.cool = max(0, self.cool - 1)


KINDS = {   # skin, layout, outer layer, scale, height
    "zombie": ("ZOMBIE", MOB64, None, 1.0, 1.95),
    "husk": ("HUSK", MOB64, None, 1.06, 2.07),
    "drowned": ("DROWNED", MOB64, "DROWNED_OUTER", 1.0, 1.95),
    "skeleton": ("SKELETON", SKEL32, None, 1.0, 1.99),
    "wither": ("WITHER", SKEL32, None, 1.2, 2.4),
}


def draw_mob(f, m, t, glow=None):
    skin_name, layout, outer, scale, height = KINDS[m.kind]
    skin = getattr(A, skin_name)
    if m.z < -0.2:
        skin = shade(skin, 0.8)
    fall = 0.0 if m.dead_at is None else min(90, (t - m.dead_at) * 9) * (1 if m.facing < 0 else -1)
    zombie_arms = m.kind in ("zombie", "husk", "drowned")
    near = far = 90 if zombie_arms else 8
    hold = None
    if m.kind == "skeleton":
        near = far = 80 if m.swing else 10
        hold = item_holder(A.BOW, (8, 8), lambda a: -a + 40, scale=1)
    if m.kind == "wither":
        sw = m.swing / 6
        near = 10 + 130 * math.sin(math.pi * (1 - sw)) if m.swing else 14
        far = 6
        hold = item_holder(A.NETHERITE_SWORD, (3, 13), lambda a: -a + 45, scale=1)
    armor = {"head": [A.NETHERITE], "body": [A.NETHERITE]} if m.kind == "wither" else \
        {"head": [A.LEATHER]} if m.kind == "skeleton" else None
    alpha = 1.0
    if m.spawned is not None and t - m.spawned < 6:
        alpha = (t - m.spawned + 1) / 6
    draw_body(f, layout, skin, m.x, m.y, m.facing, near, far, m.walk, hurt=(m.hurt / 10 if m.dead_at is None else 1.0),
              fall=fall, scale=scale, hold=hold, armor=armor, outer=getattr(A, outer) if outer else None, alpha=alpha)
    if m.fire and fall in (0.0,) or (m.fire and abs(fall) < 45):
        draw_fire(f, m.x, m.y, height, t)
        if glow is not None:
            draw_fire(glow, m.x, m.y, height, t)


def death_puffs(m, t, parts):
    if m.dead_at is not None and t - m.dead_at == 20:
        for _ in range(20):
            parts.append(poof(m.x + rng.gauss(0, 0.3), m.y + rng.random() * 0.6 + 0.1, m.z + rng.gauss(0, 0.3)))
        m.gone = True


# ------------------------------------------------------------------ scene, HUD, output

_bg_cache = {}


def background(pool=None):
    key = pool
    if key in _bg_cache:
        return _bg_cache[key]
    bg = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(bg)
    top, horizon = (16, 10, 26), (70, 22, 24)
    for yy in range(GROUND):
        tt_ = (yy / GROUND) ** 1.6
        d.line((0, yy, W, yy), fill=tuple(int(a + (b - a) * tt_) for a, b in zip(top, horizon)) + (255,))
    rb = random.Random(3)
    for _ in range(40):
        d.point((rb.randrange(W), rb.randrange(int(GROUND * 0.55))), fill=(200, 180, 220, rb.randrange(60, 160)))
    for (bx, h) in ((0.6, 3.6), (9.4, 4.4), (11.6, 2.8)):
        tile = shade(A.TILES, 0.32).resize((PPB, PPB), Image.NEAREST)
        for k in range(int(math.ceil(h))):
            bg.alpha_composite(tile, (int(sx(bx)), int(sy(k + 1) - 6)))
    for i in range(W // PPB + 1):
        in_pool = pool and pool[0] <= i < pool[1]
        if not in_pool:
            bg.alpha_composite(A.BRICKS.resize((PPB, PPB), Image.NEAREST), (i * PPB, GROUND))
        bg.alpha_composite(shade(A.NETHERRACK, 0.45).resize((PPB, PPB), Image.NEAREST), (i * PPB, GROUND + PPB))
        if in_pool:
            d.rectangle((i * PPB, GROUND, i * PPB + PPB - 1, GROUND + PPB - 1), fill=(14, 12, 20, 255))
    _bg_cache[key] = bg
    return bg


def draw_water(f, pool, t):
    for i in range(pool[0], pool[1]):
        wt = shade(A.WATER[(t // 2) % len(A.WATER)], 0.9).resize((PPB, PPB), Image.NEAREST)
        wt.putalpha(wt.split()[3].point(lambda a: int(a * 0.72)))
        f.alpha_composite(wt, (i * PPB, GROUND + 3))


def hud(f, t, icon, durability=1.0, health=None, attack=None, action=None, chat=None):
    gw, gh = W, H
    hb_x, hb_y = (gw - 182) // 2, gh - 22
    f.alpha_composite(A.HOTBAR.resize((182 * UP, 22 * UP), Image.NEAREST), (hb_x * UP, hb_y * UP))
    f.alpha_composite(A.SELECTION.resize((A.SELECTION.width * UP, A.SELECTION.height * UP), Image.NEAREST),
                      ((hb_x - 1) * UP, (hb_y - 1) * UP))
    f.alpha_composite(icon[(t // 4) % len(icon)].resize((16 * UP, 16 * UP), Image.NEAREST), ((hb_x + 3) * UP, (hb_y + 3) * UP))
    bd = ImageDraw.Draw(f)
    bx, by = (hb_x + 5) * UP, (hb_y + 16) * UP
    bd.rectangle((bx, by, bx + 13 * UP - 1, by + 2 * UP - 1), fill=(0, 0, 0))
    bd.rectangle((bx, by, bx + max(1, int(13 * durability)) * UP - 1, by + UP - 1), fill=(int(255 * (1 - durability)), 255, 0))
    if health is not None:
        hp, bounce = health
        for i in range(10):
            x, y = hb_x + i * 8, gh - 39 - (2 if bounce and i == (t // 2) % 10 else 0)
            f.alpha_composite(A.HEART_BOX.resize((9 * UP, 9 * UP), Image.NEAREST), (x * UP, y * UP))
            full = hp - i * 2
            if full >= 2:
                f.alpha_composite(A.HEART.resize((9 * UP, 9 * UP), Image.NEAREST), (x * UP, y * UP))
            elif full >= 1:
                f.alpha_composite(A.HEART_HALF.resize((9 * UP, 9 * UP), Image.NEAREST), (x * UP, y * UP))
    if attack is not None:
        x, y = gw // 2 + 91 + 6, gh - 20
        f.alpha_composite(A.ATK_BG.resize((18 * UP, 18 * UP), Image.NEAREST), (x * UP, y * UP))
        hgt = int(18 * min(1.0, attack))
        if hgt > 0:
            fg = A.ATK_FG.crop((0, 18 - hgt, 18, 18)).resize((18 * UP, hgt * UP), Image.NEAREST)
            f.alpha_composite(fg, (x * UP, (y + 18 - hgt) * UP))
    if action:
        runs, alpha = action
        draw_text(f, (gw - text_width(runs)) // 2, gh - 68 + 4, runs, UP, alpha)
    if chat:
        for i, (runs, alpha) in enumerate(reversed(chat)):
            y = gh - 40 - (i + 1) * 9
            ov = Image.new("RGBA", f.size)
            ImageDraw.Draw(ov).rectangle((0, y * UP, (4 + 320 // 1) * UP // 1, (y + 9) * UP - 1), fill=(0, 0, 0, int(128 * alpha)))
            f.alpha_composite(ov)
            draw_text(f, 2, y + 1, runs, UP, alpha)


def bloom(f, glow, tint_rgb=(255, 170, 90)):
    f = f.resize((W * UP, H * UP), Image.NEAREST)
    b = glow.resize((W * UP, H * UP), Image.BILINEAR).filter(ImageFilter.GaussianBlur(14))
    b = Image.merge("RGB", [c.point(lambda v: int(v * 0.85)) for c in b.split()[:3]])
    b = ImageChops.multiply(b, Image.new("RGB", b.size, tint_rgb))
    return Image.merge("RGBA", list(ImageChops.add(f.convert("RGB"), b).split()) + [Image.new("L", f.size, 255)])


def save_gif(frames, out, end):
    faded = []
    for t, fr in enumerate(frames):
        k = min(1.0, (t + 1) / 6, (end - t) / 8)
        faded.append(Image.blend(Image.new("RGB", fr.size), fr, k) if k < 1 else fr)
    sample = Image.new("RGB", (W * UP, H * UP * 4))
    for i in range(4):
        sample.paste(faded[(i + 1) * len(faded) // 5], (0, H * UP * i))
    pal = sample.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    q = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in faded]
    q[0].save(out, save_all=True, append_images=q[1:], duration=50, loop=0, optimize=False, disposal=1)
    print(out, len(q), "frames", os.path.getsize(out) // 1024, "KB")


def icon(name):
    for d in sorted(os.listdir(ART)):
        p = os.path.join(ART, d, f"{name}_0.png")
        if d.startswith("session-") and os.path.exists(p):
            return [art(f"{d}/{name}_{i}.png") for i in range(4) if os.path.exists(os.path.join(ART, d, f"{name}_{i}.png"))]
    raise FileNotFoundError(name)


rng = random.Random(7)


# ------------------------------------------------------------------ the weapons

class Scene:
    """One weapon's clip. step() runs the server side each tick, world() draws extra things (beams, chains),
    player() poses the wielder, overlay() adds HUD and caption."""
    key, title, end, pool, tint = None, None, 160, None, (255, 170, 90)
    player_x = 2.0

    def __init__(self):
        self.parts, self.mobs, self.t = [], [], 0
        self.action, self.action_at, self.chat = None, None, []

    def say(self, runs):
        self.action, self.action_at = runs, self.t

    def tell(self, runs):
        self.chat.append((runs, self.t))

    def action_hud(self):
        if self.action is None or self.t - self.action_at >= 80:
            return None
        return self.action, min(1.0, (80 - (self.t - self.action_at)) / 20)

    def chat_hud(self):
        return [(r, min(1.0, (200 - (self.t - at)) / 20)) for r, at in self.chat if self.t - at < 200]

    def hit(self, m, dmg, from_x, kb=0.4):
        m.hp -= dmg
        m.hurt = 10
        m.knockback(from_x, kb)
        if m.hp <= 0 and m.dead_at is None:
            m.dead_at = self.t

    def caption(self):
        return [(GRAY, "")]

    def run(self):
        frames = []
        for t in range(self.end):
            self.t = t
            self.step(t)
            for m in self.mobs:
                death_puffs(m, t, self.parts)
            self.parts = [p for p in self.parts if p.tick()]
            f = background(self.pool).copy()
            glow = Image.new("RGBA", (W, H))
            self.world_back(f, glow)
            for m in sorted(self.mobs, key=lambda m: m.z):
                if not m.gone:
                    draw_mob(f, m, t, glow)
            self.player(f, glow)
            layer = Image.new("RGBA", (W, H))
            for p in sorted(self.parts, key=lambda p: p.z):
                draw_particle(layer, glow, p)
            f.alpha_composite(layer)
            self.world_front(f, glow)
            if self.pool:
                draw_water(f, self.pool, t)
            f = bloom(f, glow, self.tint)
            self.overlay(f)
            placed = []                                      # stack tags that would overlap (side view only)
            for m in sorted((m for m in self.mobs if m.tag and not m.gone and m.dead_at is None), key=lambda m: m.x):
                y = m.y + KINDS[m.kind][4] + 0.25
                while any(abs(px - m.x) < 1.9 and abs(py - y) < 0.25 for px, py in placed):
                    y += 0.3
                placed.append((m.x, y))
                name_tag(f, m.x, y, m.tag)
            draw_text(f, 6, 6, [(GOLD, self.title)], UP)
            draw_text(f, 6, 17, self.caption(), UP)
            frames.append(f.convert("RGB"))
        out = os.path.join(OUT, f"{self.key.replace('_', '-')}-in-action.gif")
        save_gif(frames, out, self.end)
        return out

    def world_back(self, f, glow):
        pass

    def world_front(self, f, glow):
        pass


def staff_tip(px, pitch, reach, drop=0.35):
    return (px + reach * math.cos(math.radians(pitch)), EYE - drop + reach * math.sin(math.radians(pitch)), 0.36)


class Gaze(Scene):
    """Guardian's Gaze (HeldWeapons.gaze): hold use; locks a teal beam (DUST 90,220,210 size 0.9, every 0.4 blocks, every
    2 ticks) on the creature nearest the crosshair (6 degree aim assist + its half width, 40 blocks, line of sight).
    Every 10 ticks of lock: min(10, 3 + held/20) damage, 'Gaze N dmg' on the action bar. A dead target unlocks; the
    next call locks the next one and the ramp starts over."""
    key, title, end, tint = "guardians_gaze", "Guardian's Gaze", 170, (90, 230, 215)
    START, STOP, PITCH = 12, 150, -6.0

    def __init__(self):
        super().__init__()
        self.mobs = [Mob("husk", 10.4, -0.4, 0.03), Mob("zombie", 7.6, 0.3, 0.035)]
        self.target, self.held, self.locks = None, 0, 0
        self.sprite, self.pivot, _ = model_sprite("guardians_gaze", (8, 3.2, 8), using=lambda: tt.g.guardians_gaze_held(True))
        self.idle, self.idle_pivot, _ = model_sprite("guardians_gaze", (8, 3.2, 8))
        self.icon = icon("guardians_gaze")

    def using(self, t):
        return self.START <= t < self.STOP

    def aimed(self):
        best, best_a = None, 6.0
        for m in self.mobs:
            if not m.alive:
                continue
            dx, dy = m.x - self.player_x, m.y + 0.975 - EYE
            dist = math.hypot(dx, dy)
            allow = math.degrees(math.atan(0.3 / dist))
            a = abs(math.degrees(math.atan2(dy, dx)) - self.PITCH) - allow
            if a < best_a:
                best, best_a = m, a
        return best

    def step(self, t):
        for m in self.mobs:
            m.physics(self.player_x + 1.6)
        if not self.using(t) or t % 2:
            if not self.using(t):
                self.target = None
            return
        if self.target is not None and not self.target.alive:
            self.target, self.held = None, 0
        if self.target is None:
            self.target = self.aimed()
            if self.target is not None:
                self.locks += 1
        tip = staff_tip(self.player_x, self.PITCH, 1.3)
        if self.target is None:
            end = (self.player_x + 16, EYE + 16 * math.tan(math.radians(self.PITCH)))
        else:
            self.held += 2
            end = (self.target.x, self.target.y + 0.975)
            if self.held % 10 == 0:
                dmg = min(10, 3 + self.held / 20)
                self.hit(self.target, dmg, self.player_x)
                self.say([(AQUA, "Gaze "), (WHITE, "%d dmg" % math.floor(dmg + 0.5))])   # Java's %.0f rounds half up
        n = int(math.hypot(end[0] - tip[0], end[1] - tip[1]) / 0.4)
        for i in range(n):
            k = i / max(1, n)
            self.parts.append(dust(tip[0] + (end[0] - tip[0]) * k, tip[1] + (end[1] - tip[1]) * k, 0.3, (90, 220, 210), 0.9))

    def player(self, f, glow):
        u = self.using(self.t)
        if u:
            hold = item_holder(self.sprite, self.pivot, lambda a: -90 - self.PITCH, scale=1)
        else:
            hold = item_holder(self.idle, self.idle_pivot, lambda a: -45, scale=1)
        draw_body(f, PLAYER64, A.STEVE, self.player_x, 0, 1, 90 if u else 12, 6, hold=hold)

    def overlay(self, f):
        hud(f, self.t, self.icon, 0.97, action=self.action_hud())

    def caption(self):
        t = self.t
        if t < self.START:
            return [(GRAY, "hold right-click")]
        if not self.using(t):
            return [(GRAY, "released: the lock breaks")]
        if self.target is None:
            return [(GRAY, "no target: the beam runs to the first block")]
        ramp = min(10, 3 + self.held / 20)
        return [(GRAY, "locked on" + (" (next target)" if self.locks > 1 else "") + "  "), (WHITE, "%.1f dmg" % ramp),
                (GRAY, " per 0.5s, ramps to 10")]


class Censer(Scene):
    """Soulfire Censer (HeldWeapons.breathe, censer): blue SOUL_FIRE_FLAME from the censer hanging under the raised
    hand (staffTip 0.8, 0.5 lower), speed x1.4; 9 blocks, 30 degrees, 10 damage every 0.5s and 4s of fire; heat +2 per
    2 ticks, so 5s of fire before it overheats and locks for 3s."""
    key, title, end, tint = "soulfire_censer", "Soulfire Censer", 190, (90, 200, 255)
    START, PITCH = 12, -5.0

    def __init__(self):
        super().__init__()
        self.mobs = [Mob("zombie", 7.4, 0.2, 0.06), Mob("husk", 9.6, -0.5, 0.055), Mob("zombie", 12.6, 0.4, 0.06),
                     Mob("husk", 14.4, -0.3, 0.06)]
        self.heat, self.over, self.locked = 0, None, -1
        self.sprite, self.pivot, _ = model_sprite("soulfire_censer", (8, 8, 9.5), using=lambda: tt.g.soulfire_censer_held(True))
        self.glow_sprite = model_glow_sprite("soulfire_censer", (8, 8, 9.5), using=lambda: tt.g.soulfire_censer_held(True))
        self.icon = icon("soulfire_censer")

    def using(self, t):
        return t >= self.START and self.over is None

    def step(self, t):
        for m in self.mobs:
            m.physics(self.player_x + 1.6)
        if t % 2:
            return
        if not self.using(t):
            self.heat = max(0, self.heat - 2)
            return
        self.heat += 2
        if self.heat >= 100:
            self.heat, self.over, self.locked = 100, t, t + 60
            self.say([(RED, "The Censer overheated!")])
            return
        filled = self.heat // 10
        self.say([(GOLD, "Heat ")] + [((RED if self.heat > 70 else GOLD) if i < filled else DGRAY, "|") for i in range(10)])
        look = (math.cos(math.radians(self.PITCH)), math.sin(math.radians(self.PITCH)), 0.0)
        mouth = staff_tip(self.player_x, self.PITCH, 0.8, drop=0.85)
        for i in range(7):
            v = [look[k] + rng.gauss(0, 1) * 0.13 for k in range(3)]
            n = math.sqrt(sum(c * c for c in v))
            sp = (0.35 + rng.random() * 0.25) * 1.4
            v = [c / n * sp for c in v]
            self.parts.append(flame(*mouth, *v, soul=True))
            if i % 2 == 0:
                self.parts.append(flame(*mouth, *(c * 1.2 for c in v), small=True, soul=True))
        if rng.randrange(4) == 0:
            self.parts.append(lava(mouth[0] + 2 * look[0], mouth[1] + 2 * look[1], mouth[2]))
            self.parts.append(smoke(mouth[0] + 3 * look[0] + rng.gauss(0, 0.2), mouth[1] + 3 * look[1] + rng.gauss(0, 0.2), rng.gauss(0, 0.2)))
        if t % 10 == 0:
            for m in self.mobs:
                if not m.alive:
                    continue
                dx, dy = m.x - self.player_x, m.y + 0.975 - EYE
                if math.hypot(dx, dy) <= 9 and abs(math.degrees(math.atan2(dy, dx)) - self.PITCH) <= 30:
                    self.hit(m, 10, self.player_x)
                    m.fire = 80
                    for _ in range(14):
                        self.parts.append(flame(m.x + rng.gauss(0, 0.2), 0.975 + rng.gauss(0, 0.49), m.z + rng.gauss(0, 0.2),
                                                *(rng.gauss(0, 1) * 0.04 for _ in range(3)), soul=True))

    def player(self, f, glow):
        u = self.using(self.t)
        hold = item_holder(self.sprite, self.pivot, lambda a: 0, scale=1)
        gh = item_holder(self.glow_sprite, self.pivot, lambda a: 0, scale=1)
        draw_body(f, PLAYER64, A.STEVE, self.player_x, 0, 1, 90 if u else 25, 6, hold=hold, glow_hold=gh, glow=glow)

    def overlay(self, f):
        hud(f, self.t, self.icon, 0.98, action=self.action_hud())

    def caption(self):
        t = self.t
        if t < self.START:
            return [(GRAY, "hold right-click")]
        if self.using(t):
            return [(GRAY, "soul-fire cone  "), (WHITE, "9 blocks, 30 deg"), (GRAY, "  10 dmg per 0.5s, 5s of fire")]
        if t < self.locked:
            return [(RED, "overheated  "), (GRAY, "locked %.1fs" % ((self.locked - t) / 20))]
        return [(GRAY, "cooled down: ready to burn")]


class Anchor(Scene):
    """Abyssal Anchor (AbyssalAnchor): right-click hurls a HEAVY_CORE display (scale 0.7) at 1.5 blocks/tick for 12
    ticks, a grey DUST chain (70,80,90, size 0.8, every 0.5 block) back to the hand. The first creature within 1.2
    blocks is yanked: velocity min(2.2, 0.25 x distance) toward you and up 0.35, Slowness II for 3s, 8 damage (x1.3 when
    wet) - whose own knockback halves the yank - and 15 CRIT. 4s cooldown."""
    key, title, end, pool, tint = "abyssal_anchor", "Abyssal Anchor", 205, (10, 13), (90, 230, 215)
    THROWS = (14, 122)
    MELEE = (86,)             # a netherite axe up close: 10 damage, x1.5 as a falling (jump) crit
    JUMP = 78         # a netherite axe up close: 10 damage, one swing a second

    def __init__(self):
        super().__init__()
        self.mobs = [Mob("zombie", 9.0, 0.2, 0.05), Mob("drowned", 11.5, -0.2, 0.0, y=-1.0)]
        self.mobs[1].floor = -1.0
        self.anchor, self.cool_until, self.swing_at, self.last = None, -1, -99, None
        self.py, self.pvy = 0.0, 0.0
        self.sprite, self.pivot, _ = model_sprite("abyssal_anchor", (8, -6.5, 8), yaw=0)
        self.glow_sprite = model_glow_sprite("abyssal_anchor", (8, -6.5, 8), yaw=0)
        self.core = A.HEAVY_CORE.crop(A.HEAVY_CORE.getbbox())
        self.icon = icon("abyssal_anchor")

    def hand(self):
        return (self.player_x + 0.3, EYE - 0.3)

    def step(self, t):
        z, d = self.mobs
        z.physics(self.player_x + 1.4)
        if d.alive and d.on_ground() and d.x > 12.5:
            d.floor = 0.0
        if d.alive and d.x < 10 or d.x > 13:
            d.floor = 0.0
        d.physics(self.player_x + 1.4 if d.floor == 0.0 else None)
        for m in self.mobs:
            if m.slow and t % 3 == 0 and m.alive:
                self.parts.append(effect_swirl(m.x + rng.gauss(0, 0.25), m.y + rng.random() * 1.8, m.z, (139, 175, 224)))
        if t == self.JUMP:
            self.pvy = 0.42
        self.py += self.pvy
        if self.py <= 0:
            self.py, self.pvy = 0.0, 0.0
        else:
            self.pvy = (self.pvy - 0.08) * 0.98
        if t in self.MELEE:
            self.swing_at = t
            if z.alive and z.x - self.player_x < 3.6:
                crit_hit = self.pvy < 0
                self.hit(z, 15 if crit_hit else 10, self.player_x)
                for _ in range(7):
                    self.parts.append(damage_heart(z.x, z.y + 1.0, z.z + 0.3))
                if crit_hit:
                    for _ in range(14):
                        self.parts.append(crit(z.x + rng.gauss(0, 0.3), z.y + 1 + rng.gauss(0, 0.4), z.z + rng.gauss(0, 0.3)))
        if t in self.THROWS:
            target = next((m for m in self.mobs if m.alive and (m.kind == "drowned") == (t == self.THROWS[1])), None)
            sx0, sy0 = self.player_x, EYE - 0.3
            tx, ty = (target.x, target.y + 1.0) if target else (self.player_x + 10, 0.8)
            ang = math.atan2(ty - sy0, tx - sx0)
            self.anchor = {"x": sx0, "y": sy0, "vx": 1.5 * math.cos(ang), "vy": 1.5 * math.sin(ang), "ticks": 0}
            self.swing_at, self.cool_until = t, t + 80
        a = self.anchor
        if a is not None:
            a["ticks"] += 1
            if a["ticks"] > 12:
                self.anchor = None
                return
            a["x"] += a["vx"]
            a["y"] += a["vy"]
            hx, hy = self.hand()
            n = int(math.hypot(a["x"] - hx, a["y"] - hy) / 0.5)
            for i in range(n):
                k = i / max(1, n)
                self.parts.append(dust(hx + (a["x"] - hx) * k, hy + (a["y"] - hy) * k, 0.3, (70, 80, 90), 0.8))
            for m in self.mobs:
                if m.alive and abs(m.x - a["x"]) < 1.5 and m.y - 1.2 < a["y"] < m.y + KINDS[m.kind][4] + 1.2:
                    dist = abs(self.player_x - m.x)
                    wet = m.kind == "drowned"
                    if wet:
                        m.floor = -1.0
                    m.vx = -min(2.2, 0.25 * dist)
                    m.vy = 0.35
                    m.slow = 60
                    dmg = 8 * (1.3 if wet else 1)
                    self.hit(m, dmg, self.player_x)
                    if wet:
                        m.floor = 0.0 if m.x < 10 else -1.0
                    for _ in range(15):
                        self.parts.append(crit(m.x + rng.gauss(0, 0.3), m.y + 1 + rng.gauss(0, 0.4), m.z + rng.gauss(0, 0.3)))
                    self.last = (wet, dmg, t)
                    self.anchor = None
                    break

    def world_front(self, f, glow):
        a = self.anchor
        if a is not None:
            s = int(0.7 * 0.5 * PPB)
            img = self.core.resize((s, s), Image.NEAREST)
            f.alpha_composite(img, (int(sx(a["x"]) - s / 2), int(sy(a["y"]) - s / 2)))

    def player(self, f, glow):
        dt = self.t - self.swing_at
        arm = 18
        if 0 <= dt < 6:
            arm = 20 + 120 * math.sin(math.pi * (1 - dt / 6))
        hold = item_holder(self.sprite, self.pivot, lambda a: -a + 40 - 45, scale=1)
        gh = item_holder(self.glow_sprite, self.pivot, lambda a: -a + 40 - 45, scale=1)
        if self.anchor is not None:
            hold = gh = None
        draw_body(f, PLAYER64, A.STEVE, self.player_x, self.py, 1, arm, 6, hold=hold, glow_hold=gh, glow=glow)

    def overlay(self, f):
        hud(f, self.t, self.icon, 0.99)

    def caption(self):
        t = self.t
        if t < self.THROWS[0]:
            return [(GRAY, "right-click: hurl the spectral anchor")]
        if self.anchor is not None:
            return [(GRAY, "18 blocks of chain: the first creature it touches...")]
        if self.last and t - self.last[2] < 50:
            wet, dmg, _ = self.last
            return [(GRAY, "...is dragged to you, slowed  "), (WHITE, "%.1f dmg" % dmg), (AQUA if wet else GRAY, "  wet: x1.3" if wet else "")]
        if self.JUMP <= t < self.MELEE[0] + 14:
            return [(GRAY, "up close it is a heavy axe  "), (WHITE, "jump crit")]
        if t < self.cool_until:
            return [(GRAY, "cooldown %.1fs" % ((self.cool_until - t) / 20))]
        return [(GRAY, "ready")]


class Dreadlance(Scene):
    """Dreadlance (HollowGearListener.onLanceHit): a vanilla netherite spear - jabs, and a charge held at a run - whose
    every hit heals 15% of the damage dealt, at most 4 health a second, with 6 crimson DUST (170,0,20) on the target.
    The spear's own damage is vanilla's; the hits here are illustrative."""
    key, title, end, tint = "dreadlance", "Dreadlance", 170, (200, 40, 60)
    JABS, CHARGE = (16, 34, 52), (80, 118)

    def __init__(self):
        super().__init__()
        self.mobs = [Mob("zombie", 4.6, 0.2, 0.03), Mob("husk", 8.0, -0.3, 0.03), Mob("zombie", 9.6, 0.4, 0.03)]
        self.health, self.window, self.healed_at, self.last_heal, self.capped = 9.0, [0, 0.0], -99, 0.0, False
        self.sprite, self.pivot, _ = model_sprite("dreadlance", (8, 2, 8), s=2.0)
        self.glow_sprite = model_glow_sprite("dreadlance", (8, 2, 8), s=2.0)
        self.icon = icon("dreadlance")
        self.hit_this_charge = set()

    def heal_from(self, dmg, m):
        sec = self.t // 20
        if self.window[0] != sec:
            self.window = [sec, 0.0]
        heal = min(dmg * 0.15, 4 - self.window[1])
        self.capped = heal < dmg * 0.15 - 1e-9
        if heal <= 0:
            return
        self.window[1] += heal
        self.health = min(20, self.health + heal)
        self.healed_at, self.last_heal = self.t, heal
        for _ in range(6):
            self.parts.append(dust(m.x + rng.gauss(0, 0.3), m.y + 1 + rng.gauss(0, 0.4), m.z + rng.gauss(0, 0.3), (170, 0, 20), 1.0))

    def charging(self):
        return self.CHARGE[0] <= self.t < self.CHARGE[1]

    def step(self, t):
        for m in self.mobs:
            m.physics(self.player_x + 1.4)
        if self.charging():
            self.player_x = min(9.5, self.player_x + 0.16)
        elif t >= self.CHARGE[1] and self.player_x > 2.0 and t < self.CHARGE[1] + 30:
            pass
        if t in self.JABS:
            m = next((m for m in self.mobs if m.alive and abs(m.x - self.player_x) < 3.5), None)
            if m:
                self.hit(m, 8, self.player_x)
                self.heal_from(8, m)
        if self.charging():
            for m in self.mobs:
                if m.alive and id(m) not in self.hit_this_charge and abs(m.x - (self.player_x + 1.8)) < 0.5:
                    self.hit_this_charge.add(id(m))
                    self.hit(m, 14, self.player_x, kb=0.9)
                    self.heal_from(14, m)

    def player(self, f, glow):
        dt = min((self.t - j for j in self.JABS if self.t >= j), default=99)
        if self.charging():
            arm, r = 90, -90
        elif dt < 6:
            arm = 70 + 25 * math.sin(math.pi * dt / 6)
            r = -90
        else:
            arm, r = 14, -20
        hold = item_holder(self.sprite, self.pivot, lambda a: r, scale=1)
        gh = item_holder(self.glow_sprite, self.pivot, lambda a: r, scale=1)
        walk = self.t * 0.7 if self.charging() else 0
        draw_body(f, PLAYER64, A.STEVE, self.player_x, 0, 1, arm, 6, walk=walk, hold=hold, glow_hold=gh, glow=glow)

    def overlay(self, f):
        hud(f, self.t, self.icon, 0.99, health=(self.health, self.t - self.healed_at < 8))

    def caption(self):
        if self.t - self.healed_at < 25 and self.healed_at > 0:
            if self.capped:
                return [(GRAY, "lifesteal "), (RED, "capped"), (GRAY, ": at most 4 health a second")]
            return [(GRAY, "every hit heals "), (RED, "15%"), (GRAY, " of the damage  "), (WHITE, "+%.1f" % self.last_heal)]
        if self.charging():
            return [(GRAY, "hold right-click and run: a charged lunge")]
        return [(GRAY, "a spear that drinks: jab, then charge")]


class Cleaver(Scene):
    """Frenzy Cleaver (GearListener.onCleaverHit): a diamond axe (9 damage, attack speed 1.0) where each hit within 3s
    of the last adds +0.2 attack speed, up to 5 stacks (2.0); at 5 an ANGRY_VILLAGER puffs over your head; the stacks
    drop 3s after the last hit. The player swings as soon as the attack indicator is full."""
    key, title, end, tint = "frenzy_cleaver", "Frenzy Cleaver", 280, (255, 120, 80)

    def __init__(self):
        super().__init__()
        self.mobs = [Mob("zombie", 4.6 + i * 1.5, (0.3, -0.3)[i % 2], 0.1) for i in range(3)]
        self.walk = 0.0
        self.stack, self.last_hit, self.charge, self.swing_at = 0, -99, 1.0, -99
        self.sprite, self.pivot, _ = model_sprite("frenzy_cleaver", (8, 0.5, 8), yaw=0)
        self.icon = icon("frenzy_cleaver")

    def speed(self):
        return 1.0 + 0.2 * self.stack

    def step(self, t):
        front = self.player_x + 1.0                      # they queue up behind each other
        for m in sorted(self.mobs, key=lambda m: m.x):
            m.physics(front, stop_at=0.05)
            if m.alive:
                front = max(front, m.x) + 0.75
        if t - self.last_hit > 60 and self.stack:
            self.stack = 0
        self.charge = min(1.0, self.charge + self.speed() / 20)
        target = next((m for m in self.mobs if m.alive and m.x - self.player_x < 2.6), None)
        ahead = [m for m in self.mobs if m.alive]
        if target is None and ahead and t > 10 and self.player_x < 4.2:   # step in after a knocked-back target
            self.player_x += 0.2
            self.walk += 0.6
        if target and self.charge >= 1.0 and t > 10:
            self.charge, self.swing_at = 0.0, t
            self.hit(target, 9, self.player_x)
            for _ in range(4):
                self.parts.append(damage_heart(target.x, target.y + 1.0, target.z + 0.3))
            self.stack = min(5, self.stack + 1) if t - self.last_hit <= 60 else 1
            self.last_hit = t
            if self.stack == 5:
                self.parts.append(angry(self.player_x, 2.15, 0.3))

    def player(self, f, glow):
        dt = self.t - self.swing_at
        arm = 16
        if 0 <= dt < 6:
            arm = 10 + 140 * math.sin(math.pi * (1 - dt / 6)) * (1 - dt / 8)
        hold = item_holder(self.sprite, self.pivot, lambda a: -a, scale=1)
        draw_body(f, PLAYER64, A.STEVE, self.player_x, 0, 1, arm, 6, walk=self.walk, hold=hold)

    def overlay(self, f):
        hud(f, self.t, self.icon, 0.97, attack=self.charge)

    def caption(self):
        if self.stack == 0:
            if self.t > 60:
                return [(GRAY, "3s without a hit: the frenzy fades")]
            return [(GRAY, "chain your hits")]
        return [(RED if self.stack == 5 else GOLD, "Frenzy %d/5" % self.stack), (GRAY, "  attack speed "),
                (WHITE, "%.1f" % self.speed()), (GRAY, " (+0.2 a stack, 3s window)")]


class Necromancy(Scene):
    player_x = 3.0
    """Bone Scepter / Lich's Grimoire (BoneScepter + MinionService): right-click raises minions 1.5 blocks around you,
    20 SOUL particles each. Scepter: 2 skeleton archers for 30s, 20s cooldown ('The bones need Ns more to settle.').
    Grimoire: up to 4 Hollow Knights (wither skeletons in netherite, 80 health, 20 attack) that stay; using it again
    sends them back ('Your knights return to the dark.')."""

    def raise_minions(self, kind, n, tag):
        angles = [0.3, 2.8, 1.1, 2.0][:n]                   # spread round you, so the side view doesn't stack them
        for i in range(n):
            a = angles[i] + rng.uniform(-0.2, 0.2)
            m = Mob(kind, self.player_x + math.cos(a) * 1.5, math.sin(a) * 1.5 * 0.5, 0.09 if kind == "wither" else 0.06,
                    hp=80 if kind == "wither" else 20, facing=1)
            m.spawned, m.tag = self.t, tag
            self.mobs.append(m)
            for _ in range(20):
                self.parts.append(soul(m.x + rng.gauss(0, 0.3), 1 + rng.gauss(0, 0.6), m.z + rng.gauss(0, 0.3),
                                       *(rng.gauss(0, 1) * 0.02 for _ in range(3))))
        self.swing_at = self.t

    def enemies(self):
        return [m for m in self.mobs if m.alive and m.kind in ("zombie", "husk")]

    def minions(self):
        return [m for m in self.mobs if m.alive and m.kind in ("skeleton", "wither")]


class BoneScepter(Necromancy):
    key, title, end, tint = "bone_scepter", "Bone Scepter", 220, (120, 255, 90)
    USE, AGAIN = 14, 170

    def __init__(self):
        super().__init__()
        self.mobs = [Mob("zombie", 10.5, 0.2, 0.035), Mob("husk", 12.6, -0.3, 0.035), Mob("zombie", 14.0, 0.0, 0.035)]
        self.arrows, self.swing_at = [], -99
        self.sprite, self.pivot, _ = model_sprite("bone_scepter", (8, 2, 8))
        self.glow_sprite = model_glow_sprite("bone_scepter", (8, 2, 8))
        self.icon = icon("bone_scepter")

    def step(self, t):
        if t == self.USE:
            self.raise_minions("skeleton", 2, [(GRAY, "Steve's Bound Skeleton")])
        if t == self.AGAIN:
            self.swing_at = t
            self.tell([(GRAY, "The bones need %ds more to settle." % ((20 * 20 - (t - self.USE)) // 20 + 1))])
        enemies = self.enemies()
        for m in self.mobs:
            if m.kind in ("zombie", "husk"):
                m.physics(self.player_x + 2.2)
            else:
                m.physics(None)
                if m.alive and enemies and t - m.spawned > 10:
                    tgt = min(enemies, key=lambda e: abs(e.x - m.x))
                    m.facing = 1 if tgt.x > m.x else -1
                    if m.cool == 0 and abs(tgt.x - m.x) < 15:
                        m.cool, m.swing = rng.randint(24, 34), 12
                        dx = tgt.x - m.x
                        flight = abs(dx) / 1.6
                        self.arrows.append({"x": m.x + 0.4 * m.facing, "y": 1.5, "z": m.z, "vx": dx / flight,
                                            "vy": (1.0 - 1.5) / flight + 0.05 * flight / 2, "tgt": tgt, "age": 0})
        for a in list(self.arrows):
            a["age"] += 1
            a["x"] += a["vx"]
            a["y"] += a["vy"]
            a["vy"] -= 0.05
            m = a["tgt"]
            if m.alive and abs(a["x"] - m.x) < 0.4 and m.y < a["y"] < m.y + 1.95:
                self.hit(m, 4, a["x"] - a["vx"])
                self.arrows.remove(a)
            elif a["y"] < 0 or a["age"] > 40:
                self.arrows.remove(a)

    def world_front(self, f, glow):
        arrow = A.ARROW.crop((0, 0, 16, 5))
        for a in self.arrows:
            ang = math.degrees(math.atan2(a["vy"], a["vx"]))
            paste_rot(f, arrow, (8, 2.5), (sx(a["x"]), sy(a["y"])), ang + 180, scale=1)

    def player(self, f, glow):
        dt = self.t - self.swing_at
        arm = 14
        if 0 <= dt < 6:
            arm = 20 + 120 * math.sin(math.pi * (1 - dt / 6))
        hold = item_holder(self.sprite, self.pivot, lambda a: -a + 10 - 45, scale=1)
        gh = item_holder(self.glow_sprite, self.pivot, lambda a: -a + 10 - 45, scale=1)
        draw_body(f, PLAYER64, A.STEVE, self.player_x, 0, 1, arm, 6, hold=hold, glow_hold=gh, glow=glow)

    def overlay(self, f):
        hud(f, self.t, self.icon, 0.95, chat=self.chat_hud())

    def caption(self):
        t = self.t
        if t < self.USE:
            return [(GRAY, "right-click: raise the dead")]
        if t < self.AGAIN:
            return [(GRAY, "2 skeleton archers for 30s  "), (WHITE, "cooldown 20s")]
        return [(GRAY, "used again too soon")]


class Grimoire(Necromancy):
    key, title, end, tint = "lichs_grimoire", "Lich's Grimoire", 230, (80, 200, 255)
    USE, DISMISS = 14, 180

    def __init__(self):
        super().__init__()
        self.mobs = [Mob("zombie", 9.5, 0.3, 0.04), Mob("husk", 11.0, -0.3, 0.04), Mob("zombie", 12.6, 0.1, 0.04),
                     Mob("husk", 14.2, -0.2, 0.04)]
        self.swing_at = -99
        self.sprite, self.pivot, _ = model_sprite("lichs_grimoire", (8, 5, 8.7), pitch=28)
        self.glow_sprite = model_glow_sprite("lichs_grimoire", (8, 5, 8.7), pitch=28)
        self.icon = icon("lichs_grimoire")

    def step(self, t):
        if t == self.USE:
            self.raise_minions("wither", 4, [(DAQUA, "Steve's Hollow Knight")])
        if t == self.DISMISS:
            self.swing_at = t
            for m in self.minions():
                for _ in range(10):
                    self.parts.append(soul(m.x + rng.gauss(0, 0.2), m.y + 1 + rng.gauss(0, 0.5), m.z + rng.gauss(0, 0.2),
                                           *(rng.gauss(0, 1) * 0.02 for _ in range(3))))
                m.gone = True
            self.tell([(GRAY, "Your knights return to the dark.")])
        enemies = self.enemies()
        for m in self.mobs:
            if m.kind in ("zombie", "husk"):
                m.physics(self.player_x + 2.0)
            elif m.alive:
                tgt = min(enemies, key=lambda e: abs(e.x - m.x)) if enemies else None
                knights = [k for k in self.mobs if k.kind == "wither"]
                reach = 1.1 + 0.6 * (knights.index(m) % 2)          # two ranks, so they don't stand in each other
                if tgt is not None and t - m.spawned > 8:
                    m.physics(tgt.x, stop_at=reach)
                    if abs(tgt.x - m.x) <= 1.95 and m.cool == 0:
                        m.cool, m.swing = 20, 6
                        self.hit(tgt, 20, m.x)
                else:                                               # back to their places round you
                    home = (1.5, -1.5, 2.4, -2.4)[knights.index(m) % 4]
                    m.physics(self.player_x + home, stop_at=0.1)
                    m.facing = 1

    def player(self, f, glow):
        dt = self.t - self.swing_at
        arm = 38
        if 0 <= dt < 6:
            arm = 38 + 60 * math.sin(math.pi * dt / 6)
        hold = item_holder(self.sprite, self.pivot, lambda a: 0, scale=1)
        gh = item_holder(self.glow_sprite, self.pivot, lambda a: 0, scale=1)
        draw_body(f, PLAYER64, A.STEVE, self.player_x, 0, 1, arm, 6, hold=hold, glow_hold=gh, glow=glow)

    def overlay(self, f):
        hud(f, self.t, self.icon, 0.99, chat=self.chat_hud())

    def caption(self):
        t = self.t
        if t < self.USE:
            return [(GRAY, "right-click: call the Hollow Knights")]
        if t < self.DISMISS:
            return [(GRAY, "4 knights in netherite, "), (WHITE, "20 dmg a swing"), (GRAY, ", they stay until killed")]
        return [(GRAY, "use it again: they return to the dark")]


SCENES = {c.key: c for c in (Gaze, Censer, Anchor, Dreadlance, Cleaver, BoneScepter, Grimoire)}


def main():
    global JAR
    args = sys.argv[1:]
    jar = next((a for a in args if a.endswith(".jar")), None)
    if jar is None:
        raise SystemExit("pass the 26.2 client.jar path")
    JAR = zipfile.ZipFile(jar)
    A.load()
    os.makedirs(OUT, exist_ok=True)
    for key in [a for a in args if not a.endswith(".jar")] or list(SCENES):
        rng.seed(7)
        SCENES[key]().run()


if __name__ == "__main__":
    main()
