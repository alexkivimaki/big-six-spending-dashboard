# Financial Statement Extraction Bank

This folder is a club-by-club information bank for extracting finance fields from annual reports.

Its purpose is to make future extraction work faster, more consistent, and less error-prone.

Each club folder should capture:

- which legal entity/report type was used
- statement text quality
- page numbers where key notes usually appear
- exact labels used for turnover, wages, debt, and profit
- any reclassification rules
- any season-specific caveats

Recommended workflow:

1. Open the club-level README first.
2. Check the season-level row in the club CSV before reading the statement.
3. Use the documented note labels and page patterns as a first-pass map.
4. If the new statement deviates, update the bank immediately after extraction.

Suggested fields to document by season:

- `season`
- `financial_year_end`
- `report_type`
- `text_layer_quality`
- `profit_and_loss_page`
- `turnover_note_page`
- `staff_costs_note_page`
- `balance_sheet_page`
- `debt_note_pages`
- `turnover_labels`
- `wage_label`
- `debt_method`
- `key_caveats`
- `extraction_confidence`

This bank should be treated as supporting extraction guidance, not as a substitute for checking the raw statement.
