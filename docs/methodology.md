# Methodology

## Scope

The project is centered on club-season analysis for the Premier League Big Six from `2008/09` onward. Each row is intended to represent one club in one season, with transparent formulas and traceable sources.

## Currency standard

All working values should be stored in euros.

If a source is not originally in euros:

- preserve the original currency
- document the conversion rate used
- keep a note about the conversion basis

## Core formulas

### Net transfer spend

```text
net_transfer_spend_eur = gross_transfer_spend_eur - transfer_income_eur
```

### Raw player cost

```text
raw_player_cost_eur = net_transfer_spend_eur + estimated_player_wages_eur
```

### Cost per point

```text
cost_per_point = raw_player_cost_eur / points
```

### Wage-to-revenue ratio

```text
wage_to_revenue_ratio = official_staff_costs_eur / revenue_eur
```

## Interpretation caveats

- `estimated_player_wages_eur` should be treated as an estimate unless a high-quality methodology clearly supports the figure.
- `official_staff_costs_eur` comes from official accounts where available, but it includes non-player staff and is not identical to first-team wages.
- Transfer fees are often easier to validate than wage estimates.
- A negative `net_transfer_spend_eur` is possible when transfer income exceeds gross spending.
- `raw_player_cost_eur` is a practical analytical measure, not an audited accounting line.

## Source separation

The project intentionally separates:

- Transfer data collected through the local Transfermarkt API workflow
- Wage and finance data gathered through documented research workflows
- Performance data gathered from football result datasets or official sources

## Future methodology extensions

- inflation-adjusted values
- player-level transfer analysis
- spending by age or position
- more robust efficiency metrics such as cost per minute or squad amortisation views
