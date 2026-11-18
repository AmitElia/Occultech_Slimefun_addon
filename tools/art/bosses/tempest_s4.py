"""The Tempest redesign, session 4: UV and material blocking (plan: docs/art/bosses/tempest/overhaul/plan.md).

Every visible face of the session 3 rig is mapped at one texel per model unit into one atlas, each face a flat colour of
its material zone. The exceptions are vanilla's breeze skin (breeze.png from the 26.2 client) on the head (8 texels shown
over 32 units, 4 pixels per texel), the visor band (its wraparound V eyes included) and the three rods (3 pixels per
texel), the same deliberate upscale the Blaze Choir's heads use. The three rods share one set of islands.

Zones:
- the seal: pale carved stone, a darker rim;
- the circlet: older, darker weathered stone, so it parts from the breeze skin it sits on;
- the heavy core: dark steel;
- the wind: pale lavender-white bands and a darker blue-violet, alternating;
- glowing: the heart and the glyphs in tier 2's sea teal, the eyes white.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the last argument:
python tools/art/bosses/tempest_s4.py <folder>
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES  # noqa: E402
from bosses import archevoker_s4 as a4, brood_s4 as b4, volley_crone_s4 as v4  # noqa: E402
from bosses import tempest_s2 as s2, tempest_s3 as s3  # noqa: E402

OUT = ROOT / "docs/art/bosses/tempest/overhaul/s4_uv"
SIZE = 512
NAME = "occultech_tempest_rig"
SKIN = np.array(Image.open(Path(sys.argv[-1]) / "assets/minecraft/textures/entity/breeze/breeze.png").convert("RGBA"))
# vanilla box UVs: part -> (texture offset, box size in texels w, h, d); east/west as the Choir's blaze head (checked in game)
SKIN_BOXES = {"skull": ((0, 0), (8, 8, 8)), "visor": ((4, 24), (10, 3, 4)), "rod": ((0, 17), (2, 8, 2))}
ZONES = {
    "breeze": (171, 156, 203), "breeze_dark": (87, 108, 157), "rod": (122, 130, 196), "eye": (243, 245, 255), "eye_gold": (249, 213, 100),
    "stone": (196, 188, 168), "stone_dark": (106, 100, 92), "stone_aged": (72, 68, 66),
    "steel": (78, 82, 89), "recess": (30, 34, 40), "core_glow": (86, 232, 208), "glyph": (120, 250, 226),
    "wind": (222, 232, 250), "wind_dark": (128, 140, 196),
}
GLOWING = ("core_glow", "glyph", "eye", "eye_gold")
NEIGHBOURS = [("stone", "stone_dark"), ("stone", "glyph"), ("stone", "wind"), ("stone", "wind_dark"), ("stone_aged", "breeze"),
              ("stone_aged", "breeze_dark"), ("stone_aged", "glyph"), ("steel", "core_glow"), ("steel", "wind"),
              ("wind", "wind_dark"), ("breeze", "steel"), ("stone_dark", "wind_dark"), ("rod", "wind")]
a4.ZONES, a4.GLOWING = ZONES, GLOWING


def skin_part(name):
    if name in ("skull", "visor"):
        return name
    if name.startswith("rod") and name[3:].isdigit():
        return "rod"
    return None


def skin_rect(part, face):
    (u, v), (w, h, d) = SKIN_BOXES[part]
    return {"up": (u + d, v, w, d), "down": (u + d + w, v, w, d), "north": (u + d, v + d, w, h),
            "south": (u + 2 * d + w, v + d, w, h), "east": (u, v + d, d, h), "west": (u + d + w, v + d, d, h)}[face]


def zone_materials(model):
    for c in model.cubes:
        if c.name.startswith("circ_"):
            c.mat = "stone_aged" if "glyph" not in c.name else c.mat


def island_keys(model):
    keys = {}
    for i, c in enumerate(model.cubes):
        part = skin_part(c.name)
        for f in FACES:
            w, h = v4.face_size(c, f)
            if not w or not h or b4.hidden(c, f):
                continue
            keys[(i, f)] = (f"skin:{part}", f, w, h, c.mat) if part else (c.name, f, w, h, c.mat)
    return keys


def build_atlas(keys):
    b4.SIZE = SIZE
    positions, used, _ = b4.pack({k: (k[2], k[3]) for k in keys.values()})
    height = 16
    while height < used:
        height *= 2
    atlas = Image.new("RGBA", (SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        if key[0].startswith("skin:"):
            u, v, sw, sh = skin_rect(key[0][5:], key[1])
            patch = Image.fromarray(SKIN[v:v + sh, u:u + sw].astype("uint8"), "RGBA").resize((w, h), Image.NEAREST)
            # vanilla leaves a few skin texels clear; a solid model face must never be see-through
            arr = np.array(patch)
            arr[..., 3] = 255
            patch = Image.fromarray(arr, "RGBA")
        else:
            patch = Image.new("RGBA", (w, h), ZONES[key[4]] + (255,))
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return atlas, positions, used, height


VIEWS = [
    {"name": "hero", "location": (11, 15, 8), "target": (0, 0, 4.3), "scale": 12.0, "player": True},
    {"name": "front", "location": (0, 18, 4.4), "target": (0, 0, 4.4), "scale": 10.5, "player": False},
    {"name": "player_eye", "location": (-4.5, 10, 1.62), "target": (0, 0, 4.0), "scale": 11.0, "player": False},
    {"name": "back", "location": (8, -16, 7), "target": (0, 0, 4.3), "scale": 11.0, "player": False},
    {"name": "face", "location": (2.0, 10, 7.0), "target": (0, 0, 6.3), "scale": 4.2, "player": False},
    {"name": "heart", "location": (3.0, 10, 4.9), "target": (0, 0, 4.4), "scale": 4.6, "player": False},
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s2.PALETTE.update(ZONES)
    model = s3.rest_model()
    zone_materials(model)
    off = v4.check_density(model)
    if off:
        raise SystemExit("faces off the texel grid: " + ", ".join(off[:10]))
    model.name = NAME
    keys = island_keys(model)
    atlas, positions, used, height = build_atlas(keys)
    path = OUT / f"{NAME}.png"
    atlas.save(path)
    grey_path = OUT / f"{NAME}_grey.png"
    r = np.array(atlas)
    g = (r[..., :3] @ (0.2126, 0.7152, 0.0722)).astype("uint8")
    r[..., 0] = r[..., 1] = r[..., 2] = g
    Image.fromarray(r, "RGBA").save(grey_path)
    poses = s3.pose_table(s3.rest_model())
    bb, culled = a4.textured_bbmodel(model, keys, positions, path, SIZE, height, s2.HITBOX,
                                     [(k, (rt, ps)) for k, (rt, ps, _) in poses.items()])
    s3.with_scale(bb, model, poses)
    p = OUT / f"{NAME}.bbmodel"
    p.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    for folder in (s3.SERVER_MODELS, s3.TEST_MODELS):
        if folder.is_dir():
            shutil.copyfile(p, folder / p.name)
    posed = s3.build("idle")          # same cubes in the same order, in the frozen blast
    zone_materials(posed)
    for tag, atlas_file in (("colour", path), ("grey", grey_path)):
        a4.render(posed, bb, atlas_file, OUT / tag, VIEWS)
    a4.review_sheet(OUT, "Tempest: UV and material zones (session 4)", VIEWS)
    texels = sum(w * h for (_, _, w, h) in positions.values())
    close = [f"{a}/{b}: {abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])):.0f}" for a, b in NEIGHBOURS
             if abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])) < 12]
    alpha = np.array(atlas)[..., 3]
    report = {"atlas": [SIZE, height], "rows_used": used, "islands": len(positions), "faces_drawn": len(keys),
              "faces_buried_and_left_out": culled, "fill": round(texels / (SIZE * used), 2),
              "half_clear_texels": int(((alpha > 0) & (alpha < 255)).sum()),
              "neighbours_too_close_in_value": close,
              "zones": {z: [list(v), round(v4.luminance(v))] for z, v in ZONES.items()}}
    (OUT / "uv_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "zones"}, indent=1))


if __name__ == "__main__":
    main()
