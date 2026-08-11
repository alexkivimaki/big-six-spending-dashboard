"""Shared helpers for season-level FX and inflation factors."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ECONOMIC_FACTORS_PATH = Path("data/reference/economic_factors.csv")
REAL_PRICE_BASIS_LABEL = "2025/26 prices"

FACTOR_NUMERIC_COLUMNS = [
    "season_start_year",
    "season_end_year",
    "gbp_to_eur_rate",
    "eur_to_usd_rate",
    "gbp_to_usd_rate",
    "inflation_adjustment_to_2025_26",
]

FACTOR_COLUMNS = [
    "season",
    "season_start_year",
    "season_end_year",
    "gbp_to_eur_rate",
    "eur_to_usd_rate",
    "gbp_to_usd_rate",
    "inflation_adjustment_to_2025_26",
    "fx_source",
    "inflation_source",
    "notes",
]


def load_economic_factors(path: Path = ECONOMIC_FACTORS_PATH) -> pd.DataFrame:
    if not path.exists():
        print(f"[warn] Missing economic factors reference file: {path}")
        return pd.DataFrame(columns=FACTOR_COLUMNS + ["economic_factors_complete"])

    frame = pd.read_csv(path)
    for column in FACTOR_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA

    for column in FACTOR_NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame["season"] = frame["season"].astype(str).str.strip()

    missing_gbp_to_usd = (
        frame["gbp_to_usd_rate"].isna()
        & frame["gbp_to_eur_rate"].notna()
        & frame["eur_to_usd_rate"].notna()
    )
    frame.loc[missing_gbp_to_usd, "gbp_to_usd_rate"] = (
        frame.loc[missing_gbp_to_usd, "gbp_to_eur_rate"] * frame.loc[missing_gbp_to_usd, "eur_to_usd_rate"]
    )

    missing_eur_to_usd = (
        frame["eur_to_usd_rate"].isna()
        & frame["gbp_to_usd_rate"].notna()
        & frame["gbp_to_eur_rate"].notna()
        & frame["gbp_to_eur_rate"].ne(0)
    )
    frame.loc[missing_eur_to_usd, "eur_to_usd_rate"] = (
        frame.loc[missing_eur_to_usd, "gbp_to_usd_rate"] / frame.loc[missing_eur_to_usd, "gbp_to_eur_rate"]
    )

    missing_gbp_to_eur = (
        frame["gbp_to_eur_rate"].isna()
        & frame["gbp_to_usd_rate"].notna()
        & frame["eur_to_usd_rate"].notna()
        & frame["eur_to_usd_rate"].ne(0)
    )
    frame.loc[missing_gbp_to_eur, "gbp_to_eur_rate"] = (
        frame.loc[missing_gbp_to_eur, "gbp_to_usd_rate"] / frame.loc[missing_gbp_to_eur, "eur_to_usd_rate"]
    )

    frame["economic_factors_complete"] = (
        frame["gbp_to_eur_rate"].notna()
        & frame["eur_to_usd_rate"].notna()
        & frame["inflation_adjustment_to_2025_26"].notna()
    )
    return frame[FACTOR_COLUMNS + ["economic_factors_complete"]]


def merge_economic_factors(dataframe: pd.DataFrame, factors: pd.DataFrame) -> pd.DataFrame:
    frame = dataframe.copy()
    if "season" not in frame.columns:
        return frame

    if factors is None or factors.empty:
        for column in FACTOR_COLUMNS + ["economic_factors_complete"]:
            if column not in frame.columns:
                frame[column] = pd.NA
        return frame

    merged = frame.merge(
        factors,
        on="season",
        how="left",
        suffixes=("", "_economic_factors"),
    )
    for column in ["season_start_year", "season_end_year"]:
        duplicate = f"{column}_economic_factors"
        if duplicate not in merged.columns:
            continue
        if column not in merged.columns:
            merged[column] = merged[duplicate]
        else:
            merged[column] = merged[column].fillna(merged[duplicate])
        merged = merged.drop(columns=[duplicate])
    if "notes_economic_factors" in merged.columns and "economic_factor_notes" not in merged.columns:
        merged = merged.rename(columns={"notes_economic_factors": "economic_factor_notes"})
    return merged


def convert_amount(value, from_currency: str | None, to_currency: str, row: pd.Series):
    if pd.isna(value) or from_currency is None or to_currency is None:
        return None

    source_currency = str(from_currency).strip().upper()
    target_currency = str(to_currency).strip().upper()
    if not source_currency or source_currency == "NAN":
        return None
    if source_currency == target_currency:
        return float(value)

    gbp_to_eur = row.get("gbp_to_eur_rate")
    eur_to_usd = row.get("eur_to_usd_rate")
    gbp_to_usd = row.get("gbp_to_usd_rate")
    if pd.isna(gbp_to_usd) and pd.notna(gbp_to_eur) and pd.notna(eur_to_usd):
        gbp_to_usd = float(gbp_to_eur) * float(eur_to_usd)

    if source_currency == "GBP" and target_currency == "EUR":
        return float(value) * float(gbp_to_eur) if pd.notna(gbp_to_eur) else None
    if source_currency == "GBP" and target_currency == "USD":
        return float(value) * float(gbp_to_usd) if pd.notna(gbp_to_usd) else None
    if source_currency == "EUR" and target_currency == "GBP":
        if pd.notna(gbp_to_eur) and float(gbp_to_eur) != 0:
            return float(value) / float(gbp_to_eur)
        return None
    if source_currency == "EUR" and target_currency == "USD":
        return float(value) * float(eur_to_usd) if pd.notna(eur_to_usd) else None
    if source_currency == "USD" and target_currency == "EUR":
        if pd.notna(eur_to_usd) and float(eur_to_usd) != 0:
            return float(value) / float(eur_to_usd)
        return None
    if source_currency == "USD" and target_currency == "GBP":
        if pd.notna(gbp_to_usd) and float(gbp_to_usd) != 0:
            return float(value) / float(gbp_to_usd)
        return None
    return None


def add_currency_views(
    dataframe: pd.DataFrame,
    source_columns: list[str],
    *,
    currency_column: str | None = "currency_original",
    fixed_source_currency: str | None = None,
) -> pd.DataFrame:
    frame = dataframe.copy()

    def source_currency_for_row(row: pd.Series) -> str | None:
        if fixed_source_currency:
            return fixed_source_currency
        if currency_column and currency_column in row:
            return row.get(currency_column)
        return None

    for column in source_columns:
        if column not in frame.columns:
            frame[column] = pd.NA
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if column.endswith("_original"):
            prefix = column[: -len("_original")]
        elif column.endswith("_gbp"):
            prefix = column[: -len("_gbp")]
        elif column.endswith("_eur"):
            prefix = column[: -len("_eur")]
        elif column.endswith("_usd"):
            prefix = column[: -len("_usd")]
        else:
            prefix = column

        for target_currency in ("GBP", "EUR", "USD"):
            target_column = f"{prefix}_{target_currency.lower()}"
            frame[target_column] = frame.apply(
                lambda row: convert_amount(row[column], source_currency_for_row(row), target_currency, row),
                axis=1,
            )
            real_target_column = f"{prefix}_{target_currency.lower()}_real_2025_26"
            frame[real_target_column] = frame.apply(
                lambda row: (
                    row[target_column] * float(row["inflation_adjustment_to_2025_26"])
                    if pd.notna(row[target_column]) and pd.notna(row.get("inflation_adjustment_to_2025_26"))
                    else None
                ),
                axis=1,
            )

    frame["real_price_basis_label"] = REAL_PRICE_BASIS_LABEL
    return frame
