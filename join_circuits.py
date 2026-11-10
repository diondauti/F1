"""Join the two circuit tables (Person 2 deliverable).

Merges data/circuits_api.csv (Jolpica API) with f1_circuits.csv (Wikipedia
scrape) into data/circuits_joined.csv: one row per circuit with the API id
and coordinates plus the Wikipedia-only details (type, direction, length,
turns, GPs held, status).

Matching strategy
-----------------
1. Normalize both names: lowercase, drop filler words like "circuit",
   "international", "street", then compare.
2. 17 circuits are named too differently for that to work (e.g. the API
   calls Imola "Autodromo Enzo e Dino Ferrari", Wikipedia "Autodromo
   Internazionale Enzo e Dino Ferrari"). Those are mapped by hand in
   MANUAL_MATCHES, keyed by the API circuit_id.

Every circuit must match exactly one Wikipedia row or the script fails
loudly - with 78 rows on each side we want a perfect 1:1 join, not a
silent partial one.
"""

import csv
import re
import sys

API = "data/circuits_api.csv"
WIKI = "f1_circuits.csv"
OUT = "data/circuits_joined.csv"

# API circuit_id -> exact Wikipedia "Circuit" name, for the pairs that
# normalization cannot bridge.
MANUAL_MATCHES = {
    "aintree": "Aintree Motor Racing Circuit",
    "dallas": "Dallas Fair Park",
    "galvez": "Autódromo Oscar y Juan Gálvez",
    "imola": "Autodromo Internazionale Enzo e Dino Ferrari",
    "interlagos": "Autodromo José Carlos Pace",
    "jarama": "Circuito Permanente del Jarama",
    "jerez": "Circuito Permanente de Jerez",
    "las_vegas": "Caesars Palace Grand Prix Circuit",  # 1981-82 Caesars Palace GP
    "lemans": "Bugatti Circuit",  # F1 used the short Bugatti layout in 1967
    "monsanto": "Circuito de Monsanto",
    "mosport": "Mosport Park",
    "okayama": "TI Circuit Aida",
    "portimao": "Algarve International Circuit",
    "suzuka": "Suzuka International Racing Course",
    "yeongam": "Korea International Circuit",
    "zandvoort": "Circuit Zandvoort",
    "zeltweg": "Zeltweg Airfield",
}

FILLER = re.compile(
    r"\b(circuit|circuito|international|street|raceway|racecourse"
    r"|grand prix|park|of|the|de|do|del|della)\b"
)


def norm(name):
    name = FILLER.sub(" ", name.lower())
    return re.sub(r"[^a-z0-9]+", " ", name).strip()


with open(API, newline="") as f:
    api_rows = list(csv.DictReader(f))
with open(WIKI, newline="") as f:
    wiki_rows = list(csv.DictReader(f))

by_exact = {w["Circuit"]: w for w in wiki_rows}
by_norm = {}
for w in wiki_rows:
    by_norm.setdefault(norm(w["Circuit"]), []).append(w)

joined, used_wiki = [], set()
for a in api_rows:
    cid = a["circuit_id"]
    if cid in MANUAL_MATCHES:
        w = by_exact.get(MANUAL_MATCHES[cid])
        if w is None:
            sys.exit(f"manual match for {cid!r} not found in {WIKI}")
    else:
        candidates = by_norm.get(norm(a["circuit_name"]), [])
        if len(candidates) != 1:
            sys.exit(f"{cid!r}: expected 1 match, got {len(candidates)}")
        w = candidates[0]
    used_wiki.add(w["Circuit"])
    joined.append({
        "circuit_id": cid,
        "circuit_name": a["circuit_name"],
        "wiki_name": w["Circuit"],
        "locality": a["locality"],
        "country": a["country"],
        "lat": a["lat"],
        "long": a["long"],
        "type": w["Type"],
        "direction": w["Direction"],
        "length_km": w["Length (km)"],
        "turns": w["Turns"],
        "grands_prix": w["Grands Prix"],
        "seasons": w["Season(s)"],
        "gps_held": w["Grands Prix held"],
        "status": w["Status"],
    })

leftover = [w["Circuit"] for w in wiki_rows if w["Circuit"] not in used_wiki]
if leftover:
    sys.exit(f"wiki rows never matched: {leftover}")

with open(OUT, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(joined[0].keys()))
    writer.writeheader()
    writer.writerows(joined)

print(f"joined {len(joined)} circuits ({len(MANUAL_MATCHES)} matched by hand)")
print(f"written to: {OUT}")
