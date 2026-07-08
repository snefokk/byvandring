#!/usr/bin/env python3
"""Geokoding for kulturløyper — slå opp koordinater fra Wikipedia + Nominatim.

Brukseksempel:
    python3 geocode.py --kommune Vadsø --punkter arbeid/punkter-utkast.json

Strategi for hvert punkt:
1. Søk i Wikipedia "Liste over kulturminner i [kommune]" — best for kulturminner
2. Fall tilbake til Nominatim med fritekstsøk
3. Marker som usikker hvis ingen treff

Output: oppdatert punkter-JSON med 'coords' fylt inn der mulig + en flagged-liste.
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from _wikicoords import extract_kulturminner


USER_AGENT = "Kulturloype-skill/1.0 (https://github.com/snefokk/kulturloype)"


def fetch(url: str, timeout: int = 10) -> str:
    """HTTP GET med User-Agent."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def fetch_wikipedia_kulturminner(kommune: str) -> dict:
    """Hent navn → (lat, lon) fra Wikipedias 'Liste over kulturminner i X'."""
    title = f"Liste over kulturminner i {kommune}"
    url = f"https://no.wikipedia.org/wiki/{urllib.parse.quote(title)}"
    try:
        html = fetch(url)
    except Exception as e:
        print(f"  ⚠️  Wikipedia-feil for {kommune}: {e}", file=sys.stderr)
        return {}

    # Bygg navn → (lat, lon)-indeks fra kulturminnetabellen.
    result = {}
    for km in extract_kulturminner(html):
        name = km["name"].strip()
        coords = (km["lat"], km["lon"])
        result[name.lower()] = coords
        # Indekser også første ord (mange kulturminner refereres med kortnavn).
        first_word = name.split()[0].lower() if name.split() else ""
        if first_word and first_word not in result:
            result[first_word] = coords

    return result


def search_nominatim(query: str, kommune: str = None) -> tuple:
    """Søk i Nominatim. Returnerer (lat, lon) eller None."""
    q = f"{query}, {kommune}, Norway" if kommune else f"{query}, Norway"
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(q)}&format=json&limit=1"
    try:
        data = json.loads(fetch(url))
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"  ⚠️  Nominatim-feil for '{query}': {e}", file=sys.stderr)
    return None


def lookup_coords(name: str, kommune: str, wiki_index: dict) -> tuple:
    """Slå opp koordinater for et navn. Returnerer ((lat,lon), kilde) eller (None, None)."""
    name_lower = name.lower()

    # 1. Eksakt match i Wikipedia kulturminneliste
    if name_lower in wiki_index:
        return wiki_index[name_lower], "wikipedia-kulturminner"

    # 2. Delvis match i Wikipedia
    for key, coords in wiki_index.items():
        if name_lower in key or key in name_lower:
            return coords, "wikipedia-fuzzy"

    # 3. Nominatim
    coords = search_nominatim(name, kommune)
    if coords:
        return coords, "nominatim"

    return None, None


def main():
    p = argparse.ArgumentParser(description="Geokoding for kulturløyper")
    p.add_argument("--kommune", required=True, help="Kommunenavn (f.eks. Vadsø)")
    p.add_argument("--punkter", required=True, help="JSON med punkter")
    p.add_argument("--output", help="Output JSON (default: overskrive input)")
    args = p.parse_args()

    pts_path = Path(args.punkter)
    out_path = Path(args.output) if args.output else pts_path

    points = json.loads(pts_path.read_text(encoding="utf-8"))

    # Støtter både {id: {...}} og [{...}] strukturer
    if isinstance(points, list):
        items = [(str(i + 1), p) for i, p in enumerate(points)]
    else:
        items = list(points.items())

    print(f"Henter Wikipedia kulturminneliste for {args.kommune}...")
    wiki = fetch_wikipedia_kulturminner(args.kommune)
    print(f"   Fant {len(wiki)} kulturminner i registeret\n")

    flagged = []
    for pid, pt in items:
        if pt.get("coords"):
            continue  # allerede koordinatfestet

        name = pt.get("title") or pt.get("name") or ""
        if not name:
            continue

        coords, source = lookup_coords(name, args.kommune, wiki)
        if coords:
            pt["coords"] = [round(coords[0], 7), round(coords[1], 7)]
            pt["coord_source"] = source
            print(f"  ✅ {name}: {coords} ({source})")
        else:
            flagged.append({"id": pid, "name": name})
            print(f"  ❌ {name}: ingen koordinater funnet")
        time.sleep(0.5)

    # Skriv tilbake
    if isinstance(points, list):
        out = [pt for pid, pt in items]
    else:
        out = {pid: pt for pid, pt in items}

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Skrev {out_path}")

    if flagged:
        print(f"\n⚠️  {len(flagged)} punkter mangler koordinater:")
        for f in flagged:
            print(f"   - {f['name']}")
        print("\nBe brukeren om Google Maps-lenker for disse, og fyll inn manuelt.")


if __name__ == "__main__":
    main()
