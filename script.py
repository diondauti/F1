import requests, time, json, pathlib

BASE = "https://api.jolpi.ca/ergast/f1"
HEADERS = {"User-Agent": "F1-data-project/1.0 (Dion Dauti; ddauti97@gmail.com)"}
CACHE = pathlib.Path("raw/api")
CACHE.mkdir(parents=True, exist_ok=True)


def fetch(endpoint, offset=0, limit=100):
    """Fetch one page of an endpoint. Reads from disk if already cached."""
    cache_file = CACHE / f"{endpoint.replace('/', '_')}_{offset:06d}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    url = f"{BASE}/{endpoint}.json"
    r = requests.get(url, params={"limit": limit, "offset": offset}, headers=HEADERS, timeout=30)
    r.raise_for_status()                # throws on 403/429/500 so you see it
    cache_file.write_text(r.text, encoding="utf-8")
    time.sleep(1.0)                     # be polite: ~1 request per second
    return r.json()


# --- one request: the Monday access check ---
data = fetch("circuits")
md = data["MRData"]
print("total circuits:", md["total"])
print("first one:", md["CircuitTable"]["Circuits"][0])