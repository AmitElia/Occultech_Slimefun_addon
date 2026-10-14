"""The Mirrored Magus: the Jack-in-the-Box, a second mechanic beside his mirrored copies (design study).

The user, 2026-10-13: little pop-up box clowns with the colours and shape of his face and upper body but much less
detail, on a spring, animated to shoot cards with a bopping animation. This builds one in the Magus's own frame - the
head at his head's height, so his face paint (magus_s5) lands on it unchanged - then sets it on the ground, paints it
with the Magus's painters and renders it popped up, mid-bop and throwing, beside a player for size.

The rig (bones): `jack_box` (the box, fixed), `lid` (hinged at the back), `crank`, `spring` (scaled in y by the
bop), `body` (rides the spring's top: chest, ruff, arms), `hi_head` (his face, nodding), `glow_eyes`, `arm_left`,
`arm_right`, `cards`, `hat_left`, `hat_right`.

Run from the repository root: python tools/art/bosses/magus_jack.py
"""
import math
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit import sheet  # noqa: E402
from bosskit.bbmodel import Model  # noqa: E402
from bosses import magus_s2 as s2, magus_s4 as s4, magus_s5 as s5  # noqa: E402
from bosses.magus_s2 import YH, ZF, mouth_edges, _lip, yaw_box  # noqa: E402

OUT = ROOT / "docs/art/bosses/mirrored_magus/overhaul/jack"
BOX = 14                    # the box: a cube this wide
HEAD_LOW = YH - 8           # the bottom of the head (the Magus's head, his frame)
CHEST = 7                   # the chest's height under the head
SCALE = 0.5                 # built at the Magus's head size (so his face paint fits), shown at half: about 2 blocks


def face(head):
    """His face with much less detail: the same white head, brows, red nose and illager eyes; a grin of three lip
    segments a side, five big teeth; two tufts of hair a side."""
    head.box("head", (0, YH, 0), (11, 16, 11), "skin")
    for sx in (-1, 1):
        head.box(f"brow_{sx}", (sx * 2.7, YH + 4.5, ZF - 0.9), (5, 1.6, 1.8), "face", rotation=(0, 0, sx * 22.5))
        head.box(f"mouth_cheek_{sx}", (sx * 5.0, YH - 0.4, ZF - 0.8), (3.4, 2.6, 1.6), "face",
                 rotation=(0, 0, sx * 22.5))
        for k, (dy, dz, ang) in enumerate(((6.0, -1.6, 22.5), (4.6, 1.8, 45))):
            head.box(f"hair_{sx}_{k}", (sx * 7.2, YH + dy, dz), (5, 2.4, 2.6), "hair", rotation=(0, 0, -sx * ang))
    head.box("nose", (0, YH - 0.4, ZF - 2.2), (3.6, 3.6, 3.4), "rednose")
    for upper, tag, cuts in ((True, "upper", (0.0, 2.4, 4.9)), (False, "lower", (0.0, 1.4, 2.8, 3.9, 4.9))):
        _lip(head, f"lip_{tag}_0", -cuts[1], cuts[1], upper)
        for i in range(1, len(cuts) - 1):
            for sx in (-1, 1):
                a, b = sorted((sx * cuts[i], sx * cuts[i + 1]))
                _lip(head, f"lip_{tag}_{i}_{sx}", a, b, upper)
    for k, (x, upper) in enumerate(((-2.4, True), (0.0, True), (2.4, True), (-1.2, False), (1.2, False))):
        up, low = mouth_edges(x)
        root, sign = (up, -1) if upper else (low, 1)
        body = 0.32 * (up - low)
        name = f"tooth_{'upper' if upper else 'lower'}_{k}"
        head.box(name, (x, root + sign * body / 2, ZF - 0.9), (1.2, body, 0.9), "teeth")
        head.box(f"{name}_tip", (x, root + sign * (body + 0.15), ZF - 0.9), (0.85, 0.85, 0.9), "teeth",
                 rotation=(0, 0, 45))
    eyes = head.group("glow_eyes", (0, YH + 2.2, ZF - 1))
    for sx in (-1, 1):
        eyes.box(f"eye_{sx}", (sx * 3.1, YH + 2.2, ZF - 0.3), (2.6, 1.4, 0.4), "eye_glint")
    # his hat, shrunk: band, cap and two short floppy points with bells
    top = YH + 8
    head.box("hat_band", (0, top + 1.2, 0), (12, 3, 12), "crimson")
    head.box("hat_cap", (0, top + 3.6, 0.5), (11, 3, 11), "black")
    for name, base, turn, mats in (("hat_left", (-4, top + 4.5, 0), -1, ("black", "crimson")),
                                   ("hat_right", (4, top + 4.5, 0), 1, ("white", "black"))):
        g = head.group(name, base, (0, 0, -turn * 45))
        g.box(f"{name}_0", (base[0], base[1] + 4, base[2]), (4.6, 8, 4.6), mats[0])
        g.box(f"{name}_1", (base[0], base[1] + 9.5, base[2]), (3.2, 4, 3.2), mats[1], rotation=(0, 0, -turn * 22.5),
              origin=(base[0], base[1] + 7.5, base[2]))
        g.box(f"{name}_bell", (base[0] - turn * 1.6, base[1] + 12.5, base[2]), (2, 2, 2), "gold")


def upper_body(body, throw):
    """His upper body with much less detail: chest halves black and white, a ruff of eight wedges, stubby arms; the
    right hand holds a fan of three cards (thrown in the throw pose)."""
    y0 = HEAD_LOW - CHEST
    body.box("neck_box", (0, HEAD_LOW - 0.5, 0), (4, 2, 4), "face")
    for sx in (-1, 1):
        body.box(f"chest_{sx}", (sx * 3, y0 + CHEST / 2, 0), (6, CHEST, 7), "black" if sx < 0 else "white")
    for i in range(8):
        a = math.radians(i * 45)
        yaw_box(body, f"ruff_{i}", (math.sin(a) * 4.6, HEAD_LOW - 1, math.cos(a) * 4.2), (3.6, 3, 5),
                "white" if i % 2 else "black", i * 45)
    for sx in (-1, 1):
        side = "left" if sx < 0 else "right"
        sh = (sx * 7, HEAD_LOW - 2.5, 0)
        rot = (-67.5 if throw else -22.5, 0, 22.5) if sx > 0 else (0, 0, -22.5)
        arm = body.group(f"arm_{side}", sh, rot)
        arm.box(f"cap_{side}", (sx * 7, sh[1], 0), (4, 3, 4), "crimson")
        arm.box(f"sleeve_{side}", (sx * 7, sh[1] - 4.5, 0), (3, 7, 3), "white" if sx < 0 else "black")
        arm.box(f"hand_{side}", (sx * 7, sh[1] - 9.5, 0), (3, 3, 3), "skin")
        if sx > 0:
            g = arm.group("cards", (sx * 7, sh[1] - 10, -0.6))
            for k, angle in enumerate((-22.5, 0, 22.5)):
                z = -1.6 - k * 0.25
                g.box(f"card_{k}", (sx * 7, sh[1] - 13, z), (4, 6, 0), "card", rotation=(0, 0, angle),
                      origin=(sx * 7, sh[1] - 10, z))


def box_parts(box, base):
    """The box: crimson, gold-trimmed, a harlequin diamond on each side (black front and back, white sides), the lid
    standing open behind it, a crank on its right side."""
    h = BOX
    box.box("jack_box", (0, base + h / 2, 0), (h, h, h), "crimson")
    for sx in (-1, 1):
        for sz in (-1, 1):
            box.box(f"post_{sx}_{sz}", (sx * (h / 2 - 0.4), base + h / 2, sz * (h / 2 - 0.4)), (1.8, h + 0.4, 1.8),
                    "gold")
    box.box("rim", (0, base + h - 0.3, 0), (h + 0.6, 1.4, h + 0.6), "gold")
    d = h * 0.42
    box.box("diamond_front", (0, base + h / 2, -h / 2 - 0.2), (d, d, 0.4), "black", rotation=(0, 0, 45))
    box.box("diamond_back", (0, base + h / 2, h / 2 + 0.2), (d, d, 0.4), "black", rotation=(0, 0, 45))
    box.box("diamond_left", (-h / 2 - 0.2, base + h / 2, 0), (0.4, d, d), "white", rotation=(45, 0, 0))
    box.box("diamond_right", (h / 2 + 0.2, base + h / 2, 0), (0.4, d, d), "white", rotation=(45, 0, 0))
    hinge = (0, base + h, h / 2)
    lid = box.group("lid", hinge, (45, 0, 0))
    lid.box("lid", (0, base + h + h / 2, h / 2 + 0.8), (h + 0.6, h + 0.6, 1.6), "crimson")
    lid.box("lid_diamond", (0, base + h + h / 2, h / 2 - 0.2), (d * 0.8, d * 0.8, 0.4), "white", rotation=(0, 0, 45))
    crank = box.group("crank", (h / 2 + 0.6, base + h / 2, 0))
    crank.box("crank_axle", (h / 2 + 1.6, base + h / 2, 0), (2.4, 1, 1), "gold")
    crank.box("crank_arm", (h / 2 + 2.6, base + h / 2 - 2, 0), (1, 5, 1), "gold")
    crank.box("crank_knob", (h / 2 + 3.6, base + h / 2 - 4, 0), (2, 1.6, 1.6), "black")


def spring(g, bottom, top):
    """The spring: rings of four thin bars, every other ring turned 45 degrees, so it reads as a coil."""
    n = max(3, round((top - bottom) / 3.2))
    for k in range(n + 1):
        y = bottom + (top - bottom) * k / n
        yaw = 45 if k % 2 else 0
        for j in range(4):
            a = math.radians(yaw + j * 90)
            yaw_box(g, f"coil_{k}_{j}", (math.sin(a) * 2.6, y, math.cos(a) * 2.6), (5.2 + 0.6, 1, 1), "gold",
                    yaw + j * 90 + 90)


def build(stretch=16.0, nod=0.0, throw=False):
    """The jack popped up; `stretch` is the spring's length, `nod` tips his head and body forward (the bop)."""
    model = Model("occultech_mirrored_magus_jack")
    base = HEAD_LOW - CHEST - stretch - BOX
    jack = model.group("jack_box", (0, base, 0))
    box_parts(jack, base)
    s = jack.group("spring", (0, base + BOX, 0))
    spring(s, base + BOX, HEAD_LOW - CHEST)
    body = s.group("body", (0, HEAD_LOW - CHEST, 0), (nod, 0, 0))
    upper_body(body, throw)
    head = body.group("hi_head", (0, HEAD_LOW, 0), (nod * 0.5, 0, 0))
    face(head)
    model.base = base
    return model


def settle(model):
    """Set the jack on the ground and shrink it: move every bone and cube down so the box sits at y 0, then scale it
    all by SCALE (in game the rig is scaled by BetterModel the same way)."""
    dy = model.base

    def move(p):
        p[1] -= dy
        for i in range(3):
            p[i] *= SCALE
    for g in model.groups:
        move(g.origin)
    for c in model.cubes:
        for p in (c.frm, c.to, c.origin):
            move(p)


POSES = {"popped": dict(stretch=16.0), "bop": dict(stretch=9.0, nod=22.5), "throw": dict(stretch=19.0, nod=-22.5,
                                                                                          throw=True)}
VIEWS = {
    "hero": {"location": (3.2, 4.4, 1.6), "target": (0.4, 0, 0.95), "scale": 2.6, "player": True},
    "front": {"location": (0.2, 6, 1.1), "target": (0, 0, 1.0), "scale": 2.3, "player": False},
    "side": {"location": (6, 0.3, 1.1), "target": (0, 0, 1.0), "scale": 2.3, "player": False},
    "face": {"location": (0.8, 4, 1.6), "target": (0, -0.1, 1.42), "scale": 0.95, "player": False},
}
SHOTS = [("popped", "hero"), ("popped", "front"), ("popped", "side"), ("bop", "hero"), ("throw", "hero"),
         ("popped", "face")]
LABELS = {"popped": "popped up", "bop": "the bop (spring squashed, nodding)", "throw": "the throw (sprung, flicking)"}


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    s2.MASK = "clown"
    built = {}
    for key, kw in POSES.items():
        s2.build = lambda name, kw=kw: build(**kw)            # the painters run on the jack's own cubes
        model, keys, positions, used, height, atlas = s5.painted()
        settle(model)
        atlas_path = OUT / f"atlas_{key}.png"
        atlas.save(atlas_path)
        bb, _ = s4.rig_bbmodel(model, keys, positions, atlas_path, height, {})
        views = [dict(VIEWS[v], name=f"{key}_{v}") for k, v in SHOTS if k == key]
        s4.render(model, bb, atlas_path, OUT, views, player_at=(-1.3, 0.3))
        built[key] = len(model.cubes), len(model.groups)
    tw, th, pad, top = 440, 330, 12, 60
    img = Image.new("RGB", (pad + 3 * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Mirrored Magus - the Jack-in-the-Box (design)", font=sheet._font(26), fill=sheet.INK)
    for k, (key, v) in enumerate(SHOTS):
        x, y = pad + (k % 3) * (tw + pad), top + (k // 3) * (th + 34 + pad)
        img.paste(sheet._tile(OUT / f"{key}_{v}.png", tw, th), (x, y))
        dr.text((x, y + th + 6), f"{LABELS[key]} - {v}" if v != "hero" else LABELS[key], font=sheet._font(17),
                fill=sheet.DIM)
    img.save(OUT / "jack.png")
    print(built)


if __name__ == "__main__":
    main()
