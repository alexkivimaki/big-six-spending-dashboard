# Scripts Directory

This folder holds the first viable data pipeline for the project.

## Intended flow

1. Collect raw Transfermarkt outputs into `data/raw/transfermarkt/`
   Primary path: direct club transfers page HTML scraping
   Secondary path: optional API support scripts for player-level exploration
2. Save AI-agent research outputs into `data/raw/ai_agents/`
   Wage collection tasks and outputs also live here
3. Download annual reports into `data/raw/financial_statements/` for finance work
4. Clean raw inputs into standardized CSV files under `data/clean/`
5. Validate cleaned and combined datasets
6. Export dashboard-ready CSV and JSON files

## Main folders

### `collect/`
Collectors that fetch Transfermarkt pages, call optional support endpoints, or download club financial statements and save raw responses unchanged.

### `clean/`
Cleaners that normalize club-page HTML, optional API payloads, financial extraction JSON, and other AI-agent outputs into stable CSV schemas.

### `validate/`
Validation scripts for required columns, identifiers, seasons, duplicates, and formula checks.

### `export/`
Export scripts that combine clean datasets into frontend-ready outputs.

### `agents/`
Task generators that prepare club-season JSON tasks for manual or external AI-agent use without calling an AI API directly.

## Validation helper

The repository also includes a simple required-column checker:

```bash
python3 scripts/validate/check_required_columns.py data/final/club_season_finances.sample.csv club_season_finances
python3 scripts/validate/check_required_columns.py data/final/club_season_performance.sample.csv club_season_performance
```

## Conventions

- Keep raw files untouched after collection.
- Prefer readable Python with standard library plus `requests` and `pandas`.
- Keep source, confidence, and notes fields wherever possible.
