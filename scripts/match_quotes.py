"""Matcht nieuwsartikelen aan quotes op basis van gedeelde trefwoorden."""
from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NEWS_PATH = BASE_DIR / "output" / "news.json"
QUOTES_PATH = BASE_DIR / "data" / "quotes.json"
BLOCKLIST_PATH = BASE_DIR / "data" / "blocklist.json"
OUTPUT_PATH = BASE_DIR / "output" / "matches.json"

# Minimaal aantal overeenkomende trefwoorden voor een geldige match. Optrekken
# naar 2 zodra er structureel genoeg matches met score 2+ ontstaan.
MIN_KEYWORD_SCORE = 1

# data/quotes.json gebruikt Nederlandse trefwoorden, terwijl de nieuwstitels
# Engelstalig zijn. Deze mapping koppelt elk Nederlands trefwoord aan de
# Engelse (en Nederlandse) varianten waarop in een titel wordt gezocht.
KEYWORD_SYNONYMS = {
    "risico": ["risk", "risico"],
    "kennis": ["knowledge", "kennis"],
    "waarde": ["value", "worth", "waarde"],
    "investeren": ["invest", "investing", "investment", "investor", "investeren"],
    "kwaliteit": ["quality", "kwaliteit"],
    "groei": ["growth", "grow", "grows", "growing", "groei"],
    "innovatie": ["innovation", "innovate", "innovative", "innovatie"],
    "leiderschap": ["leadership", "leader", "leiderschap"],
    "passie": ["passion", "passie"],
    "werk": ["work", "job", "jobs", "werk"],
    "ambitie": ["ambition", "ambitious", "ambitie"],
    "management": ["management", "manager"],
    "toekomst": ["future", "toekomst"],
    "efficiëntie": ["efficiency", "efficient", "efficientie", "efficiëntie"],
    "verandering": ["change", "changes", "changing", "verandering"],
    # concrete nieuwstaal
    "aandelen": ["stock", "stocks", "share", "shares", "equity", "equities", "aandeel", "aandelen"],
    "winst": ["profit", "profits", "earnings", "winst"],
    "overname": ["acquisition", "acquires", "acquire", "takeover", "merger", "buyout", "overname"],
    "beurs": ["exchange", "bourse", "nasdaq", "nyse", "beurs"],
    "ipo": ["ipo", "listing"],
    "dividend": ["dividend", "dividends"],
    "omzet": ["revenue", "sales", "turnover", "omzet"],
    "aanbod": ["supply", "aanbod"],
    "vraag": ["demand", "vraag"],
    "rente": ["interest rate", "interest rates", "rente", "rentetarief"],
    "inflatie": ["inflation", "inflatie"],
}

# Keert KEYWORD_SYNONYMS om: elke variant (Nederlands of Engels) wijst terug
# naar het canonieke Nederlandse trefwoord. Hiermee kunnen quote-keywords die
# zelf in het Engels staan (bv. "stock") ook worden vergeleken met trefwoorden
# die uit een titel zijn gehaald (die altijd canoniek Nederlands zijn).
SYNONYM_TO_CANONICAL = {
    synonym.lower(): canonical
    for canonical, synonyms in KEYWORD_SYNONYMS.items()
    for synonym in synonyms
}


def canonicalize_keyword(keyword: str) -> str:
    normalized = keyword.strip().lower()
    return SYNONYM_TO_CANONICAL.get(normalized, normalized)


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def blocked_reason(title: str, blocklist: dict) -> str | None:
    """Geeft een omschrijving terug als de titel een gevoelig/negatief
    trefwoord bevat (bv. faillissement, ontslag, fraude), anders None."""
    title_lower = title.lower()
    for category, terms in blocklist.items():
        for term in terms:
            if term.lower() in title_lower:
                return f"{category} (trefwoord: '{term}')"
    return None


def extract_keywords(title: str) -> set:
    """Geeft de Nederlandse trefwoorden terug waarvan een variant voorkomt in de titel."""
    title_lower = title.lower()
    return {
        keyword
        for keyword, synonyms in KEYWORD_SYNONYMS.items()
        if any(synonym in title_lower for synonym in synonyms)
    }


def best_quote_for(article_keywords: set, quotes: list):
    """Kiest de quote met de meeste overeenkomende trefwoorden. Geeft None
    terug als geen enkele quote een overeenkomst heeft."""
    best_quote = None
    best_overlap: set = set()
    for quote in quotes:
        quote_keywords = {canonicalize_keyword(k) for k in quote.get("keywords", [])}
        overlap = article_keywords & quote_keywords
        if len(overlap) > len(best_overlap):
            best_quote = quote
            best_overlap = overlap
    if best_quote is None or len(best_overlap) < MIN_KEYWORD_SCORE:
        return None
    return best_quote, best_overlap


def build_matches(articles: list, quotes: list, blocklist: dict) -> list:
    matches = []
    for article in articles:
        title = article.get("title", "")

        reason = blocked_reason(title, blocklist)
        if reason is not None:
            print(f"Overgeslagen (gevoelig nieuws — {reason}): \"{title}\"")
            continue

        article_keywords = extract_keywords(title)
        if not article_keywords:
            continue
        result = best_quote_for(article_keywords, quotes)
        if result is None:
            continue
        quote, matched_keywords = result
        matches.append({
            "article": {
                "source": article.get("source"),
                "title": title,
                "link": article.get("link"),
                "published": article.get("published"),
            },
            "quote": quote["text"],
            "author": quote["author"],
            "matched_keywords": sorted(matched_keywords),
        })
    return matches


def main() -> None:
    articles = load_json(NEWS_PATH)
    quotes = load_json(QUOTES_PATH)
    blocklist = load_json(BLOCKLIST_PATH)
    matches = build_matches(articles, quotes, blocklist)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(matches, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"{len(matches)} van {len(articles)} artikelen gematcht met een quote")
    for match in matches[:5]:
        print(f"\n- \"{match['article']['title']}\"")
        print(f"  trefwoorden: {', '.join(match['matched_keywords'])}")
        print(f"  quote: \"{match['quote']}\" — {match['author']}")


if __name__ == "__main__":
    main()
