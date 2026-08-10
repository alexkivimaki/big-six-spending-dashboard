#!/usr/bin/env python3

"""Export manager-season spend assignment using club-season overlap shares."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


TRANSFERS_PATH = Path("data/clean/transfermarkt/club_season_transfers_clean.csv")
MANAGER_SPELLS_PATH = Path("data/clean/transfermarkt/club_season_manager_spells_clean.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/final/manager_spend_assignment.csv")
    parser.add_argument("--league-output-root", default="data/final/by_league")
    return parser.parse_args()


def load_csv(path: Path, label: str) -> pd.DataFrame | None:
    if not path.exists():
        print(f"[warn] Missing required input for {label}: {path}")
        return None
    dataframe = pd.read_csv(path)
    print(f"[load] {label}: {path} ({len(dataframe)} rows)")
    return dataframe


def write_by_league(dataframe: pd.DataFrame, league_output_root: Path) -> None:
    if dataframe.empty:
        return
    for league_key, league_frame in dataframe.groupby("league_key", dropna=False):
        league_key = str(league_key or "unknown_league")
        league_dir = league_output_root / league_key
        league_dir.mkdir(parents=True, exist_ok=True)
        league_frame.to_csv(league_dir / "manager_spend_assignment.csv", index=False)


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)
    league_output_root = Path(args.league_output_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    league_output_root.mkdir(parents=True, exist_ok=True)

    transfers = load_csv(TRANSFERS_PATH, "transfers")
    manager_spells = load_csv(MANAGER_SPELLS_PATH, "manager_spells")
    if transfers is None or manager_spells is None:
        return 1

    join_keys = ["league_key", "club_id", "season"]
    merged = manager_spells.merge(
        transfers[
            [
                "league_key",
                "league_name",
                "club_id",
                "club_name",
                "season",
                "gross_transfer_spend_eur",
                "transfer_income_eur",
                "net_transfer_spend_eur",
                "incoming_transfer_count",
                "outgoing_transfer_count",
            ]
        ],
        on=join_keys,
        how="left",
        suffixes=("", "_transfer"),
    )

    for column in [
        "gross_transfer_spend_eur",
        "transfer_income_eur",
        "net_transfer_spend_eur",
        "incoming_transfer_count",
        "outgoing_transfer_count",
        "share_of_season",
    ]:
        if column in merged.columns:
            merged[column] = pd.to_numeric(merged[column], errors="coerce")

    merged["allocated_gross_transfer_spend_eur"] = merged["gross_transfer_spend_eur"] * merged["share_of_season"]
    merged["allocated_transfer_income_eur"] = merged["transfer_income_eur"] * merged["share_of_season"]
    merged["allocated_net_transfer_spend_eur"] = merged["net_transfer_spend_eur"] * merged["share_of_season"]
    merged["allocation_method"] = "season_day_overlap_prorated"
    merged["allocation_notes"] = (
        "Transfer totals are season-level club totals prorated by the share of season days the manager was in charge. "
        "This is useful for rough attribution but does not isolate actual transfer-window decision ownership."
    )

    merged.to_csv(output_path, index=False)
    write_by_league(merged, league_output_root)
    print(f"[saved] {output_path} ({len(merged)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
