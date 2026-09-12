#!/usr/bin/env python3
"""post_best_match.py - kiest de beste (nieuwe) match uit output/matches.json
en plaatst 'm via post.py, zonder DRY_RUN - dit plaatst echt.

Aangenomen wordt dat output/matches.json al vers is (bijv. via
scripts/fetch_news.py + scripts/match_quotes.py, of via een alternatieve
manier waarop een sessie zelf nieuws heeft opgehaald). Dit script haalt
zelf geen nieuws op en matcht niets - het kiest alleen en post.

Sortering: zelfde als generate_review.py (score, dan publicatiedatum), met
een lichte dedup op eerder geplaatste quotes (laatste DEDUP_WINDOW_DAYS
dagen), zodat niet elke dag toevallig dezelfde quote terugkomt.

Exit codes:
    0 = geplaatst, of bewust niets te plaatsen (geen kandidaat)
    1 = fout
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MATCHES_PATH = BASE_DIR / "output" / "matches.json"
LOG_PATH = BASE_DIR / "output" / "posted_log.jsonl"
DEDUP_WINDOW_DAYS = 14


def parse_published(value: str) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def recently_posted_texts() -> set:
    """Posttekst van elke succesvol geplaatste post in de laatste
    DEDUP_WINDOW_DAYS, zodat dezelfde quote niet meteen terugkomt."""
    if not LOG_PATH.exists():
        return set()
    cutoff = datetime.now(timezone.utc) - timedelta(days=DEDUP_WINDOW_DAYS)
    posted = set()
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("status") != "created":
            continue
        try:
            when = datetime.fromisoformat(entry.get("logged_at", ""))
        except ValueError:
            continue
        if when >= cutoff:
            posted.add(entry.get("text"))
    return posted


def build_post_text(match: dict) -> str:
    # Quote en auteur komen letterlijk uit data/quotes.json (via matches.json),
    # nooit herformuleerd door een model.
    return f"“{match['quote']}”\n\n— {match['author']}"


def pick_best_new_match() -> dict | None:
    if not MATCHES_PATH.exists():
        return None
    matches = json.loads(MATCHES_PATH.read_text(encoding="utf-8"))
    ranked = sorted(
        matches,
        key=lambda m: (
            len(m["matched_keywords"]),
            parse_published(m["article"].get("published", "")),
        ),
        reverse=True,
    )
    already_posted = recently_posted_texts()
    for match in ranked:
        if build_post_text(match) not in already_posted:
            return match
    return None


def main() -> int:
    match = pick_best_new_match()
    if match is None:
        print("Geen (nieuwe) kandidaat boven de drempel vandaag. Niet geplaatst.")
        return 0

    text = build_post_text(match)
    if len(text) > 280:
        print(f"Posttekst te lang ({len(text)} tekens), niet geplaatst.", file=sys.stderr)
        return 1

    print("Plaatsen:\n")
    print(text)
    print()

    result = subprocess.run([sys.executable, "post.py", "--text", text], cwd=BASE_DIR)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
