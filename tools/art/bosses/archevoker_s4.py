"""The Archevoker redesign, session 4: UV and material blocking (plan: docs/art/bosses/archevoker/overhaul/plan.md).

Every visible face of the session 3 rig (session 2's geometry) is mapped at one texel per model unit (16 per block,
the vanilla density) into one atlas per model, each face a flat colour of its material zone:
- the priest's atlas holds the priest, the throne and the ring. Shared islands: a left part uses its right twin's
  (the arms, the legs, the throne's sides, the armrests' hands); the ring's twelve small hands share one hand's
  islands, since they are alike; everything else has its own;
- each casting hand has its own small atlas (it is its own model);
- a value check: neighbouring zones must stay apart in lightness, so he reads in grey too;
- textured renders in colour and in grey, and the review models (with the session 3 poses) copied into
  run/plugins/BetterModel/models for the first in-game look at the pixel size.

Run from the repository root: python tools/art/bosses/archevoker_s4.py
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
from bosses import archevoker_s2 as s2, archevoker_s3 as s3  # noqa: E402
from bosses import brood_s4 as b4, volley_crone_s4 as v4  # noqa: E402

OUT = ROOT / "docs/art/bosses/archevoker/overhaul/s4_uv"
SIZE = 512
HAND_SIZE = 64

ZONES = {
    # the priest: the evoker's black robe and gold trim, his grey skin, a violet stole (tier 1)
    "robe": (46, 44, 52), "robe_dark": (20, 18, 24), "hood_in": (12, 10, 16), "trim": (192, 160, 74),
    "stole": (104, 58, 150), "skin": (150, 156, 156), "nose": (116, 122, 122), "brow": (32, 32, 38),
    "shoe": (96, 76, 60),
    # the gold of the hands, the chain, the finials; the emeralds
    "gold": (220, 184, 86), "gold_dark": (150, 112, 46), "emerald": (28, 150, 84),
    # the woodland mansion's dark oak and its wine velvet
    "oak": (82, 56, 34), "oak_dark": (46, 31, 21), "velvet": (58, 18, 34),
    # the eyes in the palms; the magic (full-bright)
    "white": (248, 246, 240), "cyan": (80, 220, 250), "purple": (186, 104, 255),
}
GLOWING = ("cyan", "purple")
NEIGHBOURS = [("robe", "trim"), ("robe", "skin"), ("robe", "robe_dark"), ("robe", "hood_in"), ("robe", "stole"),
              ("stole", "trim"), ("skin", "nose"), ("skin", "brow"), ("skin", "cyan"), ("robe", "gold"),
              ("robe", "shoe"), ("gold", "gold_dark"), ("gold", "emerald"), ("gold", "white"), ("white", "cyan"),
              ("white", "purple"), ("oak", "oak_dark"), ("oak", "velvet"), ("oak", "gold"), ("velvet", "gold"),
              ("oak_dark", "gold_dark"), ("robe_dark", "trim"), ("oak_dark", "cyan")]


def twin(name):
    """A left part's right twin, by name: _left -> _right, a _-1 index -> _1; a ring hand -> the ring's first hand."""
    name = name.replace("_left", "_right")
    name = re.sub(r"_-1(?=_|$)", "_1", name)
    return re.sub(r"^ring_hand\d+_", "ring_hand0_", name)


def island_keys(model):
    names = {c.name: c for c in model.cubes}
    keys = {}
    for i, c in enumerate(model.cubes):
        for f in FACES:
            w, h = v4.face_size(c, f)
            if not w or not h or b4.hidden(c, f):
                continue
            t = twin(c.name)
            if t != c.name and t in names and v4.face_size(names[t], f) == (w, h) and names[t].mat == c.mat:
                keys[(i, f)] = (t, f, w, h, c.mat)
            else:
                keys[(i, f)] = (c.name, f, w, h, c.mat)
    return keys


def build_atlas(keys, size):
    sizes = {key: (key[2], key[3]) for key in keys.values()}
    b4.SIZE = size                                # brood_s4's skyline packer reads its module's width
    positions, used, _ = b4.pack(sizes)
    height = 16
    while height < used:                          # a power of two, as short as the islands allow
        height *= 2
    atlas = Image.new("RGBA", (size, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        patch = Image.new("RGBA", (w, h), ZONES[key[4]] + (255,))
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return atlas, positions, used, height


def textured_bbmodel(model, keys, positions, atlas_path, size, height, hitbox, poses=()):
    texture = {"name": atlas_path.name, "path": "", "folder": "", "namespace": "", "id": "0", "group": "",
               "width": size, "height": height, "uv_width": size, "uv_height": height, "particle": False,
               "use_as_default": True, "layers_enabled": False, "render_mode": "default", "render_sides": "auto",
               "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False,
               "visible": True, "internal": True, "saved": False, "uuid": _uuid(model.name + "/atlas"),
               "source": "data:image/png;base64," + base64.b64encode(atlas_path.read_bytes()).decode()}
    bb = model.to_bbmodel(texture_size=(size, height), textures=(texture,))
    culled = 0
    for i, element in enumerate(bb["elements"]):
        for f in FACES:
            key = keys.get((i, f))
            if key is None:   # a buried or zero-width face: no texture, so it is never drawn
                element["faces"][f] = {"uv": [0, 0, 0, 0], "texture": None}
                culled += bool(all(v4.face_size(model.cubes[i], f)))
                continue
            x, y, w, h = positions[key]
            element["faces"][f] = {"uv": [x, y, x + w, y + h], "texture": 0}
        if model.cubes[i].mat in GLOWING:
            element["light_emission"] = 15
    add_hitbox(bb, *hitbox)
    bb["animations"] = [{"uuid": _uuid(f"{model.name}/anim/{key}"), "name": key, "loop": "hold", "override": False,
                         "length": 0.5, "snapping": 20, "selected": False, "anim_time_update": "", "blend_weight": "",
                         "start_delay": "", "loop_delay": "", "animators": s3.keyframes(model, rot, pos)}
                        for key, (rot, pos) in poses]
    return bb, culled


# Blender coordinates (blocks, z up); he faces +y. Orthographic: scale is the view's width in blocks.
VIEWS = [
    {"name": "hero", "location": (10, 14, 8), "target": (0, 0, 4.2), "scale": 11.5, "player": True},
    {"name": "front", "location": (0, 18, 4.4), "target": (0, 0, 4.4), "scale": 10.0, "player": False},
    {"name": "player_eye", "location": (-4.5, 10, 1.62), "target": (0, 0, 3.6), "scale": 10.5, "player": False},
    {"name": "side", "location": (18, 0, 4.4), "target": (0, 0, 4.4), "scale": 10.0, "player": False},
    {"name": "back", "location": (8, -16, 7), "target": (0, 0, 4.2), "scale": 10.5, "player": False},
    {"name": "face", "location": (1.6, 10, 6.4), "target": (0, 0.2, 5.9), "scale": 3.6, "player": False},
]
HAND_VIEWS = [
    {"name": "hand_front", "location": (0, 10, 1.7), "target": (0, 0, 1.85), "scale": 3.7, "player": False},
    {"name": "hand_34", "location": (6, 8, 3), "target": (0, 0, 1.85), "scale": 3.7, "player": False},
    {"name": "hand_back", "location": (-4, -9, 2.4), "target": (0, 0, 1.85), "scale": 3.7, "player": False},
]


def render(model, bb, atlas_path, out, views):
    out.mkdir(parents=True, exist_ok=True)
    boxes = [{"corners": c.corners().tolist(), "from": c.frm, "to": c.to, "glow": c.mat in GLOWING,
              "uv": bb["elements"][i]["faces"]} for i, c in enumerate(model.cubes)]
    job_file = out / "render_job.json"
    job_file.write_text(json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes,
                                    "views": views, "player_at": (5.0, 3.0)}), encoding="utf-8")
    result = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job_file)],
                            capture_output=True, text=True)
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job_file.unlink()


def review_sheet(out, heading, views, rows=(("colour", "colour"), ("grey", "grey")), name="sheet.png"):
    names = [v["name"] for v in views]
    tw, th, pad, top = 400, 300, 12, 60
    img = Image.new("RGB", (pad + len(names) * (tw + pad), top + len(rows) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), heading, font=sheet._font(28), fill=sheet.INK)
    for r, (folder, label) in enumerate(rows):
        for c, n in enumerate(names):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(out / folder / f"{n}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{label}: {n.replace('_', ' ')}", font=sheet._font(17), fill=sheet.DIM)
    img.save(out / name)


def value_report():
    rows = [(z, rgb, round(v4.luminance(rgb))) for z, rgb in ZONES.items()]
    close = [(a, b, round(abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])))) for a, b in NEIGHBOURS
             if abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])) < 12]
    return rows, close


def model_pass(model, name, size, hitbox, poses, out, views):
    """UVs, the atlas (colour and grey), the review model and its renders, for one model."""
    off = v4.check_density(model)
    if off:
        raise SystemExit("faces off the texel grid: " + ", ".join(off[:10]))
    model.name = name
    keys = island_keys(model)
    atlas, positions, used, height = build_atlas(keys, size)
    atlas_path = out / f"{name}.png"
    atlas.save(atlas_path)
    grey_path = out / f"{name}_grey.png"
    atlas.convert("LA").convert("RGBA").save(grey_path)
    bb, culled = textured_bbmodel(model, keys, positions, atlas_path, size, height, hitbox, poses)
    path = out / f"{name}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    folder = "" if name == s3.MODEL_ID else name.split("_")[-2] + "_"
    render(model, bb, atlas_path, out / f"{folder}colour", views)
    render(model, bb, grey_path, out / f"{folder}grey", views)
    texels = sum(w * h for (_, _, w, h) in positions.values())
    return {"atlas": [size, height], "rows_used": used, "islands": len(positions), "faces_drawn": len(keys),
            "faces_buried_and_left_out": culled, "fill": round(texels / (size * used), 2)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.rglob("*"):                               # files only: an open folder can't be removed
        if old.is_file() and old.name != "README.md":
            old.unlink()
    model = s3.build("rest")
    report = {"priest": model_pass(model, s3.MODEL_ID, SIZE, s2.hitbox_bounds(model), s3.pose_table().items(), OUT,
                                   VIEWS)}
    review_sheet(OUT, "The Archevoker - UV and material zones (session 4), colour then grey", VIEWS)
    for glow in ("cyan", "purple"):
        hm = s2.hand_model(glow)
        s3.fold_quarter_turns(hm)
        report[glow] = model_pass(hm, f"occultech_archevoker_hand_{glow}_rig", HAND_SIZE, s2.HAND_HITBOX, (), OUT,
                                  HAND_VIEWS)
    review_sheet(OUT, "The casting hands - UV and material zones", HAND_VIEWS,
                 rows=(("cyan_colour", "cyan"), ("cyan_grey", "cyan, grey"), ("purple_colour", "purple")),
                 name="hands.png")
    rows, close = value_report()
    report["zones"] = {z: {"rgb": list(rgb), "L": L} for z, rgb, L in rows}
    report["neighbours_too_close_in_value"] = [f"{a}/{b}: {d}" for a, b, d in close]
    (OUT / "uv_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("priest", "cyan", "neighbours_too_close_in_value")}))


if __name__ == "__main__":
    main()
