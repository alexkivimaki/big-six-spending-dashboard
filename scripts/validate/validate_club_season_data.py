#!/usr/bin/env python3

"""Validate the combined club-season dashboard dataset when present."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "club_id",
    "club_name",
    "season",
    "gross_transfer_spend_eur",
    "transfer_income_eur",
    "net_transfer_spend_eur",
    "estimated_player_wages_eur",
    "raw_player_cost_eur",
    "league_position",
    "points",
    "cost_per_point",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/final/club_season_dashboard.csv")
    parser.add_argument("--clubs", default="config/clubs.json")
    parser.add_argument("--seasons", default="config/seasons.json")
    return parser.parse_args()


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def numeric_equal(left, right, tolerance: float = 1e-6) -> bool:
    if pd.isna(left) or pd.isna(right):
        return True
    return math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance)


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"[warn] Combined dashboard dataset not found yet: {input_path}")
        return 0

    dataframe = pd.read_csv(input_path)
    issues: list[str] = []

    missing = sorted(REQUIRED_COLUMNS - set(dataframe.columns))
    if missing:
        issues.append(f"Missing required columns: {', '.join(missing)}")

    valid_seasons = {item["season"] for item in load_json(Path(args.seasons))}
    valid_club_ids = {item["club_id"] for item in load_json(Path(args.clubs))}

    if "season" in dataframe.columns:
        invalid_seasons = sorted(set(dataframe["season"].dropna()) - valid_seasons)
        if invalid_seasons:
            issues.append(f"Invalid seasons: {', '.join(invalid_seasons)}")

    if "club_id" in dataframe.columns:
        invalid_club_ids = sorted(set(dataframe["club_id"].dropna()) - valid_club_ids)
        if invalid_club_ids:
            issues.append(f"Invalid club_ids: {', '.join(invalid_club_ids)}")

    numeric_columns = [
        "gross_transfer_spend_eur",
        "transfer_income_eur",
        "net_transfer_spend_eur",
        "estimated_player_wages_eur",
        "raw_player_cost_eur",
        "league_position",
        "points",
        "cost_per_point",
    ]
    for column in numeric_columns:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    for index, row in dataframe.iterrows():
        gross = row.get("gross_transfer_spend_eur")
        income = row.get("transfer_income_eur")
        net = row.get("net_transfer_spend_eur")
        wages = row.get("estimated_player_wages_eur")
        raw_cost = row.get("raw_player_cost_eur")
        points = row.get("points")
        cost_per_point = row.get("cost_per_point")

        if pd.notna(gross) and pd.notna(income) and pd.notna(net):
            if not numeric_equal(net, gross - income):
                issues.append(f"Row {index}: net_transfer_spend_eur formula check failed.")

        if pd.notna(net) and pd.notna(wages) and pd.notna(raw_cost):
            if not numeric_equal(raw_cost, net + wages):
                issues.append(f"Row {index}: raw_player_cost_eur formula check failed.")

        if pd.notna(raw_cost) and pd.notna(points) and points not in (0, 0.0) and pd.notna(cost_per_point):
            if not numeric_equal(cost_per_point, raw_cost / points):
                issues.append(f"Row {index}: cost_per_point formula check failed.")

    print("[report] Club-season dashboard validation")
    print(f"[report] rows: {len(dataframe)}")

    if issues:
        for message in issues:
            print(f"[invalid] {message}")
        return 1

    print("[valid] Club-season dashboard dataset passed validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
