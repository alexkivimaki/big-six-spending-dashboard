# Agent Prompt Library

This project uses prompt templates to support a manual or semi-automated financial statement workflow. The prompts are designed for use with Codex, ChatGPT, or another AI-agent system, but this repository does not call any AI API directly yet.

## Files

- `statement_fetcher_agent_prompt.md`
  Find official club financial statements for a given club and season.
- `financial_extraction_agent_prompt.md`
  Extract Deloitte-style revenue figures from a downloaded report.
- `financial_validation_agent_prompt.md`
  Review one extracted JSON record against the source report.
- `wage_data_agent_prompt.md`
  Collect club-season player wage estimates for use in player-cost and operating-result analysis.

## How to use

1. Generate task JSON files with the scripts in `scripts/agents/`.
2. Paste a task and the matching prompt into your chosen AI-agent tool.
3. Save the returned JSON into the relevant `data/raw/ai_agents/...` output folder.
4. Run the clean, validate, and export scripts in this repo.

## Rules

- Agents must return strict JSON only.
- Agents must not invent missing values.
- Always preserve source URL, document name, page numbers, and evidence text.
- If women’s team revenue is included in a disclosed group figure and cannot be separated, keep the disclosed figure and flag it clearly in notes.
