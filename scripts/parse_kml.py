#!/usr/bin/env python3
"""Parse en Google My Maps KML-fil og hent ut markører + ruter.

Brukseksempel:
    python3 parse_kml.py "Vadsø by Kulturløype 2.kml" --output arbeid/loype2.json

Utskrift (JSON):
{
  "name": "Vadsø by Kulturløype 2",
  "points": [
    { "name": "Hermetikkfabrikken", "lat": 70.0734, "lon": 29.7473 },
    ...
  ],
  "lines": [
    { "name": "Directions from ...", "coords": [[lat,lon], [lat,lon], ...] }
  ]
}

Bruksområder:
- Importer en bruker-justert My Maps-rute tilbake til konfigen
- Trekk ut koordinater fra bruker-plasserte markører
- Splitt en sammenhengende rute i segmenter (mellom hver markør på linja)
"""

import argparse
import json
import sys
import math
from pathlib import Path
from xml.etree import ElementTree as ET


KML_NS = "{http://www.opengis.net/kml/2.2}"


def parse_kml(path: Path) -> dict:
    tree = ET.parse(str(path))
    root = tree.getroot()

    doc_name_el = root.find(f"{KML_NS}Document/{KML_NS}name")
    doc_name = doc_name_el.text if doc_name_el is not None else path.stem

    points = []
    lines = []
    seen_point_names = set()

    for pm in root.iter(f"{KML_NS}Placemark"):
        name_el = pm.find(f"{KML_NS}name")
        name = name_el.text.strip() if name_el is not None and name_el.text else "(uten navn)"

        ls = pm.find(f".//{KML_NS}LineString")
        pt = pm.find(f".//{KML_NS}Point")

        if ls is not None:
            coords_el = ls.find(f"{KML_NS}coordinates")
            if coords_el is not None and coords_el.text:
                coords = []
                for c in coords_el.text.strip().split():
                    parts = c.split(",")
                    if len(parts) >= 2:
                        lon, lat = float(parts[0]), float(parts[1])
                        coords.append([round(lat, 6), round(lon, 6)])
                lines.append({"name": name, "coords": coords})

        elif pt is not None:
            coords_el = pt.find(f"{KML_NS}coordinates")
            if coords_el is not None and coords_el.text:
                parts = coords_el.text.strip().split(",")
                if len(parts) >= 2:
                    lon, lat = float(parts[0]), float(parts[1])
                    # Skip duplikater (KML har ofte to sett: original + på-linja)
                    key = (name, round(lat, 5), round(lon, 5))
                    if key not in seen_point_names:
                        seen_point_names.add(key)
                        points.append({
                            "name": name,
                            "lat": round(lat, 6),
                            "lon": round(lon, 6)
                        })

    return {"name": doc_name, "points": points, "lines": lines}


def haversine_m(p1: tuple, p2: tuple) -> float:
    """Avstand i meter mellom to (lat, lon)-punkter."""
    R = 6371000
    lat1, lon1 = p1
    lat2, lon2 = p2
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def split_line_by_markers(line_coords: list, markers: list) -> list:
    """Splitt en linje (liste av [lat, lon]) i segmenter mellom hvert markør.

    Args:
        line_coords: liste av [lat, lon]-punkter som utgjør hele ruten
        markers: liste av {"name", "lat", "lon"} i ruterekkefølge

    Returns:
        Liste av segmenter, der hvert segment er en liste av [lat, lon]-punkter
    """
    if len(markers) < 2 or not line_coords:
        return [line_coords] if line_coords else []

    # For hver marker, finn nærmeste indeks i linjen
    marker_indices = []
    for m in markers:
        mp = (m["lat"], m["lon"])
        best_idx, best_d = 0, float("inf")
        for i, lp in enumerate(line_coords):
            d = haversine_m(mp, tuple(lp))
            if d < best_d:
                best_idx, best_d = i, d
        marker_indices.append(best_idx)

    # Sorter i tilfelle markeres er ute av rekkefølge i linjen
    # (vanligvis er de i rekkefølge, men i edge-cases kan de være ute)
    # For å beholde bruker-rekkefølgen, splitt mellom konsekutive markør-indekser
    segments = []
    for i in range(len(marker_indices) - 1):
        a, b = marker_indices[i], marker_indices[i + 1]
        if b > a:
            seg = line_coords[a:b + 1]
        elif b < a:
            # Linja går "baklengs" mellom markørene — kan skje i loops
            seg = line_coords[b:a + 1][::-1]
        else:
            seg = [line_coords[a], line_coords[a]]
        segments.append(seg)

    return segments


def main():
    p = argparse.ArgumentParser(description="Parse Google My Maps KML")
    p.add_argument("kml", help="Path til KML-fil")
    p.add_argument("--output", help="Skriv parset JSON til denne fila (ellers stdout)")
    p.add_argument("--split-segments", action="store_true",
                   help="Hvis det er én lang LineString og N markører, splitt i N-1 segmenter")
    args = p.parse_args()

    kml_path = Path(args.kml)
    if not kml_path.exists():
        sys.exit(f"Finner ikke KML: {kml_path}")

    result = parse_kml(kml_path)

    if args.split_segments and len(result["lines"]) == 1 and len(result["points"]) >= 2:
        big_line = result["lines"][0]["coords"]
        markers = result["points"]
        segments = split_line_by_markers(big_line, markers)
        result["segments"] = segments
        result["segment_count"] = len(segments)

    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(out, encoding="utf-8")
        print(f"✅ Skrev {args.output}")
        print(f"   Navn: {result['name']}")
        print(f"   Punkter: {len(result['points'])}")
        print(f"   Linjer: {len(result['lines'])}")
        if "segments" in result:
            print(f"   Segmenter: {result['segment_count']}")
    else:
        print(out)


if __name__ == "__main__":
    main()
