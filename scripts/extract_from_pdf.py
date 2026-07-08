#!/usr/bin/env python3
"""Trekk ut strukturerte punkter fra et kulturløype-PDF-hefte.

Brukseksempel:
    python3 extract_from_pdf.py uploads/kulturloype-vadso.pdf > arbeid/punkter-utkast.json

Strategi:
1. Bruk pdftotext (fra poppler-utils) til å hente teksten med layout
2. Søk etter mønsteret "<nummer>. <tittel>" som overskrift på hvert punkt
3. Samle alle linjer fram til neste punkt-overskrift
4. Returnere som JSON-array

Krav: pdftotext må være installert (apt install poppler-utils, brew install poppler).
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def pdf_to_text(pdf_path: Path) -> str:
    """Kjør pdftotext med layout-bevaring."""
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except FileNotFoundError:
        sys.exit("pdftotext ikke installert. Installer med 'brew install poppler' eller 'apt install poppler-utils'.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"pdftotext feil: {e.stderr}")


def extract_points(text: str) -> list:
    """Søk etter punkt-overskrifter og samle tilhørende tekst."""
    # Del opp på linjeskift
    lines = text.split("\n")
    points = []
    current = None

    for line in lines:
        stripped = line.strip()
        # Sjekk om det er en ny punkt-overskrift
        m = re.match(r"^(\d+)\.\s+(.+)$", stripped)
        if m and len(m.group(1)) <= 3:
            # Lagre forrige punkt
            if current:
                current["text"] = " ".join(current["text_lines"]).strip()
                del current["text_lines"]
                points.append(current)

            num = int(m.group(1))
            rest = m.group(2)

            # Sjekk om tittelen har en adresse i seg (f.eks. "Bietilægården – Havnegata 86")
            addr_match = re.match(r"^(.+?)\s*[-–]\s*(.+)$", rest)
            if addr_match:
                title = addr_match.group(1).strip()
                address = addr_match.group(2).strip()
            else:
                title = rest.strip()
                address = None

            current = {
                "id": num,
                "title": title,
                "address": address,
                "coords": None,
                "text_lines": []
            }
        elif current and stripped:
            current["text_lines"].append(stripped)

    # Lagre siste punkt
    if current:
        current["text"] = " ".join(current["text_lines"]).strip()
        del current["text_lines"]
        points.append(current)

    return points


def main():
    p = argparse.ArgumentParser(description="Trekk ut punkter fra kulturløype-PDF")
    p.add_argument("pdf", help="Path til PDF-fila")
    p.add_argument("--output", help="Skriv til fil (ellers stdout)")
    p.add_argument("--min-text-length", type=int, default=20,
                   help="Minimum tekstlengde for å beholde et punkt (default 20 tegn)")
    args = p.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        sys.exit(f"Finner ikke {pdf_path}")

    text = pdf_to_text(pdf_path)
    points = extract_points(text)

    # Filter ut punkter med altfor lite tekst (sannsynligvis falske positives)
    points = [p for p in points if len(p.get("text", "")) >= args.min_text_length]

    out = json.dumps(points, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(out, encoding="utf-8")
        print(f"✅ Skrev {args.output}", file=sys.stderr)
        print(f"   Fant {len(points)} punkter", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
