# byvandring

Lag en printbar **A4 byvandring** for et norsk tettsted — historiske løyper eller tematiske runder, klare til print, med interaktiv web-versjon. En åpen skill for Claude (Cowork / Claude Code).

> **Vil du heller at vi lager løypa for deg?**
> Bestill en ferdig byvandring på **[snefokk.com/byvandring](https://snefokk.com/byvandring)** — så bygger Snefokk løypa, tilpasser profilen og leverer print-klar HTML + web-versjon. Dette repoet er for deg som vil gjøre jobben selv, gratis.

## Hva skillen lager

- **A4-ark klart til print** — én side per løype, kart øverst og infotekst under, print på en helt vanlig kontorprinter
- **Flere løyper i samme hefte** — del byen i mindre runder (geografisk, gate-vis eller tematisk)
- **Faktiske gå-ruter** mellom punktene — ekte fotgjenger-ruter fra OpenStreetMap, ikke luftlinje
- **Tema du velger** — historie/kulturminner, arkitektur, religion, maritim, uteliv, shopping, natur, smaksrunde, gatekunst — eller kuraterte tema som «Munch-løypa» eller «Harry Hole-løypa»
- **Kildekreditering innebygd** — kolofon på forsiden + «Kilde:»-linje per punkt + fotokreditt
- **Interaktiv web-versjon** — klikkbare markører og bilder; markørene sprer seg automatisk så tette punkter ikke overlapper

Koordinater og tekst hentes automatisk fra Riksantikvarens kulturminneregister, OpenStreetMap og Wikipedia under byggingen.

## Hvem det er for

- Kommuner, turistkontor og besøkssentre som vil ha lavterskel byvandringer
- Museer og historielag som vil digitalisere en kulturløype eller et gammelt hefte
- Næringsforeninger og reiselivsorganisasjoner
- Festivaler og lokale aktører med et tema å formidle (gatekunst, forfattere, sjøfart …)

## To måter å få løypa

| Gjør det selv (dette repoet) | La Snefokk gjøre jobben |
| --- | --- |
| Gratis — krever et Claude-abonnement | Bestill på **[snefokk.com/byvandring](https://snefokk.com/byvandring)** |
| Du kjører skillen selv i Claude — bygg og oppdater så ofte du vil | Snefokk bygger, tilpasser profilen og leverer, med én tilbakemeldingsrunde |
| **Ferdig på under en time** (med god internettforbindelse) | **Klart innen typisk en uke** |

## Hva du trenger (for å gjøre det selv)

- Et aktivt **Claude Pro**-abonnement (eller høyere) — skillen kjører i Claude Cowork / Claude Code
- **Python 3** — for å bygge HTML-en (kun standardbibliotek, ingen `pip install`; finnes på de fleste maskiner)
- **curl** — brukes som fallback for gå-ruter (finnes på macOS/Linux som standard)
- **Internett-tilgang** — kart, routing, Wikipedia, Riksantikvaren/OSM
- *Valgfritt:* **pdftotext** (poppler) — kun hvis du digitaliserer et eksisterende PDF-hefte

Skillen i seg selv er gratis og åpen kildekode.

## Kom i gang (gjør det selv)

1. **Last ned skillen** — klon eller last ned dette repoet.
2. **Installer i Claude** — pek Cowork/Claude Code mot skill-mappa (`~/.claude/skills/`).
3. **Følg `SKILL.md`** — den tar deg steg for steg: velg tema, hent punkter, godkjenn ruter og bygg.

## Bygg fra en konfig-fil (avansert)

Skillen produserer en `config.json` og bygger HTML-en med et lite Python-skript (kun standardbibliotek — ingen `pip install`):

```bash
python3 scripts/build_html.py \
  --config arbeid/config-final.json \
  --template templates/byvandring-template.html \
  --output outputs/byvandring-<kommune>.html
```

Se hvilke tema som finnes, og hent kandidatpunkter for ett av dem:

```bash
python3 scripts/candidate_pool.py --list-temaer
python3 scripts/candidate_pool.py --kommune Trondheim --tema religion \
  --bbox "63.41,10.36,63.44,10.42" --output arbeid/kandidater.json
```

## Eksempler

Løyper bygget med skillen:

- **Vadsø** — historisk kulturløype, 5 løyper / 31 punkter (basert på kommunens gamle hefte)
- **Røros** — Bergstaden i 3 gate-vise løyper / 18 punkter (bygget «fra scratch»)

## Lisens

Se [LICENSE](LICENSE). MIT — åpen kildekode, bruk, modifiser og del fritt.
