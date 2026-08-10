#!/usr/bin/env python3

"""Create AI-review tasks from deterministic draft finance extraction packages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/ai_agents/financial_extraction_drafts")
    parser.add_argument("--output", default="data/raw/ai_agents/financial_extraction_review_tasks")
    parser.add_argument("--prompt", default="agents/financial_extraction_agent_prompt.md")
    parser.add_argument("--only-needs-review", action="store_true", default=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_root = Path(args.input)
    output_root = Path(args.output)
    prompt_path = Path(args.prompt)

    written = 0
    for draft_path in sorted(input_root.glob("*.json")):
        draft = json.loads(draft_path.read_text())
        if args.only_needs_review and not draft.get("needs_ai_review", True):
            continue
        payload = {
            "task_type": "financial_extraction_review",
            "prompt_path": str(prompt_path),
            "draft_path": str(draft_path),
            "club_id": draft.get("club_id", ""),
            "club_name": draft.get("club_name", ""),
            "season": draft.get("season", ""),
            "local_statement_path": draft.get("local_statement_path", ""),
            "ocr_cache_path": draft.get("ocr_cache_path", ""),
            "candidate_extraction": draft.get("candidate_extraction", {}),
            "candidate_pages_summary": draft.get("candidate_pages_summary", []),
            "review_reasons": draft.get("review_reasons", []),
            "bank_references": draft.get("bank_references", []),
            "save_output_to": draft.get("suggested_save_output_to", ""),
        }
        output_path = output_root / f"{draft_path.stem}_review_task.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n")
        written += 1

    print(f"[saved] Wrote {written} financial review tasks to {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
