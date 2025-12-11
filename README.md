# Dev Debaters for IDE

A debate-style agent workflow template that runs via VSCode custom instructions.

## Contents
- `docs/workflow.md`: Default workflow rules for the agents.
- `prompts/`: Prompts for hearing/orchestration/spec/plan/code/doc/review agents and judges.
- `prompts/review_requirements.md`: Project-specific review requirements that feed into prompt updates.
- `scripts/generate_improvement_prompt.py`: Generates an improvement-request prompt from phase histories.

## How to use
1. Paste `docs/workflow.md` into VSCode "Custom Instructions -> Always share with AI" to set the common rules (English output, phase order, logging).
2. Load the role/judge prompts under `prompts/` (orchestration, hearing, and the plan/spec/code/doc/review pairs).
3. At session start, have the orchestration role declare "Phase 1: Hearing start". Automation respects `.env`: when `AUTO_MODE=true`, orchestration invokes subsequent phases automatically; when `AUTO_MODE=false`, orchestration must ask the user before advancing to each new phase after Hearing and must post to the user chat after each phase end with the result and the proposed next phase. To auto-run from startup, send the block in `docs/codex_auto_start.md` with `AUTO_MODE=true`.
4. After each phase, the judge appends a log to `histories/YYYYMMDD_<phase>.md` using `histories/README.md`, and appends metrics to the phase-specific file under `metrics/<phase>.md` (one rolling file per phase) using `metrics/README.md` with scores on a 0-100 scale (100 is perfect). Keep `prompts/review_requirements.md` up to date with any standing review guardrails you want included in the prompt refresh.
5. After each phase, if either of these conditions is true, suggest running `scripts/generate_improvement_prompt.py --history-dir histories --output improvements.txt` for the next iteration: the latest score for any role in that phase is below 50, or that role's win rate over its last 10 phase-matched logs is under 30% (skip if there are fewer than 10 phase-matched entries).
