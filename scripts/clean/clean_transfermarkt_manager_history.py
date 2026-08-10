#!/usr/bin/env python3

"""Parse saved Transfermarkt manager history pages into clean manager-era outputs."""

from __future__ import annotations

import argparse
import html as html_lib
import json
import math
import re
from datetime import UTC, date, datetime
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

MANAGER_HISTORY_COLUMNS = [
    "league_key",
    "league_name",
    "club_id",
    "club_name",
    "role_key",
    "role_name",
    "transfermarkt_manager_id",
    "manager_id",
    "manager_name",
    "manager_date_of_birth",
    "nationalities",
    "start_date",
    "end_date",
    "time_in_post_text",
    "time_in_post_days",
    "matches",
    "wins",
    "draws",
    "losses",
    "ppg",
    "source_name",
    "source_endpoint",
    "collected_at_utc",
    "confidence_level",
    "notes",
]

CLUB_SEASON_MANAGER_COLUMNS = [
    "league_key",
    "league_name",
    "club_id",
    "club_name",
    "role_key",
    "role_name",
    "season",
    "season_start_year",
    "season_end_year",
    "transfermarkt_manager_id",
    "manager_id",
    "manager_name",
    "manager_date_of_birth",
    "nationalities",
    "spell_start_date",
    "spell_end_date",
    "time_in_post_text",
    "time_in_post_days",
    "matches",
    "wins",
    "draws",
    "losses",
    "ppg",
    "overlap_start_date",
    "overlap_end_date",
    "days_in_charge_in_season",
    "days_in_season",
    "share_of_season",
    "source_name",
    "source_endpoint",
    "collected_at_utc",
    "confidence_level",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/transfermarkt/manager_history_pages")
    parser.add_argument("--seasons", default="config/seasons.json")
    parser.add_argument("--history-output", default="data/clean/transfermarkt/manager_history_clean.csv")
    parser.add_argument(
        "--season-output",
        default="data/clean/transfermarkt/club_season_manager_spells_clean.csv",
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
    filename = html_path.name
    if not enriched.get("role_key"):
        if "_caretaker_manager_history_" in filename:
            enriched["role_key"] = "caretaker_manager"
            enriched["role_name"] = "Caretaker Manager"
        elif "_manager_history_" in filename:
            enriched["role_key"] = "manager"
            enriched["role_name"] = "Manager"

    return enriched


def find_manager_history_table(tables: list[pd.DataFrame]) -> pd.DataFrame | None:
    required = {"Name/Date of birth", "Appointed", "End of time in post", "Time in post", "Matches", "PPG"}
    for table in tables:
        columns = {str(column) for column in table.columns}
        if required.issubset(columns):
            return table
    return None


def strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value).strip()


def parse_date(value) -> date | None:
    text = clean_text(value)
    if not text:
        return None
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        return None


def parse_any_date(value) -> date | None:
    text = clean_text(value)
    if not text:
        return None
    for parser in (date.fromisoformat, lambda raw: datetime.strptime(raw, "%d/%m/%Y").date()):
        try:
            return parser(text)
        except ValueError:
            continue
    return None


def parse_numeric(value):
    text = clean_text(value)
    if not text:
        return None
    normalized = text.replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", normalized)
    if not match:
        return None
    return float(match.group())


def parse_time_in_post_days(value) -> int | None:
    numeric = parse_numeric(value)
    return int(numeric) if numeric is not None else None


def parse_count(value) -> int | None:
    text = clean_text(value)
    if not text or text == "-":
        return 0 if text == "-" else None
    numeric = parse_numeric(text)
    return int(numeric) if numeric is not None else None


def derive_spell_days(start_date: date | None, end_date: date | None, collected_at_utc: str) -> int | None:
    if start_date is None:
        return None
    effective_end = end_date
    if effective_end is None:
        collected_date = parse_any_date(clean_text(collected_at_utc).split("T")[0])
        effective_end = collected_date
    if effective_end is None or effective_end < start_date:
        return None
    return (effective_end - start_date).days + 1


def split_name_and_birth(name_birth_text: str) -> tuple[str, str]:
    text = clean_text(name_birth_text)
    match = re.search(r"(\d{2}/\d{2}/\d{4})$", text)
    if not match:
        return text, ""
    birth_date = match.group(1)
    manager_name = text[: match.start()].strip()
    return manager_name, birth_date


def make_manager_id(manager_name: str, birth_date: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", manager_name.lower()).strip("_")
    dob = birth_date.replace("/", "-") if birth_date else "unknown_dob"
    return f"{base}_{dob}" if base else f"unknown_manager_{dob}"


def parse_manager_history_html(html: str, metadata: dict) -> list[dict]:
    rows = []
    pattern = re.compile(
        r'<tr class="(?:odd|even)">\s*'
        r'<td><table class=inline-table>.*?'
        r'<a title="(?P<manager_name>[^"]+)" id="(?P<trainer_id>\d+)" href="[^"]+">.*?</a>'
        r'.*?<tr><td>(?P<dob>[^<]*)</td></tr></table></td>'
        r'<td class="zentriert">(?P<nat_html>.*?)</td>'
        r'<td class="zentriert">(?P<appointed>[^<]*)</td>'
        r'<td class="zentriert">(?P<end>[^<]*)</td>'
        r'<td class="rechts">(?P<time_in_post>[^<]*)</td>'
        r'<td class="zentriert">(?:<a [^>]*>)?(?P<matches>[^<]*)(?:</a>)?</td>'
        r'<td class="zentriert">(?P<wins>[^<]*)</td>'
        r'<td class="zentriert">(?P<draws>[^<]*)</td>'
        r'<td class="zentriert">(?P<losses>[^<]*)</td>'
        r'<td class="zentriert">(?P<ppg>[^<]*)</td>\s*</tr>',
        re.S,
    )

    for match in pattern.finditer(html):
        manager_name = html_lib.unescape(clean_text(match.group("manager_name")))
        manager_birth = clean_text(match.group("dob"))
        nat_values = [html_lib.unescape(value).strip() for value in re.findall(r'alt="([^"]+)"', match.group("nat_html"))]
        nationalities = " | ".join(dict.fromkeys(value for value in nat_values if value))
        appointed = parse_date(match.group("appointed"))
        end_date = parse_date(match.group("end"))
        if appointed is None:
            continue

        notes = []
        if end_date is None:
            notes.append("Manager spell appears ongoing on the collection date.")

        rows.append(
            {
                "league_key": metadata.get("league_key", ""),
                "league_name": metadata.get("league_name", ""),
                "club_id": metadata.get("club_id", ""),
                "club_name": metadata.get("club_name", ""),
                "role_key": metadata.get("role_key", "manager"),
                "role_name": metadata.get("role_name", "Manager"),
                "transfermarkt_manager_id": clean_text(match.group("trainer_id")),
                "manager_id": make_manager_id(manager_name, manager_birth),
                "manager_name": manager_name,
                "manager_date_of_birth": manager_birth,
                "nationalities": nationalities,
                "start_date": appointed.isoformat(),
                "end_date": end_date.isoformat() if end_date else "",
                "time_in_post_text": clean_text(match.group("time_in_post")),
                "time_in_post_days": derive_spell_days(
                    appointed,
                    end_date,
                    metadata.get("collected_at_utc", ""),
                ),
                "matches": parse_numeric(match.group("matches")),
                "wins": parse_count(match.group("wins")),
                "draws": parse_count(match.group("draws")),
                "losses": parse_count(match.group("losses")),
                "ppg": parse_numeric(match.group("ppg")),
                "source_name": metadata.get("source_name", "transfermarkt_manager_history_page"),
                "source_endpoint": metadata.get("source_url", ""),
                "collected_at_utc": metadata.get("collected_at_utc", ""),
                "confidence_level": "high",
                "notes": " ".join(notes),
            }
        )

    return rows


def parse_manager_history_table(table: pd.DataFrame, metadata: dict) -> list[dict]:
    rows = []

    for _, row in table.iterrows():
        appointed = parse_date(row.get("Appointed"))
        if appointed is None:
            continue

        manager_name, manager_birth = split_name_and_birth(clean_text(row.get("Name/Date of birth")))
        end_date = parse_date(row.get("End of time in post"))
        notes = []
        if not manager_name:
            notes.append("Could not parse manager_name from manager history page row.")
        if end_date is None:
            notes.append("Manager spell appears ongoing on the collection date.")

        rows.append(
            {
                "league_key": metadata.get("league_key", ""),
                "league_name": metadata.get("league_name", ""),
                "club_id": metadata.get("club_id", ""),
                "club_name": metadata.get("club_name", ""),
                "role_key": metadata.get("role_key", "manager"),
                "role_name": metadata.get("role_name", "Manager"),
                "manager_id": make_manager_id(manager_name, manager_birth),
                "manager_name": manager_name,
                "manager_date_of_birth": manager_birth,
                "nationalities": "",
                "start_date": appointed.isoformat(),
                "end_date": end_date.isoformat() if end_date else "",
                "time_in_post_text": clean_text(row.get("Time in post")),
                "time_in_post_days": derive_spell_days(
                    appointed,
                    end_date,
                    metadata.get("collected_at_utc", ""),
                ),
                "matches": parse_numeric(row.get("Matches")),
                "wins": parse_count(row.get("W")) if "W" in row.index else None,
                "draws": parse_count(row.get("D")) if "D" in row.index else None,
                "losses": parse_count(row.get("L")) if "L" in row.index else None,
                "ppg": parse_numeric(row.get("PPG")),
                "source_name": metadata.get("source_name", "transfermarkt_manager_history_page"),
                "source_endpoint": metadata.get("source_url", ""),
                "collected_at_utc": metadata.get("collected_at_utc", ""),
                "confidence_level": "high",
                "notes": " ".join(notes),
            }
        )

    return rows


def season_bounds(season: dict) -> tuple[date, date]:
    return date(int(season["season_start_year"]), 7, 1), date(int(season["season_end_year"]), 6, 30)


def overlap_days(start_a: date, end_a: date, start_b: date, end_b: date) -> tuple[date, date, int] | None:
    overlap_start = max(start_a, start_b)
    overlap_end = min(end_a, end_b)
    if overlap_start > overlap_end:
        return None
    return overlap_start, overlap_end, (overlap_end - overlap_start).days + 1


def build_club_season_manager_rows(history_rows: list[dict], seasons: list[dict]) -> list[dict]:
    output = []
    today = datetime.now(UTC).date()

    for history_row in history_rows:
        spell_start = parse_any_date(history_row["start_date"])
        spell_end = parse_any_date(history_row["end_date"]) if history_row["end_date"] else today
        if spell_start is None or spell_end is None:
            continue

        for season in seasons:
            season_start, season_end = season_bounds(season)
            overlap = overlap_days(spell_start, spell_end, season_start, season_end)
            if overlap is None:
                continue

            overlap_start, overlap_end, days_in_charge = overlap
            days_in_season = (season_end - season_start).days + 1
            notes = []
            if not history_row["end_date"]:
                notes.append("Ongoing manager spell; overlap calculated through the collection date or season end.")

            output.append(
                {
                    "league_key": history_row["league_key"],
                    "league_name": history_row["league_name"],
                    "club_id": history_row["club_id"],
                    "club_name": history_row["club_name"],
                    "role_key": history_row["role_key"],
                    "role_name": history_row["role_name"],
                    "season": season["season"],
                    "season_start_year": season["season_start_year"],
                    "season_end_year": season["season_end_year"],
                    "transfermarkt_manager_id": history_row["transfermarkt_manager_id"],
                    "manager_id": history_row["manager_id"],
                    "manager_name": history_row["manager_name"],
                    "manager_date_of_birth": history_row["manager_date_of_birth"],
                    "nationalities": history_row["nationalities"],
                    "spell_start_date": history_row["start_date"],
                    "spell_end_date": history_row["end_date"],
                    "time_in_post_text": history_row["time_in_post_text"],
                    "time_in_post_days": history_row["time_in_post_days"],
                    "matches": history_row["matches"],
                    "wins": history_row["wins"],
                    "draws": history_row["draws"],
                    "losses": history_row["losses"],
                    "ppg": history_row["ppg"],
                    "overlap_start_date": overlap_start.isoformat(),
                    "overlap_end_date": overlap_end.isoformat(),
                    "days_in_charge_in_season": days_in_charge,
                    "days_in_season": days_in_season,
                    "share_of_season": days_in_charge / days_in_season,
                    "source_name": history_row["source_name"],
                    "source_endpoint": history_row["source_endpoint"],
                    "collected_at_utc": history_row["collected_at_utc"],
                    "confidence_level": history_row["confidence_level"],
                    "notes": " ".join(filter(None, [history_row.get("notes", ""), " ".join(notes)])).strip(),
                }
            )

    return output


def write_by_league(dataframe: pd.DataFrame, league_output_root: Path, filename: str) -> None:
    if "league_key" not in dataframe.columns or dataframe.empty:
        return

    for league_key, league_frame in dataframe.groupby("league_key", dropna=False):
        league_key = str(league_key or "unknown_league")
        league_dir = league_output_root / league_key
        league_dir.mkdir(parents=True, exist_ok=True)
        league_frame.to_csv(league_dir / filename, index=False)


def write_partitioned_season_manager_rows(dataframe: pd.DataFrame, partition_output_root: Path) -> None:
    if dataframe.empty:
        return

    for _, row in dataframe.iterrows():
        league_key = str(row.get("league_key") or "unknown_league")
        club_id = str(row.get("club_id") or "unknown_club")
        season_label = str(row.get("season") or "")
        season_dir = season_label.replace("/", "_") if season_label else "unknown_season"
        partition_dir = partition_output_root / league_key / season_dir / club_id
        partition_dir.mkdir(parents=True, exist_ok=True)

        partition_path = partition_dir / f"{club_id}_{season_dir}_club_season_manager_spells_clean.csv"
        slice_df = dataframe[
            (dataframe["league_key"] == row.get("league_key"))
            & (dataframe["club_id"] == row.get("club_id"))
            & (dataframe["season"] == row.get("season"))
        ]
        slice_df.to_csv(partition_path, index=False)


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input)
    seasons = load_json(Path(args.seasons))
    history_output_path = Path(args.history_output)
    season_output_path = Path(args.season_output)
    league_output_root = Path(args.league_output_root)
    partition_output_root = Path(args.partition_output_root)
    history_output_path.parent.mkdir(parents=True, exist_ok=True)
    season_output_path.parent.mkdir(parents=True, exist_ok=True)
    league_output_root.mkdir(parents=True, exist_ok=True)
    partition_output_root.mkdir(parents=True, exist_ok=True)

    history_rows: list[dict] = []
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
        parsed_rows = parse_manager_history_html(html, metadata)
        if parsed_rows:
            history_rows.extend(parsed_rows)
            continue

        try:
            tables = pd.read_html(StringIO(html))
        except ValueError:
            print(f"[warn] No HTML tables found in {html_path.name}")
            continue

        manager_table = find_manager_history_table(tables)
        if manager_table is None:
            print(f"[warn] Could not find manager history table in {html_path.name}")
            continue

        history_rows.extend(parse_manager_history_table(manager_table, metadata))

    history_dataframe = pd.DataFrame(history_rows, columns=MANAGER_HISTORY_COLUMNS)
    if not history_dataframe.empty:
        history_dataframe = history_dataframe.sort_values(
            by=["league_key", "club_id", "start_date"],
            kind="stable",
        )

    season_rows = build_club_season_manager_rows(
        history_dataframe.to_dict(orient="records"),
        seasons,
    )
    season_dataframe = pd.DataFrame(season_rows, columns=CLUB_SEASON_MANAGER_COLUMNS)
    if not season_dataframe.empty:
        season_dataframe = season_dataframe.sort_values(
            by=["league_key", "club_id", "season_start_year", "overlap_start_date"],
            kind="stable",
        )

    history_dataframe.to_csv(history_output_path, index=False)
    season_dataframe.to_csv(season_output_path, index=False)
    write_by_league(history_dataframe, league_output_root, "manager_history_clean.csv")
    write_by_league(season_dataframe, league_output_root, "club_season_manager_spells_clean.csv")
    write_partitioned_season_manager_rows(season_dataframe, partition_output_root)

    print(f"[saved] {history_output_path} ({len(history_dataframe)} rows)")
    print(f"[saved] {season_output_path} ({len(season_dataframe)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
