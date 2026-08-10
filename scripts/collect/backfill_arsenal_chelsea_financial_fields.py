#!/usr/bin/env python3

"""Backfill missing net debt and profit-before-tax fields for Arsenal and Chelsea."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

import fitz


CLUBS = ("arsenal", "chelsea")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--club", choices=CLUBS)
    parser.add_argument("--season-from", default="2011/12")
    parser.add_argument("--season-to", default="2024/25")
    parser.add_argument("--swift-script", default="scripts/collect/vision_ocr.swift")
    parser.add_argument("--statements-root", default="data/raw/financial_statements")
    parser.add_argument("--output-root", default="data/raw/ai_agents/financial_extraction_outputs")
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


def clean_number(token: str) -> int:
    negative = token.startswith("(") and token.endswith(")")
    token = token.replace("(", "").replace(")", "").replace(",", "").replace("£", "").replace("$", "")
    token = token.replace("O", "0")
    value = int(token)
    return -value if negative else value


def ocr_page(pdf_path: Path, page_number: int, swift_script: Path, clip: fitz.Rect | None = None, scale: int = 2) -> str:
    doc = fitz.open(pdf_path)
    page = doc[page_number - 1]
    pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False, clip=clip)
    image_path = Path(tempfile.gettempdir()) / f"{pdf_path.stem}_{page_number}_{scale}.png"
    pixmap.save(image_path)
    proc = subprocess.run(
        ["swift", str(swift_script), str(image_path)],
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout


def first_matching_page(pdf_path: Path, swift_script: Path, keywords: tuple[str, ...], page_numbers: range) -> tuple[int, str]:
    for page_number in page_numbers:
        if page_number < 1:
            continue
        text = ocr_page(pdf_path, page_number, swift_script, scale=2)
        lowered = text.lower()
        if all(keyword in lowered for keyword in keywords):
            return page_number, text
    raise ValueError(f"No page matched keywords: {keywords}")


def parse_first_value_after_phrase(text: str, phrase: str) -> int:
    lowered = text.lower()
    index = lowered.find(phrase.lower())
    if index == -1:
        raise ValueError(f"Phrase not found: {phrase}")
    snippet = text[index : index + 500]
    matches = re.findall(r"\(?[0-9][0-9,]*\)?", snippet)
    if not matches:
        raise ValueError(f"No values found after phrase: {phrase}")
    return clean_number(matches[0]) * 1000


def parse_cash_total_arsenal(text: str) -> int:
    lowered = text.lower()
    if "cash and short-term deposits" in lowered:
        snippet = text[lowered.index("cash and short-term deposits") : lowered.index("cash and short-term deposits") + 400]
        matches = re.findall(r"\(?[0-9][0-9,]*\)?", snippet)
        if not matches:
            raise ValueError("Could not parse Arsenal cash and short-term deposits")
        return clean_number(matches[0]) * 1000
    if "cash at bank" in lowered:
        snippet = text[lowered.index("cash at bank") : lowered.index("cash at bank") + 300]
        matches = re.findall(r"\(?[0-9][0-9,]*\)?", snippet)
        if not matches:
            raise ValueError("Could not parse Arsenal cash at bank")
        return clean_number(matches[0]) * 1000
    raise ValueError("Arsenal cash phrase not found")


def parse_total_debt_arsenal(text: str) -> int:
    lowered = text.lower()
    if "total debt" not in lowered:
        raise ValueError("Arsenal total debt phrase not found")
    snippet = text[lowered.index("total debt") : lowered.index("total debt") + 200]
    matches = re.findall(r"\(?[0-9][0-9,]*\)?", snippet)
    if not matches:
        raise ValueError("Could not parse Arsenal total debt")
    return clean_number(matches[0]) * 1000


def parse_ending_net_debt_row(text: str, month_name: str, year_end: int) -> int:
    match = re.search(rf"at\s+\d+\s+{month_name}\s+{year_end}", text, flags=re.I)
    if not match:
        raise ValueError(f"Ending net debt section not found for {month_name} {year_end}")
    snippet = text[match.start() : match.start() + 350]
    matches = re.findall(r"\(?[0-9][0-9,]*\)?", snippet)
    if not matches:
        raise ValueError("Could not parse ending net debt row")
    return clean_number(matches[-1]) * 1000


def parse_current_net_debt_chelsea(pdf_path: Path, page_number: int, swift_script: Path, year_end: int) -> int:
    doc = fitz.open(pdf_path)
    page = doc[page_number - 1]
    rect = page.rect
    clip = fitz.Rect(0, rect.height * 0.48, rect.width, rect.height * 0.95)
    text = ocr_page(pdf_path, page_number, swift_script, clip=clip, scale=4)
    match = re.search(rf"at\s+30\s+june\s+{year_end}", text, flags=re.I)
    if not match:
        raise ValueError(f"Chelsea ending net debt section not found for {year_end}")
    snippet = text[match.start() : match.start() + 300]
    matches = re.findall(r"\(?[0-9][0-9,]*\)?", snippet)
    if len(matches) < 3:
        raise ValueError("Could not parse Chelsea ending net debt row")
    return clean_number(matches[2]) * 1000


def update_record(record_path: Path, profit_before_tax: int, profit_page: int, profit_label: str, profit_evidence: str, net_debt: int, debt_page: int, debt_label: str, debt_evidence: str) -> None:
    data = json.loads(record_path.read_text())
    data["profit_loss_before_tax_original"] = profit_before_tax
    data["net_debt_original"] = net_debt

    evidence = [item for item in data.get("evidence", []) if item.get("field") not in {"profit_loss_before_tax_original", "net_debt_original"}]
    evidence.extend(
        [
            {
                "field": "profit_loss_before_tax_original",
                "value_original": profit_before_tax,
                "page_number": profit_page,
                "statement_label": profit_label,
                "evidence_text": profit_evidence,
            },
            {
                "field": "net_debt_original",
                "value_original": net_debt,
                "page_number": debt_page,
                "statement_label": debt_label,
                "evidence_text": debt_evidence,
            },
        ]
    )
    data["evidence"] = evidence
    record_path.write_text(json.dumps(data, indent=2) + "\n")


def backfill_arsenal(record_path: Path, pdf_path: Path, swift_script: Path, season: str) -> None:
    doc = fitz.open(pdf_path)
    profit_page = None
    profit_text = None
    for keywords in [
        ("profit on ordinary activities before tax",),
        ("profit on ordinary activities before taxation",),
        ("profit before taxation",),
        ("loss before taxation",),
    ]:
        try:
            profit_page, profit_text = first_matching_page(pdf_path, swift_script, keywords, range(20, len(doc) + 1))
            profit_before_tax = parse_first_value_after_phrase(profit_text, keywords[0])
            break
        except ValueError:
            continue
    if profit_page is None or profit_text is None:
        raise ValueError("Could not locate Arsenal profit before tax disclosure")

    year_end = int(season.split("/")[0]) + 1
    try:
        debt_page, debt_text = first_matching_page(pdf_path, swift_script, ("analysis of changes in net debt",), range(20, len(doc) + 1))
        net_debt = parse_ending_net_debt_row(debt_text, "may", year_end)
        debt_label = "Net (debt) from analysis of changes in net debt"
        debt_evidence = "Annual report analysis of changes in net debt note. Values were disclosed in GBP thousands and converted to full GBP."
    except ValueError:
        try:
            cash_page, cash_text = first_matching_page(pdf_path, swift_script, ("cash and short-term deposits",), range(20, len(doc) + 1))
        except ValueError:
            cash_page, cash_text = first_matching_page(pdf_path, swift_script, ("cash at bank",), range(20, len(doc) + 1))
        debt_page, debt_text = first_matching_page(pdf_path, swift_script, ("total debt",), range(20, len(doc) + 1))

        cash_total = parse_cash_total_arsenal(cash_text)
        total_debt = parse_total_debt_arsenal(debt_text)
        net_debt = total_debt - cash_total
        debt_label = "Computed net debt from total debt less cash and short-term deposits"
        debt_evidence = "Calculated from the annual report total debt disclosure and the cash / cash and short-term deposits note. Values were disclosed in GBP thousands and converted to full GBP."

    update_record(
        record_path,
        profit_before_tax=profit_before_tax,
        profit_page=profit_page,
        profit_label="Profit before taxation",
        profit_evidence="Annual report profit/tax note. Values were disclosed in GBP thousands and converted to full GBP.",
        net_debt=net_debt,
        debt_page=debt_page,
        debt_label=debt_label,
        debt_evidence=debt_evidence,
    )


def backfill_chelsea(record_path: Path, pdf_path: Path, swift_script: Path, season: str) -> None:
    doc = fitz.open(pdf_path)
    profit_page, profit_text = first_matching_page(
        pdf_path,
        swift_script,
        ("charge for the year", "ordinary activities"),
        range(12, len(doc) + 1),
    )
    profit_before_tax = parse_first_value_after_phrase(profit_text, "ordinary activities")

    debt_page, _ = first_matching_page(pdf_path, swift_script, ("analysis of net debt",), range(20, len(doc) + 1))
    year_end = int(season.split("/")[0]) + 1
    net_debt = parse_current_net_debt_chelsea(pdf_path, debt_page, swift_script, year_end)

    update_record(
        record_path,
        profit_before_tax=profit_before_tax,
        profit_page=profit_page,
        profit_label="Profit/(loss) on ordinary activities before taxation",
        profit_evidence="Annual report profit/tax note. Values were disclosed in GBP thousands and converted to full GBP.",
        net_debt=net_debt,
        debt_page=debt_page,
        debt_label="Net debt",
        debt_evidence="Annual report analysis of net debt note. Values were disclosed in GBP thousands and converted to full GBP.",
    )


BACKFILLERS = {
    "arsenal": backfill_arsenal,
    "chelsea": backfill_chelsea,
}


def main() -> int:
    args = parse_args()
    seasons = select_seasons(args.season_from, args.season_to)
    swift_script = Path(args.swift_script)
    clubs = [args.club] if args.club else list(CLUBS)

    for club in clubs:
        for season in seasons:
            season_slug = label_to_slug(season)
            record_path = Path(args.output_root) / f"{club}_{season_slug}_financial_extraction_output.json"
            if not record_path.exists():
                print(f"[skip] Missing extraction JSON for {club} {season}")
                continue
            data = json.loads(record_path.read_text())
            if (
                data.get("net_debt_original") is not None
                and data.get("profit_loss_before_tax_original") is not None
                and not args.overwrite
            ):
                print(f"[skip] {club} {season} already has net debt and profit before tax")
                continue
            pdf_matches = sorted((Path(args.statements_root) / club).glob(f"{season_slug}_*.pdf"))
            if not pdf_matches:
                print(f"[warn] Missing statement PDF for {club} {season}")
                continue
            pdf_path = pdf_matches[0]
            try:
                BACKFILLERS[club](record_path, pdf_path, swift_script, season)
            except Exception as exc:
                print(f"[error] {club} {season}: {exc}")
                continue
            print(f"[saved] {record_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
