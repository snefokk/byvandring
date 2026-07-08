# Hvor finner vi koordinater for kulturminner?

Dette dokumentet er en cheat sheet for `geocode.py` og for situasjoner der den automatiske geokoderen ikke finner noe.

## Prioriterte kilder (i rekkefølge)

### 1. Wikipedia "Liste over kulturminner i [kommune]"

URL-mønster: `https://no.wikipedia.org/wiki/Liste_over_kulturminner_i_<kommune>`

Eksempler:
- [Liste over kulturminner i Vadsø](https://no.wikipedia.org/wiki/Liste_over_kulturminner_i_Vads%C3%B8)
- [Liste over kulturminner i Vardø](https://no.wikipedia.org/wiki/Liste_over_kulturminner_i_Vard%C3%B8)
- [Liste over kulturminner i Hammerfest](https://no.wikipedia.org/wiki/Liste_over_kulturminner_i_Hammerfest)

Disse listene er hentet fra **Riksantikvarens kulturminneregister**, så koordinatene er offisielle og presise.

### 2. Kulturminnesøk (Riksantikvaren)

URL: https://www.kulturminnesok.no

Hvis Wikipedia ikke har en liste for kommunen, kan agenten søke direkte hos Riksantikvaren. Ikke en API, men HTML-scraping fungerer.

### 3. OpenStreetMap (via Overpass API)

For tourism, museum, viewpoint, monument tags:

```
[out:json];
(
  node["historic"](70.06,29.7,70.09,29.85);
  node["tourism"](70.06,29.7,70.09,29.85);
);
out;
```

URL: `https://overpass-api.de/api/interpreter`

Bra for severdigheter som ikke er i Riksantikvarens register (utsiktspunkter, monumenter, modern attraksjoner).

### 4. Nominatim (OpenStreetMap geokoder)

For adresser og kjente steder med navn:

```
https://nominatim.openstreetmap.org/search?q=<navn>+<kommune>+norway&format=json
```

OBS: maks 1 forespørsel/sek + User-Agent påkrevd.

### 5. Google Maps (manuelt — siste utvei)

Be brukeren søke i Google Maps og dele lenken. URL inneholder koordinater i ett av to mønstre:

- `@LAT,LON,Z` — visningssenter
- `!3dLAT!4dLON` — markørposisjon (mer presist)

Foretrekk `!3d!4d` hvis tilgjengelig.

## Hvordan håndtere når flere kilder gir ulike koordinater

Forhold:
1. **Wikipedia/Riksantikvar** — autoritativ for kulturminner med vernestatus
2. **Google Maps** — bra for moderne adresser og bedrifter
3. **OSM/Nominatim** — bra dekning, men kan være unøyaktig på små POI

Hvis Wikipedia og Google Maps er innenfor 50m: bruk Wikipedia (offisielt vernet punkt)
Hvis avviket er > 100m: be brukeren om å bekrefte hvilken som stemmer

## Kommune-spesifikke kilder

| Kommune | Spesifikk kilde |
|---------|-----------------|
| Vadsø | varangermuseum.no — Vadsø museum-Ruija kvenmuseum, har bilde-arkiv også |
| Vardø | varangermuseum.no — Pomormuseet, Gammelskolen |
| Hammerfest | gjenreisningsmuseet.no |
| Tromsø | tromsmuseum.no, polarmuseet.no |
| Bergen | bymuseet.no |
| Oslo | oslomuseum.no, oslobymuseum.no |

Når skillen kjenner igjen et kommune-navn, sjekker den om det finnes en lokal museum-side med kulturminne-data.
