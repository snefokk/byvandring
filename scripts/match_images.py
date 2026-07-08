#!/usr/bin/env python3
"""Mapp opplastede bilder fra brukeren til riktige byvandring-punkter.

Brukeren har lastet opp en mappe med bilder. Filnavnene kan være:
- "bietilaegarden.jpg"            → matches på tittel
- "Bietilægården foto.jpeg"       → matches på tittel (case-insensitive, fjern æøå)
- "havnegata-86.jpg"              → matches på adresse
- "punkt03.png" eller "03.jpg"    → matches på punkt-ID

Skriptet:
1. Leser punktene fra config
2. For hvert opplastet bilde, prøver å matche mot et punkt
3. Kopierer bildet til outputs/bilder/{id}-{slug}.jpg
4. Oppdaterer config med image-stier

Brukseksempel:
    python3 match_images.py \\
        --config arbeid/loyper.json \\
        --input bilder-fra-bruker/ \\
        --output-dir outputs/bilder/

Eventuelle ikke-matchede bilder vises som warning — brukeren må mappe dem manuelt.
"""

import argparse
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path


def slugify(text: str) -> str:
    """Konverter 'Bietilægården' → 'bietilaegarden'."""
    text = text.lower()
    # Norske tegn
    text = text.replace("æ", "ae").replace("ø", "oe").replace("å", "aa")
    # Fjern andre diakritiske tegn
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    # Behold kun alfanumeriske og bindestrek
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def fuzzy_match_score(filename: str, point: dict) -> float:
    """Returner en score 0-1 for hvor godt filnavn matcher et punkt."""
    fn = slugify(Path(filename).stem)
    title_slug = slugify(point.get("title", ""))
    addr_slug = slugify(point.get("address", "") or "")

    score = 0.0

    # 1. Eksakt punkt-ID match (f.eks. "03" eller "punkt-03")
    pid = str(point.get("id", ""))
    if re.search(rf"\b0?{pid}\b", fn):
        score += 0.3

    # 2. Tittel-match
    if title_slug and title_slug in fn:
        score += 0.6
    elif title_slug:
        # Delvis match: alle ord i tittelen finnes i filnavnet
        title_words = title_slug.split("-")
        if all(w in fn for w in title_words if len(w) > 2):
            score += 0.4

    # 3. Adresse-match
    if addr_slug and addr_slug in fn:
        score += 0.3

    return min(score, 1.0)


def match_images(points: dict, image_paths: list) -> dict:
    """Returner mapping {image_path: point_id} basert på beste match.

    Hvert bilde mappes til ÉN punkt (best score, > 0.4 terskel).
    Et punkt kan kun ha ett bilde — hvis to bilder matcher samme punkt, bruk det med høyest score.
    """
    # Bygge liste av (point_id, point_dict)
    if isinstance(points, list):
        items = [(str(i + 1), p) for i, p in enumerate(points)]
        for pid, p in items:
            p.setdefault("id", int(pid))
    else:
        items = []
        for pid, p in points.items():
            p.setdefault("id", int(pid) if pid.isdigit() else 0)
            items.append((pid, p))

    matches = []  # liste av (score, image_path, point_id)
    for img_path in image_paths:
        for pid, point in items:
            score = fuzzy_match_score(img_path.name, point)
            if score >= 0.4:
                matches.append((score, img_path, pid))

    # Sorter etter score desc, prioriter beste match per bilde og punkt
    matches.sort(key=lambda x: -x[0])
    used_imgs = set()
    used_pts = set()
    final = {}
    for score, img, pid in matches:
        if img in used_imgs or pid in used_pts:
            continue
        final[str(img)] = pid
        used_imgs.add(img)
        used_pts.add(pid)

    return final


def copy_with_naming(image_path: Path, point_id: str, point: dict, output_dir: Path) -> Path:
    """Kopier bildet til outputs/bilder/{id}-{slug}.{ext}."""
    pid_padded = str(point_id).zfill(2)
    slug = slugify(point.get("title", "punkt"))
    ext = image_path.suffix.lower() or ".jpg"
    new_name = f"{pid_padded}-{slug}{ext}"
    new_path = output_dir / new_name
    shutil.copy2(image_path, new_path)
    return new_path


def main():
    p = argparse.ArgumentParser(description="Match opplastede bilder mot byvandring-punkter")
    p.add_argument("--config", required=True, help="loyper.json med points")
    p.add_argument("--input", required=True, help="Mappe med opplastede bilder")
    p.add_argument("--output-dir", default="outputs/bilder", help="Mappe der bildene skal lagres")
    p.add_argument("--update-config", action="store_true",
                   help="Oppdater config med image-stier (overskriver fil)")
    args = p.parse_args()

    cfg_path = Path(args.config)
    in_dir = Path(args.input)
    out_dir = Path(args.output_dir)

    if not in_dir.is_dir():
        sys.exit(f"Finner ikke input-mappe: {in_dir}")

    config = json.loads(cfg_path.read_text(encoding="utf-8"))
    points = config["points"]

    # Hent alle bildefiler
    exts = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    image_paths = sorted([f for f in in_dir.iterdir() if f.is_file() and f.suffix.lower() in exts])

    if not image_paths:
        sys.exit(f"Ingen bilder funnet i {in_dir}")

    print(f"Fant {len(image_paths)} bilder. Matcher mot {len(points)} punkter...\n")

    matches = match_images(points, image_paths)

    out_dir.mkdir(parents=True, exist_ok=True)

    matched = []
    unmatched = []

    for img_path in image_paths:
        if str(img_path) in matches:
            pid = matches[str(img_path)]
            point = points[pid] if isinstance(points, dict) else points[int(pid) - 1]
            new_path = copy_with_naming(img_path, pid, point, out_dir)
            rel_path = f"bilder/{new_path.name}"
            matched.append((img_path.name, pid, point.get("title"), rel_path))
            if args.update_config:
                point["image"] = rel_path
            print(f"  ✅ {img_path.name}  →  {rel_path}  ({point.get('title')})")
        else:
            unmatched.append(img_path.name)

    if unmatched:
        print(f"\n⚠️  {len(unmatched)} bilder ble ikke matchet automatisk:")
        for u in unmatched:
            print(f"   - {u}")
        print("\nDu kan rename dem til å inkludere punkt-tittel/adresse, eller mappe manuelt.")

    if args.update_config:
        cfg_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n📝 Oppdatert {cfg_path} med image-stier.")
    else:
        print(f"\n💡 Kjør med --update-config for å skrive image-stier til {cfg_path}.")


if __name__ == "__main__":
    main()
