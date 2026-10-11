"""Volley redesign, session 4: UV and material blocking.

On top of the session 3 rig, this session:
- maps every cube face at one texel per model unit (16 per block, the vanilla density) into one packed atlas, with a
  1-pixel border on each island against seams;
- fills each material zone with one flat colour, plus the vanilla skeleton face as flat zones on the skull (each
  vanilla pixel doubled; the session 1-3 face insets are removed);
- renders the result in colour and in grey (the value check), and lists every zone's value;
- updates the in-game review model `occultech_volley_rig`, so the pixel size can be judged in game.

Session 5 paints over this atlas. Run from the repository root: python tools/art/bosses/volley_crone_s4.py
"""
import base64
import colorsys
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, _uuid, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s2 as s2, volley_crone_s3 as s3  # noqa: E402
from palettes import RAMPS  # noqa: E402

OUT = ROOT / "docs/art/bosses/volley/overhaul/s4_uv"
BLENDER = s2.BLENDER
SIZE = 256
HEIGHT = 512    # 66k texels at one per unit do not fit 256x256; every face stays unique (see the README)
FACE_INSETS = ("eye_left", "eye_right", "nose", "mouth")

# One flat colour per zone. Bone is vanilla's cool grey-white; iron armour is darker slate than the steel arbalest
# parts, so the weapon reads apart from the armour; violet is kept for the magic alone.
ZONES = {
    "bone": (198, 198, 192),
    "face_dark": (54, 50, 58),        # eye slits and mouth row, like vanilla's darkest face pixels
    "face_nose": (112, 110, 114),     # vanilla's nose is a mid grey, not a hole
    "marrow": RAMPS["ash"][2][:3],    # inside the ribcage
    "armour": RAMPS["iron"][2][:3],
    "chain": RAMPS["iron"][3][:3],
    "steel": (150, 158, 176),
    "wood": (112, 86, 66),            # weathered dark oak, muted: only the magic is strongly coloured
    "string": (168, 148, 118),
    "basalt": RAMPS["ash"][1][:3],
    "calcite": RAMPS["chalk"][4][:3],
    "crystal": RAMPS["violet"][4][:3],  # a step lighter than the geode rim, so the unlit shards read apart from it
    "glow": RAMPS["violet"][5][:3],
}
ARBALEST_STEEL = ("lath_rail", "trigger_lever", "stirrup", "prod_center", "prod_limb", "prod_nock", "windlass_drum",
                  "windlass_arm")
# zones that touch on the model and must stay apart in value, not just in hue
NEIGHBOURS = [("bone", "calcite"), ("bone", "armour"), ("bone", "chain"), ("bone", "marrow"), ("armour", "chain"),
              ("crystal", "basalt"), ("crystal", "calcite"), ("crystal", "glow"), ("wood", "steel"),
              ("wood", "string"), ("bone", "face_dark"), ("bone", "face_nose")]


def zone_for(cube):
    if cube.mat == "iron":
        return "steel" if cube.name.startswith(ARBALEST_STEEL) else "armour"
    return cube.mat


def remove_face_insets(model):
    for cube in [c for c in model.cubes if c.name in FACE_INSETS]:
        cube.group.children.remove(cube)
        model.cubes.remove(cube)


def face_size(cube, face):
    d = [cube.to[i] - cube.frm[i] for i in range(3)]
    w, h = (d[0], d[1]) if face in ("north", "south") else ((d[2], d[1]) if face in ("east", "west") else (d[0], d[2]))
    return int(round(w)), int(round(h))


def check_density(model):
    """Every face is a whole number of texels at one texel per unit (session 2 snapped all sizes)."""
    off = []
    for c in model.cubes:
        for i in range(3):
            size = c.to[i] - c.frm[i]
            if abs(size - round(size)) > 1e-6:
                off.append(f"{c.name} axis {i}: {size}")
    return off


def pack(rectangles):
    """Shelf pack, tallest first, each island with a 1-pixel border."""
    positions, x, y, row = {}, 0, 0, 0
    for key, w, h in sorted(rectangles, key=lambda r: (-r[2], -r[1], str(r[0]))):
        if x + w + 2 > SIZE:
            x, y, row = 0, y + row, 0
        if y + h + 2 > HEIGHT:
            raise ValueError(f"atlas needs more than {SIZE}x{HEIGHT}")
        positions[key] = (x + 1, y + 1, w, h)
        x += w + 2
        row = max(row, h + 2)
    return positions, y + row


def paint_face(cube, face, w, h):
    zone = zone_for(cube)
    img = Image.new("RGBA", (w, h), ZONES[zone] + (255,))
    if face == "north" and cube.name == "skull":
        # vanilla face rows 0-5 doubled: row 4 = the eye slits (vanilla columns 1-2 and 5-6), row 5 = the nose (3-4)
        px = img.load()
        for x in range(w):
            for y in range(h):
                col, row = x // 2, y // 2
                if row == 4 and col in (1, 2, 5, 6):
                    px[x, y] = ZONES["face_dark"] + (255,)
                elif row == 5 and col in (3, 4):
                    px[x, y] = ZONES["face_nose"] + (255,)
    if face == "north" and cube.name == "jaw":
        # vanilla rows 6-7 doubled: the mouth row (columns 1-6), then the chin
        px = img.load()
        for x in range(w):
            for y in range(h):
                if y // 2 == 0 and 1 <= x // 2 <= 6:
                    px[x, y] = ZONES["face_dark"] + (255,)
    return img


def build_atlas(model):
    rects = [((i, f), *face_size(c, f)) for i, c in enumerate(model.cubes) for f in FACES]
    positions, used = pack(rects)
    atlas = Image.new("RGBA", (SIZE, HEIGHT), (0, 0, 0, 0))
    for (i, f), (x, y, w, h) in positions.items():
        patch = paint_face(model.cubes[i], f, w, h)
        # the border repeats the island's edge, so filtering never pulls in a neighbour's colour
        border = patch.resize((w + 2, h + 2), Image.NEAREST)
        atlas.paste(border, (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return atlas, positions, used


def luminance(rgb):
    lin = [((c / 255 + 0.055) / 1.055) ** 2.4 if c / 255 > 0.04045 else c / 255 / 12.92 for c in rgb]
    y = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return 116 * y ** (1 / 3) - 16 if y > 0.008856 else 903.3 * y        # CIE L*, 0..100


def value_report():
    rows = []
    for zone, rgb in ZONES.items():
        h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
        rows.append((zone, rgb, round(luminance(rgb)), round(s, 2)))
    close = [(a, b, round(abs(luminance(ZONES[a]) - luminance(ZONES[b])))) for a, b in NEIGHBOURS
             if abs(luminance(ZONES[a]) - luminance(ZONES[b])) < 12]
    return rows, close


def views():
    """Blender coordinates are blocks with Z up; Volley faces +Y."""
    return [
        {"name": "hero", "location": (7, 9.5, 6), "target": (0, 1.2, 2.2), "scale": 9.5, "player": True},
        {"name": "front", "location": (0, 12, 2.4), "target": (0, 1.2, 2.35), "scale": 7.5, "player": False},
        {"name": "player_eye", "location": (-4, 9, 1.62), "target": (0, 1.2, 2.3), "scale": 7.5, "player": False},
        {"name": "side", "location": (11, 1.2, 2.4), "target": (0, 1.2, 2.4), "scale": 8, "player": False},
        {"name": "back", "location": (3, -9, 5.5), "target": (0, 0.6, 2.6), "scale": 7.5, "player": False},
        {"name": "face", "location": (0, 9, 2.9), "target": (0, 1.9, 2.9), "scale": 2.6, "player": False},
    ]


def render(model, bb, atlas_path, out):
    out.mkdir(parents=True, exist_ok=True)
    boxes = [{"corners": c.corners().tolist(), "from": c.frm, "to": c.to, "glow": zone_for(c) == "glow",
              "uv": bb["elements"][i]["faces"]} for i, c in enumerate(model.cubes)]
    job_file = out / "render_job.json"
    job_file.write_text(json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes,
                                    "views": views()}), encoding="utf-8")
    result = subprocess.run([str(BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job_file)],
                            capture_output=True, text=True)
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job_file.unlink()


def review_sheet(out):
    names = [v["name"] for v in views()]
    tw, th, pad, top = 420, 315, 12, 60
    img = Image.new("RGB", (pad + len(names) * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
    from PIL import ImageDraw
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Volley - UV and material zones (session 4): colour, then the grey value check",
            font=sheet._font(28), fill=sheet.INK)
    for r, folder in enumerate(("colour", "grey")):
        for c, name in enumerate(names):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(out / folder / f"{name}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{folder}: {name.replace('_', ' ')}", font=sheet._font(17), fill=sheet.DIM)
    img.save(out / "sheet.png")


def main():
    model = s2.build()
    model.name = s3.MODEL_ID
    remove_face_insets(model)
    off = check_density(model)
    if off:
        raise SystemExit("faces off the texel grid: " + ", ".join(off))
    atlas, positions, used = build_atlas(model)
    OUT.mkdir(parents=True, exist_ok=True)
    atlas_path = OUT / "occultech_volley.png"
    atlas.save(atlas_path)
    grey = atlas.convert("LA").convert("RGBA")
    grey_path = OUT / "occultech_volley_grey.png"
    grey.save(grey_path)
    atlas.resize((SIZE * 2, HEIGHT * 2), Image.NEAREST).save(OUT / "atlas_preview.png")

    texture = {"name": atlas_path.name, "path": "", "folder": "", "namespace": "", "id": "0", "group": "",
               "width": SIZE, "height": HEIGHT, "uv_width": SIZE, "uv_height": HEIGHT, "particle": False,
               "use_as_default": True, "layers_enabled": False, "render_mode": "default", "render_sides": "auto",
               "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False,
               "visible": True, "internal": True, "saved": False, "uuid": _uuid(s3.MODEL_ID + "/atlas"),
               "source": "data:image/png;base64," + base64.b64encode(atlas_path.read_bytes()).decode()}
    bb = model.to_bbmodel(texture_size=(SIZE, HEIGHT), textures=(texture,))
    for i, element in enumerate(bb["elements"]):
        for f in FACES:
            x, y, w, h = positions[(i, f)]
            element["faces"][f] = {"uv": [x, y, x + w, y + h], "texture": 0}
        if zone_for(model.cubes[i]) == "glow":
            element["light_emission"] = 15
    frm, to = s2.hitbox_bounds(model)
    add_hitbox(bb, frm, to)
    bb["animations"] = [{"uuid": _uuid(f"{s3.MODEL_ID}/anim/{key}"), "name": key, "loop": "hold", "override": False,
                         "length": 0.5, "snapping": 20, "selected": False, "anim_time_update": "", "blend_weight": "",
                         "start_delay": "", "loop_delay": "", "animators": s3.keyframes(model, pose)}
                        for key, pose in s3.POSES.items()]
    path = OUT / f"{s3.MODEL_ID}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)

    render(model, bb, atlas_path, OUT / "colour")
    render(model, bb, grey_path, OUT / "grey")
    review_sheet(OUT)

    rows, close = value_report()
    texels = sum(w * h for (_, _, w, h) in positions.values())
    report = {"atlas": [SIZE, HEIGHT], "rows_used": used, "islands": len(positions), "texels": texels,
              "fill": round(texels / (SIZE * used), 2), "cubes": len(model.cubes),
              "zones": {z: {"rgb": list(rgb), "L": L, "saturation": s} for z, rgb, L, s in rows},
              "neighbours_too_close_in_value": [f"{a}/{b}: {d}" for a, b, d in close]}
    (OUT / "uv_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("rows_used", "islands", "fill", "cubes", "neighbours_too_close_in_value")}))


if __name__ == "__main__":
    main()
