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
- No user choice for judges or winners: orchestration runs phases, calls judges, and advances automatically.

## Phase inputs, outputs, and handoffs

- Hearing (solo): Input = user issue/context. Output = clarified scope, constraints, acceptance checks, and unknowns. Handoff = feed summary to plan.
- Plan (A/B -> judge): Input = hearing summary + issue. Output = two plans with milestones/risks/tests. Handoff = winning plan to spec.
- Spec (A/B -> judge): Input = winning plan + issue. Output = two specs with data/IO, edge cases, and acceptance checks. Handoff = winning spec to code.
- Code (A/B -> judge): Input = winning spec + issue. Output = two coding approaches with diffs/commands/tests. Handoff = winning code plan to doc.
- Doc (A/B -> judge): Input = winning code plan + issue. Output = two doc updates (README/runbook/changelog). Handoff = winning doc notes to review.
- Review & improvement (judge): Input = all prior winners + logs. Output = quality review, blockers, follow-ups, metrics update, and improvement prompts if needed. Handoff = next cycle instructions if not shipped.

## Phase flow and roles

1. **Hearing (solo)**: Confirm request, constraints, acceptance criteria; produce a written task list.
2. **Plan (bench, A/B -> judge)**: Competing plans, risks, tests; judge selects one.
3. **Spec (bench, A/B -> judge)**: Concrete design, data/IO, acceptance checks; judge selects one.
4. **Code (bench, A/B -> judge)**: Minimal safe diffs and test strategy; judge selects one.
5. **Doc (bench, A/B -> judge)**: README/ops notes/comment policy; judge selects one and provides samples if needed.
6. **Review & improvement (judge)**: Aggregate history, call out risks/TODOs, and request follow-up iterations if needed. Update metrics.
7. **Orchestration (meta role)**: Announces phases, queues agents, ensures logs/metrics are written, and keeps the run moving.

## Progress rules

- Each phase: agent discussion -> judge decision -> next actions. No user prompts after hearing.
- Orchestration must state which inputs are used, where outputs are written, and which phase starts next.
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
