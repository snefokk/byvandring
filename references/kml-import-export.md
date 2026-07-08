# Google My Maps round-trip via KML

Når auto-routingen ikke gir bra nok rute (særlig i naturparker, fjell, eller områder med dårlig OSM-data), kan brukeren tegne ruten manuelt i Google My Maps og eksportere den tilbake.

## Hvorfor My Maps og ikke Google Maps Directions?

| | Google Maps Directions | Google My Maps |
|---|---|---|
| Lager URL | Ja | Ja |
| Eksporterer KML | Nei | Ja |
| Inneholder rute-geometri i KML | N/A | Ja |
| Fri | Ja | Ja |

Vanlige Google Maps Directions-lenker (`/maps/dir/`) inneholder kun waypoint-koordinater, ikke selve rute-linjen. Den ligger på Googles servere og krever betalt Directions API.

My Maps (`mymaps.google.com`) tegner og eksporterer hele rute-geometrien som KML LineString.

## Workflow

### Eksport (skillen → My Maps)

Skillen kan generere en start-KML med `scripts/generate_kml.py` som inneholder:

```xml
<Placemark>
  <name>Bietilægården</name>
  <Point><coordinates>29.7226,70.0774,0</coordinates></Point>
</Placemark>
...
<Placemark>
  <name>Auto-rute (juster om nødvendig)</name>
  <LineString>
    <coordinates>
      29.7226,70.0774,0
      29.7227,70.0774,0
      ...
    </coordinates>
  </LineString>
</Placemark>
```

Lever filen til brukeren med instruksjoner:

```
1. Åpne mymaps.google.com og logg inn
2. Trykk "+ Opprett et nytt kart"
3. Klikk "Importer" under det første laget (venstre meny)
4. Last opp <filnavn>.kml
5. Markørene og en foreslått rute vises på kartet
6. Klikk på rute-linjen og dra punkter for å justere veien
7. Når du er ferdig: tre prikker øverst → "Last ned KML"
8. Velg "Eksporter som KML i stedet for KMZ" (viktig!)
9. Lagre i samme mappe som du fikk fila fra
```

### Import (My Maps → skillen)

Når brukeren har eksportert oppdatert KML, kjør:

```bash
python3 scripts/parse_kml.py "Vadsø Byvandring 3.kml" --output arbeid/loype3.json --split-segments
```

`--split-segments` deler den lange LineString-en i N-1 segmenter mellom de N markørene. Det er det formatet `walkRoutes` i HTML-templaten forventer.

Resultatet ser slik ut:

```json
{
  "name": "Vadsø Byvandring 3",
  "points": [
    { "name": "Inngang", "lat": 70.0675, "lon": 29.7497 },
    { "name": "Russekirkegården", "lat": 70.0668, "lon": 29.7510 },
    ...
  ],
  "segments": [
    [[70.0675, 29.7497], [70.0670, 29.7501], ...],
    [[70.0668, 29.7510], [70.0660, 29.7520], ...],
    ...
  ],
  "segment_count": 6
}
```

Erstatt `walkRoutes["3"]` i `arbeid/walk_routes.json` med segments-arrayen.

## KML-struktur skillen forventer

Minimum:
- En `<Document><name>` med kart-tittel
- N `<Placemark>` med `<Point><coordinates>` for hver markør (i rekkefølge)
- En `<Placemark>` med `<LineString><coordinates>` for hele ruten

`generate_kml.py` produserer dette automatisk. Brukerens redigering i My Maps endrer ikke strukturen, så `parse_kml.py` plukker det opp uten endringer.

## Kjente fallgruver

1. **KMZ vs KML**: My Maps eksporterer KMZ som default (ZIP-pakket). Påminn brukeren å velge "KML" hvis valget kommer.
2. **Markør-rekkefølge**: My Maps bevarer ikke alltid markør-rekkefølgen i den eksporterte KML-en. Hvis det er viktig, instruer brukeren om å nummerere markørene i navnet (f.eks. "1. Bietilægården").
3. **Linjer på flere lag**: Hvis brukeren legger til ekstra lag, plukker `parse_kml.py` opp alle LineStrings. Be henne holde alt på ett lag.
4. **Maks 10 waypoints**: Google My Maps har ingen begrensning på markører, men vanlige Google Maps Directions har 10. Hvis brukeren har laget ruten i Directions først, må de splitte i flere ruter.
