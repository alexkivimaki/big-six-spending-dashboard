# Financial Extraction Workflow

Use [club_financial_statement_runbook.md](/Users/alexkivimaki/big-six-spending-dashboard/docs/club_financial_statement_runbook.md:1) as the detailed operating guide. This file focuses on extraction rules.

The preferred workflow is now:

1. build OCR cache
2. build deterministic draft extraction
3. send only uncertain draft packages to AI review
4. save reviewed strict JSON outputs

Current common-range rule:

- the standardized extraction workflow should be run for club financial statements from `2011/12` onward

## Reading statements

Avoid asking AI to read the full statement from scratch whenever possible. Instead:

- render/OCR the statement once
- cache the page text
- build candidate values in code
- use AI only to resolve ambiguity

- Use the official annual report, Companies House filing, SEC filing, or official investor-relations source wherever possible.
- Record the document title, URL, file path, page numbers, and evidence text for every extracted value.
- Install PDF rendering and OCR dependencies at the start of the project so you do not need ad hoc setup during extraction.
- If the PDF text layer is weak or missing, render the relevant pages from the local PDF and review the page images directly.

## Revenue classification

- Map disclosed categories into `matchday`, `broadcast`, and `commercial` only when the mapping is clear.
- Preserve the original label in evidence or notes when the club uses unusual wording.
- Keep `total_revenue` separate from player trading and similar disposal gains.
- If a club discloses `retail`, `retail and licensing`, or similar sub-lines separately, merge them into `commercial` only when that mapping is methodologically clear and note it explicitly.

## Units and scaling

- Always check the report unit before saving values.
- If the report states `GBP '000`, `£'000`, or similar, multiply the displayed values by `1,000`.
- Save full currency amounts in the extraction JSON.
- Use `units_original` to document that the report was presented in thousands.

## Missing values

- If a category is not disclosed clearly, return `null`.
- Explain why the value is missing in `classification_notes` or `notes`.
- Do not estimate, infer, or backfill undisclosed revenue splits.

## Women’s revenue

- Exclude women’s team revenue when it is separately disclosed.
- If it is included in a consolidated figure and cannot be separated, keep the disclosed number and flag the limitation in `women_team_treatment_notes`.
- If a women's competition distribution is separately disclosed inside a broader category, subtract it from the extracted men's/club football revenue figure and explain the adjustment.

## Non-football or stadium commercial revenue

- Commercial revenue may include tours, events, and other non-matchday stadium operations.
- Keep the disclosed figure but document that treatment in `non_football_revenue_notes`.

## Player trading

- Profit on player sales, player trading income, and similar items should not be included in revenue totals.
- Capture them separately if disclosed for auditability.
- Property development turnover should also stay outside the football revenue total.
