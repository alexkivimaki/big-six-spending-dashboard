#!/usr/bin/env python3

"""Combine structured AI-agent JSON outputs into clean CSV files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


DATASETS = {
    "wages": {
        "input_dir": "data/raw/ai_agents/wages",
        "output": "data/clean/ai_agents/club_season_wages_clean.csv",
        "columns": [
            "club_id",
            "club_name",
            "season",
            "estimated_player_wages_eur",
            "estimated_player_wages_original",
            "estimated_player_wages_original_currency",
            "estimated_player_wages_original_unit",
            "weekly_wages_original",
            "official_staff_costs_eur",
            "currency_original",
            "units_original",
            "conversion_rate_to_eur",
            "exchange_rate_source",
            "source_name",
            "source_url",
            "date_accessed",
            "evidence",
            "confidence_level",
            "requires_manual_review",
            "notes",
        ],
        "required": ["club_id", "club_name", "season"],
    },
    "club_finances": {
        "input_dir": "data/raw/ai_agents/club_finances",
        "output": "data/clean/ai_agents/club_season_finances_clean.csv",
        "columns": [
            "club_id",
            "club_name",
            "season",
            "revenue_eur",
            "matchday_revenue_eur",
            "broadcasting_revenue_eur",
            "commercial_revenue_eur",
            "official_staff_costs_eur",
            "operating_profit_loss_eur",
            "profit_loss_before_tax_eur",
            "net_debt_eur",
            "player_amortisation_eur",
            "profit_on_player_sales_eur",
            "currency_original",
            "conversion_rate_to_eur",
            "source_name",
            "source_url",
            "date_accessed",
            "evidence",
            "confidence_level",
            "notes",
        ],
        "required": ["club_id", "club_name", "season"],
    },
    "performance": {
        "input_dir": "data/raw/ai_agents/performance",
        "output": "data/clean/ai_agents/club_season_performance_clean.csv",
        "columns": [
            "club_id",
            "club_name",
            "season",
            "league_position",
            "points",
            "wins",
            "draws",
            "losses",
            "goals_for",
            "goals_against",
            "goal_difference",
            "trophies",
            "champions_league_qualified",
            "source_name",
            "source_url",
            "date_accessed",
            "evidence",
            "confidence_level",
            "notes",
        ],
        "required": ["club_id", "club_name", "season"],
    },
    "managers": {
        "input_dir": "data/raw/ai_agents/managers",
        "output": "data/clean/ai_agents/managers_clean.csv",
        "columns": [
            "manager_id",
            "manager_name",
            "club_id",
            "club_name",
            "start_date",
            "end_date",
            "source_name",
            "source_url",
            "date_accessed",
            "evidence",
            "confidence_level",
            "notes",
        ],
        "required": ["manager_name", "club_id", "club_name"],
    },
    "ownership": {
        "input_dir": "data/raw/ai_agents/ownership",
        "output": "data/clean/ai_agents/ownership_eras_clean.csv",
        "columns": [
            "club_id",
            "club_name",
            "ownership_era",
            "owner_or_group_name",
            "start_date",
            "end_date",
            "source_name",
            "source_url",
            "date_accessed",
            "evidence",
            "confidence_level",
            "notes",
        ],
        "required": ["club_id", "club_name", "ownership_era"],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args()


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def ensure_records(payload):
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def normalize_record(record: dict, columns: list[str], required: list[str], source_path: Path) -> dict:
    row = {column: record.get(column, None) for column in columns}
    notes = row.get("notes") or ""

    missing = [field for field in required if row.get(field) in ("", None)]
    if missing:
        suffix = f"Missing required fields in agent output: {', '.join(missing)}."
        notes = f"{notes} {suffix}".strip()

    if not row.get("source_name"):
        notes = f"{notes} Source name missing in agent output.".strip()
    if not row.get("source_url"):
        notes = f"{notes} Source URL missing in agent output.".strip()

    row["notes"] = notes
    row["_source_file"] = source_path.name
    return row


def process_dataset(name: str, settings: dict) -> None:
    input_dir = Path(settings["input_dir"])
    output_path = Path(settings["output"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    json_files = sorted(
        path
        for path in input_dir.glob("*.json")
        if path.name != "example_output.json"
    )

    for json_path in json_files:
        payload = load_json(json_path)
        records = ensure_records(payload)
        if not records:
            print(f"[warn] {json_path} did not contain a JSON object or list of objects.")
            continue

        for record in records:
            rows.append(
                normalize_record(record, settings["columns"], settings["required"], json_path)
            )

    output_columns = settings["columns"] + ["_source_file"]
    dataframe = pd.DataFrame(rows, columns=output_columns)
    dataframe.to_csv(output_path, index=False)
    print(f"[saved] {name}: {output_path} ({len(dataframe)} rows)")


def main() -> int:
    parse_args()
    for name, settings in DATASETS.items():
        process_dataset(name, settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
