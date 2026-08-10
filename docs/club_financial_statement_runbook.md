# Club Financial Statement Runbook

This runbook documents the practical process used to collect and extract Arsenal's club financial statement data. Use it as the default workflow for the next clubs.

The goal is to make the process repeatable, auditable, and front-loaded:

- install everything once at the start
- collect official filings first
- download and store the raw reports unchanged
- extract values into structured JSON
- clean, validate, and export only after the raw extraction is complete

This process is designed for Premier League Big Six club revenue work, but it can be extended to other clubs later.

For the structured extraction program in this repo, the common working range starts at `2011/12`.

- Statement-finding, downloading, and extraction should be run for `2011/12` onward by default.
- Earlier club statements may still be stored in `data/raw/financial_statements/`, but they are outside the current common-range extraction workflow unless there is a specific backfill decision.

## Extraction Bank

Before extracting a new statement, check the club-specific extraction bank:

- [docs/financial_statement_extraction_bank.md](/Users/alexkivimaki/big-six-spending-dashboard/docs/financial_statement_extraction_bank.md:1)
- `data/reference/financial_statement_extraction_bank/`

This bank is where we store:

- club-specific statement patterns
- season-by-season page maps
- note labels
- debt extraction logic
- OCR caveats

The goal is that each new extraction pass starts from the accumulated evidence of previous seasons rather than from zero.

## One-Time Setup

Run this once before starting a new batch of clubs:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Current finance extraction work expects these Python packages:

- `requests`
- `pandas`
- `beautifulsoup4`
- `python-dateutil`
- `pymupdf`
- `ocrmac`

Notes:

- `pymupdf` is used to render PDF pages from downloaded financial statements.
- `ocrmac` is used for OCR on rendered page images when the PDF text layer is missing or unreliable.
- Install these at the start of the project or batch so you do not have to stop mid-process later.

## Core Principles

- Always prefer official sources:
  - official club annual reports
  - investor relations pages
  - Companies House filings
  - SEC filings for Manchester United where relevant
- Keep every raw file:
  - statement finder JSON
  - downloaded PDF or HTML
  - downloaded metadata JSON
  - raw extraction JSON
- Do not overwrite raw files casually.
- Do not invent values.
- If a value is unclear, leave it `null` and explain why.
- Keep page references and evidence text for every extracted field.
- Store values as actual currency amounts, not report display units.
  - If the report says `GBP '000`, multiply values by `1,000` before saving them.

## Phase 1: Find Statements

### Objective

Identify the correct official filing for each `club_id + season`.

### Inputs

- `config/big_six_clubs.json`
- `config/financial_years.json`
- `agents/statement_fetcher_agent_prompt.md`

### Command

```bash
python3 scripts/agents/run_statement_fetcher_agent.py --season-from 2011/12 --season-to 2024/25
```

### Output

Task files are created in:

- `data/raw/ai_agents/statement_fetcher_outputs/tasks/`

The completed agent outputs should be saved in:

- `data/raw/ai_agents/statement_fetcher_outputs/`

### Checklist for the Statement-Finder Step

- Confirm the club legal entity is the most relevant football reporting entity.
- Prefer consolidated football group accounts when that best reflects the club's football operations.
- Record:
  - `source_name`
  - `source_url`
  - `download_url`
  - `report_title`
  - `report_type`
  - `financial_year_end`
  - `company_or_group_name`
  - `confidence_level`
- If multiple candidate entities exist, explain the choice in `notes`.

## Phase 2: Download Statements

### Objective

Download the official statement files and save them in a predictable raw folder structure.

### Command

```bash
python3 scripts/collect/download_financial_statements.py
```

### Output

- statement files in `data/raw/financial_statements/{club_id}/`
- metadata sidecars next to each file

### Checklist for the Download Step

- Verify the file opens locally.
- Keep the original PDF or HTML unchanged.
- Keep the metadata JSON next to the file.
- Do not rename files manually after download unless the downloader logic is updated too.

## Phase 3: Prepare Extraction Tasks

### Objective

Create one extraction task per downloaded statement, but prefer a draft-first workflow so AI only reviews uncertain cases.

### Command

```bash
python3 scripts/agents/run_financial_extraction_agent.py --season-from 2011/12 --season-to 2024/25
```

### Output

Task files are created in:

- `data/raw/ai_agents/financial_extraction_outputs/tasks/`

The completed extraction JSON files should be saved in:

- `data/raw/ai_agents/financial_extraction_outputs/`

## Phase 3A: Build Deterministic Drafts

### Objective

Run OCR and club-specific rules first so AI spends time only on ambiguous classifications and debt judgments.

### Commands

```bash
python3 scripts/collect/build_financial_statement_drafts.py --club liverpool --season-from 2011/12 --season-to 2024/25
python3 scripts/agents/run_financial_review_agent.py
```

### Outputs

- draft packages in `data/raw/ai_agents/financial_extraction_drafts/`
- AI review tasks in `data/raw/ai_agents/financial_extraction_review_tasks/`

### Review Rule

- If a draft is structurally sound and confidence is high, you may accept it without a full AI reread.
- If a draft flags ambiguity, only review the flagged pages and candidate values.

## Phase 4: Extract Revenue Data

### Objective

Extract Deloitte-style revenue fields into strict JSON, preferably by reviewing a deterministic draft rather than reading the whole statement from scratch.

### Practical Arsenal Lessons

Arsenal revealed a few patterns that should guide future clubs:

- Some reports have poor or missing text layers.
  - Do not assume `pdftotext`-style extraction will work.
- Render pages from the local PDF first if text extraction is unreliable.
- OCR should be treated as a supporting tool, not a substitute for manual checking.

### Recommended Low-AI Workflow

1. Build OCR cache once.
2. Build a draft extraction package with club-specific rules.
3. Send only the draft, relevant page summaries, and the extraction bank to AI.
4. Ask AI to confirm or correct only the ambiguous fields.
5. Save the reviewed strict JSON into `data/raw/ai_agents/financial_extraction_outputs/`.
- Some seasons expose the revenue split in:
  - a turnover note
  - a segmental analysis note
  - both
- Older Arsenal reports sometimes disclosed:
  - `Retail`
  - `Retail and licensing`
  instead of a single commercial line.
  In this project, those should be merged into `commercial_revenue_original`, with the mapping noted clearly.

### Required Extraction Fields

At minimum, capture:

- `total_revenue_original`
- `matchday_revenue_original`
- `broadcast_revenue_original`
- `commercial_revenue_original`
- `excluded_player_trading_revenue_original`
- `staff_costs_original`
- `player_amortisation_original`
- `profit_on_player_sales_original` when clearly disclosed

### How to Treat Report Units

If the report says `GBP '000`, `£'000`, or similar:

- read the value as displayed
- multiply by `1,000`
- store the converted full amount in the JSON
- write in `units_original` that the figure was converted from report-thousands into full pounds

Example:

- report shows `102,604`
- report unit is `GBP '000`
- saved value should be `102604000`

### Revenue Classification Rules

- `matchday_revenue_original`
  - gate receipts
  - season tickets
  - memberships
  - hospitality
  - matchday and event-day revenue
- `broadcast_revenue_original`
  - league distributions
  - cup broadcasting
  - UEFA broadcasting and prize distributions
  - FIFA competition distributions where disclosed
- `commercial_revenue_original`
  - sponsorship
  - merchandising
  - retail
  - licensing
  - tours
  - museum
  - stadium commercial operations

### Exclusions

Exclude from football revenue totals:

- player trading income
- profit on player sales
- property development turnover
- VAT and similar taxes where not already excluded by the report

### Women’s Team Treatment

Use this rule set:

- if women’s revenue is separately disclosed and removable:
  - exclude it from the project total
  - explain the adjustment in `women_team_treatment_notes`
- if women’s revenue is included but not separable:
  - keep the disclosed club figure
  - flag the limitation clearly in `women_team_treatment_notes`

Arsenal example:

- `2023/24` and `2024/25` separately disclosed women’s UEFA broadcasting amounts
- those can be removed from the extracted broadcasting and total figures

### Evidence Standards

Every extracted JSON should include:

- exact page numbers
- statement labels
- short evidence text
- source document title
- source URL

If a field comes from a mapping decision rather than a directly named line:

- keep the raw label in `evidence`
- explain the standardization in `classification_notes`

## Phase 5: Clean, Validate, Export

Run the pipeline only after the raw extraction JSONs are ready.

### Commands

```bash
python3 scripts/clean/clean_financial_extractions.py
python3 scripts/validate/validate_financial_extractions.py
python3 scripts/export/export_revenue_dataset.py
```

### Outputs

- clean extraction table:
  - `data/clean/club_finances/club_revenue_extractions_clean.csv`
- clean evidence table:
  - `data/clean/club_finances/club_revenue_evidence_clean.csv`
- validation report:
  - `data/clean/club_finances/validation_report.json`
- final export:
  - `data/final/club_revenue_dataset.csv`
  - `src/data/clubRevenueData.json`

## Recommended Club-by-Club Workflow

Use this order for each new club in the current common-range program:

1. Confirm statement coverage across the target season range from `2011/12` onward.
2. Save or verify statement-finder JSON outputs.
3. Download all statements for that club first.
4. Render and inspect the revenue pages for the full club range.
5. Extract all seasons for that club before moving to the next club.
6. Run clean/validate/export after the club batch is complete.

This is better than alternating club-by-club and season-by-season because:

- the report structure is often consistent within a club
- you learn where the key note pages usually sit
- classification decisions stay more consistent

## Common Failure Modes

- Values left in report-thousands instead of full currency amounts
- Commercial sub-lines not merged consistently
- Property development accidentally included in football revenue
- Player trading accidentally included in total revenue
- OCR text copied without checking the underlying page image
- Pages used not recorded
- Women’s competition revenue disclosed separately but not removed

## Review Standard Before Marking a Season Done

- Revenue fields are in full currency amounts
- `total_revenue_original` reconciles to the chosen standardized breakdown
- player trading is excluded
- property development is excluded
- women’s treatment is documented
- page references are present
- source URL is present
- notes explain any reclassification

## Suggested Next-Club Template

For the next club, follow this exact sequence:

```bash
source .venv/bin/activate
python3 scripts/agents/run_statement_fetcher_agent.py --season-from 2011/12 --season-to 2024/25
python3 scripts/collect/download_financial_statements.py
python3 scripts/agents/run_financial_extraction_agent.py --season-from 2011/12 --season-to 2024/25
python3 scripts/clean/clean_financial_extractions.py
python3 scripts/validate/validate_financial_extractions.py
python3 scripts/export/export_revenue_dataset.py
```

Between the task-generation and clean steps:

- complete the raw JSON extraction files for the club
- verify units
- verify exclusions
- verify women’s treatment
