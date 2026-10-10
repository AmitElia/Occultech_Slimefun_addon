"""Paint Volley at approximately vanilla texel density and UV every cube face.

Run after volley_s1.py. Writes one 256x256 PNG and a self-contained, editable .bbmodel.
"""
import base64
import hashlib
import io
import json
import math
import subprocess
import sys
import uuid
import zlib
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses.volley_s1 import build  # noqa: E402
from palettes import RAMPS  # noqa: E402

OUT = ROOT / "docs/art/bosses/volley/overhaul/s1_silhouettes"
SIZE = 256
FACES = ("north", "east", "south", "west", "up", "down")

RAMP = {
    "iron": RAMPS["iron"], "bone": RAMPS["bone"], "chitin": RAMPS["ash"],
    "silk": RAMPS["twine"], "wax": RAMPS["wax"], "glow": RAMPS["ember"],
    "wood": RAMPS["wood"],
}
BASE = {"iron": 2, "bone": 3, "chitin": 2, "silk": 2, "wax": 2, "glow": 4, "wood": 2}


def face_size(cube, face):
    d = [cube.to[i] - cube.frm[i] for i in range(3)]
    pair = (d[0], d[1]) if face in ("north", "south") else ((d[2], d[1]) if face in ("east", "west") else (d[0], d[2]))
    return tuple(max(1, math.ceil(v - 1e-8)) for v in pair)


def material_for(cube):
    if cube.name in ("stock", "trigger_housing"):
        return "wood"
    return cube.mat


def clustered(seed, x, y):
    """One deterministic value per 3x3 pixel cluster; no single-pixel static."""
    n = (seed * 1103515245 + (x // 3) * 741103597 + (y // 3) * 1597334677) & 0xffffffff
    n ^= n >> 13
    n = (n * 1274126177) & 0xffffffff
    return n % 23


def paint_face(cube, face, width, height, index):
    material = material_for(cube)
    ramp = RAMP[material]
    seed = zlib.crc32(f"{cube.name}/{face}/{index}".encode())
    image = Image.new("RGBA", (width, height))
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            if material == "glow":
                # A small hot center, warm edge: emissive source, not a painted world shadow.
                distance = max(abs((x + .5) / width - .5), abs((y + .5) / height - .5))
                level = 5 if distance < .18 else (4 if distance < .36 else 3)
            else:
                level = BASE[material]
                grain = clustered(seed, x, y)
                if grain in (0, 1, 2):
                    level -= 1
                elif grain in (20, 21, 22):
                    level += 1
                # Forms are recessed where plates and folds meet, not globally lit twice.
                if min(x, y, width - 1 - x, height - 1 - y) == 0 and width > 3 and height > 3:
                    level -= 1
                if material == "bone" and (x + seed % 7) % 11 == 0 and y > 1:
                    level -= 1
                if material == "wood" and (y + seed % 5) % 6 == 0:
                    level -= 1
                if material == "silk" and (x + y + seed % 5) % 8 in (0, 1):
                    level += 1
                level = max(0, min(len(ramp) - 1, level))
            pixels[x, y] = ramp[level]
    detail = ImageDraw.Draw(image)
    if face == "north":
        if cube.name == "skull" and width >= 9 and height >= 9:
            # Restrained facial structure; the separate eyes and jaw keep the expression readable.
            shadow, light = ramp[1], ramp[4]
            detail.line([(1, 2), (2, 3), (2, 5)], fill=shadow, width=1)
            detail.line([(width - 2, 2), (width - 3, 3), (width - 3, 5)], fill=shadow, width=1)
            detail.line([(3, height - 3), (width - 4, height - 3)], fill=light, width=1)
        elif cube.name == "breastplate" and width >= 13 and height >= 12:
            muted = RAMP["bone"][2]
            cx = width // 2
            detail.line([(cx - 3, 3), (cx, 7), (cx + 3, 3)], fill=muted, width=1)
            for step in range(3):
                detail.line([(cx - 3 + step * 3, height - 5), (cx - 3 + step * 3, height - 3)],
                            fill=muted, width=1)
        elif cube.name == "coat_body" and width >= 16 and height >= 18:
            detail.line([(3, 2), (5, height - 3)], fill=ramp[1], width=2)
            detail.line([(width - 4, 2), (width - 6, height - 3)], fill=ramp[1], width=2)
        elif cube.name == "mandible" and width >= 7:
            for x in range(1, width - 1, 2):
                detail.point((x, min(height - 1, 1)), fill=ramp[5])
        elif "pauldron" in cube.name and width >= 8 and height >= 6:
            detail.line([(2, 2), (width - 3, 2)], fill=ramp[3], width=1)
            detail.point((2, height - 2), fill=RAMP["bone"][2])
            detail.point((width - 3, height - 2), fill=RAMP["bone"][2])
        elif "greave_face" in cube.name and width >= 5 and height >= 6:
            detail.line([(width // 2, 2), (width // 2, height - 2)], fill=ramp[4], width=1)
        elif cube.name == "central_seal" and width >= 6 and height >= 6:
            accent = RAMPS["ember"][4]
            cx, cy = width // 2, height // 2
            detail.polygon([(cx, 1), (width - 2, cy), (cx, height - 2), (1, cy)], outline=accent)
    return image


def pack(rectangles):
    """Shelf pack all faces, with one duplicated edge pixel of padding."""
    positions = {}
    x = y = row_h = 0
    for key, w, h in sorted(rectangles, key=lambda r: (-r[2], -r[1], r[0])):
        outer_w, outer_h = w + 2, h + 2
        if x + outer_w > SIZE:
            y += row_h
            x = row_h = 0
        if y + outer_h > SIZE:
            raise ValueError(f"Atlas needs more than {SIZE}x{SIZE} pixels")
        positions[key] = (x + 1, y + 1, w, h)
        x += outer_w
        row_h = max(row_h, outer_h)
    return positions, y + row_h


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    model = build()
    rectangles = []
    for i, cube in enumerate(model.cubes):
        for face in FACES:
            w, h = face_size(cube, face)
            rectangles.append(((i, face), w, h))
    positions, used_height = pack(rectangles)
    occupied = set()
    for x, y, w, h in positions.values():
        assert 0 <= x - 1 and x + w < SIZE and 0 <= y - 1 and y + h < SIZE
        for py in range(y - 1, y + h + 1):
            for px in range(x - 1, x + w + 1):
                assert (px, py) not in occupied, "Overlapping face islands"
                occupied.add((px, py))
    atlas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    for i, cube in enumerate(model.cubes):
        for face in FACES:
            x, y, w, h = positions[i, face]
            patch = paint_face(cube, face, w, h, i)
            atlas.paste(patch, (x, y))
            # Copy border texels into the padding to prevent filtering seams.
            atlas.paste(patch.crop((0, 0, w, 1)), (x, y - 1))
            atlas.paste(patch.crop((0, h - 1, w, h)), (x, y + h))
            atlas.paste(patch.crop((0, 0, 1, h)), (x - 1, y))
            atlas.paste(patch.crop((w - 1, 0, w, h)), (x + w, y))
            for dx, dy, sx, sy in ((-1, -1, 0, 0), (w, -1, w - 1, 0),
                                    (-1, h, 0, h - 1), (w, h, w - 1, h - 1)):
                atlas.putpixel((x + dx, y + dy), patch.getpixel((sx, sy)))
    png = OUT / "occultech_volley.png"
    atlas.save(png, optimize=True)
    source = "data:image/png;base64," + base64.b64encode(png.read_bytes()).decode()
    texture = {
        "name": png.name, "path": "", "folder": "", "namespace": "", "id": "0", "group": "",
        "width": SIZE, "height": SIZE, "uv_width": SIZE, "uv_height": SIZE,
        "particle": False, "use_as_default": True, "layers_enabled": False, "sync_to_project": "",
        "render_mode": "default", "render_sides": "auto", "pbr_channel": "color",
        "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False,
        "visible": True, "internal": True, "saved": False,
        "uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, "occultech/volley/atlas")), "source": source,
    }
    bb = model.to_bbmodel(texture_size=(SIZE, SIZE), textures=(texture,))
    for i, element in enumerate(bb["elements"]):
        for face in FACES:
            x, y, w, h = positions[i, face]
            element["faces"][face] = {"uv": [x, y, x + w, y + h], "texture": 0}
        if model.cubes[i].mat == "glow":
            element["light_emission"] = 15
    out_model = OUT / "occultech_volley_humanoid_textured.bbmodel"
    out_model.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    # the copy the plugin ships and installs into BetterModel's models folder
    (ROOT / "src/main/models/occultech_volley.bbmodel").write_bytes(out_model.read_bytes())
    preview = atlas.resize((SIZE * 3, SIZE * 3), Image.Resampling.NEAREST)
    preview.save(OUT / "atlas_preview.png")
    counts = Counter(material_for(c) for c in model.cubes)
    validation = {
        "model": out_model.name, "atlas": png.name, "resolution": [SIZE, SIZE],
        "cuboids": len(model.cubes), "mapped_faces": len(rectangles), "used_height": used_height,
        "materials_by_cuboid": dict(counts), "png_sha256": hashlib.sha256(png.read_bytes()).hexdigest(),
        "embedded_texture_matches_png": base64.b64decode(source.split(",", 1)[1]) == png.read_bytes(),
        "uv_islands_disjoint_and_within_atlas": True,
        "uv_convention": "one texel per model unit, rounded upward for fractional-size blockout pieces",
    }
    (OUT / "texture_validation.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    job = {"texture": str(png), "out": OUT.as_posix(), "boxes": [
        {"corners": cube.corners().tolist(), "from": cube.frm, "to": cube.to,
         "glow": cube.mat == "glow", "uv": bb["elements"][i]["faces"]}
        for i, cube in enumerate(model.cubes)
    ]}
    job_file = OUT / "textured_render_job.json"
    job_file.write_text(json.dumps(job), encoding="utf-8")
    result = subprocess.run([r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe", "-b", "--factory-startup",
                             "--python", str(ROOT / "tools/art/bosskit/blender_texture_render.py"),
                             "--", str(job_file)], capture_output=True, text=True)
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job_file.unlink()
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
