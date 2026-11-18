"""The Hollow Warlord (the Headsman), session 4: UV and material blocking (plan: docs/art/bosses/hollow_warlord/overhaul/plan.md).

Every visible face of the session 3 rig is mapped at one texel per model unit into one atlas, each face a flat colour of
its material zone. The exception is vanilla's wither skeleton head (wither_skeleton.png from the 26.2 client) on his
skull and the three taken skulls: 8 texels over 16 units, 2 pixels per texel, the deliberate upscale the other bosses'
vanilla heads use. The four skulls share one set of islands.

Zones (tier 3: blackstone, old wither bone, soul cyan, one crimson accent):
- bone: the wither skeleton's soot-black bone, lighter than the armour so the hollow waist and the limbs read;
- bone_dark: the joints;
- plate / plate_lit: blackstone plate and its polished, bevelled edges (pauldron lames, the hat's band and crown);
- leather_dark, grip: the belt and the sword's wrapped grip;
- cloth / cloth_dark: the tabard in deep nether-wart red, front and back;
- blade, guard: the sword's dark steel and its blackstone guard and pommel;
- socket: the shadow under the hat's brim;
- glowing: soul cyan (eyes, the taken skulls' fire), the crimson brand.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the argument:
python tools/art/bosses/headsman_s4.py <folder>
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
from bosses import headsman_s2 as s2, headsman_s3 as s3, headsman_study as st  # noqa: E402

OUT = ROOT / "docs/art/bosses/hollow_warlord/overhaul/s4_uv"
SIZE = 512
NAME = "occultech_hollow_warlord_rig"
SKIN = None
SKIN_BOXES = {"skull": ((0, 0), (8, 8, 8))}
ZONES = {
    "skin": (28, 28, 29),        # the vanilla wither skin's mean value (L 10); the skulls carry the real pixels
    "bone": (45, 46, 46), "bone_dark": (31, 31, 31),
    "plate": (70, 73, 74), "plate_lit": (100, 104, 105),
    "leather_dark": (70, 73, 74), "grip": (30, 30, 32),
    "cloth": (20, 20, 22), "cloth_dark": (16, 16, 18),
    "blade": (120, 124, 126), "guard": (70, 73, 74),
    "socket": (12, 12, 14),
    "soul": (92, 232, 240), "flame": (120, 240, 246), "brand": (92, 232, 240),
}
GLOWING = ("soul", "flame", "brand")
NEIGHBOURS = [("bone", "plate"), ("plate", "plate_lit"), ("cloth", "plate"), ("cloth", "bone"),
              ("blade", "guard"), ("skin", "plate"), ("skin", "plate_lit"), ("grip", "guard"), ("bone_dark", "plate")]
a4.ZONES, a4.GLOWING = ZONES, GLOWING


def skin_part(c):
    return "skull" if c.mat in ("skull", "trophy") else None


def skin_rect(part, face):
    (u, v), (w, h, d) = SKIN_BOXES[part]
    return {"up": (u + d, v, w, d), "down": (u + d + w, v, w, d), "north": (u + d, v + d, w, h),
            "south": (u + 2 * d + w, v + d, w, h), "east": (u, v + d, d, h), "west": (u + d + w, v + d, d, h)}[face]


def zone_materials(model):
    for c in model.cubes:
        if c.mat == "px_5aecf4":
            c.mat = "soul"


def island_keys(model):
    keys = {}
    for i, c in enumerate(model.cubes):
        part = skin_part(c)
        for f in FACES:
            w, h = v4.face_size(c, f)
            if not w or not h or b4.hidden(c, f):
                continue
            keys[(i, f)] = (f"skin:{part}", f, w, h, "skin") if part else (c.name, f, w, h, c.mat)
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
            arr = SKIN[v:v + sh, u:u + sw].copy()
            arr[..., 3] = 255                    # a solid model face is never see-through
            patch = Image.fromarray(arr.astype("uint8"), "RGBA").resize((w, h), Image.NEAREST)
        else:
            patch = Image.new("RGBA", (w, h), ZONES[key[4]] + (255,))
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return atlas, positions, used, height


# Blender coordinates (blocks, z up); he faces +y
VIEWS = [
    {"name": "hero", "location": (-9, 13, 6), "target": (0, 0, 3.9), "scale": 11.0, "player": True},
    {"name": "front", "location": (0, 18, 3.8), "target": (0, 0, 3.8), "scale": 11.5, "player": False},
    {"name": "player_eye", "location": (4.0, 11, 1.62), "target": (0, 0, 3.4), "scale": 12.0, "player": False},
    {"name": "side", "location": (18, 0, 3.8), "target": (0, 0, 3.8), "scale": 11.5, "player": False},
    {"name": "back", "location": (-8, -15, 6), "target": (0, 0, 4.0), "scale": 10.5, "player": False},
    {"name": "face", "location": (-1.6, 9, 5.0), "target": (0, 0.6, 4.7), "scale": 4.2, "player": False},
]


def main(argv):
    global SKIN
    st.SKIN = Image.open(Path(argv[0]) / "assets/minecraft/textures/entity/skeleton/wither_skeleton.png").convert("RGBA")
    SKIN = np.array(st.SKIN)
    OUT.mkdir(parents=True, exist_ok=True)
    s2.PALETTE.update(ZONES)
    s3.a2.PALETTE = dict(s2.PALETTE)
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
    hitbox = s2.hitbox_bounds(s2.pose(s2.rig(), "idle"))
    bb, culled = a4.textured_bbmodel(model, keys, positions, path, SIZE, height, hitbox, list(poses.items()))
    p = OUT / f"{NAME}.bbmodel"
    p.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if "--server" in argv and s3.SERVER_MODELS.is_dir():
        shutil.copyfile(p, s3.SERVER_MODELS / p.name)
    posed = s3.posed("idle")                       # the same cubes in the same order, in the idle pose
    zone_materials(posed)
    for tag, atlas_file in (("colour", path), ("grey", grey_path)):
        a4.render(posed, bb, atlas_file, OUT / tag, VIEWS)
    a4.review_sheet(OUT, "Hollow Warlord: UV and material zones (session 4)", VIEWS)
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
    main(sys.argv[1:])
