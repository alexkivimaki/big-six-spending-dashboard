#!/usr/bin/env python3

"""Normalize raw Transfermarkt player transfer responses into player transfer rows."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import pandas as pd


OUTPUT_COLUMNS = [
    "transfer_id",
    "player_id",
    "player_name",
    "season",
    "window",
    "date",
    "buying_club_id",
    "buying_club_name",
    "selling_club_id",
    "selling_club_name",
    "fee_eur",
    "fee_type",
    "transfer_type",
    "position",
    "age",
    "source_name",
    "source_endpoint",
    "collected_at_utc",
    "confidence_level",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/transfermarkt/player_transfers")
    parser.add_argument("--output", default="data/clean/transfermarkt/player_transfers_clean.csv")
    return parser.parse_args()


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def clean_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def normalize_season_label(value: str | None) -> str:
    if not value:
        return ""
    text = str(value).strip()
    if re.fullmatch(r"\d{4}/\d{2}", text):
        return text
    if re.fullmatch(r"\d{2}/\d{2}", text):
        start_year = int(text[:2])
        century = 2000 if start_year < 50 else 1900
        return f"{century + start_year}/{text[-2:]}"
    return text


def parse_money(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        if math.isnan(value):
            return None
        return float(value)
    if isinstance(value, dict):
        for candidate_key in ("amount_eur", "eur", "amount", "value", "fee"):
            if candidate_key in value:
                parsed = parse_money(value[candidate_key])
                if parsed is not None:
                    return parsed
        return None

    text = str(value).strip()
    if not text:
        return None

    normalized = (
        text.replace("€", "")
        .replace("$", "")
        .replace("£", "")
        .replace(",", "")
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
    if "k" in normalized or "th" in normalized:
        return number * 1_000
    return number


def walk(obj):
    yield obj
    if isinstance(obj, dict):
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from walk(item)


def is_candidate_transfer(record: dict) -> bool:
    keys = {clean_key(key) for key in record.keys()}
    signals = {
        "date",
        "season",
        "fee",
        "fee_eur",
        "transfer_fee",
        "player_name",
        "player",
        "from_club",
        "to_club",
    }
    return len(keys & signals) >= 2


def collect_candidate_records(payload) -> list[dict]:
    records = []
    for item in walk(payload):
        if isinstance(item, dict) and is_candidate_transfer(item):
            records.append(item)
    return records


def pick_value(record: dict, aliases: list[str]):
    for alias in aliases:
        if alias in record and record[alias] not in ("", None):
            return record[alias]
    for value in record.values():
        if isinstance(value, dict):
            nested = pick_value(value, aliases)
            if nested not in ("", None):
                return nested
    return None


def parse_club_name(value):
    if isinstance(value, dict):
        return (
            value.get("name")
            or value.get("clubName")
            or value.get("club_name")
            or value.get("shortName")
            or value.get("short_name")
        )
    return value


def parse_club_id(value):
    if isinstance(value, dict):
        return value.get("id") or value.get("clubId") or value.get("club_id")
    return None


def normalize_record(record: dict, metadata: dict, index: int) -> dict:
    notes = []

    player_value = record.get("player") or record.get("playerName") or record.get("player_name")
    player_name = player_value.get("name") if isinstance(player_value, dict) else player_value
    player_id = (
        record.get("player_id")
        or record.get("playerId")
        or (player_value.get("id") if isinstance(player_value, dict) else None)
        or metadata.get("player_id")
    )

    buying_value = pick_value(record, ["toClub", "to_club", "buyingClub", "clubTo", "club_to"])
    selling_value = pick_value(record, ["fromClub", "from_club", "sellingClub", "clubFrom", "club_from"])
    fee_raw = pick_value(record, ["fee", "fee_eur", "transferFee", "transfer_fee", "market_value"])
    fee_value = parse_money(fee_raw)

    if fee_raw not in ("", None) and fee_value is None:
        notes.append("Fee value present but could not be parsed automatically.")

    row = {
        "transfer_id": record.get("transfer_id") or record.get("transferId") or record.get("id") or "",
        "player_id": player_id or "",
        "player_name": player_name or metadata.get("player_name", ""),
        "season": normalize_season_label(pick_value(record, ["season", "seasonName"]) or ""),
        "window": pick_value(record, ["window", "transfer_window"]) or "",
        "date": pick_value(record, ["date", "transferDate"]) or "",
        "buying_club_id": parse_club_id(buying_value) or "",
        "buying_club_name": parse_club_name(buying_value) or "",
        "selling_club_id": parse_club_id(selling_value) or "",
        "selling_club_name": parse_club_name(selling_value) or "",
        "fee_eur": fee_value,
        "fee_type": pick_value(record, ["fee_type", "feeType"]) or "",
        "transfer_type": pick_value(record, ["transfer_type", "transferType", "type"]) or "",
        "position": pick_value(record, ["position", "mainPosition"]) or "",
        "age": pick_value(record, ["age"]) or "",
        "source_name": metadata.get("source_name", "transfermarkt_api"),
        "source_endpoint": metadata.get("endpoint_url", ""),
        "collected_at_utc": metadata.get("collected_at_utc", ""),
        "confidence_level": "medium",
        "notes": " ".join(notes),
    }

    if not row["transfer_id"]:
        row["notes"] = (row["notes"] + " Synthetic transfer_id not provided by source.").strip()
        row["transfer_id"] = f"{row['player_id'] or 'unknown_player'}_{index}"
        row["confidence_level"] = "low"

    return row


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    raw_files = sorted(path for path in input_dir.glob("*.json") if not path.name.endswith(".meta.json"))

    if not raw_files:
        print(f"[warn] No raw JSON files found in {input_dir}")

    for raw_path in raw_files:
        meta_path = raw_path.with_suffix("").with_suffix(".meta.json")
        if not meta_path.exists():
            print(f"[warn] Missing metadata sidecar for {raw_path.name}; skipping file.")
            continue

        payload = load_json(raw_path)
        metadata = load_json(meta_path)
        candidates = collect_candidate_records(payload)

        if not candidates:
            print(f"[warn] No transfer-like records detected in {raw_path.name}")
            continue

        for index, record in enumerate(candidates, start=1):
            rows.append(normalize_record(record, metadata, index))

    dataframe = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    dataframe.to_csv(output_path, index=False)
    print(f"[saved] {output_path} ({len(dataframe)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
