"""Witch Coven redesign, session 4: UV and material blocking (plan: docs/art/bosses/witch_coven/overhaul/plan.md).

On top of the session 3 rigs, this session:
- maps every visible face of the three sisters at one texel per model unit (16 per block, the vanilla density) into
  **one shared atlas**, with a 1-pixel border on each island against seams;
- shares texture space where parts are truly identical: the body, head, hat and sleeves are the same cubes on all
  three sisters, and a left sleeve shares its right twin's islands; the vessels get islands of their own;
- leaves out faces buried inside another cube of the same bone;
- fills each material zone with one flat colour, tied to vanilla's witch: a purple robe under a brown coat, a
  near-black hat with a green band, pale grey-beige skin, purple eyes, a brown mole; vanilla's cauldron grey for
  the iron. The brew is the only saturated thing, in the role colour;
- renders each sister in colour and in grey (the value check) and lists every zone's value;
- updates the in-game review rigs (`occultech_coven_<vessel>_rig`), so the pixel size can be judged in game.

Session 5 paints over this atlas. Run from the repository root: python tools/art/bosses/coven_s4.py
"""
import base64
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, _uuid, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import brood_s4 as b4, coven_s2 as s2, coven_s3 as s3, volley_crone_s3 as v3, volley_crone_s4 as v4  # noqa: E402

OUT = ROOT / "docs/art/bosses/witch_coven/overhaul/s4_uv"
SIZE = 256
ATLAS = "occultech_coven.png"

# One flat colour per zone. Vanilla's witch gives the robe, coat, hat, skin, eyes and mole; the body stays dark and
# calm; the brew is the only saturated colour.
ZONES = {
    "robe": (52, 24, 78),            # vanilla's witch purple
    "robe_hem": (16, 5, 27),        # the ragged hem, a step darker
    "coat": (78, 64, 42),            # vanilla's brown jacket over the robe, and the sleeves
    "coat_dark": (44, 36, 23),       # the collar
    "cuff": (30, 25, 20),
    "skin": (171, 159, 141),         # vanilla's witch skin
    "nose": (140, 125, 106),
    "mole": (117, 71, 47),
    "brow": (46, 42, 40),
    "eye": (138, 84, 164),           # vanilla's purple witch eyes
    "hat": (46, 44, 52),             # vanilla's near-black hat
    "hat_tip": (17, 16, 21),
    "band": (52, 88, 44),            # vanilla's green band
    "iron": (94, 94, 100),            # vanilla's cauldron grey
    "iron_dark": (54, 54, 60),
    "rope": (146, 124, 82),
    "strap": (122, 88, 54),
    "buckle": (150, 140, 110),
    "glass": (178, 202, 204),
    "cork": (126, 96, 62),
    "herb": (86, 98, 58),
    "bone": (200, 190, 164),
    "brew_green": (120, 235, 90), "brew_purple": (176, 84, 230), "brew_red": (232, 76, 60),
    "foam_green": (210, 255, 170), "foam_purple": (232, 190, 255), "foam_red": (255, 196, 150),
    "steam_green": (180, 240, 160), "steam_purple": (206, 160, 238), "steam_red": (240, 160, 140),
}
GLOWING = ("brew_", "foam_", "steam_")
NEIGHBOURS = [("robe", "coat"), ("robe", "robe_hem"), ("coat", "coat_dark"), ("coat", "cuff"), ("skin", "nose"),
              ("skin", "brow"), ("skin", "eye"), ("nose", "mole"), ("hat", "band"), ("hat", "hat_tip"),
              ("hat", "skin"), ("iron", "iron_dark"), ("iron", "rope"), ("coat", "rope"), ("coat", "strap"),
              ("robe", "herb"), ("coat", "iron")]


def zone_for(cube):
    """The material zone a cube is painted in: by its part first, then by its material."""
    n, m = cube.name, cube.mat
    if n.startswith("hem_"):
        return "robe_hem"
    if n.startswith("robe_lower"):
        return "robe"
    if n.startswith("robe_upper") or n.endswith("_sleeve") or n.endswith("_shoulder"):
        return "coat"
    if n == "collar":
        return "coat_dark"
    if m.startswith("glow_"):
        return "brew_" + m[5:]
    if m.startswith("hot_"):
        return "foam_" + m[4:]
    if m.startswith("steam_"):
        return m
    return {"robe_dark": "coat_dark", "sleeve": "coat", "skin": "skin", "nose": "nose", "mole": "mole",
            "brow": "brow", "eye": "eye", "hat": "hat", "hat_dark": "hat_tip", "band": "band", "cuff": "cuff",
            "iron": "iron", "iron_dark": "iron_dark", "rope": "rope", "strap": "strap", "buckle": "buckle",
            "glass": "glass", "cork": "cork", "herb": "herb", "bone": "bone"}[m]


def island_key(cube, face, w, h):
    """Shared across the three sisters by part name and size; a left sleeve shares its right twin's islands."""
    name = cube.name
    if name.startswith("left_"):
        name = "right_" + name[5:]
    return (name, face, w, h, zone_for(cube))


def build_atlas(models):
    """One atlas for all three: every visible face's island, packed once however many sisters use it."""
    sizes, keys = {}, []
    for model in models:
        k = {}
        for i, c in enumerate(model.cubes):
            for f in FACES:
                w, h = v4.face_size(c, f)
                if not w or not h or b4.hidden(c, f):
                    continue
                key = island_key(c, f, w, h)
                k[(i, f)] = key
                sizes[key] = (w, h)
        keys.append(k)
    positions, used, height = b4.pack(sizes)
    atlas = Image.new("RGBA", (SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        patch = Image.new("RGBA", (w, h), ZONES[key[4]] + (255,))
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return atlas, positions, keys, used, height


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
                         "start_delay": "", "loop_delay": "", "animators": v3.keyframes(model, pose)}
                        for key, pose in poses.items()]
    return bb, culled


VIEWS = [
    {"name": "hero", "location": (5.5, 6.5, 4.6), "target": (0, 0.2, 1.9), "scale": 5.6, "player": True},
    {"name": "front", "location": (0, 10, 2.1), "target": (0, 0, 2.1), "scale": 4.8, "player": False},
    {"name": "player_eye", "location": (-2.4, 6, 1.62), "target": (0, 0, 2.3), "scale": 4.8, "player": False},
    {"name": "side", "location": (10, -0.3, 2.1), "target": (0, -0.3, 2.1), "scale": 5.0, "player": False},
    {"name": "back", "location": (4.5, -9, 4.5), "target": (0, -0.4, 2.0), "scale": 5.0, "player": False},
    {"name": "face", "location": (1.2, 6, 3.1), "target": (0, 0.25, 2.95), "scale": 1.7, "player": False},
]


def render(model, bb, atlas_path, out):
    out.mkdir(parents=True, exist_ok=True)
    boxes = [{"corners": c.corners().tolist(), "from": c.frm, "to": c.to, "glow": zone_for(c).startswith(GLOWING),
              "uv": bb["elements"][i]["faces"]} for i, c in enumerate(model.cubes)]
    job_file = out / "render_job.json"
    job_file.write_text(json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes,
                                    "views": VIEWS, "player_at": (2.0, 1.6)}), encoding="utf-8")
    result = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job_file)],
                            capture_output=True, text=True)
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job_file.unlink()


def review_sheet(out, title):
    names = [v["name"] for v in VIEWS]
    tw, th, pad, top = 400, 300, 12, 60
    img = Image.new("RGB", (pad + len(names) * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), f"Witch Coven - {title}: UV and material zones (session 4), colour then grey", font=sheet._font(28),
            fill=sheet.INK)
    for r, folder in enumerate(("colour", "grey")):
        for c, name in enumerate(names):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(out / folder / f"{name}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{folder}: {name.replace('_', ' ')}", font=sheet._font(17), fill=sheet.DIM)
    img.save(out / "sheet.png")


def value_report():
    rows = [(z, rgb, round(v4.luminance(rgb)), round(max(rgb) and (max(rgb) - min(rgb)) / max(rgb), 2))
            for z, rgb in ZONES.items()]
    close = [(a, b, round(abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])))) for a, b in NEIGHBOURS
             if abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])) < 12]
    return rows, close


def main():
    if OUT.exists():                              # regenerate everything but the hand-written README
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    models = []
    for vessel, role, _ in s2.SISTERS:
        m = s2.build(vessel, role)
        m.name = s3.model_id(vessel)
        off = v4.check_density(m)
        if off:
            raise SystemExit("faces off the texel grid: " + ", ".join(off))
        models.append(m)
    atlas, positions, keys, used, height = build_atlas(models)
    atlas_path = OUT / ATLAS
    atlas.save(atlas_path)
    grey_path = OUT / "occultech_coven_grey.png"
    atlas.convert("LA").convert("RGBA").save(grey_path)
    atlas.resize((SIZE * 2, height * 2), Image.NEAREST).save(OUT / "atlas_preview.png")

    report = {"atlas": [SIZE, height], "rows_used": used, "islands": len(positions), "sisters": {}}
    for (vessel, role, title), model, k in zip(s2.SISTERS, models, keys):
        out = OUT / vessel
        bb, culled = rig_bbmodel(model, k, positions, atlas_path, height, s3.pose_table(vessel, role))
        out.mkdir()
        path = out / f"{model.name}.bbmodel"
        path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
        if s3.SERVER_MODELS.is_dir():
            shutil.copyfile(path, s3.SERVER_MODELS / path.name)
        render(model, bb, atlas_path, out / "colour")
        render(model, bb, grey_path, out / "grey")
        review_sheet(out, title)
        report["sisters"][vessel] = {"faces_drawn": len(k), "faces_buried_and_left_out": culled,
                                     "islands_used": len(set(k.values()))}
    texels = sum(w * h for (_, _, w, h) in positions.values())
    rows, close = value_report()
    report.update({"texels": texels, "fill": round(texels / (SIZE * used), 2),
                   "zones": {z: {"rgb": list(rgb), "L": L, "saturation": s} for z, rgb, L, s in rows},
                   "neighbours_too_close_in_value": [f"{a}/{b}: {d}" for a, b, d in close]})
    (OUT / "uv_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("atlas", "rows_used", "islands", "fill", "sisters",
                                             "neighbours_too_close_in_value")}))


if __name__ == "__main__":
    main()
