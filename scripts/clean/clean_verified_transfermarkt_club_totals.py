#!/usr/bin/env python3

"""Normalize manually captured Transfermarkt club-page totals into clean transfer rows."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


OUTPUT_COLUMNS = [
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
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/manual/verified_transfermarkt_club_totals.csv")
    parser.add_argument("--output", default="data/clean/transfermarkt/club_season_transfers_verified_clean.csv")
    parser.add_argument("--clubs", default="config/clubs.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    clubs_path = Path(args.clubs)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"[warn] Verified club totals file not found: {input_path}")
        print(
            "[info] Start from data/reference/verified_transfermarkt_club_totals_template.csv "
            "and save your captured rows as data/raw/manual/verified_transfermarkt_club_totals.csv"
        )
        return 0

    dataframe = pd.read_csv(input_path)

    if clubs_path.exists():
        clubs = pd.read_json(clubs_path)
        club_columns = [column for column in ("club_id", "league_key", "league_name") if column in clubs.columns]
        if "club_id" in club_columns:
            dataframe = dataframe.merge(
                clubs[club_columns].drop_duplicates(subset=["club_id"]),
                on="club_id",
                how="left",
                suffixes=("", "_club_config"),
            )

    for column in [
        "gross_transfer_spend_eur",
        "transfer_income_eur",
        "incoming_transfer_count",
        "outgoing_transfer_count",
    ]:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    if "window" not in dataframe.columns:
        dataframe["window"] = "all"

    dataframe["net_transfer_spend_eur"] = (
        dataframe["gross_transfer_spend_eur"] - dataframe["transfer_income_eur"]
    )
    dataframe["source_endpoint"] = dataframe.get("source_url", "")
    dataframe["collected_at_utc"] = ""

    normalized = pd.DataFrame(columns=OUTPUT_COLUMNS)
    for column in OUTPUT_COLUMNS:
        if column in dataframe.columns:
            normalized[column] = dataframe[column]
        else:
            normalized[column] = ""

    normalized.to_csv(output_path, index=False)
    print(f"[saved] {output_path} ({len(normalized)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
