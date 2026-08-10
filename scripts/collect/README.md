# Collect Scripts

This folder contains raw-data collection scripts for the project.

## Financial statements

`download_financial_statements.py` downloads reports from URLs found by the statement fetcher agent outputs.

`build_financial_statement_drafts.py` builds deterministic draft extractions from OCR caches for clubs with supported parsers. Use this before AI review so the model only sees uncertain cases instead of the full statement from scratch.

Before running the finance collection process for a new club batch, install all dependencies once:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

This includes the PDF and OCR tooling used in the documented Arsenal workflow, so you do not need to pause later for more setup.

Example:

```bash
python3 scripts/collect/download_financial_statements.py
python3 scripts/collect/download_financial_statements.py --overwrite
python3 scripts/collect/build_financial_statement_drafts.py --club liverpool --season-from 2011/12 --season-to 2024/25
```

Downloaded files are saved under:

`data/raw/financial_statements/{club_id}/`

The script also writes a metadata JSON next to each downloaded file.
