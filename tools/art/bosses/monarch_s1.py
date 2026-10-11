"""Mire Monarch redesign, session 1: three directions, each in both of its forms.

The boss (MireMonarch.java, renamed from the Gelatinous Sovereign on 2026-10-11) is a giant crowned cellar toad. The
fight is set: it marks a player and leaps onto them, the belly-flop sending a shockwave players jump; at 66% it
retches up three spawn that crawl back to the altar to feed it; at 33% it dries and splits, leaner and faster, sweating
acid puddles. Each direction is shown big (phase 1) and dried (phase 2).

Every direction is built from vanilla's frog: a flat body, the head split by a wide mouth line, two cube eyes standing
on top of the head (a dark horizontal pupil with a gold edge), a croaking throat sac under the chin, and webbed hands
and feet as flat planes with spread toes. Colours from vanilla's cold (mire-green) frog.

  A  The Bullfrog Tyrant  vanilla's frog grown huge and fat: a wide, heavy body, a gaping mouth line, a great throat
                          sac, a warty back with pale toadstools, the crown sitting between its eyes.
  B  The Horned Maw       a pac-man (horned) frog: nearly all mouth, a round body with the mouth line running all
                          round it, horn-pointed eyelids, short legs tucked under, poison-dart stripes glowing on its back.
  C  The Bog King         sitting upright on its haunches like a king on a throne, belly out, hands on its knees, a
                          mantle of pond weed down its back, a lily-pad collar, a cattail sceptre.

Phase 2 of every direction: the skin dried grey-brown and split, acid glowing in the cracks and dripping into puddles,
ribs, spine and hip bones showing through, the body leaner, still crouched on its folded legs, eyes sunken and
glowing, the crown slipping.

Run from the repository root: python tools/art/bosses/monarch_s1.py
"""
import json
import math
import random
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import brood_s1 as b1, volley_crone_s1 as v1, volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/mire_monarch/overhaul/s1_concepts"
PALETTE = {
    # vanilla's cold frog: mossy greens, a pale yellowed underside, dark brown details
    "skin": (73, 107, 30), "skin_dark": (58, 90, 25), "skin_light": (99, 144, 46), "belly": (190, 173, 106),
    "wart": (120, 112, 52), "mouth": (46, 29, 16), "tongue": (226, 110, 120),
    "iris": (220, 176, 70), "pupil": (16, 12, 10), "web": (86, 128, 34),
    "dry": (128, 116, 84), "dry_dark": (92, 82, 60), "bone": (205, 187, 152),
    "glow": (170, 255, 0), "glow_hot": (232, 255, 120), "acid": (150, 230, 30),
    "cap": (214, 200, 168), "gill": (160, 140, 110), "stem": (220, 210, 190),
    "weed": (44, 78, 30), "weed_light": (70, 110, 40), "pad": (86, 140, 44), "reed": (110, 80, 44),
    "gold": (232, 178, 46), "gold_dark": (168, 116, 24), "gem": (170, 255, 0),
}
DIRECTIONS = {"A": "The Bullfrog Tyrant", "B": "The Horned Maw", "C": "The Bog King"}


# ---- parts --------------------------------------------------------------------------------------------------------

def crown(g, name, centre, r, h, tilt=(0, 0, 0)):
    """A big, chunky crown: a thick band with a darker rim, blocky stepped points, a glowing front stone."""
    x, y, z = centre
    c = g.group(name, (x, y, z), tilt)
    t = max(2.5, r * 0.2)
    for sd in (-1, 1):
        c.box(f"{name}_band_x{sd}", (x + sd * (r - t / 2), y, z), (t, h, 2 * r), "gold")
        c.box(f"{name}_band_z{sd}", (x, y, z + sd * (r - t / 2)), (2 * r - 2 * t, h, t), "gold")
        c.box(f"{name}_rim_x{sd}", (x + sd * (r - t / 2), y - h / 2 + 0.75, z), (t + 1.2, 1.5, 2 * r + 1.2), "gold_dark")
        c.box(f"{name}_rim_z{sd}", (x, y - h / 2 + 0.75, z + sd * (r - t / 2)), (2 * r - 2 * t, 1.5, t + 1.2), "gold_dark")
    for i, (dx, dz) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0))):
        tall = h * (1.0 if dx and dz else 0.75)
        px, pz = x + dx * (r - t / 2), z + dz * (r - t / 2)
        c.box(f"{name}_point_{i}", (px, y + h / 2 + tall * 0.3, pz), (t * 1.5, tall * 0.6, t * 1.5), "gold")
        c.box(f"{name}_tip_{i}", (px, y + h / 2 + tall * 0.75, pz), (t * 0.9, tall * 0.5, t * 0.9), "gold")
        c.box(f"{name}_ball_{i}", (px, y + h / 2 + tall * 1.05, pz), (t * 0.7, t * 0.7, t * 0.7), "gold_dark")
    c.box(f"{name}_stone", (x, y + 0.3, z - r - 0.8), (t * 2, t * 2, 1.6), "gem")
    return c


def eye(g, name, centre, s, sunken=False):
    """A vanilla frog eye: a cube standing on the head, its front a gold iris round a dark horizontal pupil. Sunken
    (dried): smaller, the pupil glowing."""
    x, y, z = centre
    if sunken:
        s *= 0.8
    b1.rounded_box(g, f"{name}", (x, y, z), (s, s * 0.75, s), "skin" if not sunken else "dry", max(1.0, s * 0.12))
    g.box(f"{name}_iris", (x, y + s * 0.05, z - s / 2 - 0.3), (s * 0.8, s * 0.5, 0.6), "iris")
    g.box(f"{name}_pupil", (x, y + s * 0.05, z - s / 2 - 0.7), (s * 0.6, s * 0.16, 0.6), "glow_hot" if sunken else "pupil")


def webbed(g, name, centre, w, d, mat="web"):
    """A vanilla frog hand or foot: a flat webbed plane (zero thick) with three toes and their pads."""
    x, y, z = centre
    g.box(f"{name}_web", (x, y, z), (w, 0, d), mat)
    for i in (-1, 0, 1):
        tx, tz = x + i * w * 0.32, z - d * 0.45
        g.box(f"{name}_toe_{i}", (tx, y + 0.6, z - d * 0.15 + abs(i) * 2), (1.6, 1.2, d * 0.6), mat)
        g.box(f"{name}_pad_{i}", (tx, y + 0.8, tz), (2.6, 1.6, 2.6), "skin_light")


def head(g, name, centre, w, h, d, sac=1.0, dried=False):
    """The vanilla frog head: an upper and a lower jaw split by the wide dark mouth line round the front and sides, a
    croaking throat sac swelling under the chin."""
    x, y, z = centre
    skin = "dry" if dried else "skin"
    b1.rounded_box(g, f"{name}_upper", (x, y + h * 0.22, z), (w, h * 0.55, d), skin, max(1.5, h * 0.12))
    b1.rounded_box(g, f"{name}_lower", (x, y - h * 0.3, z + 1), (w - 2, h * 0.42, d - 2), "belly" if not dried else "dry_dark",
                   max(1.0, h * 0.08))
    g.box(f"{name}_mouth", (x, y - h * 0.06, z + 1), (w + 0.6, max(1.0, h * 0.06), d - 4), "mouth")
    if sac:
        g.blob(f"{name}_sac", (x, y - h * 0.5, z - d * 0.15), (w * 0.3 * sac, h * 0.3 * sac, d * 0.3 * sac),
               "belly" if not dried else "dry_dark", layers=4, axes=("y", "z"))


def haunch(g, name, side, centre, thick, mat="skin", foot_size=(16, 24), lean=False):
    """A folded toad leg, the toad's signature shape: a huge thigh bulging out at the rear side, the shin folded flat
    along under it towards the front, a long webbed foot splayed out behind. Lean (dried): the same fold, wasted, the
    knee and hip bones showing."""
    x, y, z = centre
    k = 0.7 if lean else 1.0
    g.blob(f"{name}_thigh", (x, y, z), (thick * 0.8 * k, thick * 0.75 * k, thick * 1.25 * k), mat, layers=6, axes=("y", "z"))
    knee = (x + side * thick * 0.55, y - thick * 0.1, z - thick * 1.1)
    ankle = (x + side * thick * 0.35, thick * 0.25, z + thick * 0.6)
    v1.beam(g, f"{name}_shin", knee, ankle, thick * 0.5 * k, mat)
    g.box(f"{name}_knee", knee, (thick * 0.55 * k, thick * 0.55 * k, thick * 0.55 * k), "dry_dark" if lean else mat)
    webbed(g, f"{name}_foot", (x + side * thick * 0.9, 0.5, z + thick * 1.3), *foot_size)


def arm_pair(g, name, side, shoulder, elbow, hand, thick, mat="skin", hand_size=(12, 12)):
    """A frog's front leg: short and thick, the elbow out, the webbed hand planted and turned in (a push-up stance)."""
    v1.beam(g, f"{name}_upper", shoulder, elbow, thick, mat)
    v1.beam(g, f"{name}_fore", elbow, (hand[0], hand[1] + 1.5, hand[2] + 2), thick * 0.9, mat)
    g.box(f"{name}_elbow", elbow, (thick, thick, thick), mat)
    webbed(g, f"{name}_hand", hand, *hand_size)


def warts(g, name, centre, spread, n, rnd, mat="wart", size=(2, 4)):
    cx, cy, cz = centre
    sx, sy, sz = spread
    for i in range(n):
        s = rnd.uniform(*size)
        g.box(f"{name}_{i}", (cx + rnd.uniform(-sx, sx), cy + rnd.uniform(-sy, sy), cz + rnd.uniform(-sz, sz)),
              (s, s * 0.7, s), mat)


def toadstool(g, name, base, h, r):
    x, y, z = base
    g.box(f"{name}_stem", (x, y + h / 2, z), (r * 0.5, h, r * 0.5), "stem")
    g.box(f"{name}_cap", (x, y + h + r * 0.25, z), (r * 2, r * 0.6, r * 2), "cap")
    g.box(f"{name}_gills", (x, y + h - 0.1, z), (r * 1.8, 0.4, r * 1.8), "gill")


def dried(g, rnd, centre, half, top, n=14):
    """Phase 2 for every direction: cracks in the dried skin glowing with acid, acid dripping off it into puddles."""
    cx, cy, cz = centre
    hx, hz = half
    for i in range(n):
        side = i % 4
        t = rnd.uniform(-0.8, 0.8)
        y = rnd.uniform(cy - 4, top)
        pos = ((cx + hx + 0.4, y, cz + t * hz), (cx - hx - 0.4, y, cz + t * hz), (cx + t * hx, y, cz + hz + 0.4),
               (cx + t * hx, top + 0.4, cz + t * hz))[side]
        size = ((1, rnd.uniform(5, 10), 1.4), (1, rnd.uniform(5, 10), 1.4), (1.4, rnd.uniform(5, 10), 1),
                (rnd.uniform(5, 10), 1, 1.4))[side]
        g.box(f"crack_{i}", pos, size, "glow_hot" if i % 3 == 0 else "glow",
              rotation=(rnd.choice((22.5, -22.5, 0)), 0, 0) if side < 2 else (0, 0, rnd.choice((22.5, -22.5, 0))))
    for i in range(10):
        a = rnd.uniform(0, 2 * math.pi)
        length = rnd.uniform(4, 12)
        g.box(f"acid_drip_{i}", (cx + math.cos(a) * hx, cy - length / 2, cz + math.sin(a) * hz), (1.6, length, 1.6), "acid")
    for i, (dx, dz, w) in enumerate(((0, 0, 1.0), (-0.9, 0.6, 0.45), (0.8, -0.7, 0.4))):
        g.box(f"acid_puddle_{i}", (cx + dx * hx, 0.3, cz + dz * hz), (hx * 1.6 * w, 0.6, hz * 1.4 * w), "acid")


def ribs(g, side_x, centre_y, z0, z1, n, h):
    for i in range(n):
        z = z0 + (z1 - z0) * (i + 0.5) / n
        g.box(f"rib_{side_x}_{i}", (side_x, centre_y, z), (1.2, h, 2), "dry_dark")


# ---- A: The Bullfrog Tyrant ---------------------------------------------------------------------------------------

def bullfrog(model, phase):
    rnd = random.Random(1 + phase)
    root = model.group("root_body", (0, 0, 0))
    dry = phase == 2
    skin = "dry" if dry else "skin"
    w = 46 if dry else 60
    body = root.group("body", (0, 16, 6))
    # a body sloping up from the head to the hump over the hips, as a toad's back does
    b1.rounded_box(body, "body", (0, 16, 6), (w, 22 if dry else 26, 50), skin, 5)
    b1.rounded_box(body, "hump", (0, 28 if dry else 30, 16), (w * 0.7, 12, 30), skin, 4)
    if dry:
        body.box("spine", (0, 36, 10), (3, 4, 42), "dry_dark")
        for sd in (-1, 1):                                    # hip bones poking up, ribs down the flanks
            body.box(f"hip_bone_{sd}", (sd * 10, 37, 26), (4, 6, 4), "bone")
            ribs(body, sd * (w / 2 + 0.4), 16, -8, 22, 6, 14)
    else:
        warts(body, "wart", (0, 34, 14), (22, 3, 16), 22, rnd)
        for i, (x, z, h, r) in enumerate(((-12, 20, 7, 4), (10, 26, 9, 5), (2, 10, 5, 3))):
            toadstool(body, f"toadstool_{i}", (x, 35, z), h, r)
    hd = root.group("hi_head", (0, 20, -16))
    head(hd, "head", (0, 22, -24), w + 2, 26 if not dry else 22, 26, sac=1.4 if not dry else 0.5, dried=dry)
    for sd in (-1, 1):
        eye(hd, f"eye_{sd}", (sd * (w / 2 - 8), 37 - (3 if dry else 0), -30), 13, sunken=dry)
    crown(hd, "crown", (0, 39 - (3 if dry else 0), -22), 12, 9, tilt=(0, 0, -22.5) if dry else (0, 0, 0))
    legs = root.group("legs", (0, 0, 0))
    for sd in (-1, 1):
        haunch(legs, f"leg_{sd}", sd, (sd * (w / 2 + 4), 14, 20), 18 if not dry else 15, skin, lean=dry)
        arm_pair(legs, f"arm_{sd}", sd, (sd * (w / 2 - 6), 12, -18), (sd * (w / 2 + 6), 9, -24),
                 (sd * (w / 2 + 1), 0.5, -36), 9 if not dry else 6, skin)
    if dry:
        dried(root, rnd, (0, 16, 6), (w / 2, 25), 30)


# ---- B: The Horned Maw -----------------------------------------------------------------------------------------

def horned_maw(model, phase):
    """A pac-man (horned) frog: nearly all mouth, a round body with the wide mouth line running all round it, horn-
    pointed eyelids over the eyes, short legs tucked under it, poison-dart stripes glowing on its back."""
    rnd = random.Random(10 + phase)
    root = model.group("root_body", (0, 0, 0))
    dry = phase == 2
    skin = "dry" if dry else "skin_dark"
    w = 52 if dry else 66
    body = root.group("hi_head", (0, 22, 0))                  # head and body are one: the whole thing turns to look
    # round, not boxy: two domes, the upper jaw over the lower
    body.blob("upper", (0, 24, 0), (w / 2, 20 if not dry else 17, w * 0.46), skin, layers=8, axes=("y", "z"))
    body.blob("lower", (0, 14, 2), (w / 2 - 2, 13, w * 0.44), "belly" if not dry else "dry_dark", layers=6, axes=("y", "z"))
    body.box("mouth", (0, 19, 1), (w + 0.8, 2, w * 0.82), "mouth")      # the mouth line runs all the way round
    if dry:                                                   # dried: the jaw hangs open, drooling acid
        body.box("gape", (0, 18, -w * 0.3), (w * 0.7, 6, w * 0.3), "mouth")
        for i in range(5):
            body.box(f"drool_{i}", (-w * 0.25 + i * w * 0.12, 12, -w * 0.42), (2, 8 + i % 3 * 3, 2), "acid")
        body.box("spine", (0, 42, 4), (3, 4, w * 0.7), "dry_dark")
    else:
        for i in range(6):                                    # poison-dart stripes glowing down its back
            body.box(f"stripe_{i}", (-w * 0.3 + i * w * 0.12, 42.5, 8), (3, 1, w * 0.5), "glow" if i % 2 else "glow_hot")
        warts(body, "wart", (0, 38, 4), (w * 0.35, 2, w * 0.32), 18, rnd)
    for sd in (-1, 1):
        ex = sd * (w * 0.3)
        eye(body, f"eye_{sd}", (ex, 42 - (3 if dry else 0), -w * 0.22), 16, sunken=dry)
        # the horned eyelid: a big pointed hood over each eye, its horn sweeping up and out
        body.box(f"horn_{sd}", (ex, 50 - (3 if dry else 0), -w * 0.2), (15, 7, 15), skin, rotation=(0, 45, 0))
        body.box(f"horn_tip_{sd}", (ex + sd * 4, 58 - (3 if dry else 0), -w * 0.18), (6, 12, 6), skin, rotation=(0, 0, sd * -22.5))
    crown(body, "crown", (0, 47 - (3 if dry else 0), w * 0.08), 11, 9, tilt=(0, 0, 22.5) if dry else (0, 0, 0))
    legs = root.group("legs", (0, 0, 0))
    for sd in (-1, 1):                                        # short legs tucked under the round body
        haunch(legs, f"leg_{sd}", sd, (sd * (w / 2), 10, w * 0.25), 13, skin, foot_size=(12, 18), lean=dry)
        arm_pair(legs, f"arm_{sd}", sd, (sd * (w / 2 - 6), 10, -w * 0.25), (sd * (w / 2 + 2), 6, -w * 0.3),
                 (sd * (w / 2), 0.5, -w * 0.42), 7, skin, hand_size=(10, 10))
    if dry:
        dried(root, rnd, (0, 20, 0), (w / 2, w * 0.45), 40)


# ---- C: The Bog King ----------------------------------------------------------------------------------------------

def bog_king(model, phase):
    rnd = random.Random(20 + phase)
    root = model.group("root_body", (0, 0, 0))
    dry = phase == 2
    skin = "dry" if dry else "skin"
    if not dry:
        # sitting up on its haunches: the body pitched up from the hips, belly out
        body = root.group("body", (0, 14, 16), (42, 0, 0))
        b1.rounded_box(body, "body", (0, 26, 8), (52, 26, 44), skin, 5)
        b1.rounded_box(body, "belly", (0, 22, -14), (40, 20, 6), "belly", 3)
        warts(body, "wart", (0, 38, 14), (20, 3, 16), 14, rnd)
        hd = body.group("hi_head", (0, 34, -12), (-40, 0, 0))   # the head levels out to look ahead
        head(hd, "head", (0, 38, -22), 48, 26, 26, sac=1.2)
        for sd in (-1, 1):
            eye(hd, f"eye_{sd}", (sd * 15, 52, -28), 12)
        crown(hd, "crown", (0, 55, -20), 13, 10)
        hd.box("collar_pad", (0, 26, -14), (54, 3, 34), "pad")              # a lily-pad collar under the chin
        # a heavy mantle of pond weed over its shoulders, falling down its back to a ragged hem on the ground
        mantle = root.group("mantle", (0, 44, 26))
        b1.rounded_box(mantle, "mantle_shoulders", (0, 44, 24), (60, 8, 22), "weed", 3)
        mantle.box("mantle_back", (0, 24, 36), (56, 40, 6), "weed", rotation=(22.5, 0, 0))
        for i in range(8):
            x = -24 + i * 7
            length = 6 + (i * 5 % 7)
            mantle.box(f"mantle_hem_{i}", (x, 3 + length / 2 - 2, 44 + (i % 2)), (6, length, 3), "weed_light" if i % 2 else "weed")
        legs = root.group("legs", (0, 0, 0))
        for sd in (-1, 1):
            # haunches folded at its sides, knees up; hands resting on the knees
            haunch(legs, f"leg_{sd}", sd, (sd * 26, 14, 14), 18, skin, foot_size=(16, 24))
            arm_pair(legs, f"arm_{sd}", sd, (sd * 22, 40, 2), (sd * 30, 30, -6), (sd * 30, 24, -10), 8, skin, hand_size=(10, 10))
        # a cattail sceptre in its right hand
        legs.box("sceptre", (32, 34, -4), (2, 44, 2), "reed")
        legs.box("sceptre_head", (32, 58, -4), (4, 10, 4), "mouth")
        return
    # dried: the mantle shed, down on all fours, hunched and lean
    lift = 0
    body = root.group("body", (0, 18 + lift, 6))
    b1.rounded_box(body, "body", (0, 18 + lift, 8), (46, 18, 48), skin, 4)
    body.box("spine", (0, 30 + lift, 10), (3, 5, 40), "dry_dark")
    for sd in (-1, 1):
        ribs(body, sd * 23.4, 18 + lift, -8, 26, 6, 11)
    hd = root.group("hi_head", (0, 24 + lift, -16))
    head(hd, "head", (0, 22 + lift, -24), 44, 22, 24, sac=0.5, dried=True)
    for sd in (-1, 1):
        eye(hd, f"eye_{sd}", (sd * 14, 34 + lift, -28), 12, sunken=True)
    crown(hd, "crown", (2, 36 + lift, -20), 13, 10, tilt=(0, 0, -22.5))
    legs = root.group("legs", (0, 0, 0))
    for sd in (-1, 1):
        haunch(legs, f"leg_{sd}", sd, (sd * 25, 14, 20), 15, skin, lean=True)
        arm_pair(legs, f"arm_{sd}", sd, (sd * 18, 12, -16), (sd * 27, 8, -24), (sd * 24, 0.5, -36), 6, skin)
    for i in range(5):                                          # rags of the dead mantle still caught on its back
        body.box(f"rag_{i}", (-12 + i * 6, 26 + lift, 30), (4, 10 + i % 3 * 3, 1.5), "weed")
    dried(root, rnd, (0, 18 + lift, 6), (23, 24), 27 + lift)


BUILD = {"A": bullfrog, "B": horned_maw, "C": bog_king}


def build(key, phase):
    model = Model(f"occultech_mire_monarch_{key.lower()}{phase}")
    BUILD[key](model, phase)
    return model


VIEWS = b1.VIEWS


def main():
    for old in OUT.glob("*"):
        if old.is_dir():
            shutil.rmtree(old)
        elif old.suffix == ".png" or old.name == "README.md":
            old.unlink()
    items = []
    for key, title in DIRECTIONS.items():
        for phase in (1, 2):
            out = OUT / f"{key}{phase}"
            out.mkdir(parents=True, exist_ok=True)
            model = build(key, phase)
            model.write_bbmodel(out / f"{model.name}.bbmodel")
            v2.run_blender(model.render_json(PALETTE), out, VIEWS)
            stats = model.stats()
            (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
            label = f"{title}, {'big' if phase == 1 else 'dried'}"
            sheet.direction_sheet(out, f"Mire Monarch - {key} {label}", stats, out / "sheet.png")
            items.append((f"{key}{phase}", label))
            print(key, phase, stats["size_blocks"], stats["cubes"])
    sheet.compare_sheet(OUT, items, OUT / "compare.png", heading="Mire Monarch - three directions, big and dried (session 1)",
                        views=("flat_34", "sil_side", "clay_34"))
    sheet.compare_sheet(OUT, items, OUT / "compare_front.png", heading="Mire Monarch - front and side",
                        views=("flat_front", "flat_side"))


if __name__ == "__main__":
    main()
