"""Session B1: reads the combat logs the plugin writes (plugins/Occultech/combat-log/*.yml) and reports, per boss and
group size: fight length against the target, how much of the fight the boss was actually being hurt, the damage it did
to each player per second with every mechanic counted (after armor), deaths, and the attacks that hurt the most.

Run: python tools/balance.py [log folder]      (default: run/plugins/Occultech/combat-log)
Writes docs/balance-playtests.md as well as printing it.
"""
import glob
import os
import sys
from collections import defaultdict

import yaml

ROOT = os.path.join(os.path.dirname(__file__), "..")
FOLDER = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "run", "plugins", "Occultech", "combat-log")
OUT = os.path.join(ROOT, "docs", "balance-playtests.md")

# docs/scope.md: mini-bosses 1-3 min solo, gate bosses 4-8 min; a group of 3 about 60% of solo (the chosen curve)
GATES = {"GELATINOUS_SOVEREIGN", "ARCHEVOKER", "DROWNED_ELDER", "GALLUS"}


def target(boss, players):
    low, high = (240, 480) if boss in GATES else (60, 180)
    if players >= 3:
        low, high = low * 0.6, high * 0.6
    return low, high


def main():
    files = sorted(glob.glob(os.path.join(FOLDER, "*.yml")))
    if not files:
        print(f"No combat logs in {FOLDER} yet - fight a boss with players in the arena first.")
        return
    groups = defaultdict(list)
    for path in files:
        with open(path, encoding="utf-8") as f:
            log = yaml.safe_load(f)
        groups[(log["tier"], log["boss"], log.get("players-at-start", 1))].append(log)

    lines = ["# Boss playtests (from the combat logs)", "",
             "| Tier | Boss | Players | Fights | Won | Avg length | Target | Boss hurt | Damage to each player /s | Deaths per fight |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    worst = []
    for (tier, boss, players), logs in sorted(groups.items()):
        won = sum(1 for log in logs if log["result"] == "VICTORY")
        length = sum(log["seconds"] for log in logs) / len(logs)
        uptime = sum(log.get("uptime", 0) for log in logs) / len(logs)
        taken, deaths, fighters = 0.0, 0, 0
        by_mechanic = defaultdict(float)
        for log in logs:
            for player in (log.get("players") or {}).values():
                fighters += 1
                deaths += player.get("deaths", 0)
                for mechanic, tally in (player.get("taken") or {}).items():
                    taken += tally["after"] / max(1, log["seconds"])
                    by_mechanic[mechanic] += tally["after"]
        low, high = target(boss, players)
        flag = "" if low <= length <= high else (" (long)" if length > high else " (short)")
        lines.append(f"| {tier} | {boss} | {players} | {len(logs)} | {won} | {length:.0f}s{flag} | {low:.0f}-{high:.0f}s | "
                     f"{uptime * 100:.0f}% | {taken / max(1, fighters):.2f} | {deaths / len(logs):.1f} |")
        total = sum(by_mechanic.values()) or 1
        top = sorted(by_mechanic.items(), key=lambda kv: -kv[1])[:3]
        worst.append(f"- **{boss}** ({players}p): " + ", ".join(f"{name} {amount / total * 100:.0f}%" for name, amount in top))
    lines += ["", "## Where the damage came from (share of all damage players took)", ""] + worst
    text = "\n".join(lines) + "\n"
    print(text)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
