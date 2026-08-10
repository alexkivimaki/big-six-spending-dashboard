#!/usr/bin/env python3

"""Check whether a CSV file contains the required columns for a named table."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


REQUIRED_COLUMNS = {
    "club_season_finances": [
        "club_id",
        "club_name",
        "season",
        "gross_transfer_spend_eur",
        "transfer_income_eur",
        "net_transfer_spend_eur",
        "estimated_wages_eur",
        "raw_player_cost_eur",
        "source_id",
        "confidence_level",
        "notes",
    ],
    "club_season_performance": [
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
        "source_id",
        "notes",
    ],
}


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "Usage: python3 scripts/validate/check_required_columns.py <csv_path> <table_name>",
            file=sys.stderr,
        )
        return 1

    csv_path = Path(sys.argv[1])
    table_name = sys.argv[2]

    if table_name not in REQUIRED_COLUMNS:
        print(f"Unknown table name: {table_name}", file=sys.stderr)
        print(f"Supported tables: {', '.join(sorted(REQUIRED_COLUMNS))}", file=sys.stderr)
        return 1

    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}", file=sys.stderr)
        return 1

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        actual_columns = reader.fieldnames or []

    missing_columns = [column for column in REQUIRED_COLUMNS[table_name] if column not in actual_columns]

    if missing_columns:
        print(f"{csv_path} is missing required columns for {table_name}:")
        for column in missing_columns:
            print(f"- {column}")
        return 1

    print(f"{csv_path} contains all required columns for {table_name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
