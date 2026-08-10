# Financial Statement Extraction Bank

This document explains the purpose of the club-by-club extraction bank stored in:

- `data/reference/financial_statement_extraction_bank/`

Start with the single cross-club reference file:

- [master_financial_statement_extraction_bank.md](/Users/alexkivimaki/big-six-spending-dashboard/data/reference/financial_statement_extraction_bank/master_financial_statement_extraction_bank.md:1)

The bank exists to support future AI-assisted and manual extraction from annual reports.

## Why This Exists

Financial statements are not uniform.

Even within the same league:

- note names differ
- page numbers drift year to year
- scanned PDFs create OCR ambiguity
- debt is sometimes explicit and sometimes only inferable
- wage lines may mean staff costs rather than player-only wages

If those observations are not recorded, each new extraction pass starts from zero.

## How To Use It

Before extracting a new club-season:

1. Open the relevant club folder in `data/reference/financial_statement_extraction_bank/`.
2. Read the club README.
3. Check the season row in the club CSV.
4. Use the documented page pattern and note labels as the first pass.
5. Validate against the raw statement.
6. Update the bank immediately if the statement format changed.

## What To Record

For each season, document:

- report type
- financial year end
- text quality
- where the profit and loss account appears
- where the turnover split appears
- where staff costs appear
- where balance sheet cash appears
- where debt disclosures appear
- what labels the club uses for turnover categories
- how net debt was extracted or estimated
- any caveats that should affect future extraction

## Current Starting Point

Liverpool, Arsenal, and Chelsea are now documented in this structure.

That gives us a practical template for documenting:

- label patterns
- page drift across seasons
- debt extraction logic
- OCR risk areas

As we continue club by club, each club should get:

- a README with club-level patterns
- a season CSV with statement-by-statement extraction notes
