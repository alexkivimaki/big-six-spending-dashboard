#!/usr/bin/env python3

"""Parse saved Transfermarkt club transfers pages into clean CSV outputs."""

from __future__ import annotations

import argparse
import json
import math
import re
from io import StringIO
from pathlib import Path

import pandas as pd


LEAGUE_NAME_MAP = {
    "premier_league": "Premier League",
    "la_liga": "La Liga",
    "bundesliga": "Bundesliga",
    "serie_a": "Serie A",
    "ligue_1": "Ligue 1",
}


SUMMARY_OUTPUT_COLUMNS = [
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

DETAIL_OUTPUT_COLUMNS = [
    "league_key",
    "league_name",
    "club_id",
    "club_name",
    "season",
    "season_start_year",
    "direction",
    "player_name",
    "age",
    "position",
    "other_club_name",
    "other_competition",
    "fee_text",
    "fee_eur",
    "move_type",
    "source_name",
    "source_endpoint",
    "collected_at_utc",
    "confidence_level",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/transfermarkt/club_transfer_pages")
    parser.add_argument("--summary-output", default="data/clean/transfermarkt/club_season_transfers_clean.csv")
    parser.add_argument("--detail-output", default="data/clean/transfermarkt/club_transfer_rows_clean.csv")
    parser.add_argument("--league-output-root", default="data/clean/transfermarkt/by_league")
    parser.add_argument("--partition-output-root", default="data/clean/transfermarkt/by_partition")
    return parser.parse_args()


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def enrich_metadata_from_path(metadata: dict, html_path: Path, input_dir: Path) -> dict:
    enriched = dict(metadata)
    try:
        relative_parts = html_path.relative_to(input_dir).parts
    except ValueError:
        return enriched

    if len(relative_parts) >= 3:
        enriched.setdefault("league_key", relative_parts[0])
        enriched.setdefault("season_dir", relative_parts[1])
        enriched.setdefault("club_id", relative_parts[2])

    if not enriched.get("season") and enriched.get("season_dir"):
        enriched["season"] = str(enriched["season_dir"]).replace("_", "/")
    if not enriched.get("league_name") and enriched.get("league_key"):
        enriched["league_name"] = LEAGUE_NAME_MAP.get(
            str(enriched["league_key"]),
            str(enriched["league_key"]).replace("_", " ").title(),
        )

    return enriched


def parse_money(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        if math.isnan(value):
            return None
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    lowered = text.lower()
    if lowered in {"-", "free transfer", "loan transfer"} or lowered.startswith("end of loan"):
        return 0.0

    normalized = (
        text.replace("€", "")
        .replace("$", "")
        .replace("£", "")
        .replace(",", "")
        .replace("Loan fee:", "")
        .replace("loan fee:", "")
        .replace(" ", "")
        .lower()
    )
    normalized = normalized.replace("mio.", "m").replace("mill.", "m").replace("mil.", "m")

    match = re.search(r"-?\d+(?:\.\d+)?", normalized)
    if not match:
        return None

    number = float(match.group())
    if "bn" in normalized:
        return number * 1_000_000_000
    if "m" in normalized:
        return number * 1_000_000
    if "k" in normalized:
        return number * 1_000
    return number


def classify_move_type(fee_text: str) -> str:
    lowered = str(fee_text or "").strip().lower()
    if lowered.startswith("loan fee"):
        return "loan_fee"
    if lowered == "free transfer":
        return "free_transfer"
    if lowered == "loan transfer":
        return "loan_transfer"
    if lowered.startswith("end of loan"):
        return "end_of_loan"
    if lowered == "-":
        return "internal_promotion_or_return"
    return "transfer_fee"


def find_transfer_table(tables: list[pd.DataFrame], counterpart_column: str) -> pd.DataFrame | None:
    for table in tables:
        columns = [str(column) for column in table.columns]
        if "Player" in columns and "Fee" in columns and counterpart_column in columns:
            return table
    return None


def find_summary_table(tables: list[pd.DataFrame]) -> pd.DataFrame | None:
    for table in tables:
        columns = [str(column) for column in table.columns]
        if "Fee" in columns and any("Arrivals/Departures" in column for column in columns):
            return table
    return None


def clean_text(value) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def parse_age(value):
    text = clean_text(value)
    if not text:
        return None
    match = re.search(r"\d+", text)
    return int(match.group()) if match else None


def collapse_transfer_table(
    dataframe: pd.DataFrame,
    metadata: dict,
    direction: str,
) -> list[dict]:
    rows = []
    primary_indexes = [index for index, value in enumerate(dataframe["Age"].tolist()) if pd.notna(value)]

    for offset, start_index in enumerate(primary_indexes):
        end_index = primary_indexes[offset + 1] if offset + 1 < len(primary_indexes) else len(dataframe)
        primary_row = dataframe.iloc[start_index]
        details = [
            clean_text(dataframe.iloc[index]["Player"])
            for index in range(start_index + 1, end_index)
            if clean_text(dataframe.iloc[index]["Player"])
        ]

        player_name = details[0] if len(details) > 0 else clean_text(primary_row.get("Player"))
        position = details[1] if len(details) > 1 else ""
        other_club_name = details[2] if len(details) > 2 else ""
        other_competition = details[3] if len(details) > 3 else ""
        fee_text = clean_text(primary_row.get("Fee"))

        if any(
            player_name.startswith(prefix)
            for prefix in ("Sum:", "Average age:", "Total market value")
        ):
            continue

        notes = []
        if len(details) < 4:
            notes.append("Detail rows were shorter than expected while parsing the transfer table.")

        rows.append(
            {
                "league_key": metadata.get("league_key", ""),
                "league_name": metadata.get("league_name", ""),
                "club_id": metadata.get("club_id", ""),
                "club_name": metadata.get("club_name", ""),
                "season": metadata.get("season", ""),
                "season_start_year": metadata.get("season_start_year", ""),
                "direction": direction,
                "player_name": player_name,
                "age": parse_age(primary_row.get("Age")),
                "position": position,
                "other_club_name": other_club_name,
                "other_competition": other_competition,
                "fee_text": fee_text,
                "fee_eur": parse_money(fee_text),
                "move_type": classify_move_type(fee_text),
                "source_name": metadata.get("source_name", "transfermarkt_club_page"),
                "source_endpoint": metadata.get("source_url", ""),
                "collected_at_utc": metadata.get("collected_at_utc", ""),
                "confidence_level": "high" if fee_text else "medium",
                "notes": " ".join(notes),
            }
        )

    return rows


def parse_summary_totals(summary_table: pd.DataFrame) -> tuple[float | None, float | None]:
    gross = None
    income = None

    for _, row in summary_table.iterrows():
        label = " ".join(clean_text(value) for value in row.tolist() if clean_text(value))
        fee_text = clean_text(row.get("Fee"))
        if "Expenditure" in label:
            gross = parse_money(fee_text)
        if "Income" in label:
            income = parse_money(fee_text)

    return gross, income


def build_summary_row(
    metadata: dict,
    arrivals: list[dict],
    departures: list[dict],
    displayed_gross: float | None,
    displayed_income: float | None,
) -> dict:
    notes = []
    parsed_gross = sum(row["fee_eur"] for row in arrivals if row["fee_eur"] is not None)
    parsed_income = sum(row["fee_eur"] for row in departures if row["fee_eur"] is not None)

    if displayed_gross is not None and not math.isclose(parsed_gross, displayed_gross, abs_tol=1e-6):
        notes.append(
            f"Displayed arrivals sum ({displayed_gross:.0f}) differs from parsed arrivals fee sum ({parsed_gross:.0f})."
        )
    if displayed_income is not None and not math.isclose(parsed_income, displayed_income, abs_tol=1e-6):
        notes.append(
            f"Displayed departures sum ({displayed_income:.0f}) differs from parsed departures fee sum ({parsed_income:.0f})."
        )

    gross_value = displayed_gross if displayed_gross is not None else parsed_gross
    income_value = displayed_income if displayed_income is not None else parsed_income
    net_value = gross_value - income_value if gross_value is not None and income_value is not None else None

    return {
        "league_key": metadata.get("league_key", ""),
        "league_name": metadata.get("league_name", ""),
        "club_id": metadata.get("club_id", ""),
        "club_name": metadata.get("club_name", ""),
        "season": metadata.get("season", ""),
        "season_start_year": metadata.get("season_start_year", ""),
        "window": "all",
        "gross_transfer_spend_eur": gross_value,
        "transfer_income_eur": income_value,
        "net_transfer_spend_eur": net_value,
        "incoming_transfer_count": len(arrivals),
        "outgoing_transfer_count": len(departures),
        "source_name": metadata.get("source_name", "transfermarkt_club_page"),
        "source_endpoint": metadata.get("source_url", ""),
        "collected_at_utc": metadata.get("collected_at_utc", ""),
        "confidence_level": "high" if displayed_gross is not None and displayed_income is not None else "medium",
        "notes": " ".join(notes),
    }


def write_partitioned_outputs(
    summary_dataframe: pd.DataFrame,
    detail_dataframe: pd.DataFrame,
    partition_output_root: Path,
) -> None:
    if summary_dataframe.empty:
        return

    partition_output_root.mkdir(parents=True, exist_ok=True)

    for _, summary_row in summary_dataframe.iterrows():
        league_key = str(summary_row.get("league_key") or "unknown_league")
        club_id = str(summary_row.get("club_id") or "unknown_club")
        season_label = str(summary_row.get("season") or "")
        season_dir = season_label.replace("/", "_") if season_label else "unknown_season"

        partition_dir = partition_output_root / league_key / season_dir / club_id
        partition_dir.mkdir(parents=True, exist_ok=True)

        summary_slice = pd.DataFrame([summary_row.to_dict()], columns=SUMMARY_OUTPUT_COLUMNS)
        summary_path = partition_dir / f"{club_id}_{season_dir}_club_season_transfers_clean.csv"
        summary_slice.to_csv(summary_path, index=False)

        detail_slice = detail_dataframe[
            (detail_dataframe["league_key"] == summary_row.get("league_key"))
            & (detail_dataframe["club_id"] == summary_row.get("club_id"))
            & (detail_dataframe["season"] == summary_row.get("season"))
        ]
        detail_path = partition_dir / f"{club_id}_{season_dir}_club_transfer_rows_clean.csv"
        detail_slice.to_csv(detail_path, index=False)


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input)
    summary_output_path = Path(args.summary_output)
    detail_output_path = Path(args.detail_output)
    league_output_root = Path(args.league_output_root)
    partition_output_root = Path(args.partition_output_root)
    summary_output_path.parent.mkdir(parents=True, exist_ok=True)
    detail_output_path.parent.mkdir(parents=True, exist_ok=True)
    league_output_root.mkdir(parents=True, exist_ok=True)
    partition_output_root.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    detail_rows = []
    html_files = sorted(input_dir.rglob("*.html"))

    if not html_files:
        print(f"[warn] No raw HTML files found in {input_dir}")

    for html_path in html_files:
        meta_path = html_path.with_suffix(".meta.json")
        if not meta_path.exists():
            print(f"[warn] Missing metadata sidecar for {html_path.name}; skipping file.")
            continue

        metadata = enrich_metadata_from_path(load_json(meta_path), html_path, input_dir)
        if int(metadata.get("status_code", 0) or 0) >= 400:
            print(f"[warn] Skipping non-success response file: {html_path.name}")
            continue

        html = load_text(html_path)
        try:
            tables = pd.read_html(StringIO(html))
        except ValueError:
            print(f"[warn] No HTML tables found in {html_path.name}")
            continue

        arrivals_table = find_transfer_table(tables, "Left")
        departures_table = find_transfer_table(tables, "Joined")
        summary_table = find_summary_table(tables)

        if arrivals_table is None or departures_table is None or summary_table is None:
            print(f"[warn] Could not find all required tables in {html_path.name}")
            continue

        arrivals = collapse_transfer_table(arrivals_table, metadata, "arrival")
        departures = collapse_transfer_table(departures_table, metadata, "departure")
        displayed_gross, displayed_income = parse_summary_totals(summary_table)

        detail_rows.extend(arrivals)
        detail_rows.extend(departures)
        summary_rows.append(
            build_summary_row(metadata, arrivals, departures, displayed_gross, displayed_income)
        )

    summary_dataframe = pd.DataFrame(summary_rows, columns=SUMMARY_OUTPUT_COLUMNS)
    detail_dataframe = pd.DataFrame(detail_rows, columns=DETAIL_OUTPUT_COLUMNS)
    if not summary_dataframe.empty:
        summary_dataframe = summary_dataframe.sort_values(
            by=["league_key", "club_id", "season_start_year"],
            kind="stable",
        )
    if not detail_dataframe.empty:
        detail_dataframe = detail_dataframe.sort_values(
            by=["league_key", "club_id", "season_start_year", "direction", "player_name"],
            kind="stable",
        )

    summary_dataframe.to_csv(summary_output_path, index=False)
    detail_dataframe.to_csv(detail_output_path, index=False)

    if "league_key" in summary_dataframe.columns and not summary_dataframe.empty:
        for league_key, league_summary in summary_dataframe.groupby("league_key", dropna=False):
            league_key = league_key or "unknown_league"
            league_dir = league_output_root / str(league_key)
            league_dir.mkdir(parents=True, exist_ok=True)
            league_summary.to_csv(league_dir / "club_season_transfers_clean.csv", index=False)

    if "league_key" in detail_dataframe.columns and not detail_dataframe.empty:
        for league_key, league_detail in detail_dataframe.groupby("league_key", dropna=False):
            league_key = league_key or "unknown_league"
            league_dir = league_output_root / str(league_key)
            league_dir.mkdir(parents=True, exist_ok=True)
            league_detail.to_csv(league_dir / "club_transfer_rows_clean.csv", index=False)

    write_partitioned_outputs(summary_dataframe, detail_dataframe, partition_output_root)

    print(f"[saved] {summary_output_path} ({len(summary_dataframe)} rows)")
    print(f"[saved] {detail_output_path} ({len(detail_dataframe)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
