#!/usr/bin/env python3

"""Create club-season player wage collection tasks for manual AI-agent use."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


EXPECTED_OUTPUT_SCHEMA = {
    "club_id": "",
    "club_name": "",
    "season": "",
    "estimated_player_wages_eur": None,
    "source_name": "",
    "source_url": "",
    "date_accessed": "",
    "currency_original": "",
    "units_original": "",
    "conversion_rate_to_eur": None,
    "exchange_rate_source": "",
    "evidence": [],
    "confidence_level": "",
    "requires_manual_review": True,
    "notes": "",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clubs", default="config/big_six_clubs.json")
    parser.add_argument("--years", default="config/financial_years.json")
    parser.add_argument("--output", default="data/raw/ai_agents/wages/tasks")
    parser.add_argument("--prompt", default="agents/wage_data_agent_prompt.md")
    parser.add_argument("--season-from", default="2011/12")
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
                "task_type": "wage_collection",
                "club_id": club["club_id"],
                "club_name": club["club_name"],
                "season": season,
                "target_financial_year_end_range": {
                    "start": year["financial_year_end_start"],
                    "end": year["financial_year_end_end"],
                    "notes": year["notes"],
                },
                "preferred_sources": [
                    "licensed salary database or clearly documented wage-estimate source",
                    "official annual report note if player wages are directly disclosed",
                    "high-quality football finance reporting for cross-checking only",
                ],
                "prompt_path": str(prompt_path),
                "expected_output_schema": EXPECTED_OUTPUT_SCHEMA,
                "save_output_to": f"data/raw/ai_agents/wages/{club['club_id']}_{season_slug(season)}_wage_output.json",
            }
            write_json(output_dir / f"{club['club_id']}_{season_slug(season)}_wage_task.json", payload)
            tasks_written += 1

    example_payload = {
        "club_id": "arsenal",
        "club_name": "Arsenal",
        "season": "2023/24",
        "estimated_player_wages_eur": None,
        "source_name": "Example only",
        "source_url": "",
        "date_accessed": "2026-05-05",
        "currency_original": "GBP",
        "units_original": "full pounds",
        "conversion_rate_to_eur": None,
        "exchange_rate_source": "",
        "evidence": [],
        "confidence_level": "example",
        "requires_manual_review": True,
        "notes": "Example structure only; values must be verified from a trusted wage source before use.",
    }
    write_json(Path("data/raw/ai_agents/wages/example_output.json"), example_payload)

    print(f"[saved] Wrote {tasks_written} wage-collection tasks to {output_dir}")
    print(f"[report] Season range: {args.season_from} to {args.season_to}")
    print("[next] Run these tasks through your chosen AI-agent tool and save strict JSON outputs in data/raw/ai_agents/wages/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
