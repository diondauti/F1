"""Charts from the cleaned + joined data (Person 4 deliverable).

Reads data/clean_results.csv, data/grid_stats.csv and
data/circuits_joined.csv, and saves three PNGs into plots/:

1. grid_value.png      - win % and podium % per starting slot (grid 1-10)
2. pole_conversion.png - share of races won from pole, per decade
3. circuit_map.png     - every F1 circuit ever used, on a world map
                         (plain lat/long scatter), colored by status

Run the earlier pipeline steps first:
    python clean_data.py && python join_circuits.py && python analyze.py
"""

import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt

PLOTS = "plots"
os.makedirs(PLOTS, exist_ok=True)


def save(fig, name):
    path = os.path.join(PLOTS, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {path}")


# ---- 1. value of the starting slot -----------------------------------------
with open("data/grid_stats.csv", newline="") as f:
    grid_stats = [r for r in csv.DictReader(f) if int(r["grid"]) <= 10]

grids = [int(r["grid"]) for r in grid_stats]
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar([g - 0.2 for g in grids], [float(r["win_pct"]) for r in grid_stats],
       width=0.4, label="win %", color="#e10600")
ax.bar([g + 0.2 for g in grids], [float(r["podium_pct"]) for r in grid_stats],
       width=0.4, label="podium %", color="#444444")
ax.set_xticks(grids)
ax.set_xlabel("starting grid slot")
ax.set_ylabel("% of starts")
ax.set_title("What a grid slot is worth (all F1 races 1950-2025)")
ax.legend()
save(fig, "grid_value.png")

# ---- 2. pole-to-win conversion by decade ------------------------------------
with open("data/clean_results.csv", newline="") as f:
    rows = list(csv.DictReader(f))

by_decade = defaultdict(lambda: [0, 0])  # decade -> [poles, wins from pole]
for r in rows:
    if r["grid"] == "1":
        d = int(r["season"]) // 10 * 10
        by_decade[d][0] += 1
        by_decade[d][1] += int(r["win"])

decades = sorted(by_decade)
pct = [100 * by_decade[d][1] / by_decade[d][0] for d in decades]
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(decades, pct, marker="o", color="#e10600")
ax.set_xticks(decades)
ax.set_xticklabels([f"{d}s" for d in decades])
ax.set_ylabel("% of poles converted to wins")
ax.set_ylim(0, 100)
ax.set_title("Pole position keeps getting more decisive")
ax.grid(axis="y", alpha=0.3)
save(fig, "pole_conversion.png")

# ---- 3. world map of circuits ------------------------------------------------
with open("data/circuits_joined.csv", newline="") as f:
    circuits = list(csv.DictReader(f))

colors = {"Current": "#e10600", "Former": "#999999", "Future/Returning": "#1e6fd9"}
fig, ax = plt.subplots(figsize=(11, 6))
for status, color in colors.items():
    pts = [c for c in circuits if c["status"] == status]
    if not pts:
        continue
    ax.scatter([float(c["long"]) for c in pts],
               [float(c["lat"]) for c in pts],
               s=28, color=color, label=f"{status} ({len(pts)})", alpha=0.85)
ax.set_xlabel("longitude")
ax.set_ylabel("latitude")
ax.set_xlim(-180, 180)
ax.set_ylim(-60, 75)
ax.set_title(f"Every F1 circuit, 1950-2025 ({len(circuits)} total)")
ax.legend(loc="lower left")
ax.grid(alpha=0.3)
save(fig, "circuit_map.png")
