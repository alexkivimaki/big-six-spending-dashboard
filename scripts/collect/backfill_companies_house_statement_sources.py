#!/usr/bin/env python3

"""Backfill statement finder outputs from Companies House filing history pages."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


USER_AGENT = "FootballFinanceDashboard/0.1 personal research project"

COMPANY_NUMBERS = {
    "arsenal": "04250459",
    "chelsea": "02536231",
    "liverpool": "00035668",
    "manchester_city": "00040946",
    "manchester_united": "00095489",
    "tottenham_hotspur": "01706358",
}

FILING_HISTORY_BASE = "https://find-and-update.company-information.service.gov.uk/company/{company_number}/filing-history"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clubs", default="config/big_six_clubs.json")
    parser.add_argument("--years", default="config/financial_years.json")
    parser.add_argument("--output", default="data/raw/ai_agents/statement_fetcher_outputs")
    parser.add_argument("--season-from", default="2008/09")
    parser.add_argument("--season-to", default="2020/21")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def season_start_year(season: str) -> int:
    return int(season.split("/", 1)[0])


def season_slug(season: str) -> str:
    return season.replace("/", "_")


def safe_slug(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "_" for char in value)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "report"


def fetch_filing_history(company_number: str, timeout: int) -> list[dict]:
    next_url = FILING_HISTORY_BASE.format(company_number=company_number)
    rows: list[dict] = []
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    while next_url:
        response = session.get(next_url, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table")
        if table is None:
            break

        for tr in table.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) < 3:
                continue
            date_filed = cells[0].get_text(" ", strip=True)
            filing_type = cells[1].get_text(" ", strip=True)
            description = cells[2].get_text(" ", strip=True)
            link = tr.find("a", href=True)
            download_url = urljoin(response.url, link["href"]) if link else ""
            rows.append(
                {
                    "date_filed": date_filed,
                    "filing_type": filing_type,
                    "description": description,
                    "download_url": download_url,
                }
            )

        next_url = None
        for link in soup.find_all("a", href=True):
            link_text = " ".join(link.stripped_strings)
            if re.search(r"next page", link_text, re.I):
                next_url = urljoin(response.url, link["href"])
                break

    return rows


def choose_filing_for_year(filings: list[dict], year_end: int) -> dict | None:
    target = str(year_end)
    for filing in filings:
        description = filing["description"]
        if filing["filing_type"] != "AA":
            continue
        if f"made up to 31 May {target}" in description or f"made up to 30 June {target}" in description:
            return filing
    return None


def build_output_record(club: dict, season: str, filing: dict) -> dict:
    company_number = COMPANY_NUMBERS[club["club_id"]]
    start_year = season_start_year(season)
    end_year = start_year + 1
    month_day = "31 May" if club["club_id"] in {"arsenal", "liverpool"} else "30 June"
    report_type = "accounts_filing"
    company_name = club["companies_house_search_name"]
    notes = (
        f"Official Companies House filing for {company_name}. "
        "Backfilled automatically from filing history based on the financial year-end date."
    )

    return {
        "club_id": club["club_id"],
        "club_name": club["club_name"],
        "season": season,
        "financial_year_end": f"{end_year}-05-31" if month_day == "31 May" else f"{end_year}-06-30",
        "report_title": filing["description"],
        "report_type": report_type,
        "source_name": "Companies House",
        "source_url": FILING_HISTORY_BASE.format(company_number=company_number),
        "download_url": filing["download_url"],
        "file_type": "pdf",
        "date_accessed": "2026-04-28",
        "is_official_source": True,
        "company_or_group_name": company_name,
        "company_number_or_registry_id": company_number,
        "local_file_suggested_name": f"{season_slug(season)}_{safe_slug(filing['description'])}.pdf",
        "confidence_level": "high",
        "notes": notes,
    }


def write_json(path: Path, payload: dict, overwrite: bool) -> bool:
    if path.exists() and not overwrite:
        return False
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return True


def main() -> int:
    args = parse_args()
    clubs = load_json(Path(args.clubs))
    years = load_json(Path(args.years))
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    season_from_year = season_start_year(args.season_from)
    season_to_year = season_start_year(args.season_to)
    target_years = [year for year in years if season_from_year <= season_start_year(year["season"]) <= season_to_year]

    written = 0
    missing: list[str] = []

    for club in clubs:
        club_id = club["club_id"]
        company_number = COMPANY_NUMBERS.get(club_id)
        if not company_number:
            missing.append(f"{club_id}: no configured Companies House company number")
            continue

        filings = fetch_filing_history(company_number, args.timeout)
        for year in target_years:
            season = year["season"]
            if season_start_year(season) >= 2021:
                continue
            filing = choose_filing_for_year(filings, season_start_year(season) + 1)
            if filing is None:
                missing.append(f"{club_id} {season}: no matching AA filing found")
                continue

            output_path = output_dir / f"{club_id}_{season_slug(season)}_statement_fetcher_output.json"
            record = build_output_record(club, season, filing)
            if write_json(output_path, record, args.overwrite):
                written += 1
                print(f"[saved] {output_path}")

    print(f"[done] Wrote {written} backfilled statement source records.")
    if missing:
        print("[warn] Missing matches:")
        for item in missing:
            print(f"  - {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
