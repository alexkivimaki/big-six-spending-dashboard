# Financial Validation Agent Prompt

Review one extracted club financial JSON record against the original annual report and return strict JSON only.

```json
{
  "club_id": "",
  "season": "",
  "is_valid": false,
  "issues": [],
  "warnings": [],
  "manual_review_required": true,
  "recommended_confidence_level": "",
  "notes": ""
}
```

Check that:

- the source is official or otherwise high quality
- values match the cited page evidence
- units are correctly interpreted
- revenue categories are correctly classified
- player trading is excluded from revenue
- women’s team revenue treatment is clearly documented
- totals reconcile or differences are explained
- null values are justified rather than guessed
