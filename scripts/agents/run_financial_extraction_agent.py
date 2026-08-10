#!/usr/bin/env python3

"""Create financial extraction tasks for downloaded club statements."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


EXPECTED_OUTPUT_SCHEMA = {
    "club_id": "",
    "club_name": "",
    "season": "",
    "financial_year_end": "",
    "currency_original": "",
    "units_original": "",
    "total_revenue_original": None,
    "matchday_revenue_original": None,
    "broadcast_revenue_original": None,
    "commercial_revenue_original": None,
    "other_revenue_original": None,
    "women_team_revenue_original": None,
    "excluded_player_trading_revenue_original": None,
    "staff_costs_original": None,
    "net_debt_original": None,
    "player_amortisation_original": None,
    "profit_on_player_sales_original": None,
    "profit_loss_before_tax_original": None,
    "total_revenue_eur": None,
    "matchday_revenue_eur": None,
    "broadcast_revenue_eur": None,
    "commercial_revenue_eur": None,
    "other_revenue_eur": None,
    "net_debt_eur": None,
    "profit_loss_before_tax_eur": None,
    "exchange_rate_used": None,
    "exchange_rate_source": "",
    "revenue_sum_check_original": None,
    "revenue_sum_difference_original": None,
    "pages_used": [],
    "evidence": [],
    "classification_notes": "",
    "women_team_treatment_notes": "",
    "non_football_revenue_notes": "",
    "confidence_level": "",
    "requires_manual_review": True,
    "notes": "",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/financial_statements")
    parser.add_argument("--output", default="data/raw/ai_agents/financial_extraction_outputs/tasks")
    parser.add_argument("--prompt", default="agents/financial_extraction_agent_prompt.md")
    parser.add_argument("--season-from", default="")
    parser.add_argument("--season-to", default="")
    return parser.parse_args()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def season_from_filename(name: str) -> str:
    for part in name.split("_"):
        if len(part) == 4 and part.isdigit():
            continue
    return ""


def season_slug_to_display(slug: str) -> str:
    return slug.replace("_", "/")


def season_start_year(season: str) -> int:
    return int(season.split("/", 1)[0])


def main() -> int:
    args = parse_args()
    input_root = Path(args.input)
    output_dir = Path(args.output)
    prompt_path = Path(args.prompt)
    season_from_year = season_start_year(args.season_from) if args.season_from else None
    season_to_year = season_start_year(args.season_to) if args.season_to else None

    tasks_written = 0
    for club_dir in sorted(path for path in input_root.iterdir() if path.is_dir()):
        for statement_path in sorted(club_dir.iterdir()):
            if statement_path.name.startswith(".") or statement_path.suffix == ".json":
                continue
            meta_path = statement_path.with_suffix(statement_path.suffix + ".meta.json")
            season = ""
            source_url = ""
            if meta_path.exists():
                metadata = json.loads(meta_path.read_text(encoding="utf-8"))
                season = metadata.get("season", "")
                source_url = metadata.get("source_url", "")
            if not season:
                season = season_slug_to_display(statement_path.stem.split("_", 2)[0])
            if season:
                start_year = season_start_year(season)
                if season_from_year is not None and start_year < season_from_year:
                    continue
                if season_to_year is not None and start_year > season_to_year:
                    continue

            payload = {
                "task_type": "financial_extraction",
                "club_id": club_dir.name,
                "season": season,
                "local_file_path": str(statement_path),
                "source_url": source_url,
                "prompt_path": str(prompt_path),
                "expected_output_schema": EXPECTED_OUTPUT_SCHEMA,
                "save_output_to": f"data/raw/ai_agents/financial_extraction_outputs/{club_dir.name}_{season.replace('/', '_')}_financial_extraction_output.json",
            }
            write_json(output_dir / f"{club_dir.name}_{season.replace('/', '_')}_financial_extraction_task.json", payload)
            tasks_written += 1

    example_payload = {
        "club_id": "arsenal",
        "club_name": "Arsenal",
        "season": "2023/24",
        "financial_year_end": "2024-05-31",
        "currency_original": "GBP",
        "units_original": "millions",
        "total_revenue_original": None,
        "matchday_revenue_original": None,
        "broadcast_revenue_original": None,
        "commercial_revenue_original": None,
        "other_revenue_original": None,
        "women_team_revenue_original": None,
        "excluded_player_trading_revenue_original": None,
        "staff_costs_original": None,
        "net_debt_original": None,
        "player_amortisation_original": None,
        "profit_on_player_sales_original": None,
        "profit_loss_before_tax_original": None,
        "total_revenue_eur": None,
        "matchday_revenue_eur": None,
        "broadcast_revenue_eur": None,
        "commercial_revenue_eur": None,
        "other_revenue_eur": None,
        "net_debt_eur": None,
        "profit_loss_before_tax_eur": None,
        "exchange_rate_used": None,
        "exchange_rate_source": "",
        "revenue_sum_check_original": None,
        "revenue_sum_difference_original": None,
        "pages_used": [],
        "evidence": [],
        "classification_notes": "",
        "women_team_treatment_notes": "",
        "non_football_revenue_notes": "",
        "confidence_level": "example",
        "requires_manual_review": True,
        "notes": "Example structure only; values must be verified from source document."
    }
    write_json(Path("data/raw/ai_agents/financial_extraction_outputs/example_output.json"), example_payload)

    print(f"[saved] Wrote {tasks_written} financial-extraction tasks to {output_dir}")
    if args.season_from or args.season_to:
        print(f"[report] Season range filter: {args.season_from or 'min'} to {args.season_to or 'max'}")
    print("[next] Run these tasks through your chosen AI-agent tool and save strict JSON outputs in data/raw/ai_agents/financial_extraction_outputs/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
