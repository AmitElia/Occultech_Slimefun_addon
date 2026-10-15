"""The Archevoker redesign, session 1 step 1: silhouettes - the throne and the ring of hands against the priest.

The agreed direction (docs/art/bosses/archevoker/overhaul/plan.md, 2026-10-15): an illager dark priest seated on a
decorated woodland-mansion throne that floats, his arms crossed, his legs crossed at the knee or spread. Two large
gilded casting hands, palm out like a stop sign, one in a cyan glow and one in a purple glow; they are killable (his
totems). A ring of smaller gilded hands turns behind the throne. The throne's armrests end in gilded hands.

The priest is the same in all three takes (vanilla's illager head at 2.5x, the crossed arms at 3.2x). The takes
differ in how the throne's back and the ring frame him:
  A  the Halo          a low back at his shoulders; a small ring round his head
  B  the Rose Window   a tall pointed back; a ring round the whole back
  C  the Grand Wheel   a tall back; a great ring rising high above the throne
Each is shown idle (legs crossed, the hands hovering at his sides) and casting (legs spread, the cyan hand swooping
down to draw on the floor, the purple hand raised). Model units: 16 = one block, y up, the face towards -z, his right
towards +x. The blue figure is a player (1.8 blocks). Colours are blockout zones, not the palette; the glow round the
casting hands is a see-through plate.

Run from the repository root: python tools/art/bosses/archevoker_silhouettes.py [A B C]
"""
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s2 as v2, volley_s1 as v1  # noqa: E402

OUT = ROOT / "docs/art/bosses/archevoker/overhaul/s1_silhouettes"
PALETTE = {
    "robe": (46, 44, 52), "robe_dark": (30, 28, 34), "trim": (196, 166, 70), "tunic": (70, 80, 82),
    "skin": (146, 151, 151), "nose": (128, 133, 133), "brow": (28, 28, 32), "eye": (70, 200, 100),
    "stole": (92, 52, 132), "shoe": (34, 30, 30),
    "gold": (212, 176, 76), "gold_dark": (156, 120, 50), "emerald": (60, 210, 120),
    "cyan": (110, 236, 255), "purple": (178, 96, 255),
    "cyan_aura": (110, 236, 255, 70), "purple_aura": (178, 96, 255, 70),
    "oak": (78, 55, 38), "oak_dark": (52, 37, 27), "velvet": (88, 34, 52),
}
HEAD_K = 2.5
SEAT = 40                    # the seat's top
HIP = (0, SEAT + 4, 8)       # where his thighs meet his body


def beam(g, name, a, b, w, mat):
    return v1.beam(g, name, a, b, w, mat)


def vocto(g, name, c, w, h, d, mat, cham=0.3):
    """An upright mass with its four vertical edges chamfered: an octagon seen from above."""
    ch = cham * min(w, d)
    x, y, z = c
    g.box(name + "_a", c, (w, h, d - 2 * ch), mat)
    g.box(name + "_b", c, (w - 2 * ch, h, d), mat)
    for sx in (-1, 1):
        for sz in (-1, 1):
            g.box(f"{name}_c{sx}{sz}", (x + sx * (w / 2 - 0.75 * ch), y, z + sz * (d / 2 - 0.75 * ch)),
                  (ch * math.sqrt(2), h - 0.5, ch / math.sqrt(2)), mat, rotation=(0, 45 * sx * sz, 0))


def ring_panels(g, name, top_y, bot_y, top_r, bot_r, mat, n=8, t=2.5, fill=1.12, start=22.5):
    """A flared or tapered skirt of n tilted panels round the y axis: planar, never stepped."""
    h = top_y - bot_y
    tilt = math.degrees(math.atan2(bot_r - top_r, h))
    slant = math.hypot(h, bot_r - top_r)
    rm = (top_r + bot_r) / 2
    width = 2 * rm * math.tan(math.pi / n) * fill
    for i in range(n):
        a = start + 360 * i / n
        ar = math.radians(a)
        g.box(f"{name}_{i}", (rm * math.sin(ar), (top_y + bot_y) / 2, rm * math.cos(ar)), (width, slant, t), mat,
              rotation=(-tilt, a, 0))


# ---- the priest -----------------------------------------------------------------------------------------------------

def evoker_head(g, base, k=HEAD_K):
    """Vanilla's illager head at scale k; base = the centre of the chin's underside."""
    x, y, z = base
    g.box("head", (x, y + 5 * k, z), (8 * k, 10 * k, 8 * k), "skin")
    face = z - 4 * k
    g.box("nose", (x, y + 2 * k, face - k), (2 * k, 4 * k, 2 * k), "nose")
    g.box("brow", (x, y + 6.5 * k, face - 0.3), (6 * k, k, 0.6), "brow")
    for sx in (-1, 1):
        g.box(f"eye_{sx}", (x + sx * 1.5 * k, y + 5.5 * k, face - 0.3), (k, k, 0.6), "eye")


def crossed_arms(g, y, z):
    """His arms folded across his belly in wide priest's sleeves (the illager's crossed arms, made a pose): the upper
    arms down his sides, the forearms crossed in front, right over left, the sleeves' bells hanging below."""
    for sx in (-1, 1):
        beam(g, f"upper_arm_{sx}", (sx * 17, y + 33, z + 2), (sx * 18, y + 15, z - 2), 9, "robe")
        g.box(f"sleeve_{sx}", (sx * 16.5, y + 9, z - 3), (12, 13, 11), "robe")
        g.box(f"sleeve_trim_{sx}", (sx * 16.5, y + 3, z - 3), (12.6, 2, 11.6), "trim")
    beam(g, "forearm_left", (-17, y + 17, z - 2), (13, y + 20, z - 6), 9, "robe_dark")
    beam(g, "forearm_right", (17, y + 19.5, z - 4), (-13, y + 22.5, z - 9.5), 9, "robe")
    for sx, (hy, hz) in ((-1, (22.5, -10.5)), (1, (20, -7))):    # gold cuffs and the hands at the far elbows
        g.box(f"cuff_{sx}", (sx * 10.5, y + hy, z + hz), (2, 10, 10), "trim")
        g.box(f"hand_{sx}", (sx * 14.5, y + hy, z + hz), (6, 7, 5.5), "skin")


def arm(g, sx, shoulder, elbow, wrist):
    """One arm in a wide priest's sleeve: the bell round the forearm, a gold cuff, the hand past the wrist."""
    side = "right" if sx > 0 else "left"
    beam(g, f"upper_arm_{side}", shoulder, elbow, 9, "robe")
    beam(g, f"forearm_{side}", elbow, wrist, 8.5, "robe")
    e, w = np.array(elbow, float), np.array(wrist, float)
    d = (w - e) / np.linalg.norm(w - e)
    beam(g, f"sleeve_{side}", tuple(e + (w - e) * 0.35), tuple(w - d * 0.5), 12.5, "robe")
    beam(g, f"sleeve_trim_{side}", tuple(w - d * 2.5), tuple(w), 13.1, "trim")
    beam(g, f"hand_{side}", tuple(w), tuple(w + d * 7), 6, "skin")


ARMS = {   # (shoulder, elbow, wrist) for his right arm (+x); the left mirrors it
    "rest": ((17, 77, 10), (24, 61, 14), (25, 59.5, 1)),          # forearms laid along the armrests
    "cast": ((17, 77, 10), (30, 86, -4), (37, 99, -17)),            # raised, palms out
}


def leg(g, side, yaw, pitch, shin_pitch):
    """A seated leg: the thigh forward from the hip, the shin down from the knee."""
    sx = 1 if side == "right" else -1
    hx, hy, hz = HIP[0] + sx * 7, HIP[1], HIP[2]
    thigh_l, shin_l = 26, 24
    lg = g.group(f"leg_{side}", (hx, hy, hz), (pitch, yaw, 0))
    lg.box(f"thigh_{side}", (hx, hy, hz - thigh_l / 2), (12, 12, thigh_l + 4), "robe")
    knee = (hx, hy, hz - thigh_l)
    sh = lg.group(f"shin_{side}", knee, (shin_pitch, 0, 0))
    sh.box(f"shin_{side}", (hx, hy - shin_l / 2, hz - thigh_l), (10, shin_l, 10), "robe")
    sh.box(f"hem_{side}", (hx, hy - shin_l + 2, hz - thigh_l), (11.2, 2.5, 11.2), "trim")
    sh.box(f"shoe_{side}", (hx, hy - shin_l - 2, hz - thigh_l - 3), (10.5, 5, 15), "shoe")


def priest(root, pose):
    body = root.group("body", HIP)
    if pose != "cast":                                       # right knee over the left
        leg(body, "right", 24, 16, -22)
        leg(body, "left", -4, 0, 4)
    else:                                                    # spread wide, leaning in
        leg(body, "right", -20, 0, 10)
        leg(body, "left", 20, 0, 10)
    torso = body.group("torso", HIP, (6, 0, 0) if pose == "cast" else (-5, 0, 0))
    x, y, z = HIP
    body.box("lap", (0, y + 1, z - 4), (26, 10, 22), "robe")
    vocto(torso, "waist", (0, y + 8, z + 1), 25, 14, 16, "robe")
    vocto(torso, "chest", (0, y + 24, z + 1), 30, 22, 17, "robe")
    torso.box("collar", (0, y + 36, z + 1), (16, 4, 14), "robe_dark")
    torso.box("pendant", (0, y + 32, z - 8), (4, 4, 1.2), "emerald", rotation=(0, 0, 45))
    for sx in (-1, 1):                                       # the stole: two bands down the front, gold-tipped
        torso.box(f"stole_{sx}", (sx * 5.5, y + 16, z - 7.8), (5, 40, 1.2), "stole", rotation=(0, 0, sx * 4))
        torso.box(f"stole_tip_{sx}", (sx * 4.2, y - 5, z - 7.8), (6, 4, 1.4), "trim")
    if pose in ARMS:
        for sx in (-1, 1):
            arm(torso, sx, *[(sx * a, b, c) for a, b, c in ARMS[pose]])
    else:
        crossed_arms(torso, y, z)
    head = torso.group("head", (0, y + 37, z + 1), (-8, 0, 0) if pose == "cast" else (0, 0, 0))
    evoker_head(head, (0, y + 37, z))
    return torso


# ---- the throne -----------------------------------------------------------------------------------------------------

def gripping_hand(g, name, at):
    """A small gilded hand at an armrest's end, its fingers curled down over the front."""
    x, y, z = at
    g.box(name + "_back", (x, y + 0.5, z + 2), (8, 2.5, 8), "gold")
    for i, dx in enumerate((-2.7, -0.9, 0.9, 2.7)):
        g.box(f"{name}_f{i}", (x + dx, y - 1.5, z - 2.6), (1.7, 5, 1.8), "gold")
    g.box(name + "_cuff", (x, y + 0.8, z + 7), (9, 4, 3), "gold_dark")


def throne(root, back_top):
    t = root.group("throne", (0, SEAT, 0))
    vocto(t, "seat", (0, SEAT - 4, 4), 52, 8, 44, "oak", cham=0.18)
    t.box("cushion", (0, SEAT + 1.5, 3), (42, 3, 36), "velvet")
    t.box("seat_trim", (0, SEAT - 4, -18.3), (40, 2, 0.8), "gold")
    ring_panels(t, "base", SEAT - 8, 10, 22, 5, "oak_dark", t=3)
    ring_panels(t, "base_band", SEAT - 8, SEAT - 12, 22.5, 19.5, "gold_dark", t=1.4)
    # the back: a carved frame round a velvet panel, a pointed crest and a finial
    bh = back_top - SEAT
    t.box("back", (0, SEAT + bh / 2, 24), (46, bh, 6), "oak")
    t.box("back_velvet", (0, SEAT + bh / 2 + 2, 20.6), (34, bh - 12, 1), "velvet")
    for sx in (-1, 1):
        t.box(f"back_edge_{sx}", (sx * 17.5, SEAT + bh / 2 + 2, 20.3), (1.5, bh - 12, 0.8), "gold")
        t.box(f"crest_{sx}", (sx * 11, back_top + 6, 24), (28, 7, 6), "oak", rotation=(0, 0, -sx * 28))
        t.box(f"post_{sx}", (sx * 25, SEAT + (bh + 6) / 2 - 4, 24), (7, bh + 14, 8), "oak_dark")
        t.box(f"post_finial_{sx}", (sx * 25, back_top + 13, 24), (5, 5, 5), "gold", rotation=(0, 45, 0))
        t.box(f"armrest_{sx}", (sx * 25, SEAT + 12, 4), (7, 5, 34), "oak")
        t.box(f"armpost_{sx}", (sx * 25, SEAT + 4, -10), (5.5, 12, 5.5), "oak_dark")
        gripping_hand(t, f"arm_hand_{sx}", (sx * 25, SEAT + 15.5, -11))
    t.box("crest_finial", (0, back_top + 14, 24), (6, 6, 6), "gold", rotation=(0, 45, 0))
    t.box("crest_gem", (0, back_top + 2, 20.6), (5, 5, 1), "emerald", rotation=(0, 0, 45))


# ---- the hands -------------------------------------------------------------------------------------------------------

def small_hand(g, name, centre, angle):
    """One hand of the ring: palm forward, fingers pointing out from the ring's centre."""
    x, y, z = centre
    h = g.group(name, centre, (0, 0, -angle))
    h.box(name + "_palm", (x, y, z), (7, 7.5, 2.5), "gold")
    for i, dx in enumerate((-2.55, -0.85, 0.85, 2.55)):
        h.box(f"{name}_f{i}", (x + dx, y + 3.75 + 2.6, z), (1.6, 5.2 + (i in (1, 2)) * 0.8, 2.2), "gold")
    h.box(name + "_thumb", (x - 4.6, y + 0.5, z - 0.3), (1.8, 5, 2.2), "gold", rotation=(0, 0, 32))
    h.box(name + "_cuff", (x, y - 5, z + 0.3), (6, 3, 3), "gold_dark")
    h.box(name + "_sigil", (x, y, z - 1.4), (3, 3, 0.4), "cyan", rotation=(0, 0, 45))


def hand_ring(root, centre, radius, n):
    g = root.group("ring", centre)
    cx, cy, cz = centre
    for i in range(n):
        a = 360 * i / n
        ar = math.radians(a)
        small_hand(g, f"ring_hand{i}", (cx + radius * math.sin(ar), cy + radius * math.cos(ar), cz), a)


def stop_hand(g, name, centre, rot, glow):
    """A large casting hand held up like a stop sign: fingers together, the thumb out, a sigil on the palm, a glow."""
    x, y, z = centre
    h = g.group(name, centre, rot)
    h.box(name + "_palm", (x, y, z), (16, 17, 5), "gold")
    for i, dx in enumerate((-5.85, -1.95, 1.95, 5.85)):
        length = (11, 14, 13, 10)[i]
        h.box(f"{name}_f{i}", (x + dx, y + 8.5 + length / 2, z), (3.7, length, 4.2), "gold")
    h.box(name + "_thumb", (x - 10, y + 1, z - 0.5), (4, 11, 4.2), "gold", rotation=(0, 0, 34),
          origin=(x - 7.5, y - 4, z))
    h.box(name + "_cuff", (x, y - 11.5, z + 0.5), (13, 6, 7), "gold_dark")
    h.box(name + "_flare", (x, y - 15.5, z + 0.5), (16, 3, 9), "gold")
    h.box(name + "_sigil", (x, y + 1, z - 2.8), (8, 8, 0.6), glow, rotation=(0, 0, 45))
    for i in range(8):                                       # a spell circle behind the hand, in its glow
        a = math.radians(i * 45 + 22.5)
        r = 19
        h.box(f"{name}_circle{i}", (x + r * math.sin(a), y + 3 + r * math.cos(a), z + 4), (r * 0.83, 1.6, 0.8), glow,
              rotation=(0, 0, -(i * 45 + 22.5)))


# ---- the takes -------------------------------------------------------------------------------------------------------

TAKES = {
    "A": ("The Halo", dict(back_top=92, ring=((0, 92, 32), 30, 10))),
    "B": ("The Rose Window", dict(back_top=118, ring=((0, 90, 34), 48, 12))),
    "C": ("The Grand Wheel", dict(back_top=112, ring=((0, 112, 38), 62, 16))),
}


def build(key, pose):
    title, p = TAKES[key]
    m = Model(f"archevoker_{key}_{pose}")
    root = m.group("root", (0, 0, 0))
    throne(root, p["back_top"])
    hand_ring(root, *p["ring"])
    priest(root, pose)
    hands = root.group("casting", (0, 0, 0))
    if pose != "cast":
        stop_hand(hands, "hand_cyan", (48, 74, -12), (0, -14, -6), "cyan")
        stop_hand(hands, "hand_purple", (-48, 74, -12), (0, 14, 6), "purple")
    else:
        stop_hand(hands, "hand_cyan", (14, 22, -84), (-35, 0, 0), "cyan")             # drawing on the floor
        stop_hand(hands, "hand_purple", (-58, 116, -8), (8, 18, 12), "purple")       # raised
    return m, title


VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 35, "height": 3.2, "dist": 14, "target_z": 4.0},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.0, "dist": 13.5, "target_z": 4.0,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -30, "height": 1.62, "dist": 13, "target_z": 4.2,
     "player": False},
]
LABELS = {"flat_34": "three-quarter", "flat_front": "front", "sil_side": "side, silhouette", "clay_eye": "a player's eye"}


def main(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    for key in (only or TAKES):
        if (OUT / key).exists():
            shutil.rmtree(OUT / key)
        for pose in ("idle", "cast"):
            m, title = build(key, pose)
            v2.run_blender(m.render_json(v2.PALETTE), OUT / key / pose, VIEWS)
            if pose == "idle":
                lo, hi = m.bounds()
                print(key, title, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
        tw, th, pad, top = 400, 320, 12, 60
        img = Image.new("RGB", (pad + 4 * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Archevoker {key}: {title}", font=sheet._font(26), fill=sheet.INK)
        for r, pose in enumerate(("idle", "cast")):
            for c, v in enumerate(VIEWS):
                x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
                img.paste(sheet._tile(OUT / key / pose / f"{v['name']}.png", tw, th), (x, y))
                dr.text((x, y + th + 6), f"{pose}: {LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
        img.save(OUT / f"{key}_{title.lower().replace(' ', '_')}.png")


TAKE2 = ROOT / "docs/art/bosses/archevoker/overhaul/s1_take2"
POSES2 = (("rest", "resting"), ("cast", "casting"), ("fold", "arms folded"))


def take2():
    """Take 2 (2026-10-15): B, the ring's hands floating free (no band), his arms on the armrests when idle, raised to
    cast, sometimes folded."""
    TAKE2.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    for pose, _ in POSES2:
        if (TAKE2 / pose).exists():
            shutil.rmtree(TAKE2 / pose)
        m, _ = build("B", pose)
        v2.run_blender(m.render_json(v2.PALETTE), TAKE2 / pose, VIEWS)
        lo, hi = m.bounds()
        print(pose, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
    tw, th, pad, top = 400, 320, 12, 60
    img = Image.new("RGB", (pad + 4 * (tw + pad), top + 3 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Archevoker B, take 2: the ring's hands free, his arms resting, casting, folded",
            font=sheet._font(26), fill=sheet.INK)
    for r, (pose, label) in enumerate(POSES2):
        for c, v in enumerate(VIEWS):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(TAKE2 / pose / f"{v['name']}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{label}: {LABELS[v['name']]}", font=sheet._font(17), fill=sheet.DIM)
    img.save(TAKE2 / "take2.png")


if __name__ == "__main__":
    if sys.argv[1:] == ["take2"]:
        take2()
    else:
        main(sys.argv[1:] or None)
