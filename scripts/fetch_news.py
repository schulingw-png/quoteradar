"""Haalt zakelijk nieuws op via RSS feeds en slaat gefilterde artikelen op als JSON."""
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "output" / "news.json"

# Reuters biedt sinds 2020 geen publieke RSS-feeds meer aan; MarketWatch
# Business dient hier als vervanging voor "Reuters Business".
FEEDS = {
    "Bloomberg": "https://feeds.bloomberg.com/markets/news.rss",
    "CNBC": "https://www.cnbc.com/id/10001147/device/rss/rss.html",
    "MarketWatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
}

# Nederlandse en Engelse varianten, want de feeds zijn Engelstalig.
KEYWORDS = [
    "aandelen", "aandeel", "stock", "stocks", "shares",
    "winst", "profit", "profits", "earnings",
    "overname", "acquisition", "takeover", "merger",
    "markt", "markets", "market",
    "beurs", "ipo", "dividend", "omzet", "revenue",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    )
}


def fetch_feed(url: str) -> bytes:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read()


def parse_pubdate(raw_date: str) -> str:
    if not raw_date:
        return ""
    try:
        return parsedate_to_datetime(raw_date).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        return raw_date


def matches_keywords(title: str) -> bool:
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in KEYWORDS)


def parse_feed(xml_bytes: bytes, source: str) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    articles = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        if not title or not matches_keywords(title):
            continue
        articles.append({
            "source": source,
            "title": title,
            "link": link,
            "published": parse_pubdate(pub_date),
        })
    return articles


def collect_news() -> list[dict]:
    all_articles = []
    for source, url in FEEDS.items():
        try:
            xml_bytes = fetch_feed(url)
            articles = parse_feed(xml_bytes, source)
            all_articles.extend(articles)
            print(f"{source}: {len(articles)} relevante artikelen gevonden")
        except Exception as exc:
            print(f"{source}: kon feed niet ophalen ({exc})")
    return all_articles


def main() -> None:
    articles = collect_news()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(articles, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n{len(articles)} artikelen opgeslagen in {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
