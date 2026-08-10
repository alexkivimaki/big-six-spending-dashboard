# Data Collection Workflow

This project uses a staged pipeline so raw collection, research, cleaning, validation, and frontend export stay auditable.

## Full pipeline

1. Collect raw Transfermarkt club transfers pages.
2. Collect raw Transfermarkt manager history pages where manager attribution is needed.
3. Collect raw Transfermarkt achievements pages where trophy history is needed.
4. Store raw HTML unchanged in nested league/season/club directories.
5. If you want an additional manual cross-check, capture verified club-page totals into a verified club totals file.
6. Run cleaning scripts.
7. Run AI-agent research tasks for wages, finances, performance, and managers.
8. Save AI-agent JSON outputs in `data/raw/ai_agents/`.
9. Clean AI-agent outputs.
10. Validate data.
11. Export dashboard-ready data.
12. Review before publishing.

## Practical notes

- The React frontend should not call Transfermarkt directly.
- Every raw club page should be saved before any parsing or standardization.
- Use a consistent naming convention across raw, clean, and final outputs:
  `{league_key}/{season_dir}/{club_id}/{club_id}_{season_dir}_...`
- Club-season transfer totals are now intended to come directly from the Transfermarkt club transfers page scraper.
- Manager eras can also be collected directly from Transfermarkt manager history pages and expanded into club-season overlap rows.
- Club achievements can be collected directly from Transfermarkt achievements pages and assigned into season-level trophy summaries.
- Manually verified club-page totals can still be used as an override or audit layer.
- If a field cannot be trusted, leave it blank and explain why in `notes`.
- Validation is part of the workflow, not an afterthought.
