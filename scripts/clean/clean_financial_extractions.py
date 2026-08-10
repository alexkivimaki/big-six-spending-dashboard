#!/usr/bin/env python3

"""Flatten financial extraction JSON files into clean CSV outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ROW_COLUMNS = [
    "club_id",
    "club_name",
    "season",
    "financial_year_end",
    "currency_original",
    "units_original",
    "total_revenue_original",
    "matchday_revenue_original",
    "broadcast_revenue_original",
    "commercial_revenue_original",
    "other_revenue_original",
    "women_team_revenue_original",
    "excluded_player_trading_revenue_original",
    "staff_costs_original",
    "net_debt_original",
    "player_amortisation_original",
    "profit_on_player_sales_original",
    "profit_loss_before_tax_original",
    "total_revenue_eur",
    "matchday_revenue_eur",
    "broadcast_revenue_eur",
    "commercial_revenue_eur",
    "other_revenue_eur",
    "net_debt_eur",
    "profit_loss_before_tax_eur",
    "exchange_rate_used",
    "exchange_rate_source",
    "revenue_sum_check_original",
    "revenue_sum_difference_original",
    "pages_used",
    "classification_notes",
    "women_team_treatment_notes",
    "non_football_revenue_notes",
    "confidence_level",
    "requires_manual_review",
    "source_document",
    "source_url",
    "notes",
]

EVIDENCE_COLUMNS = [
    "club_id",
    "club_name",
    "season",
    "financial_year_end",
    "field",
    "value_original",
    "page_number",
    "statement_label",
    "evidence_text",
    "source_document",
    "source_url",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/ai_agents/financial_extraction_outputs")
    parser.add_argument("--output", default="data/clean/club_finances/club_revenue_extractions_clean.csv")
    parser.add_argument("--evidence-output", default="data/clean/club_finances/club_revenue_evidence_clean.csv")
    parser.add_argument("--verified-overrides", default="data/raw/manual/verified_financial_statement_fields.csv")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_row(payload: dict) -> dict:
    row = {column: payload.get(column) for column in ROW_COLUMNS}
    row["pages_used"] = json.dumps(payload.get("pages_used", []), ensure_ascii=True)
    row["source_document"] = payload.get("source_document", payload.get("report_title", ""))
    row["source_url"] = payload.get("source_url", "")
    missing = [column for column in ROW_COLUMNS if column not in payload and column not in {"pages_used", "source_document", "source_url"}]
    notes = str(row.get("notes") or "")
    if missing:
        warning = f"Missing fields in raw extraction: {', '.join(missing)}."
        row["notes"] = f"{notes} {warning}".strip()
    return row


def build_evidence_rows(payload: dict) -> list[dict]:
    rows = []
    for evidence in payload.get("evidence", []) or []:
        rows.append(
            {
                "club_id": payload.get("club_id", ""),
                "club_name": payload.get("club_name", ""),
                "season": payload.get("season", ""),
                "financial_year_end": payload.get("financial_year_end", ""),
                "field": evidence.get("field", ""),
                "value_original": evidence.get("value_original"),
                "page_number": evidence.get("page_number"),
                "statement_label": evidence.get("statement_label", ""),
                "evidence_text": evidence.get("evidence_text", ""),
                "source_document": payload.get("source_document", payload.get("report_title", "")),
                "source_url": payload.get("source_url", ""),
            }
        )
    return rows


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input)
    output_path = Path(args.output)
    evidence_output_path = Path(args.evidence_output)

    records = []
    evidence_rows = []
    for path in sorted(input_dir.glob("*.json")):
        if path.name == "example_output.json":
            continue
        payload = load_json(path)
        records.append(build_row(payload))
        evidence_rows.extend(build_evidence_rows(payload))

    records_df = pd.DataFrame(records, columns=ROW_COLUMNS)
    overrides_path = Path(args.verified_overrides)
    if overrides_path.exists() and not records_df.empty:
        overrides_df = pd.read_csv(overrides_path)
        for override in overrides_df.to_dict("records"):
            mask = (records_df["club_id"] == override["club_id"]) & (records_df["season"] == override["season"])
            if not mask.any():
                continue
            for field in ("net_debt_original", "profit_loss_before_tax_original"):
                value = override.get(field)
                if pd.notna(value):
                    records_df.loc[mask, field] = value
            note = str(override.get("notes") or "").strip()
            if note:
                existing = records_df.loc[mask, "notes"].fillna("")
                records_df.loc[mask, "notes"] = existing.apply(lambda current: f"{current} {note}".strip())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_output_path.parent.mkdir(parents=True, exist_ok=True)

    records_df.to_csv(output_path, index=False)
    pd.DataFrame(evidence_rows, columns=EVIDENCE_COLUMNS).to_csv(evidence_output_path, index=False)

    manual_review_count = int(records_df["requires_manual_review"].fillna(False).astype(bool).sum())
    print(f"[saved] {output_path} ({len(records_df)} rows)")
    print(f"[saved] {evidence_output_path} ({len(evidence_rows)} rows)")
    print(f"[summary] {manual_review_count} rows require manual review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
