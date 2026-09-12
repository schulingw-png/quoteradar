#!/usr/bin/env python3
"""
post.py - plaatst een QuoteRadar post via de Buffer GraphQL API.

Buffer verzorgt de koppeling met X, dus er zijn geen X API kosten.
Endpoint: https://api.buffer.com (altijd POST, altijd GraphQL).

Gebruik:
    python post.py --channels
        Toont je organisatie en kanalen. Draai dit een keer om
        BUFFER_CHANNEL_ID te vinden.

    python post.py --text "Tekst van de post"
        Zet de post in de Buffer wachtrij.

    python post.py --from output/queue/2026-09-12.json
        Leest tekst, beeld en tijdstip uit een bestand van compose.py.

    python post.py --text "..." --at 2026-09-12T15:30:00Z
        Plant de post op een vast tijdstip.

    DRY_RUN=true python post.py --text "..."
        Schrijft alleen naar het logbestand, plaatst niets.

Omgevingsvariabelen:
    BUFFER_API_KEY      verplicht, uit Buffer settings > API
    BUFFER_CHANNEL_ID   verplicht bij plaatsen
    BUFFER_ORG_ID       optioneel, wordt anders opgehaald
    DRY_RUN             true/false, standaard false

Exit codes:
    0 = geplaatst of droog gedraaid
    1 = fout
    2 = niets te doen (leeg payloadbestand)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_URL = "https://api.buffer.com"
LOG_PATH = Path("output/posted_log.jsonl")
TIMEOUT = 30


# --------------------------------------------------------------------
# Transport
# --------------------------------------------------------------------

def graphql(query: str, api_key: str) -> dict:
    """Stuurt een GraphQL verzoek en geeft het data blok terug.

    Buffer geeft altijd HTTP 200 terug. Fouten staan in het antwoord:
    niet herstelbare fouten in de errors array, herstelbare fouten
    als getypeerd object in data. Beide worden hier afgevangen.
    """
    body = json.dumps({"query": query}).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"HTTP {error.code}: {error.read().decode('utf-8')[:500]}")
    except urllib.error.URLError as error:
        raise RuntimeError(f"Netwerkfout: {error.reason}")

    if payload.get("errors"):
        messages = "; ".join(e.get("message", "?") for e in payload["errors"])
        raise RuntimeError(f"GraphQL fout: {messages}")

    return payload.get("data") or {}


def gql_string(value: str) -> str:
    """Escapet een Python string tot een geldige GraphQL string literal.

    Buffer verwacht enums (schedulingType, mode) zonder aanhalingstekens,
    dus de input wordt als literal opgebouwd in plaats van met variabelen.
    JSON escaping is compatibel met GraphQL string escaping.
    """
    return json.dumps(value)


# --------------------------------------------------------------------
# Queries
# --------------------------------------------------------------------

def get_org_id(api_key: str) -> str:
    data = graphql("query { account { organizations { id } } }", api_key)
    orgs = (data.get("account") or {}).get("organizations") or []
    if not orgs:
        raise RuntimeError("Geen organisatie gevonden op dit Buffer account.")
    return orgs[0]["id"]


def list_channels(api_key: str, org_id: str) -> list:
    query = f"""
    query GetChannels {{
      channels(input: {{ organizationId: {gql_string(org_id)} }}) {{
        id
        name
        displayName
        service
        isQueuePaused
      }}
    }}
    """
    return graphql(query, api_key).get("channels") or []


def create_post(api_key: str, channel_id: str, text: str,
                image_url: str | None = None, due_at: str | None = None) -> dict:
    """Maakt de post aan. Zonder due_at gaat hij in de wachtrij."""
    fields = [
        f"text: {gql_string(text)}",
        f"channelId: {gql_string(channel_id)}",
        "schedulingType: automatic",
    ]

    if due_at:
        fields.append("mode: customScheduled")
        fields.append(f"dueAt: {gql_string(due_at)}")
    else:
        fields.append("mode: addToQueue")

    if image_url:
        fields.append(f"assets: [{{ image: {{ url: {gql_string(image_url)} }} }}]")

    query = f"""
    mutation CreatePost {{
      createPost(input: {{ {", ".join(fields)} }}) {{
        ... on PostActionSuccess {{
          post {{ id text status dueAt }}
        }}
        ... on MutationError {{
          message
        }}
      }}
    }}
    """

    result = graphql(query, api_key).get("createPost") or {}

    if "message" in result:
        raise RuntimeError(f"Buffer weigerde de post: {result['message']}")
    if "post" not in result:
        raise RuntimeError(f"Onverwacht antwoord van Buffer: {result}")

    return result["post"]


# --------------------------------------------------------------------
# Logboek
# --------------------------------------------------------------------

def log(entry: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry["logged_at"] = datetime.now(timezone.utc).isoformat()
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------
# Hoofdprogramma
# --------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Plaats een post via Buffer.")
    parser.add_argument("--channels", action="store_true",
                        help="Toon organisatie en kanalen, plaats niets.")
    parser.add_argument("--text", help="Tekst van de post.")
    parser.add_argument("--from", dest="payload_file",
                        help="JSON bestand met text, image_url en due_at.")
    parser.add_argument("--image", help="Publieke URL van de quotekaart.")
    parser.add_argument("--at", help="ISO 8601 tijdstip, bijvoorbeeld 2026-09-12T15:30:00Z.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Log alleen, plaats niets.")
    args = parser.parse_args()

    api_key = os.environ.get("BUFFER_API_KEY")
    if not api_key:
        print("BUFFER_API_KEY ontbreekt.", file=sys.stderr)
        return 1

    dry_run = args.dry_run or os.environ.get("DRY_RUN", "").lower() == "true"

    # Kanalen tonen
    if args.channels:
        org_id = os.environ.get("BUFFER_ORG_ID") or get_org_id(api_key)
        print(f"Organisatie: {org_id}\n")
        for channel in list_channels(api_key, org_id):
            paused = " (wachtrij gepauzeerd)" if channel.get("isQueuePaused") else ""
            print(f"{channel['service']:<12} {channel['id']}  {channel.get('displayName') or channel['name']}{paused}")
        return 0

    # Inhoud bepalen
    text, image_url, due_at = args.text, args.image, args.at

    if args.payload_file:
        path = Path(args.payload_file)
        if not path.exists():
            print(f"Bestand niet gevonden: {path}", file=sys.stderr)
            return 1
        payload = json.loads(path.read_text(encoding="utf-8"))
        text = text or payload.get("text")
        image_url = image_url or payload.get("image_url")
        due_at = due_at or payload.get("due_at")

    if not text or not text.strip():
        print("Geen tekst om te plaatsen.", file=sys.stderr)
        return 2

    # X kapt op 280 tekens voor niet betaalde accounts
    if len(text) > 280:
        print(f"Tekst is {len(text)} tekens, dat is te lang voor X.", file=sys.stderr)
        return 1

    # Links kosten meer en halen minder bereik, dus alleen als het bewust is
    if "http" in text:
        print("Waarschuwing: de tekst bevat een link.", file=sys.stderr)

    channel_id = os.environ.get("BUFFER_CHANNEL_ID")
    if not channel_id:
        print("BUFFER_CHANNEL_ID ontbreekt. Draai eerst --channels.", file=sys.stderr)
        return 1

    record = {"text": text, "image_url": image_url, "due_at": due_at,
              "channel_id": channel_id, "dry_run": dry_run}

    if dry_run:
        log({**record, "status": "dry_run"})
        print("DROOG GEDRAAID, niets geplaatst:\n")
        print(text)
        if image_url:
            print(f"\n[beeld] {image_url}")
        return 0

    try:
        post = create_post(api_key, channel_id, text, image_url, due_at)
    except RuntimeError as error:
        log({**record, "status": "error", "error": str(error)})
        print(str(error), file=sys.stderr)
        return 1

    log({**record, "status": "created", "post_id": post.get("id")})
    print(f"Geplaatst in Buffer. Post id: {post.get('id')}, status: {post.get('status')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
