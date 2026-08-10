# Clean Scripts

This folder contains scripts that turn raw source files and raw agent JSON outputs into standardized intermediate datasets.

## Financial extractions

```bash
python3 scripts/clean/clean_financial_extractions.py
```

Outputs:

- `data/clean/club_finances/club_revenue_extractions_clean.csv`
- `data/clean/club_finances/club_revenue_evidence_clean.csv`
