#!/usr/bin/env python3
"""Felles parser for Wikipedias «Liste over kulturminner i [kommune]».

Brukes av både candidate_pool.py og geocode.py så de tolker samme side likt
(tidligere hadde de hver sin skjøre regex — den ene returnerte 0 treff).

Tabellradene har form:
    <tr> <td>{askeladden-id}</td> <td>{navn}</td> ... <td>{type}</td>
         ... koordinat-lenke med ?params=LAT_N_LON_E ... </tr>

Koordinatene i geohack-lenken er som regel desimalgrader, men kan også være
grad/minutt/sekund (DMS). parse_geohack_params() håndterer begge.
"""

import re
from html import unescape


# params=70.0615_N_29.8559_E_   (desimal)
# params=70_3_41_N_29_51_21_E_  (grad/minutt/sekund)
# params=70_4_N_29_43_E_        (grad/minutt)
_PARAMS_RE = re.compile(
    r"(-?\d+(?:\.\d+)?)(?:_(\d+(?:\.\d+)?))?(?:_(\d+(?:\.\d+)?))?_([NS])_"
    r"(-?\d+(?:\.\d+)?)(?:_(\d+(?:\.\d+)?))?(?:_(\d+(?:\.\d+)?))?_([EWØ])"
)


def _dms_to_decimal(deg, minute, second, hemi):
    val = float(deg) + (float(minute or 0)) / 60 + (float(second or 0)) / 3600
    if hemi in ("S", "W"):
        val = -val
    return round(val, 7)


def parse_geohack_params(params: str):
    """Tolk en geohack 'params'-streng til (lat, lon). None hvis ikke gyldig."""
    m = _PARAMS_RE.match(params)
    if not m:
        return None
    lat = _dms_to_decimal(m.group(1), m.group(2), m.group(3), m.group(4))
    lon = _dms_to_decimal(m.group(5), m.group(6), m.group(7), m.group(8))
    # Grovt fornuftssjekk: Norge ligger omtrent her.
    if not (57 <= lat <= 72 and 4 <= lon <= 32):
        return None
    return lat, lon


def _clean_cell(cell_html: str) -> str:
    return unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", cell_html))).strip()


def extract_kulturminner(html: str) -> list:
    """Hent [{askeladden_id, name, lat, lon}, ...] fra en kulturminneliste-side.

    Hopper over rader uten gyldig koordinat eller uten navn.
    """
    out = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL):
        if "params=" not in row:
            continue
        pm = re.search(r"params=([0-9._NSEWØ-]+)", row)
        if not pm:
            continue
        coords = parse_geohack_params(pm.group(1))
        if not coords:
            continue

        cells = [_clean_cell(c) for c in
                 re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL)]
        if not cells:
            continue

        askeladden_id = cells[0] if cells[0].isdigit() else None
        # Navnet ligger i første ikke-numeriske celle etter ID-en.
        name = ""
        for c in cells[1:]:
            if c and not c.isdigit():
                name = c
                break
        if not name:
            continue

        out.append({
            "askeladden_id": askeladden_id,
            "name": name,
            "lat": coords[0],
            "lon": coords[1],
        })
    return out
