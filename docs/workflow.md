# Dev Debaters for IDE: Workflow for VSCode Custom Instructions

## Purpose and principles

- Paste this into VSCode "Always share with AI" to run a multi-agent workflow quickly.
- Output everything in English. Follow project conventions for code/comments/file names.
- Phases: hearing -> plan -> spec -> code -> doc -> review & improvement. Keep each phase concise.
- Capture "points / claims / decisions / next actions" in every phase and append to history.
- Judges declare winners/adopted proposals per phase and record logs. Orchestration owns progress and log hygiene.
- Prioritize agreed tests/quality gates; surface risks and unknowns explicitly.
- Cite sources when including external code; avoid confidential data.
- At each phase end, judges append directly to `histories/` using `histories/README.md` and to metrics using `metrics/README.md`.
- User dialogue is only allowed in hearing. Later phases proceed without asking the user **unless** automation is disabled via `.env` (see Automation toggle below); judges write to files, not chat (only acknowledge completion).

## Phase flow and roles

1. **Hearing (bench, A/B -> judge)**: Two hearing agents gather requirements with complementary question sets; judge selects the consolidated summary/questions to present, then capture the single user reply.
2. **Plan (bench, A/B -> judge)**: Competing plans, risks, tests; judge selects one.
3. **Spec (bench, A/B -> judge)**: Concrete design, data/IO, acceptance checks; judge selects one.
4. **Code (bench, A/B -> judge)**: Minimal safe diffs and test strategy; judge selects one.
5. **Doc (bench, A/B -> judge)**: README/ops notes/comment policy; judge selects one and provides samples if needed.
6. **Review & improvement (judge)**: Aggregate history, call out risks/TODOs, and request follow-up iterations if needed. Update metrics.
7. **Orchestration (meta role)**: Announces phases, queues agents, ensures logs/metrics are written, and keeps the run moving.

### Per-phase orchestration sequence (Plan/Spec/Code/Doc)

- Orchestration issues the phase start, then explicitly prompts **Agent A** to produce its proposal/output for that phase.
- Once Agent A replies, orchestration forwards the full output to **Agent B** for critique/refinement and awaits B's response.
- After both agent outputs are collected, orchestration triggers the **Judge** to compare A vs B, select or synthesize the winner, record the decision, and only then advance to the next phase.
- These hand-offs are automatic; no additional user queries occur after Hearing **unless** automation is disabled (see Automation toggle).

## Progress rules

- Each phase: agent discussion -> judge decision -> next actions.
- If stuck, orchestration poses a concise question to converge within one turn.
- Version control: prefer small commits per phase; share diffs early.
- Logs: append chronologically to `histories/<role>.md` (one entry per phase) using the template.
- Environment/test limits must be stated; run agreed tests first.
- Metrics: append to the shared `metrics/log.md` file with status, tests, and artifacts; score each side on a 0-100 scale (100 = perfect). Do not create dated metrics files.

## Output templates

- **Discussion log (role agents)**
  - Role: XXX
  - Points: ...
  - Claims: ...
  - Decision: ...
  - Next actions: ...
- **Judge record** (append to the relevant `histories/` file at phase end)
  - Phase: Hearing / Orchestration / Plan / Spec / Code / Doc / Review
  - Participants & claim summary: ...
  - Winner / adopted proposal: ...
  - Next actions / TODO: ...

## VSCode usage steps

1. Paste this document into VSCode custom instructions ("Always share with AI").
2. Add project-specific constraints or existing tasks if needed.
3. At session start, orchestration declares "Phase 1: Hearing start."
4. Follow the agreed phase order; judges append history per phase to `histories/`.
5. Judges append metrics to the single rolling log `metrics/log.md` using `metrics/README.md`, scoring each side on a 0-100 scale (100 = perfect) and never creating dated metrics files.
6. After each phase, if the latest score for any role in that phase is below 50 or that role's win rate over its last 10 phase-matched logs is under 30% (skip if there are fewer than 10 phase-matched entries), suggest running `scripts/generate_improvement_prompt.py` to generate the next improvement-request prompt.

## Automation toggle

- Add a `.env` file at the repo root with `AUTO_MODE=true` (default) or `AUTO_MODE=false`.
- When `AUTO_MODE=true`, orchestration advances through Plan/Spec/Code/Doc/Review without asking the user after Hearing.
- When `AUTO_MODE=false`, orchestration must pause before each new phase after Hearing, ask the user to confirm whether to proceed, and post to the user chat after each phase end with the result and the proposed next phase.

## Recommended directory layout

- `prompts/`: Role and judge prompts (use this repo's examples)
- `histories/`: Log outputs, appended per phase
- `metrics/`: Metrics logs, appended per cycle
- `scripts/generate_improvement_prompt.py`: Improvement-request generator
