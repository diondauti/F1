# F1 Data Project

A small data collection project that builds a clean dataset of Formula 1 history from two independent sources: the Jolpica F1 API (an Ergast-compatible API) and Wikipedia. The goal is to have circuit information and every race result since 1950 as tidy CSV files, ready for analysis.

## Data sources

1. **Jolpica F1 API** (https://api.jolpi.ca) - circuits and full race results, 1950 to present.
2. **Wikipedia** - the ["List of Formula One circuits"](https://en.wikipedia.org/wiki/List_of_Formula_One_circuits) table, with extra details the API does not have (circuit type, direction, length, number of Grands Prix held).

The two sources can be joined: `circuits_api.csv` keeps each circuit's Wikipedia URL, and both tables share circuit names.

## Project structure

```
F1/
├── collect_api.py      # main collector: fetches circuits + all race results from the API
├── websrcaping.py      # scrapes the Wikipedia circuits table into f1_circuits.csv
├── script.py           # minimal API access check (one request, prints circuit count)
├── data/
│   ├── circuits_api.csv   # 78 circuits (id, name, Wikipedia URL, locality, country, lat/long)
│   └── results.csv        # 26,313 rows: one row per driver per race, 1950 -> now
├── raw/
│   └── api/               # every API response cached as JSON, one file per page
├── f1_circuits.csv     # scraped Wikipedia table (type, direction, length, GPs held, status)
└── circuits.json       # sample raw API response (first circuits page)
```

## The datasets

### data/results.csv

One row per driver per race. Columns include:

- **Race**: season, round, race name, date, circuit id
- **Driver**: id, code, full name, nationality, date of birth
- **Constructor**: id, name, nationality
- **Result**: grid position, finishing position, points, laps, status (Finished / Engine / Collision / ...), race time, fastest lap

### data/circuits_api.csv

One row per circuit from the API: id, name, Wikipedia URL, locality, country, latitude, longitude.

### f1_circuits.csv

One row per circuit from Wikipedia: circuit type (street/road/race), direction, location, country, lap length, turns, which Grands Prix it hosted, seasons, number of GPs held, and a derived status column (Current / Former / Future).

## How to run

```bash
pip install requests beautifulsoup4

# Fetch API data (circuits + all results)
python collect_api.py

# Scrape the Wikipedia circuits table
python websrcaping.py
```

`collect_api.py` caches every API response in `raw/api/` before parsing it. On a re-run, nothing is downloaded again - the CSVs are rebuilt from the cache in seconds. Delete `raw/api/` to force a fresh download.

Both scripts follow polite-client rules: a named User-Agent, one request per second, and every response saved to disk.

## Status

- [x] API access check (`script.py`)
- [x] Circuits from the API
- [x] All race results 1950 -> now (26,313 rows)
- [x] Wikipedia circuits table scraped
- [ ] Join the two circuit tables and analyze
