"""The Unbound redesign, session 2: design lock (plan: docs/art/bosses/the_unbound/overhaul/plan.md).

The approved blockout (unbound_s1.py) rebuilt as a rig:
- every part on a named bone (BetterModel names): the legs and shins, the torso (the hunch), `hi_head`, both arms
  and forearms, the cleaver in his right fist, the chains (they swing), the band's tails;
- the glow on its own bones: `glow_eye` (the cyan eye through the band) and `glow_chest` (the fire behind the grate);
- scaled to the planned size (3.25 blocks to the top of the head) and every cube snapped to whole texels;
- the hitbox (`ob_hitbox`): a column over his body and arms, never the horns, chains or cleaver;
- the fight's key poses, posed from the rig.

The cleaver and the chains are turned to a world direction in each pose (the rest of the rig is posed in the usual
way): the chains always hang, and the cleaver's edge always faces where the swing goes - up behind his shoulder,
down at the end of the sweep, up while he drags it. In the cleaver's own frame its handle runs up +y and its edge
faces -z.

Run from the repository root: python tools/art/bosses/unbound_s2.py
"""
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import unbound_face as uf, unbound_s1 as s1, volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/the_unbound/overhaul/s2_design"
PALETTE = dict(uf.PALETTE, **s1.PALETTE, hitbox=(220, 60, 60))
H = uf.HUNCH


# ---- rig helpers -------------------------------------------------------------------------------------------------

def group(model, name):
    return next(g for g in model.groups if g.name == name)


def cube(model, name):
    return next(c for c in model.cubes if c.name == name)


def move(c, g):
    """Puts a cube on another bone (cube coordinates are model-space, so it stays where it is)."""
    c.group.children.remove(c)
    g.children.append(c)
    c.group = g


def dissolve(model, name):
    """Hands an unrotated helper group's cubes to its parent (fewer bones, fewer displays)."""
    g = group(model, name)
    for c in [ch for ch in g.children if not hasattr(ch, "children")]:
        move(c, g.parent)
    g.parent.children.remove(g)
    model.groups.remove(g)


def euler(R):
    """Blockbench angles (x applied first: R = Rz Ry Rx) for a rotation matrix."""
    y = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    x = math.atan2(R[2, 1], R[2, 2])
    z = math.atan2(R[1, 0], R[0, 0])
    return [math.degrees(x), math.degrees(y), math.degrees(z)]


def aim(g, R):
    """Turns a bone so its world orientation is R, whatever its parents do."""
    parent = g.parent.world_matrix()[:3, :3]
    g.rotation = euler(parent.T @ R)


def frame(handle, edge):
    """A rotation taking the cleaver's handle (+y) to `handle` and its edge (-z) to `edge`."""
    y = np.array(handle, float)
    y /= np.linalg.norm(y)
    z = -np.array(edge, float)
    z -= y * (z @ y)
    z /= np.linalg.norm(z)
    x = np.cross(y, z)
    return np.column_stack([x, y, z])


def swing_edge(handle):
    """The edge faces where the overhead chop carries it: in his front-back plane, at right angles to the handle,
    turning from behind his shoulder over the top to the front and down (front is -z)."""
    hx, hy, hz = handle
    # in his (forward, up) plane the handle points (f, u) = (-hz, hy); the chop turns it up -> forward -> down, so
    # the blade moves (u, -f): forward = hy, up = hz, which is (y, z) = (hz, -hy) in model space (front is -z).
    # (Session 2's first take had this sign backwards: the spine led the sweep.)
    return (0.0, hz, -hy)


def translate(model, d):
    for g in model.groups:
        g.origin = [g.origin[i] + d[i] for i in range(3)]
    for c in model.cubes:
        c.frm = [c.frm[i] + d[i] for i in range(3)]
        c.to = [c.to[i] + d[i] for i in range(3)]
        c.origin = [c.origin[i] + d[i] for i in range(3)]


# ---- the rig --------------------------------------------------------------------------------------------------------

def hanging_chain(parent, name, top, length):
    """A chain on its own bone, hanging from top (model space) along -y; aimed straight down in every pose."""
    g = parent.group(name, top)
    x, y, z = top
    s1.chain_planes(g, name, (x, y - length / 2, z), length, "y")
    return g


def rig(name):
    model = Model(name)
    root = uf.bust(model, "MIX", "PIECE")
    torso, head = group(model, "torso"), group(model, "hi_head")
    root.origin = [0.0, 21.0, 0.5]                          # the root turns (and sinks) at the hips
    for sx in (-1, 1):
        s1.drop_cube(model, f"upper_arm_{sx}")
    for helper in ("chest", "back", "hump"):
        dissolve(model, helper)
    group(model, "horn_-1").name = "horn_left"
    group(model, "horn_1").name = "horn_right"
    # the glow on its own bones
    eye = head.group("glow_eye", tuple(cube(model, "eye").origin))
    for n in ("halo", "eye", "eye_core"):
        move(cube(model, n), eye)
    fire = torso.group("glow_chest", (0, 38, -9.8))
    for n in ("chest_fire", "chest_fire_hot"):
        move(cube(model, n), fire)
    tails = head.group("band_tails", tuple(cube(model, "knot").origin))
    for n in ("knot", "tail_a", "tail_b", "tail_c"):
        move(cube(model, n), tails)
    # hips and legs; the ankle chains drag behind on the ground, on their own bones
    root.box("pelvis", (0, 20, 0.5), (19, 7, 12.5), "pants")
    for sx, side in ((-1, "left"), (1, "right")):
        thigh = root.group(f"leg_{side}", (sx * 5.5, 21, 0.5))
        thigh.box(f"thigh_{side}", (sx * 5.8, 15.5, 0), (9, 12, 9.5), "pants")
        shin = thigh.group(f"shin_{side}", (sx * 5.8, 10, 0))
        shin.box(f"shin_{side}_box", (sx * 5.8, 6, 0.2), (8.4, 9, 8.6), "pants")
        shin.box(f"boot_{side}", (sx * 5.8, 1.5, -1.0), (9.4, 3, 11.5), "boot")
        s1.shackle(shin, f"ankle_shackle_{side}", (sx * 5.8, 5.2, 0.2), (8.4, 3.2, 8.6))
        ankle = shin.group(f"chain_ankle_{side}", (sx * 7.5, 4.5, 5.2))
        s1.chain(ankle, f"ankle_chain_{side}", (sx * 7.5, 4.5, 5.2), 3, (sx * 0.15, 0.95))
    # the arms; the wrist chains and the cleaver hang off the forearms
    for sx, side in ((-1, "left"), (1, "right")):
        s1.arm(torso, side, sx, (0, 0, 0), (0, 0, 0))
        hanging_chain(group(model, f"forearm_{side}"), f"chain_wrist_{side}", (sx * 19.6, 13.2, -0.4), 12)
    s1.cleaver(group(model, "forearm_right"), (19.8, 10.2, -0.8), (0, 0, 0))
    return model


# ---- poses -----------------------------------------------------------------------------------------------------------
# torso / head: pitch added to the rest hunch and head lift. arms: (upper, forearm) rotations relative to the torso.
# legs: (thigh, shin). drop: how far the hips sink (kneeling). cleaver: drag | windup | sweep | flat.

REST_LEGS = {"left": ((-8, 0, 3), (12, 0, 0)), "right": ((-8, 0, -3), (12, 0, 0))}
POSES = {
    "idle": ("idle and walking: the cleaver dragged", {
        "arms": {"left": ((-H, 0, -6), (4, 0, -3)), "right": ((-H - 14, 0, 6), (-6, 0, 3))}, "cleaver": "drag"}),
    "windup": ("the cleave: wound up over his shoulder (the red wedge shows)", {
        "torso": 6, "head": -4,
        "arms": {"left": ((-H + 4, 0, -16), (10, 0, -6)), "right": ((100, 0, 40), (130, 0, -30))},
        "legs": {"left": ((14, 0, 6), (-10, 0, 0)), "right": ((-14, 0, -6), (14, 0, 0))}, "cleaver": "windup"}),
    "sweep": ("the cleave: the sweep lands", {
        "torso": -20, "head": 16,
        "arms": {"left": ((-30, 0, -14), (-10, 0, 0)), "right": ((62, 0, 14), (16, 0, 0))},
        "legs": {"left": ((26, 0, 4), (-24, 0, 0)), "right": ((-24, 0, -4), (14, 0, 0))}, "cleaver": "sweep"}),
    "call": ("calling the thralls: a roar, arms spread", {
        "torso": 10, "head": 26,
        "arms": {"left": ((-H + 6, 0, -42), (0, 0, -12)), "right": ((-H + 6, 0, 42), (0, 0, 12))},
        "legs": {"left": ((-4, 0, 8), (6, 0, 0)), "right": ((-4, 0, -8), (6, 0, 0))}, "cleaver": "drag"}),
    "devour": ("devouring a thrall: hunched over, his fist to his mouth", {
        "torso": -26, "head": -6,
        "arms": {"left": ((76, 0, -14), (96, 0, 12)), "right": ((-H + 26, 0, 8), (0, 0, 3))},
        "legs": {"left": ((10, 0, 4), (-4, 0, 0)), "right": ((-6, 0, -4), (12, 0, 0))}, "cleaver": "drag"}),
    "sated": ("sated: down on one knee, the cleaver dropped (3 s)", {
        "drop": 7, "torso": -22, "head": -10, "hang": True,
        "legs": {"left": ((80, 0, 4), (-80, 0, 0)), "right": ((0, 0, -3), (-90, 0, 0))}, "cleaver": "flat"}),
    "charge": ("enraged: the charge, head down, horns first", {
        "torso": -26, "head": 22,
        "arms": {"left": ((-24, 0, -10), (-8, 0, 0)), "right": ((-20, 0, 8), (-4, 0, 0))},
        "legs": {"left": ((32, 0, 3), (-34, 0, 0)), "right": ((-28, 0, -3), (18, 0, 0))}, "cleaver": "drag"}),
    "death": ("death: on his knees, folding forward", {
        "drop": 7, "torso": -50, "head": -18, "hang": True,
        "legs": {"left": ((0, 0, 3), (-90, 0, 0)), "right": ((0, 0, -3), (-90, 0, 0))}, "cleaver": "flat"}),
}


def pose(model, spec):
    torso, head = group(model, "torso"), group(model, "hi_head")
    torso.rotation[0] = H + spec.get("torso", 0)
    head.rotation[0] = -H - 4 + spec.get("head", 0)
    for side in ("left", "right"):
        thigh, shin = spec.get("legs", REST_LEGS)[side]
        group(model, f"leg_{side}").rotation = list(thigh)
        group(model, f"shin_{side}").rotation = list(shin)
        if spec.get("hang"):
            # arms hanging straight down whatever the torso does
            sx = -1 if side == "left" else 1
            aim(group(model, f"arm_{side}"), np.eye(3))
            group(model, f"arm_{side}").rotation[2] += sx * 6
            group(model, f"forearm_{side}").rotation = [0, 0, 0]
        else:
            upper, fore = spec["arms"][side]
            group(model, f"arm_{side}").rotation = list(upper)
            group(model, f"forearm_{side}").rotation = list(fore)
    for side in ("left", "right"):
        aim(group(model, f"chain_wrist_{side}"), np.eye(3))
    cl = group(model, "cleaver")
    kind = spec["cleaver"]
    if kind == "drag":
        # back and down until its spine meets the ground; the edge up
        for down in range(0, 90):
            a = math.radians(down)
            h = (0.0, -math.sin(a), math.cos(a))
            aim(cl, frame(h, swing_edge(h)))
            if min(c.corners()[:, 1].min() for c in model.cubes if c.group is cl) <= 0.6:
                break
    elif kind == "windup":
        h = np.array((-0.32, 0.5, 0.8))
        aim(cl, frame(h, swing_edge(h / np.linalg.norm(h))))
    elif kind == "sweep":
        h = np.array((0.08, -0.62, -0.78))
        aim(cl, frame(h, swing_edge(h / np.linalg.norm(h))))
    else:
        # dropped: lying flat on the ground by his right hand, pointing ahead
        aim(cl, frame((0.25, 0.0, -0.97), (1.0, 0.0, 0.0)))
    if spec.get("drop"):
        translate(model, (0, -spec["drop"], 0))
    if kind == "flat":
        # resting on the floor: move the whole cleaver down (its cubes and its pivot together)
        low = min(c.corners()[:, 1].min() for c in model.cubes if c.group is cl)
        cl.origin[1] -= low
        for c in model.cubes:
            if c.group is cl:
                c.frm[1] -= low
                c.to[1] -= low
                c.origin[1] -= low


def build(name, key="idle"):
    model = rig(name)
    pose(model, POSES[key][1])
    return model


# ---- size, snap, hitbox -----------------------------------------------------------------------------------------------

def finish(model, k):
    s1.scale(model, k)
    v2.snap(model)
    for c in model.cubes:                       # the chains' planes stay flat (snapping makes every size at least 1)
        if c.mat == "chain" and c.name.endswith(("_a", "_b")):
            lo, hi = np.array(c.frm), np.array(c.to)
            mid = (lo + hi) / 2
            flat = {"_a": 2, "_b": 0}[c.name[-2:]] if not "_lie" in c.name else {"_a": 0, "_b": 1}[c.name[-2:]]
            lo[flat] = hi[flat] = mid[flat]
            c.frm, c.to = lo.tolist(), hi.tolist()


def in_subtree(c, names):
    g = c.group
    while g is not None:
        if any(g.name.startswith(n) for n in names):
            return True
        g = g.parent
    return False


def hitbox_bounds(model):
    """A column over his body and arms, from the floor to the top of his head: not the horns, the band's tails, the
    chains or the cleaver, so nothing loose is a free target."""
    pts = np.vstack([c.corners() for c in model.cubes
                     if not in_subtree(c, ("horn_", "band_tails", "chain_", "cleaver", "glow_"))])
    lo, hi = pts.min(0), pts.max(0)
    half_x = float(np.ceil(max(-lo[0], hi[0])))
    return (-half_x, 0.0, float(np.floor(lo[2]))), (half_x, float(np.ceil(hi[1])), float(np.ceil(hi[2])))


def parts_list(model):
    rows = []
    for g in model.groups:
        cubes = [c for c in g.children if not hasattr(c, "children")]
        if cubes:
            mats = sorted({c.mat for c in cubes})
            parent = g.parent.name if g.parent is not None and g.parent.name != "root" else "-"
            rows.append(f"| `{g.name}` | {parent} | {len(cubes)} | {', '.join(mats)} |")
    return "\n".join(["| Bone | Parent | Cubes | Materials |", "|---|---|---|---|"] + rows)


MAIN_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 35, "height": 3.2, "dist": 8.5, "target_z": 1.6},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 2.2, "dist": 8, "target_z": 1.7},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
    {"name": "clay_34", "mode": "clay", "camera": "persp", "yaw": -30, "height": 2.8, "dist": 8, "target_z": 1.6,
     "player": False},
]
POSE_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 40, "height": 3.0, "dist": 8.5, "target_z": 1.5,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
]


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    uf.PALETTE.update(PALETTE)
    rest = build("occultech_unbound_blockout")
    k = s1.HEAD_TOP / float(cube(rest, "head").corners()[:, 1].max())
    finish(rest, k)
    frm, to = hitbox_bounds(rest)
    bb = rest.to_bbmodel()
    add_hitbox(bb, frm, to)
    main_dir = OUT / "design"
    main_dir.mkdir()
    (main_dir / "occultech_unbound_blockout.bbmodel").write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    uf.render_glowing(rest, main_dir, MAIN_VIEWS, {"player_at": [-2.6, 0.0]})
    stats = dict(rest.stats(), scale=round(k, 3), hitbox_blocks=[round((t - f) / 16, 2) for f, t in zip(frm, to)])
    (OUT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    sheet.compare_sheet(OUT, [("design", "the design lock")], OUT / "design.png",
                        heading="The Unbound - design lock (session 2)", views=("flat_34", "flat_front", "sil_side", "clay_34"))
    # the hitbox, a solid red box over the model
    boxes = rest.render_json(PALETTE)
    for b in boxes:
        b["color"] = [c * 0.55 + 0.4 for c in b["color"]]
    boxes.append(v2.box_json("hitbox", frm, to, "hitbox"))
    v2.run_blender(boxes, OUT / "hitbox", [{"name": "hitbox_front", "mode": "flat", "camera": "ortho_front"},
                                           {"name": "hitbox_side", "mode": "flat", "camera": "ortho_side"}])
    from PIL import Image
    a, b = (Image.open(OUT / "hitbox" / f"hitbox_{v}.png") for v in ("front", "side"))
    both = Image.new("RGB", (a.width + b.width + 10, a.height), sheet.BG)
    both.paste(a, (0, 0))
    both.paste(b, (a.width + 10, 0))
    both.save(OUT / "hitbox.png")
    # the key poses
    for key in POSES:
        posed = build(f"occultech_unbound_{key}", key)
        finish(posed, k)
        uf.render_glowing(posed, OUT / "poses" / key, POSE_VIEWS)
    keys = list(POSES)
    for i, chunk in enumerate((keys[:4], keys[4:])):
        sheet.compare_sheet(OUT / "poses", [(key, "") for key in chunk], OUT / f"poses_{i + 1}.png",
                            heading="The Unbound - the key poses (" + ", ".join(chunk) + ")", views=("flat_34", "sil_side"))
    (OUT / "parts.md").write_text("# The Unbound blockout parts (session 2)\n\nGenerated by `tools/art/bosses/unbound_s2.py`. "
                                  "Cube sizes are whole texels.\n\n" + parts_list(rest) + "\n", encoding="utf-8")
    print(stats)


if __name__ == "__main__":
    main()
