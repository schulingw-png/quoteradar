#!/usr/bin/env python3
"""auto_post.py - draait de volledige QuoteRadar-pipeline lokaal en plaatst
automatisch de beste match van vandaag via Buffer, zonder handmatige
tussenkomst.

Volgorde:
    1. scripts/fetch_news.py       - verse RSS-data ophalen
    2. scripts/match_quotes.py     - matchen tegen quotes.json (blocklist +
                                      drempel zitten al in match_quotes.py)
    3. scripts/generate_review.py  - review.md bijwerken (eigen archief)
    4. scripts/post_best_match.py  - beste nieuwe match kiezen en plaatsen

Dit script gaat ervan uit dat fetch_news.py rechtstreeks toegang heeft tot
het open internet (werkt op een gewoon netwerk, bijv. lokaal op een Mac).
In omgevingen waar dat niet zo is (bijv. sommige cloud-sandboxes met
beperkt uitgaand verkeer), haalt een sessie het nieuws zelf op via zijn
eigen tools en draait vanaf stap 2 los verder - zie de instructies van de
betreffende geplande routine.

Exit codes:
    0 = geplaatst, of bewust niets te plaatsen (geen kandidaat)
    1 = fout
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def run_step(script: str) -> None:
    result = subprocess.run([sys.executable, script], cwd=BASE_DIR)
    if result.returncode != 0:
        raise RuntimeError(f"{script} faalde (exit code {result.returncode})")


def main() -> int:
    run_step("scripts/fetch_news.py")
    run_step("scripts/match_quotes.py")
    run_step("scripts/generate_review.py")

    result = subprocess.run(
        [sys.executable, "scripts/post_best_match.py"], cwd=BASE_DIR
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
