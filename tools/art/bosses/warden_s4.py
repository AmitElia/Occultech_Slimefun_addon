"""The Abyssal Warden redesign, session 4: UV and material blocking (plan: docs/art/bosses/abyssal_warden/overhaul/plan.md).

Every visible face of the session 3 rig is mapped at one texel per model unit (16 per block, the vanilla density) into
one atlas, each face a flat colour of its material zone:
- the zones follow the plan's materials: copper in its weathering stages (bright at the crown, exposed, weathered,
  then oxidised verdigris round the open neck, as if the sea crept up him), brass fittings and copper rivets, thick sea
  glass, the crammed eye (a wet yellowed sclera, the sea-glow iris), the creature's flesh, barnacles, kelp, the hose;
- shared islands: the left side window uses the right one's, and each valve on his left its right twin's. The hull's
  panels each keep their own, so the weathering can be painted without repeats;
- a value check: neighbouring zones must stay apart in lightness, so he reads in grey too;
- textured renders in colour and in grey (before 33% and with the hand out), and the three review models (with the
  session 3 poses) copied into run/plugins/BetterModel/models for the first in-game look at the pixel size.

Run from the repository root: python tools/art/bosses/warden_s4.py
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import _uuid  # noqa: E402
import numpy as np  # noqa: E402

from bosses import archevoker_s4 as a4, brood_s4 as b4, volley_crone_s4 as v4  # noqa: E402
from bosses import warden_s2 as s2, warden_s3 as s3  # noqa: E402

OUT = ROOT / "docs/art/bosses/abyssal_warden/overhaul/s4_uv"
SIZE = 512

ZONES = {
    # the hull, weathering from the crown down to the neck (vanilla copper's four stages)
    "copper": (205, 115, 83), "copper_exposed": (135, 101, 83), "copper_weathered": (57, 82, 59),
    "verdigris": (68, 136, 116), "copper_dark": (112, 58, 38), "rivet": (232, 162, 120),
    # the fittings: the window frames, the bars, the valves' wheels, the neck ring, the nozzle
    "brass": (210, 164, 72),
    # the window and the eye behind it
    "glass": (156, 222, 232), "sclera": (179, 171, 150), "flesh_wet": (150, 100, 104),
    "iris": (80, 232, 214), "iris_dark": (24, 128, 132), "pupil": (12, 16, 22), "glint": (250, 252, 255),
    # the creature: its skin, the barnacles, the claws
    "flesh": (104, 130, 112), "flesh_dark": (58, 78, 70), "barnacle": (204, 198, 178), "barnacle_old": (148, 144, 128),
    "nail": (34, 38, 36),
    # the growth's kelp, the hose, the burst glass, the spray
    "kelp": (112, 176, 63), "hose": (70, 56, 44), "hose_band": (182, 142, 62), "shard": (170, 226, 232),
    "spray": (226, 246, 250),
}
ALPHA = {"glass": 96, "shard": 150, "spray": 170}             # see-through: the eye shows through the glass
GLOWING = ("iris", "iris_dark", "glint")
NEIGHBOURS = [("copper", "copper_exposed"), ("copper_exposed", "copper_weathered"), ("copper_weathered", "verdigris"),
              ("copper", "rivet"), ("copper", "brass"), ("verdigris", "brass"), ("copper_exposed", "brass"),
              ("brass", "glass"), ("sclera", "iris"), ("iris", "iris_dark"), ("iris_dark", "pupil"),
              ("sclera", "flesh_wet"), ("brass", "flesh_wet"), ("verdigris", "flesh_dark"), ("flesh", "flesh_dark"),
              ("flesh", "barnacle"), ("flesh_dark", "barnacle_old"), ("flesh", "nail"), ("flesh_dark", "kelp"),
              ("flesh", "kelp"), ("copper", "hose"), ("hose", "hose_band"), ("copper_dark", "brass")]
BAND_ZONES = {0: "verdigris", 1: "verdigris", 2: "copper_weathered", 3: "copper_exposed"}


def hidden(cube, face):
    """brood_s4's buried-face test, but see-through cubes (the glass, the shards, the spray) never bury a face: the
    sclera's front lies inside the window's glass and must still be drawn."""
    if cube.mat in ALPHA or not b4._flat(cube):
        return False
    others = [o for o in cube.group.children
              if not hasattr(o, "children") and o is not cube and b4._flat(o) and o.mat not in ALPHA]
    ax, side = b4.QUAD_AXIS[face]
    lo, hi = np.array(cube.frm), np.array(cube.to)
    a_, b_ = [i for i in range(3) if i != ax]
    for a in np.linspace(0.05, 0.95, 5):
        for b in np.linspace(0.05, 0.95, 5):
            p = lo.copy()
            p[ax] = hi[ax] if side else lo[ax]
            p[a_] = lo[a_] + a * (hi[a_] - lo[a_])
            p[b_] = lo[b_] + b * (hi[b_] - lo[b_])
            if not any(all(o.frm[i] + 1e-6 < p[i] < o.to[i] - 1e-6 for i in range(3)) for o in others):
                return False
    return True


def zone_for(c):
    """The hull's bands weather from the bottom up: oxidised round the neck, then weathered, exposed, bright copper."""
    m = re.match(r"hull_(\d)_", c.name)
    if m:
        return BAND_ZONES.get(int(m[1]), "copper")
    if c.name.startswith("hull_cap_bottom"):
        return "verdigris"
    return c.mat


def twin(name):
    """A part on his left uses its right twin's islands: the left side window, the left valves."""
    name = re.sub(r"^side_l_", "side_r_", name)
    return re.sub(r"^valve([13])_", lambda m: f"valve{int(m[1]) - 1}_", name)


VIEWS = [
    {"name": "hero", "location": (11, 13, 6.5), "target": (0, 0, 3.6), "scale": 10.5, "player": True},
    {"name": "front", "location": (0, 18, 3.8), "target": (0, 0, 3.8), "scale": 8.5, "player": False},
    {"name": "player_eye", "location": (-4.5, 10, 1.62), "target": (0, 0, 3.4), "scale": 9.5, "player": False},
    {"name": "side", "location": (-18, 0, 3.8), "target": (0, 0, 3.8), "scale": 10.0, "player": False},
    {"name": "back", "location": (8, -16, 7), "target": (0, 0, 3.6), "scale": 10.0, "player": False},
    {"name": "eye", "location": (0.8, 10, 4.3), "target": (0, 0, 4.1), "scale": 3.4, "player": False},
]
HAND_VIEWS = [
    {"name": "hero", "location": (-11, 13, 7), "target": (-1.5, 0, 4.0), "scale": 13.0, "player": True},
    {"name": "front", "location": (0, 18, 4.5), "target": (-1.5, 0, 4.5), "scale": 12.0, "player": False},
    {"name": "arm", "location": (-12, 4, 7), "target": (-3.5, -0.5, 5.0), "scale": 7.0, "player": False},
]


def zoned(key):
    m = s3.build(key)
    for c in m.cubes:
        c.mat = zone_for(c)
    return m


def textured(model, name, keys, positions, atlas_path, height, poses, variant):
    s3.visibility(model, variant)
    bb, culled = a4.textured_bbmodel(model, keys, positions, atlas_path, SIZE, height, s2.HITBOX)
    bb["name"] = name
    bb["animations"] = [{"uuid": _uuid(f"{name}/anim/{key}"), "name": key, "loop": "hold", "override": False,
                         "length": 0.5, "snapping": 20, "selected": False, "anim_time_update": "", "blend_weight": "",
                         "start_delay": "", "loop_delay": "", "animators": s3.keyframes(model, *spec)}
                        for key, spec in poses.items()]
    return bb, culled


def shown_model(model, spec):
    """The model with only the cubes a pose shows (for the renders)."""
    keep = set(map(id, s2.shown(model, spec)))
    return [i for i, c in enumerate(model.cubes) if id(c) in keep]


def render(model, bb, atlas_path, out, views, keep):
    import json as _json
    import subprocess
    out.mkdir(parents=True, exist_ok=True)
    boxes = [{"corners": c.corners().tolist(), "from": c.frm, "to": c.to, "glow": c.mat in GLOWING,
              "uv": bb["elements"][i]["faces"]} for i, c in enumerate(model.cubes) if i in keep]
    job = out / "render_job.json"
    job.write_text(_json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes, "views": views,
                                "player_at": (5.0, 3.0)}), encoding="utf-8")
    r = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                        str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job)],
                       capture_output=True, text=True)
    if r.returncode or "TEXTURED_RENDER_DONE" not in r.stdout:
        raise SystemExit(r.stdout[-3000:] + r.stderr[-3000:])
    job.unlink()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.rglob("*"):                               # files only: an open folder can't be removed
        if old.is_file() and old.name != "README.md":
            old.unlink()
    a4.ZONES, a4.GLOWING, a4.twin = ZONES, GLOWING, twin
    a4.b4.hidden = hidden
    model = zoned("idle")
    off = v4.check_density(model)
    if off:
        raise SystemExit("faces off the texel grid: " + ", ".join(off[:10]))
    keys = a4.island_keys(model)
    atlas, positions, used, height = a4.build_atlas(keys, SIZE)
    px = atlas.load()
    for key, (x, y, w, h) in positions.items():               # the see-through zones, border included
        if key[4] in ALPHA:
            for i in range(x - 1, x + w + 1):
                for j in range(y - 1, y + h + 1):
                    if 0 <= i < SIZE and 0 <= j < height:
                        px[i, j] = ZONES[key[4]] + (ALPHA[key[4]],)
    name = s3.MODEL_ID
    atlas_path, grey_path = OUT / f"{name}.png", OUT / f"{name}_grey.png"
    atlas.save(atlas_path)
    grey = atlas.convert("LA").convert("RGBA")
    grey.save(grey_path)
    poses = s3.pose_table()
    culled = 0
    for variant in s3.VARIANTS:
        m = zoned("idle")
        bb, culled = textured(m, name + variant, keys, positions, atlas_path, height, poses, variant)
        path = OUT / f"{name + variant}.bbmodel"
        path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
        if s3.SERVER_MODELS.is_dir():
            shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    bb, _ = textured(model, name, keys, positions, atlas_path, height, {}, "")
    keep = shown_model(model, {})
    render(model, bb, atlas_path, OUT / "colour", VIEWS, keep)
    render(model, bb, grey_path, OUT / "grey", VIEWS, keep)
    a4.review_sheet(OUT, "The Abyssal Warden - UV and material zones (session 4), colour then grey", VIEWS)
    raised = zoned("raised")
    spec = s2.POSES["raised"][1]
    bb_r, _ = textured(raised, name + "_33", keys, positions, atlas_path, height, {}, "_33")
    keep = shown_model(raised, spec)
    render(raised, bb_r, atlas_path, OUT / "hand_colour", HAND_VIEWS, keep)
    render(raised, bb_r, grey_path, OUT / "hand_grey", HAND_VIEWS, keep)
    a4.review_sheet(OUT, "From 33%: the hand raised - colour then grey", HAND_VIEWS,
                    rows=(("hand_colour", "colour"), ("hand_grey", "grey")), name="hand.png")
    texels = sum(w * h for (_, _, w, h) in positions.values())
    report = {"atlas": [SIZE, height], "rows_used": used, "islands": len(positions), "faces_drawn": len(keys),
              "faces_buried_and_left_out": culled, "fill": round(texels / (SIZE * used), 2)}
    rows = [(z, rgb, round(v4.luminance(rgb))) for z, rgb in ZONES.items()]
    close = [(a, b, round(abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])))) for a, b in NEIGHBOURS
             if abs(v4.luminance(ZONES[a]) - v4.luminance(ZONES[b])) < 12]
    report["zones"] = {z: {"rgb": list(rgb), "L": L, **({"alpha": ALPHA[z]} if z in ALPHA else {})} for z, rgb, L in rows}
    report["neighbours_too_close_in_value"] = [f"{a}/{b}: {d}" for a, b, d in close]
    (OUT / "uv_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("atlas", "rows_used", "islands", "faces_drawn", "faces_buried_and_left_out",
                                             "fill", "neighbours_too_close_in_value")}))


if __name__ == "__main__":
    main()
