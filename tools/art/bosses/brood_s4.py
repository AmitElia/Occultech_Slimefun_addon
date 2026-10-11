"""Brood Mother redesign, session 4: UV and material blocking.

On top of the session 3 rig, this session:
- maps every visible cube face at one texel per model unit (16 per block, the vanilla density) into one packed atlas,
  with a 1-pixel border on each island against seams;
- leaves out faces buried inside another cube of the same bone (they can never be seen);
- shares texture space only where parts are truly identical: a left leg segment with its right twin (both are built
  along +X and only yawed apart), hair cards of one size (both sides of a card, and every card that size), and upright candles, wicks and
  flames of one size;
- moves the red eyes into their own glow bone: vanilla spider eyes glow in the dark, and so do hers;
- fills each material zone with one flat colour; renders the result in colour and in grey (the value check) and lists
  every zone's value;
- updates the in-game review model `occultech_brood_mother_rig`, so the pixel size can be judged in game.

Session 5 paints over this atlas (and gives the hair strips their alpha). Run from the repository root:
python tools/art/bosses/brood_s4.py
"""
import base64
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, _uuid, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import brood_s2 as s2, brood_s3 as s3, volley_crone_s3 as v3, volley_crone_s4 as v4  # noqa: E402

OUT = ROOT / "docs/art/bosses/brood_mother/overhaul/s4_uv"
SIZE = 256
EYES = ("eye_v_", "eye_mutant")
GLOW_ZONES = ("flame", "eye", "eye_small")

# One flat colour per zone. The body is the vanilla spider's warm near-black; the hair a lighter dusty brown; the wax
# honey but muted, so the only saturated colours are the lights: the red eyes and the flames.
ZONES = {
    "chitin": (52, 44, 42),
    "chitin_lit": (83, 71, 68),      # knuckles, humps, swelling: a step up
    "plate": (117, 103, 96),          # the flank and carapace plates: one more step
    "hair": (163, 132, 106),          # tarantula fur, lighter than any chitin; tips go gold in session 5
    "mandible": (26, 12, 16),        # glossy near-black jaws, darker than the body, under bone fangs
    "fang": (214, 198, 166),
    "eye": (232, 44, 44),            # vanilla's spider red, glowing
    "eye_small": (190, 30, 40),
    "wax": (212, 167, 115),
    "wax_old": (118, 81, 54),        # older, darker wax at the foot of the pile
    "candle": (236, 222, 190),
    "wick": (30, 24, 28),
    "flame": (255, 168, 58),
}
NEIGHBOURS = [("chitin", "chitin_lit"), ("chitin", "plate"), ("chitin_lit", "plate"), ("chitin", "hair"),
              ("chitin_lit", "hair"), ("chitin", "wax"), ("chitin", "wax_old"), ("hair", "wax_old"), ("wax", "wax_old"),
              ("wax", "candle"), ("candle", "flame"), ("candle", "wick"), ("chitin", "mandible"), ("mandible", "fang"),
              ("chitin", "eye"), ("chitin", "eye_small"), ("chitin_lit", "mandible")]
QUAD_AXIS = {"north": (2, 0), "south": (2, 1), "west": (0, 0), "east": (0, 1), "down": (1, 0), "up": (1, 1)}


def glowing_eyes(model):
    """The eye cubes move from the head bone into their own glow bone under it, pivoting on the face."""
    head = next(g for g in model.groups if g.name == "h_head")
    eyes = [c for c in head.children if not hasattr(c, "children") and c.name.startswith(EYES)]
    lo = np.min([c.frm for c in eyes], 0)
    hi = np.max([c.to for c in eyes], 0)
    glow = head.group("glow_eyes", ((lo + hi) / 2).tolist())
    for c in eyes:
        head.children.remove(c)
        glow.children.append(c)
        c.group = glow
    return model


def rig():
    model = glowing_eyes(s3.rigged())
    model.name = s3.MODEL_ID
    return model


def _flat(c):
    return all(v == 0 for v in c.rotation)


def hidden(cube, face):
    """True if the whole face lies strictly inside other unrotated cubes of the same bone: nothing can ever see it."""
    if not _flat(cube) or cube.mat == "hair":
        return False
    others = [o for o in cube.group.children
              if not hasattr(o, "children") and o is not cube and _flat(o) and o.mat != "hair"]
    ax, side = QUAD_AXIS[face]
    lo, hi = np.array(cube.frm), np.array(cube.to)
    a_, b_ = [i for i in range(3) if i != ax]
    for a in np.linspace(0.05, 0.95, 5):
        for b in np.linspace(0.05, 0.95, 5):
            p = lo.copy()
            p[ax] = hi[ax] if side else lo[ax]
            p[a_] = lo[a_] + a * (hi[a_] - lo[a_])
            p[b_] = lo[b_] + b * (hi[b_] - lo[b_])
            if not any(all(o.frm[i] + 1e-6 < p[i] < o.to[i] - 1e-6 for i in range(3)) for o in others):
                return False
    return True


def island_keys(model):
    """The atlas island each visible face uses. Hair cards share one island per size; a left leg cube shares its right
    twin's islands (the legs are built along +X and only yawed apart, so the faces match exactly); upright candle
    parts of one size share theirs."""
    names = {c.name: c for c in model.cubes}
    keys = {}
    for i, c in enumerate(model.cubes):
        for f in FACES:
            w, h = v4.face_size(c, f)
            if not w or not h or hidden(c, f):
                continue
            if c.mat == "hair":
                keys[(i, f)] = ("hair", w, h)
            elif c.mat in ("candle", "wick", "flame") and _flat(c):
                keys[(i, f)] = (c.mat, w, h, f)
            elif c.name.startswith("leg_l") and names.get("leg_r" + c.name[5:]) is not None \
                    and v4.face_size(names["leg_r" + c.name[5:]], f) == (w, h):
                keys[(i, f)] = ("cube", "leg_r" + c.name[5:], f)
            else:
                keys[(i, f)] = ("cube", c.name, f)
    return keys


def pack(sizes):
    """Skyline packing, tallest first: each island (with its 1-pixel border) goes where its top ends lowest. The atlas
    grows in powers of two."""
    order = sorted(sizes.items(), key=lambda kv: (-kv[1][1], -kv[1][0], str(kv[0])))
    sky = np.zeros(SIZE, int)
    positions = {}
    for key, (w, h) in order:
        bw, bh = w + 2, h + 2
        tops = np.array([sky[x:x + bw].max() for x in range(SIZE - bw + 1)])
        waste = np.array([(tops[x] - sky[x:x + bw]).sum() for x in range(SIZE - bw + 1)])
        x = int(np.lexsort((waste, tops))[0])
        y = int(tops[x])
        sky[x:x + bw] = y + bh
        positions[key] = (x + 1, y + 1, w, h)
    used = int(sky.max())
    height = SIZE
    while height < used:
        height *= 2
    return positions, used, height


def build_atlas(model, keys):
    sizes = {}
    for (i, f), key in keys.items():
        sizes[key] = v4.face_size(model.cubes[i], f)
    positions, used, height = pack(sizes)
    owner = {}
    for (i, f), key in keys.items():
        owner.setdefault(key, model.cubes[i].mat)
    atlas = Image.new("RGBA", (SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        patch = Image.new("RGBA", (w, h), ZONES[owner[key]] + (255,))
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return atlas, positions, used, height


def value_report():
    rows = [(z, rgb, round(v4.luminance(rgb)), round(max(rgb) and (max(rgb) - min(rgb)) / max(rgb), 2))
            for z, rgb in ZONES.items()]
    close = [(a, b, round(abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])))) for a, b in NEIGHBOURS
             if abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])) < 12]
    return rows, close


def views():
    """Blender coordinates are blocks with Z up; she faces +Y. The scale figure stands clear of her legs."""
    return [
        {"name": "hero", "location": (10, 11, 7.5), "target": (0, -0.2, 1.3), "scale": 12, "player": True},
        {"name": "front", "location": (0, 14, 1.6), "target": (0, 0, 1.6), "scale": 9.5, "player": False},
        {"name": "player_eye", "location": (-5, 9, 1.62), "target": (0, 0, 1.3), "scale": 9.5, "player": False},
        {"name": "side", "location": (14, -0.4, 1.9), "target": (0, -0.4, 1.9), "scale": 9.5, "player": False},
        {"name": "back", "location": (5, -13, 6.5), "target": (0, -1.2, 2.0), "scale": 9.5, "player": False},
        {"name": "face", "location": (1.2, 7, 1.3), "target": (0, 1.4, 1.0), "scale": 3.4, "player": False},
    ]


def render(model, bb, atlas_path, out, view_list=None):
    out.mkdir(parents=True, exist_ok=True)
    boxes = [{"corners": c.corners().tolist(), "from": c.frm, "to": c.to, "glow": c.mat in GLOW_ZONES,
              "uv": bb["elements"][i]["faces"]} for i, c in enumerate(model.cubes)]
    job_file = out / "render_job.json"
    job_file.write_text(json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes,
                                    "views": view_list or views(), "player_at": (5.5, 2.5)}), encoding="utf-8")
    import subprocess
    result = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job_file)],
                            capture_output=True, text=True)
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job_file.unlink()


def review_sheet(out):
    names = [v["name"] for v in views()]
    tw, th, pad, top = 420, 315, 12, 60
    img = Image.new("RGB", (pad + len(names) * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Brood Mother - UV and material zones (session 4): colour, then the grey value check",
            font=sheet._font(28), fill=sheet.INK)
    for r, folder in enumerate(("colour", "grey")):
        for c, name in enumerate(names):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(out / folder / f"{name}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), f"{folder}: {name.replace('_', ' ')}", font=sheet._font(17), fill=sheet.DIM)
    img.save(out / "sheet.png")


def main():
    model = rig()
    off = v4.check_density(model)
    if off:
        raise SystemExit("faces off the texel grid: " + ", ".join(off))
    keys = island_keys(model)
    atlas, positions, used, height = build_atlas(model, keys)
    OUT.mkdir(parents=True, exist_ok=True)
    atlas_path = OUT / "occultech_brood_mother.png"
    atlas.save(atlas_path)
    grey_path = OUT / "occultech_brood_mother_grey.png"
    atlas.convert("LA").convert("RGBA").save(grey_path)
    atlas.resize((SIZE * 2, height * 2), Image.NEAREST).save(OUT / "atlas_preview.png")

    texture = {"name": atlas_path.name, "path": "", "folder": "", "namespace": "", "id": "0", "group": "",
               "width": SIZE, "height": height, "uv_width": SIZE, "uv_height": height, "particle": False,
               "use_as_default": True, "layers_enabled": False, "render_mode": "default", "render_sides": "auto",
               "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False,
               "visible": True, "internal": True, "saved": False, "uuid": _uuid(s3.MODEL_ID + "/atlas"),
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
        if model.cubes[i].mat in GLOW_ZONES:
            element["light_emission"] = 15
    frm, to = s2.hitbox_bounds(model)
    add_hitbox(bb, frm, to)
    poses = s3.pose_table()
    bb["animations"] = [{"uuid": _uuid(f"{s3.MODEL_ID}/anim/{key}"), "name": key, "loop": "hold", "override": False,
                         "length": 0.5, "snapping": 20, "selected": False, "anim_time_update": "", "blend_weight": "",
                         "start_delay": "", "loop_delay": "", "animators": v3.keyframes(model, pose)}
                        for key, pose in poses.items()]
    path = OUT / f"{s3.MODEL_ID}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)

    render(model, bb, atlas_path, OUT / "colour")
    render(model, bb, grey_path, OUT / "grey")
    review_sheet(OUT)

    rows, close = value_report()
    texels = sum(w * h for (_, _, w, h) in positions.values())
    report = {"atlas": [SIZE, height], "rows_used": used, "islands": len(positions), "faces_drawn": len(keys),
              "faces_buried_and_left_out": culled, "texels": texels, "fill": round(texels / (SIZE * used), 2),
              "cubes": len(model.cubes),
              "zones": {z: {"rgb": list(rgb), "L": L, "saturation": s} for z, rgb, L, s in rows},
              "neighbours_too_close_in_value": [f"{a}/{b}: {d}" for a, b, d in close]}
    (OUT / "uv_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("atlas", "rows_used", "islands", "faces_drawn", "faces_buried_and_left_out",
                                             "fill", "neighbours_too_close_in_value")}))


if __name__ == "__main__":
    main()
