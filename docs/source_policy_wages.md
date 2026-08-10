# Wage Source Policy

This project treats player wage data as a separate evidence class from official club financial statements.

## Primary Goal

Estimate **club-season player wages** for dashboard analysis, not total employment costs.

## Preferred Source Hierarchy

1. licensed or clearly documented salary databases
2. reliable public wage-estimate databases with consistent football coverage
3. official club reporting only if player wages are directly isolated
4. reliable journalism only for context or cross-checking

## Rules

- Do not use unsourced fan sites as primary wage sources.
- Do not replace player wages with total staff costs.
- If the source provides weekly wage estimates, record the annualisation logic in `notes`.
- If the source only gives partial squad coverage, explain the limitation clearly.
- Always keep:
  - source name
  - source URL
  - date accessed
  - original currency
  - unit basis
  - evidence
  - confidence level

## Confidence Guidance

- `high`
  Clear season-level wage estimate from a trusted and documented source.
- `medium`
  Reasonable source but some transformation or aggregation was required.
- `low`
  Sparse or ambiguous source, weak coverage, or significant assumptions.

## Current Project Rule

For the common dashboard workflow, collect wage estimates from `2011/12` onward.
