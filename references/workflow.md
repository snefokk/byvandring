# Detaljert workflow for kulturløype-skillen

Dette dokumentet er agentens "kjøkkenoppskrift" — gå gjennom det steg for steg første gang du bruker skillen.

## Forberedelser

```bash
# Opprett arbeidsmapper i workspace
mkdir -p arbeid outputs outputs/bilder
```

Dette er midlertidige arbeidsmapper. `arbeid/` er for utkast, `outputs/` er sluttproduktet.

---

## Steg 1: Hent inn punktene

Bruk `AskUserQuestion` for å spørre brukeren hva utgangspunktet er.

### Hvis PDF-hefte:
```bash
# Bruk pdf-skill først for å trekke ut teksten
python3 scripts/extract_from_pdf.py uploads/kulturloype-hefte.pdf > arbeid/punkter-utkast.json
```

### Hvis manuell liste:
Spør brukeren om å oppgi punktene som JSON eller en strukturert liste:

```json
[
  { "title": "Bietilægården", "address": "Havnegata 86", "text": "..." },
  { "title": "Tiberghuset", "address": "Havnegata 67", "text": "..." }
]
```

Lagre i `arbeid/punkter-utkast.json`.

---

## Steg 2: Geokoding

```bash
python3 scripts/geocode.py --kommune Vadsø --punkter arbeid/punkter-utkast.json --output arbeid/punkter.json
```

Se på output. Punkter merket `❌` mangler koordinater. Spør brukeren om Google Maps-lenker for hver:

```
Jeg fant ikke koordinater for følgende:
1. Bietilægården
2. Russebakeriet
3. ...

Kan du sende meg Google Maps-lenker? Lim inn én per linje.
```

Når du har lenkene, parse dem (de har formatet `https://www.google.com/maps/.../@LAT,LON,...` eller `!3dLAT!4dLON`):

```python
import re
def parse_gmaps(url):
    m = re.search(r'!3d([\d.]+)!4d([\d.]+)', url)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = re.search(r'@([\d.]+),([\d.]+)', url)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None
```

Oppdater `arbeid/punkter.json`.

---

## Steg 3: Foreslå oppdeling

Hvis det er mange punkter (>15), foreslå auto-clustering. Bruk DBSCAN eller en enkel grid:

```python
# Pseudokode
from sklearn.cluster import DBSCAN
import numpy as np

coords = np.array([p["coords"] for p in points])
clusters = DBSCAN(eps=0.005, min_samples=2).fit_predict(coords)
# eps 0.005 grader ≈ 500m
```

Vis brukeren et oversiktskart (kan være enkel HTML med Leaflet og fargekodede markører).

Be henne navngi hver gruppe (f.eks. "Indrebyen", "Sentrum", "Vadsøya", "Ytrebyen"). Spør om hun vil flytte noen punkter mellom grupper.

Bygg `arbeid/loyper.json`:

```json
{
  "points": { ... fra forrige steg ... },
  "routes": [
    { "id": 1, "name": "Indrebyen", "order": [3, 9, 2, 1, 6, 4, 5, 7, 8, 10] },
    { "id": 2, "name": "Sentrum", "order": [11, 13, 17, 14, 12, 16] },
    ...
  ]
}
```

---

## Steg 4: Auto-routing

```bash
python3 scripts/auto_route.py --config arbeid/loyper.json --output arbeid/walk_routes.json --report arbeid/route_flags.json
```

Skriptet flagger problematiske segmenter. Vis dem til brukeren:

```
⚠️ Følgende segmenter trenger manuell sjekk:

Løype 3 (Vadsøya):
  Pkt 5 → 6 (Luftskipsmasta → Krigsminner): OSRM fant ingen sti.

Vil du:
(a) Beholde luftlinjen for disse segmentene
(b) Tegne ruten manuelt i Google My Maps
```

Hvis (b): generer KML for løype 3 (kun de problematiske segmentene), be brukeren å redigere.

---

## Steg 5: Manuell rutejustering (valgfritt)

Hvis brukeren vil overstyre flaggede segmenter:

```bash
python3 scripts/generate_kml.py --route 3 --config arbeid/loyper.json --output outputs/Vadsø\ Kulturløype\ 3.kml
```

Send brukeren instruksjoner:

```
1. Åpne mymaps.google.com
2. Trykk "Opprett et nytt kart"
3. Trykk "Importer" og last opp Vadsø Kulturløype 3.kml
4. Klikk på rute-linjen og dra punkter for å justere
5. Tre prikker → "Last ned KML" → lagre i samme mappe
6. Si fra når du har gjort det, så importerer jeg den nye ruten.
```

Når brukeren har eksportert tilbake:

```bash
python3 scripts/parse_kml.py outputs/Vadsø\ Kulturløype\ 3.kml --output arbeid/loype3_oppdatert.json --split-segments
```

Erstatt `walkRoutes["3"]` i `arbeid/walk_routes.json` med segmentene fra `arbeid/loype3_oppdatert.json`.

---

## Steg 6: Bilder (brukeren laster opp)

Bilder håndteres manuelt — ikke automatisk. Wikimedia Commons har sjelden bilder av lokale kulturminner i mindre byer.

**Spør brukeren**:

```
Har du bilder av kulturminnene? Hvis ja:
1. Samle dem i én mappe (gi gjerne hver fil et navn som inkluderer tittelen,
   f.eks. "bietilaegarden.jpg" eller "punkt-03.jpg")
2. Last dem opp til arbeidsmappen
3. Si fra når du er ferdig, så mapper jeg dem mot punktene

Hvis ikke: vi kan bygge løypa uten bilder. Bilder er valgfritt.
```

Når brukeren har lastet opp:

```bash
python3 scripts/match_images.py \
  --config arbeid/loyper.json \
  --input bilder-fra-bruker/ \
  --output-dir outputs/bilder/ \
  --update-config
```

Skriptet:
- Matcher filnavn mot punkt-tittel, adresse, eller punkt-ID
- Kopierer matchede bilder til `outputs/bilder/{ID}-{slug}.jpg`
- Oppdaterer `image:`-feltet i config
- Lister opp ikke-matchede bilder så brukeren kan rename eller mappe manuelt

**Hvis brukeren ikke har bilder**: Hopp over dette steget. `image:`-feltet er valgfritt — HTML-en fungerer fint uten thumbnails.

---

## Steg 7: Bygg HTML

Lag en final config med alt:

```json
{
  "title": "Kulturløypa i Vadsø",
  "subtitle": "5 mindre løyper du kan gå på 1–2 timer hver",
  "footer_source": "Kildetekster fra Vadsø museum.",
  "colors": ["#c0392b", "#2980b9", "#27ae60", "#d4a017", "#8e44ad"],
  "cover": {
    "title": "Kulturløypa i Vadsø",
    "lead": "31 punkter spredt over byen, delt i 5 mindre runder.",
    "legend": "<strong>Slik leser du arket:</strong> ...",
    "sourceCredit": "© Vadsø museum"
  },
  "points": { ... },
  "routes": [ ... ],
  "walkRoutes": { ... }
}
```

```bash
python3 scripts/build_html.py \
  --config arbeid/config-final.json \
  --template templates/kulturloype-template.html \
  --output outputs/kulturloype-vadso.html
```

---

## Steg 8: Visuell verifikasjon

```bash
python3 scripts/verify_screenshot.py outputs/kulturloype-vadso.html &
```

Bruk så Chrome MCP til å:

1. Naviger til `http://localhost:8765/kulturloype-vadso.html#rute1`
2. Vent 4 sek
3. Ta screenshot
4. Verifiser:
   - Alle markører synlige?
   - Gatenavn vises?
   - Rute-linjen synlig (ikke gjemt under markører)?
5. Gjenta for hver løype.

Hvis problemer:

| Problem | Løsning |
|---------|---------|
| For lav zoom, ingen gatenavn | Sett `route.center` og `route.zoom: 15` |
| Markører utenfor kart | Sett `route.bounds: [[s,w], [n,e]]` med slack |
| Markører overlapper | Flytt en av punktene 50m bort |
| Tekst flyter til neste side | Reduser font i print-CSS, eller del løypa |

Oppdater `arbeid/config-final.json` og rebuild.

---

## Steg 9: Lever

```bash
# Kopier alt til workspace
cp -r outputs/* "/path/to/workspace/06 - Kulturløype/"
```

Gi brukeren:
- En `computer://`-lenke til `kulturloype-{kommune}.html`
- En kort guide for hvordan oppdatere senere (rediger KML i My Maps, kjør `parse_kml.py`)

---

## Sjekkliste før levering

- [ ] Alle punkter har gyldige koordinater
- [ ] Alle løyper har minst 2 punkter
- [ ] Alle routes har en `meta` og `intro`-tekst
- [ ] Alle bilder ligger i `bilder/`-mappen
- [ ] Hver løype har et bra zoom (verifisert visuelt)
- [ ] Print-test: Ctrl+P viser én A4 per løype
- [ ] Brukeren har godkjent oppdelingen
