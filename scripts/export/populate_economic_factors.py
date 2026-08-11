#!/usr/bin/env python3

"""Populate season-level economic factors for dashboard exports."""

from __future__ import annotations

import csv
from pathlib import Path


INPUT_PATH = Path("data/reference/economic_factors.csv")
OUTPUT_PATH = Path("data/reference/economic_factors.csv")

FX_SOURCE = (
    "ONS average sterling exchange rates: THAP (GBP/EUR) and AUSS (GBP/USD), "
    "UK trade time series (MRET), accessed 2026-08-11"
)
INFLATION_SOURCE = "ONS CPI INDEX 00: ALL ITEMS 2015=100 (D7BT), accessed 2026-08-11"

GBP_TO_EUR_ANNUAL = {
    1997: 1.4493,
    1998: 1.4887,
    1999: 1.5192,
    2000: 1.6422,
    2001: 1.6087,
    2002: 1.5909,
    2003: 1.4456,
    2004: 1.4739,
    2005: 1.4629,
    2006: 1.4670,
    2007: 1.4619,
    2008: 1.2588,
    2009: 1.1233,
    2010: 1.1664,
    2011: 1.1527,
    2012: 1.2337,
    2013: 1.1776,
    2014: 1.2411,
    2015: 1.3782,
    2016: 1.2233,
    2017: 1.1413,
    2018: 1.1305,
    2019: 1.1405,
    2020: 1.1250,
    2021: 1.1633,
    2022: 1.1732,
    2023: 1.1500,
    2024: 1.1815,
    2025: 1.1673,
}

GBP_TO_USD_ANNUAL = {
    1997: 1.6382,
    1998: 1.6574,
    1999: 1.6180,
    2000: 1.5151,
    2001: 1.4400,
    2002: 1.5035,
    2003: 1.6353,
    2004: 1.8323,
    2005: 1.8189,
    2006: 1.8430,
    2007: 2.0022,
    2008: 1.8528,
    2009: 1.5665,
    2010: 1.5460,
    2011: 1.6030,
    2012: 1.5851,
    2013: 1.5644,
    2014: 1.6477,
    2015: 1.5286,
    2016: 1.3542,
    2017: 1.2888,
    2018: 1.3350,
    2019: 1.2766,
    2020: 1.2837,
    2021: 1.3757,
    2022: 1.2362,
    2023: 1.2434,
    2024: 1.2783,
    2025: 1.3185,
}

CPI_ANNUAL = {
    1997: 70.1,
    1998: 71.2,
    1999: 72.1,
    2000: 72.7,
    2001: 73.6,
    2002: 74.5,
    2003: 75.5,
    2004: 76.5,
    2005: 78.1,
    2006: 79.9,
    2007: 81.8,
    2008: 84.7,
    2009: 86.6,
    2010: 89.4,
    2011: 93.4,
    2012: 96.1,
    2013: 98.5,
    2014: 100.0,
    2015: 100.0,
    2016: 100.7,
    2017: 103.4,
    2018: 105.9,
    2019: 107.8,
    2020: 108.7,
    2021: 111.6,
    2022: 121.7,
    2023: 130.5,
    2024: 133.9,
    2025: 138.4,
}

GBP_TO_EUR_BASE_SEASON_MONTHS = [
    1.1550,
    1.1506,
    1.1473,
    1.1368,
    1.1429,
    1.1523,
    1.1483,
    1.1541,
    1.1505,
    1.1553,
]

GBP_TO_USD_BASE_SEASON_MONTHS = [
    1.3450,
    1.3505,
    1.3351,
    1.3143,
    1.3384,
    1.3527,
    1.3576,
    1.3334,
    1.3477,
    1.3495,
]

CPI_BASE_SEASON_MONTHS = [
    139.3,
    139.3,
    139.8,
    139.5,
    140.1,
    139.5,
    140.1,
    141.0,
    142.1,
    142.4,
]


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


BASE_SEASON_CPI = mean(CPI_BASE_SEASON_MONTHS)


def build_row_for_season(season: str) -> dict[str, str] | None:
    if season == "2025/26":
        gbp_to_eur_rate = mean(GBP_TO_EUR_BASE_SEASON_MONTHS)
        gbp_to_usd_rate = mean(GBP_TO_USD_BASE_SEASON_MONTHS)
        inflation_adjustment = 1.0
        notes = (
            "Season factors use monthly averages from August 2025 through May 2026. "
            "Inflation adjustment factor is 1.0 because 2025/26 is the base season."
        )
    else:
        start_year = int(season[:4])
        end_year = start_year + 1
        required_years = [start_year, end_year]
        if any(year not in GBP_TO_EUR_ANNUAL or year not in GBP_TO_USD_ANNUAL or year not in CPI_ANNUAL for year in required_years):
            return None
        gbp_to_eur_rate = mean([GBP_TO_EUR_ANNUAL[start_year], GBP_TO_EUR_ANNUAL[end_year]])
        gbp_to_usd_rate = mean([GBP_TO_USD_ANNUAL[start_year], GBP_TO_USD_ANNUAL[end_year]])
        season_cpi = mean([CPI_ANNUAL[start_year], CPI_ANNUAL[end_year]])
        inflation_adjustment = BASE_SEASON_CPI / season_cpi
        notes = (
            "Season factors use the mean of the two surrounding ONS annual averages "
            f"for calendar years {start_year} and {end_year}."
        )

    eur_to_usd_rate = gbp_to_usd_rate / gbp_to_eur_rate
    return {
        "gbp_to_eur_rate": f"{gbp_to_eur_rate:.6f}",
        "eur_to_usd_rate": f"{eur_to_usd_rate:.6f}",
        "gbp_to_usd_rate": f"{gbp_to_usd_rate:.6f}",
        "inflation_adjustment_to_2025_26": f"{inflation_adjustment:.6f}",
        "fx_source": FX_SOURCE,
        "inflation_source": INFLATION_SOURCE,
        "notes": notes,
    }


def main() -> int:
    with INPUT_PATH.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0].keys()) if rows else []

    updated = 0
    for row in rows:
        season = str(row.get("season") or "").strip()
        computed = build_row_for_season(season)
        if computed is None:
            continue
        row.update(computed)
        updated += 1

    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[saved] {OUTPUT_PATH}")
    print(f"[done] Populated {updated} season rows with official economic factors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
