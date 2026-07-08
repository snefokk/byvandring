#!/usr/bin/env python3
"""Sjekker flere kilder for tekstbeskrivelse av kulturminner.

For hvert punkt, sjekker:
1. Wikipedia REST API (sammendrag fra norsk Wikipedia)
2. Varangermuseum.no besøkssteder (hvis kommune er Vadsø, Vardø, Sør-Varanger)
3. Generelle museum-sider (utvides per kommune)

Output: tabell over tilgjengelige kilder + tekstkandidater per punkt.

Brukseksempel:
    python3 source_lookup.py --punkter arbeid/punkter.json --kommune Vardø --output arbeid/kilder.json

Output-format:
{
  "Vardøhus festning": {
    "wikipedia": "Vardøhus festning er Norges østligste...",
    "varangermuseum": "Velkommen til verdens nordligste festning...",
    "best_source": "varangermuseum",
    "best_text": "Velkommen til verdens nordligste festning..."
  },
  ...
}
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path


USER_AGENT = "Kulturloype-skill/1.0"

# Per-kommune museumsider å sjekke
LOCAL_MUSEUM_HOSTS = {
    "Vadsø": "https://www.varangermuseum.no/besok-oss/besokssteder/",
    "Vardø": "https://www.varangermuseum.no/besok-oss/besokssteder/",
    "Sør-Varanger": "https://www.varangermuseum.no/besok-oss/besokssteder/",
    "Hammerfest": "https://www.gjenreisningsmuseet.no/",
    "Tromsø": "https://uit.no/tmu/",
    # Utvid etter behov
}


def fetch(url: str, timeout: int = 8) -> str:
    """HTTP GET med User-Agent."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_wikipedia_summary(title: str) -> str:
    """Hent sammendrag fra Wikipedia REST API."""
    try:
        url = f"https://no.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
        data = json.loads(fetch(url))
        if data.get("type") == "standard":
            return data.get("extract", "")
    except Exception as e:
        if "404" not in str(e):
            print(f"  ⚠️  Wikipedia-feil for '{title}': {e}", file=sys.stderr)
    return ""


def fetch_wikipedia_full(title: str) -> str:
    """Hent full første-paragraph fra Wikipedia (mer tekst enn sammendrag)."""
    try:
        url = f"https://no.wikipedia.org/wiki/{urllib.parse.quote(title)}"
        html = fetch(url)
        # Finn første <p> i hovedinnholdet
        match = re.search(r'<div[^>]+id="mw-content-text"[^>]*>.*?<p[^>]*>(.*?)</p>',
                          html, re.DOTALL)
        if match:
            text = unescape(re.sub(r'<[^>]+>', '', match.group(1))).strip()
            text = re.sub(r'\s+', ' ', text)
            return text
    except Exception as e:
        if "404" not in str(e):
            print(f"  ⚠️  Wikipedia HTML-feil for '{title}': {e}", file=sys.stderr)
    return ""


def find_varangermuseum_page(name: str) -> str:
    """Søk etter besokssted-side på varangermuseum.no."""
    # Generer plausibel slug
    slug = name.lower().replace("ø", "oe").replace("å", "aa").replace("æ", "ae")
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")

    candidates = [
        f"https://www.varangermuseum.no/besok-oss/besokssteder/{slug}/",
        f"https://www.varangermuseum.no/{slug}/",
    ]

    for url in candidates:
        try:
            html = fetch(url)
            # Hent hovedinnhold (utenom nav/footer)
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
            for p in paragraphs:
                text = unescape(re.sub(r'<[^>]+>', '', p)).strip()
                text = re.sub(r'\s+', ' ', text)
                # Skip footer-tekst og praktisk info
                if len(text) > 80 and not any(
                    text.startswith(prefix) for prefix in
                    ("Grensen", "Postboks", "Faktura", "Tlf:", "Send", "This", "When", "Both")
                ):
                    return text[:600]
        except Exception:
            continue
    return ""


def lookup_sources(name: str, kommune: str = None) -> dict:
    """Sjekk alle kilder for ett punkt."""
    sources = {}

    # 1. Wikipedia sammendrag (rask)
    text = fetch_wikipedia_summary(name)
    if text and len(text) > 50:
        sources["wikipedia"] = text
    time.sleep(0.3)

    # 2. Wikipedia full første-paragraph (mer tekst)
    if "wikipedia" not in sources:
        text = fetch_wikipedia_full(name)
        if text and len(text) > 50:
            sources["wikipedia"] = text
        time.sleep(0.3)

    # 3. Lokal museum (kun for kjente kommuner)
    if kommune and kommune in LOCAL_MUSEUM_HOSTS:
        text = find_varangermuseum_page(name)
        if text and len(text) > 50:
            sources["varangermuseum"] = text
        time.sleep(0.3)

    return sources


def main():
    p = argparse.ArgumentParser(description="Slå opp tekstkilder for kulturminner")
    p.add_argument("--punkter", required=True, help="JSON med punkter (liste eller dict)")
    p.add_argument("--kommune", help="Kommunenavn for lokal museum-oppslag")
    p.add_argument("--output", help="Output JSON (ellers stdout)")
    args = p.parse_args()

    points = json.loads(Path(args.punkter).read_text(encoding="utf-8"))
    items = list(points.values()) if isinstance(points, dict) else points

    print(f"Sjekker kilder for {len(items)} punkter...\n", file=sys.stderr)

    results = {}
    for i, pt in enumerate(items, 1):
        name = pt.get("title") or pt.get("name") or ""
        if not name:
            continue
        print(f"[{i}/{len(items)}] {name}", file=sys.stderr)
        sources = lookup_sources(name, args.kommune)

        # Velg beste kilde — preferer lokal museum hvis tilgjengelig
        best_source = None
        best_text = ""
        for src_name in ("varangermuseum", "wikipedia"):
            if src_name in sources:
                best_source = src_name
                best_text = sources[src_name]
                break

        results[name] = {
            **sources,
            "best_source": best_source,
            "best_text": best_text,
            "available_sources": list(sources.keys())
        }
        if not sources:
            print(f"  ❌ Ingen kilder funnet", file=sys.stderr)
        else:
            print(f"  ✅ {', '.join(sources.keys())}", file=sys.stderr)

    out = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(out, encoding="utf-8")
        print(f"\n✅ Skrev {args.output}", file=sys.stderr)
        n_with = sum(1 for r in results.values() if r["available_sources"])
        print(f"   {n_with}/{len(results)} punkter har minst én kilde", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
