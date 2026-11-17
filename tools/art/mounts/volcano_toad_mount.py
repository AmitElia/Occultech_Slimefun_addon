"""The Volcano Toad mount: the Elder of Ash, smaller, as a model worn by a pig (MythicMobs + BetterModel, nothing else).

The pig (VOLCANO_TOAD_MOUNT) wears volcano_toad_mount itself, the way the boss's carrier wears his: BetterModel hides
the pig and turns the model with its body, from the pig's own AI when nobody rides and from the rider's keys when
someone does (a camel can't carry it: BetterModel draws the model collapsed on one). The rider sits on the model's
seat bone (p_seat, BetterModel's mountmodel) and BetterModel's walk controller drives the pig.

Built from the shipped boss model (src/main/models/occultech_mire_monarch.bbmodel: geometry, bones) on the dormant
atlas (the orange lava painted in, no tint needed):
- the tongue and the blown-top cone are dropped, the hitbox bone is cut down to the body,
- everything is shrunk to SIZE times the boss; a saddle on the shoulder ridge with the seat bone on it,
- stand is the boss's idle; waddle (a frog's walk at riding pace, its palms and feet placed on the ground), leap and
  land are the mount's, made with the boss's pose code (ash_s7). No clip has a BetterModel built-in name (idle,
  walk): BetterModel plays those itself and restarts the waddle each time its walking test flickers under a rider,
  so the skills play every clip.

Writes mounts/volcano_toad/BetterModel/models/volcano_toad_mount.bbmodel, previews in
docs/art/mounts/volcano_toad/ and the pack zip dist/volcano-toad-mount.zip (mounts/volcano_toad/ as it lands in plugins/).

Run from the repository root: python tools/art/mounts/volcano_toad_mount.py
"""
import base64
import copy
import io
import json
import math
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Cube, _uuid, pivot_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosskit.checks import flicker_pairs  # noqa: E402
from bosses import ash_s2 as s2, ash_s3 as s3, ash_s6 as s6, ash_s7 as s7  # noqa: E402

MODEL_ID = "volcano_toad_mount"
BOSS = ROOT / "src/main/models/occultech_mire_monarch.bbmodel"
PACK = ROOT / "mounts/volcano_toad"
OUT_MODEL = PACK / "BetterModel/models" / f"{MODEL_ID}.bbmodel"
PREVIEW = ROOT / "docs/art/mounts/volcano_toad"
ZIP = ROOT / "dist/volcano-toad-mount.zip"

SIZE = 0.58                    # the toad against the boss (the boss is ~9 blocks across; this one ~5.3)
BAKE = SIZE                    # what the geometry is shrunk by in the file (the camel stays at scale 1)
SEAT = (0.0, 62.0, -15.0)      # boss units: the saddle's seat, level, just behind the crest of the shoulder ridge
DROP = ("tongue", "cone_blown")
HITBOXES = ("ob_hitbox", "p_seat")                        # invisible boxes: never drawn, never flicker-checked
CLICK_BOX = ((-60, 0, -63), (60, 56, 40))                 # ob_hitbox (boss units), cut to the body, under the rider
SEAT_BOX = ((-4, 61.9, -19), (4, 62, -11))                # p_seat: a thin pad whose top is the seat
CLIPS = ("stand", "waddle", "leap", "land")               # all played by the skills (none has a built-in name)

# The saddle (boss units, on the body bone). Behind the head the neck is a sharp ridge (the neck_slope slab, turned
# -46.85 about x): up from the skull (y 38 at z -34) to a crest (y 59.5 at z -18.7), down to a dip (y 52 at z -10)
# just in front of the volcano. The saddle sits astride the crest like a horse's: a level seat on top, its base
# reaching down both faces, the cantle in the dip; the rider's legs, which point almost straight ahead when riding,
# clear the ridge's front face and the skull. The blanket lies on both faces at the slab's own angle.
# Faces that touch another cube start just inside it, so no two faces share a plane (they would flicker).
RIDGE = ((-46.8476102659946, 0.0, 0.0), (0.0, 48.10364677328798, -21.877223224840513))   # neck_slope's turn, pivot
SADDLE = [
    # name, from, to, material, (rotation, origin) or None for a level cube
    ("saddle_blanket_front", (-13, 54.0, -30), (13, 55.0, -11.2), "cloth", RIDGE),     # on the ridge's front face
    ("saddle_blanket_back", (-13, 48, -11.0), (13, 54.95, -9.9), "cloth", RIDGE),      # on its back face
    ("saddle_base", (-10, 51, -21), (10, 61, -10), "leather", None),
    ("saddle_seat", (-9, 60.9, -19.5), (9, 62, -10.5), "seat", None),
    ("saddle_cantle", (-9.5, 60.9, -11), (9.5, 66, -8.5), "leather", None),
    ("saddle_cantle_trim", (-9.5, 65.9, -11), (9.5, 67, -8.5), "gold", None),
    ("saddle_pommel", (-1.2, 60.9, -21.5), (1.2, 64.5, -19), "gold", None),
]
PAINT = {"leather": (112, 70, 40), "seat": (74, 44, 28), "gold": (214, 170, 64), "cloth": (140, 38, 26),
         "rider": (70, 110, 170)}


def seat_final():
    """The seat in final model units (16 per block, -z ahead), where the rider's hips rest."""
    return tuple(v * SIZE for v in SEAT)


# ---- clips -----------------------------------------------------------------------------------------------------------

# The waddle's feet are placed, not swung: every tick of the stride the body is posed, then each leg is turned until its
# palm (or hind foot) lies where it should. A planted palm slides back under the body at the riding speed, so on the
# ground it stays put; a lifted one swings forward to where the next step lands.
GAIT_SPEED = 3.6 * 16 / SIZE         # boss units a second: the ridden speed measured on a server (0.18 blocks a tick)
GAIT_LENGTH = 0.6                    # one stride (12 ticks): each pair down for half of it, up for the other half
GAIT_LIFT = {"hand": 7.0, "foot": 5.0}
GAIT_BACK = {"hand": 5.0, "foot": 0.0}   # the palms step a little behind where they rest: the arms can't reach far ahead
# each leg's joints, with how far each may turn about x, y, z (degrees): elbows and knees barely twist
LIMBS = {"hand": (("arm", (60, 25, 40)), ("forearm", (60, 10, 50)), ("hand", (60, 30, 40))),
         "foot": (("thigh", (70, 20, 30)), ("shin", (60, 10, 15)), ("foot", (60, 20, 20)))}
# diagonal pairs: the left palm (and the right foot) are down for the stride's first half, the left foot (and the
# right palm) for the second. Only the left legs are solved; the right ones are their mirror half a stride on.
PHASE = {"hand_left": 0.0, "foot_left": 0.5}


def posed(sp):
    """ash_s7.posed, plus "ik": bone turns solved by placed_limb, set after the pose."""
    key = json.dumps(sp, sort_keys=True)
    if key not in s7._POSED:
        m = s2.rig("p", decals=False)
        s2.pose(m, {k: v for k, v in sp.items() if k != "ik"})
        for bone, r in sp.get("ik", {}).items():
            s2.group(m, bone).rotation = list(r)
        s7._POSED[key] = {g.name: list(g.rotation) for g in m.groups}
    return s7._POSED[key]


def end_points(m, end):
    return np.vstack([c.corners() for c in s2.cubes_in(m, s2.group(m, end))])


def placed_limb(body, end, target):
    """The joint turns (within their limits, as little as will do) that put a leg's end, all its cubes' corners, on
    `target`, the body posed as `body`."""
    from scipy.optimize import least_squares
    m = s2.rig("p", decals=False)
    s2.pose(m, {**body, "plant": False})
    kind, side = end.split("_")
    joints = [(s2.group(m, f"{bone}_{side}"), limit) for bone, limit in LIMBS[kind]]
    reach = np.array([v for _, limit in joints for v in limit], float)

    def residual(x):
        for i, (g, _) in enumerate(joints):
            g.rotation = list(x[3 * i:3 * i + 3])
        return np.concatenate([(end_points(m, end) - target).ravel(), 0.05 * x])
    x = least_squares(residual, np.zeros(len(reach)), bounds=(-reach, reach), diff_step=1e-3).x
    return {g.name: [round(float(v), 3) for v in x[3 * i:3 * i + 3]] for i, (g, _) in enumerate(joints)}


def mirrored(turns):
    """The left legs' turns as the right legs' (mirrored across the toad's middle)."""
    return {bone.replace("_left", "_right"): [r[0], -r[1], -r[2]] for bone, r in turns.items()}


def waddle(ready, spec):
    """A frog's walk at riding pace: diagonal pairs (a front palm with the other side's hind foot), every planted
    palm and foot still on the ground while the body passes over it; the body rocks and swings over the planted pair,
    the head turning back against it."""
    rest = s2.rig("p", decals=False)
    s2.pose(rest, s7.REST)
    home = {end: end_points(rest, end) for end in PHASE}
    stride = GAIT_SPEED * GAIT_LENGTH / 2                 # how far a planted palm travels back under the body
    ticks = round(GAIT_LENGTH * 20)
    bodies, left = [], []
    for tick in range(ticks):
        f = tick / ticks
        wave = math.sin(2 * math.pi * f)                  # + while the left palm and right foot are down
        body = spec(ready, y=ready["y"] - 1.0 * math.cos(4 * math.pi * f), roll=3.5 * wave, yaw=-4 * wave,
                    turn=6 * wave, head=ready["head"] + 1.5 * math.cos(4 * math.pi * f), plant=False)
        turns = {}
        for end, phase in PHASE.items():
            p = (f - phase) % 1.0
            if p < 0.5:                                   # down: sliding back under the body as it walks on
                dz, lift = stride * (p / 0.5 - 0.5), 0.0
            else:                                         # up: lifted and swung forward to the next step
                s = (p - 0.5) / 0.5
                dz, lift = stride * 0.5 * math.cos(math.pi * s), GAIT_LIFT[end.split("_")[0]] * math.sin(math.pi * s)
            dz += GAIT_BACK[end.split("_")[0]]
            turns.update(placed_limb(body, end, home[end] + np.array([0.0, lift, dz])))
        bodies.append(body)
        left.append(turns)
    keys = [(round(tick / 20, 3), {**bodies[tick], "ik": {**left[tick], **mirrored(left[(tick + ticks // 2) % ticks])}})
            for tick in range(ticks)]
    keys.append((GAIT_LENGTH, keys[0][1]))
    return GAIT_LENGTH, "loop", keys


def clips():
    """The boss's idle (it reads well on the mount; named stand, so BetterModel leaves it to the skills); waddle, leap
    and land are the mount's own. leap stretches him out the moment he leaves the ground and brings the legs forward
    to land; land squashes him and lets him rise."""
    base = s7.clips()
    rest, spec, P = s7.REST, s7.spec, s7.P
    ready = spec(rest, y=3, head=3)
    flight = spec(P["leap"], y=0, tilt=12)
    tuck = spec(P["leap"], y=0, tilt=-4, head=-2, arm=(-22, 0, 6), thigh=(-40, 0, 0), foot=(30, 0, 0))
    slam = spec(P["slam"], y=-5, jaw=-3)
    return {
        "stand": base["idle"],
        "waddle": waddle(ready, spec),
        "leap": (0.7, "hold", [(0, ready), (0.1, flight), (0.5, tuck), (0.7, tuck)]),
        "land": (0.6, "once", [(0, slam), (0.12, spec(slam, y=-7)), (0.35, spec(rest, y=-1)), (0.6, rest)]),
    }


def animations():
    s3.setup()
    s7.posed = posed                    # tracks() poses through it: the waddle's placed limbs
    rest = s2.rig("rest", decals=False)
    rest_rot = {g.name: list(g.rotation) for g in rest.groups}
    clip_set = {name: (c[0], c[1], s7.tracks(c, rest_rot)) for name, c in clips().items()}
    for _, _, bones in clip_set.values():
        for bone in [b for b in bones if b in DROP]:
            del bones[bone]
        for channels in bones.values():
            if "position" in channels:
                channels["position"] = [(t, tuple(v * BAKE for v in p), i) for t, p, i in channels["position"]]
    return clip_set, s7.blockbench_animations(s3.MODEL_ID, clip_set)


# ---- the model -------------------------------------------------------------------------------------------------------

def bake(p):
    return [round(p[i] * BAKE, 4) for i in range(3)]


FACE_DIMS = {"north": (0, 1), "south": (0, 1), "east": (2, 1), "west": (2, 1), "up": (0, 2), "down": (0, 2)}


def free_texels(m):
    """Atlas texels no face uses (the atlas is one texel per boss unit)."""
    used = np.zeros((m["resolution"]["height"], m["resolution"]["width"]), bool)
    for e in m["elements"]:
        for f in e["faces"].values():
            if f.get("texture") is None or "uv" not in f:
                continue
            u1, v1, u2, v2 = f["uv"]
            used[int(min(v1, v2)):int(np.ceil(max(v1, v2))), int(min(u1, u2)):int(np.ceil(max(u1, u2)))] = True
    return ~used


def place(free, w, h):
    """The first free w x h rect (with a texel of margin), taken out of the free mask."""
    for y in range(1, free.shape[0] - h - 1):
        for x in range(1, free.shape[1] - w - 1):
            if free[y - 1:y + h + 1, x - 1:x + w + 1].all():
                free[y - 1:y + h + 1, x - 1:x + w + 1] = False
                return x, y
    raise SystemExit("no room left in the atlas for the saddle")


def paint(px, x, y, w, h, mat, seed):
    """Vanilla-style flat paint: a base colour, calm 2x2 noise, darker edges; gold gets a lit top row, the blanket a
    gold border."""
    rng = np.random.default_rng(seed)
    base = np.array(PAINT[mat], float)
    for j in range(h):
        for i in range(w):
            c = base * (1 + rng.choice((-0.06, 0, 0, 0.05)) if (i // 2 + j // 2) % 3 else 1.0)
            edge = i in (0, w - 1) or j in (0, h - 1)
            if mat == "cloth" and (i < 2 or i >= w - 2 or j < 2 or j >= h - 2) and min(w, h) > 4:
                c = np.array((200, 150, 60), float)
            elif mat == "gold":
                c = np.array((245, 215, 120), float) if j == 0 else (np.array((150, 110, 40), float) if edge else c)
            elif mat in ("leather", "seat") and edge:
                c = base * 0.72
            elif mat == "leather" and (i in (2, w - 3) or j in (2, h - 3)) and (i + j) % 2 == 0 and min(w, h) > 6:
                c = np.array((170, 130, 80), float)           # stitching
            px[y + j, x + i] = (*np.clip(c, 0, 255).astype(int), 255)


def add_saddle(m):
    """The saddle's cubes on the body bone, each face on its own freshly painted patch of the atlas."""
    tex = m["textures"][0]
    head, data = tex["source"].split(",", 1)
    img = Image.open(io.BytesIO(base64.b64decode(data))).convert("RGBA")
    px = np.array(img)
    free = free_texels(m)
    template = next(e for e in m["elements"] if e["name"] == "low")
    body = find_group(m["outliner"], "body")
    for n, (name, frm, to, mat, turn) in enumerate(SADDLE):
        rot, origin = turn or ((0.0, 0.0, 0.0), [(frm[i] + to[i]) / 2 for i in range(3)])
        size = [to[i] - frm[i] for i in range(3)]
        faces = {}
        for k, (face, (a, b)) in enumerate(FACE_DIMS.items()):
            w, h = max(1, int(np.ceil(size[a]))), max(1, int(np.ceil(size[b])))
            x, y = place(free, w, h)
            paint(px, x, y, w, h, mat, n * 10 + k)
            faces[face] = {"uv": [x, y, x + w, y + h], "texture": 0}
        e = copy.deepcopy(template)
        e.update(name=name, uuid=_uuid(f"{MODEL_ID}/{name}"), faces=faces, rotation=list(rot),
                 **{"from": list(frm), "to": list(to), "origin": list(origin)})
        m["elements"].append(e)
        body["children"].append(e["uuid"])
    out = io.BytesIO()
    Image.fromarray(px.astype(np.uint8)).save(out, "PNG")
    tex["source"] = head + "," + base64.b64encode(out.getvalue()).decode()
    return Image.fromarray(px.astype(np.uint8))


def dormant_texture(m):
    """The atlas on the dormant colours (the orange lava, as the boss's tint shows it) with the saddle painted in."""
    tex = m["textures"][0]
    head, data = tex["source"].split(",", 1)
    mine = np.array(Image.open(io.BytesIO(base64.b64decode(data))).convert("RGBA")).astype(int)
    neutral = np.array(Image.open(ATLASES / "neutral.png").convert("RGBA")).astype(int)
    atlas = np.array(Image.open(ATLASES / "dormant.png").convert("RGBA"))
    changed = np.abs(mine - neutral).sum(2) > 0
    atlas[changed] = mine[changed]
    out = io.BytesIO()
    Image.fromarray(atlas.astype(np.uint8)).save(out, "PNG")
    tex["source"] = head + "," + base64.b64encode(out.getvalue()).decode()


def add_seat(m):
    """The seat bone p_seat on the body bone (it moves with every clip): a thin pad whose top is the saddle's seat.
    BetterModel seats a mountmodel rider on top of it."""
    click = find_group(m["outliner"], "ob_hitbox")
    box = next(e for e in m["elements"] if e["uuid"] == click["children"][0])
    seat_uuid = _uuid(f"{MODEL_ID}/group/p_seat")
    group = copy.deepcopy(next(g for g in m["groups"] if g["uuid"] == click["uuid"]))
    group.update(name="p_seat", uuid=seat_uuid, origin=list(SEAT))
    m["groups"].append(group)
    pad = copy.deepcopy(box)
    pad.update(name="seat", uuid=_uuid(f"{MODEL_ID}/seat_pad"),
               **{"from": list(SEAT_BOX[0]), "to": list(SEAT_BOX[1]), "origin": list(SEAT)})
    m["elements"].append(pad)
    node = {k: v for k, v in click.items() if k != "children"}
    node.update(name="p_seat", uuid=seat_uuid, origin=list(SEAT), children=[pad["uuid"]])
    find_group(m["outliner"], "body")["children"].append(node)


def find_group(nodes, name):
    for n in nodes:
        if isinstance(n, dict):
            if n["name"] == name:
                return n
            found = find_group(n["children"], name)
            if found:
                return found
    return None


def build_model(anims):
    m = json.loads(BOSS.read_text(encoding="utf-8"))
    dropped = set()

    def prune(children):
        kept = []
        for c in children:
            if isinstance(c, dict):
                if c["name"] in DROP:
                    collect(c)
                    continue
                c["children"] = prune(c["children"])
            kept.append(c)
        return kept

    def collect(node):
        dropped.add(node["uuid"])
        for c in node["children"]:
            if isinstance(c, str):
                dropped.add(c)
            else:
                collect(c)

    m["outliner"] = prune(m["outliner"])
    m["elements"] = [e for e in m["elements"] if e["uuid"] not in dropped]
    m["groups"] = [g for g in m.get("groups", []) if g["uuid"] not in dropped]
    add_saddle(m)
    dormant_texture(m)
    box = next(e for e in m["elements"] if e["uuid"] == find_group(m["outliner"], "ob_hitbox")["children"][0])
    box["from"], box["to"] = list(CLICK_BOX[0]), list(CLICK_BOX[1])
    add_seat(m)
    for e in m["elements"]:
        e["from"], e["to"], e["origin"] = bake(e["from"]), bake(e["to"]), bake(e["origin"])
        e["inflate"] = round(e.get("inflate", 0) * BAKE, 4)

    def regroup(nodes):
        for n in nodes:
            if isinstance(n, dict):
                n["origin"] = bake(n["origin"])
                regroup(n["children"])
    regroup(m["outliner"])
    for g in m["groups"]:
        g["origin"] = bake(g["origin"])
    names = {g["uuid"]: g["name"] for g in m["groups"]}
    for a in anims:
        for uid, animator in a["animators"].items():
            if names.get(uid) != animator["name"]:
                raise SystemExit(f"animator {animator['name']} has no bone with uuid {uid}")
    for a in anims:                     # the skills' clips play over stand
        a["override"] = a["name"] != "stand"
    m["animations"] = anims
    m["name"] = MODEL_ID
    m["model_identifier"] = MODEL_ID
    for tex in m["textures"]:
        tex["name"] = f"{MODEL_ID}.png"
    return m


# ---- preview: the boss-unit model with a seated rider, posed per frame -----------------------------------------------

def preview_model():
    s3.setup()
    model = s2.build("preview", decals=False)
    s2.finish(model)
    model.cubes = [c for c in model.cubes if not set(s6.bone_names(c)) & set(DROP + HITBOXES)]
    body = next(g for g in model.groups if g.name == "body")
    for name, frm, to, mat, turn in SADDLE:
        rot, origin = turn or ((0, 0, 0), None)
        model.cubes.append(Cube(name, list(frm), list(to), mat, rot, origin, 0, body))
    clash = flicker_pairs(model.cubes)
    if clash:
        raise SystemExit(f"{MODEL_ID}: faces that would flicker in game: {clash[:5]}")
    base = next(g for g in model.groups if g.name == "base")
    # the rider in vanilla's riding pose (HumanoidModel: legs turned 81 degrees forward and 18 out), player pixels
    # at the player model's 0.9375 scale; the seat is 0.6 above the rider's feet, so the hips are 1.6 px above it
    k = 0.9375 / SIZE                              # one rider pixel in boss units
    sx, sy, sz = SEAT
    hip = 1.6 / 0.9375

    def box(name, lo, hi):
        model.cubes.append(Cube(name, [sx + lo[0] * k, sy + lo[1] * k, sz + lo[2] * k],
                                [sx + hi[0] * k, sy + hi[1] * k, sz + hi[2] * k], "rider", (0, 0, 0), None, 0, base))
    box("rider_torso", (-4, hip, -2), (4, hip + 12, 2))
    box("rider_head", (-4, hip + 12, -4), (4, hip + 20, 4))
    box("rider_arm_l", (-8, hip + 1, -3), (-4, hip + 12, 1))
    box("rider_arm_r", (4, hip + 1, -3), (8, hip + 12, 1))
    for side, x0 in (("l", -1), ("r", 1)):                     # each leg a few boxes stepping out 18 degrees
        for seg in range(3):
            z0, z1 = 2 - seg * 4.7, 2 - (seg + 1) * 4.7
            out = x0 * (0.2 + 4.7 * (seg + 0.5) * 0.325)
            drop = (seg + 0.5) * 4.7 * 0.156
            box(f"rider_leg_{side}{seg}", (out - 2, hip - 2 - drop, z1), (out + 2, hip + 2 - drop, z0))
    return model


def previews(clip_set):
    if PREVIEW.exists():
        shutil.rmtree(PREVIEW)
    (PREVIEW / "gifs").mkdir(parents=True)
    from bosses import ash_s4 as s4
    for mat, colour in PAINT.items():
        s4.ZONES.setdefault(mat, colour)
    model = preview_model()
    for name, (length, loop, bones) in clip_set.items():
        unbaked = {b: {ch: ([(t, tuple(v / BAKE for v in p), i) for t, p, i in keys] if ch == "position" else keys)
                       for ch, keys in chans.items()} for b, chans in bones.items()}
        frames = [s7.frame(model, unbaked, t, yaw=-60, pitch=10, size=(460, 400), scale=2.0)
                  for t in np.arange(0, length + 1e-6, 1 / 15)]
        frames[0].save(PREVIEW / "gifs" / f"{name}.gif", save_all=True, append_images=frames[1:], duration=66, loop=0)


# ---- textured renders: the shipped file itself in Blender, with a rider on the seat ---------------------------------

BLENDER = Path(r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe")
ATLASES = ROOT / "docs/art/bosses/elder_of_ash/overhaul/s6_variants/atlases"
RENDER_VIEWS = [   # Blender coordinates: blocks, z up, the toad facing +y
    {"name": "whole_side", "location": (14, 0.6, 2.6), "target": (0, 0.6, 2.0), "scale": 6.6, "player": False},
    {"name": "whole_three_quarter", "location": (9, 11, 7), "target": (0, 0.3, 1.7), "scale": 7.2, "player": False},
    {"name": "seat_right", "location": (8, 0.5, 2.6), "target": (0, 0.5, 2.6), "scale": 3.2, "player": False},
    {"name": "seat_left", "location": (-8, 0.5, 2.6), "target": (0, 0.5, 2.6), "scale": 3.2, "player": False},
    {"name": "seat_front", "location": (4.5, 7, 6.0), "target": (0, 0.5, 2.4), "scale": 3.4, "player": False},
    {"name": "seat_back", "location": (-4.5, -6, 6.5), "target": (0, 0.5, 2.6), "scale": 3.8, "player": False},
]


def world_boxes(m):
    """Every element's 8 corners in final units (16 per block), bones at rest."""
    mats, owner = {}, {}

    def walk(nodes, parent):
        for n in nodes:
            if isinstance(n, str):
                owner[n] = parent
            else:
                here = parent @ pivot_matrix(n["origin"], n.get("rotation", (0, 0, 0)))
                mats[n["uuid"]] = here
                walk(n["children"], here)
    walk(m["outliner"], np.eye(4))
    names, hidden = {}, set()

    def tag(nodes, glow, hide):
        for n in nodes:
            if isinstance(n, dict):
                tag(n["children"], glow or n["name"].startswith("glow_"), hide or n["name"] in HITBOXES)
            else:
                names[n] = glow
                if hide:
                    hidden.add(n)
    tag(m["outliner"], False, False)
    boxes = []
    for e in m["elements"]:
        if e["uuid"] not in owner or e["uuid"] in hidden:
            continue
        lo, hi = np.array(e["from"]), np.array(e["to"])
        pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
        w = (owner[e["uuid"]] @ pivot_matrix(e["origin"], e["rotation"]) @ pts)[:3].T
        boxes.append({"corners": w.tolist(), "from": e["from"], "to": e["to"], "glow": names[e["uuid"]],
                      "uv": e["faces"]})
    return boxes


def rider_sprites():
    """The rider as plain boxes in final units: vanilla riding pose, 0.9375 player scale, hips 1.6 px over the seat."""
    sx, sy, sz = seat_final()
    k, hip = 0.9375, 1.6 / 0.9375
    parts = [((-4, hip, -2), (4, hip + 12, 2)), ((-4, hip + 12, -4), (4, hip + 20, 4)),
             ((-8, hip + 1, -3), (-4, hip + 12, 1)), ((4, hip + 1, -3), (8, hip + 12, 1))]
    for x0 in (-1, 1):
        for seg in range(3):
            z0, z1 = 2 - seg * 4.7, 2 - (seg + 1) * 4.7
            out = x0 * (0.2 + 4.7 * (seg + 0.5) * 0.325)
            drop = (seg + 0.5) * 4.7 * 0.156
            parts.append(((out - 2, hip - 2 - drop, z1), (out + 2, hip + 2 - drop, z0)))
    sprites = []
    for lo, hi in parts:
        a = [sx + lo[0] * k, sy + lo[1] * k, sz + lo[2] * k]
        b = [sx + hi[0] * k, sy + hi[1] * k, sz + hi[2] * k]
        corners = [[x, y, z] for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
        sprites.append({"corners": corners, "color": (0.22, 0.39, 0.62)})
    return sprites


def render_textured(m):
    """Renders the shipped model (its own atlas: dormant colours and the saddle) with a rider on the seat."""
    out = PREVIEW / "textured"
    out.mkdir(parents=True, exist_ok=True)
    atlas = np.array(Image.open(io.BytesIO(base64.b64decode(m["textures"][0]["source"].split(",", 1)[1])))
                     .convert("RGBA"))
    tex = out / "atlas.png"
    Image.fromarray(atlas.astype(np.uint8)).save(tex)
    job = out / "job.json"
    job.write_text(json.dumps({"texture": tex.as_posix(), "out": out.as_posix(), "boxes": world_boxes(m),
                               "fx": rider_sprites(), "views": RENDER_VIEWS}), encoding="utf-8")
    r = subprocess.run([str(BLENDER), "-b", "--factory-startup", "--python",
                        str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job)],
                       capture_output=True, text=True)
    if r.returncode or "TEXTURED_RENDER_DONE" not in r.stdout:
        raise SystemExit(r.stdout[-3000:] + r.stderr[-3000:])
    job.unlink()
    tex.unlink()
    tiles = [("whole_side", "side"), ("whole_three_quarter", "three-quarter"), ("seat_right", "seat, from the right"),
             ("seat_left", "seat, from the left"), ("seat_front", "seat, from the front"),
             ("seat_back", "seat, from behind")]
    tw, th, pad, top = 600, 450, 10, 56
    img = Image.new("RGB", (pad + 2 * (tw + pad), top + 3 * (th + 30 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Volcano Toad mount - the shipped model, saddled, with a rider (blue) on the seat bone",
            font=sheet._font(22), fill=sheet.INK)
    for n, (name, label) in enumerate(tiles):
        x, y = pad + (n % 2) * (tw + pad), top + (n // 2) * (th + 30 + pad)
        img.paste(sheet._tile(out / f"{name}.png", tw, th), (x, y))
        dr.text((x + 4, y + th + 4), label, font=sheet._font(17), fill=sheet.DIM)
    img.save(PREVIEW / "mount_textured.png")


# ---- the zip ---------------------------------------------------------------------------------------------------------

def pack():
    ZIP.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(PACK.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(PACK).as_posix())


def main():
    clip_set, anims = animations()
    model = build_model(anims)
    previews(copy.deepcopy(clip_set))
    render_textured(model)
    OUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    OUT_MODEL.write_text(json.dumps(model, indent=1) + "\n", encoding="utf-8")
    pack()
    print(json.dumps({"model": str(OUT_MODEL.relative_to(ROOT)), "elements": len(model["elements"]),
                      "bones": len(model["groups"]), "clips": [a["name"] for a in anims],
                      "seat_blocks": [round(v / 16, 3) for v in seat_final()],
                      "zip": str(ZIP.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
