# Revenue Data Dictionary

## `statement_fetcher_outputs`

One JSON record per club-season search result for an official annual report or filing.

Key fields:

- `club_id`
- `season`
- `financial_year_end`
- `report_title`
- `source_url`
- `download_url`
- `is_official_source`
- `confidence_level`

## `financial_extraction_outputs`

One JSON record per club-season statement extraction.

Key fields:

- original-currency revenue figures
- euro-converted figures where available
- evidence array with page references
- notes about classification, women’s revenue, and player trading

## `club_revenue_extractions_clean`

Flattened clean table built from raw extraction JSON outputs.

Key fields:

- club and season identifiers
- original and euro values
- sum checks
- source document and source URL
- confidence and manual-review flags

## `club_revenue_evidence_clean`

One row per evidence item from the extraction JSON.

Key fields:

- `club_id`
- `season`
- `field`
- `page_number`
- `statement_label`
- `evidence_text`

## `club_revenue_dataset`

Final dashboard-ready export focused on season-level revenue categories and shares.

Key fields:

- `turnover_original`
- `gate_and_matchday_income_original`
- `tv_and_broadcasting_original`
- `commercial_income_original`
- `wage_bill_original`
- `wages_as_proportion_of_turnover`
- `net_debt_original`
- `profit_loss_before_tax_original`
- `total_revenue_eur`
- `matchday_revenue_eur`
- `broadcast_revenue_eur`
- `commercial_revenue_eur`
- revenue shares
- source and confidence fields
