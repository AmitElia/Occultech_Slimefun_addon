"""Witch Coven, session 8: ship the three sisters.

- src/main/models/occultech_witch_coven_<vessel>.bbmodel: each sister's final rig (E2: the painted model with its
  hitbox, glow bones and every clip: idle, walk, spawn, rotation, heal, curse, throw, death, flinch, cackle, glance),
  carrying the **neutral** brew atlas (session 5): the fight tints the brew bones the role colour (session 6). The
  review rigs carry a pre-tinted atlas instead, so they look right without the fight.
- `h_head` becomes `hi_head`: BetterModel's `hi` (head with children) turns the face, the hat and everything on the
  head with it.
- Refuses to ship if any two faces share a plane (they flicker in game; bosskit.checks.flicker_pairs).

Model names follow the bodies: the Mythic carrier OCCULTECH_WITCH_COVEN_<VESSEL> wears occultech_witch_coven_<vessel>.

Run from the repository root after the session scripts (through coven_e2.py): python tools/art/bosses/coven_ship.py
"""
import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import rename_group  # noqa: E402
from bosskit.checks import flicker_pairs  # noqa: E402
from bosses import coven_e2 as e2, coven_s2 as s2, coven_s3 as s3  # noqa: E402

MODELS = ROOT / "src/main/models"
RIGS = ROOT / "docs/art/bosses/witch_coven/overhaul/fx_clips"
NEUTRAL = ROOT / "docs/art/bosses/witch_coven/overhaul/s5_paint/occultech_coven.png"


def main():
    MODELS.mkdir(parents=True, exist_ok=True)
    neutral = "data:image/png;base64," + base64.b64encode(NEUTRAL.read_bytes()).decode()
    for vessel, role, _ in s2.SISTERS:
        model_id = f"occultech_witch_coven_{vessel}"
        clash = flicker_pairs(s2.build(vessel, role).cubes)
        if clash:
            raise SystemExit(f"{model_id}: faces that would flicker in game: {clash[:5]}")
        rig = json.loads((RIGS / vessel / f"{s3.model_id(vessel)}.bbmodel").read_text(encoding="utf-8"))
        rig["name"] = model_id
        for tex in rig["textures"]:
            tex["source"] = neutral
            tex["name"] = f"{model_id}.png"
        clips = set(e2.clips(vessel, role))
        rig["animations"] = [a for a in rig["animations"] if a["name"] in clips]
        missing = clips - {a["name"] for a in rig["animations"]}
        if missing:
            raise SystemExit(f"{model_id}: missing clips {sorted(missing)}")
        rename_group(rig, "h_head", "hi_head")
        (MODELS / f"{model_id}.bbmodel").write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({"model": model_id, "animations": sorted(a["name"] for a in rig["animations"]),
                          "elements": len(rig["elements"])}))


if __name__ == "__main__":
    main()
