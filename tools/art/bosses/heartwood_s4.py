"""Heartwood Horror, session 4: UV and material blocking (plan: docs/art/bosses/heartwood_horror/overhaul/plan.md).

Every visible face of the session 3 rig is mapped at one texel per model unit into one atlas. Most faces are a flat
colour of their material zone; three parts carry real vanilla pixels from the 26.2 client, at 1x like the rest:
- the sleeper: creaking.png on the curled creaking (head, crown, body, its leaves; its limbs take the arm and leg
  strips, turned to lie along them);
- the lantern: the awake creaking heart (creaking_heart_awake / _top_awake) on its one-block heart, and on its glow
  overlay (the same block a quarter texel bigger, full-bright) only the heart's orange cracks;
- the moss: pale_hanging_moss strips down each strand, the tip texture at the bottom.
The resin is Bayer-dithered: fully clear and fully opaque texels mixed (never half-clear, which flickers in game), so
the sleeper shows through the shell.

Zones (tier 3, the pale garden's own colours: pale oak bark, resin amber, the creaking heart's orange as the glow):
bark / bark_dark (knots, brow, hump cap), root (fingers, toes, the lantern's root), wood (the broken branches' ends),
moss, resin / resin_dark (the shell's rims), heart_frame (the lantern's cage), petal / bud / bloom (eyeblossoms),
eyelid (the sleeper's shut eyes).

Run from the repository root, with the folder holding assets/ from the 26.2 client as the argument:
python tools/art/bosses/heartwood_s4.py <folder> [--server]
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, pivot_matrix  # noqa: E402
from bosses import archevoker_s4 as a4, brood_s4 as b4, volley_crone_s4 as v4  # noqa: E402
from bosses import heartwood_s2 as s2, heartwood_s3 as s3  # noqa: E402

OUT = ROOT / "docs/art/bosses/heartwood_horror/overhaul/s4_uv"
SIZE = 512
NAME = "occultech_heartwood_horror_rig"
ZONES = {
    "bark": (87, 77, 75), "bark_dark": (58, 50, 50), "root": (132, 118, 110), "wood": (198, 189, 182),
    "moss": (150, 158, 146),
    "resin": (217, 99, 25), "resin_dark": (124, 50, 18), "resin_core": (222, 128, 40),
    "heart_frame": (46, 40, 40), "heart": (149, 84, 49),
    "sleeper": (96, 86, 84), "eyelid": (52, 46, 46),
    "petal": (226, 222, 216), "bud": (150, 146, 150), "bloom": (255, 146, 36), "glow": (255, 160, 60),
}
GLOWING = ("bloom", "glow", "resin_core")
NEIGHBOURS = [("bark", "bark_dark"), ("bark", "root"), ("bark", "moss"), ("bark", "resin"), ("bark", "petal"),
              ("bark", "wood"), ("resin", "resin_dark"), ("heart", "heart_frame"), ("root", "heart_frame"),
              ("petal", "bud"), ("bark", "bud"), ("resin", "resin_core")]
RESIN_MID_A = 70                 # the resin's alpha in the middle of a face (translucent: see resin_patch)
RESIN_EDGE_A = 180              # ... and at its edges
RESIN_LIGHT = (238, 138, 44)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
TEX = {}
a4.ZONES, a4.GLOWING = ZONES, GLOWING

# the creaking's box UVs (CreakingModel.createMesh): texture offset and box size
CREAKING = {"head": ((0, 0), (6, 10, 6)), "crown": ((28, 31), (6, 3, 6)), "body": ((0, 16), (6, 13, 5)),
            "arm": ((22, 13), (3, 21, 3)), "leg": ((42, 40), (3, 16, 3)), "leaf": ((12, 40), (9, 14, 0))}


def box_rect(part, face):
    (u, v), (w, h, d) = CREAKING[part]
    return {"up": (u + d, v, w, d), "down": (u + d + w, v, w, d), "north": (u + d, v + d, w, h),
            "south": (u + 2 * d + w, v + d, w, h), "east": (u, v + d, d, h), "west": (u + d + w, v + d, d, h)}[face]


def crop(img, rect):
    u, v, w, h = rect
    return img[v:v + h, u:u + w].copy()


def fit(src, w, h):
    """A vanilla strip fitted to a face: turned a quarter if it runs the other way, then cropped (or tiled) to size.
    Never scaled."""
    if (w > h) != (src.shape[1] > src.shape[0]) and w != h and src.shape[0] != src.shape[1]:
        src = np.rot90(src)
    reps = (int(np.ceil(h / src.shape[0])), int(np.ceil(w / src.shape[1])), 1)
    return np.tile(src, reps)[:h, :w]


def sleeper_patch(name, face, w, h):
    skin = TEX["creaking"]
    if name in ("sleeper_head", "sleeper_crown", "sleeper_body"):
        return crop(skin, box_rect(name.split("_")[1], face))
    if "leaf" in name:
        return fit(crop(skin, box_rect("leaf", "north")), w, h)
    part = "arm" if "arm" in name else "leg"
    if w == h:                                           # the ends of a limb
        return fit(crop(skin, box_rect(part, "up")), w, h)
    return fit(crop(skin, box_rect(part, "north")), w, h)


def heart_patch(face, glow):
    """The lantern's block wears the dormant creaking heart; its glow overlay carries the awake heart's cracks, so
    tinting the overlay dark puts the lantern out."""
    top = face in ("up", "down")
    if not glow:
        return TEX["heart_base_top" if top else "heart_base"].copy()
    img = TEX["heart_top" if top else "heart_side"].copy()
    if glow:                                             # only the orange cracks, the rest fully clear
        r, g, b = (img[..., i].astype(int) for i in range(3))
        orange = (r > 150) & (r - b > 90)
        img[..., 3] = np.where(orange, 255, 0)
    return img


def moss_patch(w, h):
    strip = TEX["moss"][:, 6:6 + max(1, min(w, 4))]
    tip = TEX["moss_tip"][:, 6:6 + max(1, min(w, 4))]
    if h <= 16:
        col = tip[16 - h:]
    else:
        col = np.concatenate([np.tile(strip, (int(np.ceil((h - 16) / 16)), 1, 1))[:h - 16], tip])
    return fit(col, w, h)


def resin_patch(w, h, seed):
    """Translucent amber: thicker (more opaque) at the face's edges, clearest in its middle, where the sleeper shows.
    item_translucent sorts faces back to front, and the shell's chamber keeps anything outside the womb's bone from
    showing through it."""
    ys, xs = np.mgrid[0:h, 0:w]
    edge = np.minimum(np.minimum(xs, w - 1 - xs), np.minimum(ys, h - 1 - ys)) / max(1.0, min(w, h) / 2)
    img = np.zeros((h, w, 4), np.uint8)
    img[..., :3] = np.where((edge > 0.45)[..., None], RESIN_LIGHT, ZONES["resin"])
    img[..., 3] = np.round(RESIN_EDGE_A - (RESIN_EDGE_A - RESIN_MID_A) * np.clip(edge * 1.6, 0, 1)).astype(np.uint8)
    return img


def island_keys(model):
    keys = {}
    for i, c in enumerate(model.cubes):
        for f in FACES:
            w, h = v4.face_size(c, f)
            if not w or not h or b4.hidden(c, f):
                continue
            keys[(i, f)] = (c.name, f, w, h, c.mat)
    return keys


def patch_for(key):
    name, face, w, h, mat = key
    if mat == "sleeper":
        arr = sleeper_patch(name, face, w, h)
    elif mat in ("heart", "glow") and name.startswith("heart"):
        arr = fit(heart_patch(face, mat == "glow"), w, h)
    elif mat == "moss" and face not in ("up", "down"):
        arr = moss_patch(w, h)
    elif mat == "resin" and name == "resin_c":       # the chamfer layer inside the shell: a solid rim, clear inside
        arr = resin_patch(w, h, 0)
        ys, xs = np.mgrid[0:h, 0:w]
        rim = np.minimum(np.minimum(xs, w - 1 - xs), np.minimum(ys, h - 1 - ys)) < 2
        arr[..., 3] = np.where(rim, 255, 0)
        arr[..., :3] = ZONES["resin"]
    elif mat == "resin":
        arr = resin_patch(w, h, sum(map(ord, name + face)) % 16)
    else:
        arr = np.zeros((h, w, 4), np.uint8)
        arr[..., :3] = ZONES[mat]
        arr[..., 3] = 255
    arr = arr.astype(np.uint8)
    if mat not in ("resin", "moss", "glow"):
        arr[..., 3] = 255                                # a solid face is never see-through
    elif not (mat == "resin" and name == "resin"):       # only the shell's own faces are half-clear
        arr[..., 3] = np.where(arr[..., 3] >= 128, 255, 0)
    return Image.fromarray(arr, "RGBA")


def build_atlas(keys):
    b4.SIZE = SIZE
    positions, used, _ = b4.pack({k: (k[2], k[3]) for k in keys.values()})
    height = 16
    while height < used:
        height *= 2
    atlas = Image.new("RGBA", (SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        patch = patch_for(key)
        if key[4] not in ("resin", "moss", "glow"):    # a solid island gets a bleed border; see-through ones don't
            atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return atlas, positions, used, height


def render(model, bb, atlas_path, out, views):
    """Textured renders; an inflated cube (the lantern's glow) is drawn that much bigger, like the game does."""
    out.mkdir(parents=True, exist_ok=True)
    boxes = []
    for i, c in enumerate(model.cubes):
        lo, hi = np.array(c.frm) - c.inflate, np.array(c.to) + c.inflate
        pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
        corners = ((c.group.world_matrix() @ pivot_matrix(c.origin, c.rotation)) @ pts)[:3].T
        boxes.append({"corners": corners.tolist(), "from": c.frm, "to": c.to, "glow": c.mat in GLOWING,
                      "uv": bb["elements"][i]["faces"]})
    job = out / "render_job.json"
    job.write_text(json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes, "views": views,
                               "player_at": (5.5, 4.0), "translucent": True}), encoding="utf-8")
    r = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                        str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job)],
                       capture_output=True, text=True)
    if r.returncode or "TEXTURED_RENDER_DONE" not in r.stdout:
        raise SystemExit(r.stdout[-3000:] + r.stderr[-3000:])
    job.unlink()


# Blender coordinates (blocks, z up); it faces +y. Orthographic: scale is the view's width in blocks.
VIEWS = [
    {"name": "hero", "location": (10, 15, 7.5), "target": (0, 0.5, 3.6), "scale": 13.5, "player": True},
    {"name": "front", "location": (0, 20, 4.0), "target": (0, 0, 4.0), "scale": 12.0, "player": False},
    {"name": "player_eye", "location": (-4.5, 10, 1.62), "target": (0, 1.5, 3.6), "scale": 12.5, "player": False},
    {"name": "side", "location": (20, 0, 4.2), "target": (0, -0.4, 4.2), "scale": 14.0, "player": False},
    {"name": "back", "location": (-9, -16, 8), "target": (0, 0, 4.0), "scale": 13.0, "player": False},
    {"name": "chest", "location": (2.2, 10, 2.2), "target": (0, 1.6, 3.9), "scale": 4.6, "player": False},
]


def main(argv):
    assets = Path(argv[0]) / "assets/minecraft/textures"
    for key, rel in (("creaking", "entity/creaking/creaking.png"), ("heart_side", "block/creaking_heart_awake.png"),
                     ("heart_top", "block/creaking_heart_top_awake.png"), ("moss", "block/pale_hanging_moss.png"),
                     ("moss_tip", "block/pale_hanging_moss_tip.png"), ("heart_base", "block/creaking_heart.png"),
                     ("heart_base_top", "block/creaking_heart_top.png")):
        TEX[key] = np.array(Image.open(assets / rel).convert("RGBA"))
    OUT.mkdir(parents=True, exist_ok=True)
    s2.PALETTE.update({k: v for k, v in ZONES.items()})
    s3.a2.PALETTE = dict(s2.PALETTE)
    model = s3.model()
    for c in model.cubes:                         # the lantern hangs on bark, not on a pale root
        if c.name.startswith("lantern_root"):
            c.mat = "bark_dark"
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
    poses = s3.pose_table(s3.model())
    hitbox = s2.hitbox_bounds(s2.build().m)
    bb, culled = a4.textured_bbmodel(model, keys, positions, path, SIZE, height, hitbox, list(poses.items()))
    p = OUT / f"{NAME}.bbmodel"
    p.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if "--server" in argv and s3.SERVER_MODELS.is_dir():
        shutil.copyfile(p, s3.SERVER_MODELS / p.name)
    for tag, atlas_file in (("colour", path), ("grey", grey_path)):
        render(model, bb, atlas_file, OUT / tag, VIEWS)
    a4.review_sheet(OUT, "Heartwood Horror: UV and material zones (session 4)", VIEWS)
    texels = sum(w * h for (_, _, w, h) in positions.values())
    close = [f"{a}/{b}: {abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])):.0f}" for a, b in NEIGHBOURS
             if abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])) < 12]
    alpha = np.array(atlas)[..., 3]
    report = {"atlas": [SIZE, height], "rows_used": used, "islands": len(positions), "faces_drawn": len(keys),
              "faces_buried_and_left_out": culled, "fill": round(texels / (SIZE * used), 2),
              "half_clear_texels": int(((alpha > 0) & (alpha < 255)).sum()), "resin_alpha": [RESIN_MID_A, RESIN_EDGE_A],
              "neighbours_too_close_in_value": close,
              "zones": {z: [list(v), round(v4.luminance(v))] for z, v in ZONES.items()}}
    (OUT / "uv_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "zones"}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
