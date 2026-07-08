#!/usr/bin/env python3
"""Automatisk fotgjenger-routing for byvandringer via FOSSGIS OSM-routing.

Brukseksempel:
    python3 auto_route.py --config arbeid/loyper.json --output arbeid/walk_routes.json

Input (loyper.json):
{
  "points": {
    "1": { "coords": [70.077, 29.726] },
    "2": { "coords": [70.077, 29.722] },
    ...
  },
  "routes": [
    { "id": 1, "order": [3, 9, 1, 2, ...] },
    ...
  ]
}

Output (walk_routes.json):
{
  "1": [[[lat, lon], ...], [[lat, lon], ...]],   # ett segment per par av punkter
  "2": [...],
  ...
}

Pluss en kvalitetsrapport (stdout) som flagger problematiske segmenter:
- < 0.5x luftlinje → OSRM fant ingen sti
- > 1.8x luftlinje → OSRM tar lang omveg
"""

import argparse
import json
import math
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


OSRM_URL = "https://routing.openstreetmap.de/routed-foot/route/v1/foot/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
USER_AGENT = "Byvandring-skill/1.0"


def _http_get(url: str, timeout: int):
    """GET som JSON. Faller tilbake til curl hvis Pythons SSL ikke klarer handshaket
    (stock macOS-python er bygd mot gammel LibreSSL som FOSSGIS-CDN-en avviser)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        # Prøv curl som reserve — det bruker systemets nyere TLS-stack.
        try:
            out = subprocess.run(
                ["curl", "-sS", "--max-time", str(timeout), "-A", USER_AGENT, url],
                capture_output=True, text=True, check=True,
            )
            return json.loads(out.stdout)
        except FileNotFoundError:
            raise e  # ingen curl tilgjengelig — la den opprinnelige feilen boble opp
        except (subprocess.CalledProcessError, json.JSONDecodeError) as ce:
            raise ce


def haversine_m(p1: tuple, p2: tuple) -> float:
    R = 6371000
    lat1, lon1 = p1
    lat2, lon2 = p2
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def fetch_route(p1: tuple, p2: tuple, timeout: int = 15):
    """Hent gå-rute fra FOSSGIS. Returnerer (coords-liste, distanse-meter) eller (None, 0)."""
    lat1, lon1 = p1
    lat2, lon2 = p2
    url = OSRM_URL.format(lon1=lon1, lat1=lat1, lon2=lon2, lat2=lat2)
    try:
        data = _http_get(url, timeout)
        if data.get("code") == "Ok":
            coords = data["routes"][0]["geometry"]["coordinates"]
            return [[round(c[1], 6), round(c[0], 6)] for c in coords], data["routes"][0]["distance"]
    except Exception as e:
        print(f"  ⚠️  Routing-feil: {e}", file=sys.stderr)
    return None, 0


def auto_route_for_loype(points: dict, order: list, route_id: int):
    """Returner liste av segmenter + rapport over flaggede segmenter."""
    segments = []
    flags = []
    total = 0

    for i in range(len(order) - 1):
        n1, n2 = order[i], order[i + 1]
        pt1 = points.get(str(n1)) or points.get(n1) or {}
        pt2 = points.get(str(n2)) or points.get(n2) or {}
        p1 = tuple(pt1["coords"])
        p2 = tuple(pt2["coords"])
        line_d = haversine_m(p1, p2)

        coords, dist = fetch_route(p1, p2)
        # Etikett med faktiske punktnavn der vi har dem (ellers stoppnummer).
        name1 = pt1.get("title") or pt1.get("name") or f"pkt {n1}"
        name2 = pt2.get("title") or pt2.get("name") or f"pkt {n2}"
        seg_label = f"{i + 1} → {i + 2} ({name1} → {name2})"

        if coords is None:
            segments.append([list(p1), list(p2)])
            total += line_d
            flags.append({
                "route_id": route_id,
                "segment": seg_label,
                "issue": "Routing-API svarte ikke. Bruker luftlinje.",
                "distance_air": round(line_d)
            })
        elif dist < 0.5 * line_d:
            segments.append([list(p1), list(p2)])
            total += line_d
            flags.append({
                "route_id": route_id,
                "segment": seg_label,
                "issue": f"OSRM fant ingen sti (returnerte {round(dist)}m, luftlinje er {round(line_d)}m). Bruker luftlinje.",
                "distance_air": round(line_d),
                "distance_route": round(dist)
            })
        elif dist > 1.8 * line_d:
            segments.append(coords)
            total += dist
            flags.append({
                "route_id": route_id,
                "segment": seg_label,
                "issue": f"OSRM tar lang omveg ({round(dist)}m vs luftlinje {round(line_d)}m). Vurder manuell justering i Google My Maps.",
                "distance_air": round(line_d),
                "distance_route": round(dist),
                "ratio": round(dist / line_d, 2)
            })
        else:
            segments.append(coords)
            total += dist

        time.sleep(0.2)  # snill mot serveren

    return segments, total, flags


def main():
    p = argparse.ArgumentParser(description="Auto-routing for byvandringer")
    p.add_argument("--config", required=True, help="JSON med points + routes")
    p.add_argument("--output", required=True, help="walk_routes.json")
    p.add_argument("--report", help="Kvalitetsrapport som JSON")
    args = p.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    points = config["points"]
    routes = config["routes"]

    walk_routes = {}
    all_flags = []

    for r in routes:
        rid = r["id"]
        order = r["order"]
        if len(order) < 2:
            walk_routes[str(rid)] = []
            continue
        print(f"\nLøype {rid} ({r.get('name', '')}):")
        segs, total, flags = auto_route_for_loype(points, order, rid)
        walk_routes[str(rid)] = segs
        all_flags.extend(flags)
        for f in flags:
            print(f"  ⚠️  Pkt {f['segment']}: {f['issue']}")
        print(f"  Total: {round(total)} m ({round(total/1000, 2)} km)")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(walk_routes, ensure_ascii=False, separators=(',', ':')),
                                  encoding="utf-8")
    print(f"\n✅ Skrev {args.output}")

    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(all_flags, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
        print(f"📋 Kvalitetsrapport: {args.report} ({len(all_flags)} flagg)")
    elif all_flags:
        print(f"\n⚠️  {len(all_flags)} segmenter trenger oppmerksomhet (se output over).")


if __name__ == "__main__":
    main()
