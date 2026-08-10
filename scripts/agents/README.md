# Agent Task Scripts

These scripts create task JSON files for manual or external AI-agent use. They do not call an AI API directly.

For the full club-finance workflow, use:

- [club_financial_statement_runbook.md](/Users/alexkivimaki/big-six-spending-dashboard/docs/club_financial_statement_runbook.md:1)
- [financial_statement_collection_workflow.md](/Users/alexkivimaki/big-six-spending-dashboard/docs/financial_statement_collection_workflow.md:1)
- [financial_extraction_workflow.md](/Users/alexkivimaki/big-six-spending-dashboard/docs/financial_extraction_workflow.md:1)

## Scripts

- `run_statement_fetcher_agent.py`
  Creates club-season tasks for finding official annual reports or accounts.
- `run_financial_extraction_agent.py`
  Creates extraction tasks for downloaded statement files.
- `run_financial_review_agent.py`
  Creates AI-review tasks from deterministic draft extraction packages.
- `run_wage_collection_agent.py`
  Creates club-season tasks for collecting estimated player wages.

## Workflow

1. Build deterministic drafts first where possible.
2. Run the script to generate review task files.
3. Paste a review task and the matching prompt into Codex, ChatGPT, or another agent.
4. Save the returned strict JSON into the relevant raw output folder.
5. Run the clean, validate, and export scripts in this repo.

## Recommended Batch Pattern

For financial statement work, do not switch randomly between clubs and seasons. A smoother pattern is:

1. complete statement-finding for one club across the target range
2. download that club's full statement set
3. build deterministic OCR drafts for that club
4. send only ambiguous draft packages to AI review
5. run clean/validate/export after the club batch is complete

This keeps classification choices and note-page discovery more consistent.

## Examples

```bash
python3 scripts/agents/run_statement_fetcher_agent.py
python3 scripts/agents/run_financial_extraction_agent.py
python3 scripts/agents/run_financial_review_agent.py
python3 scripts/agents/run_wage_collection_agent.py --season-from 2011/12 --season-to 2024/25
```
