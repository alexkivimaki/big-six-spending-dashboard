# Collection Workflow

## End-to-end workflow

### 1. Collect raw source data

- Download or manually capture source files from approved sources.
- Save them into the relevant `data/raw/` subfolder.
- Record the source in `data/reference/sources.csv` if it is new.

### 2. Store raw data unchanged

- Preserve the raw file exactly as obtained.
- Do not overwrite raw files after manual edits.
- If a source is refreshed, save a new dated copy or use a clear versioning convention.

### 3. Clean names, seasons, and currencies

Standardization work belongs in `data/clean/` and should include:

- club name normalization to `club_id`
- season normalization to `YYYY/YY`
- currency normalization into euros where required
- date normalization to ISO-style formats where practical
- consistent handling of null, unknown, or estimated values

### 4. Validate totals and relationships

Validation should include both structural and analytical checks, such as:

- required columns present
- numeric fields parse correctly
- `net_transfer_spend_eur = gross_transfer_spend_eur - transfer_income_eur`
- `raw_player_cost_eur = net_transfer_spend_eur + estimated_wages_eur`
- sampled season totals reconcile with source summaries where possible

### 5. Add source and confidence fields

Before final export, each record should include provenance and uncertainty context where appropriate:

- `source_id`
- `confidence_level`
- `notes`

### 6. Export final dashboard data

- Write stable CSV or JSON outputs into `data/final/`.
- Keep output schemas aligned with the documented data dictionary.
- Mark sample or demo exports clearly so they are not confused with production data.

### 7. Record freshness metadata

- Add `last_updated` dates to production-facing exports or companion metadata files.
- Capture `date_accessed` for source records.
- Make refresh timing visible so dashboard users understand data recency.

## Practical guidance

- Small, repeatable steps are better than opaque one-off spreadsheets.
- Every transformation should be explainable to a future contributor.
- If a value is estimated, disputed, or backfilled, say so explicitly in `notes`.
