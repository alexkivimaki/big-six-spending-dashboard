#!/usr/bin/env python3

"""Export the clean club revenue dataset for dashboard use."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


FINAL_COLUMNS = [
    "club_id",
    "club_name",
    "season",
    "financial_year_end",
    "turnover_original",
    "gate_and_matchday_income_original",
    "tv_and_broadcasting_original",
    "commercial_income_original",
    "wage_bill_original",
    "wages_as_proportion_of_turnover",
    "net_debt_original",
    "profit_loss_before_tax_original",
    "total_revenue_eur",
    "matchday_revenue_eur",
    "broadcast_revenue_eur",
    "commercial_revenue_eur",
    "other_revenue_eur",
    "matchday_share",
    "broadcast_share",
    "commercial_share",
    "confidence_level",
    "requires_manual_review",
    "source_url",
    "source_document",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/clean/club_finances/club_revenue_extractions_clean.csv")
    parser.add_argument("--csv-output", default="data/final/club_revenue_dataset.csv")
    parser.add_argument("--json-output", default="src/data/clubRevenueData.json")
    return parser.parse_args()


def safe_share(numerator, denominator):
    if pd.isna(numerator) or pd.isna(denominator):
        return None
    if float(denominator) == 0:
        return None
    return float(numerator) / float(denominator)


def main() -> int:
    args = parse_args()
    df = pd.read_csv(Path(args.input))

    df["turnover_original"] = df["total_revenue_original"]
    df["gate_and_matchday_income_original"] = df["matchday_revenue_original"]
    df["tv_and_broadcasting_original"] = df["broadcast_revenue_original"]
    df["commercial_income_original"] = df["commercial_revenue_original"]
    df["wage_bill_original"] = df["staff_costs_original"]

    def safe_ratio(numerator, denominator):
        if pd.isna(numerator) or pd.isna(denominator):
            return None
        if float(denominator) == 0:
            return None
        return float(numerator) / float(denominator)

    df["wages_as_proportion_of_turnover"] = df.apply(
        lambda row: safe_ratio(row["wage_bill_original"], row["turnover_original"]),
        axis=1,
    )

    df["matchday_share"] = df.apply(lambda row: safe_share(row["matchday_revenue_eur"], row["total_revenue_eur"]), axis=1)
    df["broadcast_share"] = df.apply(lambda row: safe_share(row["broadcast_revenue_eur"], row["total_revenue_eur"]), axis=1)
    df["commercial_share"] = df.apply(lambda row: safe_share(row["commercial_revenue_eur"], row["total_revenue_eur"]), axis=1)

    final_df = df.reindex(columns=FINAL_COLUMNS)
    csv_output = Path(args.csv_output)
    json_output = Path(args.json_output)
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)

    final_df.to_csv(csv_output, index=False)
    json_records = []
    for record in final_df.to_dict(orient="records"):
        json_records.append({key: (None if pd.isna(value) else value) for key, value in record.items()})
    json_output.write_text(
        json.dumps(json_records, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    print(f"[saved] CSV: {csv_output}")
    print(f"[saved] JSON: {json_output}")
    print(f"[done] Exported {len(final_df)} revenue rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
