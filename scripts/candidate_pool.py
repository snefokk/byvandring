#!/usr/bin/env python3
"""Samle kandidatpunkter for en kulturløype fra flere kilder.

For å unngå å bare bruke Riksantikvarens kulturminneregister (som ofte mangler
moderne attraksjoner som monumenter, museer, kvensk arkitektur), slår dette
scriptet sammen punkter fra:

1. Wikipedia "Liste over kulturminner i [kommune]" (Riksantikvarens register)
2. Wikipedia kommune-artikkel (sjekker "Severdigheter"/"Attraksjoner"-seksjon)
3. OpenStreetMap (tourism:museum, tourism:attraction, historic:* via Overpass)
4. Lokal museum-side (besøkssteder for kommunen, hvis kjent)

Output: en samlet kandidat-pool som brukeren kan velge fra.

Brukseksempel:
    python3 candidate_pool.py --kommune Vardø --output arbeid/kandidater.json
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from _wikicoords import extract_kulturminner


USER_AGENT = "Kulturloype-skill/1.0"

# Kjente lokale museum-sider per kommune
LOCAL_MUSEUM_LISTS = {
    "Vadsø": "https://www.varangermuseum.no/besok-oss/besokssteder/",
    "Vardø": "https://www.varangermuseum.no/besok-oss/besokssteder/",
    "Sør-Varanger": "https://www.varangermuseum.no/besok-oss/besokssteder/",
}

# Kommune bounding boxes for Overpass-spørringer (lat-lon-grov)
COMMUNE_BBOX = {
    "Vadsø":  (70.040, 29.65, 70.090, 29.83),
    "Vardø":  (70.250, 30.80, 70.400, 31.20),
}

# Tema-presets: hvilke OSM-tagger som hentes per løype-tema.
# 'use_kulturminner' slår på Wikipedia kulturminneliste + lokal museum (kun relevant for historiske tema).
# 'note' er en ærlig advarsel der OSM-dekningen er tynn og temaet i praksis må kurateres manuelt.
THEME_PRESETS = {
    "kultur": {
        "label": "Historie & kulturminner",
        "osm": [("tourism", "museum|attraction|viewpoint|artwork"),
                ("historic", "memorial|monument|castle|fort|battlefield|ruins|building")],
        "use_kulturminner": True,
    },
    "gatekunst": {
        "label": "Gatekunst & utsmykning",
        "osm": [("tourism", "artwork"), ("artwork_type", None)],
        "note": "OSM mangler ofte lokale veggmalerier (f.eks. Komafest i Vardø). "
                "Dette temaet bør som regel suppleres med en kuratert liste fra festival/kommune.",
    },
    "smaksrunde": {
        "label": "Smaksrunde (smått å smake)",
        "osm": [("shop", "bakery|pastry|confectionery|chocolate|deli|greengrocer"),
                ("amenity", "ice_cream|cafe|fast_food"),
                ("craft", "brewery")],
        "note": "Sekvensiell smaking av smått (bakeri, iskrem, gatemat, mikrobryggeri) — "
                "IKKE en middagsguide. «Hvor spiser jeg middag» er et «velg ett sted»-kart, "
                "ikke en løype (bruk kommunekart-skillen).",
    },
    "uteliv": {
        "label": "Bar & uteliv",
        "osm": [("amenity", "bar|pub|biergarten|nightclub")],
    },
    "shopping": {
        "label": "Butikker & shopping",
        "osm": [("shop", "gift|art|books|clothes|jewelry|craft|antiques|deli|bakery|interior_decoration")],
    },
    "natur": {
        "label": "Natur & utsikt",
        "osm": [("tourism", "viewpoint"), ("natural", "peak|beach"),
                ("leisure", "park|garden|nature_reserve")],
    },
    "religion": {
        "label": "Kirker & hellige steder",
        "osm": [("amenity", "place_of_worship"),
                ("historic", "church|chapel|monastery|wayside_shrine|wayside_cross")],
    },
    "maritime": {
        "label": "Kyst & sjøfart",
        "osm": [("man_made", "lighthouse|pier"), ("historic", "ship|wreck"),
                ("leisure", "marina"), ("tourism", "aquarium")],
        "note": "Dekningen i OSM varierer — suppler gjerne med lokal sjøfartshistorie "
                "(brygger, fyr, væreierhistorie) som kuratert liste.",
    },
    "arkitektur": {
        "label": "Arkitektur & severdigheter",
        "osm": [("building", "church|cathedral|chapel"), ("tourism", "attraction")],
        "use_kulturminner": True,
    },
}


def fetch(url: str, timeout: int = 10) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def candidates_from_wikipedia_list(kommune: str) -> list:
    """Hent alle kulturminner fra Wikipedia kulturminneliste."""
    candidates = []
    title = f"Liste over kulturminner i {kommune}"
    url = f"https://no.wikipedia.org/wiki/{urllib.parse.quote(title)}"
    try:
        html = fetch(url)
    except Exception as e:
        print(f"  ⚠️  Wikipedia-liste-feil: {e}", file=sys.stderr)
        return candidates

    for km in extract_kulturminner(html):
        candidates.append({
            "id": km["askeladden_id"],
            "name": km["name"],
            "lat": km["lat"],
            "lon": km["lon"],
            "source": "wikipedia-kulturminner",
            "type": "kulturminne"
        })
    return candidates


def bbox_from_nominatim(kommune: str):
    """Slå opp en grov bounding box for kommunen via Nominatim. None ved feil."""
    q = urllib.parse.quote(f"{kommune}, Norge")
    url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data and data[0].get("boundingbox"):
            s, n, w, e = [float(x) for x in data[0]["boundingbox"]]
            return (s, w, n, e)
    except Exception as ex:
        print(f"  ⚠️  Nominatim bbox-feil: {ex}", file=sys.stderr)
    return None


def _overpass_query(filters: list, bbox: tuple) -> str:
    """Bygg en Overpass-spørring fra en liste (tag-key, value-regex|None) for et tema."""
    s, w, n, e = bbox
    lines = []
    for key, val in filters:
        sel = f'["{key}"~"{val}"]' if val else f'["{key}"]'
        lines.append(f'  node{sel}({s},{w},{n},{e});')
        lines.append(f'  way{sel}({s},{w},{n},{e});')
    body = "\n".join(lines)
    return f"[out:json][timeout:25];\n(\n{body}\n);\nout center;"


def candidates_from_osm(kommune: str, osm_filters: list) -> list:
    """Hent POI-er fra OpenStreetMap via Overpass for et gitt sett tema-tagger."""
    candidates = []
    bbox = COMMUNE_BBOX.get(kommune)
    if not bbox:
        # Ikke hardkodet — utled bbox fra Nominatim så scriptet virker for alle kommuner.
        bbox = bbox_from_nominatim(kommune)
        if not bbox:
            print(f"  ⚠️  Fant ingen bbox for {kommune} — hopp over OSM (oppgi --bbox manuelt).",
                  file=sys.stderr)
            return candidates
    query = _overpass_query(osm_filters, bbox)
    try:
        url = "https://overpass-api.de/api/interpreter"
        data = urllib.parse.urlencode({"data": query}).encode()
        req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=25) as resp:
            d = json.loads(resp.read())
        for el in d.get("elements", []):
            tags = el.get("tags", {})
            name = tags.get("name") or tags.get("alt_name")
            if not name:
                continue
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            if not (lat and lon):
                continue
            poi_type = (tags.get("tourism") or tags.get("historic") or tags.get("amenity")
                        or tags.get("shop") or tags.get("artwork_type") or tags.get("natural")
                        or tags.get("leisure") or "poi")
            candidates.append({
                "name": name,
                "lat": lat,
                "lon": lon,
                "source": "osm",
                "type": poi_type,
                "osm_id": el.get("id")
            })
    except Exception as e:
        print(f"  ⚠️  OSM/Overpass-feil: {e}", file=sys.stderr)
    return candidates


def candidates_from_local_museum(kommune: str) -> list:
    """Hent besøkssteder fra lokal museum-side."""
    candidates = []
    url = LOCAL_MUSEUM_LISTS.get(kommune)
    if not url:
        return candidates
    try:
        html = fetch(url)
        # Finn lenker som matcher kommune-relaterte besøkssteder
        for m in re.finditer(r'<a[^>]+href="([^"]*besokssteder/[^"]+)"[^>]*>([^<]+)</a>', html):
            link, name = m.group(1), m.group(2).strip()
            if kommune.lower() in link.lower() or kommune.lower() in name.lower():
                candidates.append({
                    "name": name,
                    "source": "lokal-museum",
                    "type": "museum",
                    "url": link if link.startswith("http") else f"https://www.varangermuseum.no{link}"
                })
    except Exception as e:
        print(f"  ⚠️  Lokal museum-feil: {e}", file=sys.stderr)
    return candidates


def dedup(candidates: list) -> list:
    """Slå sammen duplikater (samme navn eller koord)."""
    seen_names = {}
    seen_coords = {}
    out = []
    for c in candidates:
        name_key = (c["name"] or "").lower().strip()
        coord_key = (round(c["lat"], 4), round(c["lon"], 4)) if c.get("lat") and c.get("lon") else None

        if name_key in seen_names:
            # Slå sammen kilder
            existing = seen_names[name_key]
            existing["sources"] = list(set(existing.get("sources", [existing["source"]]) + [c["source"]]))
            if not existing.get("lat") and c.get("lat"):
                existing["lat"], existing["lon"] = c["lat"], c["lon"]
        elif coord_key and coord_key in seen_coords:
            existing = seen_coords[coord_key]
            existing["sources"] = list(set(existing.get("sources", [existing["source"]]) + [c["source"]]))
        else:
            c["sources"] = [c["source"]]
            seen_names[name_key] = c
            if coord_key:
                seen_coords[coord_key] = c
            out.append(c)
    return out


def main():
    p = argparse.ArgumentParser(description="Samle kandidatpunkter for en (tema-)løype")
    p.add_argument("--kommune", help="Kommunenavn")
    p.add_argument("--output", help="Output JSON")
    p.add_argument("--tema", default="kultur",
                   help="Løype-tema (se --list-temaer). Default: kultur")
    p.add_argument("--bbox", help="Bounding box: 'sør,vest,nord,øst' for å overstyre COMMUNE_BBOX")
    p.add_argument("--list-temaer", action="store_true", help="List tilgjengelige tema og avslutt")
    args = p.parse_args()

    if args.list_temaer:
        print("Tilgjengelige tema:")
        for key, t in THEME_PRESETS.items():
            extra = "  (kulturminne-register + museum)" if t.get("use_kulturminner") else ""
            print(f"  {key:11s} {t['label']}{extra}")
            if t.get("note"):
                print(f"              ⚠️  {t['note']}")
        print("\nKuratere tema (Munch, Harry Hole, Komafest …) lages som manuell punktliste — "
              "ikke via dette scriptet.")
        return

    if not args.kommune or not args.output:
        p.error("--kommune og --output er påkrevd (eller bruk --list-temaer)")

    if args.tema not in THEME_PRESETS:
        p.error(f"Ukjent tema '{args.tema}'. Kjør --list-temaer for å se valgene.")
    preset = THEME_PRESETS[args.tema]

    if args.bbox:
        s, w, n, e = [float(x) for x in args.bbox.split(",")]
        COMMUNE_BBOX[args.kommune] = (s, w, n, e)

    print(f"Tema: {preset['label']} ({args.tema})", file=sys.stderr)
    if preset.get("note"):
        print(f"⚠️  {preset['note']}\n", file=sys.stderr)

    all_cands = []
    step = 1

    # Wikipedia kulturminneliste + lokalt museum gir bare mening for historiske tema.
    if preset.get("use_kulturminner"):
        print(f"{step}. Wikipedia kulturminneliste for {args.kommune}...", file=sys.stderr)
        wiki_cands = candidates_from_wikipedia_list(args.kommune)
        print(f"   Fant {len(wiki_cands)} fra Wikipedia\n", file=sys.stderr)
        all_cands.extend(wiki_cands)
        step += 1

    print(f"{step}. OpenStreetMap ({preset['label']})...", file=sys.stderr)
    osm_cands = candidates_from_osm(args.kommune, preset["osm"])
    print(f"   Fant {len(osm_cands)} fra OSM\n", file=sys.stderr)
    all_cands.extend(osm_cands)
    step += 1

    if preset.get("use_kulturminner"):
        print(f"{step}. Lokal museum-side...", file=sys.stderr)
        mus_cands = candidates_from_local_museum(args.kommune)
        print(f"   Fant {len(mus_cands)} fra lokal museum\n", file=sys.stderr)
        all_cands.extend(mus_cands)

    final = dedup(all_cands)

    print(f"Etter dedup: {len(final)} unike kandidater\n", file=sys.stderr)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Skrev {args.output}")

    # Vis oversikt på stderr
    by_source = {}
    for c in final:
        for s in c.get("sources", [c.get("source", "?")]):
            by_source.setdefault(s, []).append(c["name"])
    print("\nKandidater per kilde:", file=sys.stderr)
    for src, names in by_source.items():
        print(f"  {src}: {len(names)} stk", file=sys.stderr)


if __name__ == "__main__":
    main()
