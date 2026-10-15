"""The Archevoker, session 8: ship the models.

- src/main/models/occultech_archevoker.bbmodel: the priest on his throne with the ring, from session 7 (the painted
  atlas with the neutral glows, the hitbox, the fifteen clips). The Mythic carrier OCCULTECH_ARCHEVOKER wears it.
- src/main/models/occultech_archevoker_hand_cyan.bbmodel and _purple: the casting hands (their hitboxes, the hidden
  eyelid, the five clips), worn by OCCULTECH_ARCHEVOKER_HAND_CYAN / _PURPLE (BossFight.spawnLookalike).
- Refuses to ship if any two faces share a plane (they flicker in game; bosskit.checks.flicker_pairs).

Run from the repository root after the session scripts (through archevoker_s7.py): python tools/art/bosses/archevoker_ship.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.checks import flicker_pairs  # noqa: E402
from bosses import archevoker_s3 as s3, archevoker_s6 as s6  # noqa: E402

S7 = ROOT / "docs/art/bosses/archevoker/overhaul/s7_animation"
MODELS = ROOT / "src/main/models"
SHIPPED = {
    "occultech_archevoker": (f"{s3.MODEL_ID}.bbmodel", lambda: s3.build("rest")),
    "occultech_archevoker_hand_cyan": ("occultech_archevoker_hand_cyan_rig.bbmodel", lambda: s6.hand_with_lid("cyan")),
    "occultech_archevoker_hand_purple": ("occultech_archevoker_hand_purple_rig.bbmodel",
                                         lambda: s6.hand_with_lid("purple")),
}


def main():
    out = {}
    for model_id, (source, geometry) in SHIPPED.items():
        clash = flicker_pairs(geometry().cubes)
        if clash:
            raise SystemExit(f"{model_id}: faces that would flicker in game: {clash[:5]}")
        rig = json.loads((S7 / source).read_text(encoding="utf-8"))
        rig["name"] = model_id
        for tex in rig["textures"]:
            tex["name"] = f"{model_id}.png"
        (MODELS / f"{model_id}.bbmodel").write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
        out[model_id] = {"animations": sorted(a["name"] for a in rig["animations"]), "elements": len(rig["elements"]),
                         "hidden_bones": [g["name"] for g in rig["groups"] if not g.get("visibility", True)]}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
