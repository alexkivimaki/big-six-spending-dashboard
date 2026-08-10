#!/usr/bin/env python3

"""Parse saved Transfermarkt achievements pages into season-level trophy data."""

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

ACHIEVEMENT_ROWS_COLUMNS = [
    "league_key",
    "league_name",
    "club_id",
    "club_name",
    "achievement_season_label",
    "assigned_season",
    "assigned_season_start_year",
    "assigned_season_end_year",
    "achievement_name",
    "achievement_category",
    "achievement_result",
    "is_major_trophy",
    "assignment_method",
    "assignment_confidence",
    "source_name",
    "source_endpoint",
    "collected_at_utc",
    "notes",
]

CLUB_SEASON_ACHIEVEMENTS_COLUMNS = [
    "league_key",
    "league_name",
    "club_id",
    "club_name",
    "season",
    "season_start_year",
    "season_end_year",
    "achievement_count_total",
    "major_trophy_count",
    "achievement_names",
    "major_trophies",
    "source_name",
    "source_endpoint",
    "collected_at_utc",
    "confidence_level",
    "notes",
]

MAJOR_TROPHY_KEYWORDS = (
    "champion",
    "winner",
    "cup winner",
    "supercup winner",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/transfermarkt/achievement_pages")
    parser.add_argument("--seasons", default="config/seasons.json")
    parser.add_argument("--rows-output", default="data/clean/transfermarkt/achievement_rows_clean.csv")
    parser.add_argument(
        "--season-output",
        default="data/clean/transfermarkt/club_season_achievements_clean.csv",
    )
    parser.add_argument("--league-output-root", default="data/clean/transfermarkt/by_league")
    parser.add_argument("--partition-output-root", default="data/clean/transfermarkt/by_partition")
    return parser.parse_args()


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def clean_text(value) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def enrich_metadata_from_path(metadata: dict, html_path: Path, input_dir: Path) -> dict:
    enriched = dict(metadata)
    try:
        relative_parts = html_path.relative_to(input_dir).parts
    except ValueError:
        return enriched

    if len(relative_parts) >= 3:
        enriched.setdefault("league_key", relative_parts[0])
        enriched.setdefault("club_id", relative_parts[2])

    if not enriched.get("league_name") and enriched.get("league_key"):
        enriched["league_name"] = LEAGUE_NAME_MAP.get(
            str(enriched["league_key"]),
            str(enriched["league_key"]).replace("_", " ").title(),
        )

    return enriched


def parse_assignment(label: str, valid_seasons: set[str]) -> tuple[str, int | None, int | None, str, str]:
    label = clean_text(label)
    if re.fullmatch(r"\d{2}/\d{2}", label):
        two_digit_year = int(label[:2])
        candidate_years = [1900 + two_digit_year, 2000 + two_digit_year]
        for start_year in candidate_years:
            season = f"{start_year}/{label[-2:]}"
            if season in valid_seasons:
                return season, start_year, start_year + 1, "season_label_expanded", "high"

        start_year = 2000 + two_digit_year if two_digit_year <= 29 else 1900 + two_digit_year
        season = f"{start_year}/{label[-2:]}"
        return season, start_year, start_year + 1, "season_label_expanded_fallback", "medium"

    if re.fullmatch(r"\d{4}/\d{2}", label):
        start_year = int(label[:4])
        confidence = "high" if label in valid_seasons else "medium"
        return label, start_year, start_year + 1, "season_label_preserved", confidence

    if re.fullmatch(r"\d{4}", label):
        year = int(label)
        season = f"{year}/{str((year + 1) % 100).zfill(2)}"
        confidence = "medium" if season in valid_seasons else "low"
        return season, year, year + 1, "calendar_year_mapped_to_start_year_season", confidence

    return "", None, None, "unassigned", "low"


def classify_achievement(name: str) -> tuple[str, str, bool]:
    text = clean_text(name)
    lowered = text.lower()

    if "runner up" in lowered:
        result = "runner_up"
    elif "participant" in lowered:
        result = "participant"
    elif "winner" in lowered or "champion" in lowered:
        result = "winner"
    else:
        result = "other"

    if "champions league" in lowered:
        category = "uefa_champions_league"
    elif "europa league" in lowered:
        category = "uefa_europa_league"
    elif "conference league" in lowered:
        category = "uefa_conference_league"
    elif "supercup" in lowered:
        category = "super_cup"
    elif "fa cup" in lowered:
        category = "fa_cup"
    elif "league cup" in lowered or "efl cup" in lowered:
        category = "league_cup"
    elif "club world cup" in lowered:
        category = "club_world_cup"
    elif "champion" in lowered:
        category = "league_title"
    else:
        category = "other"

    is_major = result == "winner" and any(keyword in lowered for keyword in MAJOR_TROPHY_KEYWORDS)
    return category, result, is_major


def parse_achievement_rows_from_html(html: str, metadata: dict, valid_seasons: set[str]) -> list[dict]:
    rows = []
    pattern = re.compile(
        r'<tr>\s*'
        r'<td class="zentriert">(?P<label>[^<]+)</td>\s*'
        r'<td[^>]*class="zentriert no-border-rechts"[^>]*>.*?</td>\s*'
        r'<td class="no-border-links">(?P<name>[^<]+)</td>\s*'
        r'</tr>',
        re.S,
    )

    for match in pattern.finditer(html):
        raw_label = clean_text(match.group("label"))
        achievement_name = clean_text(match.group("name"))
        if not raw_label or not achievement_name:
            continue

        assigned_season, start_year, end_year, method, confidence = parse_assignment(raw_label, valid_seasons)
        category, result, is_major = classify_achievement(achievement_name)
        notes = []
        if confidence != "high":
            notes.append(
                f"Assigned season derived from achievement season label '{raw_label}' using method '{method}'."
            )

        rows.append(
            {
                "league_key": metadata.get("league_key", ""),
                "league_name": metadata.get("league_name", ""),
                "club_id": metadata.get("club_id", ""),
                "club_name": metadata.get("club_name", ""),
                "achievement_season_label": raw_label,
                "assigned_season": assigned_season,
                "assigned_season_start_year": start_year,
                "assigned_season_end_year": end_year,
                "achievement_name": achievement_name,
                "achievement_category": category,
                "achievement_result": result,
                "is_major_trophy": is_major,
                "assignment_method": method,
                "assignment_confidence": confidence,
                "source_name": metadata.get("source_name", "transfermarkt_achievements_page"),
                "source_endpoint": metadata.get("source_url", ""),
                "collected_at_utc": metadata.get("collected_at_utc", ""),
                "notes": " ".join(notes),
            }
        )

    return rows


def join_unique(series: pd.Series) -> str:
    values = []
    for value in series.dropna():
        text = clean_text(value)
        if text and text not in values:
            values.append(text)
    return " | ".join(values)


def parse_achievement_table(table: pd.DataFrame, metadata: dict, valid_seasons: set[str]) -> list[dict]:
    rows = []

    if "Season" not in table.columns:
        return rows

    title_column = "Title.1" if "Title.1" in table.columns else "Title"
    for _, row in table.iterrows():
        raw_label = clean_text(row.get("Season"))
        achievement_name = clean_text(row.get(title_column))
        if not raw_label or not achievement_name:
            continue

        assigned_season, start_year, end_year, method, confidence = parse_assignment(raw_label, valid_seasons)
        category, result, is_major = classify_achievement(achievement_name)
        notes = []
        if confidence != "high":
            notes.append(
                f"Assigned season derived from achievement season label '{raw_label}' using method '{method}'."
            )

        rows.append(
            {
                "league_key": metadata.get("league_key", ""),
                "league_name": metadata.get("league_name", ""),
                "club_id": metadata.get("club_id", ""),
                "club_name": metadata.get("club_name", ""),
                "achievement_season_label": raw_label,
                "assigned_season": assigned_season,
                "assigned_season_start_year": start_year,
                "assigned_season_end_year": end_year,
                "achievement_name": achievement_name,
                "achievement_category": category,
                "achievement_result": result,
                "is_major_trophy": is_major,
                "assignment_method": method,
                "assignment_confidence": confidence,
                "source_name": metadata.get("source_name", "transfermarkt_achievements_page"),
                "source_endpoint": metadata.get("source_url", ""),
                "collected_at_utc": metadata.get("collected_at_utc", ""),
                "notes": " ".join(notes),
            }
        )

    return rows


def write_by_league(dataframe: pd.DataFrame, league_output_root: Path, filename: str) -> None:
    if "league_key" not in dataframe.columns or dataframe.empty:
        return
    for league_key, league_frame in dataframe.groupby("league_key", dropna=False):
        league_key = str(league_key or "unknown_league")
        league_dir = league_output_root / league_key
        league_dir.mkdir(parents=True, exist_ok=True)
        league_frame.to_csv(league_dir / filename, index=False)


def write_partitioned_season_rows(dataframe: pd.DataFrame, partition_output_root: Path) -> None:
    if dataframe.empty:
        return
    for _, row in dataframe.iterrows():
        league_key = str(row.get("league_key") or "unknown_league")
        club_id = str(row.get("club_id") or "unknown_club")
        season = clean_text(row.get("season"))
        season_dir = season.replace("/", "_") if season else "unknown_season"
        partition_dir = partition_output_root / league_key / season_dir / club_id
        partition_dir.mkdir(parents=True, exist_ok=True)
        output_path = partition_dir / f"{club_id}_{season_dir}_club_season_achievements_clean.csv"
        slice_df = dataframe[
            (dataframe["league_key"] == row.get("league_key"))
            & (dataframe["club_id"] == row.get("club_id"))
            & (dataframe["season"] == row.get("season"))
        ]
        slice_df.to_csv(output_path, index=False)


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input)
    seasons = load_json(Path(args.seasons))
    valid_seasons = {item["season"] for item in seasons}
    rows_output_path = Path(args.rows_output)
    season_output_path = Path(args.season_output)
    league_output_root = Path(args.league_output_root)
    partition_output_root = Path(args.partition_output_root)
    rows_output_path.parent.mkdir(parents=True, exist_ok=True)
    season_output_path.parent.mkdir(parents=True, exist_ok=True)
    league_output_root.mkdir(parents=True, exist_ok=True)
    partition_output_root.mkdir(parents=True, exist_ok=True)

    achievement_rows: list[dict] = []
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
        parsed_rows = parse_achievement_rows_from_html(html, metadata, valid_seasons)
        if parsed_rows:
            achievement_rows.extend(parsed_rows)
            continue

        try:
            tables = pd.read_html(StringIO(html))
        except ValueError:
            print(f"[warn] No HTML tables found in {html_path.name}")
            continue

        if not tables:
            print(f"[warn] No achievement tables found in {html_path.name}")
            continue

        achievement_rows.extend(parse_achievement_table(tables[0], metadata, valid_seasons))

    rows_dataframe = pd.DataFrame(achievement_rows, columns=ACHIEVEMENT_ROWS_COLUMNS)
    if not rows_dataframe.empty:
        rows_dataframe = rows_dataframe.sort_values(
            by=["league_key", "club_id", "assigned_season_start_year", "achievement_name"],
            kind="stable",
        )

    season_dataframe = pd.DataFrame(columns=CLUB_SEASON_ACHIEVEMENTS_COLUMNS)
    if not rows_dataframe.empty:
        grouped = (
            rows_dataframe.groupby(
                [
                    "league_key",
                    "league_name",
                    "club_id",
                    "club_name",
                    "assigned_season",
                    "assigned_season_start_year",
                    "assigned_season_end_year",
                ],
                dropna=False,
            )
            .agg(
                achievement_count_total=("achievement_name", "count"),
                major_trophy_count=("is_major_trophy", "sum"),
                achievement_names=("achievement_name", join_unique),
                major_trophies=(
                    "achievement_name",
                    lambda series: join_unique(
                        pd.Series(
                            [
                                value
                                for value, is_major in zip(
                                    series,
                                    rows_dataframe.loc[series.index, "is_major_trophy"],
                                )
                                if bool(is_major)
                            ]
                        )
                    ),
                ),
                source_name=("source_name", join_unique),
                source_endpoint=("source_endpoint", join_unique),
                collected_at_utc=("collected_at_utc", "first"),
                notes=("notes", join_unique),
            )
            .reset_index()
            .rename(
                columns={
                    "assigned_season": "season",
                    "assigned_season_start_year": "season_start_year",
                    "assigned_season_end_year": "season_end_year",
                }
            )
        )
        grouped["confidence_level"] = grouped["notes"].apply(lambda value: "medium" if clean_text(value) else "high")
        season_dataframe = grouped[CLUB_SEASON_ACHIEVEMENTS_COLUMNS]
        season_dataframe = season_dataframe.sort_values(
            by=["league_key", "club_id", "season_start_year"],
            kind="stable",
        )

    rows_dataframe.to_csv(rows_output_path, index=False)
    season_dataframe.to_csv(season_output_path, index=False)
    write_by_league(rows_dataframe, league_output_root, "achievement_rows_clean.csv")
    write_by_league(season_dataframe, league_output_root, "club_season_achievements_clean.csv")
    write_partitioned_season_rows(season_dataframe, partition_output_root)

    print(f"[saved] {rows_output_path} ({len(rows_dataframe)} rows)")
    print(f"[saved] {season_output_path} ({len(season_dataframe)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
