"""The Archevoker redesign, session 2: design lock (plan: docs/art/bosses/archevoker/overhaul/plan.md).

The approved blockout (archevoker_s1.py) rebuilt as a rig, at its final size, every cube snapped to whole texels:
- two models. `occultech_archevoker` is the priest on his throne with the ring. `occultech_archevoker_hand_cyan` and
  `_purple` are the casting hands, his totems: their own carriers, hitboxes and health in the fight. The cyan is a
  right hand, the purple a left.
- the priest's bones (BetterModel names): `base` (everything; its pivot on the ground under the throne, for the float
  and the death), `throne` with `ring` (one bone, it turns) and its `glow_ring` (the small hands' irises) and
  `glow_runes` (the rune ring under the point), `body` (the hips and lap) with `thigh_*` / `shin_*`, `torso`, `hi_head`
  (follows the carrier's look) with `glow_eyes`, and each arm as `arm_*`, `forearm_*`, `hand_*` (his own grey hands)
  hanging straight in the bind pose and aimed per pose;
- the hand's bones: `hand` (the gold), `glow_eye` (the iris), `glow_circle` (the spell circle);
- the hitboxes (`ob_hitbox`): the priest and the throne's seat and back, never the ring; each casting hand its palm
  and fingers;
- the flicker fix (no two faces on one plane), found in the rest pose and kept for every pose;
- the fight's key poses, posed from the rig, as silhouettes for the design (not animation).

Units are model pixels (16 = one block). The front is -z; his right is +x.

Run from the repository root: python tools/art/bosses/archevoker_s2.py [pose ...]
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import archevoker_face as f, archevoker_s1 as b1, archevoker_silhouettes as s1  # noqa: E402
from bosses import volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/archevoker/overhaul/s2_design"
PALETTE = dict(b1.PALETTE, hitbox=(220, 60, 60))
v2.PALETTE.update(PALETTE)
SIDES = {1: "right", -1: "left"}
HIP = s1.HIP
SHOULDER = (17, 77, 10)                 # his right shoulder in the torso's rest space (the left mirrors it)
UPPER, FORE = 18, 17                    # the arm's lengths


# ---- rig helpers ---------------------------------------------------------------------------------------------------

def group(model, name):
    return next(g for g in model.groups if g.name == name)


def subtree(g):
    out = [g]
    for ch in g.children:
        if hasattr(ch, "children"):
            out += subtree(ch)
    return out


def cubes_in(model, g):
    gs = set(map(id, subtree(g)))
    return [c for c in model.cubes if id(c.group) in gs]


def move(c, g):
    """Puts a cube on another bone whose rest transform is the same as its old one."""
    c.group.children.remove(c)
    g.children.append(c)
    c.group = g


def flatten(model, g, into):
    """Moves the cubes of a bone turned about z only into its parent `into` (no rotation), keeping them in place, and
    drops the bone: the ring's twelve hands become one bone."""
    th = math.radians(g.rotation[2])
    rz = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
    pg = np.array(g.origin)
    for c in [ch for ch in g.children if not hasattr(ch, "children")]:
        oc = np.array(c.origin)
        o2 = rz @ (oc - pg) + pg
        c.frm = (np.array(c.frm) - oc + o2).tolist()
        c.to = (np.array(c.to) - oc + o2).tolist()
        c.origin = o2.tolist()
        c.rotation = [0.0, 0.0, c.rotation[2] + g.rotation[2]]
        move(c, into)
    g.parent.children.remove(g)
    model.groups.remove(g)


def new_bone(model, parent, name, origin, cubes):
    g = parent.group(name, origin)
    for c in cubes:
        move(c, g)
    return g


def translate(model, g, d):
    for x in subtree(g):
        x.origin = [x.origin[i] + d[i] for i in range(3)]
    for c in cubes_in(model, g):
        c.frm = [c.frm[i] + d[i] for i in range(3)]
        c.to = [c.to[i] + d[i] for i in range(3)]
        c.origin = [c.origin[i] + d[i] for i in range(3)]


# ---- the arms: a real chain, hanging straight in the bind pose --------------------------------------------------------

def arm_chain(torso, sx):
    side = SIDES[sx]
    s = np.array((sx * SHOULDER[0], SHOULDER[1], SHOULDER[2]), float)
    e, w = s - (0, UPPER, 0), s - (0, UPPER + FORE, 0)
    up = torso.group(f"arm_{side}", tuple(s))
    up.box(f"upper_arm_{side}", tuple(s - (0, UPPER / 2 - 0.5, 0)), (9, UPPER + 1, 9), "robe")
    fo = up.group(f"forearm_{side}", tuple(e))
    fo.box(f"forearm_{side}", tuple(e - (0, FORE / 2, 0)), (8, FORE, 8), "robe")
    fo.box(f"sleeve_{side}", tuple(e - (0, 10.5, 0)), (12, 12, 12), "robe")
    fo.box(f"sleeve_trim_{side}", tuple(e - (0, 16.5, 0)), (13, 2, 13), "trim")
    ha = fo.group(f"hand_{side}", tuple(w))
    ha.box(f"palm_{side}", tuple(w - (0, 3.5, 0)), (3, 7, 6), "skin")
    for i, dz in enumerate((-2.25, -0.75, 0.75, 2.25)):
        ha.box(f"finger_{side}{i}", tuple(w + (0, -9.5 + abs(dz) * 0.6, dz)), (2, 5, 1), "skin")
    ha.box(f"thumb_{side}", tuple(w + (0, -3.5, -3.6)), (2, 5, 2), "skin", rotation=(-20, 0, 0))


def aim(g, direction):
    """Turns a bone hanging along -y (in its parent's space) to point along a world direction."""
    parent = g.parent.world_matrix()[:3, :3]
    d = np.linalg.solve(parent, np.array(direction, float))
    d /= np.linalg.norm(d)
    a = math.degrees(math.asin(max(-1.0, min(1.0, -d[2]))))
    c = math.degrees(math.atan2(d[0], -d[1]))
    g.rotation = [a, 0.0, c]


def roll_palm(g, sx, want):
    """Rolls a hand about its own length until its palm faces a world direction."""
    best = None
    for r in range(-180, 180, 5):
        g.rotation = [0.0, float(r), 0.0]
        n = g.world_matrix()[:3, :3] @ np.array((-sx, 0, 0), float)
        score = float(np.dot(n, want))
        if best is None or score > best[0]:
            best = (score, r)
    g.rotation = [0.0, float(best[1]), 0.0]


# ---- the rig ---------------------------------------------------------------------------------------------------------

def rig(name):
    s1.evoker_head = lambda g, base, k=f.K: f.face_cardinal(g)
    s1.small_hand = f.small_hand_eye
    s1.crossed_arms = lambda *a: None                        # the arms are built as a chain below
    m = Model(name)
    base = m.group("base", (0, 0, 0))
    s1.throne(base, b1.BACK_TOP)
    throne = group(m, "throne")
    b1.decorate_throne(throne)
    s1.hand_ring(throne, *b1.RING)
    ring = group(m, "ring")
    for g in [g for g in ring.children if hasattr(g, "children")]:
        flatten(m, g, ring)
    irises = new_bone(m, ring, "glow_ring", ring.origin, [c for c in cubes_in(m, ring) if c.name.endswith("_iris")])
    for c in cubes_in(m, irises):                            # a square iris needs no turn: one display for all twelve
        c.rotation = [0.0, 0.0, 0.0]
    new_bone(m, throne, "glow_runes", (0, 6, 0), [c for c in cubes_in(m, throne) if c.name.startswith("rune_ring")])
    torso = s1.priest(base, "fold")
    head = group(m, "head")
    f.hood_draped(head, torso)
    f.neck_and_shoulders(torso)
    f.chain_draped(torso)
    f.drop(m, {"pendant", "collar"})
    head.name = "hi_head"
    new_bone(m, head, "glow_eyes", head.origin, [c for c in cubes_in(m, head) if c.name.startswith("eye_")])
    for side in ("right", "left"):
        group(m, f"leg_{side}").name = f"thigh_{side}"
    for sx in SIDES:
        arm_chain(torso, sx)
    names = [c.name for c in m.cubes]
    assert len(names) == len(set(names)), "cube names must be unique (the flicker fix finds cubes by name)"
    return m


# ---- the poses -------------------------------------------------------------------------------------------------------
#   torso, head: pitch (x) is negative to lean or look forward and down, positive to lean back or look up
#   legs: "crossed", "spread", "stand" or ((pitch, yaw, shin) right, (pitch, yaw, shin) left)
#   torso, head: rotations; arm: {side: (elbow, wrist, palm)}: world points in the torso's rest space and the palm's
#   facing; hands: the casting hands as {"cyan"/"purple": (centre, rotation)} or None when dead;
#   body: move the whole priest; base: (dy, roll) for the whole model (death)
LEGS = {"crossed": ((16, 24, -22), (0, -4, 4)), "spread": ((0, -20, 10), (0, 20, 10)),
        "stand": ((-90, -6, 90), (-90, 6, 90))}
DOWN, FWD, UP = (0, -1, 0), (0, 0, -1), (0, 1, 0)
IDLE_HANDS = {"cyan": ((48, 74, -12), (0, -14, -6)), "purple": ((-48, 74, -12), (0, 14, 6))}


def mirror_arm(spec):
    (ex, ey, ez), (wx, wy, wz), palm = spec
    return (-ex, ey, ez), (-wx, wy, wz), (-palm[0], palm[1], palm[2])


POSES = {
    "rest": ("idle: forearms on the armrests, legs crossed, the hands hovering", {
        "legs": "crossed", "torso": (-5, 0, 0),
        "arm": {"right": ((24, 61, 14), (25, 59.5, -3), DOWN)}, "hands": IDLE_HANDS}),
    "line": ("the line: his right arm thrust out, the cyan hand pressing the line into the floor", {
        "legs": "spread", "torso": (-11, -6, 0), "head": (-4, -8, 0),
        "arm": {"right": ((22, 74, -8), (24, 72, -25), FWD), "left": ((-24, 61, 14), (-25, 59.5, -3), DOWN)},
        "hands": {"cyan": ((14, 22, -84), (-35, 0, 0)), "purple": ((-48, 74, -12), (0, 14, 6))}}),
    "ring": ("the ring: his right arm sweeping overhead, the cyan hand circling the target", {
        "legs": "spread", "torso": (-11, -12, 0), "head": (-2, -12, 0),
        "arm": {"right": ((31, 91, 4), (40, 104, -8), DOWN), "left": ((-24, 61, 14), (-25, 59.5, -3), DOWN)},
        "hands": {"cyan": ((64, 40, -64), (-25, -45, 0)), "purple": ((-48, 74, -12), (0, 14, 6))}}),
    "spiral": ("the spiral: his left wrist twirling, the purple hand turning out from him", {
        "legs": "crossed", "torso": (-11, 10, 0), "head": (-4, 12, 0),
        "arm": {"left": ((-30, 87, -2), (-28, 103, -12), UP), "right": ((24, 61, 14), (25, 59.5, -3), DOWN)},
        "hands": {"cyan": ((48, 74, -12), (0, -14, -6)), "purple": ((-34, 38, -42), (-55, 30, 45))}}),
    "burst": ("the fang burst: both arms flung down, both hands slamming the floor beside him", {
        "legs": "spread", "torso": (-6, 0, 0), "head": (6, 0, 0),
        "arm": {"right": ((30, 64, 0), (40, 56, -12), DOWN)},
        "hands": {"cyan": ((40, 26, -30), (-65, 0, 0)), "purple": ((-40, 26, -30), (-65, 0, 0))}}),
    "fold": ("arms folded: waiting, the hands hovering", {
        "legs": "crossed", "torso": (-5, 0, 0),
        "arm": {"right": ((18, 59, 7), (-12, 64, -5), DOWN), "left": ((-18, 58, 9), (12, 61, -2), DOWN)},
        "hands": IDLE_HANDS}),
    "caught": ("cheating death: slumped forward, the hands catching him under the shoulders", {
        "legs": "spread", "torso": (-24, 0, 0), "head": (-28, 0, 8),
        "arm": {"right": ((19, 60, 4), (20, 44, -2), (-1, 0, 0))},
        "hands": {"cyan": ((19, 64, -36), (0, 180, 0)), "purple": ((-19, 64, -36), (0, 180, 0))}}),
    "risen": ("both hands dead: risen off the throne, arms spread, casting for himself", {
        "legs": "stand", "body": (0, 22, -30), "torso": (4, 0, 0), "head": (6, 0, 0),
        "arm": {"right": ((32, 88, 4), (46, 98, -6), FWD)}, "hands": None}),
    "death": ("death: slumped sideways, the throne listing and sinking", {
        "legs": "spread", "torso": (-14, 0, 18), "head": (-20, 10, 26), "base": (-5, 10),
        "arm": {"right": ((19, 60, 12), (21, 43, 8), (-1, 0, 0)), "left": ((-19, 60, 12), (-22, 44, 6), (1, 0, 0))},
        "hands": None}),
}


def pose(m, spec):
    legs = spec["legs"]
    legs = LEGS[legs] if isinstance(legs, str) else legs
    for side, (pitch, yaw, shin) in zip(("right", "left"), legs):
        group(m, f"thigh_{side}").rotation = [pitch, yaw, 0]
        group(m, f"shin_{side}").rotation = [shin, 0, 0]
    if spec.get("body"):
        translate(m, group(m, "body"), spec["body"])
    torso = group(m, "torso")
    torso.rotation = list(spec.get("torso", (0, 0, 0)))
    group(m, "hi_head").rotation = list(spec.get("head", (0, 0, 0)))
    arms = dict(spec["arm"])
    for side in ("right", "left"):
        if side not in arms:
            other = "left" if side == "right" else "right"
            arms[side] = mirror_arm(arms[other])
    for side, (elbow, wrist, palm) in arms.items():
        sx = 1 if side == "right" else -1
        tm = torso.world_matrix()
        sh = tm @ np.array((sx * SHOULDER[0], SHOULDER[1], SHOULDER[2], 1.0))
        el, wr = (tm @ np.array((*p, 1.0)) for p in (elbow, wrist))
        aim(group(m, f"arm_{side}"), (el - sh)[:3])
        aim(group(m, f"forearm_{side}"), (wr - el)[:3])
        roll_palm(group(m, f"hand_{side}"), sx, np.array(palm, float))
    if spec.get("base"):
        dy, roll = spec["base"]
        base = group(m, "base")
        base.rotation = [0, 0, roll]
        translate(m, base, (0, dy, 0))


def casting_hands(m, spec):
    """The casting hands where the pose puts them (render only: in game they are their own models)."""
    if not spec.get("hands"):
        return
    g = m.group("casting_render", (0, 0, 0))
    for glow, (centre, rot) in spec["hands"].items():
        f.hand_eye(g, f"hand_{glow}", centre, rot, glow, mirror=glow == "purple")


# ---- snap, flicker fix, hitboxes --------------------------------------------------------------------------------------

def snap(m):
    """Whole-texel sizes. The hood's slabs round up, so their mitred joints overlap a hair instead of opening."""
    for c in m.cubes:
        lo, hi = np.array(c.frm), np.array(c.to)
        centre = (lo + hi) / 2
        raw = hi - lo
        size = np.maximum(1, np.ceil(raw - 0.01) if c.name.startswith("hood") else np.round(raw))
        c.frm, c.to = (centre - size / 2).tolist(), (centre + size / 2).tolist()


_NUDGES = None


def finish(m):
    global _NUDGES
    snap(m)
    if _NUDGES is None:
        rest = rig("nudge_rest")
        pose(rest, POSES["rest"][1])
        snap(rest)
        from bosses.coven_s2 import _resolve
        _NUDGES = {}
        _resolve(rest, _NUDGES)
    by_name = {c.name: c for c in m.cubes}
    for name, d in _NUDGES.items():
        if name in by_name:
            c = by_name[name]
            c.frm, c.to, c.origin = [(np.array(v) + d).tolist() for v in (c.frm, c.to, c.origin)]


def hitbox_bounds(m):
    """The priest and the throne's seat and back: not the ring, the runes, the crest's finials or the casting hands."""
    keep = []
    for c in m.cubes:
        names = [g.name for g in subtree_up(c.group)]
        if any(n in ("ring", "glow_ring", "glow_runes", "casting_render") for n in names):
            continue
        keep.append(c.corners())
    lo, hi = np.vstack(keep).min(0), np.vstack(keep).max(0)
    half_x = float(np.ceil(min(max(-lo[0], hi[0]), 26)))
    return (-half_x, 12.0, float(np.floor(lo[2]))), (half_x, min(float(np.ceil(hi[1])), 112.0), float(np.ceil(hi[2])))


def subtree_up(g):
    out = [g]
    while g.parent is not None:
        g = g.parent
        out.append(g)
    return out


def hand_model(glow):
    """A casting hand on its own: `hand` (the gold), `glow_eye`, `glow_circle`; its pivot in the palm."""
    m = Model(f"occultech_archevoker_hand_{glow}")
    root = m.group("root", (0, 0, 0))
    f.hand_eye(root, "hand", (0, 24, 0), (0, 0, 0), glow, mirror=glow == "purple")
    h = group(m, "hand")
    new_bone(m, h, "glow_eye", h.origin, [c for c in cubes_in(m, h) if c.name.endswith("_iris")])
    new_bone(m, h, "glow_circle", h.origin, [c for c in cubes_in(m, h) if "_circle" in c.name])
    # the hand is the model's top bone; the root group only holds it
    h.parent.children.remove(h)
    m.root.children.append(h)
    h.parent = m.root
    root.parent.children.remove(root)
    m.groups.remove(root)
    snap(m)
    from bosses.coven_s2 import _resolve
    _resolve(m, {})                                          # no two faces on one plane
    return m


HAND_HITBOX = ((-9.0, 8.0, -5.0), (9.0, 47.0, 5.0))


def parts_list(m):
    rows = []
    for g in m.groups:
        cubes = [c for c in g.children if not hasattr(c, "children")]
        if cubes:
            mats = sorted({c.mat for c in cubes})
            parent = g.parent.name if g.parent is not None and g.parent.name != "root" else "-"
            rows.append(f"| `{g.name}` | {parent} | {len(cubes)} | {', '.join(mats)} |")
    return "\n".join(["| Bone | Parent | Cubes | Materials |", "|---|---|---|---|"] + rows)


# ---- renders ---------------------------------------------------------------------------------------------------------

MAIN_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 35, "height": 3.6, "dist": 12, "target_z": 4.2},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.4, "dist": 12, "target_z": 4.2,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_34", "mode": "clay", "camera": "persp", "yaw": -32, "height": 3.8, "dist": 12, "target_z": 4.2,
     "player": False},
]
POSE_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 35, "height": 3.6, "dist": 12.5, "target_z": 4.0,
     "player": False},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.2, "dist": 12.5, "target_z": 4.0,
     "player": False},
]
HAND_VIEWS = [
    {"name": "hand_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 1.7, "dist": 4.5, "target_z": 1.7,
     "player": False, "lens": 40},
    {"name": "hand_34", "mode": "flat", "camera": "persp", "yaw": 40, "height": 2.2, "dist": 4.5, "target_z": 1.7,
     "player": False, "lens": 40},
]


def build(key):
    m = rig(f"occultech_archevoker_{key}")
    pose(m, POSES[key][1])
    finish(m)
    return m


def side_by_side(paths, out):
    ims = [Image.open(p) for p in paths]
    w = sum(i.width for i in ims) + 10 * (len(ims) - 1)
    img = Image.new("RGB", (w, max(i.height for i in ims)), sheet.BG)
    x = 0
    for i in ims:
        img.paste(i, (x, 0))
        x += i.width + 10
    img.save(out)


def main(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    if not only:
        for old in OUT.rglob("*"):                           # files only: an open folder can't be removed
            if old.is_file() and old.name != "README.md":
                old.unlink()
        rest = build("rest")
        frm, to = hitbox_bounds(rest)
        bb = rest.to_bbmodel()
        bb["name"] = "occultech_archevoker"
        add_hitbox(bb, frm, to)
        (OUT / "design").mkdir(exist_ok=True)
        (OUT / "design" / "occultech_archevoker_blockout.bbmodel").write_text(json.dumps(bb, indent=1) + "\n",
                                                                               encoding="utf-8")
        hands = {glow: hand_model(glow) for glow in ("cyan", "purple")}
        for glow, hm in hands.items():
            hb = hm.to_bbmodel()
            add_hitbox(hb, *HAND_HITBOX)
            (OUT / "design" / f"occultech_archevoker_hand_{glow}_blockout.bbmodel").write_text(
                json.dumps(hb, indent=1) + "\n", encoding="utf-8")
        geo = lambda mm: sum(1 for g in mm.groups if any(not hasattr(c, "children") for c in g.children))
        stats = dict(rest.stats(), bones_with_geometry=geo(rest),
                     hitbox_blocks=[round((t - fr) / 16, 2) for fr, t in zip(frm, to)],
                     hand=dict(hands["cyan"].stats(), bones_with_geometry=geo(hands["cyan"]),
                               hitbox_blocks=[round((t - fr) / 16, 2) for fr, t in zip(*HAND_HITBOX)]))
        (OUT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        (OUT / "parts.md").write_text(
            "# The Archevoker blockout parts (session 2)\n\nGenerated by `tools/art/bosses/archevoker_s2.py`. Cube sizes "
            "are whole texels.\n\n## occultech_archevoker\n\n" + parts_list(rest) +
            "\n\n## occultech_archevoker_hand_cyan (the purple is its mirror)\n\n" + parts_list(hands["cyan"]) + "\n",
            encoding="utf-8")
        print(json.dumps(stats))
        shown = build("rest")
        casting_hands(shown, POSES["rest"][1])
        v2.run_blender(shown.render_json(v2.PALETTE), OUT / "design", MAIN_VIEWS)
        sheet.compare_sheet(OUT, [("design", "the design lock")], OUT / "design.png",
                            heading="The Archevoker - design lock (session 2)",
                            views=("flat_34", "flat_front", "sil_side", "clay_34"))
        boxes = rest.render_json(PALETTE)
        for bx in boxes:
            bx["color"] = [c * 0.55 + 0.4 for c in bx["color"]]
        boxes.append(v2.box_json("hitbox", frm, to, "hitbox"))
        v2.run_blender(boxes, OUT / "hitbox", [{"name": "hitbox_front", "mode": "flat", "camera": "ortho_front"},
                                               {"name": "hitbox_side", "mode": "flat", "camera": "ortho_side"}])
        side_by_side([OUT / "hitbox" / f"hitbox_{v}.png" for v in ("front", "side")], OUT / "hitbox.png")
        for glow, hm in hands.items():
            hboxes = hm.render_json(v2.PALETTE) + [dict(v2.box_json("hitbox", *HAND_HITBOX, "hitbox"), alpha=0.25)]
            v2.run_blender(hboxes, OUT / "hand" / glow, HAND_VIEWS)
        side_by_side([OUT / "hand" / g / f"{v}.png" for g in ("cyan", "purple") for v in ("hand_front", "hand_34")],
                     OUT / "hands.png")
    for key in (only or POSES):
        m = build(key)
        casting_hands(m, POSES[key][1])
        v2.run_blender(m.render_json(v2.PALETTE), OUT / "poses" / key, POSE_VIEWS)
    keys = list(POSES)
    if all((OUT / "poses" / k / "flat_34.png").exists() for k in keys):
        for i, chunk in enumerate((keys[:5], keys[5:])):
            sheet.compare_sheet(OUT / "poses", [(k, "") for k in chunk], OUT / f"poses_{i + 1}.png",
                                heading="The Archevoker - the key poses", views=("flat_34", "flat_front"))


if __name__ == "__main__":
    main(sys.argv[1:] or None)
