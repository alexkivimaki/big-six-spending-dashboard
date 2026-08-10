#!/usr/bin/env python3

"""Collect raw Transfermarkt achievements pages as HTML."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clubs", default="config/clubs.json")
    parser.add_argument("--club", help="Optional club_id filter, for example arsenal")
    parser.add_argument("--base-url", default="https://www.transfermarkt.com")
    parser.add_argument("--request-delay-seconds", type=float, default=1.5)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--output", default="data/raw/transfermarkt/achievement_pages")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-collect pages even if raw HTML already exists locally.",
    )
    return parser.parse_args()


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def build_url(base_url: str, club: dict) -> str:
    return f"{normalize_base_url(base_url)}/{club['slug']}/erfolge/verein/{club['transfermarkt_club_id']}"


def save_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def collect_one(
    session: requests.Session,
    club: dict,
    output_dir: Path,
    base_url: str,
    timeout_seconds: float,
    overwrite: bool,
) -> bool:
    url = build_url(base_url, club)
    collected_at = datetime.now(timezone.utc).isoformat()
    league_key = club.get("league_key", "unknown_league")
    club_output_dir = output_dir / league_key / "all_years" / club["club_id"]
    club_output_dir.mkdir(parents=True, exist_ok=True)
    stem = club_output_dir / f"{club['club_id']}_all_years_transfermarkt_achievements_raw"
    html_path = stem.with_suffix(".html")
    meta_path = stem.with_suffix(".meta.json")

    if html_path.exists() and not overwrite:
        print(f"[skip] Raw HTML already exists for {club['club_name']}: {html_path}")
        return True

    print(f"[collect] {club['club_name']} achievements -> {url}")

    try:
        response = session.get(url, timeout=timeout_seconds)
    except requests.RequestException as exc:
        print(f"[error] Request failed for {club['club_id']}: {exc}")
        return False

    metadata = {
        "club_id": club["club_id"],
        "club_name": club["club_name"],
        "league_key": league_key,
        "league_name": club.get("league_name", ""),
        "source_name": "transfermarkt_achievements_page",
        "source_url": url,
        "collected_at_utc": collected_at,
        "status_code": response.status_code,
        "collection_method": "direct_html_scrape",
    }

    save_text(html_path, response.text)
    save_json(meta_path, metadata)
    print(f"[saved] {html_path}")

    if not response.ok:
        print(f"[warn] Received HTTP {response.status_code} for {url}")
    return response.ok


def main() -> int:
    args = parse_args()
    clubs = load_json(Path(args.clubs))
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.club:
        clubs = [club for club in clubs if club["club_id"] == args.club]
        if not clubs:
            print(f"[error] Unknown club_id: {args.club}")
            return 1

    if not clubs:
        print("[warn] Nothing to collect.")
        return 0

    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    attempts = 0
    successes = 0

    for index, club in enumerate(clubs):
        attempts += 1
        if collect_one(
            session,
            club,
            output_dir,
            args.base_url,
            args.timeout_seconds,
            args.overwrite,
        ):
            successes += 1

        is_last = index == len(clubs) - 1
        if not is_last and args.request_delay_seconds > 0:
            time.sleep(args.request_delay_seconds)

    print(f"[done] Completed {attempts} requests with {successes} successful HTTP responses.")
    return 0 if successes == attempts else 1


if __name__ == "__main__":
    sys.exit(main())
