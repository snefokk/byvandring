#!/usr/bin/env python3
"""Bygg en kulturløype-HTML fra config + template.

Brukseksempel:
    python3 build_html.py \\
        --config arbeid/config.json \\
        --template templates/kulturloype-template.html \\
        --output outputs/kulturloype-vadso.html

Config-struktur (config.json):
{
  "title": "Kulturløypa i Vadsø",
  "subtitle": "5 mindre løyper du kan gå på 1–2 timer hver",
  "footer_source": "Kildetekster fra Vadsø museum – Ruija kvenmuseum.",
  "colors": ["#c0392b", "#2980b9", "#27ae60", "#d4a017", "#8e44ad", "#16a085"],
  "extra_css": "",
  "cover": {
    "title": "Kulturløypa i Vadsø",
    "lead": "5 mindre løyper ...",
    "legend": "<strong>Slik leser du arket:</strong> ...",
    "sourceCredit": "© Vadsø museum (kildetekster)",
    "colophon": "<strong>Kilder og lisenser</strong><br>Kartdata © OpenStreetMap ...",   // valgfri: vises nederst på forsiden
    "extraCard": null
  },
  "points": {
    // 'source' (grå kildelinje under teksten) og 'photo_credit' (vises i bildevisningen) er valgfrie.
    "1": { "title": "Prestelva", "address": null, "coords": [70.077, 29.726], "text": "...", "image": null,
           "source": "Bearbeidet fra Wikipedia (CC BY-SA 4.0)", "photo_credit": "Foto: NN / Vadsø museum" },
    ...
  },
  "routes": [
    {
      "id": 1,
      "name": "Indrebyen",
      "meta": "10 punkter · ca. 3 km · 1–1,5 time<br>Start: ... Slutt: ...",
      "intro": "Vest i Vadsø ligger ...",
      "coverDescription": "Start ved ...",
      "coverStats": "10 punkter · ca. 3 km · 1–1,5 time",
      "order": [3, 9, 2, 1, 6, 4, 5, 7, 8, 10],
      "notes": { "9": "Fra Ackermann ..." },
      "center": null, "zoom": null, "bounds": null
    },
    ...
  ],
  "walkRoutes": {
    "1": [[[70.077, 29.722], ...]],
    ...
  }
}
"""

import argparse
import json
import sys
from pathlib import Path


DEFAULT_COLORS = ["#c0392b", "#2980b9", "#27ae60", "#d4a017", "#8e44ad", "#16a085"]


def render_template(template: str, config: dict) -> str:
    """Erstatt {{PLACEHOLDERS}} i template med verdier fra config."""
    colors = (config.get("colors") or DEFAULT_COLORS)
    # Pad til minst 6 farger
    while len(colors) < 6:
        colors.append(DEFAULT_COLORS[len(colors) % len(DEFAULT_COLORS)])

    # Strip ut "id" fra route-objektene (det settes fra rekkefølgen)
    routes = []
    for i, r in enumerate(config["routes"], start=1):
        rcopy = dict(r)
        rcopy["id"] = i
        # Sett colorVar/colorClass for konsistent CSS
        rcopy["colorVar"] = f"--r{i}"
        rcopy["colorClass"] = f"r{i}"
        routes.append(rcopy)

    cover = config.get("cover", {})
    if "title" not in cover:
        cover["title"] = config.get("title", "Kulturløype")
    if "lead" not in cover:
        cover["lead"] = config.get("subtitle", "")

    replacements = {
        "{{TITLE}}": config.get("title", "Kulturløype"),
        "{{SUBTITLE}}": config.get("subtitle", ""),
        "{{FOOTER_SOURCE}}": config.get("footer_source", ""),
        "{{COLOR_1}}": colors[0],
        "{{COLOR_2}}": colors[1],
        "{{COLOR_3}}": colors[2],
        "{{COLOR_4}}": colors[3],
        "{{COLOR_5}}": colors[4],
        "{{COLOR_6}}": colors[5],
        "{{EXTRA_CSS}}": config.get("extra_css", ""),
        "{{POINTS_JSON}}": json.dumps(config.get("points", {}), ensure_ascii=False),
        "{{ROUTES_JSON}}": json.dumps(routes, ensure_ascii=False),
        "{{WALK_ROUTES_JSON}}": json.dumps(config.get("walkRoutes", {}), ensure_ascii=False, separators=(',', ':')),
        "{{COVER_DATA}}": json.dumps(cover, ensure_ascii=False),
    }
    out = template
    for k, v in replacements.items():
        out = out.replace(k, str(v))
    return out


def main():
    p = argparse.ArgumentParser(description="Bygg kulturløype-HTML fra config + template")
    p.add_argument("--config", required=True, help="Path til config.json")
    p.add_argument("--template", required=True, help="Path til kulturloype-template.html")
    p.add_argument("--output", required=True, help="Path til output HTML")
    args = p.parse_args()

    config_path = Path(args.config)
    template_path = Path(args.template)
    output_path = Path(args.output)

    config = json.loads(config_path.read_text(encoding="utf-8"))
    template = template_path.read_text(encoding="utf-8")

    # Validering
    if "points" not in config or not config["points"]:
        sys.exit("Feil: config må ha 'points'")
    if "routes" not in config or not config["routes"]:
        sys.exit("Feil: config må ha 'routes'")
    if len(config["routes"]) > 6:
        print(f"⚠️  Advarsel: {len(config['routes'])} løyper — template støtter maks 6 farger.")

    # Sjekk at alle punkter referert i routes faktisk eksisterer
    pts = config["points"]
    for ridx, r in enumerate(config["routes"], 1):
        for pid in r["order"]:
            if str(pid) not in pts and pid not in pts:
                sys.exit(f"Feil: Løype {ridx} refererer til punkt {pid} som ikke finnes")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_template(template, config), encoding="utf-8")

    n_pts = len(config["points"])
    n_routes = len(config["routes"])
    n_walk = sum(len(segs) for segs in config.get("walkRoutes", {}).values())
    print(f"✅ Bygget {output_path}")
    print(f"   {n_pts} punkter, {n_routes} løyper, {n_walk} gå-rute-segmenter")


if __name__ == "__main__":
    main()
