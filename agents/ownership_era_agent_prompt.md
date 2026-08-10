# Ownership Era Agent Prompt

Collect verified ownership-era data for a club. Do not infer missing details.

## Task

Collect:

- `club_id`
- `club_name`
- `ownership_era`
- `owner_or_group_name`
- `start_date`
- `end_date`
- source and evidence fields

## Rules

- Prefer official filings, club statements, and high-quality reporting.
- Use ISO-style dates where possible.
- Use `notes` for partial acquisitions, consortium changes, or legal-entity caveats.

## Output

Return strict JSON with this exact shape:

```json
{
  "club_id": "",
  "club_name": "",
  "ownership_era": "",
  "owner_or_group_name": "",
  "start_date": "",
  "end_date": "",
  "source_name": "",
  "source_url": "",
  "date_accessed": "",
  "evidence": "",
  "confidence_level": "",
  "notes": ""
}
```
