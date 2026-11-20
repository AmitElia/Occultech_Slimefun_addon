"""Dread Riders, session 2: design lock (plan: docs/art/bosses/dread_riders/overhaul/plan.md).

Session 1's approved take 2 (dread_concepts.py take2) rebuilt as rigs. The fight puts each rider on its own horse (two
entities), so there are four models, like the Tidebreaker's mount and rider:
- `occultech_dread_vanguard_mount` (the zombie horse: A's spiked charger) and `occultech_dread_vanguard` (the zombie
  lancer in A's armour under C's horned armet);
- `occultech_dread_outrider_mount` (the skeleton horse, buff build, A's rope tack) and `occultech_dread_outrider` (the
  skeleton archer under the reworked steppe helm).

Mount bones: `base` (pivot in the barrel; tilts for the rear) holds the body; `neck` > `head` > `glow_eyes` (and `jaw` on
the skeleton); four legs of three bones, `leg_<fl|fr|hl|hr>` > `_lower` > `_hoof`; `tail`; the charger's `banner` >
`banner_cloth` and `glow_sigil`.
Rider bones: `rider` (pivot at the hip) > `thigh_*` > `shin_*`; `torso` > `hi_head`, `arm_*` > `forearm_*` > `hand_*`;
the lance on `hand_right`; the bow on `hand_left` with `string_upper` / `string_lower`; the nocked arrow on `hand_right`
(hidden until the draw) with `glow_arrow`.
The bind pose is the rest pose (the lance carried, the bow lowered), not straight-hanging arms: it is the pose the models
show between clips. Key poses are rotations of those bones (plus whole-model lift for the rear and gallop).

Cube sizes are whole texels. The faces' patterns (the vanilla eyes, nose and mouth; the skull's sockets and nostril)
are texture: drawn in the previews, left out of the .bbmodel files.

Run from the repository root: python tools/art/bosses/dread_s2.py [vanguard] [outrider]
"""
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, add_hitbox, pivot_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import dread_concepts as dc, volley_crone_s2 as v2  # noqa: E402
from bosses.heartwood_s1 import _n  # noqa: E402
from bosses.heartwood_s2 import euler, turn_to  # noqa: E402

OUT = ROOT / "docs/art/bosses/dread_riders/overhaul/s2_design"
REST = dc.REST
PALETTE = dict(dc.PALETTE, hitbox=(220, 60, 60))
SIDES = {-1: "left", 1: "right"}
HORSE = {"vanguard": "destrier", "outrider": "courser_buff"}
CFG = {"vanguard": dict(take="A", helm="C"), "outrider": dict(take="A", helm="A2")}
DECALS = {"rider": {"eye-1", "eye1", "nose", "mouth"}, "mount": {"socket-1", "socket1", "nasal"}}   # painted later
LEGS = ("fl", "fr", "hl", "hr")
HEAD_K = 1.5        # session 5 review: the heads were small for the bodies; vanilla's horse head at 3x, not 2x


# ==== rig tools ========================================================================================================

def bones_of(m):
    return {g.name: g for g in m.groups}


def subtree(g):
    out = [g]
    for ch in g.children:
        if hasattr(ch, "children"):
            out += subtree(ch)
    return out


def move(item, bone):
    item_parent = item.group if not hasattr(item, "children") else item.parent
    item_parent.children.remove(item)
    bone.children.append(item)
    if hasattr(item, "children"):
        item.parent = bone
    else:
        item.group = bone


def bake(m, helper, bone):
    """Moves every cube under a helper group (an octo/ball/oseg group) onto `bone` with its full rotation, and drops the
    helper. Bones are unrotated in the bind pose, so a cube's bind transform is its world transform."""
    for c in [c for c in m.cubes if helper in subtree_up(c.group)]:
        M = c.group.world_matrix() @ pivot_matrix(c.origin, c.rotation)
        lo, hi = np.array(c.frm), np.array(c.to)
        centre = M @ np.array([*(lo + hi) / 2, 1.0])
        size = hi - lo
        c.frm, c.to = (centre[:3] - size / 2).tolist(), (centre[:3] + size / 2).tolist()
        c.origin = centre[:3].tolist()
        c.rotation = [float(v) for v in euler(M[:3, :3])]
        c.group.children.remove(c)
        bone.children.append(c)
        c.group = bone
    for g in subtree(helper):
        if g in m.groups:
            m.groups.remove(g)
    helper.parent.children.remove(helper)


def subtree_up(g):
    out = [g]
    while g.parent is not None:
        g = g.parent
        out.append(g)
    return out


def bone(m, parent, name, origin):
    return parent.group(name, tuple(float(v) for v in origin))


def sort_into(m, src, rules, default):
    """Moves each cube / helper group directly under `src` to the bone its name picks (first matching rule)."""
    for item in list(src.children):
        name = item.name
        target = default
        for test, b in rules:
            if test(name):
                target = b
                break
        if target is src:
            continue
        if hasattr(item, "children"):
            if item.name in BONE_NAMES:
                move(item, target)
            else:
                bake(m, item, target)
        else:
            move(item, target)


BONE_NAMES = {"head", "headbone", "torso"}


def snap(m):
    for c in m.cubes:
        lo, hi = np.array(c.frm), np.array(c.to)
        centre = (lo + hi) / 2
        size = np.maximum(1, np.round(hi - lo))
        c.frm, c.to = (centre - size / 2).tolist(), (centre + size / 2).tolist()


# ==== the mounts =======================================================================================================

def mount(kind):
    """The mount in its bind (rest) pose, rigged. Returns the model, the frame and named points."""
    f = dc.frame(HORSE[kind], REST)
    m = Model(f"occultech_dread_{kind}_mount")
    root = m.group("build", (0, 0, 0))
    (dc.destrier if kind == "vanguard" else dc.courser)(root, f, CFG[kind]["take"])
    by = f["by"]
    base = bone(m, m.root, "base", (0, by, 0))
    m.root.children.remove(base)
    m.root.children.insert(0, base)
    n0, mid, poll = f["neck"]
    neck = bone(m, base, "neck", n0)
    legs = {}
    for key in LEGS:
        p = f["legs"][key]
        up = bone(m, base, f"leg_{key}", p[0])
        lo = bone(m, up, f"leg_{key}_lower", p[1])
        hf = bone(m, lo, f"leg_{key}_hoof", p[2])
        legs[key] = (up, lo, hf)
    tail = bone(m, base, "tail", f["tail"])
    rules = []
    for key in LEGS:
        up, lo, hf = legs[key]
        rules += [
            (lambda n, k=key: n.startswith(k + "_") and any(s in n for s in ("_hoof", "_pastern", "_fetlock", "_feather", "_cuff")), hf),
            (lambda n, k=key: n.startswith(k + "_") and any(s in n for s in ("_cannon", "_knee", "_greave", "_cop", "_band1")), lo),
            (lambda n, k=key: n.startswith(k + "_"), up),
        ]
    rules += [
        (lambda n: n.startswith(("neck", "crest", "mane", "crinet", "bolt_mane", "collar")), neck),
        (lambda n: n.startswith(("tail", "bolt_tail")), tail),
    ]
    if kind == "vanguard":
        banner = bone(m, base, "banner", f["seat"] + [0, 0, 12])
        top = f["seat"] + [0, 0, 12] + [0, 52, 4]
        cloth = bone(m, banner, "banner_cloth", top + [0, -6, 8])
        sigil = bone(m, base, "glow_sigil", (0, by + 2, -f["L"] - 3))
        rules = [(lambda n: n == "banner_sigil" or (n.startswith("banner") and n[6:].isdigit()), cloth),
                 (lambda n: n.startswith("banner"), banner),
                 (lambda n: n == "boss_sigil", sigil)] + rules
    sort_into(m, root, rules, base)
    if kind == "vanguard":                 # session 6: the banner's sigil glows and takes the tints
        gb = bone(m, cloth, "glow_banner", tuple(cloth.origin))
        for c in [c for c in cloth.children if not hasattr(c, "children") and c.name == "banner_sigil"]:
            c.mat = "crimson"
            move(c, gb)
    # the head: the concept's head group (pivot at the poll, pitched) goes on the neck
    head = bones_of(m)["head"]
    move(head, neck)
    glow = head.group("glow_eyes", tuple(head.origin))
    for c in [c for c in head.children if not hasattr(c, "children") and c.name in ("eye-1", "eye1")]:
        move(c, glow)
    if kind == "outrider":
        P = np.array(poll)
        jaw = head.group("jaw", tuple(P + [0, -7, -8]))
        for c in [c for c in head.children if not hasattr(c, "children") and c.name in ("jaw", "jaw_heavy")]:
            move(c, jaw)
    for g in [g for g in head.children if hasattr(g, "children") and g.name not in ("glow_eyes", "jaw")]:
        bake(m, g, head)
    # the head grows about the poll (its bone's pivot), in the head's own unturned frame
    P = np.array(head.origin)
    for c in [c for c in m.cubes if head in subtree_up(c.group)]:
        c.frm, c.to, c.origin = [(P + (np.array(v) - P) * HEAD_K).tolist() for v in (c.frm, c.to, c.origin)]
    for g in subtree(head)[1:]:
        g.origin = (P + (np.array(g.origin) - P) * HEAD_K).tolist()
    if kind == "vanguard":                 # armoured ear cups: bare ears poked through the chanfron
        for c in m.cubes:
            if c.name in ("ear-1", "ear1"):
                c.mat = "plate"
    m.root.children.remove(root)
    m.groups.remove(root)
    return m, f


# ==== the riders =======================================================================================================

def rider_model(kind, f):
    m = Model(f"occultech_dread_{kind}")
    root = m.group("build", (0, 0, 0))
    hc, lean, hip = dc.rider(root, f, kind, CFG[kind]["take"], CFG[kind]["helm"])
    zombie = kind == "vanguard"
    if not zombie:
        outrider_armour(bones_of(m)["torso"], hip, f)
    aw = 8 if zombie else 4
    W = f["W"]
    lw = aw
    rb = bone(m, m.root, "rider", hip)
    m.root.children.remove(rb)
    m.root.children.insert(0, rb)
    thighs, shins = {}, {}
    for k, side in SIDES.items():
        thighs[k] = bone(m, rb, f"thigh_{side}", hip + [k * 4, 0, 0])
        shins[k] = bone(m, thighs[k], f"shin_{side}", hip + [k * (W / 2 + lw / 2 + 1.5), -7, -9])
    torso = bones_of(m)["torso"]
    move(torso, rb)
    hd = bones_of(m)["headbone"]
    hd.name = "hi_head"
    pts = {}
    arms = {}
    for k, side in SIDES.items():
        el, hand = (hip + np.array(v, float) for v in dc.ARMS[(kind, REST)][k])
        sh = hip + [k * (8 + aw / 2), 22, 0]
        a = bone(m, torso, f"arm_{side}", sh)
        fa = bone(m, a, f"forearm_{side}", el)
        hb = bone(m, fa, f"hand_{side}", hand)
        arms[k] = (a, fa, hb)
        pts[k] = (sh, el, hand)
    rules = [(lambda n, k=k: n == f"thigh{k}", thighs[k]) for k in (-1, 1)]
    rules += [(lambda n, k=k: n in (f"shin{k}", f"foot{k}"), shins[k]) for k in (-1, 1)]
    sort_into(m, root, rules, rb)
    trules = [(lambda n, k=k: n == f"arm{k}_upper", arms[k][0]) for k in (-1, 1)]
    trules += [(lambda n, k=k: n == f"arm{k}_fore" or n == f"bracer{k}", arms[k][1]) for k in (-1, 1)]
    trules += [(lambda n, k=k: n.startswith(f"spaulder{k}_"), arms[k][0]) for k in (-1, 1)]
    if zombie:
        lance = bone(m, arms[1][2], "lance", pts[1][2])
        trules += [(lambda n: n.startswith(("lance", "vamplate")), lance),
                   (lambda n: n == "rein", arms[-1][2])]
    else:
        bow = bone(m, arms[-1][2], "bow", pts[-1][2])
        trules += [(lambda n: n.startswith(("bow_", "staff")), bow), (lambda n: n == "string", None)]
    keep = [(t, b) for t, b in trules if b is not None]
    for c in [c for c in torso.children if not hasattr(c, "children") and c.name == "string"]:
        torso.children.remove(c)
        m.cubes.remove(c)
    sort_into(m, torso, keep, torso)
    for g in [g for g in hd.children if hasattr(g, "children")]:
        bake(m, g, hd)
    if zombie:                             # session 6: two glowing bands under the lance head carry the state tints
        axis = _n([0.14, 0.78, -0.62])
        lance = bones_of(m)["lance"]
        tip = pts[1][2] + axis * 74
        gl = bone(m, lance, "glow_lance", tip - axis * 5)
        for i, back in enumerate((2.5, 7.5)):
            dc.limb(gl, f"lance_glow{i}", tip - axis * (back + 1.2), tip - axis * (back - 1.2), 4, 4, "crimson")
    if not zombie:                         # the mirror plate's rune glows and takes the state tints with the others
        rune = bone(m, torso, "glow_rune", hip + [0, 16.5, -7.4])
        for c in [c for c in torso.children if not hasattr(c, "children") and c.name == "mirror_rune"]:
            move(c, rune)
    m.root.children.remove(root)
    m.groups.remove(root)
    info = {"hip": hip, "hc": hc, "arms": pts, "hands": {k: arms[k][2] for k in arms}}
    if not zombie:
        info.update(strings(m, bones_of(m)["bow"], pts[-1][2]))
    return m, info


def outrider_armour(t, hip, f):
    """Session 5 review ("the skeleton's body is boring"): a steppe horse archer's kit over the vanilla skeleton.
    A lamellar cuirass in bands over the jerkin with a gold-rimmed mirror plate on the chest (a cyan rune in it: the
    archer is a storm mage), two lames on each shoulder, leather bracers, a belt with a gold buckle and a pouch, a sabre
    on the left hip, a bow case on the left flank, lamellar tassets over the thighs."""
    for side, z in (("front", -5.2), ("back", 5.2)):
        for i, y in enumerate((8.5, 12.5, 16.5, 20.5)):
            t.box(f"lamellar_{side}{i}", tuple(hip + [0, y, z]), (18, 4, 1.4), "lamellar")
    for k in (-1, 1):
        t.box(f"lamellar_side{k}", tuple(hip + [k * 8.9, 14.5, 0]), (1.4, 16, 9.6), "lamellar")
    dc.disc(t, "mirror", hip + [0, 16.5, -6.2], [0, 0, -1], 9, 1.2, "gold")
    t.box("mirror_face", tuple(hip + [0, 16.5, -6.9]), (6, 6, 1), "iron")
    t.box("mirror_rune", tuple(hip + [0, 16.5, -7.4]), (2, 2, 1), "cyan", rotation=(0, 0, 45))
    for k in (-1, 1):
        for i in range(2):
            t.box(f"spaulder{k}_{i}", tuple(hip + [k * (11.5 + i * 1.0), 23.5 - i * 3.2, 0]), (7, 2, 9 - i),
                  "lamellar", rotation=(0, 0, k * -(22 + i * 12)))
    for k, side in ((-1, "left"), (1, "right")):
        el, hand = (hip + np.array(v, float) for v in dc.ARMS[("outrider", REST)][k])
        d = hand - el
        dc.limb(t, f"bracer{k}", el + d * 0.35, el + d * 0.95, 6, 6, "leather")
    t.box("belt", tuple(hip + [0, 4.5, 0]), (18.4, 3, 10), "leather")
    t.box("buckle", tuple(hip + [0, 4.5, -5.4]), (3, 3, 1), "gold")
    t.box("pouch", tuple(hip + [6.5, 2.5, -5.6]), (4, 5, 3), "leather")
    dc.limb(t, "scabbard", hip + [-9.6, 5, -4], hip + [-12.5, -15, 10], 2, 3, "leather")
    dc.limb(t, "sabre_hilt", hip + [-9.2, 5.5, -4.5], hip + [-8.4, 10, -7.5], 1.4, 1.4, "gold")
    t.box("sabre_guard", tuple(hip + [-9.4, 6, -4.8]), (1.4, 1, 4), "gold")
    t.box("bow_case", tuple(hip + [-11.5, -4, 7]), (3, 14, 8), "leather", rotation=(-18, 0, 6))
    t.box("bow_case_trim", tuple(hip + [-12.9, -4, 7]), (1, 12, 6), "gold", rotation=(-18, 0, 6))
    for k in (-1, 1):
        t.box(f"tasset{k}", tuple(hip + [k * 5, 0, -6]), (7, 8, 1.4), "lamellar", rotation=(-24, 0, k * -6),
              origin=tuple(hip + [k * 5, 3.5, -5]))


def bow_tips(m, bow_bone):
    """The upper and lower tips of the bow's limbs, in the bind pose."""
    ups = [c for c in m.cubes if c.group is bow_bone and c.name.startswith("bow_upper")]
    los = [c for c in m.cubes if c.group is bow_bone and c.name.startswith("bow_lower")]
    top = max(np.vstack([c.corners() for c in ups]), key=lambda p: p[1])
    bot = min(np.vstack([c.corners() for c in los]), key=lambda p: p[1])
    return top + [0, -1, 1], bot + [0, 1, 1]


def strings(m, bow_bone, hand):
    top, bot = bow_tips(m, bow_bone)
    midp = (top + bot) / 2
    out = {"tips": (top, bot)}
    for name, tip in (("string_upper", top), ("string_lower", bot)):
        b = bone(m, bow_bone, name, tip)
        dc.limb(b, name, tip, midp + (midp - tip) * 0.04, 1, 1, "skel")
        out[name] = (tip, midp - tip)
    return out


def add_arrow(m, info, pose_spec):
    """The nocked arrow, built where it sits in the draw pose and stored in the right hand's bind space; hidden in the
    bind pose."""
    pose_rider(m, info, pose_spec)
    hb = info["hands"][1]
    Mh = hb.world_matrix()
    inv = np.linalg.inv(Mh)
    hw = (Mh @ np.array([*info["arms"][1][2], 1.0]))[:3]
    lw = (info["hands"][-1].world_matrix() @ np.array([*info["arms"][-1][2], 1.0]))[:3]
    fwd = _n(lw - hw)
    tip = lw + fwd * 9
    a = bone(m, hb, "arrow", info["arms"][1][2])
    g = bone(m, a, "glow_arrow", info["arms"][1][2])
    loc = lambda p: (inv @ np.array([*p, 1.0]))[:3]
    dc.limb(a, "arrow_shaft", loc(hw - fwd * 2), loc(tip), 1, 1, "wood")
    for i in range(2):
        dc.limb(a, f"arrow_fletch{i}", loc(hw - fwd * 1), loc(hw + fwd * 3), 1 if i else 2, 2 if i else 1, "bone")
    dc.spike(g, "arrow_head", loc(tip), loc(tip + fwd) - loc(tip), 4, 2, "cyan")
    a.visible = False
    reset(m)


def reset(m):
    for g in m.groups:
        g.rotation = [0.0, 0.0, 0.0] if g.name not in ("head",) else g.rotation
        if hasattr(g, "scale"):
            del g.scale


# ==== poses ============================================================================================================

def ang(d):
    """A direction's angle from straight down (legs) / up (neck), forward (-z) positive, in the side plane."""
    return math.degrees(math.atan2(-d[2], -d[1]))


def neck_ang(d):
    return math.degrees(math.atan2(-d[2], d[1]))


# mount poses: legs as world angles (upper, cannon, pastern; forward positive), the base's tilt, the neck's angle from
# vertical (forward positive) and the head's world pitch, a lift off the floor
MOUNT_POSES = {
    REST: dict(),
    "gallop": dict(legs=dc.LEGS["charge"], neck=52, head=-30, lift=3),
    "rear": dict(tilt=32, legs={"fl": (75, -35, -10), "fr": (55, -75, -40), "hl": (-2, 18, 30), "hr": (6, 22, 34)},
                 neck=8, head=-20),
    "stunned": dict(legs={"fl": (14, 10, 34), "fr": (10, 6, 30), "hl": (-40, -6, 22), "hr": (-36, -2, 24)},
                    neck=78, head=-88),
    "paw": dict(legs=dc.LEGS["snipe"], neck=30, head=-36),
}


def pose_mount(m, f, spec):
    """Sets the mount's bones for a pose; returns the lift (whole-model offset) in units."""
    B = bones_of(m)
    reset(m)
    tilt = spec.get("tilt", 0)
    B["base"].rotation = [float(tilt), 0, 0]
    rest_legs = dc.LEGS[REST]
    for key in LEGS:
        if key not in spec.get("legs", {}):
            continue
        r = rest_legs[key]
        p = [a - tilt for a in spec["legs"][key]]
        B[f"leg_{key}"].rotation = [p[0] - r[0], 0, 0]
        B[f"leg_{key}_lower"].rotation = [(p[1] - r[1]) - (p[0] - r[0]), 0, 0]
        B[f"leg_{key}_hoof"].rotation = [(p[2] - r[2]) - (p[1] - r[1]), 0, 0]
    n0, mid, poll = f["neck"]
    rest_neck = neck_ang(poll - n0)
    head_rest = f["head_pitch"]
    if "neck" in spec:
        dn = spec["neck"] + tilt - rest_neck          # base tilt leans the neck back; the neck bone leans it forward
        B["neck"].rotation = [-dn, 0, 0]
        B["head"].rotation = [float(spec["head"]) - tilt + dn, 0, 0]
    else:
        B["head"].rotation = [float(head_rest) - tilt, 0, 0]
    if "banner_cloth" in B and spec.get("lift"):
        B["banner_cloth"].rotation = [-68.0, 0, 0]
    if "tail" in B and spec.get("lift"):
        B["tail"].rotation = [-55.0, 0, 0]
    if "jaw" in B and spec is MOUNT_POSES["stunned"]:
        B["jaw"].rotation = [14.0, 0, 0]
    lo = min(c.corners()[:, 1].min() for c in m.cubes)
    return -lo + spec.get("lift", 0)


# rider poses: lean (torso x), twist (torso y), head pitch, per side (elbow, hand) in torso space, and the weapon
RIDER_POSES = {
    "vanguard": {
        REST: dict(),
        "charge": dict(lean=-16, arms=dc.ARMS[("vanguard", "charge")], lance=(-0.12, 0.04, -1)),
        "rear": dict(lean=8, arms={1: ((15, 16, 2), (13, 22, -6)), -1: ((-13, 10, -6), (-6, 8, -16))},
                     lance=(0.06, 1, 0.12)),
        "stunned": dict(lean=-24, head=-22, arms={1: ((14, 8, -2), (14, -4, -6)), -1: ((-13, 9, -3), (-12, -2, -8))},
                        lance=(0.45, -0.3, -0.84)),
        "sweep": dict(twist=-30, arms={1: ((17, 17, -6), (22, 15, -16)), -1: ((-13, 10, -6), (-6, 8, -16))},
                      lance=(1, 0.05, -0.55)),
        "throw": dict(lean=6, twist=-14, arms={1: ((17, 30, 6), (14, 38, -2)), -1: ((-12, 16, -10), (-8, 20, -20))},
                      lance=(0.04, 0.12, -1)),
    },
    "outrider": {
        REST: dict(),
        "gallop": dict(lean=-12, arms={-1: ((-11, 11, -5), (-10, 6, -14)), 1: ((11, 10, -2), (8, 6, -12))}),
        "draw": dict(lean=-4, arms=dc.ARMS[("outrider", "snipe")], bow=((0.18, 1, 0), (0, 0, -1)), draw=True),
        "rain": dict(lean=10, head=24, arms={-1: ((-10, 29, -9), (-7, 37, -17)), 1: ((12, 28, 6), (3, 31, -3))},
                     bow=((0.1, 0.66, 0.75), (0, 0.75, -0.66)), draw=True),
        "loose": dict(lean=-4, arms={-1: ((-10, 23, -10), (-8, 24, -21)), 1: ((15, 23, 9), (17, 22, 14))},
                      bow=((0.18, 1, 0), (0, 0, -1))),
    },
}


def rot_between(a0, b0, a1, b1):
    """The rotation taking the frame (a0, b0) to (a1, b1)."""
    def frame3(a, b):
        a = _n(a)
        b = _n(np.array(b, float) - a * (np.array(b, float) @ a))
        return np.column_stack([a, b, np.cross(a, b)])
    return frame3(a1, b1) @ frame3(a0, b0).T


def pose_rider(m, info, spec, state=None):
    """state: a dict carried from frame to frame (animation): each arm bone's turn is then the previous frame's turn
    plus the small turn between the two frames' directions, so an arm swinging far from its bind direction never flips
    its roll (a fresh shortest turn from the bind pose does, near 180 degrees)."""
    B = bones_of(m)
    reset(m)
    B["torso"].rotation = [float(spec.get("lean", 0)), float(spec.get("twist", 0)), 0]
    B["hi_head"].rotation = [float(spec.get("head", 0)) - spec.get("lean", 0) * 0.5, 0, 0]
    hip = info["hip"]
    kind = "vanguard" if "lance" in B else "outrider"
    worlds = {}
    for k, side in SIDES.items():
        sh, el0, ha0 = info["arms"][k]
        if "arms" in spec and k in spec["arms"]:
            el1, ha1 = (hip + np.array(v, float) for v in spec["arms"][k])
        else:
            el1, ha1 = el0, ha0
        if state is None:
            Ru = turn_to(el0 - sh, el1 - sh)
            Rf = turn_to(ha0 - el0, ha1 - el1)
        else:
            du, df = el1 - sh, ha1 - el1
            pu = state.get(("u", k))
            pf = state.get(("f", k))
            Ru = turn_to(el0 - sh, du) if pu is None else turn_to(pu[0], du) @ pu[1]
            Rf = turn_to(ha0 - el0, df) if pf is None else turn_to(pf[0], df) @ pf[1]
            state[("u", k)], state[("f", k)] = (du, Ru), (df, Rf)
        B[f"arm_{side}"].rotation = [float(v) for v in euler(Ru)]
        B[f"forearm_{side}"].rotation = [float(v) for v in euler(Ru.T @ Rf)]
        worlds[k] = Rf
    if kind == "vanguard":
        rest_axis = _n([0.14, 0.78, -0.62])
        axis = _n(spec.get("lance", rest_axis))
        if state is None or "lance" not in state:
            Rl = turn_to(rest_axis, axis)
        else:
            Rl = turn_to(state["lance"][0], axis) @ state["lance"][1]
        if state is not None:
            state["lance"] = (axis, Rl)
        B["lance"].rotation = [float(v) for v in euler(worlds[1].T @ Rl)]
    else:
        up0, fwd0 = _n([0, 1, 0.12]), np.array([0, 0, -1.0])
        up1, fwd1 = spec.get("bow", (up0, fwd0))
        Rb = rot_between(up0, fwd0, np.array(up1, float), np.array(fwd1, float))
        B["bow"].rotation = [float(v) for v in euler(worlds[-1].T @ Rb)]
        if spec.get("draw"):
            hand = B["hand_right"].world_matrix() @ np.array([*info["arms"][1][2], 1.0])
            for name in ("string_upper", "string_lower"):
                tip, d0 = info[name]
                g = B[name]
                Mp = g.parent.world_matrix()
                tip_w = (Mp @ np.array([*tip, 1.0]))[:3]
                want = np.linalg.solve(Mp[:3, :3], hand[:3] - tip_w)
                g.rotation = [float(v) for v in euler(turn_to(d0, want))]
                s = float(np.linalg.norm(want) / np.linalg.norm(d0))
                g.scale = [s, s, s]
        if "arrow" in B:
            B["arrow"].visible = bool(spec.get("draw"))


def hide_arrow(m):
    B = bones_of(m)
    if "arrow" in B:
        B["arrow"].visible = False


def boxes(m, M=np.eye(4), dy=0.0, skip_hidden=True):
    out = []
    hidden = [g for g in m.groups if not g.visible]
    for c in m.cubes:
        if skip_hidden and any(h in subtree_up(c.group) for h in hidden):
            continue
        corners = c.corners()
        pts = (M @ np.column_stack([corners, np.ones(len(corners))]).T).T[:, :3] + [0, dy, 0]
        col = PALETTE[c.mat]
        out.append({"name": c.name, "mat": c.mat, "color": [v / 255 for v in col[:3]], "corners": pts.tolist()})
    return out


# ==== the pairs, posed =================================================================================================

PAIRS = {
    "vanguard": [("idle", REST, REST), ("charge", "gallop", "charge"), ("rear", "rear", "rear"),
                 ("stunned", "stunned", "stunned"), ("sweep", REST, "sweep"), ("throw", "paw", "throw")],
    "outrider": [("idle", REST, REST), ("gallop", "gallop", "gallop"), ("draw", "paw", "draw"),
                 ("rain", REST, "rain"), ("loose", "paw", "loose")],
}
TITLES = {"idle": "idle", "charge": "the charge (lance couched)", "rear": "the charge's tell (rearing)",
          "stunned": "stunned (a charge cut short)", "sweep": "the lance sweep (melee)", "throw": "the spear throw (enraged)",
          "gallop": "circling (gallop)", "draw": "the snipe (draw)", "rain": "arrow rain (aim high)",
          "loose": "the loose"}
POSE_VIEWS = [
    {"name": "side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay", "mode": "clay", "camera": "persp", "yaw": 38, "height": 3.0, "dist": 10.5, "target_z": 3.6},
]


def pair_boxes(kind, mm, f, rm, info, mpose, rpose):
    lift = pose_mount(mm, f, MOUNT_POSES[mpose])
    if rpose in RIDER_POSES[kind]:
        pose_rider(rm, info, RIDER_POSES[kind][rpose])
    Mb = bones_of(mm)["base"].world_matrix()
    return boxes(mm, dy=lift) + boxes(rm, Mb, lift)


def hitbox_bounds(f, rm):
    """The rider's hitbox: the rider and the horse's body under him, from the ground to the top of the helm, so hits
    on the horse reach the rider (the horse can't be hurt and the rider sits 4 blocks up)."""
    top = max(c.corners()[:, 1].max() for c in rm.cubes if "plume" not in c.name and "spike" not in c.name
              and "horn" not in c.name and "lance" not in c.name and "banner" not in c.name)
    s = f["seat"]
    half = 20
    return (-half, 0.0, s[2] - half), (half, float(math.ceil(top)), s[2] + half)


def main(args):
    kinds = [k for k in ("vanguard", "outrider") if k in args] or ["vanguard", "outrider"]
    v2.PALETTE.update(PALETTE)
    OUT.mkdir(parents=True, exist_ok=True)
    stats = {}
    for kind in kinds:
        mm, f = mount(kind)
        rm, info = rider_model(kind, f)
        if kind == "outrider":
            add_arrow(rm, info, RIDER_POSES["outrider"]["draw"])
        snap(mm)
        snap(rm)
        d = OUT / kind
        if d.exists():
            shutil.rmtree(d)
        # key poses
        for key, mpose, rpose in PAIRS[kind]:
            bx = pair_boxes(kind, mm, f, rm, info, mpose, rpose)
            v2.run_blender(bx, d / "poses" / key, POSE_VIEWS)
        # the bind pose, flat, and the hitbox
        pose_mount(mm, f, MOUNT_POSES[REST])
        reset(rm)
        hide_arrow(rm)
        bx = boxes(mm) + boxes(rm)
        v2.run_blender(bx, d / "bind", [
            {"name": "hero", "mode": "flat", "camera": "persp", "yaw": 40, "height": 3.4, "dist": 10.5, "target_z": 3.9},
            {"name": "front", "mode": "flat", "camera": "persp", "yaw": -20, "height": 2.4, "dist": 10.5, "target_z": 3.6,
             "player": False},
            {"name": "back", "mode": "flat", "camera": "persp", "yaw": 200, "height": 3.4, "dist": 10.5, "target_z": 3.6,
             "player": False}])
        frm, to = hitbox_bounds(f, rm)
        hb = [dict(b, color=[v * 0.55 + 0.4 for v in b["color"]]) for b in bx]
        corners = [[x, y, z] for x in (frm[0], to[0]) for y in (frm[1], to[1]) for z in (frm[2], to[2])]
        v2.run_blender(hb + [{"name": "hitbox", "mat": "hitbox", "color": [0.86, 0.24, 0.24], "corners": corners}],
                       d / "hitbox", [{"name": "front", "mode": "flat", "camera": "ortho_front", "player": False},
                                      {"name": "side", "mode": "flat", "camera": "ortho_side", "player": False}])
        # export: the faces' patterns are texture, the rider sits at its model's origin (the seat)
        design = OUT / "design"
        design.mkdir(exist_ok=True)
        for model, part in ((mm, "mount"), (rm, "rider")):
            for c in [c for c in model.cubes if c.name in DECALS[part]]:
                c.group.children.remove(c)
                model.cubes.remove(c)
        seat = f["seat"]
        for g in rm.groups:
            g.origin = (np.array(g.origin) - seat).tolist()
        for c in rm.cubes:
            c.frm, c.to, c.origin = [(np.array(v) - seat).tolist() for v in (c.frm, c.to, c.origin)]
        mm.write_bbmodel(design / f"{mm.name}.bbmodel")
        bb = rm.to_bbmodel()
        add_hitbox(bb, (frm[0], frm[1] - seat[1], frm[2] - seat[2]), (to[0], to[1] - seat[1], to[2] - seat[2]))
        (design / f"{rm.name}.bbmodel").write_text(json.dumps(bb, indent=1), encoding="utf-8")
        stats[kind] = {
            "mount": dict(mm.stats(), model=mm.name),
            "rider": dict(rm.stats(), model=rm.name, seat_units=[round(float(v), 2) for v in seat],
                          hitbox_blocks=[round((t - s) / 16, 2) for s, t in zip(frm, to)]),
        }
        (d / "parts.md").write_text(parts(mm) + "\n\n" + parts(rm) + "\n", encoding="utf-8")
        print(kind, json.dumps(stats[kind]))
    prev = json.loads((OUT / "stats.json").read_text()) if (OUT / "stats.json").exists() else {}
    prev.update(stats)
    (OUT / "stats.json").write_text(json.dumps(prev, indent=2) + "\n", encoding="utf-8")
    sheets()


def parts(m):
    rows = [f"### `{m.name}`", "", "| Bone | Parent | Cubes | Materials |", "|---|---|---|---|"]
    for g in m.groups:
        cubes = [c for c in g.children if not hasattr(c, "children")]
        mats = sorted({c.mat for c in cubes})
        parent = g.parent.name if g.parent is not None and g.parent.name != "root" else "-"
        rows.append(f"| `{g.name}` | {parent} | {len(cubes)} | {', '.join(mats) or '-'} |")
    return "\n".join(rows)


def sheets():
    for kind in ("vanguard", "outrider"):
        d = OUT / kind
        if not d.exists():
            continue
        keys = [k for k, _, _ in PAIRS[kind]]
        tw, th, pad, top = 380, 300, 10, 56
        img = Image.new("RGB", (pad + len(keys) * (tw + pad), top + 2 * (th + 30 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Dread Riders, session 2: the {kind.title()}'s key poses", font=sheet._font(24), fill=sheet.INK)
        for c, key in enumerate(keys):
            for r, v in enumerate(("side", "clay")):
                x, y = pad + c * (tw + pad), top + r * (th + 30 + pad)
                img.paste(sheet._tile(d / "poses" / key / f"{v}.png", tw, th), (x, y))
                dr.text((x, y + th + 5), TITLES[key], font=sheet._font(15), fill=sheet.DIM)
        img.save(OUT / f"poses_{kind}.png")
        tiles = [(d / "bind" / "hero.png", "bind pose"), (d / "bind" / "front.png", "front"),
                 (d / "bind" / "back.png", "back"), (d / "hitbox" / "side.png", "the rider's hitbox, side"),
                 (d / "hitbox" / "front.png", "the rider's hitbox, front")]
        img = Image.new("RGB", (pad + len(tiles) * (tw + pad), top + th + 30 + pad), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Dread Riders, session 2: the {kind.title()}, bind pose and hitbox", font=sheet._font(24),
                fill=sheet.INK)
        for c, (p, label) in enumerate(tiles):
            x = pad + c * (tw + pad)
            img.paste(sheet._tile(p, tw, th), (x, top))
            dr.text((x, top + th + 5), label, font=sheet._font(15), fill=sheet.DIM)
        img.save(OUT / f"design_{kind}.png")


if __name__ == "__main__":
    main(sys.argv[1:])
