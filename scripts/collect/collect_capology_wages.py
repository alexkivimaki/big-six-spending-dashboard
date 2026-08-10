#!/usr/bin/env python3

"""Collect Big Six club-season wage estimates from Capology season salary pages."""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import requests


META_DESCRIPTION_RE = re.compile(r'<meta name="description" content="(.*?)"', re.IGNORECASE)
DESCRIPTION_RE = re.compile(
    r"Estimated Gross Fixed Salaries for the (?P<season>\d{4}-\d{4}) Season (?:was|is) £(?P<annual>[0-9,]+), or £(?P<weekly>[0-9,]+) per week",
    re.IGNORECASE,
)

CLUB_SLUGS = {
    "arsenal": "arsenal",
    "chelsea": "chelsea",
    "liverpool": "liverpool",
    "manchester_city": "manchester-city",
    "manchester_united": "manchester-united",
    "tottenham_hotspur": "tottenham",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clubs", default="config/big_six_clubs.json")
    parser.add_argument("--years", default="config/financial_years.json")
    parser.add_argument("--output", default="data/raw/ai_agents/wages")
    parser.add_argument("--season-from", default="2011/12")
    parser.add_argument("--season-to", default="2024/25")
    parser.add_argument("--request-delay-seconds", type=float, default=1.0)
    return parser.parse_args()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def season_start_year(season: str) -> int:
    return int(season.split("/", 1)[0])


def season_to_capology_slug(season: str) -> str:
    start_year = season_start_year(season)
    return f"{start_year}-{start_year + 1}"


def build_output_payload(
    club_id: str,
    club_name: str,
    season: str,
    source_url: str,
    annual_gbp: int | None,
    weekly_gbp: int | None,
    notes: str,
    confidence_level: str,
) -> dict:
    evidence = []
    if annual_gbp is not None:
        evidence.append(
            {
                "field": "estimated_player_wages_eur",
                "value_original": annual_gbp,
                "unit_original": "GBP gross annual base wages",
                "page_or_location": "meta_description",
                "evidence_text": f"Estimated Gross Fixed Salaries for the {season_to_capology_slug(season)} Season was £{annual_gbp:,}, or £{weekly_gbp:,} per week, not including bonuses.",
            }
        )

    payload = {
        "club_id": club_id,
        "club_name": club_name,
        "season": season,
        "estimated_player_wages_eur": None,
        "estimated_player_wages_original": annual_gbp,
        "estimated_player_wages_original_currency": "GBP" if annual_gbp is not None else "",
        "estimated_player_wages_original_unit": "gross annual base wages" if annual_gbp is not None else "",
        "weekly_wages_original": weekly_gbp,
        "source_name": "Capology",
        "source_url": source_url,
        "date_accessed": time.strftime("%Y-%m-%d"),
        "currency_original": "GBP" if annual_gbp is not None else "",
        "units_original": "full pounds" if annual_gbp is not None else "",
        "conversion_rate_to_eur": None,
        "exchange_rate_source": "",
        "evidence": evidence,
        "confidence_level": confidence_level,
        "requires_manual_review": True,
        "notes": notes,
    }
    return payload


def extract_wage_values(html: str) -> tuple[int | None, int | None]:
    description_match = META_DESCRIPTION_RE.search(html)
    description = description_match.group(1) if description_match else html
    wage_match = DESCRIPTION_RE.search(description)
    if not wage_match:
        return None, None
    annual_gbp = int(wage_match.group("annual").replace(",", ""))
    weekly_gbp = int(wage_match.group("weekly").replace(",", ""))
    return annual_gbp, weekly_gbp


def main() -> int:
    args = parse_args()
    clubs = load_json(Path(args.clubs))
    years = load_json(Path(args.years))
    output_dir = Path(args.output)

    session = requests.Session()
    session.headers.update({"User-Agent": "FootballFinanceDashboard/0.1 personal research project"})

    season_from_year = season_start_year(args.season_from)
    season_to_year = season_start_year(args.season_to)

    written = 0
    supported = 0
    unsupported = 0

    for club in clubs:
        club_id = club["club_id"]
        club_name = club["club_name"]
        capology_slug = CLUB_SLUGS.get(club_id)
        if not capology_slug:
            print(f"[warn] No Capology slug mapping for {club_id}; skipping.")
            continue

        for year in years:
            season = year["season"]
            start_year = season_start_year(season)
            if start_year < season_from_year or start_year > season_to_year:
                continue

            capology_season = season_to_capology_slug(season)
            source_url = f"https://www.capology.com/club/{capology_slug}/salaries/{capology_season}/"
            output_path = output_dir / f"{club_id}_{season.replace('/', '_')}_wage_output.json"

            annual_gbp = None
            weekly_gbp = None
            notes = (
                "Capology wage estimates are not official figures. Values represent estimated gross fixed player salaries and exclude bonuses. "
                "EUR conversion is pending a project-level FX methodology, so the EUR field remains null for now."
            )
            confidence_level = "medium"

            response = session.get(source_url, timeout=30)
            annual_gbp, weekly_gbp = extract_wage_values(response.text)
            if response.status_code == 200 and annual_gbp is not None and weekly_gbp is not None:
                supported += 1
                print(f"[saved] {club_id} {season} from Capology ({annual_gbp:,} GBP)")
            else:
                unsupported += 1
                notes = (
                    f"No structured Capology season salary value was available for {season} at {source_url}. "
                    "This likely reflects missing historical coverage for that season. "
                    "EUR conversion is pending a project-level FX methodology."
                )
                confidence_level = "low"
                print(f"[warn] {club_id} {season} unsupported or unavailable on Capology season page.")

            payload = build_output_payload(
                club_id=club_id,
                club_name=club_name,
                season=season,
                source_url=source_url,
                annual_gbp=annual_gbp,
                weekly_gbp=weekly_gbp,
                notes=notes,
                confidence_level=confidence_level,
            )
            write_json(output_path, payload)
            written += 1
            time.sleep(args.request_delay_seconds)

    print(f"[done] Wrote {written} wage output JSON files to {output_dir}")
    print(f"[report] Supported seasons: {supported}")
    print(f"[report] Unsupported or missing seasons: {unsupported}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
