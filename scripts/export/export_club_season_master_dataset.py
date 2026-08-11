#!/usr/bin/env python3

"""Build a joined club-season master dataset for downstream dashboard work."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

from economic_factors import add_currency_views, load_economic_factors, merge_economic_factors


TRANSFERS_PATH = Path("data/clean/transfermarkt/club_season_transfers_clean.csv")
MANAGER_SPELLS_PATH = Path("data/clean/transfermarkt/club_season_manager_spells_clean.csv")
ACHIEVEMENTS_PATH = Path("data/clean/transfermarkt/club_season_achievements_clean.csv")
ACHIEVEMENT_ROWS_PATH = Path("data/clean/transfermarkt/achievement_rows_clean.csv")
PERFORMANCE_PATH = Path("data/clean/ai_agents/club_season_performance_clean.csv")
FINANCE_PATH = Path("data/clean/club_finances/club_revenue_extractions_clean.csv")
PREMIER_LEAGUE_RAW_PERFORMANCE_DIR = Path(
    "data/raw/performance/premier_league/premier_league_tables_2008-09_to_2024-25_with_qualification_csv"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--economic-factors-input", default="data/reference/economic_factors.csv")
    parser.add_argument("--output-csv", default="data/final/club_season_master.csv")
    parser.add_argument("--output-json", default="src/data/clubSeasonMasterData.json")
    parser.add_argument("--league-output-root", default="data/final/by_league")
    parser.add_argument("--frontend-league-output-root", default="src/data/by_league")
    parser.add_argument("--season-from", default="")
    return parser.parse_args()


def load_csv(path: Path, label: str, required: bool = False) -> pd.DataFrame | None:
    if not path.exists():
        message = f"[error] Missing required input: {path}" if required else f"[warn] Missing optional input: {path}"
        print(message)
        return None
    dataframe = pd.read_csv(path)
    print(f"[load] {label}: {path} ({len(dataframe)} rows)")
    return dataframe


def first_non_empty(series: pd.Series):
    non_empty = series.dropna()
    non_empty = non_empty[non_empty.astype(str).str.strip() != ""]
    if non_empty.empty:
        return None
    return non_empty.iloc[0]


def join_unique_text(series: pd.Series) -> str:
    values = []
    for value in series.dropna():
        text = str(value).strip()
        if text and text not in values:
            values.append(text)
    return " | ".join(values)


def safe_json_list(series: pd.Series) -> str:
    values = []
    for value in series.dropna():
        text = str(value).strip()
        if text and text not in values:
            values.append(text)
    return json.dumps(values, ensure_ascii=False)


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


def add_season_bounds(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.copy()
    dataframe["season_start_year"] = pd.to_numeric(
        dataframe["season"].astype(str).str.slice(0, 4),
        errors="coerce",
    )
    dataframe["season_end_year"] = dataframe["season_start_year"] + 1
    return dataframe


def aggregate_transfers(dataframe: pd.DataFrame) -> pd.DataFrame:
    frame = dataframe.copy()
    frame = add_season_bounds(frame)
    numeric_columns = [
        "gross_transfer_spend_eur",
        "transfer_income_eur",
        "net_transfer_spend_eur",
        "incoming_transfer_count",
        "outgoing_transfer_count",
    ]
    for column in numeric_columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    grouped = (
        frame.groupby(
            ["league_key", "league_name", "club_id", "club_name", "season", "season_start_year", "season_end_year"],
            dropna=False,
        )
        .agg(
            gross_transfer_spend_eur=("gross_transfer_spend_eur", "sum"),
            transfer_income_eur=("transfer_income_eur", "sum"),
            net_transfer_spend_eur=("net_transfer_spend_eur", "sum"),
            incoming_transfer_count=("incoming_transfer_count", "sum"),
            outgoing_transfer_count=("outgoing_transfer_count", "sum"),
            transfer_source_name=("source_name", join_unique_text),
            transfer_source_endpoint=("source_endpoint", join_unique_text),
            transfer_collected_at_utc=("collected_at_utc", first_non_empty),
            transfer_confidence_level=("confidence_level", first_non_empty),
            transfer_notes=("notes", join_unique_text),
        )
        .reset_index()
    )
    return grouped


def aggregate_manager_spells(dataframe: pd.DataFrame) -> pd.DataFrame:
    frame = dataframe.copy()
    frame["share_of_season"] = pd.to_numeric(frame["share_of_season"], errors="coerce")
    frame["days_in_charge_in_season"] = pd.to_numeric(frame["days_in_charge_in_season"], errors="coerce")
    frame["matches"] = pd.to_numeric(frame["matches"], errors="coerce")
    frame["wins"] = pd.to_numeric(frame["wins"], errors="coerce")
    frame["draws"] = pd.to_numeric(frame["draws"], errors="coerce")
    frame["losses"] = pd.to_numeric(frame["losses"], errors="coerce")
    frame["ppg"] = pd.to_numeric(frame["ppg"], errors="coerce")

    group_keys = ["league_key", "league_name", "club_id", "club_name", "season"]
    rows: list[dict] = []

    for keys, group in frame.groupby(group_keys, dropna=False):
        ordered = group.sort_values(
            by=["share_of_season", "days_in_charge_in_season", "spell_start_date", "manager_name"],
            ascending=[False, False, True, True],
            na_position="last",
        )
        primary = ordered.iloc[0]
        row = dict(zip(group_keys, keys))
        row.update(
            {
                "manager_count_in_season": int(len(group)),
                "manager_names": join_unique_text(group["manager_name"]),
                "manager_ids": safe_json_list(group["manager_id"]),
                "primary_manager_id": primary.get("manager_id"),
                "primary_manager_name": primary.get("manager_name"),
                "primary_manager_share_of_season": primary.get("share_of_season"),
                "primary_manager_days_in_charge_in_season": primary.get("days_in_charge_in_season"),
                "primary_manager_spell_start_date": primary.get("spell_start_date"),
                "primary_manager_spell_end_date": primary.get("spell_end_date"),
                "primary_manager_matches": primary.get("matches"),
                "primary_manager_wins": primary.get("wins"),
                "primary_manager_draws": primary.get("draws"),
                "primary_manager_losses": primary.get("losses"),
                "primary_manager_ppg": primary.get("ppg"),
                "manager_source_name": join_unique_text(group["source_name"]),
                "manager_source_endpoint": join_unique_text(group["source_endpoint"]),
                "manager_collected_at_utc": first_non_empty(group["collected_at_utc"]),
                "manager_confidence_level": first_non_empty(group["confidence_level"]),
                "manager_notes": join_unique_text(group["notes"]),
            }
        )
        rows.append(row)

    return pd.DataFrame(rows)


def aggregate_achievements(dataframe: pd.DataFrame) -> pd.DataFrame:
    frame = dataframe.copy()
    return frame.rename(
        columns={
            "source_name": "achievement_source_name",
            "source_endpoint": "achievement_source_endpoint",
            "collected_at_utc": "achievement_collected_at_utc",
            "confidence_level": "achievement_confidence_level",
            "notes": "achievement_notes",
        }
    )


def aggregate_achievement_rows(dataframe: pd.DataFrame) -> pd.DataFrame:
    frame = dataframe.copy().rename(
        columns={
            "assigned_season": "season",
            "assigned_season_start_year": "season_start_year",
            "assigned_season_end_year": "season_end_year",
        }
    )

    group_keys = ["league_key", "league_name", "club_id", "club_name", "season", "season_start_year", "season_end_year"]
    rows: list[dict] = []

    for keys, group in frame.groupby(group_keys, dropna=False):
        labels = []
        major_labels = []
        for _, row in group.iterrows():
            name = str(row.get("achievement_name") or "").strip()
            result = str(row.get("achievement_result") or "").strip()
            if not name:
                continue
            label = f"{name} ({result})" if result and result.lower() != "other" else name
            if label not in labels:
                labels.append(label)
            if bool(row.get("is_major_trophy")) and label not in major_labels:
                major_labels.append(label)

        grouped_row = dict(zip(group_keys, keys))
        grouped_row.update(
            {
                "achievements_in_season": " | ".join(labels),
                "achievement_categories": join_unique_text(group["achievement_category"]),
                "major_trophies_in_season": " | ".join(major_labels),
            }
        )
        rows.append(grouped_row)

    result = pd.DataFrame(rows)
    if not result.empty:
        result["achievements_in_season"] = result["achievements_in_season"].replace("", pd.NA)
        result["major_trophies_in_season"] = result["major_trophies_in_season"].replace("", pd.NA)
    return result


def aggregate_finances(dataframe: pd.DataFrame, economic_factors: pd.DataFrame) -> pd.DataFrame:
    frame = dataframe.copy()
    numeric_columns = [
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
        "revenue_sum_check_original",
        "revenue_sum_difference_original",
    ]
    for column in numeric_columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame["sporting_revenue_original"] = frame.apply(
        lambda row: (
            float(row["matchday_revenue_original"]) + float(row["broadcast_revenue_original"])
            if pd.notna(row["matchday_revenue_original"]) and pd.notna(row["broadcast_revenue_original"])
            else None
        ),
        axis=1,
    )
    frame = merge_economic_factors(frame, economic_factors)
    frame = add_currency_views(
        frame,
        [
            "total_revenue_original",
            "matchday_revenue_original",
            "broadcast_revenue_original",
            "commercial_revenue_original",
            "sporting_revenue_original",
            "staff_costs_original",
            "net_debt_original",
            "player_amortisation_original",
            "profit_on_player_sales_original",
            "profit_loss_before_tax_original",
        ],
        currency_column="currency_original",
    )

    frame = frame.rename(
        columns={
            "total_revenue_eur": "revenue_eur",
            "staff_costs_original": "official_staff_costs_original",
            "staff_costs_gbp": "official_staff_costs_gbp",
            "staff_costs_eur": "official_staff_costs_eur",
            "staff_costs_usd": "official_staff_costs_usd",
            "staff_costs_gbp_real_2025_26": "official_staff_costs_gbp_real_2025_26",
            "staff_costs_eur_real_2025_26": "official_staff_costs_eur_real_2025_26",
            "staff_costs_usd_real_2025_26": "official_staff_costs_usd_real_2025_26",
            "pages_used": "finance_pages_used",
            "classification_notes": "finance_classification_notes",
            "women_team_treatment_notes": "finance_women_team_treatment_notes",
            "non_football_revenue_notes": "finance_non_football_revenue_notes",
            "confidence_level": "finance_confidence_level",
            "requires_manual_review": "finance_requires_manual_review",
            "source_document": "finance_source_document",
            "source_url": "finance_source_url",
            "notes": "finance_notes",
            "economic_factor_notes": "finance_economic_factor_notes",
        }
    )
    return frame


def aggregate_performance(dataframe: pd.DataFrame) -> pd.DataFrame:
    frame = dataframe.copy()
    numeric_columns = [
        "league_position",
        "points",
        "wins",
        "draws",
        "losses",
        "goals_for",
        "goals_against",
        "goal_difference",
    ]
    for column in numeric_columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.rename(
        columns={
            "source_name": "performance_source_name",
            "source_url": "performance_source_url",
            "date_accessed": "performance_date_accessed",
            "evidence": "performance_evidence",
            "confidence_level": "performance_confidence_level",
            "notes": "performance_notes",
        }
    )
    return frame


def load_raw_premier_league_performance() -> pd.DataFrame | None:
    if not PREMIER_LEAGUE_RAW_PERFORMANCE_DIR.exists():
        print(f"[warn] Missing raw Premier League performance directory: {PREMIER_LEAGUE_RAW_PERFORMANCE_DIR}")
        return None

    combined_path = PREMIER_LEAGUE_RAW_PERFORMANCE_DIR / "premier_league_2008-09_to_2024-25_combined.csv"
    if combined_path.exists():
        frame = pd.read_csv(combined_path)
    else:
        frames = []
        for csv_path in sorted(PREMIER_LEAGUE_RAW_PERFORMANCE_DIR.glob("premier_league_*.csv")):
            if "combined" in csv_path.name:
                continue
            frames.append(pd.read_csv(csv_path))
        if not frames:
            print(f"[warn] No raw Premier League performance CSV files found in {PREMIER_LEAGUE_RAW_PERFORMANCE_DIR}")
            return None
        frame = pd.concat(frames, ignore_index=True)

    print(f"[load] raw_premier_league_performance: {PREMIER_LEAGUE_RAW_PERFORMANCE_DIR} ({len(frame)} rows)")
    team_to_club = {
        "Arsenal": "arsenal",
        "Chelsea": "chelsea",
        "Liverpool": "liverpool",
        "Manchester City": "manchester_city",
        "Manchester United": "manchester_united",
        "Tottenham Hotspur": "tottenham_hotspur",
    }

    frame = frame[frame["Team"].isin(team_to_club)].copy()
    frame["league_key"] = "premier_league"
    frame["league_name"] = "Premier League"
    frame["club_id"] = frame["Team"].map(team_to_club)
    frame["club_name"] = frame["Team"]
    frame["season"] = frame["season"].astype(str).str.strip()
    frame["season_start_year"] = pd.to_numeric(frame["season"].str.slice(0, 4), errors="coerce")
    frame["season_end_year"] = frame["season_start_year"] + 1

    frame = frame.rename(
        columns={
            "Pos": "league_position",
            "Pts": "points",
            "W": "wins",
            "D": "draws",
            "L": "losses",
            "GF": "goals_for",
            "GA": "goals_against",
            "GD": "goal_difference",
            "source_url": "performance_source_url",
        }
    )
    for column in ["league_position", "points", "wins", "draws", "losses", "goals_for", "goals_against", "goal_difference"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame["performance_source_name"] = "premier_league_raw_table"
    frame["performance_date_accessed"] = pd.NA
    frame["performance_evidence"] = "Raw Premier League season table CSV"
    frame["performance_confidence_level"] = "medium"
    frame["performance_notes"] = "League table data loaded from raw Premier League CSV files."

    return frame[
        [
            "league_key",
            "league_name",
            "club_id",
            "club_name",
            "season",
            "season_start_year",
            "season_end_year",
            "league_position",
            "points",
            "wins",
            "draws",
            "losses",
            "goals_for",
            "goals_against",
            "goal_difference",
            "performance_source_name",
            "performance_source_url",
            "performance_date_accessed",
            "performance_evidence",
            "performance_confidence_level",
            "performance_notes",
        ]
    ]


def merge_optional(base: pd.DataFrame, extra: pd.DataFrame | None, label: str) -> pd.DataFrame:
    if extra is None or extra.empty:
        print(f"[warn] {label} is empty and will not contribute rows.")
        return base
    join_keys = [
        key
        for key in [
            "league_key",
            "league_name",
            "club_id",
            "club_name",
            "season",
            "season_start_year",
            "season_end_year",
        ]
        if key in base.columns and key in extra.columns
    ]
    if len(join_keys) < 2:
        join_keys = [key for key in ["club_id", "season"] if key in base.columns and key in extra.columns]
    if len(join_keys) < 2:
        print(f"[warn] {label} missing join keys and will be skipped.")
        return base
    return base.merge(extra, on=join_keys, how="left", suffixes=("", f"_{label}"))


def add_derived_fields(dataframe: pd.DataFrame) -> pd.DataFrame:
    frame = dataframe.copy()

    numeric_columns = [
        "net_transfer_spend_eur",
        "points",
        "estimated_player_wages_eur",
        "official_staff_costs_eur",
        "official_staff_costs_original",
        "revenue_eur",
        "total_revenue_original",
        "matchday_revenue_eur",
        "matchday_revenue_original",
        "broadcast_revenue_eur",
        "broadcast_revenue_original",
        "commercial_revenue_eur",
        "commercial_revenue_original",
    ]
    for column in numeric_columns:
        if column not in frame.columns:
            frame[column] = pd.NA
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame["raw_player_cost_eur"] = frame["net_transfer_spend_eur"] + frame["estimated_player_wages_eur"]
    frame["cost_per_point"] = frame["raw_player_cost_eur"] / frame["points"]
    frame["wage_to_revenue_ratio"] = (
        frame["official_staff_costs_eur"] / frame["revenue_eur"]
    ).fillna(frame["official_staff_costs_original"] / frame["total_revenue_original"])
    frame["matchday_share"] = (
        frame["matchday_revenue_eur"] / frame["revenue_eur"]
    ).fillna(frame["matchday_revenue_original"] / frame["total_revenue_original"])
    frame["broadcast_share"] = (
        frame["broadcast_revenue_eur"] / frame["revenue_eur"]
    ).fillna(frame["broadcast_revenue_original"] / frame["total_revenue_original"])
    frame["commercial_share"] = (
        frame["commercial_revenue_eur"] / frame["revenue_eur"]
    ).fillna(frame["commercial_revenue_original"] / frame["total_revenue_original"])

    frame["has_performance_data"] = frame["points"].notna()
    frame["has_finance_data"] = frame["total_revenue_original"].notna() if "total_revenue_original" in frame.columns else False
    frame["has_achievement_data"] = frame["achievement_count_total"].fillna(0).gt(0) if "achievement_count_total" in frame.columns else False
    frame["has_manager_data"] = frame["primary_manager_name"].fillna("").astype(str).str.strip().ne("") if "primary_manager_name" in frame.columns else False
    return frame


def drop_redundant_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    frame = dataframe.copy()
    redundant_columns = [
        "league_name_manager_spells",
        "club_name_manager_spells",
        "league_name_achievements",
        "club_name_achievements",
        "season_start_year_achievements",
        "season_end_year_achievements",
        "club_name_finances",
    ]
    keep_columns = [column for column in frame.columns if column not in redundant_columns]
    return frame[keep_columns]


def filter_from_season(dataframe: pd.DataFrame, season_from: str) -> pd.DataFrame:
    if not season_from:
        return dataframe
    start_year = pd.to_numeric(str(season_from)[:4], errors="coerce")
    if pd.isna(start_year):
        print(f"[warn] Could not parse --season-from={season_from}; no season filter applied.")
        return dataframe
    return dataframe[dataframe["season_start_year"] >= int(start_year)].copy()


def write_per_league_exports(dataframe: pd.DataFrame, data_root: Path, frontend_root: Path) -> None:
    if dataframe.empty or "league_key" not in dataframe.columns:
        return
    data_root.mkdir(parents=True, exist_ok=True)
    frontend_root.mkdir(parents=True, exist_ok=True)

    for league_key, league_frame in dataframe.groupby("league_key", dropna=False):
        league_slug = str(league_key or "unknown_league")
        data_dir = data_root / league_slug
        frontend_dir = frontend_root / league_slug
        data_dir.mkdir(parents=True, exist_ok=True)
        frontend_dir.mkdir(parents=True, exist_ok=True)

        csv_path = data_dir / "club_season_master.csv"
        json_path = frontend_dir / "clubSeasonMasterData.json"
        league_frame.to_csv(csv_path, index=False)
        write_json(json_path, dataframe_to_json_records(league_frame))


def main() -> int:
    args = parse_args()
    output_csv = Path(args.output_csv)
    output_json = Path(args.output_json)
    league_output_root = Path(args.league_output_root)
    frontend_league_output_root = Path(args.frontend_league_output_root)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    economic_factors = load_economic_factors(Path(args.economic_factors_input))

    transfers = load_csv(TRANSFERS_PATH, "transfers", required=True)
    if transfers is None:
        return 1

    manager_spells = load_csv(MANAGER_SPELLS_PATH, "manager_spells")
    achievements = load_csv(ACHIEVEMENTS_PATH, "achievements")
    achievement_rows = load_csv(ACHIEVEMENT_ROWS_PATH, "achievement_rows")
    performance = load_csv(PERFORMANCE_PATH, "performance")
    finances = load_csv(FINANCE_PATH, "finances")
    raw_premier_league_performance = load_raw_premier_league_performance()

    master = aggregate_transfers(transfers)
    master = merge_optional(master, aggregate_manager_spells(manager_spells) if manager_spells is not None else None, "manager_spells")
    master = merge_optional(master, aggregate_achievements(achievements) if achievements is not None else None, "achievements")
    master = merge_optional(master, aggregate_achievement_rows(achievement_rows) if achievement_rows is not None else None, "achievement_rows")
    master = merge_optional(master, aggregate_performance(performance) if performance is not None else None, "performance")
    master = merge_optional(master, raw_premier_league_performance, "raw_premier_league_performance")
    master = merge_optional(
        master,
        aggregate_finances(finances, economic_factors) if finances is not None else None,
        "finances",
    )

    master = add_derived_fields(master)
    master = drop_redundant_columns(master)
    master = filter_from_season(master, args.season_from)
    master = master.sort_values(by=["league_key", "club_id", "season_start_year", "season"]).reset_index(drop=True)

    master.to_csv(output_csv, index=False)
    write_json(output_json, dataframe_to_json_records(master))
    write_per_league_exports(master, league_output_root, frontend_league_output_root)

    print(f"[saved] CSV: {output_csv}")
    print(f"[saved] JSON: {output_json}")
    print(f"[done] Exported {len(master)} club-season master rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
