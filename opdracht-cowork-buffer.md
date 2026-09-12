# Opdracht: Buffer koppeling opzetten voor QuoteRadar

## Context

QuoteRadar is een X account (@QuoteRadar) dat geverifieerde uitspraken van bekende
ondernemers en investeerders koppelt aan actueel bedrijfsnieuws. Het project dient twee
doelen: een echt contentaccount, en oefenen met automatisering.

De code staat lokaal in `Desktop/quoteradar`. Werk uitsluitend in die map.

Wat er al staat:

- `fetch_news.py` haalt RSS van Bloomberg, CNBC en MarketWatch
- `match_quotes.py` matcht nieuws op uitspraken via trefwoorden, met blocklist
- `generate_review.py` sorteert op score en publicatiedatum
- `data/quotes.json` geverifieerde uitspraken
- `data/blocklist.json` gevoelige nieuwscategorieen
- `PROJECT_STATUS.md` contextbestand dat sessies gelijk houdt
- `post.py` nieuw, plaatst een post via de Buffer API (bijgeleverd)

## Waarom Buffer

De X API heeft sinds februari 2026 geen gratis laag meer. Buffer heeft een permanent
gratis abonnement waar X bij zit, inclusief API toegang met een sleutel en 3.000
verzoeken per 30 dagen. Buffer betaalt de X kosten zelf. Daarom loopt het plaatsen via
Buffer en niet rechtstreeks via X.

## Wat je moet doen

1. Controleer of `post.py` in `Desktop/quoteradar` staat. Zo niet, meld dat en stop.
2. Maak een `.env` bestand met `BUFFER_API_KEY`. De sleutel krijg je van de gebruiker.
   Vraag erom als hij ontbreekt. Zet de sleutel nooit in code of in git.
3. Zet `.env` in `.gitignore`. Maak `.gitignore` aan als die er niet is.
4. Draai `python post.py --channels`. Dit toont de organisatie en de kanalen.
5. Zoek het kanaal met service `twitter` en zet het id als `BUFFER_CHANNEL_ID` in `.env`.
6. Draai een droge test: `DRY_RUN=true python post.py --text "Test"`. Er mag niets
   naar buiten gaan. Controleer dat er een regel bijkomt in `output/posted_log.jsonl`.
7. Rapporteer het resultaat: organisatie id, kanaal id, en of de droge test slaagde.
8. Werk `PROJECT_STATUS.md` bij met een kort blok over de Buffer koppeling.

## Belangrijk

- Plaats niets echt op X zonder expliciete toestemming van de gebruiker. Stap 6 is de
  laatste stap die je zelfstandig uitvoert.
- Gebruik niet de X API rechtstreeks. Alles loopt via Buffer.
- Quote tweets zijn niet mogelijk. X heeft die per 20 april 2026 uit alle
  zelfbedieningslagen gehaald. Stel dat niet voor.
- Zet geen sleutels in `PROJECT_STATUS.md` of in een commit.

## Technische feiten over de Buffer API

Deze zijn nagetrokken in de documentatie, ga er niet vanaf zonder reden.

- Endpoint: `https://api.buffer.com`, altijd POST, altijd GraphQL
- Auth: header `Authorization: Bearer <sleutel>`
- Sleutel aanmaken: Buffer settings, onderdeel API
- Buffer geeft altijd HTTP 200 terug. Niet herstelbare fouten staan in de `errors`
  array, herstelbare fouten komen terug als `MutationError` binnen data.

Organisatie ophalen:

```graphql
query { account { organizations { id } } }
```

Kanalen ophalen:

```graphql
query GetChannels {
  channels(input: { organizationId: "ORG_ID" }) {
    id
    name
    displayName
    service
    isQueuePaused
  }
}
```

Post aanmaken:

```graphql
mutation CreatePost {
  createPost(input: {
    text: "tekst",
    channelId: "KANAAL_ID",
    schedulingType: automatic,
    mode: customScheduled,
    dueAt: "2026-09-12T15:30:00Z"
  }) {
    ... on PostActionSuccess { post { id text status } }
    ... on MutationError { message }
  }
}
```

Zonder `dueAt` gebruik je `mode: addToQueue`. Beeld gaat mee als
`assets: [{ image: { url: "..." } }]`, dus als publieke URL en niet als bestand.

## Werkafspraken van dit project

- Uitspraak, spreker, jaartal en bron komen altijd letterlijk uit `data/quotes.json`.
  Nooit door een model laten formuleren.
- Geen kandidaat boven de drempel betekent die dag niet plaatsen.
- Geen links in de post zelf.
- Tekst blijft onder 280 tekens.
- Toon moet menselijk zijn: geen opsommingstekens, geen gedachtestreepjes.

## Resultaat dat ik verwacht

Een `.env` met beide waarden, een aangevulde `.gitignore`, een geslaagde droge test,
een bijgewerkte `PROJECT_STATUS.md`, en een korte terugkoppeling van wat er gebeurde.
Meld het gewoon als iets niet lukt, verzin geen omweg.
