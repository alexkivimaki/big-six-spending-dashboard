#!/usr/bin/env python3

"""Backfill Liverpool finance extraction rows from scanned statements using OCR."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

import fitz


CLUB_ID = "liverpool"
CLUB_NAME = "Liverpool"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season-from", default="2012/13")
    parser.add_argument("--season-to", default="2024/25")
    parser.add_argument("--statements-root", default="data/raw/financial_statements")
    parser.add_argument("--output-root", default="data/raw/ai_agents/financial_extraction_outputs")
    parser.add_argument("--swift-script", default="scripts/collect/vision_ocr.swift")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def load_seasons() -> list[str]:
    return [f"{year}/{str(year + 1)[-2:]}" for year in range(2008, 2025)]


def select_seasons(season_from: str, season_to: str) -> list[str]:
    seasons = load_seasons()
    start = seasons.index(season_from)
    end = seasons.index(season_to)
    return seasons[start : end + 1]


def label_to_slug(label: str) -> str:
    return label.replace("/", "_")


def render_and_ocr(pdf_path: Path, page_number: int, swift_script: Path, scale: float = 1) -> str:
    doc = fitz.open(pdf_path)
    page = doc[page_number - 1]
    image_path = Path(tempfile.gettempdir()) / f"{pdf_path.stem}_{page_number}_{scale}.png"
    page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).save(image_path)
    proc = subprocess.run(
        ["swift", str(swift_script), str(image_path)],
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_number(token: str) -> int:
    token = token.strip()
    negative = token.startswith("(") and token.endswith(")")
    token = token.replace("(", "").replace(")", "").replace(",", "")
    token = token.replace("£", "").replace("€", "").replace("$", "")
    token = token.replace("O", "0")
    value = int(token)
    return -value if negative else value


def to_full_pounds(token: str) -> int:
    return clean_number(token) * 1000


def find_page(pdf_path: Path, swift_script: Path, phrases: list[str], page_range: range) -> tuple[int, str]:
    for page_number in page_range:
        text = render_and_ocr(pdf_path, page_number, swift_script)
        lowered = text.lower()
        if any(phrase.lower() in lowered for phrase in phrases):
            return page_number, text
    raise ValueError(f"Phrase not found: {' | '.join(phrases)}")


def first_number_after(text: str, phrase: str) -> int:
    lowered = text.lower()
    idx = lowered.find(phrase.lower())
    if idx == -1:
        raise ValueError(f"Phrase not found: {phrase}")
    snippet = text[idx : idx + 600]
    matches = re.findall(r"\(?[0-9][0-9,]*\)?", snippet)
    if not matches:
        raise ValueError(f"No numbers found after phrase: {phrase}")
    return to_full_pounds(matches[0])


def parse_profit_before_tax(text: str, season_start: int) -> int:
    current_year = season_start + 1
    patterns = [
        rf"{current_year}\s+£?000.*?profit.*?ordinary activities.*?([\(]?[0-9][0-9,]*[)]?)",
        rf"{current_year}\s+£?000.*?loss.*?ordinary activities.*?([\(]?[0-9][0-9,]*[)]?)",
    ]
    squashed = normalize_spaces(text)
    for pattern in patterns:
        match = re.search(pattern, squashed, flags=re.I)
        if match:
            return to_full_pounds(match.group(1))

    phrase_candidates = [
        "profit taxatio ordinary activities",
        "loss on ordinary activities before taxation",
        "profit on ordinary activities before taxation",
        "profit / (loss) on ordinary activities before taxation",
        "loss before taxation",
        "profit before taxation",
    ]
    for phrase in phrase_candidates:
        try:
            return first_number_after(text, phrase)
        except ValueError:
            continue
    raise ValueError("Could not parse profit before tax")


def parse_turnover_split(text: str, season_start: int) -> tuple[int, int, int]:
    current_year = season_start + 1
    squashed = normalize_spaces(text)
    match = re.search(
        rf"{current_year}\s+£?000\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)",
        squashed,
        flags=re.I,
    )
    if not match:
        raise ValueError("Could not parse turnover split")
    return (
        to_full_pounds(match.group(1)),
        to_full_pounds(match.group(2)),
        to_full_pounds(match.group(3)),
    )


def parse_cash(text: str) -> int:
    return first_number_after(text, "cash at bank and in hand")


def parse_current_group_loan(text: str) -> int:
    for phrase in [
        "amounts owed to parent undertaking",
        "amounts owed to current group undertakings",
        "amounts owed to current group undertaking",
        "amounts owed to group undertakings",
    ]:
        try:
            return first_number_after(text, phrase)
        except ValueError:
            continue
    raise ValueError("Could not parse Liverpool current group loan")


def parse_bank_loan(text: str) -> int:
    for phrase in [
        "secured bank loans",
        "bank loans and overdrafts",
        "bank loan",
    ]:
        try:
            return first_number_after(text, phrase)
        except ValueError:
            continue
    raise ValueError("Could not parse Liverpool bank loan")


def parse_staff_costs(text: str) -> int:
    wages = first_number_after(text, "wages and salaries")
    social_security = first_number_after(text, "social security costs")
    pension = first_number_after(text, "pension costs")
    return wages + social_security + pension


def build_output(source_meta: dict, season: str, values: dict[str, int], pages_used: list[int]) -> dict:
    total_revenue = values["matchday"] + values["broadcast"] + values["commercial"]
    return {
        "club_id": CLUB_ID,
        "club_name": CLUB_NAME,
        "season": season,
        "financial_year_end": source_meta.get("financial_year_end", ""),
        "currency_original": "GBP",
        "units_original": "full pounds (converted from GBP thousands disclosed in report)",
        "total_revenue_original": total_revenue,
        "matchday_revenue_original": values["matchday"],
        "broadcast_revenue_original": values["broadcast"],
        "commercial_revenue_original": values["commercial"],
        "other_revenue_original": None,
        "women_team_revenue_original": None,
        "excluded_player_trading_revenue_original": None,
        "staff_costs_original": values["staff_costs"],
        "net_debt_original": values["net_debt"],
        "player_amortisation_original": values["player_amortisation"],
        "profit_on_player_sales_original": None,
        "profit_loss_before_tax_original": values["profit_before_tax"],
        "total_revenue_eur": None,
        "matchday_revenue_eur": None,
        "broadcast_revenue_eur": None,
        "commercial_revenue_eur": None,
        "other_revenue_eur": None,
        "net_debt_eur": None,
        "profit_loss_before_tax_eur": None,
        "exchange_rate_used": None,
        "exchange_rate_source": "",
        "revenue_sum_check_original": total_revenue,
        "revenue_sum_difference_original": 0,
        "pages_used": pages_used,
        "evidence": [
            {
                "field": "matchday_revenue_original",
                "value_original": values["matchday"],
                "page_number": values["turnover_page"],
                "statement_label": "Matchday",
                "evidence_text": "Analysis of turnover note. Values were disclosed in GBP thousands and converted to full GBP.",
            },
            {
                "field": "broadcast_revenue_original",
                "value_original": values["broadcast"],
                "page_number": values["turnover_page"],
                "statement_label": "Media / broadcasting",
                "evidence_text": "Analysis of turnover note. Values were disclosed in GBP thousands and converted to full GBP.",
            },
            {
                "field": "commercial_revenue_original",
                "value_original": values["commercial"],
                "page_number": values["turnover_page"],
                "statement_label": "Commercial",
                "evidence_text": "Analysis of turnover note. Values were disclosed in GBP thousands and converted to full GBP.",
            },
            {
                "field": "staff_costs_original",
                "value_original": values["staff_costs"],
                "page_number": values["staff_page"],
                "statement_label": "Staff costs",
                "evidence_text": "Administrative expenses note. Values were disclosed in GBP thousands and converted to full GBP.",
            },
            {
                "field": "player_amortisation_original",
                "value_original": values["player_amortisation"],
                "page_number": values["staff_page"],
                "statement_label": "Amortisation of players' registrations",
                "evidence_text": "Administrative expenses note. Values were disclosed in GBP thousands and converted to full GBP.",
            },
            {
                "field": "profit_loss_before_tax_original",
                "value_original": values["profit_before_tax"],
                "page_number": values["profit_page"],
                "statement_label": "Profit / loss before taxation",
                "evidence_text": "Profit and loss account. Values were disclosed in GBP thousands and converted to full GBP.",
            },
            {
                "field": "net_debt_original",
                "value_original": values["net_debt"],
                "page_number": values["debt_page"],
                "statement_label": "Estimated net debt from bank loans plus current parent/group loan less cash",
                "evidence_text": "Calculated from the balance sheet cash line plus the current-group-owed line and bank loan line in the creditors notes. Values were disclosed in GBP thousands and converted to full GBP.",
            },
        ],
        "classification_notes": "Liverpool discloses matchday, media/broadcasting, and commercial turnover directly in the annual accounts. No player trading figure was used in football revenue.",
        "women_team_treatment_notes": "Women's team revenue is not separately disclosed in the report.",
        "non_football_revenue_notes": "No separate non-football commercial adjustment was identified in the extracted note.",
        "confidence_level": "medium",
        "requires_manual_review": True,
        "source_document": source_meta.get("report_title") or source_meta.get("source_document") or "",
        "source_url": source_meta.get("source_url", ""),
        "notes": "Values in the annual report were disclosed in GBP thousands and have been converted here into full GBP amounts by multiplying by 1,000. Liverpool net debt is estimated here as bank loans plus the current parent/group loan less cash, based on the debt-related note disclosures available in the scanned statement.",
    }


def load_meta_for_pdf(pdf_path: Path) -> dict:
    meta_path = pdf_path.with_suffix(pdf_path.suffix + ".meta.json")
    if not meta_path.exists():
        return {}
    return json.loads(meta_path.read_text())


def process_season(pdf_path: Path, output_path: Path, swift_script: Path, season: str) -> None:
    season_start = int(season.split("/")[0])
    doc = fitz.open(pdf_path)

    profit_page, profit_text = find_page(pdf_path, swift_script, ["profit and loss account"], range(11, min(18, len(doc)) + 1))
    turnover_page, turnover_text = find_page(pdf_path, swift_script, ["2 turnover", "turnover by activity", "by activity:"], range(20, min(28, len(doc)) + 1))
    staff_page, staff_text = find_page(pdf_path, swift_script, ["staff numbers and costs"], range(20, min(28, len(doc)) + 1))
    balance_page, balance_text = find_page(pdf_path, swift_script, ["cash at bank and in hand"], range(11, min(18, len(doc)) + 1))
    debt_page, debt_text = find_page(pdf_path, swift_script, ["interest-bearing loans and borrowings"], range(24, min(33, len(doc)) + 1))

    broadcast, matchday, commercial = parse_turnover_split(turnover_text, season_start)
    staff_costs = parse_staff_costs(staff_text)
    player_amortisation = first_number_after(staff_text, "amortisation of players' registrations")
    profit_before_tax = parse_profit_before_tax(profit_text, season_start)
    cash = parse_cash(balance_text)
    current_group_loan = parse_current_group_loan(debt_text)
    bank_loan = parse_bank_loan(debt_text)
    net_debt = current_group_loan + bank_loan - cash

    values = {
        "broadcast": broadcast,
        "matchday": matchday,
        "commercial": commercial,
        "staff_costs": staff_costs,
        "player_amortisation": player_amortisation,
        "profit_before_tax": profit_before_tax,
        "net_debt": net_debt,
        "turnover_page": turnover_page,
        "staff_page": staff_page,
        "profit_page": profit_page,
        "debt_page": debt_page,
    }
    payload = build_output(load_meta_for_pdf(pdf_path), season, values, sorted({profit_page, turnover_page, staff_page, balance_page, debt_page}))
    output_path.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> int:
    args = parse_args()
    seasons = select_seasons(args.season_from, args.season_to)
    statements_root = Path(args.statements_root) / CLUB_ID
    output_root = Path(args.output_root)
    swift_script = Path(args.swift_script)

    for season in seasons:
        season_slug = label_to_slug(season)
        output_path = output_root / f"{CLUB_ID}_{season_slug}_financial_extraction_output.json"
        if output_path.exists() and not args.overwrite:
            print(f"[skip] {season} already exists")
            continue
        pdf_matches = sorted(statements_root.glob(f"{season_slug}_*.pdf"))
        if not pdf_matches:
            print(f"[warn] Missing PDF for {season}")
            continue
        try:
            process_season(pdf_matches[0], output_path, swift_script, season)
        except Exception as exc:
            print(f"[error] {season}: {exc}")
            continue
        print(f"[saved] {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
