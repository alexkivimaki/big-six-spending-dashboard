#!/usr/bin/env python3

"""Build deterministic draft finance extractions from OCR caches before AI review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from extract_statement_financials_from_ocr import (
    EXTRACTORS,
    load_seasons,
    load_source_url,
    render_and_ocr_pdf,
    season_slug_to_label,
    source_document_for_pdf,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--club", choices=sorted(EXTRACTORS))
    parser.add_argument("--season-from", default="2011/12")
    parser.add_argument("--season-to", default="2024/25")
    parser.add_argument("--statements-root", default="data/raw/financial_statements")
    parser.add_argument("--ocr-cache-root", default="data/raw/financial_statement_ocr")
    parser.add_argument("--output-root", default="data/raw/ai_agents/financial_extraction_drafts")
    parser.add_argument("--swift-script", default="scripts/collect/vision_ocr.swift")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def label_to_slug(label: str) -> str:
    return label.replace("/", "_")


def select_seasons(season_from: str, season_to: str) -> list[str]:
    seasons = load_seasons()
    start = seasons.index(season_from)
    end = seasons.index(season_to)
    return seasons[start : end + 1]


def summarize_pages(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = []
    for record in records:
        text = record.get("text", "")
        summary.append(
            {
                "page": record.get("page"),
                "char_count": len(text),
                "preview": " ".join(text.split())[:240],
            }
        )
    return summary


def review_reasons(candidate: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if candidate.get("confidence_level") != "high":
        reasons.append(f"confidence_level={candidate.get('confidence_level')}")
    notes = str(candidate.get("notes") or "")
    if "estimated" in notes.lower():
        reasons.append("estimated methodology in notes")
    women_notes = str(candidate.get("women_team_treatment_notes") or "")
    lowered_women = women_notes.lower()
    generic_non_disclosure_prefixes = [
        "women's team revenue is not separately disclosed",
        "womens team revenue is not separately disclosed",
    ]
    if women_notes and not any(lowered_women.strip().startswith(prefix) for prefix in generic_non_disclosure_prefixes) and (
        "separately disclosed" in lowered_women
        or "inseparable" in lowered_women
        or "included" in lowered_women
    ):
        reasons.append("women_team_treatment needs review")
    fields = [
        "total_revenue_original",
        "matchday_revenue_original",
        "broadcast_revenue_original",
        "commercial_revenue_original",
        "staff_costs_original",
        "net_debt_original",
        "profit_loss_before_tax_original",
    ]
    missing = [field for field in fields if candidate.get(field) is None]
    if missing:
        reasons.append(f"missing core fields: {', '.join(missing)}")
    return reasons


def build_draft_payload(
    club: str,
    season: str,
    pdf_path: Path,
    ocr_cache_path: Path,
    candidate: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    reasons = review_reasons(candidate)
    return {
        "task_type": "financial_extraction_review",
        "club_id": club,
        "club_name": candidate.get("club_name", club.replace("_", " ").title()),
        "season": season,
        "source_document": source_document_for_pdf(pdf_path),
        "source_url": load_source_url(club, label_to_slug(season)),
        "local_statement_path": str(pdf_path),
        "ocr_cache_path": str(ocr_cache_path),
        "candidate_extraction": candidate,
        "candidate_pages_summary": summarize_pages(records),
        "review_reasons": reasons,
        "needs_ai_review": bool(reasons),
        "suggested_save_output_to": f"data/raw/ai_agents/financial_extraction_outputs/{club}_{label_to_slug(season)}_financial_extraction_output.json",
        "bank_references": [
            "data/reference/financial_statement_extraction_bank/master_financial_statement_extraction_bank.md",
            f"data/reference/financial_statement_extraction_bank/{club}/README.md",
            f"data/reference/financial_statement_extraction_bank/{club}/{club}_extraction_bank.csv",
        ],
    }


def load_existing_output(output_path: Path) -> dict[str, Any] | None:
    if not output_path.exists():
        return None
    return json.loads(output_path.read_text())


def main() -> int:
    args = parse_args()
    statements_root = Path(args.statements_root)
    ocr_cache_root = Path(args.ocr_cache_root)
    output_root = Path(args.output_root)
    swift_script = Path(args.swift_script)
    seasons = select_seasons(args.season_from, args.season_to)
    clubs = [args.club] if args.club else sorted(EXTRACTORS)

    written = 0
    for club in clubs:
        extractor = EXTRACTORS[club]
        for season in seasons:
            season_slug = label_to_slug(season)
            output_path = output_root / f"{club}_{season_slug}_draft.json"
            if output_path.exists() and not args.overwrite:
                print(f"[skip] {output_path}")
                continue
            pdf_matches = sorted((statements_root / club).glob(f"{season_slug}_*.pdf"))
            if not pdf_matches:
                print(f"[warn] Missing statement PDF for {club} {season}")
                continue
            pdf_path = pdf_matches[0]
            ocr_cache_path = ocr_cache_root / club / f"{season_slug}_ocr.json"
            existing_output_path = Path("data/raw/ai_agents/financial_extraction_outputs") / f"{club}_{season_slug}_financial_extraction_output.json"
            existing_candidate = load_existing_output(existing_output_path)
            records = render_and_ocr_pdf(pdf_path, swift_script, ocr_cache_path)
            if existing_candidate is not None:
                payload = build_draft_payload(club, season, pdf_path, ocr_cache_path, existing_candidate, records)
                payload["draft_source"] = "existing_extraction_output"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(json.dumps(payload, indent=2) + "\n")
                print(f"[saved] {output_path} (from existing extraction)")
                written += 1
                continue
            try:
                candidate = extractor(
                    records,
                    season,
                    source_document_for_pdf(pdf_path),
                    load_source_url(club, season_slug),
                )
            except Exception as exc:
                payload = {
                    "task_type": "financial_extraction_review",
                    "club_id": club,
                    "season": season,
                    "local_statement_path": str(pdf_path),
                    "ocr_cache_path": str(ocr_cache_path),
                    "candidate_extraction": {},
                    "candidate_pages_summary": summarize_pages(records),
                    "review_reasons": [f"draft extraction failed: {exc}"],
                    "needs_ai_review": True,
                    "suggested_save_output_to": f"data/raw/ai_agents/financial_extraction_outputs/{club}_{season_slug}_financial_extraction_output.json",
                    "bank_references": [
                        "data/reference/financial_statement_extraction_bank/master_financial_statement_extraction_bank.md",
                        f"data/reference/financial_statement_extraction_bank/{club}/README.md",
                        f"data/reference/financial_statement_extraction_bank/{club}/{club}_extraction_bank.csv",
                    ],
                }
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(json.dumps(payload, indent=2) + "\n")
                print(f"[draft-error] {club} {season}: {exc}")
                print(f"[saved] {output_path}")
                written += 1
                continue

            payload = build_draft_payload(club, season, pdf_path, ocr_cache_path, candidate, records)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(payload, indent=2) + "\n")
            print(f"[saved] {output_path}")
            written += 1

    print(f"[done] Built {written} draft extraction packages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
