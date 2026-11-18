"""The Hollow Warlord (the Headsman), session 2: design lock (plan: docs/art/bosses/hollow_warlord/overhaul/plan.md).

The approved blockout (headsman_blockout.py: the Plate, the Kettle Hat, the Executioner's sword) rebuilt as a rig:
- the bind pose stands upright, arms hanging, the sword held level ahead, so limbs are whole-texel boxes along the axes;
- every part on a BetterModel bone: hips > torso > hi_head > hat; arms, forearms, the sword in the right fist; thighs,
  shins, feet; the tabard's front and back; the three taken skulls on their own bones off the model's root (they float
  in world space and never lean with him);
- the glow on its own bones: glow_eyes (his eyes), glow_brand (the sword's brand), glow_skull_c/l/r (each taken skull's
  eyes and soul fire, so a skull can go dark when its guard dies);
- the hat on its own bone so the enraged phase can drop it;
- the hitbox (ob_hitbox): a column over his body, not the skulls, the sword or the tabard;
- the fight's key poses from the rig: two-bone IK on arms and legs (fixed bone lengths), the sword aimed in world space.

The skull faces (his and the taken ones) are the real wither skeleton pixels, drawn over the renders as decals; in the
model each skull is one 16-unit cube that session 4 maps to the vanilla skin at 2x.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the argument:
python tools/art/bosses/headsman_s2.py <folder>
"""
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Group, Model, add_hitbox, rotation_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import headsman_study as st, headsman_take2 as h2, volley_crone_s2 as v2  # noqa: E402
from bosses.headsman_silhouettes import _n  # noqa: E402
from bosses.tide_silhouettes import frame  # noqa: E402

OUT = ROOT / "docs/art/bosses/hollow_warlord/overhaul/s2_design"
NAME = "occultech_hollow_warlord"
HIP = h2.HIP                       # 34
T = h2.T
HEAD_BASE = HIP + 35               # the skull's underside
HEAD_PIVOT = (0.0, HEAD_BASE, -3.0)
SHOULDER = 20.0                    # shoulder joints at x +-20, 31 above the hips
ARM = (20.0, 19.0)                 # upper arm, forearm
LEG = (16.5, 12.5)                 # thigh, shin (the ankle 5 above the sole)
HIP_X = 7.0
PALETTE = dict(h2.PALETTE, hitbox=(220, 60, 60), px_5aecf4=(90, 236, 244))
GLOW = {"slit", "soul", "flame", "brand", "px_5aecf4"}


# ---- helpers ----------------------------------------------------------------------------------------------------------

def group(model, name):
    return next(g for g in model.groups if g.name == name)


def col(g, name, top, bottom, w, mat, d=None):
    """An upright box from top to bottom (rest pose), w wide, d deep."""
    top, bottom = np.array(top, float), np.array(bottom, float)
    c = (top + bottom) / 2
    return g.box(name, tuple(c), (w, abs(top[1] - bottom[1]), d or w), mat)


def euler(R):
    y = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    x = math.atan2(R[2, 1], R[2, 2])
    z = math.atan2(R[1, 0], R[0, 0])
    return [math.degrees(x), math.degrees(y), math.degrees(z)]


def aim(g, R):
    """Turns a bone so its world orientation is R, whatever its parents do."""
    parent = g.parent.world_matrix()[:3, :3]
    g.rotation = euler(parent.T @ R)


def turn_to(d0, d, roll_hint=None):
    """The smallest rotation taking direction d0 to d."""
    a, b = _n(d0), _n(d)
    v = np.cross(a, b)
    c = float(a @ b)
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3) if c > 0 else rotation_matrix((180, 0, 0))
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k * (1 / (1 + c))


def wpos(g, p):
    return (g.world_matrix() @ np.array([*p, 1.0]))[:3]


def ik(root_pt, target, hint, l1, l2):
    """Two-bone IK: the middle joint for fixed lengths, bending towards `hint`."""
    root_pt, target, hint = (np.array(v, float) for v in (root_pt, target, hint))
    d = target - root_pt
    dist = min(np.linalg.norm(d), l1 + l2 - 0.05)
    u = _n(d)
    a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    p = hint - root_pt
    p = p - u * (p @ u)
    p = _n(p) if np.linalg.norm(p) > 1e-6 else _n(np.cross(u, (1, 0, 0)))
    return root_pt + u * a + p * h, root_pt + u * dist


def translate(g, d):
    d = np.array(d, float)
    g.origin = (np.array(g.origin) + d).tolist()
    for ch in g.children:
        if isinstance(ch, Group):
            translate(ch, d)
        else:
            ch.frm, ch.to, ch.origin = [(np.array(v) + d).tolist() for v in (ch.frm, ch.to, ch.origin)]


# ---- the rig ----------------------------------------------------------------------------------------------------------

SKULLS = {"c": ((0, 38, 20), 0, 0), "l": ((-30, 28, 16), -20, 12), "r": ((30, 28, 16), 20, -12)}  # off the head centre


def rig():
    m = Model(NAME)
    hips = m.group("hips", (0, HIP, 0))
    # the tabard: front and back strips on their own bones (they swing)
    hips.box("belt", T(0, 2.5, 0.5), (19, 4, 11), "leather_dark")
    for side, z, strips in (("front", -6.5, (("tab_fl", -2.6, 24, "cloth"), ("tab_fr", 2.8, 18, "cloth"))),
                            ("back", 7.0, (("tab_bl", -3, 20, "cloth_dark"), ("tab_br", 3, 25, "cloth_dark")))):
        g = hips.group(f"tabard_{side}", T(0, 1, z))
        for name, x, length, mat in strips:
            g.box(name, (x, HIP + 1 - length / 2, z), (5, length, 2), mat)
    # the legs: thigh > shin > foot, upright in the bind pose
    for s, side in ((-1, "left"), (1, "right")):
        hip = (s * HIP_X, HIP, 0.0)
        knee = (s * HIP_X, HIP - LEG[0], 0.0)
        ankle = (s * HIP_X, HIP - LEG[0] - LEG[1], 0.0)
        thigh = hips.group(f"leg_{side}", hip)
        col(thigh, f"thigh_{side}", hip, knee, 6, "bone")
        shin = thigh.group(f"shin_{side}", knee)
        shin.box(f"knee_{side}", (knee[0], knee[1], -1.5), (9, 8, 6), "plate_lit")
        col(shin, f"shin_{side}_bone", knee, ankle, 6, "bone")
        col(shin, f"greave_{side}", (knee[0], knee[1] - 3, 0), (ankle[0], ankle[1] + 0.5, 0), 10, "plate")
        foot = shin.group(f"foot_{side}", ankle)
        foot.box(f"sabaton_{side}", (ankle[0], 2.5, -3.5), (10, 5, 16), "plate")
    # the torso: waist, ribs, breastplate, pauldrons on their own bones, gorget, neck
    torso = hips.group("torso", (0, HIP, 0))
    h2.spine_and_waist(torso)
    h2.breastplate(torso)
    h2.bone_chest(torso)
    h2.gorget(torso)
    torso.box("neck", (0, HEAD_BASE - 2.5, -1), (6, 7, 6), "bone")
    for s, side in ((-1, "left"), (1, "right")):
        p = torso.group(f"pauldron_{side}", T(s * SHOULDER, 32, 0))
        h2.pauldron(p, s)
    # the head: the skull (one cube; its face is painted in session 4), the eyes' glow, the hat on its own bone
    head = torso.group("hi_head", HEAD_PIVOT)
    head.box("skull", (0, HEAD_BASE + 8, -3), (16, 16, 16), "skull")
    eyes = head.group("glow_eyes", (0, HEAD_BASE + 7, -11))
    for s in (-1, 1):
        eyes.box(f"eye_{'right' if s > 0 else 'left'}", (s * 4, HEAD_BASE + 7, -11.1), (4, 2, 0.2), "px_5aecf4")
    hat = head.group("hat", (0, HEAD_BASE + 11, -3))
    tmp = Model("tmp")
    th = tmp.group("h", (0, 0, 0))
    st.helm_kettle(th, HEAD_BASE)
    for c in list(th.children):
        if c.name.startswith(("px", "skull", "teeth")):
            continue
        c.frm[2] -= 2
        c.to[2] -= 2
        c.origin[2] -= 2
        c.group = hat
        hat.children.append(c)
        m.cubes.append(c)
    # the arms: arm > forearm (gauntlet, hand) > the sword in the right fist
    for s, side in ((-1, "left"), (1, "right")):
        sh = T(s * SHOULDER, 31, 0)
        el = (sh[0], sh[1] - ARM[0], 0)
        wr = (sh[0], el[1] - ARM[1], 0)
        arm = torso.group(f"arm_{side}", sh)
        arm.box(f"shoulder_{side}", sh, (9, 9, 9), "bone_dark")
        col(arm, f"upper_{side}", sh, el, 6, "bone")
        col(arm, f"rerebrace_{side}", (sh[0], sh[1] - 5, 0), (el[0], el[1] + 4, 0), 8, "plate")
        fore = arm.group(f"forearm_{side}", el)
        fore.box(f"elbow_{side}", el, (8, 8, 8), "bone_dark")
        col(fore, f"fore_{side}", el, wr, 6, "bone")
        col(fore, f"gauntlet_{side}", (el[0], el[1] - 6, 0), wr, 10, "plate")
        fore.box(f"cuff_{side}", (el[0], el[1] - 6.5, 0), (12, 3, 12), "plate_lit")
        fore.box(f"hand_{side}", (wr[0], wr[1] - 3.5, 0), (8, 8, 8), "plate")
    hand = (SHOULDER, HIP + 31 - ARM[0] - ARM[1] - 3.5, 0)
    sword = group(m, "forearm_right").group("sword", hand)
    st.sword_executioner(sword, hand, (0, 0, -1), (1, 0, 0))
    brand = sword.group("glow_brand", hand)
    b = next(c for c in m.cubes if c.name == "brand")
    sword.children.remove(b)
    brand.children.append(b)
    b.group = brand
    # the taken skulls: off the model's root, so they never lean with him
    head_c = np.array([0, HEAD_BASE + 8, -3.0])
    for key, (off, _, _) in SKULLS.items():
        c = head_c + off
        g = m.group(f"skull_{key}", tuple(c))
        g.box(f"skull_{key}_cube", tuple(c), (16, 16, 16), "trophy")
        glow = g.group(f"glow_skull_{key}", tuple(c))
        for s in (-1, 1):
            glow.box(f"skull_{key}_eye{s}", (c[0] + s * 4, c[1] - 1, c[2] - 8.1), (4, 2, 0.2), "px_5aecf4")
        g.box(f"skull_{key}_vert0", (c[0], c[1] - 9.5, c[2] + 3), (6, 3, 6), "bone")      # a severed vertebra
        g.box(f"skull_{key}_vert1", (c[0], c[1] - 12.5, c[2] + 3.5), (4, 3, 4), "bone_dark")
    return m


# ---- poses ------------------------------------------------------------------------------------------------------------
# lean/twist: the torso; head: (pitch, yaw) on hi_head; drop: the hips sink; legs: per side (ankle, knee hint, toe);
# sword: (grip, tip direction, flat normal) in world space; left: where the left hand goes (None: hanging, or "grip");
# hat: on/off; lit: the taken skulls' fire.

A = 5.0
POSES = {
    "idle": ("idle: the point on the floor ahead, the skulls lit", dict(
        lean=18, twist=0, head=(14, 0), drop=0,
        legs={"right": ((11, A, -1), (10, 18, -8), (0, 0, -1)), "left": ((-12, A, 4), (-10, 18, -4), (0, 0, -1))},
        sword=((17, 40, -12), (0.25, -0.62, -1), (1, 0.2, -0.1)), elbow_r=(28, 48, -2),
        left=None, elbow_l=(-28, 46, -2), hand_l=(-27, 27, -6))),
    "walk": ("walking: the sword dragged behind him", dict(
        lean=22, twist=0, head=(18, 0), drop=0,
        legs={"right": ((9, A, 16), (9, 18, 2), (0, 0, -1)), "left": ((-9, A, -10), (-9, 17, -14), (0, 0, -1))},
        sword=((19, 28, 12), (0.22, -0.33, 1), (1, 0, -0.22)), elbow_r=(26, 46, 8),
        left=None, elbow_l=(-25, 46, -10), hand_l=(-25, 28, -18))),
    "windup": ("the soul sweep's warning: twisted back, the blade trailing low behind", dict(
        lean=20, twist=34, head=(16, -30), drop=3,
        legs={"right": ((18, A, 10), (14, 16, 2), (0.3, 0, -1)), "left": ((-18, A, -8), (-14, 16, -12), (-0.2, 0, -1))},
        sword=((22, 32, 10), (0.55, -0.32, 0.78), (0.8, 0.2, -0.55)), elbow_r=(30, 46, 10),
        left="grip", elbow_l=(4, 44, -6))),
    "sweep": ("the sweep: level at hip height, two hands", dict(
        lean=20, twist=-32, head=(14, -20), drop=0,
        legs={"right": ((20, A, -6), (15, 17, -12), (0, 0, -1)), "left": ((-20, A, 10), (-15, 17, 2), (0, 0, -1))},
        sword=((17, 36, -24), (1, 0.04, 0.32), (-0.32, 0, 1)), elbow_r=(28, 46, -18),
        left="grip", elbow_l=(0, 42, -22))),
    "enraged": ("enraged (below 35%): the hat gone, the sword cocked over his shoulder", dict(
        lean=22, twist=12, head=(10, -6), drop=5, hat=False,
        legs={"right": ((13, A, 13), (12, 15, 3), (0, 0, -1)), "left": ((-13, A, -11), (-12, 16, -15), (0, 0, -1))},
        sword=((15, 76, -2), (0.2, -0.42, 1), (1, 0.2, 0)), elbow_r=(32, 66, -8),
        left="grip", elbow_l=(-6, 66, -16))),
    "death": ("death: on one knee, the sword driven into the floor; the skulls fallen, dark", dict(
        lean=26, twist=0, head=(-8, 0), drop=13, lit=False,
        legs={"right": ((8, 4, 15), (8, 4.5, -6), (0, -0.4, 1)), "left": ((-9, A, -14), (-8, 18, -20), (0, 0, -1))},
        sword=((0, 44, -24), (0, -1, -0.08), (0, 0, -1)), elbow_r=(18, 40, -18),
        left="grip", elbow_l=(-18, 40, -18))),
}
SWORD_REST = ((0, 0, -1), (1, 0, 0))


def sword_frame(tip, normal):
    a = _n(tip)
    w = _n(np.cross(normal, a))
    return frame(a, w)


def place_arm(m, torso, side, wrist_target, hint):
    s = 1 if side == "right" else -1
    arm, fore = group(m, f"arm_{side}"), group(m, f"forearm_{side}")
    sh = wpos(torso, arm.origin)
    el, wr = ik(sh, wrist_target, hint, *ARM)
    aim(arm, turn_to((0, -1, 0), el - sh))
    aim(fore, turn_to((0, -1, 0), wr - el))


def pose(m, key):
    p = POSES[key][1]
    hips, torso = group(m, "hips"), group(m, "torso")
    reach = sum(LEG) - 0.4
    drop = p["drop"]
    for side, (ankle, _, _) in p["legs"].items():      # sink the hips until both feet can reach the floor
        s = 1 if side == "right" else -1
        h = math.hypot(ankle[0] - s * HIP_X, ankle[2])
        drop = max(drop, HIP - (ankle[1] + math.sqrt(max(0.0, reach * reach - h * h))))
    p = dict(p, drop=drop)
    if drop:
        translate(hips, (0, -drop, 0))
    torso.rotation = [-p["lean"], p["twist"], 0]
    group(m, "hi_head").rotation = [p["head"][0], p["head"][1], 0]
    # the legs
    for side, (ankle, hint, toe) in p["legs"].items():
        s = 1 if side == "right" else -1
        hip = wpos(hips, group(m, f"leg_{side}").origin)
        knee, ank = ik(hip, ankle, hint, *LEG)
        aim(group(m, f"leg_{side}"), turn_to((0, -1, 0), knee - hip))
        aim(group(m, f"shin_{side}"), turn_to((0, -1, 0), ank - knee))
        t = _n(toe)
        aim(group(m, f"foot_{side}"), turn_to((0, 0, -1), t))
    # the sword arm: the wrist sits above the grip along the forearm's line, then the sword is aimed from the hand
    grip, tip, normal = p["sword"]
    grip = np.array(grip, float)
    R = sword_frame(tip, normal) @ sword_frame(*SWORD_REST).T
    d = _n(grip - np.array(p["elbow_r"], float))       # the hand hangs 3.5 below the wrist along the forearm
    place_arm(m, torso, "right", grip - d * 3.5, p["elbow_r"])
    aim(group(m, "sword"), R)
    sw = group(m, "sword")
    hand_now = wpos(sw.parent, sw.origin)
    off = grip - hand_now                                # whatever IK could not reach: nudge the sword onto the grip
    if np.linalg.norm(off) > 0.5:
        sw = group(m, "sword")
        local = np.linalg.inv(sw.parent.world_matrix()[:3, :3]) @ off
        translate(sw, local)
    a = _n(tip)
    if p.get("left") == "grip":
        target = grip - a * 6
        d = _n(target - np.array(p["elbow_l"], float))
        place_arm(m, torso, "left", target - d * 3.5, p["elbow_l"])
    else:
        hand = np.array(p["hand_l"], float)
        d = _n(hand - np.array(p["elbow_l"], float))
        place_arm(m, torso, "left", hand - d * 3.5, p["elbow_l"])
    # the hat
    group(m, "hat").visible = p.get("hat", True)
    # the taken skulls follow the head's position (not its lean), turned with the twist; at death they lie on the floor
    head_c = next(c for c in m.cubes if c.name == "skull").corners().mean(0)
    tw = math.radians(p["twist"])
    for k, (off, yaw, roll) in SKULLS.items():
        g = group(m, f"skull_{k}")
        if p.get("lit", True):
            x, z = off[0] * math.cos(tw) + off[2] * math.sin(tw), -off[0] * math.sin(tw) + off[2] * math.cos(tw)
            target = head_c + [x, off[1], z]
            g.rotation = [0, yaw + p["twist"], roll]
        else:
            target, rot = {"c": ((4, 8.6, 26), (0, 20, 0)), "l": ((-30, 9.6, -6), (0, -50, 18)),
                           "r": ((32, 9.6, 8), (0, 35, -12))}[k]
            target = np.array(target, float)
            g.rotation = list(rot)
        translate(g, target - np.array(g.origin))
        group(m, f"glow_skull_{k}").visible = p.get("lit", True)
    return m


# ---- finish, decals, hitbox, renders ------------------------------------------------------------------------------

def finish(m):
    v2.snap(m)


def decals(m):
    """The real wither skeleton pixels on every skull (render only: session 4 paints them into the texture)."""
    root = m.group("decals", (0, 0, 0))
    for gname, cname, eyes in [("hi_head", "skull", True)] + [(f"skull_{k}", f"skull_{k}_cube", True) for k in SKULLS]:
        g = group(m, gname)
        cube = next(c for c in m.cubes if c.name == cname)
        center = cube.corners().mean(0)
        R = g.world_matrix()[:3, :3]
        lit = eyes and (gname == "hi_head" or group(m, "glow_" + gname).visible)
        st.pixel_skull(root, center, tuple(euler(R)), eyes=lit, name="decal_" + gname)
    return m


def visible_boxes(m, palette):
    hidden = set()
    for g in m.groups:
        x = g
        while x is not None:
            if not x.visible:
                hidden.add(g.name)
                break
            x = x.parent
    boxes = []
    for c in m.cubes:
        if c.group.name in hidden:
            continue
        col_ = palette[c.mat]
        boxes.append({"name": c.name, "mat": c.mat, "color": [v / 255 for v in col_[:3]],
                      "corners": c.corners().tolist()})
    return boxes


def render_glowing(m, out, views, extra=None):
    """A normal render, then an unlit pass with only the glow coloured, laid over it with a bloom."""
    def job(palette, folder, vs, more):
        folder.mkdir(parents=True, exist_ok=True)
        f = folder / "render_job.json"
        f.write_text(json.dumps(dict({"boxes": visible_boxes(m, palette), "out": folder.as_posix(), "views": vs,
                                      "res": [900, 700]}, **more)), encoding="utf-8")
        import subprocess
        r = subprocess.run([str(v2.BLENDER), "-b", "--factory-startup", "--python",
                            str(ROOT / "tools/art/bosskit/blender_render.py"), "--", str(f)], capture_output=True, text=True)
        if r.returncode or "RENDER_DONE" not in r.stdout:
            raise SystemExit(r.stdout[-2000:] + r.stderr[-2000:])
        f.unlink()
    job(v2.PALETTE, out, views, extra or {})
    dark = {k: (v if k in GLOW else (0, 0, 0)) for k, v in v2.PALETTE.items()}
    job(dark, out / "glow", [dict(v, light="FLAT") for v in views],
        dict(extra or {}, ground=[0, 0, 0], sky=[0, 0, 0], player_color=[0, 0, 0]))
    for v in views:
        if v["mode"] != "flat":
            continue
        base = Image.open(out / f"{v['name']}.png").convert("RGB")
        mask = Image.open(out / "glow" / f"{v['name']}.png").convert("RGB")
        lit = mask.convert("L").point(lambda x: 255 if x > 24 else 0)
        base.paste(mask, (0, 0), lit)
        bloom = mask.filter(ImageFilter.GaussianBlur(8)).point(lambda x: min(255, int(x * 1.1)))
        ImageChops.screen(base, bloom).save(out / f"{v['name']}.png")
    shutil.rmtree(out / "glow")


def in_subtree(c, names):
    g = c.group
    while g is not None:
        if any(g.name.startswith(n) for n in names):
            return True
        g = g.parent
    return False


def hitbox_bounds(m):
    pts = np.vstack([c.corners() for c in m.cubes
                     if not in_subtree(c, ("skull_", "sword", "tabard_", "glow_", "decals"))])
    lo, hi = pts.min(0), pts.max(0)
    half_x = float(np.ceil(max(-lo[0], hi[0])))
    return (-half_x, 0.0, float(np.floor(lo[2]))), (half_x, float(np.ceil(hi[1])), float(np.ceil(hi[2])))


def parts_list(m):
    rows = []
    for g in m.groups:
        cubes = [c for c in g.children if not isinstance(c, Group)]
        if cubes:
            mats = sorted({c.mat for c in cubes})
            parent = g.parent.name if g.parent is not None and g.parent.name != "root" else "-"
            rows.append(f"| `{g.name}` | {parent} | {len(cubes)} | {', '.join(mats)} |")
    return "\n".join(["| Bone | Parent | Cubes | Materials |", "|---|---|---|---|"] + rows)


MAIN_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": -32, "height": 2.0, "dist": 12, "target_z": 3.8,
     "lens": 30},
    {"name": "flat_front", "mode": "flat", "camera": "ortho_front"},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
    {"name": "clay_34", "mode": "clay", "camera": "persp", "yaw": 30, "height": 3.0, "dist": 13, "target_z": 3.4,
     "player": False},
]
POSE_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": -30, "height": 2.2, "dist": 13, "target_z": 3.6,
     "lens": 30, "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
]


def main(args):
    st.SKIN = Image.open(Path(args[0]) / "assets/minecraft/textures/entity/skeleton/wither_skeleton.png").convert("RGBA")
    v2.PALETTE.update(PALETTE)
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    # the bind pose: the exported model
    bind = rig()
    finish(bind)
    frm, to = hitbox_bounds(pose(rig(), "idle"))
    bb = bind.to_bbmodel()
    add_hitbox(bb, frm, to)
    (OUT / "design").mkdir()
    (OUT / "design" / f"{NAME}_blockout.bbmodel").write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    render_glowing(decals(rig()), OUT / "bind", [MAIN_VIEWS[1]])
    # the design lock, shown in the idle pose
    idle = pose(rig(), "idle")
    finish(idle)
    render_glowing(decals(idle), OUT / "design", MAIN_VIEWS)
    stats = dict(bind.stats(), hitbox_blocks=[round((t - f) / 16, 2) for f, t in zip(frm, to)],
                 idle_size_blocks=idle.stats()["size_blocks"])
    (OUT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    sheet.compare_sheet(OUT, [("design", "the design lock (idle)")], OUT / "design.png",
                        heading="Hollow Warlord - design lock (session 2)",
                        views=("flat_34", "flat_front", "sil_side", "clay_34"))
    # the hitbox
    boxes = visible_boxes(idle, v2.PALETTE)
    for b in boxes:
        b["color"] = [c * 0.55 + 0.4 for c in b["color"]]
    boxes.append(v2.box_json("hitbox", frm, to, "hitbox"))
    v2.run_blender(boxes, OUT / "hitbox", [{"name": "hitbox_front", "mode": "flat", "camera": "ortho_front"},
                                           {"name": "hitbox_side", "mode": "flat", "camera": "ortho_side"}])
    a, b = (Image.open(OUT / "hitbox" / f"hitbox_{v}.png") for v in ("front", "side"))
    both = Image.new("RGB", (a.width + b.width + 10, a.height), sheet.BG)
    both.paste(a, (0, 0))
    both.paste(b, (a.width + 10, 0))
    both.save(OUT / "hitbox.png")
    # the key poses
    for key in POSES:
        m = pose(rig(), key)
        finish(m)
        render_glowing(decals(m), OUT / "poses" / key, POSE_VIEWS)
        lo, hi = m.bounds()
        feet = [c.corners()[:, 1].min() for c in m.cubes if c.name.startswith("sabaton")]
        print(key, "size", [round(float(v) / 16, 2) for v in hi - lo], "feet low", [round(float(f), 1) for f in feet],
              "lowest", round(float(lo[1]), 1))
    keys = list(POSES)
    for i, chunk in enumerate((keys[:3], keys[3:])):
        sheet.compare_sheet(OUT / "poses", [(k, POSES[k][0].split(":")[0]) for k in chunk], OUT / f"poses_{i + 1}.png",
                            heading="Hollow Warlord - key poses from the rig (" + ", ".join(chunk) + ")",
                            views=("flat_34", "sil_side"))
    (OUT / "parts.md").write_text("# Hollow Warlord rig parts (session 2)\n\nGenerated by `tools/art/bosses/headsman_s2.py`."
                                  " Cube sizes are whole texels.\n\n" + parts_list(bind) + "\n", encoding="utf-8")
    print(json.dumps(stats))


if __name__ == "__main__":
    main(sys.argv[1:])
