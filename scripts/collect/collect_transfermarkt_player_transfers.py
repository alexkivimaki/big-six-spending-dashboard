#!/usr/bin/env python3

"""Collect raw player transfer history from a local Transfermarkt API service."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/transfermarkt_api.example.json")
    parser.add_argument("--player-id", required=True)
    parser.add_argument("--output", default="data/raw/transfermarkt/player_transfers")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_json(Path(args.config))
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    endpoint = config["player_transfers_endpoint_template"].format(
        transfermarkt_player_id=args.player_id
    )
    url = f"{normalize_base_url(config['base_url'])}{endpoint}"
    collected_at = datetime.now(timezone.utc).isoformat()
    json_path = output_dir / f"{args.player_id}_player_transfers_raw.json"
    txt_path = output_dir / f"{args.player_id}_player_transfers_raw.txt"
    meta_path = output_dir / f"{args.player_id}_player_transfers_raw.meta.json"

    print(
        "[info] Confirm the endpoint path against the local API Swagger/OpenAPI docs "
        "if this request fails."
    )
    print(f"[collect] Player {args.player_id} -> {url}")

    try:
        response = requests.get(url, timeout=config["timeout_seconds"])
    except requests.RequestException as exc:
        print(f"[error] Request failed: {exc}")
        return 1

    metadata = {
        "player_id": args.player_id,
        "endpoint_url": url,
        "collected_at_utc": collected_at,
        "status_code": response.status_code,
        "source_name": "transfermarkt_api",
        "collection_method": "local_transfermarkt_api",
    }

    try:
        payload = response.json()
    except ValueError:
        txt_path.write_text(response.text, encoding="utf-8")
        meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[warn] Non-JSON response saved to {txt_path}")
        return 0 if response.ok else 1

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[saved] {json_path}")
    return 0 if response.ok else 1


if __name__ == "__main__":
    sys.exit(main())
