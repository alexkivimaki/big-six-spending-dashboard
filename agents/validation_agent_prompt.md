# Validation Agent Prompt

Review a completed football finance data row and assess whether it is ready for publication.

## Review goals

Identify:

- missing fields
- inconsistent values
- source quality issues
- caveats that should be carried forward
- whether the row is safe to publish

## Rules

- Do not invent replacement values.
- Flag formulas that do not reconcile.
- Flag weak or missing provenance.
- Explain why a row is or is not safe to publish.

## Output

Return strict JSON with this exact shape:

```json
{
  "row_identifier": "",
  "missing_fields": [],
  "inconsistent_values": [],
  "source_quality_issues": [],
  "caveats": [],
  "safe_to_publish": false,
  "notes": ""
}
```
