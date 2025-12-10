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
- User dialogue is only allowed in hearing. Later phases proceed without asking the user; judges write to files, not chat (only acknowledge completion).

## Phase flow and roles

1. **Hearing (solo)**: Confirm request, constraints, acceptance criteria; produce a written task list.
2. **Plan (bench, A/B -> judge)**: Competing plans, risks, tests; judge selects one.
3. **Spec (bench, A/B -> judge)**: Concrete design, data/IO, acceptance checks; judge selects one.
4. **Code (bench, A/B -> judge)**: Minimal safe diffs and test strategy; judge selects one.
5. **Doc (bench, A/B -> judge)**: README/ops notes/comment policy; judge selects one and provides samples if needed.
6. **Review & improvement (judge)**: Aggregate history, call out risks/TODOs, and request follow-up iterations if needed. Update metrics.
7. **Orchestration (meta role)**: Announces phases, queues agents, ensures logs/metrics are written, and keeps the run moving.

## Progress rules

- Each phase: agent discussion -> judge decision -> next actions.
- If stuck, orchestration poses a concise question to converge within one turn.
- Version control: prefer small commits per phase; share diffs early.
- Logs: append chronologically to `histories/<role>.md` (one entry per phase) using the template.
- Environment/test limits must be stated; run agreed tests first.
- Metrics: append to `metrics/log.md` (or dated file) with status, tests, and artifacts.

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
5. Judges append metrics to `metrics/log.md` (or dated files) using `metrics/README.md`.
6. Load all histories with `scripts/generate_improvement_prompt.py` to generate the next improvement-request prompt.

## Recommended directory layout

- `prompts/`: Role and judge prompts (use this repo's examples)
- `histories/`: Log outputs, appended per phase
- `metrics/`: Metrics logs, appended per cycle
- `scripts/generate_improvement_prompt.py`: Improvement-request generator
