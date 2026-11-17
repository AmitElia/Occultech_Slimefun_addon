"""The Abyssal Warden redesign, session 3: rig and pose test (plan: docs/art/bosses/abyssal_warden/overhaul/plan.md).

On top of the session 2 design lock (warden_s2.py), with the same look, a display pass. Session 2 cost about 245
displays, because BetterModel needs one more display for every cube turn it can't keep in a bone's item model
(anything but one 0, 22.5 or 45-degree turn, or a quarter turn plus one of those):
- **the hull:** each of its 12 columns of panels is its own bone, turned to its place round the sphere. Inside it the
  panels only tilt, and the latitude bands are re-cut so every tilt is a multiple of 22.5 degrees (0, 22.5, 45, 67.5);
- **the side windows** keep their own groups as bones (session 2 baked them into the body, which gave every frame
  slab a turn of its own);
- **the kelp and the tendrils** lean out in the four square directions only, by 22.5 or 45 degrees;
- **the flesh round the eye** is 8 lumps, 45 degrees apart (it was 9, 40 apart);
- quarter turns folded, as on the Archevoker.
Then: a pivot check, a BetterModel tag check, a flat colour per material, and the nine key poses as BetterModel
animations in three review models: `occultech_abyssal_warden_rig` (before 33%), `_rig_spikes` (the spray jets shown)
and `_rig_33` (the side window burst, the hand out).

Output: docs/art/bosses/abyssal_warden/overhaul/s3_rig/, plus the review models copied into
run/plugins/BetterModel/models. They are never shipped.

Run from the repository root: python tools/art/bosses/warden_s3.py
"""
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, _uuid, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosskit.checks import flicker_pairs  # noqa: E402
from bosses import volley_crone_s2 as v2, volley_crone_s3 as v3, archevoker_s3 as a3  # noqa: E402
from bosses import warden_silhouettes as w1, warden_take2 as t2, warden_window as ww, warden_s2 as s2  # noqa: E402

OUT = ROOT / "docs/art/bosses/abyssal_warden/overhaul/s3_rig"
SERVER_MODELS = ROOT / "run/plugins/BetterModel/models"
MODEL_ID = "occultech_abyssal_warden_rig"
GLOWING = ("iris", "iris_dark", "glint")
INTENDED = {"glow_iris": {"glow"}, "ob_hitbox": {"ob"}}


# ---- the display pass: builders that keep their turns legal ----------------------------------------------------------

BANDS = (-78.75, -56.25, -33.75, -11.25, 11.25, 33.75, 56.25, 78.75)     # each band's tilt is a multiple of 22.5


def sphere(g, name, c, r, mat, skip=lambda d: False, n=12, bands=BANDS, t=3.0, band_mats=None):
    """take 1's sphere of panels, a column per bone: the column bone turns round the sphere (any angle: a bone's own
    turn is free), and its panels only tilt about x (multiples of 22.5, which an item model keeps)."""
    cx, cy, cz = c
    for i in range(n):
        a = 360 * i / n + 180 / n
        col = None
        for b, (p0, p1) in enumerate(zip(bands, bands[1:])):
            y0, y1 = cy + r * math.sin(math.radians(p0)), cy + r * math.sin(math.radians(p1))
            r0, r1 = r * math.cos(math.radians(p0)), r * math.cos(math.radians(p1))
            h = y1 - y0
            tilt = (p0 + p1) / 2                             # the chord between two latitudes leans by their mean
            slant = math.hypot(h, r0 - r1)
            rm = (r0 + r1) / 2
            width = 2 * max(r0, r1) * math.tan(math.pi / n) * 1.04     # wide enough at the band's wider edge
            pm = math.radians(tilt)
            ar = math.radians(a)
            d = np.array([math.sin(ar) * math.cos(pm), math.sin(pm), math.cos(ar) * math.cos(pm)])
            m = band_mats[min(max(b - 1, 0), len(band_mats) - 1)] if band_mats else mat   # one band more below
            centre = np.array((cx, (y0 + y1) / 2, cz + rm))
            if not skip(d):
                if col is None:
                    col = g.group(f"{name}_col{i}", c, (0, a, 0))
                col.box(f"{name}_{b}_{i}", tuple(centre), (width, slant, t), m, rotation=(-tilt, 0, 0))
                continue
            # a panel by an opening: only the tiles over the opening go, so no slot opens round the window's frame.
            # The tiles keep the panel's tilt, so they cost no display.
            tr = np.array([[1, 0, 0], [0, math.cos(pm), math.sin(pm)], [0, -math.sin(pm), math.cos(pm)]])
            yaw = np.array([[math.cos(ar), 0, math.sin(ar)], [0, 1, 0], [-math.sin(ar), 0, math.cos(ar)]])
            for u in range(TILES):
                for v in range(TILES):
                    p = centre + tr @ np.array((((u + 0.5) / TILES - 0.5) * width, ((v + 0.5) / TILES - 0.5) * slant, 0))
                    dd = yaw @ (p - np.array(c))
                    if skip(dd / np.linalg.norm(dd)):
                        continue
                    if col is None:
                        col = g.group(f"{name}_col{i}", c, (0, a, 0))
                    col.box(f"{name}_{b}_{i}_tile{u}{v}", tuple(p), (width / TILES, slant / TILES, t), m,
                            rotation=(-tilt, 0, 0))
    for nm, p in ((name + "_cap_top", math.radians(bands[-1])), (name + "_cap_bottom", math.radians(bands[0]))):
        rr = r * math.cos(p) + 0.6
        y = cy + r * math.sin(p)
        g.box(nm + "_a", (cx, y, cz), (2 * rr * 0.83, t, 2 * rr * 0.83), mat)
        g.box(nm + "_b", (cx, y, cz), (2 * rr * 0.83, t, 2 * rr * 0.83), mat, rotation=(0, 45, 0))


TILES = 3                                                   # a panel by an opening is cut into 3 x 3 tiles


CARDINAL = ((0, 1), (1, 0), (0, -1), (-1, 0))               # (x, z): the four ways a strand may lean


def lean(g, name, start, length, size, deg, way, mat):
    """A strand segment hanging from `start`, leaning `deg` (a multiple of 22.5) towards a square direction. Its
    width runs across the lean, its thickness along it. Returns its lower end."""
    sx, sz = way
    t = math.radians(deg)
    d = np.array([sx * math.sin(t), -math.cos(t), sz * math.sin(t)])
    end = np.array(start, float) + d * length
    mid = (np.array(start, float) + end) / 2
    w, th = size
    if sz:                                                   # leaning along z: turn about x
        g.box(name, tuple(mid), (w, length, th), mat, rotation=(-sz * deg, 0, 0))
    else:                                                    # leaning along x: turn about z
        g.box(name, tuple(mid), (th, length, w), mat, rotation=(0, 0, sx * deg))
    return end


def nearest_way(a):
    s, c = math.sin(a), math.cos(a)
    return max(CARDINAL, key=lambda w: w[0] * s + w[1] * c)


def growth(g):
    """take 2's growth (the fleshy mass, ten tendrils, 22 kelp strands), each strand leaning in a square direction."""
    ny = t2.C[1] - t2.R * 0.74
    t2.lump(g, "mass", (0, ny - 3, 2), 26, "flesh_dark")
    t2.lump(g, "mass_low", (3, ny - 10, 5), 16, "flesh")
    for i, (x, z, sz) in enumerate(((-11, -4, 9), (10, 8, 8), (-6, 12, 7), (12, -6, 6))):
        t2.lump(g, f"mass_swell{i}", (x, ny - 6, z), sz, "flesh")
    rng = np.random.default_rng(7)
    for i in range(10):                                      # tendrils: thick, curling outwards as they go down
        a = math.radians(i * 36 + 15)
        r0 = 7 + i % 3 * 3
        p = np.array([math.sin(a) * r0, ny - 6, math.cos(a) * r0 + 3])
        way = nearest_way(a)
        length = 12 + (i * 7) % 9
        for k, (deg, share) in enumerate(((0, 0.3), (22.5, 0.35), (45, 0.45))):
            w = 6.5 - k * 1.8
            p = lean(g, f"tendril{i}_{k}", p, length * share + 1, (w, w), deg, way,
                     "flesh" if k % 2 == 0 else "flesh_dark")
    for i in range(22):                                      # kelp: flat ragged strands, uneven, two leans each
        a = math.radians(i * 16.4 + 5)
        r0 = 6 + (i % 4) * 3.5
        root = np.array([math.sin(a) * r0, ny - 2, math.cos(a) * r0 + 2])
        length = 12 + rng.integers(0, 12)
        out = nearest_way(a)
        sway = CARDINAL[(CARDINAL.index(out) + (1 if i % 2 else 3)) % 4]
        p1 = lean(g, f"kelp{i}_0", root, length * 0.5, (4, 0.8), 22.5, out, "kelp")
        lean(g, f"kelp{i}_1", p1, length * 0.5, (3, 0.8), 22.5 if i % 3 else 0, sway if i % 3 else out, "kelp")
        g.box(f"kelp{i}_bulb", tuple(root + np.array([0, -3, 0])), (2.4, 2.4, 2.4), "kelp", rotation=(0, 45, 0))


_flesh_rim = ww.flesh_rim


def flesh_rim(w, name, x, y, z, rw, n=8, size=6.5):
    """The flesh bulging into the eye's window: 8 lumps, 45 degrees apart."""
    for i in range(n):
        a = math.radians(360 * i / n + 22.5)
        w.box(f"{name}_flesh{i}", (x + math.sin(a) * (rw - 1.5), y + math.cos(a) * (rw - 1.5), z + 2.2),
              (size, size * 0.8, 3), "flesh_wet", rotation=(0, 0, 360 * i / n))


def patched():
    w1.sphere, t2.growth, ww.flesh_rim = sphere, growth, flesh_rim
    s2.BAKE_ALL_GROUPS = False


def build(key):
    patched()
    m = s2.build(key)
    for old, new in (("side_l", "window_l"), ("side_r", "window_r")):
        s2.group(m, old).name = new
    a3.fold_quarter_turns(m)
    return m


# ---- the review models -----------------------------------------------------------------------------------------------

VARIANTS = {
    "": "before 33%: the side window whole, the hand and the spray hidden",
    "_spikes": "the spray jets shown (the spike burst)",
    "_33": "from 33%: the side window burst, the hand out",
}


def visibility(m, variant):
    shown = {"": set(), "_spikes": {"spray"}, "_33": {"window_r_burst", "arm", "forearm", "hand"}}[variant]
    for g in m.groups:
        if g.name in ("spray", "window_r_burst", "arm", "forearm", "hand"):
            g.visible = g.name in shown
        if g.name == "window_r_glass":
            g.visible = variant != "_33"


def pose_table():
    """Per pose: the bones turned away from rest (absolute rotations), position offsets and the pupil's scale."""
    rest = {g.name: tuple(g.rotation) for g in build("idle").groups}
    out = {}
    for key, (_, spec) in s2.POSES.items():
        posed = build(key)
        rot = {g.name: tuple(g.rotation) for g in posed.groups
               if g.name in rest and any(abs(a - b) > 1e-6 for a, b in zip(g.rotation, rest[g.name]))}
        pos = {}
        if spec.get("base"):
            pos["base"] = tuple(map(float, spec["base"]))
        lx, ly = spec.get("look", (0.2, -0.1))
        if (lx, ly) != (0.2, -0.1):
            pos["glow_iris"] = (16 * (lx - 0.2), 16 * (ly + 0.1), 0.0)
        if spec.get("valves"):
            for i, d in enumerate(s2.VALVES):
                d = np.array(d, float) / np.linalg.norm(d) * spec["valves"]
                pos[f"valve{i}"] = tuple(map(float, d))
        scale = {"pupil": (spec["pupil"], 1.0, 1.0)} if spec.get("pupil") else {}
        out[key] = (rot, pos, scale)
    return out


def keyframes(model, rot, pos, scale):
    animators = v3.keyframes(model, rot)

    def channel(name, kind, point):
        frames = [{"channel": kind, "data_points": [point], "uuid": _uuid(f"{model.name}/kf{kind}/{name}/{t}"),
                   "time": t, "color": -1, "interpolation": "linear"} for t in (0, 0.5)]
        uid = _uuid(f"{model.name}/group/{name}")
        animators.setdefault(uid, {"name": name, "type": "bone", "keyframes": []})["keyframes"] += frames

    for name, (x, y, z) in pos.items():
        channel(name, "position", {"x": round(-x, 2), "y": round(y, 2), "z": round(z, 2)})
    for name, (x, y, z) in scale.items():
        channel(name, "scale", {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3)})
    return animators


def flat_bbmodel(model, name, animations):
    v3.s2.PALETTE = v2.PALETTE
    img, uv, png = v3.material_atlas(model)
    import base64
    texture = {"name": f"{name}.png", "path": "", "folder": "", "namespace": "", "id": "0", "group": "",
               "width": 32, "height": 32, "uv_width": 32, "uv_height": 32, "particle": False,
               "use_as_default": True, "layers_enabled": False, "render_mode": "default", "render_sides": "auto",
               "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False,
               "visible": True, "internal": True, "saved": False, "uuid": _uuid(name + "/atlas"),
               "source": "data:image/png;base64," + base64.b64encode(png).decode()}
    model.name = name
    bb = model.to_bbmodel(texture_size=(32, 32), textures=(texture,))
    for element, cube in zip(bb["elements"], model.cubes):
        for face in FACES:
            element["faces"][face] = {"uv": list(uv[cube.mat]), "texture": 0}
        if cube.mat in GLOWING:
            element["light_emission"] = 15
    add_hitbox(bb, *s2.HITBOX)
    bb["animations"] = [{"uuid": _uuid(f"{name}/anim/{key}"), "name": key, "loop": "hold", "override": False,
                         "length": 0.5, "snapping": 20, "selected": False, "anim_time_update": "",
                         "blend_weight": "", "start_delay": "", "loop_delay": "",
                         "animators": keyframes(model, *spec)} for key, spec in animations.items()]
    return bb, img


def report(model):
    rows, bad = v3.pivot_report(model)
    found = {}
    for g in model.groups:
        tags = {w for w in g.name.lower().split("_") if w in v3.BETTERMODEL_TAGS}
        if tags:
            found[g.name] = tags
    found["ob_hitbox"] = {"ob"}
    wrong = {n: sorted(t) for n, t in found.items() if INTENDED.get(n) != t}
    total, per_bone = v3.display_count(model)
    hidden = {"spray", "window_r_burst", "arm", "forearm", "hand"}
    return {"bones_with_cubes": len(per_bone), "cubes": len(model.cubes), "displays": total,
            "displays_at_spawn": sum(v for k, v in per_bone.items() if k not in hidden),
            "flicker_pairs": len(flicker_pairs(model.cubes)), "pivots_to_check": bad,
            "tags": {n: sorted(t) for n, t in found.items()}, "unintended_tags": wrong,
            "hitbox_blocks": [round((t - f) / 16, 2) for f, t in zip(*s2.HITBOX)],
            "displays_per_bone": dict(sorted(per_bone.items(), key=lambda kv: -kv[1]))}, rows


VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 40, "height": 3.8, "dist": 15, "target_z": 3.9},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.6, "dist": 14, "target_z": 3.8,
     "player": False},
    {"name": "flat_back", "mode": "flat", "camera": "persp", "yaw": 160, "height": 4.4, "dist": 15, "target_z": 3.8,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.rglob("*"):                               # files only: an open folder can't be removed
        if old.is_file() and old.name != "README.md":
            old.unlink()
    v2.PALETTE.update(s2.PALETTE)
    poses = pose_table()
    paths = []
    for variant in VARIANTS:
        model = build("idle")
        visibility(model, variant)
        bb, img = flat_bbmodel(model, MODEL_ID + variant, poses)
        p = OUT / f"{MODEL_ID + variant}.bbmodel"
        p.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
        paths.append(p)
    img.resize((256, 256), 0).save(OUT / "material_atlas.png")
    model = build("idle")
    rep, rows = report(model)
    rep["animations"] = list(poses)
    rep["review_models"] = {MODEL_ID + k: v for k, v in VARIANTS.items()}
    (OUT / "rig_report.json").write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
    (OUT / "pivots.md").write_text("# The Abyssal Warden: rig pivots (session 3)\n\nGenerated by "
                                   "`tools/art/bosses/warden_s3.py`. Gap = distance from the pivot to the bone's "
                                   "nearest cube, in model units.\n\n| Bone | Pivot | Gap | |\n|---|---|---|---|\n"
                                   + "\n".join(rows) + "\n", encoding="utf-8")
    if SERVER_MODELS.is_dir():
        for p in paths:
            shutil.copyfile(p, SERVER_MODELS / p.name)
    # the rig as it goes in game (before 33%) and after the burst, next to session 2's
    v2.run_blender(s2.render(model, {}), OUT / "rig", VIEWS)
    after = build("raised")
    v2.run_blender(s2.render(after, s2.POSES["raised"][1]), OUT / "rig_33", VIEWS)
    sheet.compare_sheet(OUT, [("rig", "before 33%"), ("rig_33", "from 33%: the hand raised")], OUT / "rig.png",
                        heading="The Abyssal Warden - session 3: the rig",
                        views=("flat_34", "flat_front", "flat_back", "sil_side"))
    s2v = ROOT / "docs/art/bosses/abyssal_warden/overhaul/s2_design/design"
    s2.side_by_side([s2v / "flat_34.png", OUT / "rig" / "flat_34.png"], OUT / "before_after.png")
    boxes = model.render_json(s2.PALETTE)
    for b in boxes:
        b["color"] = [c * 0.5 + 0.45 for c in b["color"]]
    for g in model.groups:
        p = v3.world_pivot(g)
        boxes.append(v2.box_json("pivot_" + g.name, (p - 1.2).tolist(), (p + 1.2).tolist(), "hitbox"))
    v2.run_blender(boxes, OUT / "pivots", v3.PIVOT_VIEWS)
    s2.side_by_side([OUT / "pivots/pivots_front.png", OUT / "pivots/pivots_side.png"], OUT / "pivots.png")
    print(json.dumps({k: rep[k] for k in ("bones_with_cubes", "cubes", "displays", "displays_at_spawn",
                                          "flicker_pairs", "pivots_to_check", "unintended_tags", "displays_per_bone")}))


if __name__ == "__main__":
    main()
