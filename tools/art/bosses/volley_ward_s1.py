"""Volley's amethyst wards, session 1: three concepts as Blockbench cuboid blockouts.

The wards are the fight objects Volley raises (two at a time, 4 hits each); while one stands he takes 70% less damage
and a beam links it to him. Unlike the crystals on his back, these are targets, so they must read as "break me".
Each concept loses one piece per hit, so the 4 hits show on the model.

  A  Geode spire     a cracked geode erupting from the floor, one tall glowing shard ringed by four smaller ones
  B  Bound crystal   one big crystal staked to a cracked slab by iron staples and chains, a rune band round it
  C  Floating heart  a basalt bowl, a double-pointed crystal hovering above it, three chips orbiting

Run from the repository root: python tools/art/bosses/volley_ward_s1.py
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s1 as s1, volley_crone_s2 as s2  # noqa: E402

OUT = ROOT / "docs/art/bosses/volley/wards/s1_concepts"
CONCEPTS = {"A": "Geode spire", "B": "Bound crystal", "C": "Floating heart"}


def geode_spire():
    m = Model("occultech_volley_ward_a")
    base = m.group("base", (0, 0, 0))
    for i in range(7):
        a = math.radians(i * 360 / 7 + 10)
        h = 4 + (i * 3) % 5
        base.box(f"rim_{i}", (math.cos(a) * 7.5, h / 2, math.sin(a) * 7.5), (5, h, 6), "basalt",
                 rotation=(0, -math.degrees(a), 12))
    base.box("calcite", (0, 1.5, 0), (13, 3, 13), "calcite")
    core = m.group("glow_core", (0, 3, 0))
    s1.crystal(core, "core", (0, 3, 0), 90, 0, 28, 7, "glow")
    for i, (a, pitch, side, length, w) in enumerate(((0, 66, 0, 16, 4), (90, 70, 0, 14, 4), (180, 62, 0, 15, 4),
                                                     (270, 68, 0, 13, 4))):
        piece = m.group(f"shard_{i}", (0, 3, 0))      # one piece breaks off per hit
        r = math.radians(a)
        s1.crystal(piece, f"shard_{i}", (math.cos(r) * 4, 3, math.sin(r) * 4), pitch, 90 - a, length, w, "crystal")
    for i, a in enumerate((45, 160, 250, 330)):
        r = math.radians(a)
        s1.crystal(base, f"bud_{i}", (math.cos(r) * 8.5, 6, math.sin(r) * 8.5), 40, 90 - a, 5, 2, "crystal")
    return m


def bound_crystal():
    m = Model("occultech_volley_ward_b")
    base = m.group("base", (0, 0, 0))
    base.box("slab", (0, 1.5, 0), (16, 3, 16), "basalt")
    base.box("slab_crack", (2, 3.2, -1), (10, 0.6, 2), "calcite", rotation=(0, 30, 0))
    core = m.group("glow_core", (0, 3, 0))
    core.box("crystal", (0, 15, 0), (9, 22, 9), "crystal", rotation=(0, 45, 0))
    core.box("crystal_tip", (0, 28.5, 0), (5, 5, 5), "crystal", rotation=(0, 45, 0))
    core.box("heart", (0, 15, 0), (5, 14, 5), "glow", rotation=(0, 45, 0))
    core.box("rune_band", (0, 12, 0), (11, 2, 11), "iron", rotation=(0, 45, 0))
    for i, (x, z) in enumerate(((6, 6), (-6, 6), (-6, -6), (6, -6))):
        chain = m.group(f"chain_{i}", (x, 3, z))      # one chain snaps per hit
        chain.box(f"staple_{i}", (x, 4, z), (3, 3, 3), "iron")
        s1.beam(chain, f"links_{i}", (x, 5, z), (x * 0.45, 18, z * 0.45), 1.5, "chain")
    return m


def floating_heart():
    m = Model("occultech_volley_ward_c")
    base = m.group("base", (0, 0, 0))
    for i in range(8):
        a = math.radians(i * 45)
        base.box(f"bowl_{i}", (math.cos(a) * 6, 2, math.sin(a) * 6), (5, 4, 4), "basalt", rotation=(0, -i * 45, 0))
    base.box("bowl_floor", (0, 0.75, 0), (11, 1.5, 11), "calcite")
    heart = m.group("glow_core", (0, 18, 0))
    s1.crystal(heart, "heart_up", (0, 18, 0), 90, 0, 12, 6, "glow")
    s1.crystal(heart, "heart_down", (0, 18, 0), -90, 0, 8, 6, "glow")
    for i, a in enumerate((0, 120, 240)):
        chip = m.group(f"chip_{i}", (0, 18, 0))       # one chip falls per hit; the last hit breaks the heart
        r = math.radians(a)
        chip.box(f"chip_{i}", (math.cos(r) * 8, 14 + i * 2, math.sin(r) * 8), (3, 4, 3), "crystal", rotation=(20, a, 15))
    return m


# the boss views, brought in closer for a 2-block prop
VIEWS = [dict(v, **({"dist": v["dist"] * 0.55} if "dist" in v else {}),
              **({"height": min(v["height"], 3.0)} if "height" in v else {})) for v in s1.VIEWS]

BUILDERS = {"A": geode_spire, "B": bound_crystal, "C": floating_heart}


def main():
    for key, build in BUILDERS.items():
        out = OUT / key
        out.mkdir(parents=True, exist_ok=True)
        model = build()
        model.write_bbmodel(out / f"{model.name}.bbmodel")
        s2.run_blender(model.render_json(s1.PALETTE), out, VIEWS)
        stats = model.stats()
        (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        sheet.direction_sheet(out, f"Volley ward - {key} {CONCEPTS[key]}", stats, out / "sheet.png")
        print(key, stats["size_blocks"], stats["cubes"])
    sheet.compare_sheet(OUT, list(CONCEPTS.items()), OUT / "compare.png", heading="Volley's wards - three concepts",
                        views=("sil_eye", "clay_eye", "flat_34"))


if __name__ == "__main__":
    main()
