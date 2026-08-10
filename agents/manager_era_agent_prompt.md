# Manager Era Agent Prompt

Collect verified manager spell data for a club. Do not guess dates.

## Task

Collect:

- `manager_id`
- `manager_name`
- `club_id`
- `club_name`
- `start_date`
- `end_date`
- source and evidence fields

## Rules

- Prefer official club histories, club announcements, or well-documented databases.
- Use ISO-style dates where possible.
- If a spell is ongoing, leave `end_date` empty or null and explain in `notes`.

## Output

Return strict JSON with this exact shape:

```json
{
  "manager_id": "",
  "manager_name": "",
  "club_id": "",
  "club_name": "",
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
