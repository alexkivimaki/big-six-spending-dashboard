# Liverpool Financial Statement Extraction Bank

This folder documents how Liverpool's statements are structured for the club-finance dataset.

Current scope:

- working extraction range starts at `2011/12`
- extracted so far:
  - `2011/12`
  - `2012/13`
  - `2013/14`

General Liverpool patterns observed so far:

- reporting currency is GBP
- values are disclosed in `GBP '000`
- stored values in the dataset must be converted to full GBP by multiplying by `1,000`
- the club changes to a `31 May` year end from `2011/12`
- older Liverpool statements are scanned PDFs, so OCR is required
- the turnover split is usually disclosed explicitly in an `Analysis of turnover` note
- Liverpool uses:
  - `Media`
  - `Matchday`
  - `Commercial`
  as the primary turnover categories in the early seasons reviewed so far
- staff costs and player amortisation are disclosed in the administrative expenses notes
- net debt is not always shown as a single explicit line, so it may need to be estimated from:
  - bank loan
  - current parent/group undertaking loan
  - cash at bank and in hand

Important Liverpool-specific caveats:

- `2011/12` is a shortened `10 month` reporting period
- the scanned PDFs can cause OCR misreads on:
  - commas
  - bracketed negatives
  - column order
- for Liverpool, the turnover note should be trusted over noisy OCR from the face financial statements when both exist
- the debt method used for `2012/13` and `2013/14` is an estimate, not an explicitly disclosed net-debt line

When adding more Liverpool seasons:

1. Check the season row in `liverpool_extraction_bank.csv`.
2. Confirm whether the report is still using the same turnover labels.
3. Confirm whether the debt note still uses the same current-loan + bank-loan structure.
4. Record any page-number drift or wording changes immediately after extraction.
