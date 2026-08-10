# Source Policy

## Goal

Source selection should support transparency, reproducibility, and possible future monetization.

## Preferred source hierarchy

### 1. Official club annual reports and Companies House filings
Use these first for:

- revenue
- staff costs
- debt
- profit and loss context
- accounting notes

### 2. Licensed APIs and structured salary sources
Use licensed APIs or carefully documented structured wage sources for:

- wage estimates
- contract context
- squad payroll assumptions

### 3. Transfermarkt club pages and API outputs for transfer and market value data
Use direct Transfermarkt club transfers pages or API outputs primarily for:

- club-season transfer totals
- transfer histories
- transfer fees
- market values
- club and player metadata

For club-season transfer totals, prefer direct club transfers pages where practical because they reflect Transfermarkt's club-level ledger more directly than roster-derived API reconstruction.

### 4. Open football datasets for performance
Use open football datasets for:

- league table outcomes
- points
- match results
- goals for and goals against

### 5. Manual validation for disputed values
Use manual review where sources conflict or where the automated pipeline cannot reconcile a value.

## Operating principles

- Preserve `source_name`, `source_url`, `date_accessed`, and `confidence_level`.
- Do not guess missing values.
- Keep notes when a source is estimated, incomplete, or disputed.
- Avoid uncontrolled scraping for commercial use unless terms clearly permit it.
