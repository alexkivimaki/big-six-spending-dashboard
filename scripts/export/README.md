# Export Scripts

This folder contains scripts that convert clean datasets into stable dashboard-ready outputs.

## Revenue dataset

```bash
python3 scripts/export/export_revenue_dataset.py
```

Outputs:

- `data/final/club_revenue_dataset.csv`
- `src/data/clubRevenueData.json`

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
