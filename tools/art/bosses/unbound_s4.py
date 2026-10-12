"""The Unbound redesign, session 4: UV and material blocking (plan: docs/art/bosses/the_unbound/overhaul/plan.md).

On top of the session 3 rig, this session:
- maps every visible face at one texel per model unit (16 per block, the vanilla density) into one atlas, with a
  1-pixel border on each island against seams;
- shares texture space where parts are mirror twins: a left limb, horn, strap or brow uses its right twin's islands;
- leaves out faces buried inside another cube of the same bone;
- fills each material zone with one flat colour, tied to vanilla's vindicator: grey skin, the dark heavy brow, dark
  trousers and black boots. On top of that: the red band, bone horns, dark leather straps with silver studs,
  blackened iron (chest piece, shackles), steel chains, the steel cleaver with dried blood on its edge. The eye's
  spirit cyan and the chest fire are the only saturated colours, and are drawn full-bright;
- renders him in colour and in grey (the value check) and lists every zone's value;
- updates the in-game review rig (`occultech_unbound_rig`), so the pixel size can be judged in game.

Session 5 paints over this atlas. Run from the repository root: python tools/art/bosses/unbound_s4.py
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
from bosses import brood_s4 as b4, unbound_s2 as s2, unbound_s3 as s3, volley_crone_s4 as v4  # noqa: E402

OUT = ROOT / "docs/art/bosses/the_unbound/overhaul/s4_uv"
SIZE = 256
ATLAS = "occultech_unbound.png"

ZONES = {
    "skin": (126, 132, 130),          # vanilla's vindicator grey
    "skin_crease": (92, 98, 98),       # the line under the pecs
    "nose": (92, 98, 97),
    "brow": (44, 44, 48),              # the vindicator's heavy dark brow
    "cloth": (134, 30, 32),            # the red band
    "cloth_dark": (70, 14, 18),        # its knot, tails and torn flap
    "horn": (196, 184, 152),
    "horn_root": (124, 110, 86),       # the boss across the skull
    "horn_tip": (150, 136, 104),
    "strap": (112, 78, 48),            # leather, a step lighter than the trousers
    "stud": (198, 202, 210),           # silver
    "iron": (56, 54, 60),              # blackened iron: the chest piece, the shackles
    "iron_lit": (104, 102, 110),       # rims, the nose ring
    "chain": (128, 128, 136),
    "pants": (48, 48, 58),             # vanilla's dark vindicator trousers
    "boot": (20, 17, 17),
    "steel": (156, 162, 168),
    "spine": (90, 94, 100),
    "wrap": (66, 46, 30),
    "blood": (94, 18, 18),
    "hole": (24, 22, 26),
    "fire": (236, 92, 18), "fire_hot": (255, 186, 70),
    "eye": (70, 210, 250), "eye_hot": (200, 248, 255), "eye_dim": (26, 92, 116),
}
GLOWING = ("fire", "eye")
NEIGHBOURS = [("skin", "nose"), ("skin", "brow"), ("skin", "cloth"), ("cloth", "cloth_dark"), ("skin", "strap"),
              ("strap", "stud"), ("skin", "iron"), ("iron", "iron_lit"), ("skin", "horn"), ("horn", "horn_root"),
              ("horn", "horn_tip"), ("pants", "boot"), ("pants", "strap"), ("skin", "pants"), ("steel", "spine"),
              ("steel", "blood"), ("wrap", "spine"), ("iron", "chain"), ("skin", "skin_crease")]


def zone_for(cube):
    """The material zone a cube is painted in: by its part first, then by its material."""
    n, m = cube.name, cube.mat
    if n.startswith("pec_line"):
        return "skin_crease"
    if n in ("rag",) or m == "cloth_dark":
        return "cloth_dark"
    return {"skin": "skin", "skin_dark": "skin", "nose": "nose", "brow": "brow", "cloth": "cloth",
            "horn": "horn", "horn_root": "horn_root", "horn_dark": "horn_tip", "strap": "strap", "stud": "stud",
            "iron": "iron", "iron_lit": "iron_lit", "chain": "chain", "pants": "pants", "boot": "boot",
            "steel": "steel", "spine": "spine", "wrap": "wrap", "blood": "blood", "hole": "hole",
            "fire": "fire", "fire_hot": "fire_hot", "eye": "eye", "eye_hot": "eye_hot", "eye_dim": "eye_dim"}[m]


def twin(name):
    """A left part's right twin: limbs, horns, straps, brows and studs are built mirrored by name."""
    return re.sub(r"_-1(?=_|$)", "_1", name.replace("_left", "_right").replace("ring_l", "ring_r"))


def island_keys(model):
    names = {c.name: c for c in model.cubes}
    keys = {}
    for i, c in enumerate(model.cubes):
        for f in FACES:
            w, h = v4.face_size(c, f)
            if not w or not h or b4.hidden(c, f):
                continue
            t = twin(c.name)
            if t != c.name and t in names and v4.face_size(names[t], f) == (w, h):
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


VIEWS = [
    {"name": "hero", "location": (6.0, 7.0, 4.4), "target": (0, -0.3, 1.7), "scale": 6.2, "player": True},
    {"name": "front", "location": (0, 10, 1.9), "target": (0, 0, 1.9), "scale": 4.6, "player": False},
    {"name": "player_eye", "location": (-2.4, 5.5, 1.62), "target": (0, 0, 2.4), "scale": 4.8, "player": False},
    {"name": "side", "location": (10, -0.8, 1.9), "target": (0, -0.8, 1.9), "scale": 5.6, "player": False},
    {"name": "back", "location": (4.5, -9, 4.2), "target": (0, -0.8, 1.6), "scale": 5.6, "player": False},
    {"name": "face", "location": (1.4, 6, 3.0), "target": (0, 0.4, 2.95), "scale": 1.6, "player": False},
]


def render(model, bb, atlas_path, out):
    out.mkdir(parents=True, exist_ok=True)
    boxes = [{"corners": c.corners().tolist(), "from": c.frm, "to": c.to, "glow": zone_for(c).startswith(GLOWING),
              "uv": bb["elements"][i]["faces"]} for i, c in enumerate(model.cubes)]
    job_file = out / "render_job.json"
    job_file.write_text(json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes,
                                    "views": VIEWS, "player_at": (2.6, 1.0)}), encoding="utf-8")
    result = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job_file)],
                            capture_output=True, text=True)
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job_file.unlink()


def review_sheet(out, heading):
    names = [v["name"] for v in VIEWS]
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


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    k = s3.scale_factor()
    model = s2.build(s3.MODEL_ID)
    s2.finish(model, k)
    off = v4.check_density(model)
    if off:
        raise SystemExit("faces off the texel grid: " + ", ".join(off[:10]))
    keys = island_keys(model)
    atlas, positions, used, height = build_atlas(keys)
    atlas_path = OUT / ATLAS
    atlas.save(atlas_path)
    grey_path = OUT / "occultech_unbound_grey.png"
    atlas.convert("LA").convert("RGBA").save(grey_path)
    atlas.resize((SIZE * 2, height * 2), Image.NEAREST).save(OUT / "atlas_preview.png")
    bb, culled = rig_bbmodel(model, keys, positions, atlas_path, height, s3.pose_table(k))
    path = OUT / f"{model.name}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    render(model, bb, atlas_path, OUT / "colour")
    render(model, bb, grey_path, OUT / "grey")
    review_sheet(OUT, "The Unbound - UV and material zones (session 4), colour then grey")
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
