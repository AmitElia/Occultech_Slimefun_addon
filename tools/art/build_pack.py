"""Build Occultech's resource pack from the finished art.

For every item in docs/recipes.yml it looks for that item's texture in the art sessions (A, C-F) by the slug of its
display name, and writes - all in Occultech's own `occultech` namespace, so no vanilla item is ever retextured:

    assets/occultech/items/<key>.json          item model definition (what the `item_model` component points at)
    assets/occultech/models/item/<key>.json    the model (generated, handheld for weapons, the bow's own for bows)
    assets/occultech/textures/item/<key>.png   the texture; animated icons become a vertical strip + .png.mcmeta

The pack is written to src/main/pack/occultech-pack.zip (packaged into the plugin jar, unfiltered) together with
occultech-pack-items.txt, the item ids that have a model - the plugin only sets `item_model` on those.

Run: python tools/art/build_pack.py
"""
import io
import json
import os
import sys
import zipfile

import yaml
from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
ART = os.path.join(ROOT, "docs", "art")
OUT = os.path.join(ROOT, "src", "main", "pack")
SESSIONS = ["session-a", "session-c", "session-d", "session-e", "session-f"]
PACK_FORMAT = 88          # resource pack format of Minecraft 26.2 (from the server jar's version.json)
FRAMETIME = 4             # ticks per animation frame (0.2 s)
NS = "occultech"
HANDHELD = {"weapon"}     # held like a tool in third person
BOW_STATES = ["standby", "pulling_0", "pulling_1", "pulling_2"]
FIXED_DATE = (2026, 1, 1, 0, 0, 0)   # deterministic zip: same art, same bytes, same hash

# ---- custom blocks (Session N): Occultech's blocks as real block states, the way Nexo does it ----
# Each block look gets a vanilla block state of its own, set aside for it, and the pack's blockstate files show the
# block's model for that state. Solid blocks use note-block states (Nexo's NOTEBLOCK type); the flat, walk-through
# ritual glyphs use tripwire states (Nexo's STRINGBLOCK type). The states are recorded in BLOCK_STATES and NEVER change
# once given out - placed blocks are stored as their state. New looks get the next free state.
BLOCK_STATES = os.path.join(os.path.dirname(__file__), "block_states.json")
VANILLA_TRIPWIRE = os.path.join(os.path.dirname(__file__), "vanilla_tripwire.json")   # from the 26.2 client
VANILLA_CHORUS = os.path.join(os.path.dirname(__file__), "vanilla_chorus_plant.json")
STRING_BLOCKS = {"chalk_glyph", "bound_glyph", "abyssal_glyph", "hollow_glyph"}
FACINGS = {"occult_forge": ["north", "east", "south", "west"]}   # blocks with a front: a state per facing
FACING_Y = {"north": 0, "east": 90, "south": 180, "west": 270}
# Note-block states set aside: powered=true (vanilla note blocks never get there once Paper's noteblock updates are
# off, as Nexo also requires), notes 1-24 (a freshly placed powered note block is note 0), the 16 classic instruments.
NOTE_INSTRUMENTS = ["harp", "basedrum", "snare", "hat", "bass", "flute", "bell", "guitar", "chime", "xylophone",
                    "iron_xylophone", "cow_bell", "didgeridoo", "bit", "banjo", "pling"]
ALL_INSTRUMENTS = NOTE_INSTRUMENTS + ["trumpet", "trumpet_exposed", "trumpet_oxidized", "trumpet_weathered", "zombie",
                                      "skeleton", "creeper", "dragon", "wither_skeleton", "piglin", "custom_head"]
# Chorus-plant states set aside (Nexo's CHORUSBLOCK type) for models smaller than a full cube: a note block is a solid
# cube to the client, which hides every touching block's face - through a smaller model you'd see the sky (the "blue
# bottom"). A chorus plant hides nothing. The states: up=false and down=false (natural chorus trees all but never make a
# piece with neither), the four sides free - 16 states. Needs Paper's disable-chorus-plant-updates.
CHORUS_SIDES = ["east", "north", "south", "west"]
# Tripwire states set aside: disarmed=true (vanilla string only gets there while being cut with shears), the other six
# booleans free - 64 states.
TRIPWIRE_SIDES = ["attached", "east", "north", "south", "west", "powered"]


def note_state(slot):
    return f"minecraft:note_block[instrument={NOTE_INSTRUMENTS[slot // 24]},note={slot % 24 + 1},powered=true]"


def tripwire_state(slot):
    v = {name: "true" if slot >> i & 1 else "false" for i, name in enumerate(TRIPWIRE_SIDES)}
    return ("minecraft:tripwire[attached={attached},disarmed=true,east={east},north={north},powered={powered},"
            "south={south},west={west}]").format(**v)


def chorus_state(slot):
    v = {name: "true" if slot >> i & 1 else "false" for i, name in enumerate(CHORUS_SIDES)}
    return "minecraft:chorus_plant[down=false,east={east},north={north},south={south},up=false,west={west}]".format(**v)


def is_full(model):
    """Whether the model fills its block's six faces (an element spanning each whole face at the block's edge)."""
    for i in range(3):
        others = [j for j in range(3) if j != i]
        for val in (0, 16):
            if not any(e["from"][i] <= val <= e["to"][i] and all(e["from"][k] <= 0 and e["to"][k] >= 16 for k in others)
                       for e in model["elements"]):
                return False
    return True


def block_kind(state):
    return state[len("minecraft:"):state.index("[")]


def state_props(state):
    return dict(kv.split("=") for kv in state[state.index("[") + 1:-1].split(","))


def custom_blocks(skins, gdir):
    """Gives every block look its state (keeping the ones already given out) and returns
    [(item_id, look, facing, state, model_key, y)] plus the retired states [(item_id, state, model_key, y)].
    A look whose kind of block changed (a model that stopped filling its cube) gets a new state; its old one is
    retired - never given out again, and still shown with the model until the plugin converts the placed blocks."""
    given = json.load(open(BLOCK_STATES, encoding="utf-8")) if os.path.exists(BLOCK_STATES) else {}
    used = set(given.values())
    out = []
    makers = {"tripwire": (tripwire_state, 64), "note_block": (note_state, 24 * len(NOTE_INSTRUMENTS)),
              "chorus_plant": (chorus_state, 16)}
    for base in sorted(skins):
        model0 = json.load(open(os.path.join(gdir, base, "model.json"), encoding="utf-8"))
        kind = "tripwire" if base in STRING_BLOCKS else "note_block" if is_full(model0) else "chorus_plant"
        for look in range(skins[base]):
            for facing in FACINGS.get(base, ["-"]):
                key = f"{base.upper()} {look} {facing}"
                if key in given and block_kind(given[key]) != kind:
                    n = sum(1 for k in given if k.startswith(f"~retired {key}"))
                    given[f"~retired {key} {n}"] = given.pop(key)
                if key not in given:
                    make, limit = makers[kind]
                    slot = 0
                    while make(slot) in used:
                        slot += 1
                    if slot >= limit:
                        raise SystemExit(f"out of {kind} states")
                    given[key] = make(slot)
                    used.add(given[key])
                model = base if look == 0 else f"{base}_v{look}"
                # a skin's item display drew the model turned half a turn from a block; the blockstate keeps the
                # approved look: plain blocks turn 180, a front faces its way (north = as drawn)
                y = FACING_Y[facing] if facing != "-" else 180
                out.append((base.upper(), look, facing, given[key], model, y))
    retired = []
    for k, state in given.items():
        if k.startswith("~retired "):
            item, look, facing = k.split(" ")[1:4]
            if item.lower() in skins:
                model = item.lower() if look == "0" else f"{item.lower()}_v{look}"
                retired.append((item, state, model, FACING_Y[facing] if facing != "-" else 180))
    with open(BLOCK_STATES, "w", encoding="utf-8", newline="\n") as f:
        json.dump(dict(sorted(given.items())), f, indent=1)
        f.write("\n")
    return out, retired


def blockstate_files(blocks, retired):
    """note_block.json, tripwire.json, chorus_plant.json: our states show our models; every other state keeps vanilla's
    look."""
    def apply(model, y):
        a = {"model": model}
        if y:
            a["y"] = y
        return a
    ours = {b[3]: apply(f"{NS}:block/{b[4]}", b[5]) for b in blocks}
    ours.update({r[1]: apply(f"{NS}:block/{r[2]}", r[3]) for r in retired})
    note = [{"when": {"powered": "false"}, "apply": {"model": "minecraft:block/note_block"}}]
    taken = {}
    for state, a in ours.items():
        if state.startswith("minecraft:note_block"):
            pr = state_props(state)
            taken.setdefault(pr["instrument"], set()).add(int(pr["note"]))
            note.append({"when": {"instrument": pr["instrument"], "note": pr["note"], "powered": "true"}, "apply": a})
    for inst in ALL_INSTRUMENTS:
        free = [str(n) for n in range(25) if n not in taken.get(inst, set())]
        if len(free) == 25:
            continue
        note.append({"when": {"instrument": inst, "note": "|".join(free), "powered": "true"},
                     "apply": {"model": "minecraft:block/note_block"}})
    untouched = [i for i in ALL_INSTRUMENTS if i not in taken]
    if untouched:
        note.append({"when": {"instrument": "|".join(untouched), "powered": "true"}, "apply": {"model": "minecraft:block/note_block"}})
    vanilla = json.load(open(VANILLA_TRIPWIRE, encoding="utf-8"))["variants"]
    trip = []
    for key, a in vanilla.items():
        when = state_props("x[" + key + "]")
        trip.append({"when": dict(when, disarmed="false"), "apply": a})
    for slot in range(64):
        state = tripwire_state(slot)
        pr = state_props(state)
        a = ours.get(state) or vanilla[",".join(f"{k}={pr[k]}" for k in ["attached", "east", "north", "south", "west"])]
        trip.append({"when": pr, "apply": a})
    # chorus_plant: vanilla's parts, each limited to states that aren't ours, then ours
    taken_chorus = {tuple(state_props(st)[k] for k in CHORUS_SIDES) for st in ours if block_kind(st) == "chorus_plant"}
    free = [dict(zip(CHORUS_SIDES, combo), up="false", down="false")
            for combo in (tuple("true" if slot >> i & 1 else "false" for i in range(4)) for slot in range(16))
            if combo not in taken_chorus]
    not_ours = {"OR": [{"up": "true"}, {"down": "true"}] + free}
    chorus = [{"when": {"AND": [part["when"], not_ours]}, "apply": part["apply"]}
              for part in json.load(open(VANILLA_CHORUS, encoding="utf-8"))["multipart"]]
    for state, a in ours.items():
        if block_kind(state) == "chorus_plant":
            chorus.append({"when": state_props(state), "apply": a})
    return {"assets/minecraft/blockstates/note_block.json": {"multipart": note},
            "assets/minecraft/blockstates/tripwire.json": {"multipart": trip},
            "assets/minecraft/blockstates/chorus_plant.json": {"multipart": chorus}}


def nexo_config(blocks, items):
    """A draft Nexo item config for the same blocks (Session N: finished and tested on the Nexo server). Nexo gives
    out its own states from custom_variation; the plugin's conversion command re-places placed blocks through Nexo."""
    lines = ["# Occultech blocks for Nexo - DRAFT, generated by tools/art/build_pack.py; finish and test on the Nexo",
             "# server (docs/nexo-migration.md). The models come from Occultech's pack (handed to Nexo as an external pack).", ""]
    variation = {"NOTEBLOCK": 0, "STRINGBLOCK": 0, "CHORUSBLOCK": 0}
    for (item_id, look, facing, state, model, y) in blocks:
        if facing not in ("-", "north"):
            continue   # Nexo turns a directional block itself (directional: type: FURNACE)
        kind = {"tripwire": "STRINGBLOCK", "chorus_plant": "CHORUSBLOCK"}.get(block_kind(state), "NOTEBLOCK")
        variation[kind] += 1
        nexo_id = f"occultech_{model}"
        name = items.get(item_id, {}).get("name", item_id)
        lines += [f"{nexo_id}:", f"  itemname: \"{name}\"", "  material: PAPER", "  Pack:",
                  f"    model: {NS}:block/{model}", "  Mechanics:", "    custom_block:", f"      type: {kind}",
                  f"      custom_variation: {variation[kind]}", f"      model: {NS}:block/{model}"]
        if facing == "north":
            lines += ["      directional:", "        type: FURNACE"]
        lines.append("")
    return "\n".join(lines)


def slug(name):
    return name.lower().replace("'", "").replace(":", "").replace(" ", "_")


def find_art(name):
    """('static', path) | ('frames', [paths]) | ('bow', {state: path}) | None"""
    s = slug(name)
    for session in SESSIONS:
        d = os.path.join(ART, session)
        if os.path.exists(os.path.join(d, f"{s}_{BOW_STATES[0]}.png")):
            return "bow", {st: os.path.join(d, f"{s}_{st}.png") for st in BOW_STATES}
        frames = []
        while os.path.exists(os.path.join(d, f"{s}_{len(frames)}.png")):
            frames.append(os.path.join(d, f"{s}_{len(frames)}.png"))
        if frames:
            return "frames", frames
        if os.path.exists(os.path.join(d, f"{s}.png")):
            return "static", os.path.join(d, f"{s}.png")
    return None


def png_bytes(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def model_ref(key):
    return f"{NS}:item/{key}"


def plain_definition(key):
    return {"model": {"type": "minecraft:model", "model": model_ref(key)}}


def bow_definition(key):
    """Like the vanilla bow's: the standby model, and while drawing the three pulling models by draw time."""
    m = lambda suffix: {"type": "minecraft:model", "model": model_ref(key + suffix)}  # noqa: E731
    return {"model": {
        "type": "minecraft:condition", "property": "minecraft:using_item",
        "on_false": m(""),
        "on_true": {"type": "minecraft:range_dispatch", "property": "minecraft:use_duration", "scale": 0.05,
                    "fallback": m("_pulling_0"),
                    "entries": [{"threshold": 0.65, "model": m("_pulling_1")}, {"threshold": 0.9, "model": m("_pulling_2")}]},
    }}


def main():
    with open(os.path.join(ROOT, "docs", "recipes.yml"), encoding="utf-8") as f:
        items = yaml.safe_load(f)["items"]
    files = {}
    with_models, without = [], []
    for item_id, item in items.items():
        key = item_id.lower()
        art = find_art(item["name"])
        if art is None:
            without.append(f"T{item.get('tier')} {item_id} ({item.get('cat')})")
            continue
        kind, src = art
        parent = "minecraft:item/handheld" if item.get("cat") in HANDHELD else "minecraft:item/generated"
        if kind == "bow":
            files[f"assets/{NS}/items/{key}.json"] = bow_definition(key)
            for st in BOW_STATES:
                suffix = "" if st == "standby" else "_" + st
                files[f"assets/{NS}/models/item/{key}{suffix}.json"] = {
                    "parent": "minecraft:item/bow", "textures": {"layer0": model_ref(key + suffix)}}
                files[f"assets/{NS}/textures/item/{key}{suffix}.png"] = png_bytes(Image.open(src[st]).convert("RGBA"))
        else:
            files[f"assets/{NS}/items/{key}.json"] = plain_definition(key)
            files[f"assets/{NS}/models/item/{key}.json"] = {"parent": parent, "textures": {"layer0": model_ref(key)}}
            if kind == "static":
                img = Image.open(src).convert("RGBA")
                assert img.size == (16, 16), (src, img.size)
                files[f"assets/{NS}/textures/item/{key}.png"] = png_bytes(img)
            else:
                frames = [Image.open(p).convert("RGBA") for p in src]
                for p, fr in zip(src, frames):
                    assert fr.size == (16, 16), (p, fr.size)
                strip = Image.new("RGBA", (16, 16 * len(frames)))
                for i, fr in enumerate(frames):
                    strip.paste(fr, (0, 16 * i))
                files[f"assets/{NS}/textures/item/{key}.png"] = png_bytes(strip)
                files[f"assets/{NS}/textures/item/{key}.png.mcmeta"] = {"animation": {"frametime": FRAMETIME}}
        with_models.append(item_id)

    # blocks (Session G): each model folder becomes a block model + its textures; the item definition (used by the
    # block's item in the inventory and by the skin display over the placed block) points at that model
    skins = {}
    gdir = os.path.join(ART, "session-g")
    for key in sorted(os.listdir(gdir)) if os.path.isdir(gdir) else []:
        mpath = os.path.join(gdir, key, "model.json")
        if not os.path.exists(mpath):
            continue
        with open(mpath, encoding="utf-8") as f:
            model = json.load(f)
        for el in model["elements"]:   # the game rejects a whole model (black and purple) if one element leaves -16..32
            if any(c < -16 or c > 32 for c in el["from"] + el["to"]):
                raise SystemExit(f"{key}: an element leaves the -16..32 model bounds: {el['from']} .. {el['to']}")
        files[f"assets/{NS}/models/block/{key}.json"] = model
        plain = {"type": "minecraft:model", "model": f"{NS}:block/{key}"}
        if os.path.isdir(os.path.join(gdir, key + "_inventory")):
            # the placed skin (an item display, context "none") and the inventory show different models: e.g. the
            # Guardian Eye's column alone (its eye is a separate, turning display) vs the column with its eye
            plain = {"type": "minecraft:select", "property": "minecraft:display_context",
                     "cases": [{"when": "none", "model": plain}],
                     "fallback": {"type": "minecraft:model", "model": f"{NS}:block/{key}_inventory"}}
        if os.path.exists(os.path.join(gdir, key, "tint.txt")):
            # tinted by the item's dyed colour (the floor warnings take each attack's colour, Session O4)
            plain = dict(plain, tints=[{"type": "minecraft:dye", "default": -1}])
        files[f"assets/{NS}/items/{key}.json"] = {"model": plain}
        for tex_ref in set(model["textures"].values()):
            name = tex_ref.split("/")[-1][len(key) + 1:]
            single = os.path.join(gdir, key, f"{name}.png")
            frames = []
            while os.path.exists(os.path.join(gdir, key, f"{name}_{len(frames)}.png")):
                frames.append(os.path.join(gdir, key, f"{name}_{len(frames)}.png"))
            target = f"assets/{NS}/textures/block/{key}_{name}.png"
            if os.path.exists(single):
                files[target] = png_bytes(Image.open(single).convert("RGBA"))
            elif frames:
                fw, fh = Image.open(frames[0]).size   # 16x16, or 64x64 for the shield
                strip = Image.new("RGBA", (fw, fh * len(frames)))
                for i, p in enumerate(frames):
                    strip.paste(Image.open(p).convert("RGBA"), (0, fh * i))
                files[target] = png_bytes(strip)
                custom = os.path.join(gdir, key, f"{name}.mcmeta.json")
                files[target + ".mcmeta"] = (json.load(open(custom, encoding="utf-8")) if os.path.exists(custom)
                                             else {"animation": {"frametime": FRAMETIME}})
            else:
                raise SystemExit(f"{key}: texture {name} has no image")
        if os.path.exists(os.path.join(gdir, key, "part.txt")):
            continue   # a part the plugin shows itself (the Guardian Eye's eye, coloured fire), not a block skin
        base = key.split("_v")[0] if "_v" in key and key.rsplit("_v", 1)[1].isdigit() else key
        skins[base] = skins.get(base, 0) + 1
        if base == key and key.upper() in items and key.upper() not in with_models:
            with_models.append(key.upper())
            without[:] = [w for w in without if f" {key.upper()} " not in w]

    # frame-stepped sprites (Session O5 hit bursts): part folders <name>_f0, _f1, ... become one item <name> whose
    # definition picks the frame by the item's custom-model-data number (the plugin steps it), so a burst always plays
    # from its first frame (an animated texture would start wherever the game's global clock was)
    frame_sets = {}
    for key in sorted(os.listdir(gdir)) if os.path.isdir(gdir) else []:
        if "_f" in key and key.rsplit("_f", 1)[1].isdigit() and os.path.exists(os.path.join(gdir, key, "model.json")):
            base, n = key.rsplit("_f", 1)
            frame_sets.setdefault(base, []).append(int(n))
    for base, frames in frame_sets.items():
        def leaf(n):
            leaf_model = {"type": "minecraft:model", "model": f"{NS}:block/{base}_f{n}"}
            if os.path.exists(os.path.join(gdir, f"{base}_f{n}", "tint.txt")):
                leaf_model["tints"] = [{"type": "minecraft:dye", "default": -1}]
            return leaf_model
        frames.sort()
        files[f"assets/{NS}/items/{base}.json"] = {"model": {
            "type": "minecraft:range_dispatch", "property": "minecraft:custom_model_data", "index": 0,
            "entries": [{"threshold": float(n), "model": leaf(n)} for n in frames], "fallback": leaf(frames[0])}}

    # in-hand sprites (a spear drawn like vanilla's): <slug>_in_hand_N.png in the item's art session, shown in the hand
    # with vanilla's own spear_in_hand model; the inventory keeps the icon
    for item_id, item in items.items():
        key = item_id.lower()
        for session in SESSIONS:
            d = os.path.join(ART, session)
            frames = []
            while os.path.exists(os.path.join(d, f"{slug(item['name'])}_in_hand_{len(frames)}.png")):
                frames.append(os.path.join(d, f"{slug(item['name'])}_in_hand_{len(frames)}.png"))
            if not frames:
                continue
            fw, fh = Image.open(frames[0]).size
            strip = Image.new("RGBA", (fw, fh * len(frames)))
            for i, fp in enumerate(frames):
                strip.paste(Image.open(fp).convert("RGBA"), (0, fh * i))
            files[f"assets/{NS}/textures/item/{key}_in_hand.png"] = png_bytes(strip)
            if len(frames) > 1:
                files[f"assets/{NS}/textures/item/{key}_in_hand.png.mcmeta"] = {"animation": {"frametime": FRAMETIME}}
            files[f"assets/{NS}/models/item/{key}_in_hand.json"] = {"parent": "minecraft:item/spear_in_hand",
                                                                    "textures": {"layer0": model_ref(key + "_in_hand")}}
            files[f"assets/{NS}/items/{key}.json"] = {"model": {
                "type": "minecraft:select", "property": "minecraft:display_context",
                "cases": [{"when": ["gui", "ground", "fixed", "on_shelf"], "model": {"type": "minecraft:model", "model": model_ref(key)}}],
                "fallback": {"type": "minecraft:model", "model": model_ref(key + "_in_hand")}}}

    # held 3D models (Session G5): <key>_held is what the hand holds; the inventory, the ground and item frames keep
    # the 2D icon - like vanilla's trident, the item definition selects on display_context
    for key in sorted(os.listdir(gdir)) if os.path.isdir(gdir) else []:
        if not key.endswith("_held") or not os.path.exists(os.path.join(gdir, key, "model.json")):
            continue
        base = key[:-len("_held")]
        if base.upper() not in items or base.upper() not in with_models:
            raise SystemExit(f"{key}: no item {base.upper()} with a 2D icon")
        held = {"type": "minecraft:model", "model": f"{NS}:block/{key}"}
        if os.path.isdir(os.path.join(gdir, key + "_using")):   # its pose while right-click is held
            held = {"type": "minecraft:condition", "property": "minecraft:using_item", "on_false": held,
                    "on_true": {"type": "minecraft:model", "model": f"{NS}:block/{key}_using"}}
        files[f"assets/{NS}/items/{base}.json"] = {"model": {
            "type": "minecraft:select", "property": "minecraft:display_context",
            "cases": [{"when": ["gui", "ground", "fixed", "on_shelf"], "model": {"type": "minecraft:model", "model": model_ref(base)}}],
            "fallback": held}}
    # worn helmets (Session G6): <key>_head is the 3D helm drawn on the wearer's head (display context "head"); the
    # inventory and everything else keep the 2D icon
    for key in sorted(os.listdir(gdir)) if os.path.isdir(gdir) else []:
        if not key.endswith("_head") or not os.path.exists(os.path.join(gdir, key, "model.json")):
            continue
        base = key[:-len("_head")]
        if base.upper() not in items or base.upper() not in with_models:
            raise SystemExit(f"{key}: no item {base.upper()} with a 2D icon")
        files[f"assets/{NS}/items/{base}.json"] = {"model": {
            "type": "minecraft:select", "property": "minecraft:display_context",
            "cases": [{"when": "head", "model": {"type": "minecraft:model", "model": f"{NS}:block/{key}"}}],
            "fallback": {"type": "minecraft:model", "model": model_ref(base)}}}
    # the Heartwood Aegis: a shield - its model while held, and its blocking model while in use (vanilla's shield)
    if os.path.isdir(os.path.join(gdir, "heartwood_aegis_shield")):
        files[f"assets/{NS}/items/heartwood_aegis.json"] = {"model": {
            "type": "minecraft:condition", "property": "minecraft:using_item",
            "on_false": {"type": "minecraft:model", "model": f"{NS}:block/heartwood_aegis_shield"},
            "on_true": {"type": "minecraft:model", "model": f"{NS}:block/heartwood_aegis_shield_blocking"}}}
        if "HEARTWOOD_AEGIS" not in with_models:
            with_models.append("HEARTWOOD_AEGIS")
            without[:] = [w for w in without if " HEARTWOOD_AEGIS " not in w]

    # worn armor (Session G6): an equipment asset per set, its humanoid and humanoid_leggings textures
    equipment = []
    edir = os.path.join(gdir, "equipment")
    for name in sorted(os.listdir(edir)) if os.path.isdir(edir) else []:
        layers = ["humanoid", "humanoid_leggings"]
        if os.path.exists(os.path.join(edir, name, "wings.png")):
            layers.append("wings")   # the chestplate's 3D back pieces, drawn on the elytra's wings
        files[f"assets/{NS}/equipment/{name}.json"] = {"layers": {
            layer: [{"texture": f"{NS}:{name}"}] for layer in layers}}
        for layer in layers:
            img = Image.open(os.path.join(edir, name, f"{layer}.png")).convert("RGBA")
            assert img.size == (64, 32), (name, layer, img.size)
            files[f"assets/{NS}/textures/entity/equipment/{layer}/{name}.png"] = png_bytes(img)
        equipment.append(name)

    # custom blocks (Session N): every skinned block look gets its block state and the blockstate files
    blocks, retired = custom_blocks(skins, gdir)
    files.update(blockstate_files(blocks, retired))

    files["pack.mcmeta"] = {"pack": {
        "description": "Occultech - occult rituals, bosses and relics",
        "min_format": PACK_FORMAT, "max_format": PACK_FORMAT, "pack_format": PACK_FORMAT}}
    icon = Image.open(os.path.join(ART, "session-a", "hollow_sigil.png")).convert("RGBA").resize((64, 64), Image.NEAREST)
    files["pack.png"] = png_bytes(icon)

    os.makedirs(OUT, exist_ok=True)
    zip_path = os.path.join(OUT, "occultech-pack.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(files):
            data = files[name]
            if not isinstance(data, bytes):
                data = (json.dumps(data, indent=2) + "\n").encode("utf-8")
            info = zipfile.ZipInfo(name, FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    with open(os.path.join(OUT, "occultech-pack-items.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# item ids with a model in occultech-pack.zip (generated by tools/art/build_pack.py)\n")
        f.write("\n".join(with_models) + "\n")

    with open(os.path.join(OUT, "occultech-pack-equipment.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# worn armor sets: equipment assets occultech:<set> (generated by tools/art/build_pack.py)\n")
        f.write("".join(name + "\n" for name in equipment))

    with open(os.path.join(OUT, "occultech-pack-skins.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# block skins: <ITEM_ID> <variants> (generated by tools/art/build_pack.py)\n")
        f.write("".join(f"{k.upper()} {n}\n" for k, n in sorted(skins.items())))

    with open(os.path.join(OUT, "occultech-pack-blocks.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# custom blocks: <ITEM_ID> <look> <facing or -> <block state> (generated by tools/art/build_pack.py from\n"
                "# tools/art/block_states.json - a state never changes once given out)\n")
        f.write("".join(f"{b[0]} {b[1]} {b[2]} {b[3]}\n" for b in blocks))
        f.write("".join(f"{r[0]} ~ - {r[1]}\n" for r in retired))   # retired: placed blocks are converted
    os.makedirs(os.path.join(ROOT, "docs", "nexo"), exist_ok=True)
    with open(os.path.join(ROOT, "docs", "nexo", "occultech-blocks.yml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(nexo_config(blocks, items))

    print(f"{zip_path}: {len(with_models)} items with models ({len(skins)} blocks skinned, {len(blocks)} custom block states), "
          f"{os.path.getsize(zip_path)} bytes")
    print(f"{len(without)} items without art yet (blocks and held models are Session G):")
    for line in without:
        print("  " + line)


if __name__ == "__main__":
    sys.exit(main())
