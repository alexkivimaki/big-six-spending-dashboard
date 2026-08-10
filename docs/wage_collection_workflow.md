# Wage Collection Workflow

This workflow covers the first practical version of the player wage pipeline for the clubs in analysis.

The current common working range starts at `2011/12`.

## Goal

Collect one **club-season player wage estimate** per `club_id + season` so the dashboard can support:

- `Player cost = net_transfer_spend_eur + estimated_player_wages_eur`
- `Estimated football operating result = football_revenue - player_cost`

## One-Time Setup

Run this once at the start of the wage collection batch:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

No extra tools should be needed beyond the project requirements and your AI-agent workflow.

## Workflow

1. Generate wage-collection tasks.

```bash
python3 scripts/agents/run_wage_collection_agent.py --season-from 2011/12 --season-to 2024/25
```

2. Use the prompt in `agents/wage_data_agent_prompt.md` with the generated task JSON.

3. Save strict JSON outputs in:

- `data/raw/ai_agents/wages/`

4. Clean the outputs:

```bash
python3 scripts/clean/clean_ai_agent_outputs.py
```

5. Re-export the master dataset after wage rows exist:

```bash
python3 scripts/export/export_club_season_master_dataset.py --season-from 2011/12
```

## Source Guidance

Preferred wage sources are:

1. licensed or clearly documented football salary sources
2. reliable public wage-estimate databases with season-level coverage
3. official reports only when player wages are directly disclosed

Do not substitute total staff costs for player wages.

## Output Standard

Each JSON output should include:

- `estimated_player_wages_eur`
- `source_name`
- `source_url`
- `date_accessed`
- `currency_original`
- `units_original`
- `conversion_rate_to_eur`
- `exchange_rate_source`
- `evidence`
- `confidence_level`
- `requires_manual_review`
- `notes`

## Important Caveats

- Most public player wage data is estimated, not audited.
- Some sources report weekly wages, so annualisation must be explained.
- Staff costs and player wages are not the same thing.
- If the wage estimate is not trustworthy enough, keep the value null and explain why.
