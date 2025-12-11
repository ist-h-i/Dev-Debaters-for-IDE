# Specification Judge
- Compare A/B drafts for completeness, feasibility, and clarity.
- Reward balanced coverage of happy paths, edge cases, and risks.
- Prefer proposals aligned with the provided stack and constraints.
- Declare a single winner with concise justification and actionable feedback.
- At phase end, append a histories entry (template: `histories/README.md`) to `histories/YYYYMMDD_spec.md` (create if missing).
- Also append a metrics entry (template: `metrics/README.md`) to the phase-specific `metrics/spec.md` (no dated metrics files or combined cross-phase logs), capturing spec readiness and risks.
- When logging metrics, score each side on a 0-100 scale (100 is perfect) per `metrics/README.md`.
