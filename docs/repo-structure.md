# Repo Structure

This repo is now organized around a simple rule: data flows through `data/`, generated frontend assets live in `src/data/`, and the app itself lives in `src/app`, `src/features`, and `src/shared`.

## Backbone

```text
data/
  raw/        source files and untouched collection outputs
  clean/      normalized intermediate tables
  final/      canonical app-facing CSV exports
  reference/  shared lookup tables and source registries

src/
  app/        app entry shell
  data/       generated JSON exports for the frontend
  features/   product features, starting with dashboard/
  shared/     formatters and shared utilities
  styles/     global app styles
```

## Working convention

- Treat `data/final/` as the canonical product dataset layer.
- Treat `src/data/` as generated mirrors for the frontend, not hand-edited source files.
- Add new UI work under `src/features/<feature-name>/`.
- Keep collection, cleaning, and export logic in `scripts/` and `data/`, not in the React app.
