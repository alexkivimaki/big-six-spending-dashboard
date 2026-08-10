#!/usr/bin/env python3

"""Backfill Manchester United finance extraction rows from scanned statements using OCR."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

import fitz


CLUB_ID = "manchester_united"
CLUB_NAME = "Manchester United"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season-from", default="2016/17")
    parser.add_argument("--season-to", default="2020/21")
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
    token = token.replace(".", "")
    token = token.replace("£", "").replace("€", "").replace("$", "")
    token = token.replace("O", "0")
    value = int(token)
    return -value if negative else value


def to_full_pounds(token: str) -> int:
    return clean_number(token) * 1000


def first_number_after(text: str, phrase: str, window: int = 700) -> int:
    lowered = text.lower()
    idx = lowered.find(phrase.lower())
    if idx == -1:
        raise ValueError(f"Phrase not found: {phrase}")
    snippet = text[idx : idx + window]
    matches = re.findall(r"\(?[0-9][0-9,]*\)?", snippet)
    if not matches:
        raise ValueError(f"No numbers found after phrase: {phrase}")
    return to_full_pounds(matches[0])


def find_page(pdf_path: Path, swift_script: Path, predicates: list[tuple[str, ...]], page_range: range) -> tuple[int, str]:
    previews: list[str] = []
    for page_number in page_range:
        text = render_and_ocr(pdf_path, page_number, swift_script)
        lowered = text.lower()
        previews.append(f"page {page_number}: {normalize_spaces(text)[:180]}")
        if any(all(phrase.lower() in lowered for phrase in phrases) for phrases in predicates):
            return page_number, text
    phrase_preview = " | ".join(" & ".join(group) for group in predicates)
    preview_text = " || ".join(previews[:8])
    raise ValueError(f"Could not find page matching: {phrase_preview}. searched={preview_text}")


def maybe_append_page(pdf_path: Path, swift_script: Path, page_number: int, text: str, max_page: int) -> str:
    if page_number >= max_page:
        return text
    next_text = render_and_ocr(pdf_path, page_number + 1, swift_script)
    return text + "\n" + next_text


def find_revenue_page_by_parsing(pdf_path: Path, swift_script: Path, season_start: int, page_range: range, max_page: int) -> tuple[int, str]:
    for page_number in page_range:
        text = render_and_ocr(pdf_path, page_number, swift_script)
        combined = maybe_append_page(pdf_path, swift_script, page_number, text, max_page)
        lowered = combined.lower()
        if not any(
            phrase in lowered
            for phrase in [
                "revenue can be analysed",
                "disaggregation of revenue",
                "revenue from contracts with customers",
            ]
        ):
            continue
        try:
            parse_revenue_split(combined, season_start)
            return page_number, combined
        except Exception:
            continue
    raise ValueError("Could not locate a parsable Manchester United revenue note")


def find_staff_operating_page_by_parsing(pdf_path: Path, swift_script: Path, page_range: range, max_page: int) -> tuple[int, str]:
    for page_number in page_range:
        text = render_and_ocr(pdf_path, page_number, swift_script)
        combined = maybe_append_page(pdf_path, swift_script, page_number, text, max_page)
        try:
            parse_staff_and_amortisation(combined, combined)
            return page_number, combined
        except Exception:
            continue
    raise ValueError("Could not locate a parsable Manchester United operating/staff note")


def parse_profit_page(text: str) -> tuple[int, int]:
    squashed = normalize_spaces(text)
    patterns = [
        (
            r"loss on ordinary activities before tax.*?([\(]?[0-9][0-9,]*[)]?)",
            r"(loss)/profit on disposal of intangible assets.*?([\(]?[0-9][0-9,]*[)]?)",
        ),
        (
            r"loss on ordinary activities before taxation.*?([\(]?[0-9][0-9,]*[)]?)",
            r"profit on disposal of intangible assets.*?([\(]?[0-9][0-9,]*[)]?)",
        ),
        (
            r"profit/(loss) before taxation.*?([\(]?[0-9][0-9,]*[)]?)",
            r"profit on disposal of intangible assets.*?([\(]?[0-9][0-9,]*[)]?)",
        ),
        (
            r"profit before tax.*?([\(]?[0-9][0-9,\.]*[)]?)",
            r"profit on disposal of intangible assets.*?([\(]?[0-9][0-9,\.]*[)]?)",
        ),
        (
            r"loss before income tax.*?([\(]?[0-9][0-9,\.]*[)]?)",
            r"profit on disposal of intangible assets.*?([\(]?[0-9][0-9,\.]*[)]?)",
        ),
        (
            r"\(loss\)/profit before income tax.*?([\(]?[0-9][0-9,\.]*[)]?)",
            r"profit on disposal of intangible assets.*?([\(]?[0-9][0-9,\.]*[)]?)",
        ),
    ]
    for pbt_pattern, sale_pattern in patterns:
        pbt_match = re.search(pbt_pattern, squashed, flags=re.I)
        sale_match = re.search(sale_pattern, squashed, flags=re.I)
        if pbt_match and sale_match:
            return to_full_pounds(pbt_match.group(1)), to_full_pounds(sale_match.group(1))

    phrases = [
        "loss on ordinary activities before tax",
        "loss on ordinary activities before taxation",
        "profit/(loss) before taxation",
        "profit before tax",
        "loss before income tax",
        "(loss)/profit before income tax",
    ]
    pbt = None
    for phrase in phrases:
        try:
            pbt = first_number_after(text, phrase)
            break
        except ValueError:
            continue
    if pbt is None:
        raise ValueError("Could not parse profit before tax from Manchester United income statement")

    for phrase in [
        "(loss)/profit on disposal of intangible assets",
        "profit on disposal of intangible assets",
    ]:
        try:
            sale = first_number_after(text, phrase)
            return pbt, sale
        except ValueError:
            continue
    raise ValueError("Could not parse player-sale result from Manchester United income statement")


def parse_revenue_split(text: str, season_start: int) -> tuple[int, int, int, int]:
    current_year = season_start + 1
    squashed = normalize_spaces(text)
    patterns = [
        rf"{current_year}\s+£?000\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)",
        rf"commercial\s+broadcasting\s+matchday\s+revenue.*?{current_year}\s+£?000\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)",
        rf"commercial\s+broad\w+\s+matchday\s+{current_year}\s+£?[0-9'° ]*([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)",
        rf"commercial\s+broad\w+\s+matchday.*?{current_year}\s+£?[0-9'° ]*([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, squashed, flags=re.I)
        if match:
            return tuple(to_full_pounds(match.group(i)) for i in range(1, 5))

    anchor_phrases = [
        "Revenue can be analysed into its three main components as follows",
        "Disaggregation of revenue from contracts with customers",
        "Revenue from contracts with customers",
    ]
    for phrase in anchor_phrases:
        lowered = text.lower()
        idx = lowered.find(phrase.lower())
        if idx != -1:
            snippet = text[idx : idx + 1200]
            numbers = re.findall(r"\(?[0-9][0-9,]*\)?", snippet)
            if len(numbers) >= 4:
                return tuple(to_full_pounds(n) for n in numbers[:4])

    label_match = re.search(
        rf"commercial\s+broad\w+\s+matchday.*?{current_year}\s+£?[0-9'° ]*(?:000)?\s*([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)",
        squashed,
        flags=re.I,
    )
    if label_match:
        return tuple(to_full_pounds(label_match.group(i)) for i in range(1, 5))

    values = []
    for phrase in ["Commercial", "Broadcasting", "Matchday", "Revenue"]:
        values.append(first_number_after(text, phrase, window=1200))
    return tuple(values)


def parse_staff_and_amortisation(staff_text: str, operating_text: str) -> tuple[int, int]:
    squashed_operating = normalize_spaces(operating_text)
    staff_patterns = [
        r"employee benefit expenses?\s+\(note\s+[0-9il]+\)\s+(\(?[0-9][0-9,]*\)?)",
        r"employee benefit expenses?\s+(\(?[0-9][0-9,]*\)?)",
        r"employee benefit expense\s+\(note\s+[0-9il]+\)\s+(\(?[0-9][0-9,]*\)?)",
    ]
    amort_patterns = [
        r"amortisation(?: of intangible assets)?\s+\(note\s+[0-9il]+\)\s+(\(?[0-9][0-9,]*\)?)",
        r"amortisation(?: of intangible assets)?\s+(\(?[0-9][0-9,]*\)?)",
    ]
    for staff_pattern in staff_patterns:
        staff_match = re.search(staff_pattern, squashed_operating, flags=re.I)
        if not staff_match:
            continue
        for amort_pattern in amort_patterns:
            amort_match = re.search(amort_pattern, squashed_operating, flags=re.I)
            if amort_match:
                return to_full_pounds(staff_match.group(1)), to_full_pounds(amort_match.group(1))

    staff_total = None
    for phrase in ["Employee benefit expense", "Staff costs", "Employee benefit expenses"]:
        try:
            staff_total = first_number_after(staff_text, phrase)
            break
        except ValueError:
            continue
    if staff_total is None:
        raise ValueError("Could not parse Manchester United staff costs")

    for phrase in ["Amortisation of intangible assets", "Amortisation of players' registrations", "Amortization of players' registrations"]:
        try:
            amortisation = first_number_after(operating_text, phrase)
            return staff_total, amortisation
        except ValueError:
            continue
    try:
        return staff_total, first_number_after(operating_text, "Amortisation", window=1200)
    except ValueError:
        pass
    raise ValueError("Could not parse Manchester United player amortisation")


def parse_cash(text: str) -> int:
    for phrase in ["cash at bank and in hand", "cash and cash equivalents"]:
        try:
            return first_number_after(text, phrase)
        except ValueError:
            continue
    raise ValueError("Could not parse Manchester United cash balance")


def parse_debt_components(text: str) -> tuple[int, int]:
    senior_notes = None
    for phrase in [
        "senior secured notes",
        "senior notes",
    ]:
        try:
            senior_notes = first_number_after(text, phrase)
            break
        except ValueError:
            continue
    if senior_notes is None:
        raise ValueError("Could not parse Manchester United senior secured notes")

    term_loan = None
    for phrase in [
        "secured term loan",
        "term loan",
    ]:
        try:
            term_loan = first_number_after(text, phrase)
            break
        except ValueError:
            continue
    if term_loan is None:
        raise ValueError("Could not parse Manchester United secured term loan")

    return senior_notes, term_loan


def parse_borrowings_from_balance(text: str) -> int:
    squashed = normalize_spaces(text)
    matches = re.findall(r"borrowings[:;]?\s+(\(?[0-9][0-9,]*\)?)", squashed, flags=re.I)
    if len(matches) >= 2:
        return to_full_pounds(matches[0]) + to_full_pounds(matches[1])
    raise ValueError("Could not parse Manchester United balance-sheet borrowings")


def build_output(source_meta: dict, season: str, values: dict[str, int], pages_used: list[int]) -> dict:
    return {
        "club_id": CLUB_ID,
        "club_name": CLUB_NAME,
        "season": season,
        "financial_year_end": source_meta.get("financial_year_end", ""),
        "currency_original": "GBP",
        "units_original": "full pounds (converted from GBP thousands disclosed in report, with debt-note borrowings disclosed in GBP millions converted to full GBP)",
        "total_revenue_original": values["revenue_total"],
        "matchday_revenue_original": values["matchday"],
        "broadcast_revenue_original": values["broadcast"],
        "commercial_revenue_original": values["commercial"],
        "other_revenue_original": None,
        "women_team_revenue_original": None,
        "excluded_player_trading_revenue_original": None,
        "staff_costs_original": values["staff_costs"],
        "net_debt_original": values["net_debt"],
        "player_amortisation_original": values["player_amortisation"],
        "profit_on_player_sales_original": values["profit_on_player_sales"],
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
        "revenue_sum_check_original": values["commercial"] + values["broadcast"] + values["matchday"],
        "revenue_sum_difference_original": values["commercial"] + values["broadcast"] + values["matchday"] - values["revenue_total"],
        "pages_used": pages_used,
        "evidence": [
            {
                "field": "total_revenue_original",
                "value_original": values["revenue_total"],
                "page_number": values["turnover_page"],
                "statement_label": "Revenue",
                "evidence_text": "Scanned Manchester United Football Club Limited annual accounts revenue note. Values disclosed in GBP thousands and converted to full GBP.",
            },
            {
                "field": "commercial_revenue_original",
                "value_original": values["commercial"],
                "page_number": values["turnover_page"],
                "statement_label": "Commercial",
                "evidence_text": "Revenue note in the club-limited filing. Values disclosed in GBP thousands and converted to full GBP.",
            },
            {
                "field": "broadcast_revenue_original",
                "value_original": values["broadcast"],
                "page_number": values["turnover_page"],
                "statement_label": "Broadcasting",
                "evidence_text": "Revenue note in the club-limited filing. Values disclosed in GBP thousands and converted to full GBP.",
            },
            {
                "field": "matchday_revenue_original",
                "value_original": values["matchday"],
                "page_number": values["turnover_page"],
                "statement_label": "Matchday",
                "evidence_text": "Revenue note in the club-limited filing. Values disclosed in GBP thousands and converted to full GBP.",
            },
            {
                "field": "staff_costs_original",
                "value_original": values["staff_costs"],
                "page_number": values["staff_page"],
                "statement_label": "Employee benefit expense / Staff costs",
                "evidence_text": "Employees and directors note in the scanned annual accounts. Values disclosed in GBP thousands and converted to full GBP.",
            },
            {
                "field": "player_amortisation_original",
                "value_original": values["player_amortisation"],
                "page_number": values["operating_page"],
                "statement_label": "Amortisation of intangible assets",
                "evidence_text": "Operating-expenses note in the scanned annual accounts. Values disclosed in GBP thousands and converted to full GBP.",
            },
            {
                "field": "profit_on_player_sales_original",
                "value_original": values["profit_on_player_sales"],
                "page_number": values["profit_page"],
                "statement_label": "Profit on disposal of intangible assets",
                "evidence_text": "Income statement in the scanned annual accounts. Values disclosed in GBP thousands and converted to full GBP.",
            },
            {
                "field": "profit_loss_before_tax_original",
                "value_original": values["profit_before_tax"],
                "page_number": values["profit_page"],
                "statement_label": "Loss on ordinary activities before tax",
                "evidence_text": "Income statement in the scanned annual accounts. Values disclosed in GBP thousands and converted to full GBP.",
            },
            {
                "field": "net_debt_original",
                "value_original": values["net_debt"],
                "page_number": values["debt_page"],
                "statement_label": "Estimated net debt from fellow-subsidiary senior secured notes and secured term loan less cash at bank and in hand",
                "evidence_text": "Calculated from the debt-of-fellow-subsidiary note less cash at bank and in hand from the balance sheet.",
            },
        ],
        "classification_notes": "This season was extracted from the downloaded Manchester United Football Club Limited Companies House filing. Under the club-limited FRS 101 / Companies House layouts the revenue note still discloses Commercial, Broadcasting and Matchday directly, but the commercial line remains materially narrower than the broader plc commercial segment used in later seasons.",
        "women_team_treatment_notes": "Women's team revenue is not separately disclosed in the source used here.",
        "non_football_revenue_notes": "The revenue note states the principal activity is the operation of a professional football club and all activities support that operation. No separate non-football revenue adjustment was identified within the club-limited revenue note used here.",
        "confidence_level": "medium",
        "requires_manual_review": True,
        "source_document": source_meta.get("report_title", ""),
        "source_url": source_meta.get("source_url", ""),
        "notes": "Scanned PDF extraction. Debt is not disclosed as a single company net-debt line, so net debt has been estimated as fellow-subsidiary senior secured notes plus secured term loan less company cash at bank and in hand.",
    }


def load_meta(pdf_path: Path) -> dict:
    meta_path = pdf_path.with_suffix(pdf_path.suffix + ".meta.json")
    if not meta_path.exists():
        return {"report_title": pdf_path.stem.replace("_", " "), "source_url": ""}
    return json.loads(meta_path.read_text())


def process_season(pdf_path: Path, output_path: Path, swift_script: Path, season: str) -> None:
    season_start = int(season.split("/")[0])
    doc = fitz.open(pdf_path)

    profit_page, profit_text = find_page(
        pdf_path,
        swift_script,
        [
            ("income statement", "revenue"),
            ("statement of profit or loss", "revenue"),
            ("income statement", "loss before tax"),
            ("income statement", "loss before taxation"),
            ("statement of profit or loss", "loss before income tax"),
            ("statement of profit or loss", "loss before tax"),
            ("statement of profit or loss", "loss before taxation"),
            ("consolidated income statement", "before tax"),
            ("profit and loss account", "before tax"),
            ("loss on ordinary activities before tax",),
        ],
        range(8, min(18, len(doc)) + 1),
    )
    balance_page, balance_text = find_page(
        pdf_path,
        swift_script,
        [
            ("balance sheet",),
        ],
        range(9, min(19, len(doc)) + 1),
    )
    balance_text = maybe_append_page(pdf_path, swift_script, balance_page, balance_text, len(doc))
    turnover_page, turnover_text = find_revenue_page_by_parsing(
        pdf_path, swift_script, season_start, range(15, min(35, len(doc)) + 1), len(doc)
    )
    operating_page, operating_text = find_staff_operating_page_by_parsing(
        pdf_path, swift_script, range(18, min(35, len(doc)) + 1), len(doc)
    )
    staff_page, staff_text = operating_page, operating_text

    revenue_total, commercial, broadcast, matchday = parse_revenue_split(turnover_text, season_start)
    staff_costs, amortisation = parse_staff_and_amortisation(staff_text, operating_text)
    profit_before_tax, player_sale_result = parse_profit_page(profit_text)
    cash = parse_cash(balance_text)
    debt_page = balance_page
    try:
        debt_page, debt_text = find_page(
            pdf_path,
            swift_script,
            [
                ("senior secured notes",),
                ("secured term loan",),
                ("fellow subsidiary senior secured notes",),
            ],
            range(24, min(40, len(doc)) + 1),
        )
        senior_notes, term_loan = parse_debt_components(debt_text)
        net_debt = senior_notes + term_loan - cash
    except Exception:
        net_debt = parse_borrowings_from_balance(balance_text) - cash

    values = {
        "revenue_total": revenue_total,
        "commercial": commercial,
        "broadcast": broadcast,
        "matchday": matchday,
        "staff_costs": staff_costs,
        "player_amortisation": amortisation,
        "profit_on_player_sales": player_sale_result,
        "profit_before_tax": profit_before_tax,
        "net_debt": net_debt,
        "turnover_page": turnover_page,
        "staff_page": staff_page,
        "operating_page": operating_page,
        "profit_page": profit_page,
        "debt_page": debt_page,
    }
    payload = build_output(load_meta(pdf_path), season, values, [profit_page, balance_page, turnover_page, operating_page, staff_page, debt_page])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"[saved] {output_path}")


def main() -> int:
    args = parse_args()
    swift_script = Path(args.swift_script)
    statements_root = Path(args.statements_root)
    output_root = Path(args.output_root)

    for season in select_seasons(args.season_from, args.season_to):
        season_slug = label_to_slug(season)
        pdf_matches = sorted((statements_root / CLUB_ID).glob(f"{season_slug}_*.pdf"))
        if not pdf_matches:
            print(f"[warn] Missing statement for {season}")
            continue
        output_path = output_root / f"{CLUB_ID}_{season_slug}_financial_extraction_output.json"
        if output_path.exists() and not args.overwrite:
            print(f"[skip] {output_path}")
            continue
        try:
            process_season(pdf_matches[0], output_path, swift_script, season)
        except Exception as exc:
            print(f"[error] {season}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
