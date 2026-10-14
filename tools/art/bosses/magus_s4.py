"""The Mirrored Magus redesign, session 4: UV and material blocking.

On top of the session 3 rig, this session:
- maps every visible face at one texel per model unit (16 per block, the vanilla density) into one atlas, with a
  1-pixel border on each island against seams;
- shares texture space where a left part and its right twin are the same size and the same material (his legs, shoes,
  knees, hands, fingers, the hat's links); the coat and sleeves are split black and white by side, so those don't;
- leaves out faces buried inside another cube of the same bone;
- fills each material zone with one flat colour: the scary harlequin's black, bone white and blood crimson, tarnished
  gold, the illager's grey skin, the porcelain mask with its dark sockets, dark plum legs (their diamonds are painted
  next), and the crystal bow in the tier's cyan, drawn full-bright with the glint in his sockets;
- renders him in colour and in grey (the value check) and lists every zone's value;
- updates the in-game review rig (`occultech_mirrored_magus_rig`).

Session 5 paints over this atlas: the harlequin diamonds, the mask's grin and cracks. Run from the repository root:
python tools/art/bosses/magus_s4.py
"""
import base64
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, _uuid, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import brood_s4 as b4, magus_s2 as s2, magus_s3 as s3, volley_crone_s3 as v3, \
    volley_crone_s4 as v4  # noqa: E402

OUT = ROOT / "docs/art/bosses/mirrored_magus/overhaul/s4_uv"
SIZE = 256
ATLAS = "occultech_mirrored_magus.png"

ZONES = {
    "black": (24, 20, 28),
    "white": (206, 198, 180),        # bone white, a step under the porcelain
    "crimson": (138, 18, 32),
    "gold": (176, 140, 60),          # tarnished bells
    "skin": (118, 124, 126),         # the illager's grey
    "nose": (100, 106, 108),
    "porcelain": (236, 230, 216),    # the mask
    "socket": (10, 8, 14),
    "leg": (118, 92, 112),           # grey plum, lighter than the coat: the diamonds are painted over it
    "claw": (40, 34, 40),
    "crystal": (150, 230, 250),
    "crystal_dark": (90, 160, 210),
    "string": (230, 240, 255),
    "eye_glint": (150, 240, 255),
}
GLOWING = ("crystal", "string", "eye_glint")
NEIGHBOURS = [("black", "white"), ("black", "crimson"), ("white", "crimson"), ("porcelain", "skin"),
              ("porcelain", "socket"), ("leg", "black"), ("leg", "crimson"), ("skin", "claw"), ("crimson", "gold"),
              ("black", "gold"), ("crystal", "crystal_dark"), ("skin", "black")]


def zone_for(cube):
    return cube.mat


def twin(name):
    """A left part's right twin: legs, arms, fingers and the hat are built mirrored by name."""
    return name.replace("_left", "_right").replace("_-1", "_1")


def island_keys(model):
    names = {c.name: c for c in model.cubes}
    keys = {}
    for i, c in enumerate(model.cubes):
        for f in FACES:
            w, h = v4.face_size(c, f)
            if not w or not h or b4.hidden(c, f):
                continue
            t = twin(c.name)
            if t != c.name and t in names and v4.face_size(names[t], f) == (w, h) and zone_for(names[t]) == zone_for(c):
                keys[(i, f)] = (t, f, w, h, zone_for(c))
            else:
                keys[(i, f)] = (c.name, f, w, h, zone_for(c))
    return keys


def build_atlas(keys):
    sizes = {key: (key[2], key[3]) for key in keys.values()}
    positions, used, height = b4.pack(sizes)
    atlas = Image.new("RGBA", (SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        patch = Image.new("RGBA", (w, h), ZONES[key[4]] + (255,))
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return atlas, positions, used, height


def rig_bbmodel(model, keys, positions, atlas_path, height, poses):
    texture = {"name": ATLAS, "path": "", "folder": "", "namespace": "", "id": "0", "group": "",
               "width": SIZE, "height": height, "uv_width": SIZE, "uv_height": height, "particle": False,
               "use_as_default": True, "layers_enabled": False, "render_mode": "default", "render_sides": "auto",
               "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False,
               "visible": True, "internal": True, "saved": False, "uuid": _uuid(model.name + "/atlas"),
               "source": "data:image/png;base64," + base64.b64encode(atlas_path.read_bytes()).decode()}
    bb = model.to_bbmodel(texture_size=(SIZE, height), textures=(texture,))
    culled = 0
    for i, element in enumerate(bb["elements"]):
        for f in FACES:
            key = keys.get((i, f))
            if key is None:
                element["faces"][f] = {"uv": [0, 0, 0, 0], "texture": None}
                culled += bool(all(v4.face_size(model.cubes[i], f)))
                continue
            x, y, w, h = positions[key]
            element["faces"][f] = {"uv": [x, y, x + w, y + h], "texture": 0}
        if zone_for(model.cubes[i]).startswith(GLOWING):
            element["light_emission"] = 15
    frm, to = s2.hitbox_bounds(model)
    add_hitbox(bb, frm, to)
    bb["animations"] = [{"uuid": _uuid(f"{model.name}/anim/{key}"), "name": key, "loop": "hold", "override": False,
                         "length": 0.5, "snapping": 20, "selected": False, "anim_time_update": "", "blend_weight": "",
                         "start_delay": "", "loop_delay": "", "animators": s3.keyframes(model, rot, pos)}
                        for key, (rot, pos) in poses.items()]
    return bb, culled


# Blender coordinates (blocks, z up; his face looks along +y)
VIEWS = [
    {"name": "hero", "location": (7, 9, 5.5), "target": (0, 0, 3.6), "scale": 8.6, "player": True},
    {"name": "front", "location": (0, 12, 3.6), "target": (0, 0, 3.6), "scale": 8.4, "player": False},
    {"name": "side", "location": (12, 0, 3.6), "target": (0, 0, 3.6), "scale": 8.4, "player": False},
    {"name": "back", "location": (-4, -11, 4.6), "target": (0, 0, 3.6), "scale": 8.4, "player": False},
    {"name": "face", "location": (1.4, 5, 5.3), "target": (0, -0.1, 5.15), "scale": 1.7, "player": False},
]
DRAW = [{"name": "draw", "location": (7, 7, 4.4), "target": (0, 0, 3.4), "scale": 8.4, "player": False}]


def render(model, bb, atlas_path, out, views, player_at=(5.5, 3.0)):
    out.mkdir(parents=True, exist_ok=True)
    boxes = [{"corners": c.corners().tolist(), "from": c.frm, "to": c.to, "glow": zone_for(c).startswith(GLOWING),
              "uv": bb["elements"][i]["faces"]} for i, c in enumerate(model.cubes)]
    job_file = out / f"render_job_{views[0]['name']}.json"
    job_file.write_text(json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes,
                                    "views": views, "player_at": player_at}), encoding="utf-8")
    result = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job_file)],
                            capture_output=True, text=True)
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job_file.unlink()


def render_all(model, bb, atlas_path, out):
    """Standing, from five sides, and drawing his bow."""
    render(model, bb, atlas_path, out, VIEWS, player_at=(2.2, 1.2))
    draw = s2.build("draw_view")
    s2.finish(draw)
    s2.pose(draw, "draw")
    render(draw, bb, atlas_path, out, DRAW, player_at=(2.2, 1.2))


NAMES = ["hero", "front", "side", "back", "face", "draw"]


def review_sheet(out, heading):
    tw, th, pad, top = 400, 300, 12, 60
    img = Image.new("RGB", (pad + len(NAMES) * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), heading, font=sheet._font(28), fill=sheet.INK)
    for r, folder in enumerate(("colour", "grey")):
        for c, name in enumerate(NAMES):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(out / folder / f"{name}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{folder}: {name.replace('_', ' ')}", font=sheet._font(17), fill=sheet.DIM)
    img.save(out / "sheet.png")


def value_report():
    rows = [(z, rgb, round(v4.luminance(rgb))) for z, rgb in ZONES.items()]
    close = [(a, b, round(abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])))) for a, b in NEIGHBOURS
             if abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])) < 12]
    return rows, close


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    model = s2.build(s3.MODEL_ID)
    s2.finish(model)
    off = v4.check_density(model)
    if off:
        raise SystemExit("faces off the texel grid: " + ", ".join(off[:10]))
    keys = island_keys(model)
    atlas, positions, used, height = build_atlas(keys)
    atlas_path = OUT / ATLAS
    atlas.save(atlas_path)
    grey_path = OUT / "occultech_night_matriarch_grey.png"
    atlas.convert("LA").convert("RGBA").save(grey_path)
    atlas.resize((SIZE * 2, height * 2), Image.NEAREST).save(OUT / "atlas_preview.png")
    bb, culled = rig_bbmodel(model, keys, positions, atlas_path, height, s3.pose_table())
    path = OUT / f"{model.name}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    render_all(model, bb, atlas_path, OUT / "colour")
    render_all(model, bb, grey_path, OUT / "grey")
    review_sheet(OUT, "Mirrored Magus - UV and material zones (session 4), colour then grey")
    texels = sum(w * h for (_, _, w, h) in positions.values())
    rows, close = value_report()
    report = {"atlas": [SIZE, height], "rows_used": used, "islands": len(positions), "faces_drawn": len(keys),
              "faces_buried_and_left_out": culled, "texels": texels, "fill": round(texels / (SIZE * used), 2),
              "zones": {z: {"rgb": list(rgb), "L": L} for z, rgb, L in rows},
              "neighbours_too_close_in_value": [f"{a}/{b}: {d}" for a, b, d in close]}
    (OUT / "uv_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("atlas", "rows_used", "islands", "faces_drawn",
                                                   "faces_buried_and_left_out", "fill",
                                                   "neighbours_too_close_in_value")}))


if __name__ == "__main__":
    main()
