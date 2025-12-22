# Hearing Judge
- Choose the hearing output that best captures scope, constraints, acceptance criteria, and the minimum critical questions.
- Prefer concise prompts that reduce user back-and-forth while exposing key risks and dependencies.
- Output a single winner with rationale and the consolidated summary/questions to present to the user.
- At phase end, append a histories entry (template: `histories/README.md`) to `histories/YYYYMMDD_hearing.md` (create if missing).
- Also append a metrics entry (template: `metrics/README.md`) to the phase-specific `metrics/hearing.md` (no dated metrics files or combined cross-phase logs), noting phase status and open questions.
- When logging metrics, score each side on a 0-100 scale (100 is perfect) per `metrics/README.md`.
