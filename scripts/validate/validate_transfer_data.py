#!/usr/bin/env python3

"""Validate cleaned Transfermarkt club-page transfer datasets."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import pandas as pd


CLUB_TRANSFER_REQUIRED = {
    "league_key",
    "league_name",
    "club_id",
    "club_name",
    "season",
    "season_start_year",
    "window",
    "gross_transfer_spend_eur",
    "transfer_income_eur",
    "net_transfer_spend_eur",
    "incoming_transfer_count",
    "outgoing_transfer_count",
    "source_name",
    "source_endpoint",
    "collected_at_utc",
    "confidence_level",
    "notes",
}

TRANSFER_ROW_REQUIRED = {
    "league_key",
    "league_name",
    "player_name",
    "season",
    "season_start_year",
    "direction",
    "club_id",
    "club_name",
    "age",
    "position",
    "other_club_name",
    "other_competition",
    "fee_text",
    "fee_eur",
    "source_name",
    "source_endpoint",
    "collected_at_utc",
    "confidence_level",
    "notes",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--club-transfers",
        default="data/clean/transfermarkt/club_season_transfers_clean.csv",
    )
    parser.add_argument(
        "--transfer-rows",
        default="data/clean/transfermarkt/club_transfer_rows_clean.csv",
    )
    parser.add_argument("--clubs", default="config/clubs.json")
    parser.add_argument("--seasons", default="config/seasons.json")
    return parser.parse_args()


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def add_issue(issues: list[str], message: str) -> None:
    issues.append(message)


def validate_required_columns(dataframe: pd.DataFrame, required: set[str], label: str, issues: list[str]) -> None:
    missing = sorted(required - set(dataframe.columns))
    if missing:
        add_issue(issues, f"{label}: missing required columns: {', '.join(missing)}")


def numeric_equal(left, right, tolerance: float = 1e-6) -> bool:
    if pd.isna(left) or pd.isna(right):
        return True
    return math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance)


def main() -> int:
    args = parse_args()
    issues: list[str] = []
    warnings: list[str] = []

    valid_seasons = {item["season"] for item in load_json(Path(args.seasons))}
    valid_club_ids = {item["club_id"] for item in load_json(Path(args.clubs))}

    club_path = Path(args.club_transfers)
    transfer_rows_path = Path(args.transfer_rows)

    if not club_path.exists():
        add_issue(issues, f"Missing club transfer file: {club_path}")
    if not transfer_rows_path.exists():
        add_issue(issues, f"Missing transfer rows file: {transfer_rows_path}")

    if not club_path.exists() or not transfer_rows_path.exists():
        for message in issues:
            print(f"[invalid] {message}")
        return 1

    club_df = pd.read_csv(club_path)
    transfer_rows_df = pd.read_csv(transfer_rows_path)

    validate_required_columns(club_df, CLUB_TRANSFER_REQUIRED, "club_season_transfers_clean", issues)
    validate_required_columns(transfer_rows_df, TRANSFER_ROW_REQUIRED, "club_transfer_rows_clean", issues)

    if "season" in club_df.columns:
        invalid_club_seasons = sorted(set(club_df["season"].dropna()) - valid_seasons)
        if invalid_club_seasons:
            add_issue(issues, f"club_season_transfers_clean: invalid seasons: {', '.join(invalid_club_seasons)}")

    if "club_id" in club_df.columns:
        invalid_club_ids = sorted(set(club_df["club_id"].dropna()) - valid_club_ids)
        if invalid_club_ids:
            add_issue(issues, f"club_season_transfers_clean: invalid club_ids: {', '.join(invalid_club_ids)}")

    numeric_columns = [
        "gross_transfer_spend_eur",
        "transfer_income_eur",
        "net_transfer_spend_eur",
    ]
    for column in numeric_columns:
        if column in club_df.columns:
            club_df[column] = pd.to_numeric(club_df[column], errors="coerce")

    for index, row in club_df.iterrows():
        gross = row.get("gross_transfer_spend_eur")
        income = row.get("transfer_income_eur")
        net = row.get("net_transfer_spend_eur")
        if pd.notna(gross) and pd.notna(income) and pd.notna(net):
            expected = gross - income
            if not numeric_equal(net, expected):
                add_issue(
                    issues,
                    f"club_season_transfers_clean row {index}: net_transfer_spend_eur does not equal gross_transfer_spend_eur - transfer_income_eur",
                )

    if "season" in transfer_rows_df.columns:
        transfer_row_seasons = {str(value) for value in transfer_rows_df["season"].dropna()}
        malformed_transfer_row_seasons = sorted(
            season for season in transfer_row_seasons if not re.fullmatch(r"\d{4}/\d{2}", season)
        )
        if malformed_transfer_row_seasons:
            add_issue(
                issues,
                f"club_transfer_rows_clean: malformed season labels: {', '.join(malformed_transfer_row_seasons)}",
            )

        out_of_range_transfer_row_seasons = sorted(transfer_row_seasons - valid_seasons)
        if out_of_range_transfer_row_seasons:
            add_issue(
                issues,
                "club_transfer_rows_clean contains seasons outside the configured tracked range: "
                + ", ".join(out_of_range_transfer_row_seasons),
            )

    if "club_id" in transfer_rows_df.columns:
        invalid_transfer_row_club_ids = sorted(set(transfer_rows_df["club_id"].dropna()) - valid_club_ids)
        if invalid_transfer_row_club_ids:
            add_issue(
                issues,
                f"club_transfer_rows_clean: invalid club_ids: {', '.join(invalid_transfer_row_club_ids)}",
            )

    if "direction" in transfer_rows_df.columns:
        invalid_directions = sorted(
            {
                str(value)
                for value in transfer_rows_df["direction"].dropna()
                if str(value) not in {"arrival", "departure"}
            }
        )
        if invalid_directions:
            add_issue(
                issues,
                f"club_transfer_rows_clean: invalid direction values: {', '.join(invalid_directions)}",
            )

    if {"league_key", "club_id", "season", "direction"}.issubset(transfer_rows_df.columns):
        grouped = (
            transfer_rows_df.assign(fee_eur=pd.to_numeric(transfer_rows_df["fee_eur"], errors="coerce"))
            .groupby(["league_key", "club_id", "season", "direction"], dropna=False)
            .agg(
                fee_sum=("fee_eur", "sum"),
                transfer_count=("direction", "count"),
            )
            .reset_index()
        )

        for _, summary_row in club_df.iterrows():
            league_key = summary_row.get("league_key")
            club_id = summary_row.get("club_id")
            season = summary_row.get("season")

            arrivals = grouped[
                (grouped["league_key"] == league_key)
                & (grouped["club_id"] == club_id)
                & (grouped["season"] == season)
                & (grouped["direction"] == "arrival")
            ]
            departures = grouped[
                (grouped["league_key"] == league_key)
                & (grouped["club_id"] == club_id)
                & (grouped["season"] == season)
                & (grouped["direction"] == "departure")
            ]

            if not arrivals.empty:
                arrival_sum = float(arrivals.iloc[0]["fee_sum"])
                arrival_count = int(arrivals.iloc[0]["transfer_count"])
                gross = summary_row.get("gross_transfer_spend_eur")
                incoming_count = summary_row.get("incoming_transfer_count")
                if pd.notna(gross) and not numeric_equal(gross, arrival_sum):
                    warnings.append(
                        f"{club_id} {season}: displayed gross transfer spend differs from parsed arrival fee sum."
                    )
                if pd.notna(incoming_count) and int(incoming_count) != arrival_count:
                    warnings.append(
                        f"{club_id} {season}: incoming transfer count differs from parsed arrival row count."
                    )

            if not departures.empty:
                departure_sum = float(departures.iloc[0]["fee_sum"])
                departure_count = int(departures.iloc[0]["transfer_count"])
                income = summary_row.get("transfer_income_eur")
                outgoing_count = summary_row.get("outgoing_transfer_count")
                if pd.notna(income) and not numeric_equal(income, departure_sum):
                    warnings.append(
                        f"{club_id} {season}: displayed transfer income differs from parsed departure fee sum."
                    )
                if pd.notna(outgoing_count) and int(outgoing_count) != departure_count:
                    warnings.append(
                        f"{club_id} {season}: outgoing transfer count differs from parsed departure row count."
                    )

    print("[report] Transfer data validation")
    print(f"[report] club_season_transfers_clean rows: {len(club_df)}")
    print(f"[report] club_transfer_rows_clean rows: {len(transfer_rows_df)}")

    for message in warnings:
        print(f"[warn] {message}")

    if issues:
        for message in issues:
            print(f"[invalid] {message}")
        return 1

    print("[valid] Transfer datasets passed validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
