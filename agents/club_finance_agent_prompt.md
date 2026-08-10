# Club Finance Agent Prompt

Collect one club-season’s official finance data from trusted sources. Do not guess missing values.

## Task

For one `club_id` and one `season`, collect:

- `revenue_eur`
- `matchday_revenue_eur`
- `broadcasting_revenue_eur`
- `commercial_revenue_eur`
- `official_staff_costs_eur`
- `operating_profit_loss_eur`
- `profit_loss_before_tax_eur`
- `net_debt_eur`
- `player_amortisation_eur`
- `profit_on_player_sales_eur`
- source and evidence fields

## Rules

- Prefer official annual reports and Companies House filings.
- Use `null` for unavailable fields.
- Record the original currency if the source is not in euros.
- Include a short evidence quote or page reference.
- Put accounting caveats in `notes`.

## Output

Return strict JSON with this exact shape:

```json
{
  "club_id": "",
  "club_name": "",
  "season": "",
  "revenue_eur": null,
  "matchday_revenue_eur": null,
  "broadcasting_revenue_eur": null,
  "commercial_revenue_eur": null,
  "official_staff_costs_eur": null,
  "operating_profit_loss_eur": null,
  "profit_loss_before_tax_eur": null,
  "net_debt_eur": null,
  "player_amortisation_eur": null,
  "profit_on_player_sales_eur": null,
  "currency_original": "",
  "conversion_rate_to_eur": null,
  "source_name": "",
  "source_url": "",
  "date_accessed": "",
  "evidence": "",
  "confidence_level": "",
  "notes": ""
}
```
