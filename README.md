# kulturloype

En Claude Code-skill som lager **interaktive og printbare by-løyper** (A4) for norske
byer — historiske kulturløyper *eller* tematiske runder. Den foreslår hva stedet er
kjent for, lar deg velge tema, henter punkter, beregner faktiske gå-ruter og bygger en
selvstendig HTML-fil klar til print.

> Full arbeidsflyt for agenten ligger i [`SKILL.md`](SKILL.md). Denne README-en er en
> menneske-vennlig oversikt.

## Hva den lager

- **Forside** med oversikt over alle løypene
- **Ett A4-ark per løype**: kart øverst (CARTO Voyager), infotekst i to kolonner under
- **Faktiske gå-ruter** mellom punktene (OSM/FOSSGIS foot-routing — ikke luftlinje)
- **Kildekreditering** innebygd: kolofon på forsiden + «Kilde:»-linje per punkt + fotokreditt
- **Automatisk markør-spredning** så tette punkter ikke overlapper
- Klikkbare bilder (thumbnails i web, skjult ved print)

## Tema-løyper

Én løype = ett tema. Datadrevne tema hentes fra OpenStreetMap / Riksantikvaren:

| Tema | Kilde | Egnet for |
|---|---|---|
| `kultur` | Riksantikvaren + OSM + museum | historiske byer (standard) |
| `arkitektur` | Riksantikvaren + OSM | trehusbyer, severdigheter |
| `religion` | OSM `place_of_worship` | kirker, kapell, synagoger |
| `maritime` | OSM fyr/brygge/marina | kystbyer, sjøfart |
| `uteliv` | OSM bar/pub | bar-crawl |
| `shopping` | OSM `shop` | butikkrunder |
| `natur` | OSM utsikt/park | utsiktspunkter |
| `smaksrunde` | OSM bakeri/iskrem/gatemat | smått å smake (ikke middagsguide) |
| `gatekunst` | OSM `artwork` | ofte kuratert |

**Kuraterte tema** (manuell punktliste): «Munch-løypa», «Harry Hole-løypa»,
spøkelsesvandring, festival-gatekunst, kvensk/samisk innvandringshistorie, industri.

```bash
python3 scripts/candidate_pool.py --list-temaer   # se alle tema
```

## Kom i gang

Skillen kjøres normalt av Claude Code (si f.eks. *«lag en kirkevandring i Trondheim»*),
men scriptene kan også kjøres manuelt:

```bash
# 1. Hent kandidatpunkter for et tema
python3 scripts/candidate_pool.py --kommune Trondheim --tema religion \
  --bbox "63.41,10.36,63.44,10.42" --output arbeid/kandidater.json

# 2. (Historiske tema) fyll inn koordinater / sjekk tekstkilder
python3 scripts/geocode.py --kommune Trondheim --punkter arbeid/kandidater.json
python3 scripts/source_lookup.py --punkter arbeid/kandidater.json --kommune Trondheim

# 3. Beregn gå-ruter
python3 scripts/auto_route.py --config arbeid/loyper.json --output arbeid/walk.json

# 4. Bygg HTML fra én samlet config (se templates/config-eksempel.json)
python3 scripts/build_html.py --config arbeid/config-final.json \
  --template templates/kulturloype-template.html --output outputs/kulturloype.html
```

## Byggekjede

```
config.json ──► build_html.py ──► kulturloype-template.html ──► ferdig .html
```

Se [`templates/config-eksempel.json`](templates/config-eksempel.json) for full datastruktur
(tittel, farger, cover/kolofon, points, routes, walkRoutes).

## Forutsetninger

- **Python 3** (kun standardbibliotek — ingen `pip install`)
- **curl** — brukes som TLS-fallback for gå-routing (finnes på macOS som standard)
- **pdftotext** (poppler) — *kun* hvis du importerer et eksisterende PDF-hefte
- Nettilgang — OSM/CARTO-kart, FOSSGIS-routing, Wikipedia, Nominatim/Overpass

## Mappestruktur

```
kulturloype/
├── SKILL.md                        full arbeidsflyt (agent-instruks)
├── README.md                       denne fila
├── scripts/                        Python-scripts (byggekjede + datakilder)
├── templates/                      HTML-template + eksempel-config
└── references/                     workflow, tekstkilder, koordinatkilder, KML-flyt
```

## Kildekreditering og lisens

Standard arbeidsmåte: **skriv tekstene om til egne ord (behold fakta), og oppgi alltid
kilden.** Wikipedia er CC BY-SA (ordrett gjenbruk krever ShareAlike — unngås ved
omskriving); museumstekst er som regel opphavsrettslig vernet; kartdata krever
attribusjon (OSM/CARTO) i kolofonen. Se `references/text-sources.md`.

---

Laget av **Snefokk**. Kartdata © OpenStreetMap-bidragsytere (ODbL) · karttegning © CARTO.
