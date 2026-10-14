"""The Masquerade redesign, session 8: ship the models.

- src/main/models/occultech_masquerade.bbmodel: his final rig from session 7 (the painted atlas, the hitbox, the
  eleven clips). The Mythic carriers OCCULTECH_MASQUERADE and OCCULTECH_MASQUERADE_DECOY both wear it: the
  decoys are the same model.
- src/main/models/occultech_masquerade_jack.bbmodel: the Jack-in-the-Box, a fight object's model (rise, idle,
  throw, hit, wind, shatter).
- Refuses to ship if any two faces share a plane (they flicker in game; bosskit.checks.flicker_pairs).

Run from the repository root after the session scripts (through magus_s7.py): python tools/art/bosses/magus_ship.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.checks import flicker_pairs  # noqa: E402
from bosses import magus_s2 as s2, magus_s3 as s3, magus_jack as jack  # noqa: E402

S7 = ROOT / "docs/art/bosses/mirrored_magus/overhaul/s7_animation"
SHIP = [("occultech_masquerade", S7 / f"{s3.MODEL_ID}.bbmodel"),
        ("occultech_masquerade_jack", S7 / "jack" / "occultech_masquerade_jack.bbmodel")]


def check(model, name):
    clash = flicker_pairs(model.cubes)
    if clash:
        raise SystemExit(f"{name}: faces that would flicker in game: {clash[:5]}")


def main():
    s2.MASK = "clown"
    magus = s2.build("check")
    s2.finish(magus)
    check(magus, "occultech_masquerade")
    box = jack.build()
    s2.finish(box)
    jack.settle(box)
    check(box, "occultech_masquerade_jack")
    for model_id, rig_path in SHIP:
        rig = json.loads(rig_path.read_text(encoding="utf-8"))
        rig["name"] = model_id
        for tex in rig["textures"]:
            tex["name"] = f"{model_id}.png"
        out = ROOT / "src/main/models" / f"{model_id}.bbmodel"
        out.write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({"model": model_id, "animations": sorted(a["name"] for a in rig["animations"]),
                          "elements": len(rig["elements"])}))


if __name__ == "__main__":
    main()
