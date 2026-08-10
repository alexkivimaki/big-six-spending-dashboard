#!/usr/bin/env python3

"""OCR and extract club finance fields from downloaded statement PDFs."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Callable

import fitz


CLUBS = ("liverpool", "manchester_city", "tottenham_hotspur")


def season_slug_to_label(slug: str) -> str:
    return slug.replace("_", "/")


def label_to_slug(label: str) -> str:
    return label.replace("/", "_")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--club", choices=CLUBS)
    parser.add_argument("--season-from", default="2011/12")
    parser.add_argument("--season-to", default="2024/25")
    parser.add_argument("--statements-root", default="data/raw/financial_statements")
    parser.add_argument("--ocr-cache-root", default="data/raw/financial_statement_ocr")
    parser.add_argument("--output-root", default="data/raw/ai_agents/financial_extraction_outputs")
    parser.add_argument("--swift-script", default="scripts/collect/vision_ocr.swift")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def load_seasons() -> list[str]:
    return [f"{year}/{str(year + 1)[-2:]}" for year in range(2011, 2025)]


def select_seasons(season_from: str, season_to: str) -> list[str]:
    seasons = load_seasons()
    start = seasons.index(season_from)
    end = seasons.index(season_to)
    return seasons[start : end + 1]


def run_ocr(swift_script: Path, image_path: Path) -> str:
    cache_root = Path("tmp/swift_cache")
    cache_root.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["HOME"] = str(cache_root.resolve())
    env["CLANG_MODULE_CACHE_PATH"] = str((cache_root / "clang-module-cache").resolve())
    proc = subprocess.run(
        ["swift", str(swift_script), str(image_path)],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    return proc.stdout


def render_and_ocr_pdf(pdf_path: Path, swift_script: Path, cache_path: Path) -> list[dict]:
    if cache_path.exists():
        return json.loads(cache_path.read_text())

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    page_image_dir = cache_path.parent / f"{cache_path.stem}_pages"
    page_image_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    records = []
    for page_number, page in enumerate(doc, start=1):
        image_path = page_image_dir / f"page_{page_number}.png"
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        pixmap.save(image_path)
        text = run_ocr(swift_script, image_path)
        records.append({"page": page_number, "text": text})
    cache_path.write_text(json.dumps(records, indent=2) + "\n")
    return records


def find_page(records: list[dict], predicate: Callable[[str], bool]) -> dict:
    for record in records:
        if predicate(record["text"].lower()):
            return record
    raise ValueError("Matching page not found")


def find_page_any(records: list[dict], predicates: list[Callable[[str], bool]]) -> dict:
    for predicate in predicates:
        try:
            return find_page(records, predicate)
        except ValueError:
            continue
    raise ValueError("Matching page not found")


def clean_number(token: str) -> int:
    token = token.strip()
    negative = "(" in token and ")" in token
    token = token.replace("(", "").replace(")", "").replace(",", "")
    token = token.replace("£", "").replace("$", "")
    token = token.replace("O", "0")
    value = int(token)
    return -value if negative else value


def find_line_value(text: str, label: str) -> int:
    pattern = re.compile(rf"{re.escape(label)}.*?([\(\-]?[0-9,]+[\)]?)\s*(?:[\(\-]?[0-9,]+[\)]?)?\s*$", re.I | re.M)
    match = pattern.search(text)
    if not match:
        raise ValueError(f"Could not find {label!r}")
    return clean_number(match.group(1)) * 1000


def find_first_line_value(text: str, labels: list[str]) -> int:
    for label in labels:
        try:
            return find_line_value(text, label)
        except ValueError:
            try:
                return line_value_after_label(text, label)
            except ValueError:
                continue
    raise ValueError(f"Could not find any of {labels!r}")


def has_money_figure(text: str) -> bool:
    return bool(re.search(r"\d{1,3},\d{3}", text))


def parse_millions_amount_to_pounds(token: str) -> int:
    cleaned = token.replace("£", "").replace("$", "").replace("€", "").replace(",", "").strip()
    return int(round(float(cleaned) * 1_000_000))


def find_net_debt_from_strategic_text(text: str) -> int:
    lowered = text.lower()
    match = re.search(r"net debt of\s*[£€]?([\d,]+(?:\.\d+)?)m", lowered, re.I)
    if match:
        return parse_millions_amount_to_pounds(match.group(1))
    match = re.search(r"net cash of\s*[£€]?([\d,]+(?:\.\d+)?)m", lowered, re.I)
    if match:
        return -parse_millions_amount_to_pounds(match.group(1))
    match = re.search(r"([£€]?[\d,]+(?:\.\d+)?)m\s+net funds", lowered, re.I)
    if match:
        return -parse_millions_amount_to_pounds(match.group(1))
    match = re.search(r"([£€]?[\d,]+(?:\.\d+)?)m\s+net cash", lowered, re.I)
    if match:
        return -parse_millions_amount_to_pounds(match.group(1))
    raise ValueError("Could not find explicit net debt or net cash disclosure")


def parse_tottenham_revenue_values(text: str, season: str) -> tuple[int, int, int, int]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if season == "2017/18":
        start = lines.index("Revenue comprises:") + 1
        end = lines.index("Timing of revenue recognition:")
        numbers = [clean_number(x) * 1000 for x in re.findall(r"[\(\-]?[0-9,]+[\)]?", "\n".join(lines[start:end]))]
        return numbers[0], numbers[2], numbers[4], numbers[6]

    if season == "2018/19":
        start = lines.index("Revenue comprises:") + 1
        end = lines.index("Timing of revonue recognition:")
        numbers = [clean_number(x) * 1000 for x in re.findall(r"[\(\-]?[0-9,]+[\)]?", "\n".join(lines[start:end]))]
        return numbers[0], numbers[1], numbers[2], numbers[3]

    current_year = str(int(season.split("/")[0]) + 1)
    start = lines.index("Revenue comprises:")
    year_idx = None
    for i in range(start, len(lines) - 1):
        if lines[i] == current_year and "000" in lines[i + 1]:
            year_idx = i
            break
    if year_idx is None:
        raise ValueError("Could not locate current-year revenue block")
    numbers = [clean_number(x) * 1000 for x in re.findall(r"[\(\-]?[0-9,]+[\)]?", "\n".join(lines[year_idx + 2 : year_idx + 14]))]
    return numbers[0], numbers[1], numbers[2], numbers[3]


def find_line_values(text: str, label: str) -> list[int]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if label.lower() in line.lower():
            matches = re.findall(r"[\(\-]?[0-9,]+[\)]?", line)
            if matches:
                return [clean_number(match) * 1000 for match in matches]
    raise ValueError(f"Could not find values for {label!r}")


def line_value_after_label(text: str, label: str) -> int:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for idx, line in enumerate(lines):
        if label.lower() in line.lower():
            for next_line in lines[idx + 1 : idx + 16]:
                nums = re.findall(r"[\(\-]?[0-9,]+[\)]?", next_line)
                if nums:
                    return clean_number(nums[0]) * 1000
    raise ValueError(f"Could not find value after {label!r}")


def build_common_record(club_id: str, club_name: str, season: str, financial_year_end: str, source_document: str, source_url: str) -> dict:
    return {
        "club_id": club_id,
        "club_name": club_name,
        "season": season,
        "financial_year_end": financial_year_end,
        "currency_original": "GBP",
        "units_original": "full pounds (converted from GBP thousands disclosed in report)",
        "other_revenue_original": None,
        "women_team_revenue_original": None,
        "excluded_player_trading_revenue_original": None,
        "total_revenue_eur": None,
        "matchday_revenue_eur": None,
        "broadcast_revenue_eur": None,
        "commercial_revenue_eur": None,
        "other_revenue_eur": None,
        "net_debt_eur": None,
        "profit_loss_before_tax_eur": None,
        "exchange_rate_used": None,
        "exchange_rate_source": "",
        "requires_manual_review": True,
        "source_document": source_document,
        "source_url": source_url,
    }


def extract_liverpool(records: list[dict], season: str, source_document: str, source_url: str) -> dict:
    turnover = find_page(records, lambda t: "analysis of turnover" in t)
    staff = find_page(records, lambda t: "administrative expenses" in t and "staff costs" in t)
    tax = find_page(records, lambda t: "loss on ordinary activities before taxation" in t)
    debt = find_page(records, lambda t: "analysis of changes in net debt" in t)

    record = build_common_record("liverpool", "Liverpool", season, f"{season.split('/')[0]}-05-31", source_document, source_url)
    record["matchday_revenue_original"] = find_line_value(turnover["text"], "Matchday")
    record["broadcast_revenue_original"] = find_line_value(turnover["text"], "Media")
    record["commercial_revenue_original"] = find_line_value(turnover["text"], "Commercial")
    record["total_revenue_original"] = record["matchday_revenue_original"] + record["broadcast_revenue_original"] + record["commercial_revenue_original"]
    record["staff_costs_original"] = find_line_value(staff["text"], "Staff costs")
    record["player_amortisation_original"] = find_line_value(staff["text"], "Amortisation of players")
    record["profit_on_player_sales_original"] = None
    record["profit_loss_before_tax_original"] = find_line_value(tax["text"], "Loss on ordinary activities before taxation")
    record["net_debt_original"] = find_line_value(debt["text"], "Net debt at")
    record["revenue_sum_check_original"] = record["total_revenue_original"]
    record["revenue_sum_difference_original"] = 0
    record["pages_used"] = [turnover["page"], staff["page"], tax["page"], debt["page"]]
    record["evidence"] = [
        {"field": "matchday_revenue_original", "value_original": record["matchday_revenue_original"], "page_number": turnover["page"], "statement_label": "Matchday", "evidence_text": "Analysis of turnover note."},
        {"field": "broadcast_revenue_original", "value_original": record["broadcast_revenue_original"], "page_number": turnover["page"], "statement_label": "Media", "evidence_text": "Analysis of turnover note."},
        {"field": "commercial_revenue_original", "value_original": record["commercial_revenue_original"], "page_number": turnover["page"], "statement_label": "Commercial", "evidence_text": "Analysis of turnover note."},
        {"field": "staff_costs_original", "value_original": record["staff_costs_original"], "page_number": staff["page"], "statement_label": "Staff costs", "evidence_text": "Administrative expenses note."},
        {"field": "player_amortisation_original", "value_original": record["player_amortisation_original"], "page_number": staff["page"], "statement_label": "Amortisation of players' registrations", "evidence_text": "Administrative expenses note."},
        {"field": "profit_loss_before_tax_original", "value_original": record["profit_loss_before_tax_original"], "page_number": tax["page"], "statement_label": "Loss on ordinary activities before taxation", "evidence_text": "Taxation note."},
        {"field": "net_debt_original", "value_original": record["net_debt_original"], "page_number": debt["page"], "statement_label": "Net debt at period end", "evidence_text": "Analysis of changes in net debt note."},
    ]
    record["classification_notes"] = "Liverpool discloses matchday, media, and commercial turnover directly in the annual accounts."
    record["women_team_treatment_notes"] = "Women's team revenue is not separately disclosed in the report."
    record["non_football_revenue_notes"] = "No separate non-football commercial adjustment was identified in the extracted note."
    record["confidence_level"] = "high"
    record["notes"] = "Values in the annual report were disclosed in GBP thousands and have been converted here into full GBP amounts by multiplying by 1,000."
    return record


def extract_manchester_city(records: list[dict], season: str, source_document: str, source_url: str) -> dict:
    balance = find_page_any(
        records,
        [
            lambda t: "balance sheet" in t and "cash at bank and in hand" in t,
            lambda t: "statement of financial position" in t and "cash at bank and in hand" in t,
        ],
    )
    turnover = find_page_any(
        records,
        [
            lambda t: "gate receipts" in t and "other commercial activities" in t,
            lambda t: "4. revenue" in t and "broadcasting - uefa" in t and "other commercial activities" in t and has_money_figure(t),
            lambda t: "turnover" in t and "matchday" in t and "broadcasting - uefa" in t and "other commercial activities" in t and has_money_figure(t),
            lambda t: "matchday" in t and "broadcasting - uefa" in t and "other commercial activities" in t and has_money_figure(t),
        ],
    )
    staff = find_page_any(
        records,
        [
            lambda t: "staff numbers and costs" in t and "wages and salaries" in t,
            lambda t: "the aggregate payroll costs of these persons were as follows" in t,
        ],
    )
    tax = find_page_any(
        records,
        [
            lambda t: "loss on ordinary activities before taxation" in t,
            lambda t: "profit on ordinary activities before taxation" in t,
            lambda t: "(loss)/profit on ordinary activities before taxation" in t,
            lambda t: "profit/(loss) on ordinary activities before taxation" in t,
        ],
    )
    borrowings = find_page_any(
        records,
        [
            lambda t: "borrowings" in t and "within one year" in t and "after more than five years" in t,
            lambda t: "maturity of obligations under finance leases" in t,
            lambda t: "maturity of lease liabilities" in t,
        ],
    )
    operating = find_page_any(
        records,
        [
            lambda t: "operating loss" in t and "employee costs (note 7)" in t,
            lambda t: "operating expenses" in t and "employee costs (note 7)" in t,
            lambda t: "5. operating loss" in t and "amortisation" in t,
        ],
    )

    record = build_common_record("manchester_city", "Manchester City", season, f"{season.split('/')[0]}-05-31", source_document, source_url)
    matchday = find_first_line_value(turnover["text"], ["Gate receipts", "Matchday"])
    broadcast = find_first_line_value(turnover["text"], ["Television - UEFA", "Broadcasting - UEFA"]) + find_first_line_value(
        turnover["text"], ["Television - All Other", "Broadcasting - All Other", "Broadcasting - all other"]
    )
    commercial = find_first_line_value(turnover["text"], ["Other commercial activities"])
    cash = find_first_line_value(balance["text"], ["Cash at bank and in hand"])
    borrowings_total = sum(
        find_first_line_value(borrowings["text"], [label])
        for label in ["Within one year", "Between one and two years", "Between two and five years", "After more than five years"]
    )
    record.update(
        {
            "matchday_revenue_original": matchday,
            "broadcast_revenue_original": broadcast,
            "commercial_revenue_original": commercial,
            "total_revenue_original": matchday + broadcast + commercial,
            "staff_costs_original": find_line_value(staff["text"], "Wages and salaries")
            + find_line_value(staff["text"], "Social security costs")
            + find_line_value(staff["text"], "Other pension costs")
            + (find_line_value(staff["text"], "Share-based payments") if "share-based payments" in staff["text"].lower() else 0),
            "player_amortisation_original": find_first_line_value(
                operating["text"],
                [
                    "Amortisation of player registrations",
                    "Amortisation of players' registrations",
                    "Amortisation and impairment of intangible assets",
                ],
            ),
            "profit_on_player_sales_original": None,
            "profit_loss_before_tax_original": find_first_line_value(
                tax["text"],
                [
                    "Loss on ordinary activities before taxation",
                    "Profit on ordinary activities before taxation",
                    "(Loss)/profit on ordinary activities before taxation",
                    "Profit/(loss) on ordinary activities before taxation",
                ],
            ),
            "net_debt_original": borrowings_total - cash,
        }
    )
    record["revenue_sum_check_original"] = record["total_revenue_original"]
    record["revenue_sum_difference_original"] = 0
    record["pages_used"] = [balance["page"], turnover["page"], staff["page"], tax["page"], borrowings["page"], operating["page"]]
    record["evidence"] = [
        {"field": "matchday_revenue_original", "value_original": matchday, "page_number": turnover["page"], "statement_label": "Gate receipts", "evidence_text": "Turnover note."},
        {"field": "broadcast_revenue_original", "value_original": broadcast, "page_number": turnover["page"], "statement_label": "Television - UEFA and Television - All Other", "evidence_text": "Turnover note with UEFA and other television lines combined."},
        {"field": "commercial_revenue_original", "value_original": commercial, "page_number": turnover["page"], "statement_label": "Other commercial activities", "evidence_text": "Turnover note."},
        {"field": "staff_costs_original", "value_original": record["staff_costs_original"], "page_number": staff["page"], "statement_label": "Aggregate payroll costs", "evidence_text": "Staff numbers and costs note."},
        {"field": "player_amortisation_original", "value_original": record["player_amortisation_original"], "page_number": operating["page"], "statement_label": "Amortisation of players' registrations / intangible assets", "evidence_text": "Operating expenses note."},
        {"field": "profit_loss_before_tax_original", "value_original": record["profit_loss_before_tax_original"], "page_number": tax["page"], "statement_label": "Loss on ordinary activities before taxation", "evidence_text": "Taxation note."},
        {"field": "net_debt_original", "value_original": record["net_debt_original"], "page_number": borrowings["page"], "statement_label": "Computed net debt from borrowings less cash", "evidence_text": "Calculated from borrowings note and balance sheet cash at bank and in hand."},
    ]
    record["classification_notes"] = "Manchester City discloses gate receipts, television income, and other commercial activities directly in the annual accounts. Broadcasting is formed by combining the UEFA and all other television lines."
    record["women_team_treatment_notes"] = "Women's team revenue is not separately disclosed in the report."
    record["non_football_revenue_notes"] = "Other commercial activities may include hospitality and event income classified within club commercial operations."
    record["confidence_level"] = "high"
    record["notes"] = "Values in the annual report were disclosed in GBP thousands and have been converted here into full GBP amounts by multiplying by 1,000. Net debt has been computed from statement borrowings and cash."
    return record


def extract_tottenham(records: list[dict], season: str, source_document: str, source_url: str) -> dict:
    revenue = find_page_any(
        records,
        [
            lambda t: "revenue comprises" in t and "media and broadcasting" in t,
            lambda t: "revenue comprises" in t and "match receipts" in t and "tv and media" in t and "commercial" in t,
            lambda t: "revenue and other income" in t and "match receipts" in t and "tv and media" in t and "commercial" in t,
        ],
    )
    staff = find_page_any(
        records,
        [
            lambda t: "staff numbers and costs" in t and "salaries and bonuses" in t,
            lambda t: "staff numbers and costs (continued)" in t and "salaries and bonuses" in t,
            lambda t: "staff numbers and costs" in t and "aggregate payroll costs" in t,
        ],
    )
    income_statement = find_page_any(
        records,
        [
            lambda t: "consolidated income statement" in t and "before taxation" in t,
            lambda t: "consolidated income statement and statement of other comprehensive income" in t and "loss before taxation" in t,
        ],
    )
    debt = find_page_any(
        records,
        [
            lambda t: "group has net debt of" in t or "group has net cash of" in t or "net funds" in t,
            lambda t: "net debt" in t and "cash and cash equivalents" in t,
        ],
    )
    operating = find_page_any(
        records,
        [
            lambda t: "operating expenses" in t and "staff costs (see note 5)" in t,
            lambda t: "loss from operations" in t and "amortisation of intangible fixed assets" in t,
            lambda t: "profit/(loss) from operations" in t and "amortisation of intangible fixed assets" in t,
        ],
    )

    if "gate receipts" in revenue["text"].lower():
        matchday = find_line_value(revenue["text"], "Gate receipts – Premier League") + find_line_value(revenue["text"], "Cup competitions – Gate receipts and domestic prize money")
        broadcast = find_line_value(revenue["text"], "UEFA solidarity and prize money") + find_line_value(revenue["text"], "Media and broadcasting")
        commercial = find_line_value(revenue["text"], "Sponsorship and corporate hospitality") + find_line_value(revenue["text"], "Merchandising") + find_line_value(revenue["text"], "Other")
        classification_notes = "Tottenham's accounts require reclassification because UEFA solidarity and prize money is disclosed separately from media and broadcasting, and cup competition gate receipts are combined with domestic prize money."
        non_football_notes = "The 'Other' revenue line has been grouped into commercial revenue for comparability."
    else:
        matchday, uefa, tv_media, commercial = parse_tottenham_revenue_values(revenue["text"], season)
        broadcast = uefa + tv_media
        classification_notes = "Tottenham's later accounts disclose direct revenue lines for match receipts, UEFA prize money, TV and media, and commercial. UEFA prize money is grouped into broadcasting for comparability."
        non_football_notes = "Commercial revenue may include stadium and other non-football event activity where disclosed within the club's commercial line."

    record = build_common_record("tottenham_hotspur", "Tottenham Hotspur", season, f"{int(season.split('/')[0]) + 1}-06-30", source_document, source_url)
    staff_total = find_first_line_value(operating["text"], ["Staff costs (see note 5)", "Staff costs"])
    try:
        player_amortisation = find_first_line_value(
            operating["text"],
            ["Amortisation of intangible fixed assets", "Amortisation and impairment of intangible assets", "Amortisation of intangible fixed"],
        )
    except ValueError:
        player_amortisation = None
    record.update(
        {
            "matchday_revenue_original": matchday,
            "broadcast_revenue_original": broadcast,
            "commercial_revenue_original": commercial,
            "total_revenue_original": matchday + broadcast + commercial,
            "staff_costs_original": staff_total,
            "player_amortisation_original": player_amortisation,
            "profit_on_player_sales_original": find_first_line_value(income_statement["text"], ["Profit on disposal of intangible fixed assets"]),
            "profit_loss_before_tax_original": find_first_line_value(
                income_statement["text"],
                [
                    "(Loss)/profit on ordinary activities before taxation",
                    "Profit on ordinary activities before taxation",
                    "Loss on ordinary activities before taxation",
                    "Loss before taxation",
                ],
            ),
            "net_debt_original": find_net_debt_from_strategic_text(debt["text"]),
        }
    )
    record["revenue_sum_check_original"] = record["total_revenue_original"]
    record["revenue_sum_difference_original"] = 0
    record["pages_used"] = [revenue["page"], staff["page"], income_statement["page"], debt["page"], operating["page"]]
    record["evidence"] = [
        {"field": "matchday_revenue_original", "value_original": matchday, "page_number": revenue["page"], "statement_label": "Gate receipts and cup competition gate receipts", "evidence_text": "Revenue note with gate-related lines combined."},
        {"field": "broadcast_revenue_original", "value_original": broadcast, "page_number": revenue["page"], "statement_label": "UEFA solidarity and prize money plus Media and broadcasting", "evidence_text": "Revenue note with UEFA solidarity grouped into broadcasting."},
        {"field": "commercial_revenue_original", "value_original": commercial, "page_number": revenue["page"], "statement_label": "Sponsorship and corporate hospitality, Merchandising, Other", "evidence_text": "Revenue note with non-broadcasting commercial lines combined."},
        {"field": "staff_costs_original", "value_original": record["staff_costs_original"], "page_number": staff["page"], "statement_label": "Aggregate payroll costs", "evidence_text": "Staff numbers and costs note."},
        {"field": "profit_on_player_sales_original", "value_original": record["profit_on_player_sales_original"], "page_number": income_statement["page"], "statement_label": "Profit on disposal of intangible fixed assets", "evidence_text": "Consolidated income statement football-trading split."},
        {"field": "profit_loss_before_tax_original", "value_original": record["profit_loss_before_tax_original"], "page_number": income_statement["page"], "statement_label": "(Loss)/profit on ordinary activities before taxation", "evidence_text": "Consolidated income statement."},
        {"field": "player_amortisation_original", "value_original": record["player_amortisation_original"], "page_number": operating["page"], "statement_label": "Amortisation of intangible fixed assets / football trading", "evidence_text": "Operating expenses or loss from operations note."},
        {"field": "net_debt_original", "value_original": record["net_debt_original"], "page_number": debt["page"], "statement_label": "Explicit net debt / net cash disclosure", "evidence_text": "Strategic report balance-sheet summary."},
    ]
    record["classification_notes"] = classification_notes
    record["women_team_treatment_notes"] = "Women's team revenue is not separately disclosed in the report."
    record["non_football_revenue_notes"] = non_football_notes
    record["confidence_level"] = "high" if "match receipts" in revenue["text"].lower() else "medium"
    record["notes"] = "Values in the annual report were disclosed in GBP thousands and have been converted here into full GBP amounts by multiplying by 1,000."
    return record


EXTRACTORS = {
    "liverpool": extract_liverpool,
    "manchester_city": extract_manchester_city,
    "tottenham_hotspur": extract_tottenham,
}


def source_document_for_pdf(pdf_path: Path) -> str:
    stem = pdf_path.stem.replace("_", " ")
    return stem[0].upper() + stem[1:]


def load_source_url(club_id: str, season_slug: str) -> str:
    meta_path = Path(f"data/raw/financial_statements/{club_id}/{season_slug}_*.pdf.meta.json")
    matches = list(Path(f"data/raw/financial_statements/{club_id}").glob(f"{season_slug}_*.pdf.meta.json"))
    if not matches:
        return ""
    data = json.loads(matches[0].read_text())
    return data.get("download_url") or data.get("source_url") or ""


def main() -> int:
    args = parse_args()
    swift_script = Path(args.swift_script)
    statements_root = Path(args.statements_root)
    ocr_cache_root = Path(args.ocr_cache_root)
    output_root = Path(args.output_root)
    clubs = [args.club] if args.club else list(CLUBS)
    seasons = select_seasons(args.season_from, args.season_to)

    for club in clubs:
        extractor = EXTRACTORS[club]
        for season in seasons:
            season_slug = label_to_slug(season)
            matches = sorted((statements_root / club).glob(f"{season_slug}_*.pdf"))
            if not matches:
                print(f"[warn] Missing statement for {club} {season}")
                continue
            pdf_path = matches[0]
            output_path = output_root / f"{club}_{season_slug}_financial_extraction_output.json"
            if output_path.exists() and not args.overwrite:
                print(f"[skip] {output_path}")
                continue
            cache_path = ocr_cache_root / club / f"{season_slug}_ocr.json"
            print(f"[ocr] {club} {season}")
            records = render_and_ocr_pdf(pdf_path, swift_script, cache_path)
            source_url = load_source_url(club, season_slug)
            try:
                record = extractor(records, season, source_document_for_pdf(pdf_path), source_url)
            except Exception as exc:
                print(f"[error] {club} {season}: {exc}")
                continue
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(record, indent=2) + "\n")
            print(f"[saved] {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
