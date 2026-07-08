---
name: kulturloype
description: Lag interaktive og printbare by-løyper for en norsk by — historiske kulturløyper *eller* tematiske runder (mat, uteliv/bar, shopping, natur, gatekunst, eller kuraterte tema som «Munch-løypa» og «Harry Hole-løypa»). Skillen foreslår hva stedet er kjent for, lar brukeren velge tema, henter kandidatpunkter (Riksantikvarens register for historie, OpenStreetMap for mat/uteliv/shopping/natur, eller en manuell/kuratert liste), beregner gå-ruter automatisk, og leverer en HTML-fil der hver løype printes som A4. Bruk når brukeren sier "lag kulturløype", "byvandring", "historisk vandring", "lag en POI-tur", "tema-løype", "smaksrunde", "bar-runde", "shopping-løype", "gatekunst-vandring", "kirkevandring", "spøkelsesvandring", "Munch-løype", "Harry Hole-løype", eller har et eksisterende hefte/liste de vil digitalisere.
---

# Kulturløype-skillen

Bygger interaktive og printbare by-løyper for norske byer — til fots. Løypene kan være **historiske** (kulturminner) eller **tematiske** (mat, uteliv, shopping, natur, gatekunst, eller kuraterte tema som «Munch-løypa»). Samme sted kan tilbys med flere tema. Skillen er for **bygjenger** i bymiljø — ikke fjell/natur-turer.

All kommunikasjon med brukeren skjer på **norsk**.

## Hva skillen leverer

En enkelt selvstående HTML-fil + tilhørende `bilder/` mappe som inneholder:
- En forside med oversikt over alle delturer
- Én A4-side per deltur, med kart øverst og infotekst i to kolonner under
- Klikkbare bilder som thumbnails i web (skjult ved print)
- Faktiske gå-ruter mellom punktene (ikke luftlinje)
- Notater mellom punkter for veibeskrivelse eller anbefalte avstikkere

## Når skillen passer

✅ **Bruk for**:
- Eksisterende kulturløype-hefte (PDF) som skal digitaliseres
- Kommune som vil lage en byvandring fra scratch
- Næringsforening eller turistkontor som har en liste over interessante steder
- Museer som vil lage en historisk vandring
- **Tematiske runder**: mat-/kafé-runde, bar-/uteliv-runde, shopping-løype, natur-/utsiktsrunde, gatekunst-vandring
- **Kuraterte tema** med en lokal punktliste: forfatter-/kunstnerløype («Munch», «Harry Hole»), festival-gatekunst, lokalhistorie

❌ **Ikke bruk for**:
- Fjell- eller naturløyper utenfor by (bruk ut.no eller dedikerte turapper)
- Sykkel- eller bilruter (skillen er fotgjenger-fokusert)
- Et fullt næringskart med alle kategorier samtidig (bruk `kommunekart`-skillen) — kulturløypa er én tematisk vandring av gangen

## Forutsetninger

- **Bash + Python 3** — for å kjøre scripts
- **Workspace-tilgang** — alle filer lagres i brukerens workspace-mappe
- **Internett** — for OSM-tiles, FOSSGIS routing og Wikipedia-oppslag
- **Chrome MCP** (valgfritt men anbefalt) — for visuell verifikasjon via screenshot
- **Brukerens samarbeid for finjustering** — særlig på koordinater og rute-godkjenning

## Viktige begrensninger (les før bruk)

**Opphavsrett og kreditering (standard arbeidsmåte).** `source_lookup.py` henter
tekst fra Wikipedia og lokale museumssider — dette er *råstoff*, ikke ferdig,
publiseringsklar tekst.

> **Default: skriv tekstene om til egne ord (behold fakta), og oppgi alltid
> kilden.** Fakta (byggeår, arkitekt, bruk) er frie å gjenfortelle; det er den
> konkrete *ordlyden* som er vernet. Omskriving unngår CC BY‑SA sin ShareAlike‑
> binding helt, og holder produktet som kundens eget.

- **Wikipedia** = CC BY‑SA 4.0: ordrett gjenbruk krever kreditering *og* at *hele*
  heftet deles under samme lisens (ShareAlike). Skriv heller om → da holder en
  kildehenvisning. Bruk ordrett kun unntaksvis, og merk i så fall hvert slikt
  punkt med «Tekst fra Wikipedia «X», CC BY‑SA 4.0».
- **Museums-/turistsider** = som regel «alle rettigheter forbeholdt». Ikke kopiér
  ordrett uten skriftlig avtale. Bruk som faktakilde og skriv om.
- **Koordinater/vernedata** (Riksantikvaren/Kulturminnesøk) og **kartdata** (OSM,
  via Nominatim/Overpass/CARTO) = faktadata, men kreditering er påkrevd. Oppgi dem
  i kolofonen.
- **Foto** = krediter per bilde (`photo_credit`).

**Slik krediteres det i produktet (felter i config):**
- `cover.colophon` — «Kilder og lisenser»-blokk nederst på forsiden (HTML tillatt).
  Bruk malen i `Snefokk-defaults` nedenfor.
- `points.<id>.source` — kort grå kildelinje under hver punkttekst (f.eks.
  «Bearbeidet fra Wikipedia (CC BY-SA 4.0)» eller «Vadsø museum»).
- `points.<id>.photo_credit` — fotograf/arkiv, vises i bildevisningen.
- `cover.sourceCredit` / `footer_source` — kort kreditt i ark-footer og verktøylinje.

**Geografisk dekning.** `source_lookup.py` har innebygde museumssider kun for
Varanger (Vadsø/Vardø/Sør‑Varanger → varangermuseum.no) pluss noen få andre.
- `candidate_pool.py` utleder nå bbox automatisk fra Nominatim for ukjente
  kommuner, men du kan overstyre med `--bbox "sør,vest,nord,øst"` hvis OSM-treffene
  blir for vide/smale.
- Lokal-museum-oppslag gir ingenting med mindre kommunen står i
  `LOCAL_MUSEUM_*`-tabellene. Legg eventuelt til kommunen der, eller fall tilbake
  til Wikipedia + manuell tekst.

**Auto-geokoding er «best effort».** `geocode.py` og `candidate_pool.py` deler nå
parseren i `_wikicoords.py`, som håndterer både desimal- og grad/minutt/sekund-
koordinater og forkaster treff utenfor Norge. Den kan likevel bomme på navne-
matching. **La alltid brukeren verifisere koordinatene** før bygg — be om Google
Maps-lenker for usikre punkter.

## Overordnet flyt

```
0. Velg tema                    → Foreslå hva stedet er kjent for → bruker velger tema (historie/mat/uteliv/gatekunst/…)
1. Samle kandidat-pool          → OSM (tema-tagger) + Wikipedia/museum for historiske tema, ELLER kuratert liste
2. Sjekk kildedekning           → For hvert punkt: hvilke tekstkilder finnes?
3. Brukeren velger punkter      → Basert på kildedekning + tilleggsønsker
4. Brukeren velger tekstkilde   → For hvert punkt: Wikipedia / lokal museum / egen
5. Foreslå oppdeling            → Klustering (geografisk) ELLER tema/gate-vis oppdeling i flere løyper
6. Auto-routing                 → FOSSGIS foot-profile + kvalitetsflagg
7. Brukerjustering (valgfritt)  → KML i Google My Maps for problemløyper
8. Bilder                       → Brukeren laster opp, scripts/match_images.py
9. Bygg HTML                    → Templating med config + brand
10. Verifiser visuelt           → Screenshot per løype, juster zoom om nødvendig
11. Lever                       → HTML + bilder/ til workspace
```

Ikke hopp over verifiseringstrinnet — det sparer mange runder med "kartet er feil zoom" som vi har erfart tidligere.

**Erfaring fra tidlige tester**: Tekstkildedekning varierer drastisk per kommune. For Vadsø fikk vi 100% dekning fra et eksisterende PDF-hefte. For Vardø: bare 4 av 13 punkter har egen Wikipedia-artikkel. **Sjekk alltid kildedekning før du forplikter deg til et sett punkter** — det er ofte bedre med færre godt dokumenterte enn mange tomme.

## Trinn 0: Hva er stedet kjent for → velg tema

Skillen lager ikke bare *historiske* løyper. Én løype = ett **tema**, og samme sted
kan ha flere: en historisk runde, en mat-/uteliv-runde, en gatekunst-runde osv.
(Et prosjekt kan ha flere tema-løyper side om side — akkurat som de geografiske
delturene.)

**Steg 0a — foreslå hva stedet er kjent for.** Slå opp Wikipedia-artikkelen for
kommunen/tettstedet (avsnittene «Kjent for» / «Severdigheter» / «Kultur») og se
hva som dominerer. Du kan også telle OSM-kategorier ved å kjøre `candidate_pool.py`
for et par tema og se antallet. Presenter 3–5 forslag, f.eks.:

```
Røros er kjent for: kobberverket/bergstaden (historie), trehusarkitektur, vintermarked.
Bergen er kjent for: Bryggen (historie), fisk/sjømat, uteliv, kunst (Munch/Astrup).
Vardø er kjent for: festning og pomorhistorie, fugleturisme, og Komafest-gatekunst.
```

**Steg 0b — la brukeren velge tema** med `AskUserQuestion`. Tilgjengelige presets
(`python3 scripts/candidate_pool.py --list-temaer`):

**Datadrevne presets** (`python3 scripts/candidate_pool.py --tema X`):

| Tema | Datakilde | Virker godt for |
|---|---|---|
| `kultur` | Riksantikvaren + OSM + museum | historiske byer (standard) |
| `arkitektur` | Riksantikvaren + OSM | trehusbyer, severdigheter |
| `religion` | OSM `place_of_worship` + `historic` | kirker/kapell/synagoger (Trondheim sentrum: 23) |
| `maritime` | OSM fyr/brygge/marina | kystbyer, sjøfartshistorie |
| `uteliv` | OSM `amenity` (bar/pub) | bar-crawl i byer |
| `shopping` | OSM `shop` | byer |
| `natur` | OSM `tourism`/`natural`/`leisure` | utsiktspunkter, parker |
| `smaksrunde` | OSM bakeri/iskrem/gatemat/mikrobryggeri | **smått å smake** — ikke middagsguide |
| `gatekunst` | OSM `artwork` (ofte tynt) | **som regel kuratert** |

> **NB om mat:** en *middagsløype* gir ikke mening (man spiser én middag). Bruk
> `smaksrunde` for ting man smaker litt av på flere stopp. «Hvor spiser jeg
> middag» er et «velg ett sted»-kart, ikke en vandring → `kommunekart`-skillen.

**To kildemodi** — vær ærlig med brukeren om hvilken som gjelder:
- **Datadrevet** (tabellen over): OSM/Riksantikvaren har punktene. Fungerer best i
  byer med god OSM-dekning (Bergen: 200+ spisesteder; Trondheim: 23 kirker i sentrum).
- **Kuratert** (smale, narrative eller lokale tema): OSM har dem sjelden — be
  brukeren (eller en lokal aktør: festival, forfatterforening, galleri,
  turistkontor, historielag) om en **manuell punktliste** (navn + adresse/koordinat
  + kort tekst). Skillens verdi her er bygg + ruting + print, ikke oppdagelsen.
  Behandle som «manuell liste» i Trinn 1. Populære kuraterte tema (research):
  - **Spøkelse / mørk historie** («spøkelsesvandring» er stort i Norge — Akershus, Kvadraturen)
  - **Krim / true-crime / litterær** («Harry Hole-løypa», lokale forfattere, kjente saker)
  - **Kunstner / maler** («Munch-steder», Astrup i Jølster — der en kjent person virket)
  - **Festival-gatekunst** (Komafest i Vardø, UPEA, o.l.)
  - **Innvandring / minoritet** (kvensk og samisk historie — f.eks. Vadsø; immigranthistorie)
  - **Industri / arbeider** (gruve, fabrikk, kraft — «Rivers of Steel»-typen)

> **«Gamleby»-løype** er ikke et eget tema — det er `kultur`/`arkitektur` *filtrert
> til den gamle bydelen* (snever bbox / utvalg). Bruk geografisk avgrensning, ikke
> et nytt preset.

## Trinn 1: Samle kandidat-pool

Spør brukeren via `AskUserQuestion`:

```
Hva er utgangspunktet ditt?
- Et eksisterende PDF-hefte → bruk pdf-skill først (gir 100% kildedekning)
- Manuell liste → spør om navn, evt. adresse, kort tekst per punkt (også for kuraterte tema)
- Bygg fra scratch → vi henter kandidater fra OSM (+ Wikipedia/museum for historiske tema)
```

**Hvis PDF**: Last inn PDF, kjør `scripts/extract_from_pdf.py`. Dette er den **beste** kilden — gå rett til Trinn 4.

**Hvis manuell / kuratert tema**: Brukeren oppgir punkter. Hopp til Trinn 4.

**Hvis fra scratch**: Kjør `scripts/candidate_pool.py` med temaet fra Trinn 0:

```bash
python3 scripts/candidate_pool.py --kommune Bergen --tema mat \
  --bbox "60.388,5.31,60.402,5.34" --output arbeid/kandidater.json
```

Skriptet samler kandidater fra (avhengig av tema):
1. **For historiske tema** (`kultur`/`arkitektur`): Wikipedia kulturminneliste (Riksantikvaren) + lokal museum-side
2. **OpenStreetMap** — tag-settet for det valgte temaet (mat → `amenity=restaurant…`, gatekunst → `tourism=artwork`, osv.)

Resultatet er en pool deduplikert på navn/koordinat. Disse er bare "mulige" — brukeren bestemmer hvilke som skal med. For store byer: filtrer til et gå-vennlig sentrum (snever `--bbox` eller etterfilter på avstand fra et sentrumspunkt).

Punkt-strukturen er:
```json
{
  "id": 1,
  "title": "Bietilægården",
  "address": "Havnegata 86",          // valgfri, vises i grå mindre font
  "coords": [70.0774, 29.7226],       // [lat, lon] — fyl inn i geokoding-trinn
  "text": "Bietilægården er en gård med kaianlegg fra 1880-tallet...",
  "image": "bilder/03-bietilaegarden.jpg"  // valgfri, lagt til senere
}
```

## Trinn 2: Sjekk kildedekning per kandidat

Før brukeren velger punkter, sjekk hvilke tekstkilder som finnes:

```bash
python3 scripts/source_lookup.py --kommune Vardø --punkter arbeid/kandidater.json --output arbeid/kilder.json
```

Skriptet sjekker for hvert punkt:
1. **Wikipedia REST API summary** (raskt, sammendrag)
2. **Wikipedia full første-paragraph** (hvis sammendrag for kort)
3. **Lokal museum besokssted-side** (varangermuseum.no, etc.)

Resultat: en tabell pr punkt med tilgjengelige kilder + tekst-kandidater.

Presenter denne tabellen for brukeren:

```
| # | Punkt | Wikipedia | Varangermuseum | Annet |
|---|-------|:---------:|:--------------:|:-----:|
| 1 | Vardøhus festning | ✅ | ✅ |  |
| 2 | Brodtkorbsjåene | ❌ | ✅ |  |
| 3 | Husegården | ❌ | ❌ | ⚠️ |
...
```

Detaljert om kilder, se [`references/text-sources.md`](references/text-sources.md).

## Trinn 3: Brukeren velger punkter

Basert på kilde-tabellen, la brukeren velge hvilke punkter hun vil ha med:

```
Du har 15 kandidater, men bare 8 har god tekstkilde. Anbefaling:
- Bruk de 8 med kilde som hovedløype
- Vurder om noen av de uten kilde er viktige nok at du vil skrive selv
```

Bruk `AskUserQuestion` med multiselect for et håndterlig sett (4 i gangen). For større sett: la brukeren liste numre i fri tekst.

## Trinn 4: Brukeren velger tekstkilde per punkt

For punkter med flere kilder, spør:

```
Vardøhus festning har to kilder:
A) Wikipedia: "Vardøhus festning er Norges østligste festning..."
B) Varangermuseum: "Velkommen til verdens nordligste festning..."
Hvilken vil du bruke? (A/B/skriv selv)
```

For punkter uten kilde:
```
Husegården har ingen tekstkilde. Vil du:
- Droppe punktet
- Skrive selv (gi meg 50-100 ord)
- Bruke placeholder ("Vernet kulturminne fra 1800-tallet. Beskrivelse kommer.")
```

## Trinn 5: Geokoding (hvis ikke allerede)

Hvis kandidatene mangler koordinater (f.eks. fra PDF-extraction), kjør `scripts/geocode.py`:

```bash
python3 scripts/geocode.py --kommune Vardø --punkter arbeid/valgte.json
```

For punkter uten koordinater:
- List dem til brukeren med `AskUserQuestion`
- Be henne om Google Maps-lenker for hvert
- Parse koordinatene fra URL-en (`@lat,lon` eller `!3dLAT!4dLON`)

## Trinn 6: Foreslå oppdeling i delturer

> **Merk:** Det finnes *ikke* et eget `cluster_routes.py`-script. Klustringen gjør
> agenten inline (få punkter, kjøres én gang). Standardbiblioteket holder — du
> trenger ikke `pip install`.

Grupper punktene geografisk, ~4–6 grupper avhengig av byens utstrekning. En
enkel stdlib-tilnærming (single-linkage med haversine, terskel ≈ 500 m):

```python
# Slå sammen punkter som ligger < 500 m fra hverandre (union-find / single-linkage).
# haversine_m finnes allerede i auto_route.py — kopier funksjonen inn.
THRESHOLD_M = 500
parent = list(range(len(pts)))
def find(i):
    while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
    return i
for i in range(len(pts)):
    for j in range(i + 1, len(pts)):
        if haversine_m(pts[i]["coords"], pts[j]["coords"]) < THRESHOLD_M:
            parent[find(i)] = find(j)
# Grupper på find(i) → juster terskel til du får 4–6 fornuftige grupper.
```

Hvis `scikit-learn` *tilfeldigvis* er installert kan du heller bruke
`DBSCAN(eps=0.005, min_samples=2)` (≈500 m), men det er valgfritt — ikke en
forutsetning for skillen.

> **Kompakte byer & tema-løyper:** Geografisk klustring passer dårlig når alt
> ligger tett (f.eks. Røros sentrum) — da blir det bare én klynge. Del heller
> **tematisk eller gate-vis** (f.eks. «Kjerkgata», «Sleggveien», «Malmplassen»),
> eller etter *under-tema* (mat: «kafé-runde» vs «fine-dining»). Hver løype er
> uansett bare en `route` med sin egen `order` — du står fritt til å gruppere
> etter geografi, gate, eller tema.

Vis brukeren et oversiktskart med foreslåtte grupper (HTML-side genereres lokalt). Brukeren kan justere ved å flytte punkter mellom grupper.

For hver gruppe, foreslå et navn (basert på bydel) og en farge fra paletten:
- `#c0392b` (rød)
- `#2980b9` (blå)
- `#27ae60` (grønn)
- `#d4a017` (oker/gul)
- `#8e44ad` (lilla)
- `#16a085` (turkis) — for 6+ løyper

## Trinn 7: Auto-routing med kvalitetsflagg

For hver løype, kjør `scripts/auto_route.py`:

```bash
python3 scripts/auto_route.py --config arbeid/loyper.json --output arbeid/walk_routes.json
```

Scriptet:
1. Henter rute fra `routing.openstreetmap.de/routed-foot/` mellom hvert par av punkter
2. Beregner luftlinje-distansen som baseline
3. **Flagger segmentet** hvis:
   - rute_distanse < 0.5 × luftlinje (OSRM ga "trivial" svar — ingen sti funnet)
   - rute_distanse > 1.8 × luftlinje (OSRM tar lang omveg — sannsynligvis dårlig OSM-data)
4. Lagrer alle segmenter, samt en liste over flaggede

Vis brukeren flaggede segmenter med:
```
Løype 3 (Vadsøya):
  ⚠️ Pkt 5 → Pkt 6 (Luftskipsmasta → Krigsminner): rute 5m, luftlinje 211m
     OSRM fant ingen sti. Vil du lage manuell rute i Google My Maps?
```

## Trinn 8: Manuell rutejustering (valgfritt)

Hvis brukeren vil overstyre flaggede segmenter:

1. Kjør `scripts/generate_kml.py` for å lage start-KML med markører + auto-rute
2. Be brukeren om å:
   - Åpne mymaps.google.com
   - Importere KML-fila
   - Justere ruten ved å dra i den
   - Eksportere KML tilbake til `outputs/`-mappen
3. Når brukeren har levert tilbake, kjør `scripts/parse_kml.py` for å erstatte de auto-generertede rutene

Skillen kan også gjøre dette per delsegment hvis bare deler av en løype trenger justering.

## Trinn 9: Bilder (brukeren laster opp selv)

Bilder håndteres **manuelt av brukeren**, ikke automatisk. Grunner:
- Wikimedia Commons har sjelden bilder av lokale kulturminner i mindre byer
- Hver kommune har sin egen museum-nettside — ikke generaliserbart
- Brukeren har ofte tilgang til høyere kvalitet via lokale arkiver/eget kamera

**Be brukeren laste opp bildene** og bruk denne navnekonvensjonen:

```
{punkt-id}-{slugified-tittel}.jpg

Eksempler:
01-bietilaegarden.jpg
04-tiberghuset.jpg
17-innvandringsmonumentet.jpg
```

Slik gjør du det:
1. Spør brukeren om hun har bilder (de fleste museum/næringsforeninger har dem)
2. Hvis ja: be henne legge dem i en mappe (f.eks. `bilder-til-loype/`)
3. Bruk `scripts/match_images.py` for å mappe opplastede bilder mot punktene basert på filnavn
4. Skillen kopierer dem til `outputs/bilder/` med riktig naming og oppdaterer punkt-konfigen

```bash
python3 scripts/match_images.py \
  --config arbeid/config-final.json \
  --input bilder-fra-bruker/ \
  --output-dir outputs/bilder/ \
  --update-config        # uten dette flagget skrives IKKE image-stiene til config
```

Hvis brukeren ikke har bilder: skillen fungerer fint uten — `image`-feltet er valgfritt.

**Bilder som er valgfritt** = HTML-fila viser punktene fint uten thumbnails. Bilder kan legges til senere uten å re-bygge alt.

## Trinn 10: Bygg HTML

Først: slå sammen `points`, `routes` og `walkRoutes` til **én** `config-final.json`
sammen med `title`, `subtitle`, `cover`, `colors` osv. (se
`templates/config-eksempel.json` for full struktur). `build_html.py` tar bare
*én* config-fil — ikke separate `--punkter`/`--walk-routes`.

```bash
python3 scripts/build_html.py \
  --config arbeid/config-final.json \
  --template templates/kulturloype-template.html \
  --output outputs/kulturloype-vadso.html
```

Templatet inneholder placeholders som `{{TITLE}}`, `{{ROUTES_JSON}}`, `{{POINTS_JSON}}`, `{{WALK_ROUTES_JSON}}` osv. Bygge-scriptet erstatter disse med faktiske data.

**`notes`-konvensjon:** `route.notes` er nøklet på *lokalt stoppnummer* i løypa
(1 = første stopp i `order`), ikke på punkt-ID. `{ "9": "..." }` viser altså
notatet etter det 9. stoppet.

## Trinn 11: Visuell verifikasjon

**Dette er det viktigste trinnet.** Hopp ikke over det.

Kjør `scripts/verify_screenshot.py`:

```bash
python3 scripts/verify_screenshot.py outputs/kulturloype-vadso.html
```

> **Hva scriptet faktisk gjør:** det starter en lokal `http.server` i HTML-fila
> sin mappe og skriver ut en sjekkliste. Selve screenshot-takingen og
> vurderingen gjør **agenten** (via Chrome MCP eller `preview_*`-verktøyene) —
> scriptet gjør ingen OCR og endrer ikke HTML-en automatisk.

Agentens jobb, per løype (`#rute1`, `#rute2`, … + forsiden `#cover`):
1. Naviger til `http://localhost:8765/<fil>.html#rute<N>`, vent ~4 sek på at kartet laster, ta screenshot.
2. Vurder:
   - Er alle markører innenfor kart-viewport?
   - Er minst 3 gatenavn synlige?
   - Er rute-linjen synlig (ikke under markører)?
3. Hvis problem: juster `center+zoom` eller `bounds` for løypa i `config-final.json`, bygg på nytt, ta nytt screenshot. Gjenta til OK eller maks ~3 forsøk.
4. Lever screenshots til brukeren for sluttgodkjenning.

**Sjekk også en ekte PDF, ikke bare skjermbildet.** Noen markør-feil (fargeløse markører, mørke firkanter rundt tallene) dukker *bare* opp i selve PDF-rasteriseringen — se «Vanlige feilsituasjoner». Generer én PDF og se på en kart-side før levering:
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --no-pdf-header-footer --print-to-pdf=/tmp/kul-test.pdf \
  http://localhost:8765/<fil>.html --virtual-time-budget=8000
pdftoppm -png -r 150 -f 2 -l 2 /tmp/kul-test.pdf /tmp/kulpage   # side 2 = første løype
```
Markørene skal være rene fargede sirkler med hvit kant — ingen grå firkanter, ingen fargeløse badges.

**Visningsmoduser per løype** (samme datastruktur som vi sluttet med i Vadsø):
- `bounds: [[s, w], [n, e]]` — for løyper med store områder
- `center: [lat, lon], zoom: 15` — for ett-punkts-løyper med kontekst
- *(ingen, default)* — auto-fitBounds basert på markører + ruten

## Trinn 12: Lever

Endelig output:
- `outputs/kulturloype-<kommune>.html` — hovedfil
- `outputs/bilder/` — alle bilder
- `outputs/<Kommune> Kulturløype <N>.kml` — original KML-er for hver løype (så brukeren kan oppdatere senere)

Gi brukeren en `computer://`-lenke til HTML-fila + en kort guide:
- Hvordan printe (Cmd+P → "Behold bakgrunnsfarger" → A4 portrait)
- Hvordan oppdatere ruter (rediger KML i My Maps, kjør `parse_kml.py` på nytt)

## Filer og scripts i skillen

```
kulturloype/
├── SKILL.md                          (denne fila)
├── templates/
│   └── kulturloype-template.html     (HTML med placeholders)
├── scripts/
│   ├── _wikicoords.py                (delt parser for Wikipedia kulturminneliste)
│   ├── extract_from_pdf.py           (PDF → punkter)
│   ├── candidate_pool.py             (Wikipedia + OSM + lokal museum → kandidater)
│   ├── source_lookup.py              (tekstkilde-dekning per punkt)
│   ├── geocode.py                    (Wikipedia + Nominatim)
│   ├── auto_route.py                 (FOSSGIS foot-routing; klustring gjøres inline, se Trinn 6)
│   ├── generate_kml.py               (lag KML for My Maps)
│   ├── parse_kml.py                  (importere brukerens KML)
│   ├── match_images.py               (mappe opplastede bilder mot punkter)
│   ├── build_html.py                 (templating)
│   └── verify_screenshot.py          (lokal server + sjekkliste for visuell sjekk)
└── references/
    ├── workflow.md                   (steg-for-steg detaljert)
    ├── text-sources.md               (hvilke tekstkilder finnes + copyright)
    ├── coord-sources.md              (hvor finne koordinater)
    └── kml-import-export.md          (Google My Maps round-trip)
```

## Vanlige feilsituasjoner

**Punkt mangler koordinater etter geokoding** → Be brukeren om Google Maps-lenke. Parse `@lat,lon` eller `!3dLAT!4dLON` fra URL.

**OSRM/FOSSGIS gir for lang rute** → Auto-routing-scriptet har innebygd kvalitetsflagg. Tilby brukeren KML-justering for det spesifikke segmentet.

**Kart zoomer for langt ut og viser ikke gatenavn** → Sett `center+zoom: 15` eller `bounds` med snevre verdier. Verifiser med screenshot.

**To markører overlapper** → Håndteres nå automatisk: templaten har `spreadMarkers()` som vifter ut markører som ligger nærmere enn 30 px fra hverandre (i en liten sirkel rundt felles tyngdepunkt), og kjører på nytt ved zoom/print. Rute-linjen røres ikke. Bare hvis to punkter har *helt* like koordinater og du vil ha dem på ekte plass, juster koordinatene manuelt.

**A4-print får tekst som flyter til neste side** → Reduser font-størrelse i `@media print` eller del løypa i to.

**Nummer-markørene mister farge / får mørk firkant i PDF** → To separate Chrome-print-feil på samme divIcon-markør, begge løst i malen (`@media print`):
- *Fargeløse markører*: nettleseren dropper `background`-farger ved «Lagre som PDF». Kreves `-webkit-print-color-adjust: exact; print-color-adjust: exact;` på `html, body` (kantlinjer printes uansett, bakgrunner ikke).
- *Mørk grå firkant rundt markøren*: `box-shadow` rendres som en hard firkant (følger ikke `border-radius`) i PDF. Sett `.num-marker { box-shadow: none !important; }` i `@media print` — den hvite 2px-kanten gir nok kontrast.
Verifiser alltid en **ekte PDF**, ikke bare skjerm/print-emulering — begge feilene dukker bare opp i selve PDF-rasteriseringen. Rask sjekk: `chrome --headless=new --print-to-pdf` mot en lokalt servert kopi, så `pdftoppm -png` på en kart-side.

## Snefokk-defaults

Med mindre kommunen har egne brand-farger:
- Tittel-font: Helvetica Neue
- 5 løype-farger: rød, blå, grønn, oker, lilla (kontrasterende, gode for daltonisme)
- Bakgrunn: papirhvit `#ffffff` for kart-area, lett gråbeige `#f4f1ea` for omgivelser
- Footer: "© [Kommune] / [Museumsnavn] (kildetekster)"

**Kolofon-mal** (lim inn i `cover.colophon`, bytt ut `[…]`):

```
<strong>Kilder og lisenser</strong><br>
Kartdata © OpenStreetMap-bidragsytere (ODbL) · karttegning © CARTO.<br>
Koordinater og vernedata: Riksantikvaren / Kulturminnesøk.<br>
Stedstekstene er bearbeidet av [Museum/Næringsforening] på grunnlag av
Wikipedia (CC BY-SA 4.0) og lokale kilder. Foto: se den enkelte bildetekst.<br>
© [Kommune / Næringsforening] [år].
```
