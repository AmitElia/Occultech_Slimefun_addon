"""Dread Riders, session 4: UV and material blocking (plan: docs/art/bosses/dread_riders/overhaul/plan.md).

Every visible face of the four session 3 rigs is mapped at one texel per model unit, one atlas per model. Most faces
are a flat colour of their material zone. Vanilla pixels from the 26.2 client go where the design keeps vanilla's
parts, each at exactly 2 pixels per skin texel (those parts are vanilla's at 2x, so this is still one texel per unit):
- the riders' heads: zombie.png / skeleton.png (the head box);
- the riders' bodies: the vanilla body box; the skeleton's bare arms and legs take the vanilla limb strips (the upper
  half on the upper arm and thigh, the lower half on the forearm and shin);
- the horses' heads: horse_zombie.png / horse_skeleton.png on the cranium (6x5x7) and the muzzle (4x5x5); the
  skeleton's muzzle is split from its jaw, so it takes the muzzle box's upper half.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the argument:
python tools/art/bosses/dread_s4.py <client folder> [--server]
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
from bosskit.bbmodel import FACES, _uuid  # noqa: E402
from bosses import archevoker_s2 as a2, archevoker_s4 as a4, brood_s4 as b4, volley_crone_s4 as v4  # noqa: E402
from bosses import dread_s2 as s2, dread_s3 as s3  # noqa: E402

OUT = ROOT / "docs/art/bosses/dread_riders/overhaul/s4_uv"
SIZE = 512
TEX = {}
# tier 3: netherite-dark plate with a crimson accent on the Vanguard's side; old bone, iron and gold with hollow cyan on
# the Outrider's; the zombie horse keeps vanilla's rotting green
ZONES = {
    # the Vanguard and his horse
    "zhorse": (78, 98, 70), "zhorse_dark": (52, 66, 48), "hair": (30, 30, 28), "hoof": (52, 46, 42),
    "plate": (66, 60, 68), "plate_edge": (118, 110, 116), "plate_dark": (34, 30, 36), "crimson": (232, 48, 56),
    "cloth": (30, 24, 40), "trim": (150, 32, 38), "leather": (96, 68, 50), "wood": (128, 96, 66),
    "horn": (40, 34, 32), "horn_tip": (176, 166, 146), "chain": (96, 94, 102), "iron_dark": (62, 62, 70),
    "zskin": (98, 138, 74), "zface": (34, 50, 30),
    # the Outrider and his horse
    "bone": (206, 205, 200), "bone_dark": (158, 156, 152), "lamellar": (138, 140, 154), "socket": (30, 30, 34), "cyan": (96, 236, 226),
    "rope": (128, 38, 36), "blanket": (136, 122, 112), "iron": (172, 172, 180), "skel": (196, 196, 192),
    "skel_dark": (70, 70, 72), "coat": (58, 70, 86), "coat_dark": (40, 46, 60), "mail": (104, 106, 112),
    "plume": (166, 36, 42), "gold": (138, 100, 44),
}
GLOWING = ("cyan", "crimson")
NEIGHBOURS = [("plate", "plate_edge"), ("plate", "plate_dark"), ("plate", "zhorse"), ("plate", "cloth"),
              ("cloth", "trim"), ("plate", "crimson"), ("zhorse", "hair"), ("zhorse", "hoof"), ("leather", "cloth"),
              ("plate", "horn"), ("horn", "horn_tip"), ("wood", "plate"),
              ("bone", "bone_dark"), ("bone", "rope"), ("bone", "blanket"), ("blanket", "rope"), ("iron", "gold"),
              ("iron", "mail"), ("skel", "leather"), ("lamellar", "leather"), ("lamellar", "skel"), ("lamellar", "gold"), ("skel", "coat_dark"), ("iron", "plume")]
# glows (cyan, crimson) are judged by hue and full-bright emission, not value: the eyes sit on vanilla dark sockets

# vanilla box UVs: texture offset and box size (w = x, h = y, d = z), in skin texels
HUMANOID = {"head": ((0, 0), (8, 8, 8)), "body": ((16, 16), (8, 12, 4))}
SKELETON_LIMB = {"arm": ((40, 16), (2, 12, 2)), "leg": ((0, 16), (2, 12, 2))}
HORSE = {"cranium": ((0, 13), (6, 5, 7)), "muzzle": ((0, 25), (4, 5, 5))}


def box_rect(box, face):
    (u, v), (w, h, d) = box
    return {"up": (u + d, v, w, d), "down": (u + d + w, v, w, d), "north": (u + d, v + d, w, h),
            "south": (u + 2 * d + w, v + d, w, h), "east": (u, v + d, d, h), "west": (u + d + w, v + d, d, h)}[face]


def crop2(img, rect, k=2):
    """A skin rectangle at k pixels per texel (2 on the riders, 3 on the horses' heads)."""
    u, v, w, h = rect
    a = img[v:v + h, u:u + w]
    return np.repeat(np.repeat(a, k, axis=0), k, axis=1)


def fit(src, w, h):
    """Turned a quarter if it runs the other way, then cropped (or tiled) to size; never scaled."""
    if (w > h) != (src.shape[1] > src.shape[0]) and w != h and src.shape[0] != src.shape[1]:
        src = np.rot90(src)
    reps = (int(np.ceil(h / src.shape[0])), int(np.ceil(w / src.shape[1])), 1)
    return np.tile(src, reps)[:h, :w]


def vanilla_patch(kind, part, c, face, w, h):
    """The vanilla pixels for a face, or None for a flat zone."""
    n = c.name
    if part == "rider":
        skin = TEX["zombie" if kind == "vanguard" else "skeleton"]
        if n == "head":
            return crop2(skin, box_rect(HUMANOID["head"], face))
        if n == "torso":
            return crop2(skin, box_rect(HUMANOID["body"], face))
        if kind == "outrider" and c.mat == "skel" and n.startswith(("arm", "thigh", "shin")):
            box = SKELETON_LIMB["arm" if n.startswith("arm") else "leg"]
            upper = n.endswith("_upper") or n.startswith("thigh")
            if w == h:                                        # an end cap
                return fit(crop2(skin, box_rect(box, "up" if upper else "down")), w, h)
            strip = crop2(skin, box_rect(box, "north"))       # 4 x 24, the limb's length down the rows
            half = strip[:12] if upper else strip[12:]
            return fit(half, w, h)
        return None
    skin = TEX["horse_zombie" if kind == "vanguard" else "horse_skeleton"]
    if n == "cranium":
        return crop2(skin, box_rect(HORSE["cranium"], face), 3)
    if n == "muzzle":
        img = crop2(skin, box_rect(HORSE["muzzle"], face), 3)
        if img.shape[:2] == (h, w):
            return img
        return fit(img[:h] if face not in ("up", "down") else img, w, h)
    return None


def island_keys(model):
    keys = {}
    for i, c in enumerate(model.cubes):
        for f in FACES:
            w, h = v4.face_size(c, f)
            if not w or not h or b4.hidden(c, f):
                continue
            keys[(i, f)] = (c.name, f, w, h, c.mat, i)
    return keys


def build_atlas(kind, part, model, keys):
    b4.SIZE = SIZE
    positions, used, _ = b4.pack({k: (k[2], k[3]) for k in keys.values()})
    height = 16
    while height < used:                       # the atlas is only as tall as it needs to be (a power of two)
        height *= 2
    atlas = Image.new("RGBA", (SIZE, height), (0, 0, 0, 0))
    vanilla = 0
    for key, (x, y, w, h) in positions.items():
        name, face, _, _, mat, i = key
        arr = vanilla_patch(kind, part, model.cubes[i], face, w, h)
        if arr is None or arr.shape[:2] != (h, w):
            arr = np.zeros((h, w, 4), np.uint8)
            arr[..., :3] = ZONES[mat]
        else:
            vanilla += 1
        arr = arr.astype(np.uint8).copy()
        arr[..., 3] = 255                          # every face here is solid
        patch = Image.fromarray(arr, "RGBA")
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return atlas, positions, used, height, vanilla


def grey(img):
    r = np.array(img)
    g = (r[..., :3] @ (0.2126, 0.7152, 0.0722)).astype("uint8")
    r[..., 0] = r[..., 1] = r[..., 2] = g
    return Image.fromarray(r, "RGBA")


def textured(model, name, keys, positions, path, height, hitbox, poses):
    model.name = name
    bb, culled = a4.textured_bbmodel(model, keys, positions, path, SIZE, height, hitbox or ((0, 0, 0), (1, 1, 1)),
                                     [(k, (rot, pos)) for k, (rot, pos, _) in poses.items()])
    if hitbox is None:
        bb["elements"] = [e for e in bb["elements"] if e["name"] != "hitbox"]
        bb["groups"] = [g for g in bb["groups"] if g["name"] != "ob_hitbox"]
        bb["outliner"] = [o for o in bb["outliner"] if not (isinstance(o, dict) and o.get("name") == "ob_hitbox")]
    s3.with_scale(bb, name, poses)
    return bb, culled


# ==== renders: the pair together, one texture (the two atlases side by side) ===========================================

def to_blender(p):
    return [p[0] / 16, -p[2] / 16, p[1] / 16]


def pair_render(kind, P, bbs, atlases, out, views):
    mm, rm, seat = P["mount"], P["rider"], P["seat"]
    wm = atlases[0].width
    combo = Image.new("RGBA", (wm + atlases[1].width, max(a.height for a in atlases)), (0, 0, 0, 0))
    combo.paste(atlases[0], (0, 0))
    combo.paste(atlases[1], (wm, 0))
    tex = out / "pair_texture.png"
    out.mkdir(parents=True, exist_ok=True)
    combo.save(tex)
    boxes = []
    for model, bb, dx, shift in ((mm, bbs[0], 0, np.zeros(3)), (rm, bbs[1], wm, np.array(seat))):
        for i, c in enumerate(model.cubes):
            faces = {}
            for f, d in bb["elements"][i]["faces"].items():
                u = list(d["uv"])
                if d.get("texture") is not None:
                    u = [u[0] + dx, u[1], u[2] + dx, u[3]]
                faces[f] = dict(d, uv=u)
            corners = (c.corners() + shift).tolist()
            boxes.append({"corners": corners, "from": c.frm, "to": c.to, "glow": c.mat in GLOWING, "uv": faces})
    job = out / "render_job.json"
    job.write_text(json.dumps({"texture": str(tex), "out": out.as_posix(), "boxes": boxes, "views": views,
                               "player_at": (3.2, 2.6)}), encoding="utf-8")
    r = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                        str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job)],
                       capture_output=True, text=True)
    if r.returncode or "TEXTURED_RENDER_DONE" not in r.stdout:
        raise SystemExit(r.stdout[-3000:] + r.stderr[-3000:])
    job.unlink()


def views_for(P):
    mm, rm, seat = P["mount"], P["rider"], np.array(P["seat"])
    head = next(c for c in rm.cubes if c.name == "head")
    hc = to_blender(head.corners().mean(0) + seat)
    cran = next(c for c in mm.cubes if c.name == "cranium")
    pc = to_blender(cran.corners().mean(0))
    return [
        {"name": "hero", "location": (9, 12, 6.5), "target": (0, 0, 2.8), "scale": 9.5, "player": True},
        {"name": "front", "location": (0, 16, 3.2), "target": (0, 0, 3.2), "scale": 7.8, "player": False},
        {"name": "side", "location": (16, 0, 3.2), "target": (0, -0.3, 3.2), "scale": 9.4, "player": False},
        {"name": "player_eye", "location": (-4, 7, 1.62), "target": (0, 0.8, 3.0), "scale": 9.4, "player": False},
        {"name": "back", "location": (-7, -12, 6), "target": (0, 0, 3.0), "scale": 9.4, "player": False},
        {"name": "rider_head", "location": (hc[0] + 2.2, hc[1] + 6, hc[2] + 0.6), "target": tuple(hc), "scale": 2.6,
         "player": False},
        {"name": "horse_head", "location": (pc[0] + 3.5, pc[1] + 5.5, pc[2] + 0.8), "target": tuple(pc), "scale": 3.4,
         "player": False},
    ]


def main(argv):
    assets = Path(argv[0]) / "assets/minecraft/textures/entity"
    for key, rel in (("zombie", "zombie/zombie.png"), ("skeleton", "skeleton/skeleton.png"),
                     ("horse_zombie", "horse/horse_zombie.png"), ("horse_skeleton", "horse/horse_skeleton.png")):
        TEX[key] = np.array(Image.open(assets / rel).convert("RGBA"))
    OUT.mkdir(parents=True, exist_ok=True)
    s2.PALETTE.update(ZONES)
    a2.PALETTE = dict(s2.PALETTE)
    a4.ZONES, a4.GLOWING = ZONES, GLOWING
    report = {}
    for kind in ("vanguard", "outrider"):
        P = s3.build_pair(kind)
        bbs, atlases, greys = [], [], []
        for part, model, name, hb, poses in (("mount", P["mount"], f"occultech_dread_{kind}_mount_rig", None, P["mount_poses"]),
                                             ("rider", P["rider"], f"occultech_dread_{kind}_rig", P["hitbox"], P["rider_poses"])):
            missing = sorted({c.mat for c in model.cubes} - set(ZONES))
            assert not missing, missing
            off = v4.check_density(model)
            if off:
                raise SystemExit("faces off the texel grid: " + ", ".join(off[:10]))
            keys = island_keys(model)
            atlas, positions, used, height, vanilla = build_atlas(kind, part, model, keys)
            path = OUT / f"{name}.png"
            atlas.save(path)
            g = grey(atlas)
            g.save(OUT / f"{name}_grey.png")
            s3.scale_model(model)
            bb, culled = textured(model, name, keys, positions, path, height, s3.scaled_hitbox(hb), s3.scaled_poses(poses))
            p = OUT / f"{name}.bbmodel"
            p.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
            if "--server" in argv and s3.SERVER_MODELS.is_dir():
                shutil.copyfile(p, s3.SERVER_MODELS / p.name)
            texels = sum(w * h for (_, _, w, h) in positions.values())
            alpha = np.array(atlas)[..., 3]
            report[name] = {"atlas": [SIZE, height], "rows_used": used, "islands": len(positions),
                            "vanilla_islands": vanilla, "faces_buried_and_left_out": culled,
                            "fill": round(texels / (SIZE * used), 2),
                            "half_clear_texels": int(((alpha > 0) & (alpha < 255)).sum())}
            bbs.append(bb)
            atlases.append(atlas)
            greys.append(g)
        P["seat"] = np.array(P["seat"]) * s3.SCALE
        views = views_for(P)
        pair_render(kind, P, bbs, atlases, OUT / kind / "colour", views)
        pair_render(kind, P, bbs, greys, OUT / kind / "grey", views)
        a4.review_sheet(OUT / kind, f"Dread Riders: the {kind.title()}, UV and material zones (session 4)", views,
                        name="sheet.png")
    close = [f"{a}/{b}: {abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])):.0f}" for a, b in NEIGHBOURS
             if abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])) < 12]
    report["neighbours_too_close_in_value"] = close
    report["zones"] = {z: [list(v), round(v4.luminance(v))] for z, v in ZONES.items()}
    (OUT / "uv_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "zones"}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
