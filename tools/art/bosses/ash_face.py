"""The Elder of Ash, session 1 step 2: the face study, on B2's front half (picked 2026-10-14).

Three faces of the elder toad sage on the same front half of B2 (the bust, the beefy front legs with their big
fingers, the foot of the volcano behind), so each face is judged in the frame it will live in. Shared by all three:
the frog's face (the eyes standing up on the corners of a wide flat head, a mouth as wide as the head), a heavy brow,
the parotoid glands, the pipe in the boss's right mouth corner with smoke from its bowl, and the glow kept to the
eyes, the pipe's ember and the lava.

  F1  The Old Chief      a heavy ridged brow shelf, a scar through the right eye (narrowed), thick jowls, a long
                         pipe clenched hard in the corner of the mouth
  F2  The Hermit         long ash-white brows drooping past the eyes, sleepy lids over slivers of glow, a hanging
                         dewlap under the chin; a long pipe resting in the corner
  F3  The Ember Sage     a single heavy brow ridge, wide open eyes with a bar pupil, sage markings in ember round
                         the eyes and down to the mouth corners; the same long pipe

Units are model pixels (16 = one block), y up, the model faces -z; +x is his right.

Run from the repository root: python tools/art/bosses/ash_face.py
"""
import json
import math
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import monarch_s1 as m1, unbound_face as uf  # noqa: E402

OUT = ROOT / "docs/art/bosses/elder_of_ash/overhaul/s1_face"
PALETTE = {
    "skin": (96, 88, 56), "skin_dark": (74, 68, 44), "flank": (112, 90, 60), "limb": (126, 102, 66),
    "belly": (170, 146, 102), "lip": (62, 50, 36), "mouth": (34, 24, 20), "wart": (82, 76, 48),
    "gland": (88, 82, 52), "toe": (130, 104, 70), "pad": (150, 122, 84),
    "brow": (70, 64, 42), "brow_ash": (196, 192, 184), "brow_ash_dark": (150, 146, 140), "scar": (140, 112, 92),
    "mark": (236, 150, 52), "eye_socket": (40, 30, 22),
    "eye": (255, 186, 60), "eye_hot": (255, 226, 140), "pupil": (40, 22, 14),
    "skin_ash": (110, 104, 84), "ash": (128, 124, 118), "ash_dark": (100, 96, 92), "basalt": (60, 56, 60), "basalt_lit": (82, 78, 82),
    "lava": (255, 120, 30), "lava_hot": (255, 214, 110),
    "pipe": (92, 60, 36), "pipe_dark": (66, 42, 26), "pipe_metal": (150, 140, 120), "ember": (255, 140, 40),
    "smoke": (196, 192, 188, 110), "smoke_thin": (206, 202, 198, 70),
}
GLOW = {"eye", "eye_hot", "lava", "lava_hot", "ember"}
FACES = {"F1": "The Old Chief", "F2": "The Hermit", "F3": "The Ember Sage"}
T = 1.25                                    # B2's height over step 1's toad

octo, ball, tapered, beam = m1.octo, m1.ball, m1.tapered, m1.beam


# ---- the frame shared by every face --------------------------------------------------------------------------------

def finger(g, name, base, yaw, length, w):
    """A thick toad finger lying on the ground from base, yawed (0 = straight ahead), ending in a broad pad."""
    a = math.radians(yaw)
    tip = (base[0] + math.sin(a) * length, base[1], base[2] - math.cos(a) * length)
    mid = ((base[0] + tip[0]) / 2, base[1], (base[2] + tip[2]) / 2)
    g.box(name, mid, (w, w * 0.8, length), "toe", rotation=(0, -yaw, 0))
    g.box(name + "_pad", (tip[0], base[1] + 0.3, tip[2]), (w * 1.4, w * 0.95, w * 1.2), "pad", rotation=(0, -yaw, 0))


def front_leg(root, sd):
    """A beefy front leg: the upper arm out to an elbow standing clear of the body, a heavy forearm, a broad hand with
    four big fingers."""
    sh, el, wr = (sd * 36, 18, -16), (sd * 57, 15, -30), (sd * 52, 5, -44)
    arm = root.group(f"arm_{sd}", sh)
    beam(arm, f"arm_{sd}_upper", sh, el, 16, "limb", 15)
    arm.box(f"arm_{sd}_elbow", el, (15, 14, 15), "limb")
    beam(arm, f"arm_{sd}_fore", el, wr, 14, "limb", 13)
    arm.box(f"arm_{sd}_palm", (sd * 52, 3.0, -48), (18, 6, 14), "toe")
    for i, yaw in enumerate((-50, -17, 17, 50)):
        finger(arm, f"arm_{sd}_finger{i}", (sd * 52 + sd * yaw * 0.1, 2.8, -52), sd * yaw, 11 if abs(yaw) < 30 else 9, 6.4)


def volcano_foot(root):
    """The foot of the volcano behind the head: an ash-grey crust, the basalt cone's lower half (a core and eight
    leaning slabs), two lava streams."""
    v = root.group("volcano", (0, 52, 14))
    v.box("crust", (0, 55, 10), (78, 8, 58), "ash")
    for i, (x, z, s) in enumerate(((-34, -10, 9), (-24, -20, 7), (30, -14, 8), (36, 4, 7), (-36, 14, 8), (22, -22, 6))):
        v.box(f"crust_rock{i}", (x, 59.5, z), (s, 5, s), "ash_dark", rotation=(0, i * 23, 0))
    v.box("cone_core", (0, 80, 14), (34, 44, 34), "basalt")
    for i in range(8):
        yaw = i * 45
        a = math.radians(yaw)
        c = (math.sin(a) * 18, 78, 14 - math.cos(a) * 18)
        v.box(f"cone_{i}", c, (26, 44, 8), "basalt_lit" if i in (0, 7) else "basalt", rotation=(18, -yaw, 0))
    for sd, x in ((-1, -8), (1, 10)):                    # lava running down the cone's front face onto the crust
        beam(v, f"lava_{sd}_a", (x * 0.5, 100, -1), (x, 72, -12), 3.4, "lava", 1.4)
        beam(v, f"lava_{sd}_b", (x, 72, -12), (x * 1.5, 59.5, -22), 3.2, "lava", 1.4)


def bust(root):
    """B2's front half: the body, the pale chest, the warts, the beefy front legs, the volcano's foot behind."""
    b = root.group("body", (0, 30, 0))
    b.box("torso", (0, 27, 4), (88, 42, 62), "flank")
    b.box("hump", (0, 50, 8), (72, 8, 50), "skin")
    b.box("chest", (0, 15, -27.6), (58, 18, 1.4), "belly")
    for i, (x, y, z) in enumerate(((-30, 46.5, -12), (32, 46.5, -8), (-44.5, 30, -6), (44.5, 28, -2), (-20, 54.5, 14), (24, 54.5, 20))):
        b.box(f"wart{i}", (x, y, z), (6, 3, 6), "wart")
    volcano_foot(root)
    for sd in (-1, 1):
        front_leg(root, sd)


def head_base(h, jowls=False, dewlap=False):
    """The frog's head, vanilla's way: a big flat upper head over a thin jaw, the mouth the seam between them, low on
    the face and right round it. The front mouth line bends down at the face's corners and runs back along the sides.
    A chamfer on the snout's top edge, nostrils, the pale throat, the glands behind the eyes."""
    h.box("skull", (0, 29, -40), (66, 18, 38), "skin")
    h.box("snout_bevel", (0, 35.4, -56.4), (65.8, 8, 8), "skin", rotation=(45, 0, 0))
    h.box("brow_dip", (0, 38.6, -48), (14, 1.2, 10), "skin_dark")
    h.box("jaw", (0, 16.5, -38.5), (63, 7, 35), "skin_dark")
    h.box("mouth", (0, 19.9, -38.8), (63.4, 1.4, 35.6), "mouth")
    h.box("mouth_front", (0, 20.6, -59.2), (48, 1.6, 0.4), "mouth")
    for sd in (-1, 1):
        # the bend: from the end of the front line down to the face's corner, then back along the side
        h.box(f"mouth_bend_{sd}", (sd * 27.6, 19.1, -59.2), (7.8, 1.6, 0.4), "mouth", rotation=(0, 0, -sd * 23))
        h.box(f"mouth_side_{sd}", (sd * 33.2, 18.6, -44), (0.4, 1.6, 30), "mouth")
        h.box(f"nostril_{sd}", (sd * 7, 38.2, -55), (2.4, 0.6, 2.0), "mouth")
        h.box(f"gland_{sd}", (sd * 29, 40, -26), (10, 5, 16), "gland")
        if jowls:                                       # heavy jowls hanging off the jaw's back corners
            h.box(f"jowl_{sd}", (sd * 29, 14, -28), (8, 9, 14), "skin_dark")
    h.box("throat", (0, 10.5, -34), (54, 5, 26), "belly")
    if dewlap:                                          # the old toad's hanging throat fold
        h.box("dewlap", (0, 7, -44), (28, 5, 12), "belly")


def eye(h, sd, c, open_=0.5, size=(19, 12, 15)):
    """The frog's eye bulging up on the head's corner (vanilla's placement): a block of skin with a smaller cap on top
    so it reads round, the glowing eye in its front, the upper lid down over it. open_: how much of the eye shows
    (0 = shut, 1 = wide). Returns the front z."""
    x, y, z = c
    h.box(f"eye_block_{sd}", c, size, "skin")
    h.box(f"eye_cap_{sd}", (x, y + size[1] / 2 + 1.2, z + 0.5), (size[0] - 5, 2.4, size[2] - 4), "skin")
    front = z - size[2] / 2
    eh = 1.4 + 4.4 * open_
    ey = y - 1.0
    h.box(f"eye_socket_{sd}", (x, ey, front - 0.2), (13.4, eh + 1.4, 0.4), "eye_socket")
    h.box(f"eye_{sd}", (x, ey, front - 0.4), (12, eh, 0.4), "eye")
    h.box(f"pupil_{sd}", (x, ey, front - 0.6), (7.2, min(1.2, eh * 0.4), 0.4), "pupil")
    lid_h = y + size[1] / 2 - (ey + eh / 2)             # the lid fills the eye block's front above the eye
    h.box(f"lid_{sd}", (x, ey + eh / 2 + lid_h / 2, front - 0.7), (size[0] - 1, lid_h, 1.2), "skin_dark")
    return front


def pipe(h, held="clenched"):
    """The sage's long pipe from his right mouth corner, out and down, the metal bowl turned up with an ember in it,
    smoke rising from the bowl."""
    m = (31, 19.6, -55)
    bowl = (46, 8, -80)
    p = h.group("pipe", m)
    p.box("pipe_mouthpiece", m, (3.6, 3.4, 6), "pipe_metal", rotation=(0, -28, 0))
    beam(p, "pipe_stem", m, (bowl[0] - 0.8, bowl[1] + 2, bowl[2] + 3), 2.6, "pipe", 2.6)
    beam(p, "pipe_ferrule", (bowl[0] - 2.0, bowl[1] + 3.2, bowl[2] + 5.6), (bowl[0] - 0.4, bowl[1] + 1.6, bowl[2] + 1.6),
         3.4, "pipe_metal", 3.4)
    p.box("pipe_bowl", (bowl[0], bowl[1] + 4, bowl[2]), (6, 8, 6), "pipe_metal")
    p.box("pipe_ember", (bowl[0], bowl[1] + 8.1, bowl[2]), (4.2, 0.4, 4.2), "ember")
    if held == "clenched":                               # the lip bunched up round the stem
        h.box("lip_clench", (30.4, 21.4, -55.4), (5, 2.2, 6), "skin", rotation=(0, -28, 8))
    for i in range(4):                                   # smoke curling up from the bowl
        t = i / 3
        s = 4 + 5 * t
        p.box(f"smoke{i}", (bowl[0] + 3 * t + math.sin(i * 1.9) * 2, bowl[1] + 14 + 20 * t, bowl[2] + 4 * t), (s, s, s),
              "smoke" if i < 2 else "smoke_thin", rotation=(i * 17, i * 29, i * 11))


# ---- the three faces ---------------------------------------------------------------------------------------------

EYE_AT = 23, 45.5, -47


def old_chief(model):
    root = model.group("root", (0, 0, 0))
    bust(root)
    h = root.group("hi_head", (0, 26, -26))
    head_base(h, jowls=True)
    x, y, z = EYE_AT
    for sd in (-1, 1):
        front = eye(h, sd, (sd * x, y, z), open_=0.2 if sd > 0 else 0.5)
        # a heavy brow shelf on the eye's top front edge, jutting out over it, its inner end low (the scowl)
        h.box(f"brow_{sd}", (sd * (x + 0.5), y + 6.6, front + 3.2), (21, 4.4, 10), "brow", rotation=(-10, 0, sd * 15))
    # the old scar through the right eye: one pale line across the brow, the lid and below the eye
    h.box("scar", (x + 1.5, y + 0.5, z - 7.5 - 1.6), (1.6, 15, 0.4), "scar", rotation=(0, 0, -14))
    pipe(h, "clenched")


def hermit(model):
    root = model.group("root", (0, 0, 0))
    bust(root)
    h = root.group("hi_head", (0, 26, -26))
    head_base(h, dewlap=True)
    x, y, z = EYE_AT
    for sd in (-1, 1):
        front = eye(h, sd, (sd * x, y, z), open_=0.12)
        # long ash-white brows: three tufts from over the eye's inner end, sweeping out and drooping past its corner
        for i, (ox, oy, ln, th, tilt) in enumerate(((-7, 6.2, 20, 3.4, -8), (-4, 4.0, 19, 3.0, -24), (-1, 1.8, 16, 2.6, -40))):
            a = math.radians(tilt)
            cx = sd * (x + ox + ln / 2 * math.cos(a))
            cy = y + oy + ln / 2 * math.sin(a)
            h.box(f"brow_{sd}_{i}", (cx, cy, front - 1.4 - i * 0.8), (ln, th, 5 - i),
                  "brow_ash" if i < 2 else "brow_ash_dark", rotation=(0, 0, sd * tilt))
    pipe(h, "resting")


def ember_sage(model):
    root = model.group("root", (0, 0, 0))
    bust(root)
    h = root.group("hi_head", (0, 26, -26))
    head_base(h)
    x, y, z = EYE_AT
    for sd in (-1, 1):
        front = eye(h, sd, (sd * x, y, z), open_=0.85)
        # one heavy brow ridge over each eye, low over its inner end
        h.box(f"brow_{sd}", (sd * (x + 0.5), y + 6.8, front + 2.6), (21, 3.6, 8), "brow", rotation=(-8, 0, sd * 11))
        # sage markings: an ember bar under the eye, one beside it, a stripe down the cheek to the mouth
        h.box(f"mark_under_{sd}", (sd * x, y - 5.0, front - 0.3), (12, 1.6, 0.4), "mark")
        h.box(f"mark_outer_{sd}", (sd * (x + 8.7), y - 0.5, front + 2.5), (0.4, 8, 5), "mark")
        h.box(f"mark_cheek_{sd}", (sd * (x + 4), 28.5, -59.2), (1.8, 10, 0.4), "mark", rotation=(0, 0, sd * -16))
    pipe(h, "clenched")


BUILD = {"F1": old_chief, "F2": hermit, "F3": ember_sage}
VIEWS = [
    {"name": "front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 2.2, "dist": 7.5, "target_z": 2.0, "player": False},
    {"name": "three_quarter", "mode": "flat", "camera": "persp", "yaw": 32, "height": 2.8, "dist": 8, "target_z": 2.0,
     "player": False},
    {"name": "player_eye", "mode": "flat", "camera": "persp", "yaw": -18, "height": 1.62, "dist": 7.0, "target_z": 2.2,
     "lens": 28, "player": False},
    {"name": "side", "mode": "flat", "camera": "persp", "yaw": 90, "height": 2.4, "dist": 12, "target_z": 2.3, "player": False},
    {"name": "clay", "mode": "clay", "camera": "persp", "yaw": 25, "height": 2.6, "dist": 9, "target_z": 2.2, "player": False},
]


def render(model, out, views=VIEWS, extra=None):
    """The views with the eyes, the ember and the lava glowing (the Unbound's two-pass glow)."""
    from PIL import Image, ImageChops, ImageFilter
    uf._blender(model.render_json(PALETTE), out, views, extra)
    dark = {k: (v if k in GLOW else (0, 0, 0, v[3]) if len(v) > 3 else (0, 0, 0)) for k, v in PALETTE.items()}
    dark = {k: ((0, 0, 0) if k not in GLOW else v) for k, v in dark.items()}
    glow_dir = out / "glow"
    uf._blender(model.render_json(dark), glow_dir, [dict(v, light="FLAT") for v in views],
                dict(extra or {}, ground=[0, 0, 0], sky=[0, 0, 0], player_color=[0, 0, 0]))
    for v in views:
        if v["mode"] != "flat":
            continue
        base = Image.open(out / f"{v['name']}.png").convert("RGB")
        mask = Image.open(glow_dir / f"{v['name']}.png").convert("RGB")
        lit = mask.convert("L").point(lambda x: 255 if x > 24 else 0)
        base.paste(mask, (0, 0), lit)
        bloom = mask.filter(ImageFilter.GaussianBlur(7)).point(lambda x: min(255, int(x * 1.1)))
        ImageChops.screen(base, bloom).save(out / f"{v['name']}.png")
    shutil.rmtree(glow_dir)


def main(keys=None):
    keys = keys or list(FACES)
    OUT.mkdir(parents=True, exist_ok=True)
    for key in keys:
        out = OUT / key
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        model = Model(f"occultech_elder_of_ash_face_{key.lower()}")
        BUILD[key](model)
        model.write_bbmodel(out / f"{model.name}.bbmodel")
        render(model, out)
        stats = model.stats()
        (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        print(key, stats["cubes"], stats["size_blocks"])
    if all((OUT / k / "front.png").exists() for k in FACES):
        sheet.compare_sheet(OUT, list(FACES.items()), OUT / "faces.png",
                            heading="The Elder of Ash - the sage's face, three options (step 2)",
                            views=("front", "three_quarter", "player_eye", "clay"))


if __name__ == "__main__":
    main(sys.argv[1:] or None)
