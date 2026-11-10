"""Group B — data cleaning (Person 1 deliverable).

Reads the raw API output (data/results.csv) and writes the one dataset the
whole team analyzes (data/clean_results.csv).

Cleaning decisions
------------------
1. Indianapolis 500 removed (race_name == "Indianapolis 500").
   Counted toward the championship 1950-60, but F1 drivers didn't race it.
   Filtered by race name, not circuit: the 2000-2007 United States GP ran
   at the same circuit_id ("indianapolis") and those are real F1 races.
2. Season 2026 removed: races that haven't happened yet.
3. Pit-lane / unknown starts removed (grid == 0): no grid slot to analyze.
4. `grid` is kept as recorded: where the car ACTUALLY started, so grid
   penalties are included by design. We measure the value of the starting
   slot, not of the qualifying lap.

Known quirk, kept on purpose: the 1951 French GP, 1956 Argentine GP and
1957 British GP list two winners each - shared drives, legal in the 1950s.
Both drivers are credited; each start still counts once per grid slot.

Added columns: field_size (starters in that race), win, podium.
"""

import csv

RAW = "data/results.csv"
OUT = "data/clean_results.csv"

with open(RAW, newline="") as f:
    rows = list(csv.DictReader(f))
n_raw = len(rows)

rows = [r for r in rows if r["race_name"] != "Indianapolis 500"]
n_indy = n_raw - len(rows)

rows = [r for r in rows if int(r["season"]) <= 2025]
n_future = n_raw - n_indy - len(rows)

rows = [r for r in rows if r["grid"] not in ("", "0")]
n_pitlane = n_raw - n_indy - n_future - len(rows)

field_size = {}
for r in rows:
    key = (r["season"], r["round"])
    field_size[key] = field_size.get(key, 0) + 1

for r in rows:
    r["field_size"] = field_size[(r["season"], r["round"])]
    pos = int(r["position"])
    r["win"] = int(pos == 1)
    r["podium"] = int(pos <= 3)

with open(OUT, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

races = len(field_size)
print(f"raw rows:            {n_raw}")
print(f"- Indy 500:          {n_indy}")
print(f"- season 2026:       {n_future}")
print(f"- pit-lane (grid=0): {n_pitlane}")
print(f"kept rows:           {len(rows)}  ({races} races, seasons 1950-2025)")
print(f"written to:          {OUT}")
