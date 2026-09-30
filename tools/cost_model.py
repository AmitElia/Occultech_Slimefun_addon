# Cost model for docs/recipes.yml.
# Expands every Occultech recipe down to raw materials using base-Slimefun costs from the
# server guide export, and writes docs/items.md with per-tier tables and checks.
#
# Usage: python tools/cost_model.py [recipes.yml] [guide.csv] [out.md]
import csv
import math
import re
import sys
from collections import Counter, defaultdict
from functools import lru_cache

import yaml

RECIPES = sys.argv[1] if len(sys.argv) > 1 else "docs/recipes.yml"
GUIDE = sys.argv[2] if len(sys.argv) > 2 else "docs/Public Slimefun Guide - Sheet1.csv"
OUT = sys.argv[3] if len(sys.argv) > 3 else "docs/items.md"

# Vanilla items that are themselves crafted, as rough raw-item counts. Everything else counts as 1.
VANILLA_RAW = {
    "NETHERITE_INGOT": 8, "NETHERITE_HELMET": 13, "NETHERITE_CHESTPLATE": 16, "NETHERITE_LEGGINGS": 15,
    "NETHERITE_BOOTS": 12, "DIAMOND_AXE": 5, "BOW": 6, "SHIELD": 7, "SLIME_BLOCK": 9, "BONE_BLOCK": 9,
    "EMERALD_BLOCK": 9, "IRON_BLOCK": 9, "HAY_BLOCK": 9, "BEACON": 9, "LODESTONE": 17, "SOUL_LANTERN": 10,
    "HOPPER": 6, "GOLDEN_HOE": 3, "BOOK": 4, "CANDLE": 2, "ENDER_EYE": 2, "FERMENTED_SPIDER_EYE": 3,
    "IRON_AXE": 5, "MAGMA_CREAM": 2, "GLOW_INK_SAC": 1, "POLISHED_BLACKSTONE_SLAB": 1, "GLASS_PANE": 1,
}
SLOT_LIMITS = {"ENHANCED_CRAFTING_TABLE": 9, "MAGIC_WORKBENCH": 9, "ARMOR_FORGE": 9, "ANCIENT_ALTAR": 9,
               "SMELTERY": 9, "HOLLOW_ASSEMBLER": 36}
BOWLS = {0: 4, 1: 8, 2: 8, 3: 12}
MACHINE_TIER = {"OCCULT_FORGE": 2, "SOUL_CONDENSER": 2, "HOLLOW_ASSEMBLER": 3}


def load_guide(path):
    """Returns {slimefun_id: (raw_cost, set_of_step_strings, name)} for base Slimefun items."""
    out, cur = {}, None
    header = re.compile(r"^#(\d+)\s+(.*)$")
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.reader(f):
            row += [""] * (5 - len(row))
            m = header.match(row[0])
            if m and "|" in row[2]:
                addon, _, iid = row[2].partition("|")
                cur = None
                if addon.strip() == "Slimefun":
                    cur = out[iid.strip()] = [0.0, set(), m.group(2).strip()]
                continue
            if cur is None or row[0] == "ITEMS":
                continue
            if row[0]:
                try:
                    cur[0] += float(row[1])
                except ValueError:
                    pass
            if row[3] and row[4]:
                cur[1].add(row[4])
    return out


data = yaml.safe_load(open(RECIPES, encoding="utf-8"))
items, bosses, tiers, circles = data["items"], data["bosses"], data["tiers"], data["circles"]
sf = load_guide(GUIDE)
problems = []


def ref(key):
    if key.startswith("mc:"):
        return ("mc", key[3:])
    if key.startswith("sf:"):
        return ("sf", key[3:])
    return ("oc", key)


def inputs_of(recipe):
    ins = dict(recipe.get("in", {}))
    if "center" in recipe:
        ins[recipe["center"]] = ins.get(recipe["center"], 0) + 1
    return ins


class Cost:
    """raw: raw items, drops: boss drops needed, steps: distinct crafting operations, depth: longest chain."""
    def __init__(self, raw=0.0, drops=None, steps=None, depth=0):
        self.raw, self.drops, self.steps, self.depth = raw, Counter(drops or {}), set(steps or ()), depth


@lru_cache(maxsize=None)
def cost(key):
    kind, iid = ref(key)
    if kind == "mc":
        return Cost(VANILLA_RAW.get(iid, 1))
    if kind == "sf":
        if iid not in sf:
            problems.append(f"Unknown Slimefun item sf:{iid}")
            return Cost(1)
        raw, steps, _ = sf[iid]
        return Cost(max(raw, 1), steps=steps, depth=1 if steps else 0)
    item = items.get(iid)
    if item is None:
        problems.append(f"Unknown Occultech item {iid}")
        return Cost(1)
    recipe = item["recipe"]
    if recipe["type"] == "BOSS_DROP":
        return Cost(0, drops={iid: 1})
    out = recipe.get("out", 1)
    total = Cost(steps={f"OC:{iid}"})
    for k, q in inputs_of(recipe).items():
        c = cost(k)
        total.raw += c.raw * q / out
        for d, n in c.drops.items():
            total.drops[d] += n * q / out
        total.steps |= c.steps
        total.depth = max(total.depth, c.depth)
    total.depth += 1
    return total


@lru_cache(maxsize=None)
def drop_value(drop_id):
    """Effective raw cost of one boss drop = summon cost / guaranteed drops per win."""
    recipe = items[drop_id]["recipe"]
    boss = recipe["boss"]
    if "chance" in recipe:
        return summon_cost(boss) / recipe["chance"]
    return summon_cost(boss) / bosses[boss]["drops"]


@lru_cache(maxsize=None)
def summon_cost(boss_id):
    b = bosses[boss_id]
    keys = dict(b["offerings"])
    if b.get("catalyst"):
        keys[b["catalyst"]] = 1
    return sum(effective(k) * q for k, q in keys.items())


def effective(key):
    c = cost(key)
    return c.raw + sum(n * drop_value(d) for d, n in c.drops.items())


def wins_needed(c):
    """Boss drops needed -> number of wins per boss."""
    out = {}
    for d, n in c.drops.items():
        boss = items[d]["recipe"]["boss"]
        out[boss] = math.ceil(n / bosses[boss]["drops"] - 1e-9)
    return out


def circle_cost(tier):
    return sum(effective(k) * q for k, q in circles[tier].items())


# ---- structural checks
for iid, item in items.items():
    r = item["recipe"]
    t = r["type"]
    if t == "BOSS_DROP":
        if r["boss"] not in bosses:
            problems.append(f"{iid}: unknown boss {r['boss']}")
        continue
    ins = inputs_of(r)
    for k in ins:
        kind, ref_id = ref(k)
        if kind == "oc" and ref_id in items and items[ref_id]["tier"] > item["tier"]:
            problems.append(f"{iid} (tier {item['tier']}) uses higher-tier item {ref_id}")
    if t in SLOT_LIMITS and sum(ins.values()) > SLOT_LIMITS[t]:
        problems.append(f"{iid}: {sum(ins.values())} items > {SLOT_LIMITS[t]} slots for {t}")
    if t == "RITUAL":
        bowls = len(r.get("in", {}))
        if bowls > BOWLS[r["circle"]]:
            problems.append(f"{iid}: {bowls} bowls > {BOWLS[r['circle']]} for circle {r['circle']}")
        if r["circle"] > item["tier"]:
            problems.append(f"{iid}: needs circle {r['circle']} above its tier {item['tier']}")
    if t in MACHINE_TIER and MACHINE_TIER[t] > item["tier"]:
        problems.append(f"{iid}: uses {t} (tier {MACHINE_TIER[t]}) above its tier")
    if t in ("OCCULT_FORGE", "SOUL_CONDENSER") and len(ins) > 4:
        problems.append(f"{iid}: {len(ins)} different inputs > 4 for {t}")
used = Counter()
for item in items.values():
    for k in inputs_of(item["recipe"]):
        used[ref(k)[1]] += 1
for b in bosses.values():
    for k in list(b["offerings"]) + ([b["catalyst"]] if b.get("catalyst") else []):
        used[ref(k)[1]] += 1
for iid, item in items.items():
    if item["cat"] not in ("weapon", "armor", "charm", "utility", "labor", "machine") and used[iid] == 0 \
            and item["cat"] != "infrastructure":
        problems.append(f"{iid}: material is never used")


def fmt(n):
    return f"{n/1e6:.2f}M" if n >= 1e6 else f"{n/1e3:.1f}k" if n >= 1e4 else f"{n:,.0f}"


# ---- report
lines = ["# Occultech - items and recipe costs (generated)", "",
         "Generated by `tools/cost_model.py` from `docs/recipes.yml` and the server guide export. Do not edit by hand.", "",
         "- **Raw:** raw items per 1 output, not counting boss drops.",
         "- **Drops:** boss drops needed. **Effective:** raw cost plus drops valued at summon cost ÷ drops per win.",
         "- **Steps:** distinct crafting operations in the full tree, the same metric as `server-analysis.md`.",
         "- **Wins:** boss wins needed for one of this item (from each boss's guaranteed drops).", ""]

lines += ["## Summary per tier", "",
          "| Tier | Gear benchmark | Items | Raw target | Most expensive (effective) | Median steps | Circle cost |",
          "|---|---|---:|---|---|---:|---:|"]
by_tier = defaultdict(list)
for iid, item in items.items():
    by_tier[item["tier"]].append(iid)
for t in sorted(by_tier):
    ids = [i for i in by_tier[t] if items[i]["recipe"]["type"] != "BOSS_DROP"]
    eff = sorted(ids, key=effective)
    steps = sorted(len(cost(i).steps) for i in ids)
    top = eff[-1]
    lo, hi = tiers[t]["raw_target"]
    lines.append(f"| {t} · {tiers[t]['name']} | {tiers[t]['gear']} | {len(by_tier[t])} | {fmt(lo)}-{fmt(hi)} | "
                 f"{items[top]['name']} ({fmt(effective(top))}) | {steps[len(steps)//2]} | {fmt(circle_cost(t))} |")
lines.append(f"\n**Total items: {len(items)}**\n")

lines += ["## Summons", "",
          "Rule: a lesser summon should cost about 1-5% of that tier's circle; a major summon about 3-5× a lesser one.", "",
          "| Boss | Tier | Kind | Base mob | Drop (per win) | Summon cost (effective) | % of circle | Check |",
          "|---|---:|---|---|---|---:|---:|---|"]
for bid, b in bosses.items():
    sc = summon_cost(bid)
    pct = 100 * sc / circle_cost(b["tier"])
    lesser = [summon_cost(x) for x, y in bosses.items() if y["tier"] == b["tier"] and y["kind"] == "lesser"]
    avg_lesser = sum(lesser) / len(lesser)
    if b["kind"] == "lesser":
        ok = "ok" if 0.5 <= pct <= 5 else ("very cheap" if pct < 0.5 else "EXPENSIVE")
    else:
        ratio = sc / avg_lesser
        ok = f"{ratio:.1f}× lesser" + ("" if 2 <= ratio <= 6 else " (check)")
    extra = f" ({b['condition']})" if b.get("condition") else ""
    extra += f" [MC {b['min_mc']}+]" if b.get("min_mc") else ""
    lines.append(f"| {bid.replace('_', ' ').title()}{extra} | {b['tier']} | {b['kind']} | {b['base']} | "
                 f"{items[b['drop']]['name']} ({b['drops']}) | {fmt(sc)} | {pct:.1f}% | {ok} |")

for t in sorted(by_tier):
    lines += ["", f"## Tier {t} · {tiers[t]['name']} (gear: {tiers[t]['gear']})", "",
              "| Item | Type | Recipe | Raw | Drops | Effective | Wins | Steps | Purpose |",
              "|---|---|---|---:|---|---:|---|---:|---|"]
    for iid in by_tier[t]:
        item = items[iid]
        r = item["recipe"]
        if r["type"] == "BOSS_DROP":
            recipe = f"drop: {r['boss'].replace('_', ' ').title()}"
            lines.append(f"| **{item['name']}** | {item['cat']} | {recipe} | - | - | {fmt(drop_value(iid))} | - | - | {item['purpose']} |")
            continue
        parts = []
        if "center" in r:
            parts.append(f"center {r['center']}")
        parts += [f"{q}× {k}" for k, q in r.get("in", {}).items()]
        where = r["type"].replace("_", " ").title() + (f" (circle {r['circle']})" if "circle" in r else "")
        recipe = f"{where}: " + ", ".join(parts) + (f" → {r['out']}" if r.get("out", 1) > 1 else "")
        c = cost(iid)
        drops = ", ".join(f"{n:g} {items[d]['name']}" for d, n in sorted(c.drops.items())) or "-"
        wins = ", ".join(f"{w} {b.replace('_', ' ').title()}" for b, w in wins_needed(c).items()) or "-"
        lines.append(f"| **{item['name']}** | {item['cat']} | {recipe} | {fmt(c.raw)} | {drops} | "
                     f"{fmt(effective(iid))} | {wins} | {len(c.steps)} | {item['purpose']} |")

lines += ["", "## Checks", ""]
lines += [f"- ⚠ {p}" for p in sorted(set(problems))] or ["- All structural checks passed."]
open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(f"{len(items)} items, {len(bosses)} bosses -> {OUT}")
for p in sorted(set(problems)):
    print("WARN", p)
