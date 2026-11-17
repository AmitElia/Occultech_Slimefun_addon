"""The Tidebreaker redesign, session 4: UV and material blocking (plan: docs/art/bosses/tidebreaker/overhaul/plan.md).

Every visible face of the session 3 rigs is mapped at one texel per model unit into one atlas per model, each face a
flat colour of its material zone. Left parts share their right twin's islands. Two documented exceptions:
- the head is painted at 24 x 24 on its 12-unit faces: three pixels per skin texel, so the vanilla zombie stays crisp.
  It carries the real 26.2 skin already.
- the barnacles keep their half-texel sizes, so a face may be half a unit wide on one pixel.
The net is cut out (alpha 0 or 255), since a solid sheet would hide the shell.

Run from the repository root, with a folder holding the 26.2 zombie textures as the last argument:
python tools/art/bosses/tide_s4.py <folder>
"""
import json
import math
import re
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES  # noqa: E402
from bosses import archevoker_s4 as a4, brood_s4 as b4, tide_s2 as s2, tide_s3 as s3, volley_crone_s4 as v4  # noqa: E402

OUT = ROOT / "docs/art/bosses/tidebreaker/overhaul/s4_uv"
SIZE = 512
SKIN = np.array(Image.open(s2.tf2.SKINS / "zombie.png").convert("RGBA"))
SKIN_MEAN = tuple(int(v) for v in np.median(SKIN[8:16, 8:16, :3].reshape(-1, 3), axis=0))
ZONES = {k: tuple(v[:3]) for k, v in {**s2.PALETTE, **s2.tf2.PAL}.items()}
ZONES.update({
    # the nautilus: vanilla's cream shell and red tiger stripes
    "shell": (222, 206, 176), "shell_in": (146, 124, 104), "stripe": (164, 70, 50), "nacre": (198, 208, 216),
    "body": (150, 58, 48), "hood": (84, 40, 38), "tentacle": (196, 98, 76), "naut_eye": (220, 184, 104), "pupil": (18, 18, 24),
    # the longship: tarred, sea-worn spruce, iron, hemp; flaking paint
    "wood": (106, 96, 84), "wood_dark": (62, 54, 50), "iron": (62, 64, 74), "iron_light": (118, 120, 128),
    "rope": (164, 138, 94), "net": (150, 128, 90), "paint_white": (206, 198, 178), "paint_red": (118, 38, 34),
    "tooth": (208, 198, 170), "glow": (255, 214, 110),
    # the Viking: the zombie's own green, torn leather, an old fur, ox horn
    "skin": SKIN_MEAN, "skin_dark": tuple(int(v * 0.72) for v in SKIN_MEAN), "leather": (92, 60, 42),
    "leather_dark": (52, 36, 30), "fur": (132, 118, 100), "b_mid": (146, 146, 124), "b_dark": (126, 128, 108), "horn": (206, 190, 156),
})
GLOWING = ("glow",)
NEIGHBOURS = [("shell", "stripe"), ("shell", "wood"), ("shell", "shell_in"), ("wood", "wood_dark"), ("wood", "paint_red"),
              ("paint_white", "paint_red"), ("wood", "iron"), ("wood", "rope"), ("body", "hood"), ("tentacle", "body"),
              ("leather", "skin"), ("leather", "leather_dark"), ("leather", "fur"), ("iron", "horn"), ("iron", "skin"),
              ("skin", "b_big"), ("skin", "b_mid"), ("wood", "tooth"), ("hood", "naut_eye")]
a4.ZONES, a4.GLOWING = ZONES, GLOWING
UV_SKIN = {"north": (8, 8), "east": (0, 8), "west": (16, 8), "south": (24, 8), "up": (8, 0), "down": (16, 0)}
VIEWS = [
    {"name": "hero", "location": (9, 13, 7), "target": (0, 0, 2.9), "scale": 10.5, "player": True},
    {"name": "low", "location": (-5, 10, 2.8), "target": (0, 0.6, 2.9), "scale": 9.0, "player": False},
    {"name": "side", "location": (18, 0, 3), "target": (0, 0, 3), "scale": 9.5, "player": False},
    {"name": "back", "location": (8, -14, 6), "target": (0, -1, 2.4), "scale": 9.5, "player": False},
    {"name": "viking", "location": (3, 12, 5.6), "target": (0, 1.4, 4.2), "scale": 3.6, "player": False},
]


def fsize(c, f):
    d = [c.to[i] - c.frm[i] for i in range(3)]
    w, h = (d[0], d[1]) if f in ("north", "south") else ((d[2], d[1]) if f in ("east", "west") else (d[0], d[2]))
    return int(math.ceil(w - 1e-6)), int(math.ceil(h - 1e-6))


def twin(name):
    name = name.replace("_left", "_right")
    name = re.sub(r"_-1(?=_|$)", "_1", name)
    return re.sub(r"_l(\d*)(?=_|$)", r"_r\1", name)


def island_keys(model):
    names = {c.name: c for c in model.cubes}
    keys = {}
    for i, c in enumerate(model.cubes):
        for f in FACES:
            w, h = fsize(c, f)
            if not w or not h or b4.hidden(c, f):
                continue
            if c.name == "head":
                keys[(i, f)] = (c.name, f, 24, 24, c.mat)
                continue
            t = twin(c.name)
            same = t != c.name and t in names and fsize(names[t], f) == (w, h) and names[t].mat == c.mat
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
            patch = Image.fromarray(SKIN[v:v + 8, u:u + 8].astype("uint8"), "RGBA").resize((24, 24), Image.NEAREST)
        elif key[4] == "net":                                 # a knotted mesh: cords every fourth texel
            for py in range(h):
                for px in range(w):
                    if px % 4 and py % 4:
                        patch.putpixel((px, py), (0, 0, 0, 0))
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return atlas, positions, used, height


def model_pass(kind, name, hitbox):
    model = s3.build(kind, "idle")
    off = [o for o in v4.check_density(model) if not s2.BARNACLE.match(o.split()[0])]
    if off:
        raise SystemExit("faces off the texel grid: " + ", ".join(off[:10]))
    model.name = name
    keys = island_keys(model)
    atlas, positions, used, height = build_atlas(keys)
    path = OUT / f"{name}.png"
    atlas.save(path)
    grey = OUT / f"{name}_grey.png"
    r = np.array(atlas)
    g = (r[..., :3] @ (0.2126, 0.7152, 0.0722)).astype("uint8")
    r[..., 0] = r[..., 1] = r[..., 2] = g
    Image.fromarray(r, "RGBA").save(grey)
    bb, culled = a4.textured_bbmodel(model, keys, positions, path, SIZE, height, hitbox, s3.pose_table(kind).items())
    p = OUT / f"{name}.bbmodel"
    p.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(p, s3.SERVER_MODELS / p.name)
    texels = sum(w * h for (_, _, w, h) in positions.values())
    faces = {c.name: bb["elements"][i]["faces"] for i, c in enumerate(model.cubes)}
    return faces, height, {"atlas": [SIZE, height], "rows_used": used, "islands": len(positions), "faces_drawn": len(keys),
                           "faces_buried_and_left_out": culled, "fill": round(texels / (SIZE * used), 2)}


def together(mount_faces, rider_faces, mh, rh, grey, key="idle", tag=None, folder=None):
    """Both models posed together, through one stacked atlas (render only)."""
    tag = tag if tag is not None else ("_grey" if grey else "")
    img = Image.new("RGBA", (SIZE, mh + rh), (0, 0, 0, 0))
    img.paste(Image.open(OUT / f"{s3.MOUNT_ID}{tag}.png"), (0, 0))
    img.paste(Image.open(OUT / f"{s3.RIDER_ID}{tag}.png"), (0, mh))
    stacked = OUT / f"_stack{tag}.png"
    img.save(stacked)
    m = s2.model(key, preview=False)
    s3.a3.fold_quarter_turns(m)
    def faces(c):
        g = c.group
        while g is not None and g.name != "rider":
            g = g.parent
        if g is None:
            return mount_faces[c.name]
        out = {}
        for f, d in rider_faces[c.name].items():
            u0, v0, u1, v1 = d["uv"]
            out[f] = dict(d, uv=[u0, v0 + mh, u1, v1 + mh])
        return out
    a4.render(m, {"elements": [{"faces": faces(c)} for c in m.cubes]}, stacked, OUT / (folder or ("grey" if grey else "colour")), VIEWS)
    stacked.unlink()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mf, mh, mrep = model_pass("mount", s3.MOUNT_ID, s3.MOUNT_HITBOX)
    rf, rh, rrep = model_pass("rider", s3.RIDER_ID, s3.RIDER_HITBOX)
    together(mf, rf, mh, rh, False)
    together(mf, rf, mh, rh, True)
    a4.review_sheet(OUT, "The Tidebreaker: UV and material zones (session 4), colour then grey", VIEWS)
    close = [f"{a}/{b}: {abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])):.0f}" for a, b in NEIGHBOURS
             if abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])) < 12]
    report = {"mount": mrep, "rider": rrep, "neighbours_too_close_in_value": close,
              "zones": {z: list(ZONES[z]) for z in ZONES if not z.startswith("tx_")}}
    (OUT / "uv_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("mount", "rider", "neighbours_too_close_in_value")}))


if __name__ == "__main__":
    main()
