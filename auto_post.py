#!/usr/bin/env python3
"""auto_post.py - draait de QuoteRadar-pipeline en plaatst automatisch de
beste match van vandaag via Buffer, zonder handmatige tussenkomst.

Volgorde:
    1. fetch_news.py       - verse RSS-data ophalen
    2. match_quotes.py     - matchen tegen quotes.json (blocklist + drempel
                              zitten al in match_quotes.py zelf)
    3. generate_review.py  - review.md bijwerken (alleen voor eigen archief,
                              wordt niet gelezen door dit script)
    4. beste match kiezen (zelfde sortering als generate_review.py: score,
       dan publicatiedatum), met een lichte dedup op eerder geplaatste
       quotes (laatste 14 dagen), zodat niet elke dag toevallig dezelfde
       quote terugkomt
    5. post.py aanroepen zonder DRY_RUN - dit plaatst echt

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

BASE_DIR = Path(__file__).resolve().parent
MATCHES_PATH = BASE_DIR / "output" / "matches.json"
LOG_PATH = BASE_DIR / "output" / "posted_log.jsonl"
DEDUP_WINDOW_DAYS = 14


def run_step(script: str) -> None:
    result = subprocess.run([sys.executable, script], cwd=BASE_DIR)
    if result.returncode != 0:
        raise RuntimeError(f"{script} faalde (exit code {result.returncode})")


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
    run_step("scripts/fetch_news.py")
    run_step("scripts/match_quotes.py")
    run_step("scripts/generate_review.py")

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
