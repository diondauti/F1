"""
Scrape the "List of Formula One circuits" table from Wikipedia into a CSV.

Usage:
    pip install requests beautifulsoup4
    python scrape_f1_circuits.py            # writes f1_circuits.csv
"""

import csv
import re

import requests
from bs4 import BeautifulSoup

URL = "https://en.wikipedia.org/wiki/List_of_Formula_One_circuits"
OUT = "f1_circuits.csv"

# Wikipedia asks bots to identify themselves; a plain descriptive UA is enough.
HEADERS = {"User-Agent": "f1-circuits-scraper/1.0 (personal project)"}


def clean(text: str) -> str:
    """Collapse whitespace and strip footnote markers like [a] or [12]."""
    text = re.sub(r"\[[^\]]*\]", "", text)
    return " ".join(text.split())


def main() -> None:
    html = requests.get(URL, headers=HEADERS, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")

    # The circuits table is the big sortable wikitable. There may be smaller
    # wikitables on the page (e.g. the key), so pick the one whose header
    # contains "Circuit" and "Grands Prix held".
    table = None
    for t in soup.select("table.wikitable"):
        header_text = clean(t.find("tr").get_text(" "))
        if "Circuit" in header_text and "Grands Prix held" in header_text:
            table = t
            break
    if table is None:
        raise SystemExit("Could not find the circuits table - page layout changed?")

    # Header names, in order. These become CSV columns.
    headers = [clean(th.get_text(" ")) for th in table.find("tr").find_all("th")]

    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = tr.find_all(["th", "td"])   # first column is a <th> on Wikipedia
        if len(cells) != len(headers):
            continue                        # skip spacer / malformed rows

        row = {}
        for name, cell in zip(headers, cells):
            if name == "Map":
                # Just an image — keep the alt text or nothing.
                img = cell.find("img")
                row[name] = img.get("alt", "") if img else ""
            else:
                row[name] = clean(cell.get_text(" "))

        # --- Derived columns -------------------------------------------------
        circuit = row["Circuit"]
        if "*" in circuit:
            row["Status"] = "Current"
        elif "†" in circuit:
            row["Status"] = "Future/Returning"
        else:
            row["Status"] = "Former"
        row["Circuit"] = circuit.replace("*", "").replace("†", "").strip()

        # "5.793 km (3.600 mi)" -> two numeric columns
        m = re.search(r"([\d.]+)\s*km\s*\(([\d.]+)\s*mi\)", row.get("Last length used", ""))
        row["Length (km)"] = m.group(1) if m else ""
        row["Length (mi)"] = m.group(2) if m else ""

        # Country cell often starts with a flag abbreviation, e.g. "AUS Australia"
        row["Country"] = re.sub(r"^[A-Z]{3}\s+", "", row.get("Country", ""))

        rows.append(row)

    fieldnames = headers + ["Status", "Length (km)", "Length (mi)"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} circuits to {OUT}")


if __name__ == "__main__":
    main()