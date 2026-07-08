#!/usr/bin/env python3
"""Visuell verifikasjon av kulturløype-HTML via screenshot.

Skillen bruker dette for å sjekke at hver løypes kart faktisk viser:
- Alle markørene innenfor viewport
- Gatenavn (zoom høy nok)
- Ruten ikke utenfor kart-kanten

Brukseksempel:
    python3 verify_screenshot.py outputs/kulturloype-vadso.html

Forutsetninger:
- Chrome MCP må være tilkoblet (Claude in Chrome)
- HTML-fila ligger i en mappe som kan serveres lokalt

Skriptet:
1. Starter en lokal Python http-server i HTML-fila sin mappe
2. Skriver instruksjoner for hvordan agenten kan fortsette via Chrome MCP
3. (Selve screenshot-taking gjøres av agenten med Chrome MCP-verktøyene)
"""

import argparse
import http.server
import os
import socketserver
import sys
import threading
from pathlib import Path


def serve(directory: Path, port: int = 8765):
    """Start lokal http-server."""
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(directory), **kw)
    httpd = socketserver.TCPServer(("", port), handler)
    print(f"🌐 Server kjører på http://localhost:{port}/")
    print(f"   Mappe: {directory}")
    print(f"   Trykk Ctrl+C for å stoppe.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopper server.")
        httpd.shutdown()


def main():
    p = argparse.ArgumentParser(description="Start lokal server for visuell verifikasjon")
    p.add_argument("html", help="Path til HTML-fila")
    p.add_argument("--port", type=int, default=8765, help="Port (default 8765)")
    p.add_argument("--no-serve", action="store_true",
                   help="Ikke start server, bare skriv ut instruksjoner")
    args = p.parse_args()

    html_path = Path(args.html).resolve()
    if not html_path.exists():
        sys.exit(f"Finner ikke {html_path}")

    directory = html_path.parent
    file_name = html_path.name

    print(f"""
══════════════════════════════════════════════════════════════
 VERIFIKASJON AV KULTURLØYPE
══════════════════════════════════════════════════════════════

HTML-fil: {html_path}

For agenten (Claude in Chrome MCP):

1. Naviger til http://localhost:{args.port}/{file_name}#rute1
2. Vent 4 sekunder for at kart laster
3. Ta screenshot
4. Verifiser:
   - Alle markører synlige (1, 2, 3, ...)?
   - Minst 3 gatenavn synlige?
   - Rute-linjen synlig?
5. Hvis problemer:
   - For lav zoom (ingen gatenavn): sett 'center: [lat,lon], zoom: 15'
   - For tett zoom (markører utenfor): sett 'bounds: [[s,w],[n,e]]'
   - For stor avstand mellom punkter: del løypen i to mindre løyper
6. Gjenta for #rute2, #rute3, ... og forsiden #cover.

══════════════════════════════════════════════════════════════
""")

    if not args.no_serve:
        serve(directory, port=args.port)


if __name__ == "__main__":
    main()
