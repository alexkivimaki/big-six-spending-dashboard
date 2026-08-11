#!/usr/bin/env python3

"""Export the clean club revenue dataset for dashboard use."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

from economic_factors import add_currency_views, load_economic_factors, merge_economic_factors


FINAL_COLUMNS = [
    "club_id",
    "club_name",
    "season",
    "financial_year_end",
    "currency_original",
    "gbp_to_eur_rate",
    "eur_to_usd_rate",
    "gbp_to_usd_rate",
    "inflation_adjustment_to_2025_26",
    "real_price_basis_label",
    "economic_factors_complete",
    "fx_source",
    "inflation_source",
    "economic_factor_notes",
    "turnover_original",
    "turnover_gbp",
    "turnover_eur",
    "turnover_usd",
    "turnover_gbp_real_2025_26",
    "turnover_eur_real_2025_26",
    "turnover_usd_real_2025_26",
    "gate_and_matchday_income_original",
    "gate_and_matchday_income_gbp",
    "gate_and_matchday_income_eur",
    "gate_and_matchday_income_usd",
    "gate_and_matchday_income_gbp_real_2025_26",
    "gate_and_matchday_income_eur_real_2025_26",
    "gate_and_matchday_income_usd_real_2025_26",
    "tv_and_broadcasting_original",
    "tv_and_broadcasting_gbp",
    "tv_and_broadcasting_eur",
    "tv_and_broadcasting_usd",
    "tv_and_broadcasting_gbp_real_2025_26",
    "tv_and_broadcasting_eur_real_2025_26",
    "tv_and_broadcasting_usd_real_2025_26",
    "commercial_income_original",
    "commercial_income_gbp",
    "commercial_income_eur",
    "commercial_income_usd",
    "commercial_income_gbp_real_2025_26",
    "commercial_income_eur_real_2025_26",
    "commercial_income_usd_real_2025_26",
    "sporting_revenue_original",
    "sporting_revenue_gbp",
    "sporting_revenue_eur",
    "sporting_revenue_usd",
    "sporting_revenue_gbp_real_2025_26",
    "sporting_revenue_eur_real_2025_26",
    "sporting_revenue_usd_real_2025_26",
    "wage_bill_original",
    "wage_bill_gbp",
    "wage_bill_eur",
    "wage_bill_usd",
    "wage_bill_gbp_real_2025_26",
    "wage_bill_eur_real_2025_26",
    "wage_bill_usd_real_2025_26",
    "wages_as_proportion_of_turnover",
    "net_debt_original",
    "net_debt_gbp",
    "net_debt_eur",
    "net_debt_usd",
    "net_debt_gbp_real_2025_26",
    "net_debt_eur_real_2025_26",
    "net_debt_usd_real_2025_26",
    "profit_loss_before_tax_original",
    "profit_loss_before_tax_gbp",
    "total_revenue_eur",
    "total_revenue_gbp",
    "total_revenue_usd",
    "total_revenue_gbp_real_2025_26",
    "total_revenue_eur_real_2025_26",
    "total_revenue_usd_real_2025_26",
    "matchday_revenue_eur",
    "matchday_revenue_gbp",
    "matchday_revenue_usd",
    "matchday_revenue_gbp_real_2025_26",
    "matchday_revenue_eur_real_2025_26",
    "matchday_revenue_usd_real_2025_26",
    "broadcast_revenue_eur",
    "broadcast_revenue_gbp",
    "broadcast_revenue_usd",
    "broadcast_revenue_gbp_real_2025_26",
    "broadcast_revenue_eur_real_2025_26",
    "broadcast_revenue_usd_real_2025_26",
    "commercial_revenue_eur",
    "commercial_revenue_gbp",
    "commercial_revenue_usd",
    "commercial_revenue_gbp_real_2025_26",
    "commercial_revenue_eur_real_2025_26",
    "commercial_revenue_usd_real_2025_26",
    "other_revenue_eur",
    "staff_costs_eur",
    "staff_costs_usd",
    "staff_costs_gbp_real_2025_26",
    "staff_costs_eur_real_2025_26",
    "staff_costs_usd_real_2025_26",
    "profit_loss_before_tax_eur",
    "profit_loss_before_tax_usd",
    "profit_loss_before_tax_gbp_real_2025_26",
    "profit_loss_before_tax_eur_real_2025_26",
    "profit_loss_before_tax_usd_real_2025_26",
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
    parser.add_argument("--economic-factors-input", default="data/reference/economic_factors.csv")
    parser.add_argument("--csv-output", default="data/final/club_revenue_dataset.csv")
    parser.add_argument("--json-output", default="src/data/clubRevenueData.json")
    return parser.parse_args()


def safe_share(numerator, denominator):
    if pd.isna(numerator) or pd.isna(denominator):
        return None
    if float(denominator) == 0:
        return None
    return float(numerator) / float(denominator)


def sanitize_for_json(value):
    if isinstance(value, dict):
        return {key: sanitize_for_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_for_json(item) for item in value]
    if value is None or value is pd.NA:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if pd.isna(value):
        return None
    return value


def main() -> int:
    args = parse_args()
    df = pd.read_csv(Path(args.input))
    factors = load_economic_factors(Path(args.economic_factors_input))

    df["turnover_original"] = df["total_revenue_original"]
    df["gate_and_matchday_income_original"] = df["matchday_revenue_original"]
    df["tv_and_broadcasting_original"] = df["broadcast_revenue_original"]
    df["commercial_income_original"] = df["commercial_revenue_original"]
    df["wage_bill_original"] = df["staff_costs_original"]
    df["sporting_revenue_original"] = df.apply(
        lambda row: (
            float(row["matchday_revenue_original"]) + float(row["broadcast_revenue_original"])
            if pd.notna(row["matchday_revenue_original"]) and pd.notna(row["broadcast_revenue_original"])
            else None
        ),
        axis=1,
    )
    df = merge_economic_factors(df, factors)
    df = add_currency_views(
        df,
        [
            "total_revenue_original",
            "matchday_revenue_original",
            "broadcast_revenue_original",
            "commercial_revenue_original",
            "sporting_revenue_original",
            "staff_costs_original",
            "net_debt_original",
            "profit_loss_before_tax_original",
        ],
        currency_column="currency_original",
    )

    alias_columns = {
        "turnover_gbp": "total_revenue_gbp",
        "turnover_eur": "total_revenue_eur",
        "turnover_usd": "total_revenue_usd",
        "turnover_gbp_real_2025_26": "total_revenue_gbp_real_2025_26",
        "turnover_eur_real_2025_26": "total_revenue_eur_real_2025_26",
        "turnover_usd_real_2025_26": "total_revenue_usd_real_2025_26",
        "gate_and_matchday_income_gbp": "matchday_revenue_gbp",
        "gate_and_matchday_income_eur": "matchday_revenue_eur",
        "gate_and_matchday_income_usd": "matchday_revenue_usd",
        "gate_and_matchday_income_gbp_real_2025_26": "matchday_revenue_gbp_real_2025_26",
        "gate_and_matchday_income_eur_real_2025_26": "matchday_revenue_eur_real_2025_26",
        "gate_and_matchday_income_usd_real_2025_26": "matchday_revenue_usd_real_2025_26",
        "tv_and_broadcasting_gbp": "broadcast_revenue_gbp",
        "tv_and_broadcasting_eur": "broadcast_revenue_eur",
        "tv_and_broadcasting_usd": "broadcast_revenue_usd",
        "tv_and_broadcasting_gbp_real_2025_26": "broadcast_revenue_gbp_real_2025_26",
        "tv_and_broadcasting_eur_real_2025_26": "broadcast_revenue_eur_real_2025_26",
        "tv_and_broadcasting_usd_real_2025_26": "broadcast_revenue_usd_real_2025_26",
        "commercial_income_gbp": "commercial_revenue_gbp",
        "commercial_income_eur": "commercial_revenue_eur",
        "commercial_income_usd": "commercial_revenue_usd",
        "commercial_income_gbp_real_2025_26": "commercial_revenue_gbp_real_2025_26",
        "commercial_income_eur_real_2025_26": "commercial_revenue_eur_real_2025_26",
        "commercial_income_usd_real_2025_26": "commercial_revenue_usd_real_2025_26",
        "wage_bill_gbp": "staff_costs_gbp",
        "wage_bill_eur": "staff_costs_eur",
        "wage_bill_usd": "staff_costs_usd",
        "wage_bill_gbp_real_2025_26": "staff_costs_gbp_real_2025_26",
        "wage_bill_eur_real_2025_26": "staff_costs_eur_real_2025_26",
        "wage_bill_usd_real_2025_26": "staff_costs_usd_real_2025_26",
    }
    for alias, source in alias_columns.items():
        df[alias] = df[source]

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

    df["matchday_share"] = df.apply(
        lambda row: safe_share(row["matchday_revenue_original"], row["total_revenue_original"]),
        axis=1,
    )
    df["broadcast_share"] = df.apply(
        lambda row: safe_share(row["broadcast_revenue_original"], row["total_revenue_original"]),
        axis=1,
    )
    df["commercial_share"] = df.apply(
        lambda row: safe_share(row["commercial_revenue_original"], row["total_revenue_original"]),
        axis=1,
    )

    final_df = df.reindex(columns=FINAL_COLUMNS)
    csv_output = Path(args.csv_output)
    json_output = Path(args.json_output)
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)

    final_df.to_csv(csv_output, index=False)
    json_records = [sanitize_for_json(record) for record in final_df.to_dict(orient="records")]
    json_output.write_text(
        json.dumps(json_records, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    print(f"[saved] CSV: {csv_output}")
    print(f"[saved] JSON: {json_output}")
    print(f"[done] Exported {len(final_df)} revenue rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
