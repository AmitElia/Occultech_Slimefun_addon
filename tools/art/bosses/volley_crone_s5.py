"""Volley redesign, session 5: texture painting.

Paints the session 4 atlas (same UV islands, 256 x 512):
- the skull is vanilla's skeleton head texture, each pixel doubled and re-coloured into Volley's bone ramp;
- every other zone is painted from a hue-shifted ramp (shadows go violet, lights go warm). Detail sits in clusters of
  2-4 tones: cracks and grime on bone, rivets and scratches on armour, rings on chain, grain on wood, streaks on basalt,
  facets on amethyst;
- form only, no painted light direction. Ambient occlusion is baked from the real geometry (texels darken where
  another part is close in front of them), plus darker joint ends on long bones and lit edges on armour plates;
- the glowing shards keep a hot core.

Run from the repository root: python tools/art/bosses/volley_crone_s5.py
"""
import base64
import json
import shutil
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, FACE_UV, _uuid, add_hitbox, pivot_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s2 as s2, volley_crone_s3 as s3, volley_crone_s4 as s4  # noqa: E402
from palettes import RAMPS  # noqa: E402

OUT = ROOT / "docs/art/bosses/volley/overhaul/s5_paint"
VANILLA = Path("C:/Users/eliaa/curseforge/minecraft/Install/versions/26.2/26.2.jar")

# Hue-shifted ramps, dark to light: shadows lean violet-blue, lights lean warm.
RAMP = {
    "bone": [(46, 42, 58), (84, 80, 96), (128, 126, 134), (170, 169, 170), (204, 202, 196), (230, 227, 216)],
    "marrow": [(16, 12, 22), (30, 24, 36), (46, 38, 50), (64, 54, 64), (86, 74, 82), (110, 98, 102)],
    "iron": [c[:3] for c in RAMPS["iron"]],
    "wood": [(36, 28, 32), (62, 48, 46), (88, 68, 58), (112, 86, 66), (138, 110, 84), (166, 138, 106)],
    "string": [(70, 58, 56), (110, 94, 80), (142, 124, 100), (168, 148, 118), (196, 178, 146), (220, 204, 172)],
    "basalt": [(12, 10, 18), (24, 20, 28), (38, 32, 40), (56, 48, 56), (78, 68, 74), (100, 90, 94)],
    "calcite": [c[:3] for c in RAMPS["chalk"]],
    "violet": [c[:3] for c in RAMPS["violet"]] + [(240, 228, 255)],
}
# zone -> (ramp, base level)
ZONE = {"bone": ("bone", 4), "marrow": ("marrow", 2), "armour": ("iron", 2), "chain": ("iron", 3),
        "steel": ("iron", 3), "wood": ("wood", 3), "string": ("string", 3), "basalt": ("basalt", 1),
        "calcite": ("calcite", 4), "crystal": ("violet", 4), "glow": ("violet", 5)}
LONG_BONES = ("humerus", "ulna", "femur", "tibia", "neck")
VANILLA_HEAD = {"up": (8, 0), "down": (16, 0), "east": (0, 8), "north": (8, 8), "west": (16, 8), "south": (24, 8)}


def noise(seed, x, y, cell=2):
    """A deterministic value 0..999 per cell (2x2 texels by default): detail comes in clusters, never single pixels."""
    n = (seed * 1103515245 + (x // cell) * 741103597 + (y // cell) * 1597334677) & 0xffffffff
    n ^= n >> 13
    n = (n * 1274126177) & 0xffffffff
    return (n >> 8) % 1000


# ---- geometry: where each texel is, and what is in front of it ---------------------------------------------------

def cube_matrix(cube):
    return cube.group.world_matrix() @ pivot_matrix(cube.origin, cube.rotation)


def texel_points(cube, face, w, h):
    """Rest-pose positions, normals and in-face axes of a face's texel centres (model units, local cube space)."""
    au, su, av, sv = FACE_UV[face]
    lo, hi = np.array(cube.frm), np.array(cube.to)
    normal_axis = ({0, 1, 2} - {au, av}).pop()
    outward = 1 if face in ("east", "up", "south") else -1
    us, vs = np.meshgrid(np.arange(w) + 0.5, np.arange(h) + 0.5)
    pts = np.zeros((h, w, 3))
    pts[..., au] = lo[au] + us if su > 0 else hi[au] - us
    pts[..., av] = lo[av] + vs if sv > 0 else hi[av] - vs
    pts[..., normal_axis] = hi[normal_axis] if outward > 0 else lo[normal_axis]
    n = np.zeros(3)
    n[normal_axis] = outward
    tu, tv = np.zeros(3), np.zeros(3)
    tu[au], tv[av] = 1, 1
    return pts, n, tu, tv


def occlusion(model, index, face, w, h, solids):
    """0..1 per texel: how much of the space just in front of it is filled by other parts (crease shading)."""
    cube = model.cubes[index]
    pts, n, tu, tv = texel_points(cube, face, w, h)
    m = cube_matrix(cube)
    samples = [n * 0.7, n * 1.6, n * 0.8 + tu * 1.6, n * 0.8 - tu * 1.6, n * 0.8 + tv * 1.6, n * 0.8 - tv * 1.6]
    flat = pts.reshape(-1, 3)
    hits = np.zeros(len(flat))
    for off in samples:
        world = (m @ np.c_[flat + off, np.ones(len(flat))].T).T
        inside = np.zeros(len(flat), bool)
        for j, (inv, lo, hi) in enumerate(solids):
            if j == index:
                continue
            local = (inv @ world.T).T[:, :3]
            inside |= np.all((local > lo + 0.05) & (local < hi - 0.05), axis=1)
        hits += inside
    return (hits / len(samples)).reshape(h, w)


# ---- painters ----------------------------------------------------------------------------------------------------

def vanilla_head():
    import zipfile
    with zipfile.ZipFile(VANILLA) as jar:
        img = Image.open(jar.open("assets/minecraft/textures/entity/skeleton/skeleton.png")).convert("L")
    return img


def vanilla_level(v):
    """A vanilla grey (0..255) to a bone ramp level, keeping vanilla's own light-dark structure."""
    return int(np.clip(round((v - 40) / 190 * 5), 0, 5))


def paint_skull(cube, face, w, h, head):
    """The skull (vanilla rows 0-5) and the jaw (rows 6-7): vanilla's head, pixel-doubled, in Volley's bone ramp."""
    ox, oy = VANILLA_HEAD[face]
    out = np.zeros((h, w), int)
    for y in range(h):
        for x in range(w):
            vx, vy = x // 2, y // 2
            if face in ("east", "west", "north", "south") and cube.name == "jaw":
                vy += 6
            out[y, x] = vanilla_level(head.getpixel((ox + min(7, vx), oy + min(7, vy))))
    return out


def paint_levels(cube, zone, face, w, h, seed):
    ramp, base = ZONE[zone]
    lv = np.full((h, w), base, int)
    long_axis = int(np.argmax(np.array(cube.to) - np.array(cube.frm)))
    au, _, av, _ = FACE_UV[face]
    for y in range(h):
        for x in range(w):
            r = noise(seed, x, y)
            edge = min(x, y, w - 1 - x, h - 1 - y)
            if zone == "bone":
                if r < 40:
                    lv[y, x] -= 1                                   # a little pitting
                elif r > 975:
                    lv[y, x] += 1                                   # polished knuckles of bone
                if h >= 10 and av == 1 and y > h * 0.7 and noise(seed + 7, x, y, 3) < 300:
                    lv[y, x] -= 1                                   # grime settles low on upright faces
                if any(k in cube.name for k in LONG_BONES):
                    along = x if au == long_axis else (y if av == long_axis else None)
                    span = w if au == long_axis else h
                    if along is not None and min(along, span - 1 - along) < 2:
                        lv[y, x] -= 1                               # joint ends: the knob meets the next bone
                if cube.name.startswith("rib_"):
                    lv[y, x] += 1 if y == 0 and av == 1 else (-1 if y == h - 1 and av == 1 else 0)
            elif zone == "marrow":
                lv[y, x] += -1 if r < 300 else 0
            elif zone == "armour":
                if edge == 0:
                    lv[y, x] += 1 if (av == 1 and y == 0) or av != 1 else -1   # lit plate edges, a dark lower lip
                elif r < 70:
                    lv[y, x] += 1                                   # scratches catch the light
                elif r > 900 and (av != 1 or y > h * 0.5):
                    lv[y, x] -= 1                                   # tarnish, heavier low down
            elif zone == "chain":
                # 2x2 rings in a staggered grid, lit on a plain ground: mail, not a grille
                lv[y, x] += 1 if ((x // 2) + (y // 2)) % 2 == 0 and (x + y) % 2 == 0 else 0
            elif zone == "steel":
                lv[y, x] += 1 if edge == 0 else (-1 if r < 120 else 0)
            elif zone == "wood":
                along = x if au == long_axis else y
                across = y if au == long_axis else x
                if (across + (along // 5) % 2) % 3 == 0:
                    lv[y, x] -= 1                                   # grain runs the length of the stock
                if noise(seed + 3, x, y, 3) > 975:
                    lv[y, x] -= 1                                   # knots
            elif zone == "string":
                lv[y, x] += 1 if (x + y) % 3 == 0 else 0
            elif zone == "basalt":
                lv[y, x] += 1 if noise(seed, x, y // 3, 1) < 260 else (-1 if r > 850 else 0)   # vertical streaks
            elif zone == "calcite":
                lv[y, x] += -1 if r < 160 else (1 if r > 880 else 0)
            elif zone == "crystal":
                # amethyst facets: a lit diagonal band and a dark corner on each face
                band = (x + y + seed % 5) % 7
                lv[y, x] += 1 if band in (0, 1) else (-1 if band == 4 else 0)
                if edge == 0:
                    lv[y, x] -= 1
            elif zone == "glow":
                d = max(abs((x + 0.5) / w - 0.5), abs((y + 0.5) / h - 0.5))
                lv[y, x] = 6 if d < 0.2 else (5 if d < 0.38 else 4)
    if zone == "bone" and w * h >= 120 and not cube.name.startswith("rib_"):
        crack(lv, seed, w, h)
    return np.clip(lv, 0, len(RAMP[ramp]) - 1)


def crack(lv, seed, w, h):
    """One short crack: a 3-6 texel walk, dark, with a lit lip beside it."""
    rng = np.random.default_rng(seed)
    x, y = int(rng.integers(1, w - 1)), int(rng.integers(1, max(2, h // 2)))
    for _ in range(int(rng.integers(3, 7))):
        lv[y, x] = max(0, lv[y, x] - 1)
        if x + 1 < w:
            lv[y, x + 1] = min(5, lv[y, x + 1] + 1)
        x = int(np.clip(x + rng.integers(-1, 2), 0, w - 1))
        y = int(np.clip(y + 1, 0, h - 1))


def paint(model, positions, shadowed=None):
    head = vanilla_head()
    # cubes that cast ambient occlusion: by default all of them; hidden variant parts are left out by the caller
    solids = [(np.linalg.inv(cube_matrix(c)), np.array(c.frm), np.array(c.to)) if shadowed is None or shadowed(c)
              else (np.eye(4), np.full(3, 1e9), np.full(3, -1e9)) for c in model.cubes]
    atlas = Image.new("RGBA", (s4.SIZE, s4.HEIGHT), (0, 0, 0, 0))
    for (i, face), (x0, y0, w, h) in positions.items():
        cube = model.cubes[i]
        zone = s4.zone_for(cube)
        seed = zlib.crc32(f"{cube.name}/{face}".encode())
        if cube.name in ("skull", "jaw"):
            lv, ramp = paint_skull(cube, face, w, h, head), RAMP["bone"]
        else:
            ramp_name, _ = ZONE[zone]
            lv, ramp = paint_levels(cube, zone, face, w, h, seed), RAMP[ramp_name]
        if zone != "glow":
            ao = occlusion(model, i, face, w, h, solids)
            lv = np.clip(lv - (ao >= 0.34) - (ao >= 0.6), 0, len(ramp) - 1)
        patch = Image.new("RGBA", (w, h))
        px = patch.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = tuple(ramp[lv[y, x]]) + (255,)
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x0 - 1, y0 - 1))
        atlas.paste(patch, (x0, y0))
    return atlas


def views():
    near = s4.views()
    return near + [
        # about how big he is on a 1080p screen at 10 blocks (70 degree field of view): ~350 pixels tall
        {"name": "ten_blocks", "location": (-3, 11, 1.62), "target": (0, 1.2, 2.3), "scale": 8.5, "player": True,
         "res": (640, 480)},
        {"name": "geode", "location": (2, -6, 6), "target": (0, 0.4, 3.6), "scale": 3.6, "player": False},
    ]


def main():
    model = s2.build()
    model.name = s3.MODEL_ID
    s4.remove_face_insets(model)
    rects = [((i, f), *s4.face_size(c, f)) for i, c in enumerate(model.cubes) for f in FACES]
    positions, used = s4.pack(rects)
    atlas = paint(model, positions)
    OUT.mkdir(parents=True, exist_ok=True)
    atlas_path = OUT / "occultech_volley.png"
    atlas.save(atlas_path)
    atlas.resize((s4.SIZE * 2, s4.HEIGHT * 2), Image.NEAREST).save(OUT / "atlas_preview.png")

    texture = {"name": atlas_path.name, "path": "", "folder": "", "namespace": "", "id": "0", "group": "",
               "width": s4.SIZE, "height": s4.HEIGHT, "uv_width": s4.SIZE, "uv_height": s4.HEIGHT,
               "particle": False, "use_as_default": True, "layers_enabled": False, "render_mode": "default",
               "render_sides": "auto", "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
               "frame_interpolate": False, "visible": True, "internal": True, "saved": False,
               "uuid": _uuid(s3.MODEL_ID + "/atlas"),
               "source": "data:image/png;base64," + base64.b64encode(atlas_path.read_bytes()).decode()}
    bb = model.to_bbmodel(texture_size=(s4.SIZE, s4.HEIGHT), textures=(texture,))
    for i, element in enumerate(bb["elements"]):
        for f in FACES:
            x, y, w, h = positions[(i, f)]
            element["faces"][f] = {"uv": [x, y, x + w, y + h], "texture": 0}
        if s4.zone_for(model.cubes[i]) == "glow":
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

    s4.render(model, bb, atlas_path, OUT / "renders", views())
    names = [v["name"] for v in views()]
    tw, th, pad, top = 520, 390, 12, 56
    cols = 4
    rows = (len(names) + cols - 1) // cols
    img = Image.new("RGB", (pad + cols * (tw + pad), top + rows * (th + 34 + pad)), sheet.BG)
    from PIL import ImageDraw
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Volley - painted (session 5)", font=sheet._font(28), fill=sheet.INK)
    for k, name in enumerate(names):
        x, y = pad + (k % cols) * (tw + pad), top + (k // cols) * (th + 34 + pad)
        img.paste(sheet._tile(OUT / "renders" / f"{name}.png", tw, th), (x, y))
        dr.text((x, y + th + 6), name.replace("_", " "), font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "sheet.png")
    print(json.dumps({"rows_used": used, "islands": len(positions), "cubes": len(model.cubes)}))


if __name__ == "__main__":
    main()
