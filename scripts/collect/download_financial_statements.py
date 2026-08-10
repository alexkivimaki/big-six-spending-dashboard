#!/usr/bin/env python3

"""Download club financial statements from agent-produced source JSON files."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


USER_AGENT = "FootballFinanceDashboard/0.1 personal research project"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/ai_agents/statement_fetcher_outputs")
    parser.add_argument("--output", default="data/raw/financial_statements")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def safe_slug(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "_" for char in value)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "report"


def infer_extension(payload: dict, response: requests.Response) -> str:
    file_type = str(payload.get("file_type", "")).lower()
    if file_type in {"pdf", "html"}:
        return f".{file_type}"
    content_type = response.headers.get("content-type", "").lower()
    if "pdf" in content_type:
        return ".pdf"
    if "html" in content_type:
        return ".html"
    parsed = urlparse(payload.get("download_url", ""))
    suffix = Path(parsed.path).suffix
    return suffix or ".bin"


def season_slug(season: str) -> str:
    return season.replace("/", "_")


def download_one(payload: dict, output_root: Path, overwrite: bool, timeout: int) -> None:
    club_id = payload.get("club_id")
    season = payload.get("season")
    download_url = payload.get("download_url")
    if not club_id or not season or not download_url:
        print(f"[skip] Missing club_id, season, or download_url in payload: {payload}")
        return

    club_dir = output_root / club_id
    club_dir.mkdir(parents=True, exist_ok=True)
    safe_title = safe_slug(payload.get("report_title", "annual_report"))
    target_base = club_dir / f"{season_slug(season)}_{safe_title}"

    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(download_url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        print(f"[error] Failed to download {club_id} {season}: {exc}")
        return

    extension = infer_extension(payload, response)
    target_path = target_base.with_suffix(extension)
    meta_path = Path(str(target_path) + ".meta.json")

    if target_path.exists() and not overwrite:
        print(f"[skip] {target_path} already exists. Use --overwrite to replace it.")
        return

    if response.status_code >= 400:
        print(f"[error] HTTP {response.status_code} for {download_url}")
    else:
        target_path.write_bytes(response.content)
        print(f"[saved] {target_path}")

    metadata = {
        "club_id": club_id,
        "season": season,
        "source_url": payload.get("source_url", ""),
        "download_url": download_url,
        "date_downloaded_utc": datetime.now(timezone.utc).isoformat(),
        "status_code": response.status_code,
        "file_path": str(target_path),
        "original_agent_output_path": payload.get("_source_path", ""),
        "report_title": payload.get("report_title", ""),
        "report_type": payload.get("report_type", ""),
    }
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input)
    output_root = Path(args.output)

    json_files = sorted(
        path for path in input_dir.glob("*.json")
        if path.name != "example_output.json"
    )
    for path in json_files:
        payload = load_json(path)
        payload["_source_path"] = str(path)
        download_one(payload, output_root, args.overwrite, args.timeout)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
