"""The Elder of Ash, session 4: UV and material blocking.

On top of the session 3 rig (session 2's geometry), this session:
- maps every visible face at one texel per model unit (16 per block, the vanilla density) into one atlas, with a
  1-pixel border on each island against seams. He is about 9 blocks across, so the atlas is 512 wide;
- shares texture space only where both sides really are the same: a left limb, hand, foot, eye or gland uses its right
  twin's islands (mirrored by name, the same size);
- leaves out faces buried inside another cube of the same bone;
- fills each material zone with one flat colour, tied to vanilla's temperate frog (its orange-brown, the pale belly)
  and the user's brown, green and ash grey; the volcano runs from skin through ash to basalt; the lava, the eyes, the
  pipe's ember and the tongue's tip are drawn full-bright;
- the painted details (the tribal markings, the mouth's line, the nostrils, the pupils, the streams' wiggle) come in
  session 5 on top of these zones;
- renders him in colour and in grey (the value check) and lists every zone's value;
- updates the in-game review rig (`occultech_elder_of_ash_rig`).

Session 5 paints over this atlas. Run from the repository root: python tools/art/bosses/ash_s4.py
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
from bosses import brood_s4 as b4, ash_s2 as s2, ash_s3 as s3, volley_crone_s4 as v4  # noqa: E402

OUT = ROOT / "docs/art/bosses/elder_of_ash/overhaul/s4_uv"
SIZE = 512
ATLAS = "occultech_elder_of_ash.png"

ZONES = {
    # the toad: an olive-brown back, warmer brown flanks and limbs, the temperate frog's pale ochre belly
    "skin": (58, 72, 38), "flank": (136, 106, 66),
    "belly": (204, 178, 126), "wart": (38, 36, 22), "gland": (118, 112, 70),
    "toe": (92, 70, 42), "pad": (178, 146, 98),
    "mouth": (34, 18, 18), "tongue": (178, 78, 76), "tongue_tip": (255, 150, 60),
    "brow": (34, 30, 20), "brow_ash": (214, 210, 200), "brow_ash_dark": (164, 160, 152),
    "eye": (255, 186, 60),
    # the volcano: skin hardening to ash, then basalt
    "skin_ash": (124, 120, 102), "ash": (158, 154, 148), "ash_dark": (104, 100, 98), "basalt": (52, 48, 54),
    "basalt_lit": (80, 76, 84), "lava": (255, 120, 30), "lava_hot": (255, 214, 110),
    # the pipe
    "pipe": (124, 80, 44), "pipe_metal": (168, 158, 134), "ember": (255, 140, 40),
}
GLOWING = ("eye", "lava", "ember", "tongue_tip")
NEIGHBOURS = [("skin", "flank"), ("flank", "belly"), ("skin", "wart"), ("flank", "wart"), ("skin", "gland"),
              ("flank", "toe"), ("toe", "pad"), ("skin", "brow"), ("brow", "brow_ash"),
              ("brow_ash", "brow_ash_dark"), ("skin", "eye"), ("flank", "mouth"), ("mouth", "tongue"),
              ("skin", "skin_ash"), ("skin_ash", "ash"), ("ash", "ash_dark"), ("ash_dark", "basalt"),
              ("basalt", "basalt_lit"), ("basalt", "lava"), ("flank", "lava"), ("pipe", "pipe_metal"),
              ("flank", "pipe_metal")]


TOAD = ("skin", "flank", "limb", "skin_dark")         # countershaded like a real toad: green above, brown below
SHARED = ("toe", "pad", "wart", "lava", "lava_hot", "ash_dark")       # same-size pieces look alike (the lava is one glowing flow)
UP = 0.35                                             # a face counts as facing the sky past this much upward tilt


def zone_for(cube):
    return cube.mat


def face_normals(model):
    """Each face's outward normal in the rest pose, by (cube index, face)."""
    from bosskit.checks import QUADS
    import numpy as np
    out = {}
    for i, c in enumerate(model.cubes):
        p = c.corners()
        centre = p.mean(0)
        for f, q in QUADS.items():
            pts = p[list(q)]
            n = np.cross(pts[1] - pts[0], pts[2] - pts[0])
            if np.linalg.norm(n) < 1e-9:
                continue
            n /= np.linalg.norm(n)
            if np.dot(pts.mean(0) - centre, n) < 0:
                n = -n
            out[(i, f)] = n
    return out


def face_zone(model, i, f, normals):
    """The zone of one face: the toad's skin is dark green where it faces the sky, brown everywhere else (body, head
    and limbs alike); every other material keeps its own zone."""
    c = model.cubes[i]
    if c.mat in TOAD:
        n = normals.get((i, f))
        return "skin" if n is not None and n[1] > UP else "flank"
    return c.mat


def twin(name):
    """A left part's right twin: limbs, hands, feet, eyes and glands are built mirrored by name."""
    name = name.replace("_left", "_right")
    return re.sub(r"_-1(?=_|$)", "_1", name)


def island_keys(model):
    names = {c.name: c for c in model.cubes}
    index = {c.name: i for i, c in enumerate(model.cubes)}
    normals = face_normals(model)
    keys = {}
    for i, c in enumerate(model.cubes):
        for f in FACES:
            w, h = v4.face_size(c, f)
            if not w or not h or b4.hidden(c, f):
                continue
            zone = face_zone(model, i, f, normals)
            if c.mat in SHARED:                       # every finger, toe, tip bump and wart of a size looks alike
                keys[(i, f)] = (c.mat, f, w, h, zone)
                continue
            t = twin(c.name)
            if t != c.name and t in names and v4.face_size(names[t], f) == (w, h)                     and face_zone(model, index[t], f, normals) == zone:
                keys[(i, f)] = (t, f, w, h, zone)
            else:
                keys[(i, f)] = (c.name, f, w, h, zone)
    return keys


def build_atlas(keys):
    sizes = {key: (key[2], key[3]) for key in keys.values()}
    b4.SIZE = SIZE                               # brood_s4's skyline packer reads its module's width
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
            if key is None:   # a buried or zero-width face: no texture, so it is never drawn
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


# Blender coordinates (blocks, z up); he faces +y. Orthographic: scale is the view's width in blocks.
VIEWS = [
    {"name": "hero", "location": (11, 13, 8), "target": (0, -0.3, 2.8), "scale": 12.5, "player": True},
    {"name": "front", "location": (0, 18, 3.2), "target": (0, 0, 3.2), "scale": 10.5, "player": False},
    {"name": "player_eye", "location": (-4.5, 10, 1.62), "target": (0, 0, 1.9), "scale": 11.5, "player": False},
    {"name": "side", "location": (18, -0.5, 3.4), "target": (0, -0.5, 3.4), "scale": 11, "player": False},
    {"name": "back", "location": (8, -16, 7), "target": (0, -0.5, 2.8), "scale": 11.5, "player": False},
    {"name": "face", "location": (2.0, 10, 2.7), "target": (0, 3.2, 2.2), "scale": 5.0, "player": False},
]


def render(model, bb, atlas_path, out, views=VIEWS):
    out.mkdir(parents=True, exist_ok=True)
    boxes = [{"corners": c.corners().tolist(), "from": c.frm, "to": c.to, "glow": zone_for(c).startswith(GLOWING),
              "uv": bb["elements"][i]["faces"]} for i, c in enumerate(model.cubes)]
    job_file = out / "render_job.json"
    job_file.write_text(json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes,
                                    "views": views, "player_at": (5.6, 2.0)}), encoding="utf-8")
    result = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job_file)],
                            capture_output=True, text=True)
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job_file.unlink()


def review_sheet(out, heading, views=VIEWS):
    names = [v["name"] for v in views]
    tw, th, pad, top = 400, 300, 12, 60
    img = Image.new("RGB", (pad + len(names) * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), heading, font=sheet._font(28), fill=sheet.INK)
    for r, folder in enumerate(("colour", "grey")):
        for c, name in enumerate(names):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(out / folder / f"{name}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{folder}: {name.replace('_', ' ')}", font=sheet._font(17), fill=sheet.DIM)
    img.save(out / "sheet.png")


def value_report():
    rows = [(z, rgb, round(v4.luminance(rgb))) for z, rgb in ZONES.items()]
    close = [(a, b, round(abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])))) for a, b in NEIGHBOURS
             if abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])) < 12]
    return rows, close


def build_model():
    s3.setup()
    model = s2.build(s3.MODEL_ID, decals=False)
    s2.finish(model)
    off = v4.check_density(model)
    if off:
        raise SystemExit("faces off the texel grid: " + ", ".join(off[:10]))
    return model


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    model = build_model()
    keys = island_keys(model)
    atlas, positions, used, height = build_atlas(keys)
    atlas_path = OUT / ATLAS
    atlas.save(atlas_path)
    grey_path = OUT / "occultech_elder_of_ash_grey.png"
    atlas.convert("LA").convert("RGBA").save(grey_path)
    atlas.save(OUT / "atlas_preview.png")
    bb, culled = rig_bbmodel(model, keys, positions, atlas_path, height, s3.pose_table())
    path = OUT / f"{model.name}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    render(model, bb, atlas_path, OUT / "colour")
    render(model, bb, grey_path, OUT / "grey")
    review_sheet(OUT, "The Elder of Ash - UV and material zones (session 4), colour then grey")
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
