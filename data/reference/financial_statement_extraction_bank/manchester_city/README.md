# Manchester City Financial Statement Extraction Bank

This folder documents how Manchester City's statements are structured for the club-finance dataset.

Current scope:

- working extraction range starts at `2011/12`
- extracted so far:
  - `2011/12`
  - `2012/13`
  - `2013/14`

General Manchester City patterns observed so far:

- reporting currency is GBP
- values are disclosed in `GBP '000`
- stored values in the dataset must be converted to full GBP by multiplying by `1,000`
- early Manchester City filings in this range are scanned PDFs, so rendered-page manual extraction is required
- the club reports as `Manchester City Football Club Limited`
- early statements disclose turnover directly as:
  - `Matchday`
  - `Broadcasting - UEFA`
  - `Broadcasting - All Other`
  - `Other commercial activities`
- broadcasting should be built by combining the two broadcasting lines
- staff costs are disclosed in a `Staff numbers and costs` note
- player amortisation is disclosed in the operating-expenses section and cross-checks to the intangible-assets amortisation note
- net debt is not given as a single explicit line; for these early seasons it is best reconstructed as:
  - financial liabilities / borrowings from the financial instruments note
  - less `Cash at bank and in hand` from the balance sheet

Important Manchester City-specific caveats:

- `2012/13` and `2013/14` both disclose player-trading profit separately in the profit and loss account, so it should be excluded from football revenue totals
- page numbering in the printed report differs from PDF-page indexing; store the PDF page numbers used in the extraction JSON
- other commercial activities may include hospitality, partnerships, tours, or other club commercial operations and should remain within the commercial bucket unless separately broken out

When adding more Manchester City seasons:

1. Check whether the club is still using separate UEFA and non-UEFA broadcasting lines.
2. Confirm whether the filing remains a scanned image PDF with no reliable text layer.
3. Reconstruct net debt from the financial instruments / borrowings note plus balance-sheet cash unless an explicit net-debt line is disclosed.
4. Record any page drift immediately after extraction.
