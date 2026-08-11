# Export Scripts

This folder contains scripts that convert clean datasets into stable dashboard-ready outputs.

## Economic factors reference

The season-level FX and inflation backbone lives in:

- `data/reference/economic_factors.csv`

You can repopulate the currently curated season factors with:

```bash
./.venv/bin/python scripts/export/populate_economic_factors.py
```

This file is the single source of truth for:

- `gbp_to_eur_rate`
- `eur_to_usd_rate`
- `gbp_to_usd_rate`
- `inflation_adjustment_to_2025_26`

The export scripts will merge these factors by season and carry the factor columns plus converted monetary fields into the final datasets. Blank factor values remain blank in the exports rather than being backfilled with guessed numbers.

## Revenue dataset

```bash
python3 scripts/export/export_revenue_dataset.py
```

Outputs:

- `data/final/club_revenue_dataset.csv`
- `src/data/clubRevenueData.json`

This export now also carries:

- nominal `GBP`, `EUR`, and `USD` views for the available finance fields
- real-value `2025/26 prices` columns where `inflation_adjustment_to_2025_26` is populated
- season-level economic factor metadata

## Club-season master dataset

```bash
python3 scripts/export/export_club_season_master_dataset.py
```

Optional common-start filter:

```bash
python3 scripts/export/export_club_season_master_dataset.py --season-from 2011/12
```

Outputs:

- `data/final/club_season_master.csv`
- `src/data/clubSeasonMasterData.json`
- `data/final/by_league/<league_key>/club_season_master.csv`
- `src/data/by_league/<league_key>/clubSeasonMasterData.json`

This export joins the currently available transfer, manager, achievement, performance, and finance layers into one club-season table. Missing layers remain blank rather than blocking the export.

Finance rows inherit the same season-level economic factors and converted monetary fields used by the standalone revenue export.

## Dashboard dataset

```bash
python3 scripts/export/export_dashboard_data.py
```

Outputs:

- `data/final/club_season_dashboard.csv`
- `src/data/clubSeasonData.json`
- `data/final/by_league/<league_key>/club_season_dashboard.csv`
- `src/data/by_league/<league_key>/clubSeasonData.json`
- `src/data/clubTransferRowsData.json`

This export now carries season-level economic factors and converted transfer-spend currency views so nominal and inflation-adjusted frontend comparisons can later read from one consistent source model.
