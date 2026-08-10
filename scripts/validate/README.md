# Validate Scripts

This folder contains validation scripts for cleaned datasets.

## Financial extractions

```bash
python3 scripts/validate/validate_financial_extractions.py
```

The validator checks:

- required columns
- valid Big Six club IDs
- season format
- numeric revenue fields
- revenue breakdown vs total revenue
- source, page, confidence, and manual-review metadata

It writes:

- `data/clean/club_finances/validation_report.json`
