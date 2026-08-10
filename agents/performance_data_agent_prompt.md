# Performance Data Agent Prompt

Collect one club-season’s verified performance data. Do not guess missing values.

## Task

For one `club_id` and one `season`, collect:

- `league_position`
- `points`
- `wins`
- `draws`
- `losses`
- `goals_for`
- `goals_against`
- `goal_difference`
- `trophies`
- `champions_league_qualified`
- source and evidence fields

## Rules

- Prefer structured league result datasets or official competition records.
- Keep trophy notes explicit if the list is ambiguous.
- Use `null` where a value cannot be verified.

## Output

Return strict JSON with this exact shape:

```json
{
  "club_id": "",
  "club_name": "",
  "season": "",
  "league_position": null,
  "points": null,
  "wins": null,
  "draws": null,
  "losses": null,
  "goals_for": null,
  "goals_against": null,
  "goal_difference": null,
  "trophies": "",
  "champions_league_qualified": null,
  "source_name": "",
  "source_url": "",
  "date_accessed": "",
  "evidence": "",
  "confidence_level": "",
  "notes": ""
}
```
