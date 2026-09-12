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
- auto_post.py — draait fetch_news.py, match_quotes.py en
  generate_review.py achter elkaar, kiest daarna zelf de beste nieuwe
  match (score, dan publicatiedatum, met een dedup van 14 dagen tegen
  exact dezelfde eerder geplaatste quote) en post 'm via post.py, zonder
  handmatige tussenkomst. Quote en auteur komen altijd letterlijk uit
  matches.json/quotes.json. Geen kandidaat boven de drempel betekent
  bewust niet posten die run

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
- Fase 6, posten: klaar — volledig geautomatiseerd op expliciet verzoek
  van de gebruiker (bewuste keuze, zie hieronder: geen handmatige
  goedkeuring per post meer, alleen blocklist + score-drempel + dedup
  als controle)
- Fase 7, volledige testrun van nieuws tot voorstel: klaar, zie
  Buffer-koppeling hieronder (eerste live post is geplaatst)

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
- Eerste echte post is handmatig getriggerd (via auto_post.py, niet
  DRY_RUN): "If you're changing the world, you're working on important
  things." — Larry Page, Buffer post-id 6aa59ec17da3ee968d0240e9

## Volledige automatisering (2026-09-12)
- Op expliciet verzoek van de gebruiker ("ik wil het juist automatiseren,
  het is voor mij niet een heel serieus project") is gekozen voor volledig
  automatisch posten, zonder goedkeuring per post. Dit is een bewuste
  afwijking van het eerdere "altijd expliciete toestemming"-uitgangspunt
  — vastgelegd zodat toekomstige sessies niet per ongeluk terugvallen op
  de oude, voorzichtigere aanname
- `Desktop/quoteradar` is een git-repo geworden, gepusht naar
  https://github.com/schulingw-png/quoteradar (nodig omdat cloud-routines
  alleen uit een git-repo kunnen draaien). `.env`, `venv/` en `output/`
  staan in `.gitignore` en zijn nooit gepusht
- Een Claude Code cloud-routine "QuoteRadar" (id
  trig_01L1udSXDpKJ8emGskgxW6JH) draait dagelijks om 09:00 Europe/Amsterdam
  (cron 0 7 * * *, UTC) op environment env_01FcsphzjLegExxQjKhMsbR4, kloont
  de repo, en voert auto_post.py uit
- Bewuste afweging over de sleutel: er is in deze sessie geen manier
  gevonden om een los "geheim"/environment variable aan een cloud-routine
  mee te geven. De BUFFER_API_KEY en BUFFER_CHANNEL_ID staan daarom
  letterlijk in de prompt/instructions van de routine, wat betekent dat ze
  in leesbare vorm opgeslagen liggen in de routine-configuratie bij
  Anthropic (zichtbaar voor wie de routine kan beheren op
  claude.ai/code/routines). De gebruiker is hierover expliciet gevraagd
  (incl. het alternatief van een aparte, losse sleutel) en heeft bewust
  gekozen om dezelfde sleutel te hergebruiken
- De routine had bij aanmaken standaard vier MCP-connectors gekoppeld
  (Gmail, Google Drive, Portfolio Dividend Tracker, visualize) die niets
  met dit project te maken hebben — verwijderd via een update
  (clear_mcp_connections), de routine heeft nu alleen toegang tot de
  eigen repo
- Nog open: auto_post.py plaatst hooguit één nieuwe post per run en
  vermijdt herhaling van exact dezelfde quote binnen 14 dagen, maar heeft
  geen expliciete "al gepost vandaag"-check. Bij precies één run per dag
  (huidige schema) is dat geen probleem; wordt relevant als de
  cron-frequentie ooit omhoog gaat

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
