# Summarizes a Slimefun guide export (CSV) per addon: item count, crafting steps, raw material cost.
# Usage: python tools/analyze_guide.py [guide.csv] [items.json]
import csv, re, json, sys, statistics
from collections import defaultdict, Counter

PATH = sys.argv[1] if len(sys.argv) > 1 else "docs/Public Slimefun Guide - Sheet1.csv"

items = []
cur = None
header_re = re.compile(r"^#(\d+)\s+(.*)$")

with open(PATH, encoding="utf-8", newline="") as f:
    for row in csv.reader(f):
        row += [""] * (5 - len(row))
        m = header_re.match(row[0])
        if m and "|" in row[2]:
            addon, _, iid = row[2].partition("|")
            cur = {
                "n": int(m.group(1)), "name": m.group(2).strip(),
                "addon": addon.strip(), "id": iid.strip(),
                "machines": [x.strip() for x in row[4].split(",") if x.strip()],
                "raw": [], "steps": [],
            }
            items.append(cur)
            continue
        if cur is None or row[0] == "ITEMS":
            continue
        if row[0]:
            try:
                amt = float(row[1])
            except ValueError:
                amt = 0
            cur["raw"].append((row[0], amt, row[2]))
        if row[3] and row[4]:
            cur["steps"].append(row[4])

if len(sys.argv) > 2:
    json.dump(items, open(sys.argv[2], "w"), indent=0)
print("items", len(items))
by = defaultdict(list)
for it in items:
    by[it["addon"]].append(it)

print(f"{'addon':32} {'items':>6} {'stepsMed':>8} {'stepsP90':>8} {'stepsMax':>8} {'rawMed':>9} {'rawP90':>10} {'rawMax':>12} {'machines':>8}")
rows = []
for a, its in by.items():
    steps = sorted(len(i["steps"]) for i in its)
    raw = sorted(sum(r[1] for r in i["raw"]) for i in its)
    mach = set(m for i in its for m in i["machines"])
    p90 = lambda xs: xs[int(len(xs) * 0.9) - 1] if len(xs) > 1 else xs[0]
    rows.append((a, len(its), statistics.median(steps), p90(steps), steps[-1], statistics.median(raw), p90(raw), raw[-1], len(mach)))
for r in sorted(rows, key=lambda r: -r[1]):
    print(f"{r[0][:32]:32} {r[1]:6} {r[2]:8.0f} {r[3]:8} {r[4]:8} {r[5]:9.0f} {r[6]:10.0f} {r[7]:12.0f} {r[8]:8}")
