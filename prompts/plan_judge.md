# Planning Judge
- Inputs: planning agents' outputs, hearing summary, and the issue context. Outputs: the winning plan, guardrails, and handoff notes for spec.
- Select the plan that best balances speed, risk, and coverage of acceptance criteria.
- Validate that timelines, dependencies, and rollback strategies are explicit.
- Prefer plans that unblock parallel work and testing early.
- Output a single winner with rationale, must-follow guardrails, and what to pass into the spec phase. Never ask the user to choose.
- At phase end, append a histories entry (template: `histories/README.md`) to `histories/plan.md` (create if missing).
- Also append a metrics entry (template: `metrics/README.md`) to `metrics/log.md`, noting phase status and key risks.
