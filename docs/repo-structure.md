# Repo Structure

This repo is now organized around a simple rule: data flows through `data/`, generated frontend assets live in `src/data/`, and the app itself lives in `src/app`, `src/pages`, `src/components`, `src/config`, `src/lib`, and `src/shared`.

## Backbone

```text
data/
  raw/        source files and untouched collection outputs
  clean/      normalized intermediate tables
  final/      canonical app-facing CSV exports
  reference/  shared lookup tables and source registries

src/
  app/        app entry shell
  components/ reusable UI building blocks
  config/     club metadata and metric registry
  data/       generated JSON exports for the frontend
  lib/        data adapters and availability helpers
  pages/      routed page experiences
  shared/     formatters and shared utilities
  styles/     global app styles
```

## Working convention

- Treat `data/final/` as the canonical product dataset layer.
- Treat `src/data/` as generated mirrors for the frontend, not hand-edited source files.
- Add routed experiences under `src/pages/` and reusable UI under `src/components/`.
- Keep collection, cleaning, and export logic in `scripts/` and `data/`, not in the React app.
