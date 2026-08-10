# Data Directory

This folder holds the project’s data pipeline outputs from raw collection through dashboard-ready exports.

## `data/raw/`

Unchanged source outputs. Never edit these files manually.

Raw storage is split by collection method:

- `data/raw/transfermarkt/`
  Raw Transfermarkt outputs, primarily saved club transfers HTML pages and related raw support files.
  Recommended club page layout:
  `data/raw/transfermarkt/club_transfer_pages/{league_key}/{season}/{club_id}/`
  Recommended manager history layout:
  `data/raw/transfermarkt/manager_history_pages/{league_key}/all_years/{club_id}/`
  Recommended achievements layout:
  `data/raw/transfermarkt/achievement_pages/{league_key}/all_years/{club_id}/`
- `data/raw/ai_agents/`
  Structured JSON outputs produced by AI-agent research tasks.
- `data/raw/financial_statements/`
  Downloaded annual reports, Companies House filings, SEC reports, or HTML statement pages for club finance work.
  Recommended layout:
  `data/raw/financial_statements/{club_id}/`

Raw files should preserve as much collection context as possible, including:

- source name
- source URL where relevant
- date collected
- collection method
- confidence notes

For club transfer scraping, save the raw page HTML exactly as collected before any parsing.
For club finance work, save the original PDF or HTML statement file unchanged before any extraction.

## `data/clean/`

Standardized intermediate files created after parsing and cleaning raw inputs.

- Club names, IDs, seasons, and currencies should be normalized here.
- Cleaning scripts should add notes when fields cannot be parsed automatically.
- These files are the staging area before validation and export.
- Keep the top-level aggregate CSVs for whole-project workflows.
- Also write browseable partitions when helpful, for example:
  `data/clean/transfermarkt/by_partition/{league_key}/{season}/{club_id}/`
  `data/clean/transfermarkt/by_league/{league_key}/`

## `data/final/`

Dashboard-ready CSV and JSON files.

- Schemas should be stable and documented.
- Sample outputs should be clearly labeled.
- Production exports should be easy for the React app to consume.
- Keep a global dashboard export, plus per-league exports under:
  `data/final/by_league/{league_key}/`
- Finance exports live alongside the footballing datasets, including:
  `data/final/club_revenue_dataset.csv`

## `data/reference/`

Reference tables shared across the project, such as:

- club IDs
- league definitions
- season mappings
- source registry
- inflation factors
- other shared lookup tables

## Club finance workflow

The revenue dataset adds a parallel finance pipeline:

- `data/raw/ai_agents/statement_fetcher_outputs/`
  JSON outputs describing where an official report or filing was found.
- `data/raw/ai_agents/financial_extraction_outputs/`
  JSON outputs containing extracted revenue values, evidence, and classification notes.
- `data/clean/club_finances/`
  Standardized revenue tables and flattened evidence tables.
- `data/final/club_revenue_dataset.csv`
  Dashboard-ready export for revenue splits and shares.

## Working rule

If a value is transformed, corrected, or merged, that work belongs in `clean/` or `final/`, not in `raw/`.
