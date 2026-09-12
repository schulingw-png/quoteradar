"""Zet output/matches.json om naar een leesbaar Markdown-reviewbestand."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MATCHES_PATH = BASE_DIR / "output" / "matches.json"
OUTPUT_PATH = BASE_DIR / "output" / "review.md"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from match_quotes import MIN_KEYWORD_SCORE  # noqa: E402


def load_matches() -> list:
    with MATCHES_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def parse_published(value: str) -> datetime:
    """Parseert de ISO-publicatiedatum voor sortering. Ontbrekende of
    onleesbare datums vallen achteraan (oudste)."""
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def render_match(number: int, match: dict) -> str:
    article = match["article"]
    keywords = match["matched_keywords"]
    score = len(keywords)

    lines = [
        f"## {number}. {article['title']}",
        "",
        f"- **Bron:** {article.get('source', 'onbekend')}",
        f"- **Link:** [{article['title']}]({article['link']})",
        f"- **Gepubliceerd:** {article.get('published', 'onbekend')}",
        "",
        f"> \"{match['quote']}\" — {match['author']}",
        "",
        f"**Trefwoorden:** {', '.join(keywords)} (score: {score})",
        "",
        "- [ ] Goedkeuren",
        "- [ ] Afkeuren",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def build_review(matches: list) -> str:
    ranked = sorted(
        matches,
        key=lambda m: (
            len(m["matched_keywords"]),
            parse_published(m["article"].get("published", "")),
        ),
        reverse=True,
    )

    at_minimum = sum(1 for m in ranked if len(m["matched_keywords"]) == MIN_KEYWORD_SCORE)

    header = [
        "# QuoteRadar Review",
        "",
        f"{len(ranked)} matches, gesorteerd op score (aantal overeenkomende trefwoorden) van hoog naar laag, "
        "bij gelijke score op publicatiedatum (nieuwste eerst).",
        "",
        f"**Huidige drempel:** MIN_KEYWORD_SCORE = {MIN_KEYWORD_SCORE} (zie `scripts/match_quotes.py`). "
        f"{at_minimum} van de {len(ranked)} matches zitten precies op deze drempel en zouden afvallen "
        f"als je hem verhoogt naar {MIN_KEYWORD_SCORE + 1}.",
        "",
        "---",
        "",
    ]
    body = [render_match(i, match) for i, match in enumerate(ranked, start=1)]
    return "\n".join(header) + "\n".join(body)


def main() -> None:
    matches = load_matches()
    review = build_review(matches)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(review, encoding="utf-8")
    print(f"{len(matches)} matches geschreven naar {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
