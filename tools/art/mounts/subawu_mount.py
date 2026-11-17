"""The Subawu mount: a kei truck, as a model worn by a pig (MythicMobs + BetterModel, nothing else), the same way the
Volcano Toad is made (tools/art/mounts/volcano_toad_mount.py).

Built from the hand-made model (tools/art/mounts/source/subawu.bbmodel, Blockbench 5, its own 64x64 texture):
- moved so the truck's middle sits on the mob (it was built 9 units to the side and 21.5 behind the origin): the
  truck turns about its own centre,
- its two mesh bones (a click box and a seat, which BetterModel can't use) are replaced by an ob_hitbox cube around the
  truck, the p_seat bone in the driver's seat (on the right, as in the real truck), p_seat2 beside it and p_seat3-6
  in the bed (the passengers),
- everything but the wheels rides on a chassis bone (the engine shakes it); a steering wheel in front of the driver,
- its own clips replace the file's walk: park (the engine idling), drive (the wheels rolling at the driving speed and
  the chassis rumbling). Neither has a BetterModel built-in name (idle, walk): the skills play both.

Writes mounts/subawu/BetterModel/models/subawu_mount.bbmodel and the pack zip dist/subawu-mount.zip (mounts/subawu/
as it lands in plugins/).

Run from the repository root: python tools/art/mounts/subawu_mount.py
"""
import base64
import copy
import io
import json
import math
import sys
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import _uuid  # noqa: E402

MODEL_ID = "subawu_mount"
SOURCE = ROOT / "tools/art/mounts/source/subawu.bbmodel"
PACK = ROOT / "mounts/subawu"
OUT_MODEL = PACK / "BetterModel/models" / f"{MODEL_ID}.bbmodel"
ZIP = ROOT / "dist/subawu-mount.zip"

SHIFT = (9.0, 0.0, -21.5)              # the truck's middle onto the origin (it spans x -27..9, z -12..55)
RENAME = {"group": "truck", "group4": "cab_shell", "tyre": "wheels", "group2": "wheels_front", "group3": "wheels_rear"}
DROP = ("hitbox", "mount")             # the source's mesh bones
CLICK_BOX = ((-18, 0, -34), (18, 38, 34))
SEAT = (7.0, 14.0, -13.0)              # the driver, right half of the cab, well forward: head and shoulders show
                                       # through the windows and the eye looks out under the roof's front edge
SEAT_BOX = ((3, 13.9, -16), (11, 14, -10))
# the passengers: one beside the driver (the left half of the cab), four sitting on the floor of the bed in two rows
# (the floor is at y 11, its walls reach 16.5: their upper bodies show). Each is a p_seatN bone with a seat pad; the
# rider sits on top of the pad.
BED_FLOOR = 11.0
PASSENGERS = {
    "seat2": (-SEAT[0], SEAT[1], SEAT[2]),
    "seat3": (SEAT[0], BED_FLOOR, 9.0),
    "seat4": (-SEAT[0], BED_FLOOR, 9.0),
    "seat5": (SEAT[0], BED_FLOOR, 23.0),
    "seat6": (-SEAT[0], BED_FLOOR, 23.0),
}
STEERING = ((4.75, 20.5, -27.0), (9.25, 25.0, -26.5))  # a wheel on its column in front of the driver
STEERING_TILT = -35.0
DARK_UV = [1, 49, 15, 63]              # the tyres' dark rubber on the texture
GLASS_ALPHA = 30                       # the windows (the source's 92 tinted the driver's view)

# the driving speed: ridden, the pig covers 12 blocks a second per point of MovementSpeed (0.35 was 4.2); 0.75 is 9
# blocks a second, a car next to a sprinting player's 5.6
SPEED = 9.0
WHEEL_RADIUS = 5 / 16                  # blocks (the wheels are 10 units tall)
ROLL = 2 * math.pi * WHEEL_RADIUS / SPEED   # seconds a wheel takes to turn once


def load():
    m = json.loads(SOURCE.read_text(encoding="utf-8"))
    m["reference_images"] = []
    return m


def shifted(v):
    return [round(v[i] + SHIFT[i], 4) for i in range(3)]


def outliner_v4(m):
    """Blockbench 5 keeps bones in `groups` and only uuids in the outliner; BetterModel reads the 4.x outliner, where
    every node carries its bone's name, origin and turn. Meshes and the dropped bones go."""
    groups = {g["uuid"]: g for g in m["groups"]}
    elements = {e["uuid"]: e for e in m["elements"]}
    kept_elements, kept_groups = [], []

    def node(n):
        if isinstance(n, str):
            e = elements[n]
            if e.get("type") == "mesh":
                return None
            kept_elements.append(e)
            return n
        g = groups[n["uuid"]]
        if g["name"] in DROP:
            return None
        g = dict(g)
        g["name"] = RENAME.get(g["name"], g["name"])
        kept_groups.append(g)
        out = {k: v for k, v in g.items() if k != "children"}
        out["children"] = [c for c in (node(c) for c in n["children"]) if c is not None]
        return out
    outliner = [c for c in (node(n) for n in m["outliner"]) if c is not None]
    return outliner, kept_elements, kept_groups


def take(nodes, name):
    """Takes the bone `name` out of the tree (wherever it is) and returns it."""
    for n in nodes:
        if isinstance(n, dict):
            if n["name"] == name:
                nodes.remove(n)
                return n
            found = take(n["children"], name)
            if found:
                return found
    return None


def bone(name, origin, children):
    uid = _uuid(f"{MODEL_ID}/group/{name}")
    g = {"name": name, "origin": list(origin), "rotation": [0, 0, 0], "color": 0, "uuid": uid, "export": True,
         "mirror_uv": False, "isOpen": False, "locked": False, "visibility": True, "autouv": 0}
    return g, {**g, "children": children}


def cube(template, name, frm, to, origin, rotation=(0, 0, 0), uv=None):
    e = copy.deepcopy(template)
    e.update(name=name, uuid=_uuid(f"{MODEL_ID}/{name}"), rotation=list(rotation), box_uv=False,
             **{"from": list(frm), "to": list(to), "origin": list(origin)})
    e.pop("uv_offset", None)
    if uv:
        e["faces"] = {f: {"uv": list(uv), "texture": 0} for f in ("north", "east", "south", "west", "up", "down")}
    return e


def build_model():
    m = load()
    outliner, elements, groups = outliner_v4(m)
    for e in elements:
        e["from"], e["to"], e["origin"] = shifted(e["from"]), shifted(e["to"]), shifted(e["origin"])

    def move(nodes):
        for n in nodes:
            if isinstance(n, dict):
                n["origin"] = shifted(n["origin"])
                move(n["children"])
    move(outliner)
    for g in groups:
        g["origin"] = shifted(g["origin"])
    template = next(e for e in elements if e.get("type", "cube") == "cube")
    # the steering wheel, on the chassis
    wheel = cube(template, "steering_wheel", STEERING[0], STEERING[1],
                 [(STEERING[0][i] + STEERING[1][i]) / 2 for i in range(3)], (STEERING_TILT, 0, 0), DARK_UV)
    column = cube(template, "steering_column", (6.6, 17.5, -29.5), (7.4, 22.5, -26.9), (7.0, 20.0, -28.2),
                  (STEERING_TILT, 0, 0), DARK_UV)
    elements += [wheel, column]
    # everything but the wheels on a chassis bone the engine can shake
    wheels = take(outliner, "wheels")
    chassis_children = outliner + [wheel["uuid"], column["uuid"]]
    chassis_group, chassis = bone("chassis", (0, 0, 0), chassis_children)
    hit = cube(template, "hitbox", CLICK_BOX[0], CLICK_BOX[1], (0, 0, 0))
    hit_group, hit_node = bone("ob_hitbox", (0, 0, 0), [hit["uuid"]])
    pad = cube(template, "seat", SEAT_BOX[0], SEAT_BOX[1], SEAT)
    seat_group, seat_node = bone("p_seat", SEAT, [pad["uuid"]])
    pads, seat_groups, seat_nodes = [], [], []
    for name, (x, y, z) in PASSENGERS.items():
        p = cube(template, name, (x - 4, y - 0.1, z - 3), (x + 4, y, z + 3), (x, y, z))
        g, n = bone(f"p_{name}", (x, y, z), [p["uuid"]])
        pads.append(p); seat_groups.append(g); seat_nodes.append(n)
    for e in [hit, pad] + pads:
        e["visibility"] = False
    elements += [hit, pad] + pads
    m["outliner"] = [chassis, wheels, hit_node, seat_node] + seat_nodes
    m["groups"] = groups + [chassis_group, hit_group, seat_group] + seat_groups
    m["elements"] = elements
    m["meta"] = {"format_version": "4.10", "model_format": "free", "box_uv": False}
    m["resolution"] = {"width": 64, "height": 64}          # the texture's own UV space (the source said 256)
    m["animations"] = animations({g["name"]: g["uuid"] for g in m["groups"]})
    m["name"] = MODEL_ID
    m["model_identifier"] = MODEL_ID
    clear_glass(m["textures"][0])
    for tex in m["textures"]:
        tex["name"] = f"{MODEL_ID}.png"
        tex["relative_path"] = f"{MODEL_ID}.png"
    return m


def clear_glass(tex):
    """The see-through texels (the windows) made clearer."""
    head, data = tex["source"].split(",", 1)
    img = Image.open(io.BytesIO(base64.b64decode(data))).convert("RGBA")
    img.putdata([(r, g, b, GLASS_ALPHA if 0 < a < 255 else a) for r, g, b, a in img.getdata()])
    out = io.BytesIO()
    img.save(out, "PNG")
    tex["source"] = head + "," + base64.b64encode(out.getvalue()).decode()


# ---- clips -----------------------------------------------------------------------------------------------------------

def key(clip, bone_name, channel, t, v, interp="linear"):
    return {"channel": channel, "data_points": [{"x": str(v[0]), "y": str(v[1]), "z": str(v[2])}], "time": round(t, 4),
            "color": -1, "interpolation": interp, "uuid": _uuid(f"{MODEL_ID}/{clip}/{bone_name}/{channel}/{t}")}


def clip(name, length, loop, tracks, uuids):
    animators = {uuids[b]: {"name": b, "type": "bone", "keyframes": frames} for b, frames in tracks.items()}
    return {"uuid": _uuid(f"{MODEL_ID}/anim/{name}"), "name": name, "loop": loop, "override": name != "park",
            "length": round(length, 4), "snapping": 20, "selected": False, "anim_time_update": "", "blend_weight": "",
            "start_delay": "", "loop_delay": "", "animators": animators}


def animations(uuids):
    """park: the engine idling, a quick shiver of the chassis. drive: every wheel turning once per ROLL seconds (the
    wheels roll on the ground, not slide over it, at the driving speed) and the chassis rumbling."""
    shiver = [key("park", "chassis", "position", t, (0, y, 0)) for t, y in ((0, 0), (0.05, 0.12), (0.1, 0))]
    park = clip("park", 0.1, "loop", {"chassis": shiver}, uuids)
    steps = 8
    spin = lambda b: [key("drive", b, "rotation", ROLL * i / steps, (-360 * i / steps, 0, 0))   # noqa: E731
                      for i in range(steps + 1)]
    rumble = [key("drive", "chassis", "position", t, (0, y, 0), "catmullrom")
              for t, y in ((0, 0), (ROLL / 4, 0.25), (ROLL / 2, -0.1), (ROLL * 3 / 4, 0.2), (ROLL, 0))]
    drive = clip("drive", ROLL, "loop", {"wheels_front": spin("wheels_front"), "wheels_rear": spin("wheels_rear"),
                                         "chassis": rumble}, uuids)
    return [park, drive]


def pack():
    ZIP.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(PACK.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(PACK).as_posix())


def main():
    model = build_model()
    OUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    OUT_MODEL.write_text(json.dumps(model, indent=1) + "\n", encoding="utf-8")
    pack()
    print(json.dumps({"model": str(OUT_MODEL.relative_to(ROOT)), "elements": len(model["elements"]),
                      "bones": [g["name"] for g in model["groups"]], "clips": [a["name"] for a in model["animations"]],
                      "roll_s": round(ROLL, 3), "seat_blocks": [round(v / 16, 3) for v in SEAT]}))


if __name__ == "__main__":
    main()
