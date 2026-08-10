#!/usr/bin/env python3

"""Validate the cleaned club revenue extraction dataset."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "club_id",
    "season",
    "total_revenue_original",
    "matchday_revenue_original",
    "broadcast_revenue_original",
    "commercial_revenue_original",
    "confidence_level",
    "requires_manual_review",
    "women_team_treatment_notes",
    "source_url",
    "source_document",
    "pages_used",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/clean/club_finances/club_revenue_extractions_clean.csv")
    parser.add_argument("--clubs", default="config/big_six_clubs.json")
    parser.add_argument("--output", default="data/clean/club_finances/validation_report.json")
    return parser.parse_args()


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def is_number(value) -> bool:
    if pd.isna(value) or value == "":
        return False
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def main() -> int:
    args = parse_args()
    data_path = Path(args.input)
    df = pd.read_csv(data_path)
    valid_clubs = {club["club_id"] for club in load_json(Path(args.clubs))}

    report = {"critical_errors": [], "warnings": [], "row_findings": []}

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            report["critical_errors"].append(f"Missing required column: {column}")

    season_pattern = re.compile(r"^\d{4}/\d{2}$")

    if not report["critical_errors"]:
        for _, row in df.iterrows():
            findings = {"club_id": row.get("club_id", ""), "season": row.get("season", ""), "warnings": [], "critical_errors": []}
            if row["club_id"] not in valid_clubs:
                findings["critical_errors"].append("club_id is not in the configured Big Six list.")
            if not season_pattern.fullmatch(str(row["season"])):
                findings["critical_errors"].append("season format is invalid.")

            numeric_columns = [
                "total_revenue_original",
                "matchday_revenue_original",
                "broadcast_revenue_original",
                "commercial_revenue_original",
            ]
            for column in numeric_columns:
                if row[column] != "" and not pd.isna(row[column]) and not is_number(row[column]):
                    findings["critical_errors"].append(f"{column} must be numeric or null.")

            if all(is_number(row[column]) for column in numeric_columns):
                total = float(row["total_revenue_original"])
                breakdown = (
                    float(row["matchday_revenue_original"])
                    + float(row["broadcast_revenue_original"])
                    + float(row["commercial_revenue_original"])
                )
                if total and abs(total - breakdown) > total * 0.02:
                    findings["warnings"].append("Revenue breakdown differs from total revenue by more than 2%.")

            if str(row.get("confidence_level", "")).lower() == "low":
                findings["warnings"].append("confidence_level is low.")
            if bool(row.get("requires_manual_review")):
                findings["warnings"].append("requires_manual_review is true.")
            if not str(row.get("women_team_treatment_notes", "")).strip():
                findings["warnings"].append("women_team_treatment_notes is empty.")
            if not str(row.get("source_url", "")).strip() or not str(row.get("source_document", "")).strip():
                findings["warnings"].append("source_url or source_document is missing.")
            if not str(row.get("pages_used", "")).strip() or str(row.get("pages_used")).strip() == "[]":
                findings["warnings"].append("pages_used is empty.")
            if not any(is_number(row[column]) for column in ["matchday_revenue_original", "broadcast_revenue_original", "commercial_revenue_original", "total_revenue_original"]):
                findings["warnings"].append("All revenue categories are null.")

            if findings["warnings"] or findings["critical_errors"]:
                report["row_findings"].append(findings)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print("[report] Financial extraction validation")
    print(f"[report] Rows checked: {len(df)}")
    print(f"[report] Critical errors: {len(report['critical_errors'])}")
    print(f"[report] Row findings: {len(report['row_findings'])}")
    print(f"[saved] {output_path}")

    critical_row_errors = any(finding["critical_errors"] for finding in report["row_findings"])
    return 1 if report["critical_errors"] or critical_row_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
