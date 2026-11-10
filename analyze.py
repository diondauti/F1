"""Analysis of the cleaned results (Person 3 deliverable).

Reads data/clean_results.csv and answers the project question: does
Saturday (the starting slot) decide Sunday (the race result)?

Sections
--------
1. Grid -> finish: average finishing position, win % and podium % per slot.
2. Pole-to-win conversion by decade: has starting first become more or
   less decisive over time?
3. Pole-to-win conversion by driver (min. 10 poles): who turned pole
   into victory most often?
4. All-time top drivers and constructors by wins.

Note on `position`: the API gives every starter a classified position,
including cars that retired (they are ranked at the back by laps
completed). So `position` is always a number, and for retired cars it means
"order of classification", not "crossed the line in that place".

Results are printed and the per-grid-slot table is also written to
data/grid_stats.csv for the plotting step.
"""

import csv
from collections import defaultdict

CLEAN = "data/clean_results.csv"
GRID_OUT = "data/grid_stats.csv"
MIN_POLES = 10

with open(CLEAN, newline="") as f:
    rows = list(csv.DictReader(f))

races = {(r["season"], r["round"]) for r in rows}
print(f"Loaded {len(rows)} starts from {len(races)} races\n")

# ---- 1. value of each grid slot -------------------------------------------
per_grid = defaultdict(lambda: {"starts": 0, "wins": 0, "podiums": 0, "pos_sum": 0})
for r in rows:
    g = int(r["grid"])
    s = per_grid[g]
    s["starts"] += 1
    s["wins"] += int(r["win"])
    s["podiums"] += int(r["podium"])
    s["pos_sum"] += int(r["position"])

print("=== 1. Value of the starting slot (grid 1-10) ===")
print(f"{'grid':>4} {'starts':>7} {'avg finish':>11} {'win %':>7} {'podium %':>9}")
grid_stats = []
for g in sorted(per_grid):
    s = per_grid[g]
    stat = {
        "grid": g,
        "starts": s["starts"],
        "avg_finish": round(s["pos_sum"] / s["starts"], 2),
        "win_pct": round(100 * s["wins"] / s["starts"], 1),
        "podium_pct": round(100 * s["podiums"] / s["starts"], 1),
    }
    grid_stats.append(stat)
    if g <= 10:
        print(f"{g:>4} {stat['starts']:>7} {stat['avg_finish']:>11} "
              f"{stat['win_pct']:>7} {stat['podium_pct']:>9}")

with open(GRID_OUT, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(grid_stats[0].keys()))
    writer.writeheader()
    writer.writerows(grid_stats)
print(f"(full table for every grid slot written to {GRID_OUT})")

# ---- 2. pole-to-win conversion by decade ----------------------------------
by_decade = defaultdict(lambda: {"poles": 0, "wins_from_pole": 0})
for r in rows:
    if r["grid"] == "1":
        d = int(r["season"]) // 10 * 10
        by_decade[d]["poles"] += 1
        by_decade[d]["wins_from_pole"] += int(r["win"])

print("\n=== 2. Pole-to-win conversion by decade ===")
for d in sorted(by_decade):
    s = by_decade[d]
    pct = 100 * s["wins_from_pole"] / s["poles"]
    print(f"{d}s: {s['wins_from_pole']:>3}/{s['poles']:>3} poles converted "
          f"({pct:.0f}%)  {'#' * round(pct / 2)}")

# ---- 3. pole-to-win conversion by driver ----------------------------------
by_driver = defaultdict(lambda: {"poles": 0, "wins_from_pole": 0})
for r in rows:
    if r["grid"] == "1":
        by_driver[r["driver_name"]]["poles"] += 1
        by_driver[r["driver_name"]]["wins_from_pole"] += int(r["win"])

conv = []
for name, s in by_driver.items():
    if s["poles"] >= MIN_POLES:
        conv.append((name, s["wins_from_pole"], s["poles"],
                     100 * s["wins_from_pole"] / s["poles"]))
conv.sort(key=lambda t: -t[3])

print(f"\n=== 3. Pole-to-win conversion by driver (min. {MIN_POLES} poles) ===")
for i, (name, w, p, pct) in enumerate(conv, 1):
    print(f"{i:>2}. {name:<25} {w:>3}/{p:<3} ({pct:.0f}%)")

# ---- 4. all-time winners ---------------------------------------------------
def top_wins(key, label, n=10):
    wins = defaultdict(int)
    for r in rows:
        if r["win"] == "1":
            wins[r[key]] += 1
    print(f"\n=== 4. Top {n} {label} by wins ===")
    ranked = sorted(wins.items(), key=lambda kv: -kv[1])[:n]
    for i, (name, w) in enumerate(ranked, 1):
        print(f"{i:>2}. {name:<30} {w}")


top_wins("driver_name", "drivers")
top_wins("constructor_name", "constructors")
