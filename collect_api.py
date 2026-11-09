"""
Collect Formula 1 data from the Jolpica-F1 API (Ergast-compatible).

  python collect_api.py            # fetches what is missing, re-reads what is cached

Produces:
  raw/api/*.json            one file per API page  (commit these)
  data/circuits_api.csv     one row per circuit
  data/results.csv          one row per driver per race, 1950 -> now

Rules followed: named User-Agent, one request per second, every response
cached to disk before parsing, nothing re-downloaded on later runs.
"""

import csv
import json
import pathlib
import time

import requests

BASE = "https://api.jolpi.ca/ergast/f1"
HEADERS = {"User-Agent": "F1-data-project/1.0 (Dion Dauti; ddauti97@gmail.com)"}
PAGE = 100                       # API maximum
SLEEP = 1.0                      # seconds between live requests

RAW = pathlib.Path("raw/api")
OUT = pathlib.Path("data")
RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(exist_ok=True)


# --------------------------------------------------------------------------- #
# Fetching with cache
# --------------------------------------------------------------------------- #
def fetch(endpoint: str, offset: int = 0) -> dict:
    """One page of one endpoint. Disk cache first, network second."""
    cache_file = RAW / f"{endpoint.replace('/', '_')}_{offset:06d}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    r = requests.get(
        f"{BASE}/{endpoint}.json",
        params={"limit": PAGE, "offset": offset},
        headers=HEADERS,
        timeout=30,
    )
    if r.status_code == 429:
        wait = int(r.headers.get("Retry-After", 60))
        print(f"  429 rate limited - waiting {wait}s. Body: {r.text[:200]}")
        time.sleep(wait)
        return fetch(endpoint, offset)
    r.raise_for_status()

    cache_file.write_text(r.text, encoding="utf-8")
    time.sleep(SLEEP)
    return r.json()


def fetch_all(endpoint: str, table_key: str, list_key: str) -> list:
    """Every page of an endpoint, concatenated."""
    rows, offset = [], 0
    while True:
        md = fetch(endpoint, offset)["MRData"]
        rows.extend(md[table_key][list_key])
        total = int(md["total"])
        offset += PAGE
        print(f"  {endpoint}: {min(offset, total)}/{total}", end="\r")
        if offset >= total:
            print()
            return rows


def write_csv(path: pathlib.Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows):,} rows -> {path}")


# --------------------------------------------------------------------------- #
# 1. Circuits  (1 request)
# --------------------------------------------------------------------------- #
def collect_circuits() -> None:
    circuits = fetch_all("circuits", "CircuitTable", "Circuits")
    rows = [
        {
            "circuit_id": c["circuitId"],
            "circuit_name": c["circuitName"],
            "wikipedia_url": c["url"],              # <- join key to the Wikipedia table
            "locality": c["Location"]["locality"],
            "country": c["Location"]["country"],
            "lat": float(c["Location"]["lat"]),
            "long": float(c["Location"]["long"]),
        }
        for c in circuits
    ]
    write_csv(OUT / "circuits_api.csv", rows)


# --------------------------------------------------------------------------- #
# 2. Race results, all seasons  (~270 requests, ~5 minutes first run)
# --------------------------------------------------------------------------- #
def collect_results() -> None:
    races = fetch_all("results", "RaceTable", "Races")

    rows = []
    for race in races:
        for res in race["Results"]:
            fastest = res.get("FastestLap", {})
            rows.append(
                {
                    # race
                    "season": int(race["season"]),
                    "round": int(race["round"]),
                    "race_name": race["raceName"],
                    "race_date": race["date"],
                    "circuit_id": race["Circuit"]["circuitId"],
                    # driver
                    "driver_id": res["Driver"]["driverId"],
                    "driver_code": res["Driver"].get("code", ""),
                    "driver_name": f'{res["Driver"]["givenName"]} {res["Driver"]["familyName"]}',
                    "driver_nationality": res["Driver"].get("nationality", ""),
                    "driver_dob": res["Driver"].get("dateOfBirth", ""),
                    # constructor
                    "constructor_id": res["Constructor"]["constructorId"],
                    "constructor_name": res["Constructor"]["name"],
                    "constructor_nationality": res["Constructor"].get("nationality", ""),
                    # result
                    "car_number": res.get("number", ""),
                    "grid": int(res["grid"]),               # 0 = started from pit lane
                    "position": res.get("position", ""),    # blank if not classified
                    "position_text": res["positionText"],   # "R" retired, "D" disqualified ...
                    "position_order": int(res["positionOrder"]) if "positionOrder" in res else "",
                    "points": float(res["points"]),
                    "laps": int(res["laps"]),
                    "status": res["status"],                # Finished, +1 Lap, Engine, Collision ...
                    "race_time_ms": res.get("Time", {}).get("millis", ""),
                    "fastest_lap_rank": fastest.get("rank", ""),
                    "fastest_lap_time": fastest.get("Time", {}).get("time", ""),
                }
            )
    write_csv(OUT / "results.csv", rows)


if __name__ == "__main__":
    collect_circuits()
    collect_results()
