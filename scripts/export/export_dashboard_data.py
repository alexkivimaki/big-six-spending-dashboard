#!/usr/bin/env python3

"""Export dashboard-ready club-season CSV and JSON files."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

from economic_factors import add_currency_views, load_economic_factors, merge_economic_factors


TRANSFER_PATH = Path("data/clean/transfermarkt/club_season_transfers_clean.csv")
VERIFIED_TRANSFER_PATH = Path("data/clean/transfermarkt/club_season_transfers_verified_clean.csv")
WAGES_PATH = Path("data/clean/ai_agents/club_season_wages_clean.csv")
PERFORMANCE_PATH = Path("data/clean/ai_agents/club_season_performance_clean.csv")
FINANCES_PATH = Path("data/clean/ai_agents/club_season_finances_clean.csv")
MANAGERS_PATH = Path("data/clean/ai_agents/managers_clean.csv")
TRANSFER_ROWS_PATH = Path("data/clean/transfermarkt/club_transfer_rows_clean.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--economic-factors-input", default="data/reference/economic_factors.csv")
    parser.add_argument("--output-csv", default="data/final/club_season_dashboard.csv")
    parser.add_argument("--output-json", default="src/data/clubSeasonData.json")
    parser.add_argument("--transfer-rows-json-output", default="src/data/clubTransferRowsData.json")
    parser.add_argument("--league-output-root", default="data/final/by_league")
    parser.add_argument("--frontend-league-output-root", default="src/data/by_league")
    return parser.parse_args()


def load_csv_if_exists(path: Path, label: str, required: bool = False):
    if not path.exists():
        message = f"[warn] Missing optional input: {path}" if not required else f"[error] Missing required input: {path}"
        print(message)
        return None
    dataframe = pd.read_csv(path)
    print(f"[load] {label}: {path} ({len(dataframe)} rows)")
    return dataframe


def first_non_empty(series: pd.Series):
    non_empty = series.dropna()
    non_empty = non_empty[non_empty.astype(str) != ""]
    if non_empty.empty:
        return None
    return non_empty.iloc[0]


def join_unique_text(series: pd.Series) -> str:
    values = [str(value).strip() for value in series.dropna() if str(value).strip()]
    unique_values = []
    for value in values:
        if value not in unique_values:
            unique_values.append(value)
    return " | ".join(unique_values)


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


def dataframe_to_json_records(dataframe: pd.DataFrame) -> list[dict]:
    records = dataframe.to_dict(orient="records")
    return [sanitize_for_json(record) for record in records]


def write_json(path: Path, records: list[dict]) -> None:
    path.write_text(
        json.dumps(records, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def get_join_keys(dataframe: pd.DataFrame) -> list[str]:
    candidate_keys = ["league_key", "club_id", "season"]
    keys = [column for column in candidate_keys if column in dataframe.columns]
    fallback_keys = [column for column in ("club_id", "season") if column in dataframe.columns]
    return keys if len(keys) >= 2 else fallback_keys


def aggregate_transfers(dataframe: pd.DataFrame) -> pd.DataFrame:
    for column in ("league_key", "league_name"):
        if column not in dataframe.columns:
            dataframe[column] = ""

    numeric_columns = [
        "gross_transfer_spend_eur",
        "transfer_income_eur",
        "net_transfer_spend_eur",
        "incoming_transfer_count",
        "outgoing_transfer_count",
    ]
    for column in numeric_columns:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    grouped = (
        dataframe.groupby(["league_key", "league_name", "club_id", "club_name", "season"], dropna=False)
        .agg(
            gross_transfer_spend_eur=("gross_transfer_spend_eur", "sum"),
            transfer_income_eur=("transfer_income_eur", "sum"),
            net_transfer_spend_eur=("net_transfer_spend_eur", "sum"),
            incoming_transfer_count=("incoming_transfer_count", "sum"),
            outgoing_transfer_count=("outgoing_transfer_count", "sum"),
            source_name=("source_name", join_unique_text),
            source_endpoint=("source_endpoint", join_unique_text),
            collected_at_utc=("collected_at_utc", first_non_empty),
            confidence_level=("confidence_level", first_non_empty),
            notes=("notes", join_unique_text),
        )
        .reset_index()
    )
    return grouped


def dedupe_on_keys(dataframe: pd.DataFrame, label: str) -> pd.DataFrame:
    key_columns = get_join_keys(dataframe)
    if len(key_columns) < 2:
        print(f"[warn] {label} missing join keys and will be skipped.")
        return pd.DataFrame()
    duplicates = dataframe.duplicated(subset=key_columns, keep=False).sum()
    if duplicates:
        print(f"[warn] {label} contains duplicate club_id/season rows; keeping the last occurrence.")
    return dataframe.drop_duplicates(subset=key_columns, keep="last")


def merge_optional(base: pd.DataFrame, extra: pd.DataFrame | None, label: str) -> pd.DataFrame:
    if extra is None or extra.empty:
        return base
    extra = dedupe_on_keys(extra, label)
    if extra.empty:
        return base
    join_keys = [key for key in get_join_keys(base) if key in extra.columns]
    if len(join_keys) < 2:
        join_keys = [key for key in ("club_id", "season") if key in base.columns and key in extra.columns]
    return base.merge(extra, on=join_keys, how="left", suffixes=("", f"_{label}"))


def merge_verified_transfers(derived: pd.DataFrame, verified: pd.DataFrame | None) -> pd.DataFrame:
    if verified is None or verified.empty:
        return derived
    verified = dedupe_on_keys(verified, "verified_transfers")
    if verified.empty:
        return derived

    derived = dedupe_on_keys(derived, "derived_transfers")
    if derived.empty:
        return verified

    join_keys = get_join_keys(verified)
    verified_keys = set(tuple(row[key] for key in join_keys) for _, row in verified.iterrows())
    keep_mask = [
        tuple(row[key] for key in join_keys) not in verified_keys
        for _, row in derived.iterrows()
    ]
    merged = pd.concat([derived.loc[keep_mask], verified], ignore_index=True)
    print(f"[info] Applied {len(verified)} verified transfer row(s) over derived transfer data.")
    return merged


def write_per_league_exports(
    dashboard: pd.DataFrame,
    league_output_root: Path,
    frontend_league_output_root: Path,
) -> None:
    if "league_key" not in dashboard.columns or dashboard.empty:
        return

    league_output_root.mkdir(parents=True, exist_ok=True)
    frontend_league_output_root.mkdir(parents=True, exist_ok=True)

    for league_key, league_frame in dashboard.groupby("league_key", dropna=False):
        league_key = str(league_key or "unknown_league")
        data_dir = league_output_root / league_key
        frontend_dir = frontend_league_output_root / league_key
        data_dir.mkdir(parents=True, exist_ok=True)
        frontend_dir.mkdir(parents=True, exist_ok=True)

        csv_path = data_dir / "club_season_dashboard.csv"
        json_path = frontend_dir / "clubSeasonData.json"
        league_frame.to_csv(csv_path, index=False)
        write_json(json_path, dataframe_to_json_records(league_frame))


def main() -> int:
    args = parse_args()
    output_csv = Path(args.output_csv)
    output_json = Path(args.output_json)
    transfer_rows_json_output = Path(args.transfer_rows_json_output)
    league_output_root = Path(args.league_output_root)
    frontend_league_output_root = Path(args.frontend_league_output_root)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    transfer_rows_json_output.parent.mkdir(parents=True, exist_ok=True)
    league_output_root.mkdir(parents=True, exist_ok=True)
    frontend_league_output_root.mkdir(parents=True, exist_ok=True)
    economic_factors = load_economic_factors(Path(args.economic_factors_input))

    transfers = load_csv_if_exists(TRANSFER_PATH, "transfers", required=True)
    if transfers is None:
        return 1
    verified_transfers = load_csv_if_exists(VERIFIED_TRANSFER_PATH, "verified_transfers")

    wages = load_csv_if_exists(WAGES_PATH, "wages")
    performance = load_csv_if_exists(PERFORMANCE_PATH, "performance")
    finances = load_csv_if_exists(FINANCES_PATH, "finances")
    managers = load_csv_if_exists(MANAGERS_PATH, "managers")
    transfer_rows = load_csv_if_exists(TRANSFER_ROWS_PATH, "club_transfer_rows")

    dashboard = aggregate_transfers(transfers)
    if verified_transfers is not None:
        dashboard = merge_verified_transfers(dashboard, aggregate_transfers(verified_transfers))

    if wages is not None:
        dashboard = merge_optional(dashboard, wages, "wages")
    if performance is not None:
        dashboard = merge_optional(dashboard, performance, "performance")
    if finances is not None:
        dashboard = merge_optional(dashboard, finances, "finances")

    if managers is not None:
        if "season" in managers.columns:
            dashboard = merge_optional(dashboard, managers, "managers")
        else:
            print("[warn] managers_clean.csv does not contain season, so it is not merged into the club-season dashboard export.")

    dashboard = merge_economic_factors(dashboard, economic_factors)
    dashboard = add_currency_views(
        dashboard,
        [
            "gross_transfer_spend_eur",
            "transfer_income_eur",
            "net_transfer_spend_eur",
            "estimated_player_wages_eur",
            "official_staff_costs_eur",
            "revenue_eur",
        ],
        fixed_source_currency="EUR",
    )

    for column in [
        "gross_transfer_spend_eur",
        "transfer_income_eur",
        "net_transfer_spend_eur",
        "estimated_player_wages_eur",
        "official_staff_costs_eur",
        "revenue_eur",
        "points",
    ]:
        if column in dashboard.columns:
            dashboard[column] = pd.to_numeric(dashboard[column], errors="coerce")

    if "estimated_player_wages_eur" not in dashboard.columns:
        dashboard["estimated_player_wages_eur"] = pd.NA
    if "official_staff_costs_eur" not in dashboard.columns:
        dashboard["official_staff_costs_eur"] = pd.NA
    if "revenue_eur" not in dashboard.columns:
        dashboard["revenue_eur"] = pd.NA
    if "points" not in dashboard.columns:
        dashboard["points"] = pd.NA
    if "league_position" not in dashboard.columns:
        dashboard["league_position"] = pd.NA

    dashboard["raw_player_cost_eur"] = dashboard["net_transfer_spend_eur"] + dashboard["estimated_player_wages_eur"]
    dashboard["raw_player_cost_gbp"] = dashboard["net_transfer_spend_gbp"] + dashboard["estimated_player_wages_gbp"]
    dashboard["raw_player_cost_usd"] = dashboard["net_transfer_spend_usd"] + dashboard["estimated_player_wages_usd"]
    dashboard["raw_player_cost_eur_real_2025_26"] = (
        dashboard["net_transfer_spend_eur_real_2025_26"] + dashboard["estimated_player_wages_eur_real_2025_26"]
    )
    dashboard["cost_per_point"] = dashboard["raw_player_cost_eur"] / dashboard["points"]
    dashboard["wage_to_revenue_ratio"] = dashboard["official_staff_costs_eur"] / dashboard["revenue_eur"]

    if "club_name_wages" in dashboard.columns:
        dashboard["club_name"] = dashboard["club_name"].fillna(dashboard["club_name_wages"])
    if "club_name_performance" in dashboard.columns:
        dashboard["club_name"] = dashboard["club_name"].fillna(dashboard["club_name_performance"])

    dashboard.to_csv(output_csv, index=False)
    write_json(output_json, dataframe_to_json_records(dashboard))
    write_per_league_exports(dashboard, league_output_root, frontend_league_output_root)

    if transfer_rows is not None:
        write_json(transfer_rows_json_output, dataframe_to_json_records(transfer_rows))
        print(f"[saved] Transfer rows JSON: {transfer_rows_json_output}")

    print(f"[saved] CSV: {output_csv}")
    print(f"[saved] JSON: {output_json}")
    print(f"[done] Exported {len(dashboard)} dashboard rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
