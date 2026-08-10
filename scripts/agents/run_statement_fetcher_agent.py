#!/usr/bin/env python3

"""Create club-season financial statement search tasks for manual AI-agent use."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clubs", default="config/big_six_clubs.json")
    parser.add_argument("--years", default="config/financial_years.json")
    parser.add_argument("--output", default="data/raw/ai_agents/statement_fetcher_outputs/tasks")
    parser.add_argument("--prompt", default="agents/statement_fetcher_agent_prompt.md")
    parser.add_argument("--season-from", default="2021/22")
    parser.add_argument("--season-to", default="2024/25")
    return parser.parse_args()


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def season_slug(season: str) -> str:
    return season.replace("/", "_")


def season_start_year(season: str) -> int:
    return int(season.split("/", 1)[0])


def main() -> int:
    args = parse_args()
    clubs = load_json(Path(args.clubs))
    years = load_json(Path(args.years))
    output_dir = Path(args.output)
    prompt_path = Path(args.prompt)
    season_from_year = season_start_year(args.season_from)
    season_to_year = season_start_year(args.season_to)

    tasks_written = 0
    for club in clubs:
        for year in years:
            season = year["season"]
            start_year = season_start_year(season)
            if start_year < season_from_year or start_year > season_to_year:
                continue
            payload = {
                "task_type": "statement_fetcher",
                "club_id": club["club_id"],
                "club_name": club["club_name"],
                "season": season,
                "target_financial_year_end_range": {
                    "start": year["financial_year_end_start"],
                    "end": year["financial_year_end_end"],
                    "notes": year["notes"],
                },
                "preferred_sources": [
                    "official club annual report page",
                    "investor relations page",
                    "Companies House filing",
                    "SEC filing if applicable",
                    "other official registry or club source",
                ],
                "company_or_group_notes": club["company_or_group_notes"],
                "official_financial_reports_url": club["official_financial_reports_url"],
                "companies_house_search_name": club["companies_house_search_name"],
                "currency_common": club["currency_common"],
                "prompt_path": str(prompt_path),
                "save_output_to": f"data/raw/ai_agents/statement_fetcher_outputs/{club['club_id']}_{season_slug(season)}_statement_fetcher_output.json",
            }
            write_json(output_dir / f"{club['club_id']}_{season_slug(season)}_statement_fetcher_task.json", payload)
            tasks_written += 1

    example_payload = {
        "club_id": "arsenal",
        "club_name": "Arsenal",
        "season": "2023/24",
        "financial_year_end": "2024-05-31",
        "report_title": "Arsenal Holdings Limited annual report and financial statements 2024",
        "report_type": "annual_report",
        "source_name": "Official club financial results page",
        "source_url": "https://www.arsenal.com/the-club/corporate-info/arsenal-holdings-financial-results",
        "download_url": "https://example.com/arsenal-2024-annual-report.pdf",
        "file_type": "pdf",
        "date_accessed": "2026-04-28",
        "is_official_source": True,
        "company_or_group_name": "Arsenal Holdings Limited",
        "company_number_or_registry_id": "",
        "local_file_suggested_name": "2023_24_arsenal_holdings_limited_annual_report_2024.pdf",
        "confidence_level": "example",
        "notes": "Example only, verify before use."
    }
    write_json(Path("data/raw/ai_agents/statement_fetcher_outputs/example_output.json"), example_payload)

    print(f"[saved] Wrote {tasks_written} statement-fetcher tasks to {output_dir}")
    print(f"[report] Season range: {args.season_from} to {args.season_to}")
    print("[next] Run these tasks through your chosen AI-agent tool and save strict JSON outputs in data/raw/ai_agents/statement_fetcher_outputs/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
