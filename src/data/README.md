# Frontend Data Layer

This folder holds generated JSON assets that mirror the canonical exports in `data/final/`.

## What belongs here

- `clubSeasonData.json`
- `clubSeasonMasterData.json`
- `clubRevenueData.json`
- `clubTransferRowsData.json`
- per-league JSON mirrors under `by_league/{league_key}/`

## Working rule

- Treat these files as generated app inputs, not hand-edited source files.
- Keep data cleaning, validation, and reconciliation in `scripts/` and `data/`.
- Build app adapters in `src/pages/`, `src/components/`, `src/lib/`, or `src/shared/`, not in this folder.

## Relationship to the app

- `data/final/` is the canonical export layer.
- `src/data/` is the frontend mirror layer.
- The React app should read from here and focus only on presentation and interaction.
