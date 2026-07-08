#!/usr/bin/env python3
"""Generer en start-KML for Google My Maps.

Brukseksempel:
    python3 generate_kml.py --route 3 --config arbeid/loyper.json --output outputs/Vadso\\ Kulturloype\\ 3.kml

Lager en KML-fil med:
- Markører for hvert punkt i løypa (i rekkefølge)
- En auto-generert LineString-rute (fra walkRoutes hvis tilgjengelig, ellers OSRM)

Brukeren kan importere denne i mymaps.google.com, justere ruten, og eksportere tilbake.
"""

import argparse
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape


KML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{name}</name>
    <description>{description}</description>
    <Style id="marker">
      <IconStyle>
        <color>ff0066cc</color>
        <Icon><href>https://www.gstatic.com/mapspro/images/stock/503-wht-blank_maps.png</href></Icon>
      </IconStyle>
    </Style>
    <Style id="line">
      <LineStyle><color>ffcc6600</color><width>5</width></LineStyle>
    </Style>
{placemarks}
  </Document>
</kml>
"""

POINT_TEMPLATE = """    <Placemark>
      <name>{n}. {name}</name>
      <styleUrl>#marker</styleUrl>
      <Point><coordinates>{lon},{lat},0</coordinates></Point>
    </Placemark>
"""

LINE_TEMPLATE = """    <Placemark>
      <name>{name}</name>
      <styleUrl>#line</styleUrl>
      <LineString><coordinates>
{coords}
      </coordinates></LineString>
    </Placemark>
"""


def generate_kml(route: dict, points: dict, walk_segments: list = None,
                 map_name: str = None) -> str:
    """Bygg KML-streng."""
    map_name = map_name or f"Kulturløype {route['id']} – {route.get('name', '')}"

    placemarks = []
    for i, pid in enumerate(route["order"], start=1):
        p = points.get(str(pid)) or points.get(pid)
        if not p:
            continue
        lat, lon = p["coords"]
        name = escape(p.get("title") or p.get("name") or f"Punkt {i}")
        placemarks.append(POINT_TEMPLATE.format(n=i, name=name, lat=lat, lon=lon))

    if walk_segments:
        # Slå sammen alle segmenter til én lang linje
        all_coords = []
        for seg in walk_segments:
            for c in seg:
                all_coords.append(f"{c[1]},{c[0]},0")
        coords_str = "\n        ".join(all_coords)
        placemarks.append(LINE_TEMPLATE.format(
            name=f"Auto-rute (juster om nødvendig)",
            coords=coords_str
        ))

    return KML_TEMPLATE.format(
        name=escape(map_name),
        description=escape(f"Auto-generert utgangspunkt — juster ruten i Google My Maps og eksporter tilbake."),
        placemarks="".join(placemarks)
    )


def main():
    p = argparse.ArgumentParser(description="Generer KML for Google My Maps")
    p.add_argument("--route", type=int, required=True, help="Løype-ID (1, 2, 3, ...)")
    p.add_argument("--config", required=True, help="loyper.json med points + routes")
    p.add_argument("--walk-routes", help="walk_routes.json med rute-geometri (valgfri)")
    p.add_argument("--output", required=True, help="Output KML-fil")
    p.add_argument("--name", help="Tittel på kartet (default: 'Kulturløype N – Navn')")
    args = p.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    points = config["points"]
    routes = config["routes"]

    route = next((r for r in routes if r["id"] == args.route), None)
    if not route:
        sys.exit(f"Fant ikke løype {args.route} i config")

    walk_segments = None
    if args.walk_routes:
        walk_data = json.loads(Path(args.walk_routes).read_text(encoding="utf-8"))
        walk_segments = walk_data.get(str(args.route))

    kml = generate_kml(route, points, walk_segments, args.name)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(kml, encoding="utf-8")
    print(f"✅ Skrev {args.output}")
    print(f"   {len(route['order'])} markører + {'rute' if walk_segments else 'ingen rute'}")
    print(f"\nNeste steg for brukeren:")
    print(f"  1. Åpne mymaps.google.com")
    print(f"  2. Opprett nytt kart → Importer → last opp denne KML-en")
    print(f"  3. Juster ruten ved å dra punktene")
    print(f"  4. Last ned KML, lever tilbake — så kjører vi parse_kml.py")


if __name__ == "__main__":
    main()
