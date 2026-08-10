# Financial Statement Collection Workflow

Use [club_financial_statement_runbook.md](/Users/alexkivimaki/big-six-spending-dashboard/docs/club_financial_statement_runbook.md:1) as the operational guide. This file gives the short version of the pipeline.

Current common-range rule:

- extract club financial statement data from `2011/12` onward
- treat earlier statements as optional archival material unless a specific backfill decision is made

## One-Time Setup

Before starting a new club batch:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

This installs the PDF/OCR tooling used in the Arsenal workflow so the next clubs do not require extra setup mid-process.

## Workflow

1. Generate statement-fetching tasks with `scripts/agents/run_statement_fetcher_agent.py`.
2. Use an AI agent to find official financial statements for each club and season.
3. Save statement-fetcher outputs as JSON in `data/raw/ai_agents/statement_fetcher_outputs/`.
4. Download statements with `scripts/collect/download_financial_statements.py`.
5. Review the downloaded files in `data/raw/financial_statements/`.
6. Generate extraction tasks with `scripts/agents/run_financial_extraction_agent.py`.
7. Use an AI agent or the documented manual workflow to extract revenue data from each statement.
8. Save extraction JSON in `data/raw/ai_agents/financial_extraction_outputs/`.
9. Run the clean, validate, and export scripts.

## Process Rules

- Keep every raw statement file and every raw agent output.
- Corrections and standardization belong in clean outputs, not the raw layer.
- Store extracted values as full currency amounts.
  - If the report is in `GBP '000`, multiply by `1,000` before saving.
- Record page references and evidence text for every extracted field.
- Exclude player trading and property development from football revenue totals.
