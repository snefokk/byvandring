# Tekstkilder for kulturminner

Dette er en oversikt over hvilke tekstkilder skillen sjekker, og hva som faktisk fungerer i praksis. Basert på erfaring fra Vadsø og Vardø-testene.

## Prioriterte kilder

### 1. Wikipedia (norsk REST API)

**Hva**: Sammendrag fra Wikipedia-artikkelen for kulturminnet.

**Endepunkt**:
```
https://no.wikipedia.org/api/rest_v1/page/summary/{tittel}
```

**Hvor godt fungerer**:
- For **kjente kulturminner med egen artikkel**: 100%, og teksten er ofte fagfellevurdert
- For **mindre kjente**: typisk 30-40% har egen artikkel
- Mange ikke-arkitektoniske kulturminner (kirkegårder, tradisjonslokaliteter, spekkproduksjon) har sjelden artikkel

**Eksempler som fungerer**:
- Vardøhus festning
- Vardø kirke
- Pomormuseet
- Steilneset minnested
- Brodtkorbsjåene

**Eksempler som ikke fungerer**:
- Husegården, Vardø slipp, Norges Bank Vardø, Vardø gamle barneskole (alle "rød lenke" på Wikipedia)

### 2. Lokalt museums-nettsted

**Hva**: Dedikerte besøkssteder-sider hos kommune-museet.

**Eksempel**: `https://www.varangermuseum.no/besok-oss/besokssteder/{slug}/`

**Hvor godt fungerer**:
- For kulturminner som museet aktivt formidler: typisk god kvalitet (50-200 ord)
- Dekker ofte: museumsbygninger, festninger, kjente kulturminner
- Ikke garantert for: mindre kulturminner, private bygg

**Kjente lokale museum-sider** (utvides etter behov):
| Kommune | URL |
|---|---|
| Vadsø, Vardø, Sør-Varanger | varangermuseum.no |
| Hammerfest | gjenreisningsmuseet.no |
| Tromsø | uit.no/tmu eller polarmuseet.no |
| Bergen | bymuseet.no |
| Oslo | oslomuseum.no |

### 3. Riksantikvarens Kulturminnesøk

**Hva**: Vernebegrunnelse fra Riksantikvaren.

**Endepunkt**: `https://www.kulturminnesok.no/minne?id={askeladden_id}`

**Utfordring**: Sidens er en SPA — krever browser-emulator (Selenium/Playwright) for å hente data. **Ikke implementert i skillen ennå.**

**Alternativ**: data.kulturminne.no har en JSON-API:
```
https://data.kulturminne.no/askeladden/lokalitet/{id}
```
men responsen er ofte XML og ikke alltid med beskrivende tekst.

### 4. OpenStreetMap-tags

**Hva**: For tourism:museum, historic:* tags har OSM ofte "description"-tag.

**Endepunkt**: Overpass API
```
[out:json];
node["tourism"="museum"]["name"="X"];
out tags;
```

**Hvor godt fungerer**: Sjelden god tekst, men gir alternative navn (`alt_name`) og kategori-info.

### 5. Visit Norway / regionale turistsider

**Hva**: Turistmessig beskrivelse.

**Eksempler**:
- visitnorway.com (har spesifikke sider for hovedattraksjoner)
- travel-north.no (Nord-Norge)
- nordnorge.com

**Hvor godt fungerer**: God for STORE attraksjoner (Vardøhus, Lofoten osv.), mindre for spesifikke gater/hus.

## Praktisk strategi for skillen

Skillen følger denne sekvensen for hvert punkt:

```
1. Wikipedia REST API summary
   ↓ (hvis < 50 ord eller ingen artikkel)
2. Wikipedia full første-paragraph (mer detaljert)
   ↓
3. Lokal museum-side (hvis kjent kommune)
   ↓
4. Markert som "trenger manuell tekst"
```

> **Implementasjonsstatus:** `source_lookup.py` gjør i dag steg 1–3. OSM
> `description`-tag og Riksantikvar/Kulturminnesøk er *ikke* implementert (begge
> krever henholdsvis Overpass-navnesøk og SPA-rendering) — de hentes manuelt ved
> behov. Lokal museum-oppslag dekker kun kommuner som står i `LOCAL_MUSEUM_HOSTS`.

Resultatet presenteres til brukeren som en tabell, og hun velger:
- Hvilke punkter å ha med (basert på kilde-dekning)
- Hvilken tekstkilde å bruke per punkt
- Eventuelt skrive selv eller redigere

## Erfaringer

### Vadsø (31 punkter fra PDF)
- PDF-hefte med eksisterende tekst: 100% dekning, god kvalitet
- Konklusjon: PDF-hefte er den **beste** kilden hvis tilgjengelig

### Vardø (test fra Wikipedia + supplering)
- 13 punkter fra Wikipedia kulturminneliste: bare 4 hadde egen Wikipedia-artikkel (31%)
- Etter supplering med Steilneset, Pomormuseet, Brodtkorbsjåene: 6 av 7 valgte punkter har god kilde
- Konklusjon: **Vurder kilde-dekning før du velger punkter**

### Anbefaling per kommune

| Kommune | Beste kildestrategi |
|---|---|
| Vadsø | PDF-heftet finnes — bruk det |
| Vardø | Wikipedia + Varangermuseum gir 6-8 gode punkter |
| Hammerfest | Sjekk gjenreisningsmuseet.no først |
| Tromsø | Wikipedia har gode artikler for mange sentrum-bygg |
| Mindre kommuner | Sannsynligvis manuell tekstskriving for de fleste punkter |

## Når ingen kilde funnet

Hvis et punkt ikke har noen kilde, skal skillen:

1. **Foreslå å droppe punktet** — er det virkelig viktig nok for en kulturløype hvis ingen har skrevet om det?
2. **Spørre brukeren** om hun har lokal kunnskap (besteforeldre, museum-ansatte)
3. **Generere kort placeholder** basert på Riksantikvar-kategori og periode, så brukeren kan finjustere:
   > "Bygård/Forsvarsanlegg/Fiskevær-sjøbruksanlegg fra [periode]. Vernet i Riksantikvarens kulturminneregister."
