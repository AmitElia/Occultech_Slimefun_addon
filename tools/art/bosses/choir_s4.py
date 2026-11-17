"""The Blaze Choir redesign, session 4: UV and material blocking (plan: docs/art/bosses/blaze_choir/overhaul/plan.md).

Every visible face of the session 3 rigs is mapped at one texel per model unit into one atlas per singer, each face a
flat colour of its material zone. Left parts share their right twin's islands. The head carries vanilla's blaze skin
already: its 8 texels upscaled to the head's 16 (Soprano) or 24 (Alto, Bass) units, whole pixels per texel.

Zones: the Soprano and the Alto are dull, heat-stained brass; the Bass's bell is darker bell bronze, its wheel dark oak;
red cord and the Alto's cap are the one liturgical accent; the fire and the singing mouths glow.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the last argument:
python tools/art/bosses/choir_s4.py <folder>
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
from bosses import archevoker_s4 as a4, brood_s4 as b4, choir_s2 as s2, choir_s3 as s3, volley_crone_s4 as v4  # noqa: E402
from bosses.archevoker_s2 import subtree  # noqa: E402

OUT = ROOT / "docs/art/bosses/blaze_choir/overhaul/s4_uv"
SIZE = 512
SKIN = np.array(Image.open(Path(sys.argv[-1]) / "assets/minecraft/textures/entity/blaze/blaze.png").convert("RGBA"))
UV_SKIN = {"north": (8, 8), "east": (0, 8), "west": (16, 8), "south": (24, 8), "up": (8, 0), "down": (16, 0)}
ZONES = {
    "brass": (188, 150, 88), "brass_dark": (96, 70, 46), "inside": (46, 32, 30),
    "bronze": (138, 94, 58), "bronze_dark": (84, 56, 40), "wood": (54, 38, 30),
    "cord": (204, 62, 54), "blaze": (236, 176, 60),
    "white_fire": (255, 244, 214), "fire": (255, 164, 64), "red_fire": (236, 84, 44), "mouth": (255, 196, 70),
}
GLOWING = ("white_fire", "fire", "red_fire", "mouth")
NEIGHBOURS = [("brass", "brass_dark"), ("brass", "inside"), ("brass", "cord"), ("bronze", "bronze_dark"), ("wood", "cord"),
              ("wood", "brass_dark"), ("bronze", "inside"), ("brass_dark", "cord"), ("bronze", "wood")]
FULL_BRIGHT = GLOWING + ("blaze",)   # vanilla draws a blaze full-bright: the head never darkens (not tinted)
a4.ZONES, a4.GLOWING = ZONES, FULL_BRIGHT
HEAD_Z = {"soprano": 5.0, "alto": 4.3, "bass": 3.9}
WIDE = {"soprano": 8.5, "alto": 10.5, "bass": 8.5}


def views(singer):
    hz, w = HEAD_Z[singer], WIDE[singer]
    return [
        {"name": "hero", "location": (7, 11, 6), "target": (0, 0, 3.4), "scale": w, "player": True},
        {"name": "player_eye", "location": (-4.5, 9, 1.62), "target": (0, 0, 3.4), "scale": w, "player": False},
        {"name": "back", "location": (6, -11, 6), "target": (0, 0, 3.4), "scale": w, "player": False},
        {"name": "head", "location": (1.8, 8, hz + 0.8), "target": (0, 0, hz), "scale": 3.4, "player": False},
    ]


def bell_bronze(model):
    """The Bass's bell is bell bronze, darker than the brass of its yoke and the other two singers."""
    bell = next((g for g in model.groups if g.name == "bell"), None)
    if bell is None:
        return
    ids = set(map(id, subtree(bell)))
    for c in model.cubes:
        if id(c.group) in ids and c.mat in ("brass", "brass_dark"):
            c.mat = "bronze" if c.mat == "brass" else "bronze_dark"


def island_keys(model):
    names = {c.name: c for c in model.cubes}
    keys = {}
    for i, c in enumerate(model.cubes):
        for f in FACES:
            w, h = v4.face_size(c, f)
            if not w or not h or b4.hidden(c, f):
                continue
            if c.name == "head":
                keys[(i, f)] = ("head", f, w, h, c.mat)
                continue
            t = a4.twin(c.name)
            same = t != c.name and t in names and v4.face_size(names[t], f) == (w, h) and names[t].mat == c.mat
            keys[(i, f)] = (t if same else c.name, f, w, h, c.mat)
    return keys


def build_atlas(keys):
    b4.SIZE = SIZE
    positions, used, _ = b4.pack({k: (k[2], k[3]) for k in keys.values()})
    height = 16
    while height < used:
        height *= 2
    atlas = Image.new("RGBA", (SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        patch = Image.new("RGBA", (w, h), ZONES[key[4]] + (255,))
        if key[0] == "head":
            u, v = UV_SKIN[key[1]]
            patch = Image.fromarray(SKIN[v:v + 8, u:u + 8].astype("uint8"), "RGBA").resize((w, h), Image.NEAREST)
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return atlas, positions, used, height


def grey(src, dst):
    r = np.array(Image.open(src))
    g = (r[..., :3] @ (0.2126, 0.7152, 0.0722)).astype("uint8")
    r[..., 0] = r[..., 1] = r[..., 2] = g
    Image.fromarray(r, "RGBA").save(dst)


def model_pass(singer):
    model = s3.build(singer, "idle")
    bell_bronze(model)
    off = v4.check_density(model)
    if off:
        raise SystemExit("faces off the texel grid: " + ", ".join(off[:10]))
    name = s3.rig_id(singer)
    model.name = name
    keys = island_keys(model)
    atlas, positions, used, height = build_atlas(keys)
    path = OUT / f"{name}.png"
    atlas.save(path)
    grey(path, OUT / f"{name}_grey.png")
    bb, culled = a4.textured_bbmodel(model, keys, positions, path, SIZE, height, s2.HITBOX[singer], s3.pose_table(singer).items())
    p = OUT / f"{name}.bbmodel"
    p.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(p, s3.SERVER_MODELS / p.name)
    for tag, atlas_file in (("colour", path), ("grey", OUT / f"{name}_grey.png")):
        a4.render(model, bb, atlas_file, OUT / f"{tag}_{singer}", views(singer))
    texels = sum(w * h for (_, _, w, h) in positions.values())
    return {"atlas": [SIZE, height], "islands": len(positions), "faces_drawn": len(keys), "faces_buried_and_left_out": culled,
            "fill": round(texels / (SIZE * used), 2)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {s: model_pass(s) for s in s2.RIGS}
    rows = []
    for s in s2.RIGS:
        rows += [(f"colour_{s}", f"{s}"), (f"grey_{s}", f"{s}, grey")]
    a4.review_sheet(OUT, "The Blaze Choir: UV and material zones (session 4)", views("soprano"), rows=rows)
    close = [f"{a}/{b}: {abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])):.0f}" for a, b in NEIGHBOURS
             if abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])) < 12]
    report["neighbours_too_close_in_value"] = close
    report["zones"] = {z: [list(v), round(v4.luminance(v))] for z, v in ZONES.items()}
    (OUT / "uv_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
