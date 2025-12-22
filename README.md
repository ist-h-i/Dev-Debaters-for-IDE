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
3. At session start, have the orchestration role declare "Phase 1: Hearing start" and invoke subsequent phases automatically. To auto-run from startup, send the block in `docs/codex_auto_start.md`.
4. After each phase, the judge appends to the persistent phase log (e.g., `histories/hearing.md`, `histories/plan.md`) using `histories/README.md`, and updates `metrics/log.md` using `metrics/README.md`.
5. After a cycle, optionally run `scripts/generate_improvement_prompt.py --history-dir histories --output improvements.txt` to produce an improvement-request prompt for the next iteration.
