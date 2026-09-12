## Project
QuoteRadar (@QuoteRadar) — een X-account dat dagelijks een quote van een
bekende ondernemer of investeerder koppelt aan een actueel nieuwsartikel
dat er inhoudelijk bij past. Tegelijk een leerproject om met Claude Code
te werken aan automatisering.

## Account-status (buiten de code)
- Naam: QuoteRadar, handle: @QuoteRadar
- Banner en profielfoto: klaar (radar-logo met aanhalingsteken, donkere
  zakelijke stijl)
- Bio: nog te kiezen uit tien opties — nog open

## Technische structuur
- Map: Desktop/quoteradar, Python project met venv
- data/quotes.json — 35 quotes van 24 bekende zakenmensen, met text,
  author en keywords (Nederlands + Engels, mix van filosofische en
  nieuwstaal-trefwoorden)
- data/blocklist.json — blocklist gevoelig nieuws (7 categorieën, NL+EN):
  faillissement, ontslag, overlijden, fraude, rechtszaak, ramp, boete
- scripts/fetch_news.py — haalt nieuws op via RSS (Bloomberg, CNBC,
  MarketWatch), schrijft output/news.json
- scripts/match_quotes.py — matcht quotes aan nieuws op trefwoordoverlap,
  met KEYWORD_SYNONYMS/SYNONYM_TO_CANONICAL voor NL/EN-canonicalisatie,
  MIN_KEYWORD_SCORE als instelbare drempel, en blocked_reason() die
  artikelen tegen de blocklist checkt vóór matching. Schrijft
  output/matches.json
- scripts/generate_review.py — sorteert op (score, publicatiedatum),
  toont drempelmonitor bovenaan, schrijft output/review.md met
  goedkeuren/afkeuren-checkboxes per match
- post.py — plaatst een post via de Buffer GraphQL API (niet rechtstreeks
  via X, want X heeft sinds februari 2026 geen gratis API-laag meer;
  Buffer heeft een gratis laag met 3.000 verzoeken/30 dagen en betaalt de
  X-kosten zelf). Ondersteunt --channels (kanalen tonen), --text/--from
  (post samenstellen), --at (inplannen), en DRY_RUN=true (alleen loggen,
  niets plaatsen). Logt elke poging naar output/posted_log.jsonl

## Voortgang (fases)
- Fase 1, projectstructuur: klaar
- Fase 2, nieuws ophalen (fetch_news.py): klaar
- Fase 3, quotes matchen aan nieuws (match_quotes.py): klaar,
  matchrate 21/21 (100%)
- Fase 4, kwaliteitsdrempel + score: klaar (MIN_KEYWORD_SCORE=1,
  instelbaar, huidige matches zitten allemaal op de drempel)
- Fase 4b, gevoelig-nieuws-filter (blocklist): klaar, 0/21 artikelen
  geraakt in huidige testrun
- Fase 5, review-overzicht (generate_review.py): klaar
- Fase 6, posten: Buffer-koppeling technisch klaar (zie hieronder),
  daadwerkelijk automatisch posten nog niet gedaan — elke keer expliciete
  toestemming nodig voordat post.py zonder DRY_RUN draait
- Fase 7, volledige testrun van nieuws tot voorstel: nog te doen

## Buffer-koppeling (2026-09-12)
- Reden voor Buffer i.p.v. rechtstreeks de X API: X heeft sinds februari
  2026 geen gratis laag meer; Buffer wel (3.000 verzoeken/30 dagen,
  Buffer betaalt de X-kosten zelf)
- `.env` aangemaakt met BUFFER_API_KEY en BUFFER_CHANNEL_ID (nooit in git —
  `.env` staat in `.gitignore`; sleutelwaarden staan hier bewust niet)
- Organisatie-id: 6aa599498bcd2d49c063139c
- Twitter-kanaal "QuoteRadar", channel-id: 6aa59dbbcd8b9c702c59c03d,
  wachtrij niet gepauzeerd
- Buffer↔X-koppeling was al actief (door de gebruiker zelf gedaan,
  buiten deze sessie om)
- Droge test (`DRY_RUN=true python post.py --text "Test"`) geslaagd:
  niets naar buiten, wel een regel toegevoegd aan output/posted_log.jsonl
- post.py bevatte een Python 3.9-incompatibiliteit (`str | None` in
  functiesignatuur zonder `from __future__ import annotations`, de venv
  hier draait op 3.9.6) — gefixt met dezelfde aanpak als eerder bij
  match_quotes.py
- Nog niet gedaan: een echte post plaatsen. Dat gebeurt pas na expliciete
  toestemming per keer, nooit automatisch als vaste regel

## Belangrijk aandachtspunt
Matches moeten inhoudelijk kloppen en goed aanvoelen voor lezers, niet
generiek of geforceerd. Trefwoordscore alleen is niet genoeg —
handmatige review blijft de uiteindelijke controle. Aandachtspunt:
bij score 1 kan een match technisch correct zijn maar toch ver gezocht
aanvoelen; dat is een reden om ook bij lage scores kritisch te blijven
reviewen, niet alleen bij afwijzen op basis van score.

Blocklist-gedrag (getest met randgevallen op 2026-08-01): de blocklist
blokkeert op trefwoord, niet op sentiment. Een blocklist-woord in een
overigens positief artikel (bv. "rechtszaak geschikt, aandeel stijgt 5%")
wordt alsnog volledig uitgesloten van matching. Dit is een bewuste afweging:
het voorkomt dat negatieve artikelen doorglippen, ten koste van af en toe
een gemist positief artikel. Herformuleringen zonder het letterlijke
trefwoord (bv. "sluit 200 filialen" zonder het woord "faillissement") worden
niet gepakt — dat blijft binnen het bereik van de handmatige review, niet
van de blocklist. Geen actie nodig; dit is vastgelegd zodat het gedrag
bekend blijft bij toekomstige sessies.
