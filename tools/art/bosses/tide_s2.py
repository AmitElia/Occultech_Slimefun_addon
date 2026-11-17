"""The Tidebreaker redesign, session 2: design lock (plan: docs/art/bosses/tidebreaker/overhaul/plan.md).

The approved blockout (tide_blockout.py) rebuilt as two rigs, every cube on whole texels:
- `occultech_tidebreaker_mount`, worn by the zombie nautilus: `base` (pivot in the coil, for pitch and sinking), `shell`,
  `hull` (the longship's bow), `figurehead` + `figure_upper` / `figure_jaw` (carved: they never move), `lantern` with
  `glow_lantern` (it swings), `flesh` (the body and hood), `eye_*` with `pupil_*` and `lid_*`, and twelve tentacles of
  three bones each, `tent<n>_1` to `_3`.
- `occultech_tidebreaker`, worn by the drowned: `rider`, `thigh_*` > `shin_*`, `torso` (tunic, cloak, collar), `hi_head`,
  `arm_*` > `forearm_*` > `hand_*`, and `spear` on the right hand.
Bones hang straight in the bind pose and are aimed per pose. The rider is scaled 1.5 instead of 1.45, so that a vanilla
head (8 texels) is exactly 12 units.

The barnacles keep their approved sizes (a half-texel grid), an agreed exception to whole texels. The head's texel
tiles are preview only: the model has one painted cube.

Run from the repository root, with a folder holding the 26.2 zombie textures as the last argument:
python tools/art/bosses/tide_s2.py [pose ...] <folder>
"""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import archevoker_s2 as a2, monarch_s1 as ms, tide_blockout as tb, tide_faces as tf, tide_faces2 as tf2  # noqa: E402
from bosses import tide_silhouettes as t1, tide_take2 as t2, volley_crone_s2 as v2  # noqa: E402
from bosses.archevoker_s2 import aim, cubes_in, group, new_bone, translate  # noqa: E402
from bosses.tide_silhouettes import CY, CZ, R, W, _n, beam, plate  # noqa: E402

OUT = ROOT / "docs/art/bosses/tidebreaker/overhaul/s2_design"
K = 1.5
tf.K = tf2.K = K
PALETTE = dict(tf.PALETTE, hitbox=(220, 60, 60))
SIDES = {1: "right", -1: "left"}
DECK_Y = CY + 2
ZF = t1.front_z(DECK_Y, R)
FEET = (0.0, DECK_Y + 1, ZF - 3.0)                    # back against the shell: the deck is short here
HIP = 11.6 * K
SHOULDER = (5.4 * K, HIP + 11.6 * K, 0.0)
UPPER, FORE, THIGH, SHIN = 5.5 * K, 6.5 * K, 6 * K, 5.5 * K
MOUTH = np.array([0, CY - 4, CZ + R * 0.62 + 11])
SEG = (10, 9, 7)
LID = (1.0, 5.0, 10.0)


# ---- the mount -----------------------------------------------------------------------------------------------------

def flesh(g):
    zb = CZ + R * 0.62
    ms.octo(g, "body", (0, CY - 3, zb + 3), (W - 6, R * 0.95, 16), "body", cham=0.32)
    ms.octo(g, "hood", (0, CY + R * 0.4, zb + 7), (W - 2, 11, 19), "hood", cham=0.4, rot=(-18, 0, 0))
    beam(g, "siphon", (0, CY - 12, zb + 8), (0, CY - 14, zb + 16), 5.5, "body")


def eyes(m, base):
    zb = CZ + R * 0.62
    for s, side in SIDES.items():
        c = np.array((s * ((W - 6) / 2 + 0.8), CY + 2, zb + 5))
        eye = base.group(f"eye_{side}", tuple(c))
        plate(eye, f"iris_{side}", tuple(c), 4.4, 1.6, "naut_eye")
        pupil = eye.group(f"pupil_{side}", tuple(c))
        pupil.box(f"slit_{side}", tuple(c + (s * 0.9, 0, 0)), (1, 2, 6), "pupil")
        lid = eye.group(f"lid_{side}", tuple(c + (0, 4.4, 0)))
        lid.box(f"lidplate_{side}", tuple(c + (s * 1.5, 2.4, 0)), (1, 5, 10), "hood")


def tentacles(base):
    """Twelve tentacles of three bones each, hanging straight in the bind pose."""
    for i in range(12):
        a = math.radians(i * 30 + 15)
        ring = 9 if i % 2 == 0 else 6
        p = MOUTH + (math.cos(a) * ring, math.sin(a) * ring * 0.8, 0)
        scale = (1.0 if i % 2 == 0 else 0.7) * (1 + 0.15 * ((i * 7) % 3))
        parent = base
        for j, (ln, w) in enumerate(zip(SEG, (4.4, 3.4, 2.4))):
            ln = round(ln * scale)
            bone = parent.group(f"tent{i}_{j + 1}", tuple(p))
            bone.box(f"tentacle{i}_{j}", tuple(p - (0, ln / 2 - 0.5, 0)), (w, ln + 1, w), "tentacle")
            p = p - (0, ln, 0)
            parent = bone


PREFIX = {"shell": ("keel_", "shoulder_", "flank_", "dome_", "whorl_", "callus_", "stripe_", "lash_", "net_", "old_spear"),
          "hull": ("strake", "rail_", "stem", "forefoot", "cutwater", "deck", "shield_", "rack"),
          "flesh": ("body", "hood", "siphon"), "figurehead": ("neck",)}


def mount_rig(name):
    m = Model(name)
    base = m.group("base", (0, CY, CZ))
    t1.shell(base)
    flesh(base)
    top, _ = t1.bow(base, d_top=20, d_bot=4, top=46, step=3.6, clinker=True, flank_back=11, flare=0.22, sheer=6)
    base.box("deck", (0, DECK_Y, (top[2] + ZF) / 2 + 1), (W - 4, 1.6, ZF - top[2] + 2), "wood_dark")
    tb.dragon(base, top)
    group(m, "upper").name, group(m, "jaw").name = "figure_upper", "figure_jaw"
    t2.shields(base, 46, 20, 6)
    t1.lashing(base, "lash_bow", CZ - 2, out=2.6)
    t1.lashing(base, "lash_bow2", CZ + 5, out=1.6)
    t1.net(base, 262, 352)
    seat = np.array([0, DECK_Y + 6, ZF + 2])
    t1.stuck_harpoon(base, "old_spear_l", (-W / 2 + 1, CY + 8, CZ + 10), (-0.7, 0.5, 0.5), seat + (-6, 0, 0))
    t1.stuck_harpoon(base, "old_spear_r", (W / 2 - 1, CY - 4, CZ + 6), (0.8, 0.15, 0.55), seat + (6, 0, 0))
    for i in range(2):
        beam(base, f"rack{i}", (W / 2 - 1.5, DECK_Y + 2 + i * 1.8, top[2] + 7), (W / 2, DECK_Y + 9 + i * 1.8, ZF + 4), 1.3,
             "wood")
    own = [c for c in base.children if not hasattr(c, "children")]
    for bone, names in PREFIX.items():
        new_bone(m, base, bone, base.origin, [c for c in own if c.name.startswith(names)])
    hang = tf.S + (0, -5, -15)
    lamp = new_bone(m, base, "lantern", tuple(hang), [c for c in own if c.name.startswith("lantern")])
    new_bone(m, lamp, "glow_lantern", tuple(hang), [c for c in lamp.children if not hasattr(c, "children") and c.name == "lantern"])
    left = [c.name for c in base.children if not hasattr(c, "children")]
    assert not left, left
    eyes(m, base)
    tentacles(base)
    return m


# ---- the Viking ----------------------------------------------------------------------------------------------------

def spear(g, hand):
    """Hanging tip down in the bind pose, so that aim() points it."""
    hand = np.array(hand, float)
    d, name = np.array((0.0, -1.0, 0.0)), "spear"
    butt, mid, tip = hand - d * 24, hand + d * 3, hand + d * 30   # two shaft cubes: one item model stops at 48 units
    beam(g, name + "_shaft", butt, mid, 1.5, "wood")
    beam(g, name + "_shaft2", mid, tip, 1.5, "wood")
    beam(g, name + "_socket", tip - d * 1.5, tip + d * 1.5, 2.2, "iron")
    side = np.array((1.0, 0.0, 0.0))
    t1.plank(g, name + "_blade", tip + d * 1.2, tip + d * 9.5, 3.2, 0.8, "iron", up=side)
    t1.plank(g, name + "_point", tip + d * 9.0, tip + d * 11.5, 1.6, 0.8, "iron", up=side)
    beam(g, name + "_butt", butt - d * 0.6, butt + d * 0.8, 2.0, "iron")


def viking_rig(parent, feet, preview):
    feet = np.array(feet, float)
    r = parent.group("rider", tuple(feet))
    hip = feet + (0, HIP, 0)
    x, y, z = hip
    for s, side in SIDES.items():
        h = hip + (s * 2.2 * K, 0, 0)
        th = r.group(f"thigh_{side}", tuple(h))
        th.box(f"thighb_{side}", tuple(h - (0, THIGH / 2 - 0.5, 0)), (6, THIGH + 1, 6), "leather_dark")
        kn = h - (0, THIGH, 0)
        sh = th.group(f"shin_{side}", tuple(kn))
        sh.box(f"wrap_{side}", tuple(kn - (0, SHIN / 2 - 0.5, 0)), (6, SHIN + 1, 6), "leather")
        sh.box(f"boot_{side}", tuple(kn - (0, SHIN + 0.6, 1.5)), (7, 4, 9), "leather_dark")
    t = r.group("torso", tuple(hip))
    t.box("tunic_hips", (x, y + 1.4 * K, z), (9 * K, 3 * K, 5 * K), "leather")
    t.box("belt", (x, y + 3.2 * K, z), (9.4 * K, 1.4 * K, 5.4 * K), "leather_dark")
    t.box("buckle", (x, y + 3.2 * K, z - 2.8 * K), (2 * K, 1.6 * K, 1), "iron")
    for i, (dx, ln, dz) in enumerate(((-3.4, 5.5, -1), (-1.2, 3.5, -1), (1.3, 6.5, -1), (3.4, 4, -1), (-2.6, 5, 1), (2.2, 6, 1))):
        t.box(f"hem{i}", (x + dx * K, y - ln / 2 * K + 0.2, z + dz * 2.3 * K), (2 * K, ln * K, 1), "leather",
              rotation=(dz * 6, 0, dx * 2))
    t.box("chest", (x, y + 8 * K, z), (8 * K, 10 * K, 4 * K), "leather")
    t.box("chest_tear", (x + 1.6 * K, y + 8.5 * K, z - 2.1 * K), (2.6 * K, 3.2 * K, 1), "skin")
    t.box("fur_collar", (x, y + 12.4 * K, z + 0.4 * K), (10.4 * K, 2.4 * K, 6 * K), "fur")
    t.box("cloak", (x, y + 7.5 * K, z + 3.1 * K), (9.6 * K, 9 * K, 1), "leather_dark", rotation=(6, 0, 0))
    for i, (dx, ln) in enumerate(((-3.6, 6), (-1.2, 9), (1.2, 5), (3.6, 8))):
        t.box(f"cloak_strip{i}", (x + dx * K, y + 3 * K - ln / 2 * K, z + 3.7 * K), (2.2 * K, ln * K, 1), "leather_dark",
              rotation=(10, 0, dx * 1.5))
    # the F3 head, in its own bone; the barnacles that spread onto the collar stay on the torso
    neck_at = hip + (0, 15 * K, -0.4 * K)
    head = t.group("hi_head", tuple(neck_at))
    tf.H[:] = hip + (0, 19 * K, -0.4 * K)
    tf.TOP = tf.H + np.array([0, 4.8 * K, 0])
    bust, tiles = tf.bust, tf2.tiles
    tf.bust = lambda g: g.box("neck", tf.at(0, -5, 0), (5 * K, 3 * K, 5 * K), "skin_dark")
    tf2.tiles = tiles if preview else (lambda *a: None)
    tf2.viking(head, "F3")
    tf.bust, tf2.tiles = bust, tiles
    for c in [c for c in head.children if not hasattr(c, "children") and c.name.startswith("collar_b")]:
        a2.move(c, t)
    for s, side in SIDES.items():
        sh = hip + (s * SHOULDER[0], SHOULDER[1] - HIP, 0)
        arm = t.group(f"arm_{side}", tuple(sh))
        arm.box(f"upper_{side}", tuple(sh - (0, UPPER / 2 - 1, 0)), (6, UPPER + 2, 6), "skin")
        el = sh - (0, UPPER, 0)
        fore = arm.group(f"forearm_{side}", tuple(el))
        fore.box(f"bracer_{side}", tuple(el - (0, FORE / 2 - 0.5, 0)), (6, FORE + 1, 6), "leather")
        wr = el - (0, FORE, 0)
        hand = fore.group(f"hand_{side}", tuple(wr))
        hand.box(f"palm_{side}", tuple(wr - (0, 1, 0)), (5, 5, 5), "skin")
        if s == 1:
            spear(hand.group("spear", tuple(wr)), wr)
    return r


# ---- the poses -----------------------------------------------------------------------------------------------------
#   tent: how the tentacles lie.  base: (pitch, dy).  lid: lid lift.  torso, head: rotations.
#   legs: the ankle in the hip's space, right then left (the knees solve themselves).  arms: (elbow, hand) from the shoulder, in the torso's rest
#   space.  spear: where its tip points, in the torso's rest space.
TENT = {
    "trail": ((.45, -.15, 1), (.3, -.6, .8), (.15, -1, .15)),
    "glide": ((.5, -.05, 1), (.35, 0, 1), (.25, .12, 1)),
    "pulled": ((-.2, -.1, .6), (-.8, 0, -.2), (-.5, .4, -.9)),
    "splay": ((.7, -.5, .6), (1, -.25, .5), (.8, -.02, .6)),
}
# the left foot flat on the deck, the right braced up behind him on the curve of the shell
STANCE = ((2.7, -5.1, 3.4), (-2.5, -9.9, -1.0))
LOW = ((3.4, -5.1, 3.4), (-3.2, -9.9, -1.4))
IDLE_L = ((-1.2, -5.5, 0), (-1.4, -10.5, .5))
POSES = {
    "idle": ("idle: spear upright, swimming slowly", dict(tent="trail", base=(0, 0), lid=0, torso=(-4, 0, 0), legs=STANCE,
             arms=(((1.4, -5.5, -1), (1.4, -8, -5)), IDLE_L), spear=(0, 1, -.06))),
    "glide": ("glide: nose up a little, tentacles streaming", dict(tent="glide", base=(5, 0), lid=0, torso=(-8, 0, 0),
              legs=STANCE, arms=(((1.4, -5.5, -1), (1.4, -8, -5)), IDLE_L), spear=(0, 1, -.1))),
    "ram": ("the ram: tentacles pulled in, bow dipped, spear couched", dict(tent="pulled", base=(-9, 0), lid=0, torso=(-22, 0, 0),
            legs=LOW, arms=(((.6, -4.5, 3), (-.6, -5.5, -4.5)), ((1.2, -3.5, -5), (6, -3.6, -10.5))), spear=(-.1, .3, -1))),
    "winded": ("winded: sagging, the eye wide open, he hangs over the rail", dict(tent="splay", base=(0, -3.5), lid=4, pupil=(0, -1, 2),
               torso=(-24, 8, 0), head=(14, 8, 0), legs=LOW, arms=(((1, -6, -2), (.6, -11.5, -2)), ((-1, -6, -3), (.8, -10.5, -6))),
               spear=(.05, -.42, -1))),
    "throw": ("the volley: drawn back over his shoulder, the left arm aiming", dict(tent="trail", base=(2, 0), lid=0, torso=(8, -14, 0),
              head=(-6, 14, 0), legs=STANCE, arms=(((1.6, 2.6, 3.4), (.8, 6.4, 4.4)), ((-.6, -.6, -5.4), (.6, .6, -10.6))),
              spear=(0, .32, -1))),
    "thrust": ("the thrust: a short jab over the rail", dict(tent="trail", base=(-3, 0), lid=0, torso=(-16, 12, 0), head=(6, -10, 0),
               legs=LOW, arms=(((1.2, -3.5, 1), (-.4, -4.2, -9)), IDLE_L), spear=(0, -.4, -1))),
    "death": ("death: he slumps over the bow, the animal pulls in and sinks", dict(tent="pulled", base=(-13, -11), lid=-3,
              torso=(-58, 0, 10), head=(-20, 0, 14), legs=LOW, arms=(((1, -6, -1), (1, -12, 0)), ((-1, -6, -1), (-1, -12, 0))),
              spear=(.2, -1, -.2))),
}


def pose_mount(m, spec):
    base = group(m, "base")
    pitch, dy = spec["base"]
    base.rotation = [pitch, 0, 0]
    if dy:
        translate(m, base, (0, dy, 0))
    dirs = TENT[spec["tent"]] if isinstance(spec["tent"], str) else spec["tent"]
    amp, phase = spec.get("wave", (0.0, 0.0))                 # session 7: a travelling wave down each tentacle
    for i in range(12):
        a = math.radians(i * 30 + 15)
        sp = np.array([math.cos(a), math.sin(a) * 0.6, 0])
        if spec["tent"] == "splay":                           # lying on the floor: the lower ones spread, not dig in
            sp[1] = max(sp[1], 0.25)
        for j, d in enumerate(dirs):
            sway = amp * math.sin(phase + i * 0.9 + j * 0.8)
            aim(group(m, f"tent{i}_{j + 1}"), tuple(_n(sp * (d[0] + sway) + (0, d[1] + sway * 0.5, d[2]))))
    for side in SIDES.values():
        if spec.get("lid"):
            translate(m, group(m, f"lid_{side}"), (0, spec["lid"], 0))
        if spec.get("pupil"):
            translate(m, group(m, f"pupil_{side}"), spec["pupil"])


def knee(hip_at, ankle):
    """Two-bone solve: where the knee goes for the ankle to land on its mark, bending forward."""
    d = ankle - hip_at
    ln = min(float(np.linalg.norm(d)), THIGH + SHIN - 0.01)
    d = d / np.linalg.norm(d)
    a = (ln * ln + THIGH * THIGH - SHIN * SHIN) / (2 * ln)
    fwd = np.array((0.0, 0.0, -1.0))
    return hip_at + d * a + _n(fwd - d * float(fwd @ d)) * math.sqrt(max(0.0, THIGH * THIGH - a * a))


def pose_rider(m, spec):
    feet = np.array(group(m, "rider").origin, float)
    hip = feet + (0, HIP, 0)
    root = group(m, "rider").parent.world_matrix()
    world = lambda p, mat=root: (mat @ np.array((*p, 1.0)))[:3]
    for foot, side in zip(spec["legs"], ("right", "left")):
        s = 1 if side == "right" else -1
        h = hip + (s * 2.2 * K, 0, 0)
        ft = hip + np.array(foot) * K
        kn = knee(h, ft)
        aim(group(m, f"thigh_{side}"), tuple(world(kn) - world(h)))
        aim(group(m, f"shin_{side}"), tuple(world(ft) - world(kn)))
    torso = group(m, "torso")
    torso.rotation = list(spec["torso"])
    group(m, "hi_head").rotation = list(spec.get("head", (0, 0, 0)))
    tm = torso.world_matrix()
    for (el, ha), side in zip(spec["arms"], ("right", "left")):
        s = 1 if side == "right" else -1
        sh = hip + (s * SHOULDER[0], SHOULDER[1] - HIP, 0)
        a, b, c = (world(p, tm) for p in (sh, sh + np.array(el) * K, sh + np.array(ha) * K))
        aim(group(m, f"arm_{side}"), tuple(b - a))
        aim(group(m, f"forearm_{side}"), tuple(c - b))
    aim(group(m, "spear"), tuple(tm[:3, :3] @ np.array(spec["spear"], float)))


# ---- snap, flicker fix, hitboxes -----------------------------------------------------------------------------------

BARNACLE = re.compile(r"^(b\d+_\d+|helm_b\d|collar_b\d)")
TILE = re.compile(r"^(front|back|left|right)_\d_\d$")
PANEL = ("keel_", "shoulder_", "strake", "helm_plate", "rail_", "stem", "neck", "horn_", "forefoot")


def snap(m):
    """Whole texels. Panels round up so their joints overlap; barnacles keep a half-texel grid; tiles are preview."""
    for c in m.cubes:
        if TILE.match(c.name):
            continue
        lo, hi = np.array(c.frm), np.array(c.to)
        centre, raw = (lo + hi) / 2, hi - lo
        if BARNACLE.match(c.name):
            size = np.maximum(0.5, np.round(raw * 2) / 2)
        else:
            size = np.maximum(1, np.ceil(raw - 0.01) if c.name.startswith(PANEL) else np.round(raw))
        c.frm, c.to = (centre - size / 2).tolist(), (centre + size / 2).tolist()


def model(key, preview=True):
    """The mount with the rider standing on it, posed."""
    m = mount_rig(f"tide_{key}")
    viking_rig(group(m, "base"), FEET, preview)
    pose_mount(m, POSES[key][1])
    pose_rider(m, POSES[key][1])
    snap(m)
    return m


def export():
    from bosses.coven_s2 import _resolve
    out = OUT / "design"
    out.mkdir(parents=True, exist_ok=True)
    mt = mount_rig("occultech_tidebreaker_mount")
    pose_mount(mt, POSES["idle"][1])
    snap(mt)
    _resolve(mt, {})
    bb = mt.to_bbmodel()
    add_hitbox(bb, (-20.0, 0.0, -30.0), (20.0, 56.0, 40.0))
    (out / "occultech_tidebreaker_mount_blockout.bbmodel").write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    rd = Model("occultech_tidebreaker")
    viking_rig(rd.group("carrier", (0, 0, 0)), (0, 0, 0), False)
    pose_rider(rd, POSES["idle"][1])
    snap(rd)
    _resolve(rd, {})
    hb = ((-10.0, 0.0, -8.0), (10.0, 52.0, 8.0))
    bb = rd.to_bbmodel()
    add_hitbox(bb, *hb)
    (out / "occultech_tidebreaker_blockout.bbmodel").write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    geo = lambda mm: sum(1 for g in mm.groups if any(not hasattr(c, "children") for c in g.children))
    stats = {"mount": dict(mt.stats(), bones_with_geometry=geo(mt)), "rider": dict(rd.stats(), bones_with_geometry=geo(rd),
             hitbox_blocks=[round((b - a) / 16, 2) for a, b in zip(*hb)])}
    (OUT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    (OUT / "parts.md").write_text("# The Tidebreaker blockout parts (session 2)\n\nGenerated by `tools/art/bosses/tide_s2.py`.\n\n"
                                  "## occultech_tidebreaker_mount\n\n" + a2.parts_list(mt) + "\n\n## occultech_tidebreaker\n\n"
                                  + a2.parts_list(rd) + "\n", encoding="utf-8")
    print(json.dumps(stats))


VIEWS = [
    {"name": "q", "mode": "flat", "camera": "persp", "yaw": 38, "height": 3.4, "dist": 11, "target_z": 2.6},
    {"name": "side", "mode": "flat", "camera": "persp", "yaw": 90, "height": 2.6, "dist": 11, "target_z": 2.6, "player": False},
    {"name": "eye", "mode": "flat", "camera": "persp", "yaw": -32, "height": 1.62, "dist": 9, "target_z": 2.8, "player": False},
]


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    keys = [a for a in argv if a in POSES]
    if not keys:
        export()
    for key in keys or POSES:
        m = model(key)
        v2.PALETTE.update(tf2.PAL)
        lo, _ = m.bounds()
        print(key, "lowest y", round(float(lo[1]), 1))
        v2.run_blender(m.render_json(v2.PALETTE), OUT / "poses" / key, VIEWS)
    tw, th, pad, top = 400, 300, 12, 60
    img = Image.new("RGB", (pad + 3 * (tw + pad) , top + len(POSES) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "The Tidebreaker: the key poses", font=sheet._font(26), fill=sheet.INK)
    for r, k in enumerate(POSES):
        y = top + r * (th + 34 + pad)
        dr.text((pad, y + th + 6), POSES[k][0], font=sheet._font(17), fill=sheet.DIM)
        for c, v in enumerate(VIEWS):
            f = OUT / "poses" / k / f"{v['name']}.png"
            if f.exists():
                img.paste(sheet._tile(f, tw, th), (pad + c * (tw + pad), y))
    img.save(OUT / "poses.png")


if __name__ == "__main__":
    main(sys.argv[1:])
