"""The Drowned Elder redesign, session 4: UV and material blocking (plan: docs/art/bosses/drowned_elder/overhaul/plan.md).

Every visible face of the session 3 rig is mapped at one texel per model unit into one atlas, each face a flat colour of
its material zone. The exception is vanilla's Elder Guardian skin (guardian_elder.png from the 26.2 client) on the
head's core, its four plates and its eye: the head is vanilla's GuardianModel at exactly 3x, so the skin goes on at 3
pixels per texel, the same deliberate upscale as the Tempest's and the Choir's vanilla heads. The two side plates share
one set of islands, as do the top and bottom plates (vanilla does the same).

Zones (the head's skin sets the palette):
- plate: the shingles and the tail, the elder's own pale stone-cream, sampled from the skin;
- belly: the bottom shingles, lighter (it's what players see from below);
- seam: the soft body between the shingles, a dark grey-mauve, so each segment reads;
- spike: the elder's violet-navy spikes (head, hood, back), sampled from the skin;
- membrane: the hood's webs, a pale violet-grey;
- fin: the pectoral fins and the fluke, vanilla's brown fin;
- glow: the beam eyes, tier 2's sea glow, full-bright.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the last argument:
python tools/art/bosses/drowned_s4.py <folder>
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
from bosses import drowned_s2 as s2, drowned_s3 as s3  # noqa: E402

OUT = ROOT / "docs/art/bosses/drowned_elder/overhaul/s4_uv"
SIZE = 512
NAME = "occultech_drowned_elder_rig"
K = 3
SKIN = np.array(Image.open(Path(sys.argv[-1]) / "assets/minecraft/textures/entity/guardian/guardian_elder.png")
                .convert("RGBA"))
# vanilla box UVs (GuardianModel, 26.2): part -> (texture offset, box size in texels w, h, d)
SKIN_BOXES = {"head": ((0, 0), (12, 12, 16)), "plate_x": ((0, 28), (2, 12, 12)), "plate_y": ((16, 40), (12, 2, 12)),
              "eye": ((8, 0), (2, 2, 1)), "spike": ((0, 0), (2, 9, 2))}


def skin_mean(part, face):
    u, v, w, h = skin_rect(part, face)
    px = SKIN[v:v + h, u:u + w].reshape(-1, 4)
    px = px[px[:, 3] > 0]
    return tuple(int(c) for c in px[:, :3].mean(0))


OPPOSITE = {"up": "down", "down": "up", "north": "south", "south": "north", "east": "west", "west": "east"}


def _rect(part, face):
    (u, v), (w, h, d) = SKIN_BOXES[part]
    return {"up": (u + d, v, w, d), "down": (u + d + w, v, w, d), "north": (u + d, v + d, w, h),
            "south": (u + 2 * d + w, v + d, w, h), "east": (u, v + d, d, h), "west": (u + d + w, v + d, d, h)}[face]


def skin_rect(part, face):
    """The face's rectangle on vanilla's skin. Vanilla paints only one side of a plate (the other plate is the same box
    mirrored), so a face whose rectangle is empty takes its opposite face's."""
    u, v, w, h = _rect(part, face)
    if SKIN[v:v + h, u:u + w, 3].max() == 0:
        return _rect(part, OPPOSITE[face])
    return u, v, w, h


ZONES = {
    "plate": skin_mean("plate_x", "east"), "belly": (226, 220, 196), "seam": (96, 88, 92),
    "spike": skin_mean("spike", "north"), "membrane": (128, 112, 144), "fin": (136, 112, 128),
    "glow": (110, 232, 206), "eye": skin_mean("eye", "north"), "skin": skin_mean("head", "north"),
}
GLOWING = ("glow",)
NEIGHBOURS = [("plate", "seam"), ("plate", "belly"), ("plate", "spike"), ("seam", "glow"), ("plate", "glow"),
              ("spike", "membrane"), ("plate", "fin"), ("skin", "spike"), ("skin", "membrane"), ("belly", "seam")]
a4.ZONES, a4.GLOWING = ZONES, GLOWING
a4.add_hitbox = lambda bb, *args, **kw: bb


def skin_part(c):
    if c.name == "head":
        return "head"
    if c.name.startswith("plate_x"):
        return "plate_x"
    if c.name.startswith("plate_y"):
        return "plate_y"
    if c.name == "eye":
        return "eye"
    return None


def zone_materials(model):
    for c in model.cubes:
        if c.mat == "hitbox":
            continue
        if skin_part(c):
            c.mat = "skin" if c.name != "eye" else "eye"
        elif c.name.startswith("seg") and "_sh" in c.name:
            c.mat = "belly" if c.name.endswith("_shb") else "plate"
        elif c.name.startswith("seg") and c.name[3:].isdigit():
            c.mat = "seam"
        elif c.name.startswith("tail"):
            c.mat = "plate"
        elif c.mat in ("hide",):
            c.mat = "plate"


def island_keys(model):
    keys = {}
    for i, c in enumerate(model.cubes):
        if c.mat == "hitbox":
            continue
        part = skin_part(c)
        for f in FACES:
            w, h = v4.face_size(c, f)
            if not w or not h or b4.hidden(c, f):
                continue
            if part:                               # vanilla's skin only where the face is its box face at 3x
                _, _, sw, sh = skin_rect(part, f)
                part_f = part if (w, h) == (sw * K, sh * K) else None
            else:
                part_f = None
            keys[(i, f)] = (f"skin:{part_f}", f, w, h, c.mat) if part_f else (c.name, f, w, h, c.mat)
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
            assert (w, h) == (sw * K, sh * K), (key, w, h, sw, sh)
            arr = SKIN[v:v + sh, u:u + sw].copy()
            arr[..., 3] = 255                      # a solid model face must never be see-through
            patch = Image.fromarray(arr.astype("uint8"), "RGBA").resize((w, h), Image.NEAREST)
        else:
            patch = Image.new("RGBA", (w, h), ZONES[key[4]] + (255,))
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return atlas, positions, used, height


# Blender coordinates (blocks, z up); the head faces +y, the body runs back along -y. Orthographic: scale = view width.
VIEWS = [
    {"name": "hero", "location": (16, 9, 10), "target": (0, -6.5, 3.2), "scale": 19.0, "player": True},
    {"name": "side", "location": (28, -6.5, 3.6), "target": (0, -6.5, 3.6), "scale": 21.0, "player": False},
    {"name": "player_eye", "location": (-7, 9, 1.62), "target": (0, -4, 3.4), "scale": 15.0, "player": False},
    {"name": "below", "location": (9, 2, 0.4), "target": (0, -5.0, 3.0), "scale": 17.0, "player": False},
    {"name": "head", "location": (4.5, 8, 5.5), "target": (0, 0.2, 3.6), "scale": 6.5, "player": False},
    {"name": "hood", "location": (-5, -8, 7.5), "target": (0, -0.6, 4.0), "scale": 7.5, "player": False},
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
    bb, culled = a4.textured_bbmodel(model, keys, positions, path, SIZE, height, (),
                                     [(k, (rt, ps)) for k, (rt, ps, _) in poses.items()])
    s3.with_scale(bb, model, poses)
    hit = {c.name for c in model.cubes if c.mat == "hitbox"}
    for e in bb["elements"]:
        if e["name"] in hit:
            e["faces"] = {f: {"uv": [0, 0, 0, 0], "texture": None} for f in e["faces"]}
    p = OUT / f"{NAME}.bbmodel"
    p.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    for folder in (s3.SERVER_MODELS, s3.TEST_MODELS):
        if folder.is_dir():
            shutil.copyfile(p, folder / p.name)
    posed = s3.build("idle")          # same cubes in the same order, swimming
    zone_materials(posed)
    keep = [i for i, c in enumerate(posed.cubes) if c.mat != "hitbox"]
    posed.cubes = [posed.cubes[i] for i in keep]
    bb_shown = dict(bb, elements=[bb["elements"][i] for i in keep])
    for tag, atlas_file in (("colour", path), ("grey", grey_path)):
        a4.render(posed, bb_shown, atlas_file, OUT / tag, VIEWS)
    a4.review_sheet(OUT, "Drowned Elder: UV and material zones (session 4)", VIEWS)
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
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
