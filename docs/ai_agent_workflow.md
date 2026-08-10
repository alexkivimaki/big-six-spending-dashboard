# AI Agent Workflow

AI agents in this project are used for structured research, not guessing.

## Core rules

- Agents should return strict JSON.
- Agents should include source and confidence fields.
- Agents should use `null` for missing values rather than inventing them.
- Agents should include evidence text or a page reference whenever possible.

## Intended research areas

- wages
- official club finances
- league performance
- trophies
- manager eras
- ownership eras

## Workflow

1. Choose the right prompt template from `agents/`.
2. Run the research task for a single club-season or a clearly scoped unit.
3. Save the JSON result in the matching folder under `data/raw/ai_agents/`.
4. Run the AI-agent cleaning script to normalize outputs.
5. Validate cleaned results before export.

## Why this separation matters

Separating prompts from cleaned outputs makes it easier to:

- inspect provenance
- rerun one research task without touching others
- compare low-confidence and high-confidence values
- keep monetization options cleaner by preserving source transparency
